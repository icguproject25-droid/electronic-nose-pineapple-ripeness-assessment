"""
pipeline.py
-----------
兩階段鳳梨品種辨識推論腳本（本機 CLI 用途，非 Flask API）：

  Stage 1：YOLOv8n 偵測鳳梨（bounding box）
            → 找出圖中每顆鳳梨的位置與偵測信心分數
  Stage 2：EfficientNet-B0 Focal + TTA 辨識品種
            → 對每個 crop 分類為 金鑽 / 土鳳梨 / 牛奶 / 西瓜

使用方式：
  python src/pipeline.py --image path/to/photo.jpg          # 基本推論
  python src/pipeline.py --image path/to/photo.jpg --save   # 儲存標註圖
  python src/pipeline.py --image path/to/photo.jpg --no-tta # 快速模式（關閉 TTA）
"""

import argparse
import time
from pathlib import Path

import torch
import torch.nn.functional as F
from torchvision import transforms
from ultralytics import YOLO
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# 從上層目錄匯入 models.py 的 build_model
import sys
sys.path.append(str(Path(__file__).parent))
from models import build_model


# ══════════════════════════════════════════
# 全域設定，集中管理所有可調整的參數
# ══════════════════════════════════════════
CFG = {
    # Stage 1：YOLOv8 偵測設定
    "det_model"  : "outputs/yolov8n_pineapple_best.pt",  # 訓練好的 YOLO 權重路徑
    "det_conf"   : 0.35,    # 偵測信心門檻：低於此值的框會被捨棄（0~1，越高越嚴格）
    "det_iou"    : 0.45,    # NMS IoU 門檻：兩個框重疊超過此比例就會合併（去除重複框）

    # Stage 2：EfficientNet-B0 分類設定
    "cls_model"  : "outputs/b0_focal_best.pth",          # 訓練好的分類模型權重
    "cls_classes": ["jinzuan", "local", "milk", "watermelon"],  # 類別順序要和訓練時一致
    "cls_names"  : {           # 英文 → 中文品種名稱對照
        "jinzuan"   : "金鑽鳳梨",
        "local"     : "土鳳梨",
        "milk"      : "牛奶鳳梨",
        "watermelon": "西瓜鳳梨",
    },
    "tta_n"      : 5,          # TTA 次數：同一張圖做幾種增強後平均，數字越大越準但越慢
    "device"     : "cpu",      # 推論裝置：沒有 GPU 就用 cpu
}
# ══════════════════════════════════════════

# 每個品種的標注框顏色（RGB）
CLASS_COLORS = {
    "jinzuan"   : (255, 180, 0),    # 金色：金鑽
    "local"     : (80, 200, 80),    # 綠色：土鳳梨
    "milk"      : (100, 180, 255),  # 藍色：牛奶
    "watermelon": (255, 80, 80),    # 紅色：西瓜
}


# ── 分類模型前處理 Transform ──────────────────────────────
def get_cls_transform(tta=False):
    """
    建立分類模型的圖片前處理流程。

    tta=False（一般推論）：Resize → CenterCrop → 標準化
        和訓練時 validation transform 完全對齊，確保推論結果可信。

    tta=True（Test-Time Augmentation）：隨機裁切 + 翻轉 + 色彩抖動
        每次呼叫都會產生略有不同的圖片，多次推論後平均可提升準確率。

    ImageNet 標準化參數（mean/std）是 timm 預訓練模型的標準，不能改。
    """
    mean = [0.485, 0.456, 0.406]
    std  = [0.229, 0.224, 0.225]
    if tta:
        return transforms.Compose([
            transforms.RandomResizedCrop(224, scale=(0.8, 1.0)),  # 隨機縮放裁切
            transforms.RandomHorizontalFlip(),                     # 隨機水平翻轉
            transforms.RandomVerticalFlip(),                       # 隨機垂直翻轉
            transforms.ColorJitter(0.2, 0.2, 0.2),               # 輕微色彩抖動
            transforms.ToTensor(),
            transforms.Normalize(mean, std),
        ])
    return transforms.Compose([
        transforms.Resize(256),       # 先放大到 256，再 crop 到 224（標準做法）
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean, std),
    ])


