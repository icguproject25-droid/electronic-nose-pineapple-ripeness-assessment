"""
models.py
---------
定義訓練與部署用的分類模型。

Teacher 模型（較大、較準）：
  - EfficientNet-B3（12.2M 參數）
  - ConvNeXt-Tiny（28.6M 參數）

Student 模型（較小、適合部署）：
  - EfficientNet-B0（5.3M 參數）← 實際部署使用這個
  - MobileNetV3-Small（2.5M 參數）

透過 build_model() 建立模型，並換掉原本的分類頭（head），
讓模型輸出我們自訂的類別數（這裡是 4 種鳳梨品種）。
"""

import torch
import torch.nn as nn
import timm


# 支援的模型名稱對應 timm 內部名稱與大約參數量（百萬）
# 訓練時可以選 teacher 模型取得更高準確率，部署時用 student 模型降低執行時間
MODELS = {
    # name            : (timm_name,              params_M)
    "efficientnet_b3" : ("efficientnet_b3",       12.2),   # teacher：準確率高
    "convnext_tiny"   : ("convnext_tiny",          28.6),   # teacher：最大、最準
    "efficientnet_b0" : ("efficientnet_b0",         5.3),   # student：部署首選
    "mobilenet_v3"    : ("mobilenetv3_small_100",   2.5),   # student：最輕量
}


def build_model(
    name: str,
    num_classes: int,
    pretrained: bool = True,
    dropout: float = 0.3,
) -> nn.Module:
    """
    用 timm 建立模型並換掉 classifier head。

    Args:
        name        : 模型名稱，必須在 MODELS 字典中
        num_classes : 輸出類別數，這裡是 4（四種鳳梨品種）
        pretrained  : 是否使用 ImageNet 預訓練權重（遷移學習，小資料集效果好）
        dropout     : Dropout 機率，加在最後全連接層前，防止 overfit

    Returns:
        已換好 head 的 PyTorch 模型（尚未載入我們自己的訓練權重）
    """
    if name not in MODELS:
        raise ValueError(f"未知模型 {name}，選項：{list(MODELS.keys())}")

    timm_name, param_m = MODELS[name]

    # num_classes=0 代表先移除原本的分類頭，只保留 feature extractor 部分
    # 這樣後面才能自己換上適合 4 類的新 head
    model = timm.create_model(
        timm_name,
        pretrained=pretrained,
        num_classes=0,
    )

    # 用一張假圖跑過 feature extractor，得到 feature 維度
    # 不同模型的 feature 維度不同（B0=1280, B3=1536...）
    with torch.no_grad():
        dummy = torch.zeros(1, 3, 224, 224)
        feat_dim = model(dummy).shape[-1]

    # 換上自訂的分類 head：Dropout → Linear(feature_dim → num_classes)
    # Dropout 在小資料集（270 張）時有明顯防 overfit 效果
    model.head = nn.Sequential(
        nn.Dropout(p=dropout),
        nn.Linear(feat_dim, num_classes),
    )

    # timm 不同模型存 head 的屬性名稱不一樣（有的叫 classifier，有的叫 head）
    # 這裡統一處理，確保 model.head 和 model.classifier 指向同一個 head
    if hasattr(model, "classifier"):
        model.classifier = model.head
    elif hasattr(model, "head"):
        pass  # 已設定，不需再做

    print(f"[Model] {name}  params≈{param_m}M  feat_dim={feat_dim}  "
          f"num_classes={num_classes}")
    return model


def count_params(model: nn.Module) -> str:
    """計算模型的總參數量與可訓練參數量，方便確認模型大小。"""
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return f"Total: {total/1e6:.2f}M  Trainable: {trainable/1e6:.2f}M"
