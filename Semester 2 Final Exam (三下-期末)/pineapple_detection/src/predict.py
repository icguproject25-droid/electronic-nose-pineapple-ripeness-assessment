"""
predict.py  ── 給朋友或同學用的單張推論腳本
----------------------------------------------
不需要重新訓練，只要有兩個權重檔就可以直接推論。

前置需求：
  pip install ultralytics torch torchvision timm pillow

執行範例：
  python predict.py --image 我的鳳梨.jpg              # 基本推論
  python predict.py --image 我的鳳梨.jpg --save       # 儲存標注圖
  python predict.py --image 我的鳳梨.jpg --no-tta     # 快速模式（不做 TTA）

輸出範例：
  偵測到 1 個鳳梨
    鳳梨 #1：金鑽鳳梨  信心 91.2%
      金鑽鳳梨  ████████████████████  91.2%
      土鳳梨    ██                     4.0%
      牛奶鳳梨  █                      3.1%
      西瓜鳳梨  ▏                      1.7%
"""

import argparse
import time
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import transforms
from ultralytics import YOLO
from PIL import Image, ImageDraw
import timm


# ══════════════════════════════════════════
# 權重檔路徑：把這兩個檔案放到 weights/ 資料夾下
# ══════════════════════════════════════════
DET_CKPT = "weights/yolov8n_pineapple_best.pt"   # YOLOv8n 鳳梨偵測權重
CLS_CKPT = "weights/b0_focal_best.pth"            # EfficientNet-B0 品種分類權重
# ══════════════════════════════════════════

# 四個品種的類別名稱，順序必須和訓練時完全一致
CLASSES  = ["jinzuan", "local", "milk", "watermelon"]

# 英文代碼對應中文品種名稱
NAMES_ZH = {
    "jinzuan"   : "金鑽鳳梨",
    "local"     : "土鳳梨",
    "milk"      : "牛奶鳳梨",
    "watermelon": "西瓜鳳梨",
}

# 標注框顏色，每個品種一個顏色（RGB）
COLORS = {
    "jinzuan"   : (255, 180, 0),    # 金色
    "local"     : (80, 200, 80),    # 綠色
    "milk"      : (100, 180, 255),  # 藍色
    "watermelon": (255, 80, 80),    # 紅色
}

DET_CONF = 0.35   # YOLO 偵測信心門檻，低於此值的框會被捨棄
TTA_N    = 5      # TTA 次數：對同一張圖做幾次隨機增強後平均機率


def build_cls_model(ckpt_path, device):
    """
    重建 EfficientNet-B0 分類模型並載入訓練好的權重。

    這裡不使用 models.py 的 build_model，是為了讓這支腳本可以
    獨立執行，不需要依賴 models.py。

    架構說明：
      - timm 的 EfficientNet-B0 先去掉 head（num_classes=0）
      - feature extractor 輸出 1280 維特徵向量
      - 自訂 head：Dropout(0.3) → Linear(1280 → 4)
      - Dropout 在小資料集（270張）時有防 overfit 效果
    """
    # num_classes=0 → 只保留特徵提取部分，移除原本的 1000 類分類頭
    model = timm.create_model("efficientnet_b0", pretrained=False, num_classes=0)

    # EfficientNet-B0 的特徵維度是 1280
    feat_dim = 1280

    # 換上自訂的 4 類分類頭
    model.head = nn.Sequential(
        nn.Dropout(p=0.3),
        nn.Linear(feat_dim, 4),
    )

    # 載入訓練好的權重，map_location=device 確保沒有 GPU 也能讀取
    model.load_state_dict(torch.load(ckpt_path, map_location=device))
    model.to(device).eval()  # eval() 關閉 Dropout，確保推論結果穩定
    return model


