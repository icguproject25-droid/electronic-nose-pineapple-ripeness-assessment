"""
predict.py  ── 給朋友用的單張推論腳本
--------------------------------------
不需要重新訓練，直接用訓練好的權重推論。

前置需求：
  pip install ultralytics torch torchvision timm pillow

執行範例：
  python predict.py --image 我的鳳梨.jpg
  python predict.py --image 我的鳳梨.jpg --save
  python predict.py --image 我的鳳梨.jpg --no-tta   # 快速模式
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
# 請把以下路徑改成你收到的權重檔位置
DET_CKPT = "weights/yolov8n_pineapple_best.pt"   # YOLOv8 偵測權重
CLS_CKPT = "weights/b0_focal_best.pth"            # 分類權重
# ══════════════════════════════════════════

CLASSES    = ["jinzuan", "local", "milk", "watermelon"]
NAMES_ZH   = {"jinzuan": "金鑽鳳梨", "local": "土鳳梨",
               "milk": "牛奶鳳梨", "watermelon": "西瓜鳳梨"}
COLORS     = {"jinzuan": (255,180,0), "local": (80,200,80),
              "milk": (100,180,255), "watermelon": (255,80,80)}
DET_CONF   = 0.35
TTA_N      = 5


def build_cls_model(ckpt_path, device):
    """重建 EfficientNet-B0 分類模型並載入權重"""
    model = timm.create_model("efficientnet_b0", pretrained=False, num_classes=0)
    feat_dim = 1280
    model.head = nn.Sequential(
        nn.Dropout(p=0.3),
        nn.Linear(feat_dim, 4),
    )
    model.load_state_dict(torch.load(ckpt_path, map_location=device))
    model.to(device).eval()
    return model


@torch.no_grad()
def classify(crop, model, device, use_tta):
    mean, std = [0.485,0.456,0.406], [0.229,0.224,0.225]
    if use_tta:
        tf = transforms.Compose([
            transforms.RandomResizedCrop(224, scale=(0.8,1.0)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomVerticalFlip(),
            transforms.ColorJitter(0.2,0.2,0.2),
            transforms.ToTensor(),
            transforms.Normalize(mean, std),
        ])
        acc = None
        for _ in range(TTA_N):
            p = F.softmax(model(tf(crop).unsqueeze(0).to(device)), dim=1).cpu()
            acc = p if acc is None else acc + p
        probs = (acc / TTA_N).squeeze(0)
    else:
        tf = transforms.Compose([
            transforms.Resize(256), transforms.CenterCrop(224),
            transforms.ToTensor(), transforms.Normalize(mean, std),
        ])
        probs = F.softmax(model(tf(crop).unsqueeze(0).to(device)), dim=1).squeeze(0).cpu()

    conf, idx = probs.max(0)
    return CLASSES[idx.item()], conf.item(), probs.numpy()


def predict(image_path, save=False, use_tta=True):
    device = torch.device("cpu")

    print("載入模型...")
    det = YOLO(DET_CKPT)
    cls = build_cls_model(CLS_CKPT, device)
    print("完成！\n")

    img = Image.open(image_path).convert("RGB")
    W, H = img.size
    t0   = time.time()

    res   = det(img, conf=DET_CONF, verbose=False)[0]
    boxes = res.boxes

    if not boxes or len(boxes) == 0:
        print("未偵測到鳳梨。")
        return

    print(f"偵測到 {len(boxes)} 個鳳梨\n")
    draw = ImageDraw.Draw(img)

    for i, box in enumerate(boxes):
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        det_conf = box.conf[0].item()
        pad  = 10
        crop = img.crop((max(0,int(x1)-pad), max(0,int(y1)-pad),
                         min(W,int(x2)+pad), min(H,int(y2)+pad)))

        cls_name, cls_conf, all_probs = classify(crop, cls, device, use_tta)
        name_zh = NAMES_ZH[cls_name]
        color   = COLORS[cls_name]

        print(f"  鳳梨 #{i+1}：{name_zh}  信心 {cls_conf*100:.1f}%")
        for cn, p in zip(CLASSES, all_probs):
            bar = "█" * int(p * 20)
            print(f"    {NAMES_ZH[cn]:6s}  {bar:20s}  {p*100:.1f}%")
        print()

        if save:
            draw.rectangle([x1,y1,x2,y2], outline=color, width=3)
            label = f"{name_zh} {cls_conf*100:.0f}%"
            draw.rectangle([x1, y1-24, x1+len(label)*9, y1], fill=color)
            draw.text((x1+4, y1-20), label, fill=(255,255,255))

    print(f"總耗時：{(time.time()-t0)*1000:.0f}ms")

    if save:
        out = Path("result_" + Path(image_path).name)
        img.save(out)
        print(f"結果圖儲存 → {out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image",  required=True)
    parser.add_argument("--save",   action="store_true")
    parser.add_argument("--no-tta", action="store_true")
    args = parser.parse_args()
    predict(args.image, save=args.save, use_tta=not args.no_tta)