# ── 載入兩個模型 ────────────────────────────────────────
def load_models(device):
    """
    載入 YOLO 偵測模型和 EfficientNet-B0 分類模型。
    兩個模型都需要在推論前完成載入，否則第一張圖會很慢。
    """
    print("載入模型...")
    det_model = YOLO(CFG["det_model"])

    # pretrained=False：不下載 ImageNet 權重，因為我們會直接載入自己訓練的 checkpoint
    cls_model = build_model("efficientnet_b0", num_classes=4, pretrained=False)
    cls_model.load_state_dict(torch.load(CFG["cls_model"], map_location=device))
    cls_model = cls_model.to(device)
    cls_model.eval()  # 設成 eval 模式，關閉 Dropout 和 BatchNorm 的訓練行為

    print(f"  偵測模型: {CFG['det_model']}")
    print(f"  分類模型: {CFG['cls_model']}")
    return det_model, cls_model


# ── Stage 2：對單一 crop 做品種分類 ──────────────────────
@torch.no_grad()  # 推論不需要計算梯度，省記憶體和加速
def classify_crop(crop_img: Image.Image, cls_model, device, use_tta=True):
    """
    對一張 crop（YOLO 框出的鳳梨區域）進行品種分類。

    use_tta=True 時：
        對同一張圖做 tta_n 次隨機增強，每次取 softmax 機率，
        最後平均，得到更穩定的分類結果（TTA = Test-Time Augmentation）。

    use_tta=False 時：
        只做一次標準前處理，速度快但準確率稍低。

    Returns:
        (cls_name, confidence, all_probs_array)
        cls_name     : 預測品種英文代碼（如 "jinzuan"）
        confidence   : 最高類別的機率（0~1）
        all_probs    : 四個類別的機率陣列，可用來顯示各品種分數
    """
    if use_tta and CFG["tta_n"] > 1:
        tf = get_cls_transform(tta=True)
        probs_sum = None
        for _ in range(CFG["tta_n"]):
            # 每次前處理都會有隨機變化，所以可以累加機率
            t = tf(crop_img).unsqueeze(0).to(device)  # (1, 3, 224, 224)
            p = F.softmax(cls_model(t), dim=1).cpu()
            probs_sum = p if probs_sum is None else probs_sum + p
        # 除以次數取平均
        probs = (probs_sum / CFG["tta_n"]).squeeze(0)
    else:
        tf = get_cls_transform(tta=False)
        t = tf(crop_img).unsqueeze(0).to(device)
        probs = F.softmax(cls_model(t), dim=1).squeeze(0).cpu()

    # 取最高機率的類別作為預測結果
    conf, idx = probs.max(0)
    cls_name  = CFG["cls_classes"][idx.item()]
    return cls_name, conf.item(), probs.numpy()