@torch.no_grad()  # 推論不需要反向傳播，關掉梯度計算省記憶體
def classify(crop, model, device, use_tta):
    """
    對一張 crop 圖做品種分類，支援 TTA（Test-Time Augmentation）。

    TTA 原理：
      對同一張圖做隨機翻轉、縮放、色彩抖動等變化，
      跑多次推論後對機率取平均，讓結果比只跑一次更穩定。
      我們做 5 次 TTA，準確率從 88.9% 提升到約 92.6%。

    Args:
        crop    : PIL Image，YOLO 偵測到的鳳梨區域
        model   : 已載入的 EfficientNet 分類模型
        device  : 推論裝置
        use_tta : True 時做 5 次 TTA，False 時只做一次標準推論

    Returns:
        (class_name, confidence, all_probs)
    """
    mean, std = [0.485, 0.456, 0.406], [0.229, 0.224, 0.225]

    if use_tta:
        # TTA transform：每次都有隨機變化
        tf = transforms.Compose([
            transforms.RandomResizedCrop(224, scale=(0.8, 1.0)),  # 隨機縮放裁切
            transforms.RandomHorizontalFlip(),                     # 50% 機率水平翻轉
            transforms.RandomVerticalFlip(),                       # 50% 機率垂直翻轉
            transforms.ColorJitter(0.2, 0.2, 0.2),               # 輕微色彩抖動
            transforms.ToTensor(),
            transforms.Normalize(mean, std),
        ])
        acc = None
        for _ in range(TTA_N):
            # 每次前處理結果不同，累加各次機率
            p = F.softmax(model(tf(crop).unsqueeze(0).to(device)), dim=1).cpu()
            acc = p if acc is None else acc + p
        # 對 TTA_N 次的機率取平均
        probs = (acc / TTA_N).squeeze(0)
    else:
        # 標準推論：固定的 Resize → CenterCrop → 標準化
        tf = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean, std),
        ])
        probs = F.softmax(model(tf(crop).unsqueeze(0).to(device)), dim=1).squeeze(0).cpu()

    # 取最高機率的類別
    conf, idx = probs.max(0)
    return CLASSES[idx.item()], conf.item(), probs.numpy()


def predict(image_path, save=False, use_tta=True):
    """
    對單張圖片執行完整推論流程：
      1. 載入 YOLO 和 EfficientNet 模型
      2. YOLO 偵測圖中的鳳梨框
      3. 對每個框 crop + padding，用 EfficientNet 分類品種
      4. 印出結果，可選擇儲存標注圖

    Args:
        image_path : 輸入圖片路徑（字串或 Path）
        save       : 是否儲存標注結果圖
        use_tta    : 是否開啟 TTA（預設開啟）
    """
    device = torch.device("cpu")  # 沒有 GPU 就用 CPU

    print("載入模型...")
    det = YOLO(DET_CKPT)                          # 載入 YOLO 偵測模型
    cls = build_cls_model(CLS_CKPT, device)       # 載入 EfficientNet 分類模型
    print("完成！\n")

    # 讀取圖片並轉成 RGB（確保不是灰階或 RGBA）
    img  = Image.open(image_path).convert("RGB")
    W, H = img.size
    t0   = time.time()

    # ── Stage 1：YOLO 偵測鳳梨框 ────────────────────────
    res   = det(img, conf=DET_CONF, verbose=False)[0]
    boxes = res.boxes

    if not boxes or len(boxes) == 0:
        print("未偵測到鳳梨。請確認圖片中有鳳梨，或嘗試調低 DET_CONF 門檻。")
        return

    print(f"偵測到 {len(boxes)} 個鳳梨\n")
    draw = ImageDraw.Draw(img)

    # ── Stage 2：對每個框分類品種 ────────────────────────
    for i, box in enumerate(boxes):
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        det_conf = box.conf[0].item()

        # crop 時加一點 padding，避免切掉鳳梨邊緣
        pad  = 10
        crop = img.crop((
            max(0, int(x1) - pad),
            max(0, int(y1) - pad),
            min(W, int(x2) + pad),
            min(H, int(y2) + pad),
        ))

        # 品種分類（含 TTA）
        cls_name, cls_conf, all_probs = classify(crop, cls, device, use_tta)
        name_zh = NAMES_ZH[cls_name]
        color   = COLORS[cls_name]

        # 印出這顆鳳梨的辨識結果
        print(f"  鳳梨 #{i+1}：{name_zh}（{cls_name}）  偵測信心 {det_conf:.2f}  分類信心 {cls_conf*100:.1f}%")
        for cn, p in zip(CLASSES, all_probs):
            # ASCII 進度條：每個 █ 代表 5%
            bar = "█" * int(p * 20)
            print(f"    {NAMES_ZH[cn]:6s}  {bar:20s}  {p*100:.1f}%")
        print()

        # 在圖片上畫標注框和品種標籤
        if save:
            draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
            label = f"{name_zh} {cls_conf*100:.0f}%"
            # 畫標籤背景方塊，讓文字在任何背景下都清楚
            draw.rectangle([x1, y1 - 24, x1 + len(label) * 9, y1], fill=color)
            draw.text((x1 + 4, y1 - 20), label, fill=(255, 255, 255))

    print(f"總耗時：{(time.time()-t0)*1000:.0f}ms")

    # 儲存標注結果圖
    if save:
        out = Path("result_" + Path(image_path).name)
        img.save(out)
        print(f"結果圖儲存 → {out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="鳳梨品種辨識（兩階段推論）")
    parser.add_argument("--image",  required=True,       help="輸入圖片路徑")
    parser.add_argument("--save",   action="store_true", help="儲存標注結果圖")
    parser.add_argument("--no-tta", action="store_true", help="關閉 TTA（快速但準確率稍低）")
    args = parser.parse_args()
    predict(args.image, save=args.save, use_tta=not args.no_tta)
