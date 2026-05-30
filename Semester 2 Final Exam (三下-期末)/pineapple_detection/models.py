"""
models.py
---------
Teacher（EfficientNet-B3 / ConvNeXt-Tiny）
Student（EfficientNet-B0 / MobileNetV3-Small）
"""

import torch
import torch.nn as nn
import timm


MODELS = {
    # name            : (timm_name,              params_M)
    "efficientnet_b3" : ("efficientnet_b3",       12.2),
    "convnext_tiny"   : ("convnext_tiny",          28.6),
    "efficientnet_b0" : ("efficientnet_b0",         5.3),
    "mobilenet_v3"    : ("mobilenetv3_small_100",   2.5),
}


def build_model(
    name: str,
    num_classes: int,
    pretrained: bool = True,
    dropout: float = 0.3,
) -> nn.Module:
    """
    用 timm 建立模型並換掉 classifier head。
    dropout 加在 classifier 前，幫助小資料集防 overfit。
    """
    if name not in MODELS:
        raise ValueError(f"未知模型 {name}，選項：{list(MODELS.keys())}")

    timm_name, param_m = MODELS[name]
    model = timm.create_model(
        timm_name,
        pretrained=pretrained,
        num_classes=0,          # 先移除 head
    )

    # 取得 feature dim
    with torch.no_grad():
        dummy = torch.zeros(1, 3, 224, 224)
        feat_dim = model(dummy).shape[-1]

    # 換上自訂 head
    model.head = nn.Sequential(
        nn.Dropout(p=dropout),
        nn.Linear(feat_dim, num_classes),
    )
    # timm 的 head 名稱依模型而異，統一設定
    if hasattr(model, "classifier"):
        model.classifier = model.head
    elif hasattr(model, "head"):
        pass  # 已設定

    print(f"[Model] {name}  params≈{param_m}M  feat_dim={feat_dim}  "
          f"num_classes={num_classes}")
    return model


def count_params(model: nn.Module) -> str:
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return f"Total: {total/1e6:.2f}M  Trainable: {trainable/1e6:.2f}M"