# ── 主推論流程 ────────────────────────────────────────────
def run_pipeline(image_path: str, det_model, cls_model, device,
                 save=False, use_tta=True):
    """
    對一張圖片執行完整的兩階段推論：YOLO 偵測 → 品種分類。

    Args:
        image_path : 輸入圖片路徑
        det_model  : 已載入的 YOLO 偵測模型
        cls_model  : 已載入的 EfficientNet 分類模型
        device     : 推論裝置（cpu / cuda）
        save       : 是否將標注結果圖存到 outputs/
        use_tta    : 是否開啟 TTA（提升準確率但較慢）

    Returns:
        detections : list of dict，每個元素代表一顆偵測到的鳳梨及其分類結果
    """
    img_path  = Path(image_path)
    img_pil   = Image.open(img_path).convert("RGB")
    img_w, img_h = img_pil.size

    t0 = time.time()

    # ── Stage 1：YOLO 偵測鳳梨框 ─────────────────────────
    det_results = det_model(
        img_pil,
        conf   = CFG["det_conf"],   # 信心門檻
        iou    = CFG["det_iou"],    # NMS IoU 門檻
        device = CFG["device"],
        verbose= False,             # 關閉 YOLO 的詳細輸出
    )[0]

    boxes = det_results.boxes
    t1 = time.time()

    if boxes is None or len(boxes) == 0:
        print(f"\n[結果] 未偵測到鳳梨  ({(t1-t0)*1000:.0f}ms)")
        return []

    print(f"\n[Stage 1] 偵測到 {len(boxes)} 個鳳梨  ({(t1-t0)*1000:.0f}ms)")

    # ── Stage 2：對每個偵測框分類品種 ─────────────────────
    detections = []
    draw = ImageDraw.Draw(img_pil)

    for i, box in enumerate(boxes):
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        det_conf = box.conf[0].item()

        # 在框周圍加一點 padding，讓分類模型看到完整的鳳梨輪廓
        # 不加 padding 可能會把鳳梨邊緣切掉，影響分類準確率
        pad  = 10
        cx1  = max(0, int(x1) - pad)
        cy1  = max(0, int(y1) - pad)
        cx2  = min(img_w, int(x2) + pad)
        cy2  = min(img_h, int(y2) + pad)
        crop = img_pil.crop((cx1, cy1, cx2, cy2))

        # 用 crop 圖做品種分類
        cls_name, cls_conf, all_probs = classify_crop(
            crop, cls_model, device, use_tta=use_tta
        )
        display_name = CFG["cls_names"][cls_name]
        color = CLASS_COLORS[cls_name]

        t2 = time.time()

        # 印出這顆鳳梨的辨識結果
        print(f"\n  鳳梨 #{i+1}")
        print(f"    偵測信心   : {det_conf:.3f}")
        print(f"    品種       : {display_name} ({cls_name})")
        print(f"    分類信心   : {cls_conf:.3f}  ({cls_conf*100:.1f}%)")
        print(f"    所有品種機率:")
        for j, (cn, p) in enumerate(zip(CFG["cls_classes"], all_probs)):
            # 用 ASCII 進度條直觀顯示各品種機率
            bar = "█" * int(p * 20)
            print(f"      {CFG['cls_names'][cn]:8s} {bar:20s} {p*100:.1f}%")

        detections.append({
            "id"          : i + 1,
            "bbox"        : [x1, y1, x2, y2],
            "det_conf"    : det_conf,
            "variety"     : cls_name,
            "variety_zh"  : display_name,
            "cls_conf"    : cls_conf,
            "all_probs"   : {cn: float(p)
                             for cn, p in zip(CFG["cls_classes"], all_probs)},
        })

        # 在圖片上畫標注框和品種標籤
        if save:
            draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
            label = f"{display_name} {cls_conf*100:.0f}%"
            # 畫標籤背景色塊，讓文字更清楚
            draw.rectangle([x1, y1 - 24, x1 + len(label) * 8, y1],
                           fill=color)
            draw.text((x1 + 4, y1 - 20), label,
                      fill=(255, 255, 255))

    total_ms = (time.time() - t0) * 1000
    print(f"\n  總推論時間: {total_ms:.0f}ms")

    # 把標注圖存到 outputs/
    if save:
        out_path = Path("outputs") / f"result_{img_path.stem}.jpg"
        img_pil.save(out_path)
        print(f"  標註圖儲存 → {out_path}")

    return detections


# ── CLI 入口 ─────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="鳳梨偵測 + 品種辨識")
    parser.add_argument("--image",  required=True, help="輸入圖片路徑")
    parser.add_argument("--save",   action="store_true", help="儲存標註結果圖到 outputs/")
    parser.add_argument("--no-tta", action="store_true", help="關閉 TTA（加快速度，準確率稍低）")
    args = parser.parse_args()

    device = torch.device("cpu")
    det_model, cls_model = load_models(device)

    run_pipeline(
        image_path = args.image,
        det_model  = det_model,
        cls_model  = cls_model,
        device     = device,
        save       = args.save,
        use_tta    = not args.no_tta,  # --no-tta 旗標存的是「要不要關閉」，所以取反
    )


if __name__ == "__main__":
    main()
