"""
pipeline.py
-----------
兩階段推論：
  Stage 1：YOLOv8n 偵測鳳梨（bounding box）
  Stage 2：EfficientNet-B0 Focal 辨識品種

使用方式：
  python src/pipeline.py --image path/to/photo.jpg
  python src/pipeline.py --image path/to/photo.jpg --save   # 儲存標註圖
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

# 分類模型（從之前的專案 import）
import sys
sys.path.append(str(Path(__file__).parent))
from models import build_model


# ══════════════════════════════════════════
CFG = {
    # Stage 1
    "det_model"  : "outputs/yolov8n_pineapple_best.pt",
    "det_conf"   : 0.35,       # 偵測信心門檻
    "det_iou"    : 0.45,       # NMS IoU

    # Stage 2
    "cls_model"  : "outputs/b0_focal_best.pth",
    "cls_classes": ["jinzuan", "local", "milk", "watermelon"],
    "cls_names"  : {           # 中文顯示名稱
        "jinzuan"   : "金鑽鳳梨",
        "local"     : "土鳳梨",
        "milk"      : "牛奶鳳梨",
        "watermelon": "西瓜鳳梨",
    },
    "tta_n"      : 5,          # TTA 次數（平衡準確率與速度）
    "device"     : "cpu",
}
# ══════════════════════════════════════════

CLASS_COLORS = {
    "jinzuan"   : (255, 180, 0),
    "local"     : (80, 200, 80),
    "milk"      : (100, 180, 255),
    "watermelon": (255, 80, 80),
}


# ── 分類 Transform ──────────────────────────────────────
def get_cls_transform(tta=False):
    mean = [0.485, 0.456, 0.406]
    std  = [0.229, 0.224, 0.225]
    if tta:
        return transforms.Compose([
            transforms.RandomResizedCrop(224, scale=(0.8, 1.0)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomVerticalFlip(),
            transforms.ColorJitter(0.2, 0.2, 0.2),
            transforms.ToTensor(),
            transforms.Normalize(mean, std),
        ])
    return transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean, std),
    ])


# ── 載入模型 ────────────────────────────────────────────
def load_models(device):
    print("載入模型...")
    det_model = YOLO(CFG["det_model"])

    cls_model = build_model("efficientnet_b0", num_classes=4, pretrained=False)
    cls_model.load_state_dict(torch.load(CFG["cls_model"], map_location=device))
    cls_model = cls_model.to(device)
    cls_model.eval()

    print(f"  偵測模型: {CFG['det_model']}")
    print(f"  分類模型: {CFG['cls_model']}")
    return det_model, cls_model


# ── Stage 2：分類單一 crop ──────────────────────────────
@torch.no_grad()
def classify_crop(crop_img: Image.Image, cls_model, device, use_tta=True):
    if use_tta and CFG["tta_n"] > 1:
        tf = get_cls_transform(tta=True)
        probs_sum = None
        for _ in range(CFG["tta_n"]):
            t = tf(crop_img).unsqueeze(0).to(device)
            p = F.softmax(cls_model(t), dim=1).cpu()
            probs_sum = p if probs_sum is None else probs_sum + p
        probs = (probs_sum / CFG["tta_n"]).squeeze(0)
    else:
        tf = get_cls_transform(tta=False)
        t = tf(crop_img).unsqueeze(0).to(device)
        probs = F.softmax(cls_model(t), dim=1).squeeze(0).cpu()

    conf, idx = probs.max(0)
    cls_name  = CFG["cls_classes"][idx.item()]
    return cls_name, conf.item(), probs.numpy()


# ── 主推論函數 ──────────────────────────────────────────
def run_pipeline(image_path: str, det_model, cls_model, device,
                 save=False, use_tta=True):
    img_path = Path(image_path)
    img_pil  = Image.open(img_path).convert("RGB")
    img_w, img_h = img_pil.size

    t0 = time.time()

    # Stage 1：偵測
    det_results = det_model(
        img_pil,
        conf   = CFG["det_conf"],
        iou    = CFG["det_iou"],
        device = CFG["device"],
        verbose= False,
    )[0]

    boxes = det_results.boxes
    t1 = time.time()

    detections = []

    if boxes is None or len(boxes) == 0:
        print(f"\n[結果] 未偵測到鳳梨  ({(t1-t0)*1000:.0f}ms)")
        return []

    print(f"\n[Stage 1] 偵測到 {len(boxes)} 個鳳梨  ({(t1-t0)*1000:.0f}ms)")

    # Stage 2：對每個 box 做分類
    draw = ImageDraw.Draw(img_pil)

    for i, box in enumerate(boxes):
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        det_conf = box.conf[0].item()

        # crop（加一點 padding 讓分類更準）
        pad  = 10
        cx1  = max(0, int(x1) - pad)
        cy1  = max(0, int(y1) - pad)
        cx2  = min(img_w, int(x2) + pad)
        cy2  = min(img_h, int(y2) + pad)
        crop = img_pil.crop((cx1, cy1, cx2, cy2))

        cls_name, cls_conf, all_probs = classify_crop(
            crop, cls_model, device, use_tta=use_tta
        )
        display_name = CFG["cls_names"][cls_name]
        color = CLASS_COLORS[cls_name]

        t2 = time.time()

        print(f"\n  鳳梨 #{i+1}")
        print(f"    偵測信心   : {det_conf:.3f}")
        print(f"    品種       : {display_name} ({cls_name})")
        print(f"    分類信心   : {cls_conf:.3f}  ({cls_conf*100:.1f}%)")
        print(f"    所有品種機率:")
        for j, (cn, p) in enumerate(zip(CFG["cls_classes"], all_probs)):
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

        # 畫 bounding box
        if save:
            draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
            label = f"{display_name} {cls_conf*100:.0f}%"
            draw.rectangle([x1, y1 - 24, x1 + len(label) * 8, y1],
                           fill=color)
            draw.text((x1 + 4, y1 - 20), label,
                      fill=(255, 255, 255))

    total_ms = (time.time() - t0) * 1000
    print(f"\n  總推論時間: {total_ms:.0f}ms")

    if save:
        out_path = Path("outputs") / f"result_{img_path.stem}.jpg"
        img_pil.save(out_path)
        print(f"  標註圖儲存 → {out_path}")

    return detections


# ── CLI 入口 ────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="鳳梨偵測 + 品種辨識")
    parser.add_argument("--image",  required=True, help="輸入圖片路徑")
    parser.add_argument("--save",   action="store_true", help="儲存標註結果圖")
    parser.add_argument("--no-tta", action="store_true", help="關閉 TTA（加快速度）")
    args = parser.parse_args()

    device = torch.device("cpu")
    det_model, cls_model = load_models(device)

    run_pipeline(
        image_path = args.image,
        det_model  = det_model,
        cls_model  = cls_model,
        device     = device,
        save       = args.save,
        use_tta    = not args.no_tta,
    )


if __name__ == "__main__":
    main()
