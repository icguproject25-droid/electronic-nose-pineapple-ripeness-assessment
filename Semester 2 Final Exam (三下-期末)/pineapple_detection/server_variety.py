import json
from pathlib import Path
from io import BytesIO

import cv2
import numpy as np
import torch
from PIL import Image, ImageOps
from torchvision import transforms
from flask import Flask, request, jsonify
from ultralytics import YOLO

from models import build_model


# =========================
# 基本設定
# =========================

YOLO_PATH       = Path("weights/yolov8n_pineapple_best.pt")
CLASS_CKPT_PATH = Path("weights/b0_focal_best.pth")
CLASS_PATH      = Path("class_names.json")

MODEL_NAME = "efficientnet_b0"
DEVICE     = torch.device("cpu")

DETECT_CONF_THRES = 0.05   # 降低門檻，避免漏偵測俯拍角度

ZH_NAMES = {
    "jinzuan"   : "金鑽鳳梨",
    "local"     : "土鳳梨",
    "milk"      : "牛奶鳳梨",
    "watermelon": "西瓜鳳梨",
}


# =========================
# Flask App
# =========================

app = Flask(__name__)


# =========================
# 載入類別名稱
# =========================

if not CLASS_PATH.exists():
    raise FileNotFoundError(f"找不到類別檔：{CLASS_PATH}")

with open(CLASS_PATH, "r", encoding="utf-8") as f:
    class_names = json.load(f)


# =========================
# 載入 YOLO 偵測模型
# =========================

if not YOLO_PATH.exists():
    raise FileNotFoundError(f"找不到 YOLO 權重：{YOLO_PATH}")

detector = YOLO(str(YOLO_PATH))
print("[OK] YOLO detector loaded:", YOLO_PATH)


# =========================
# 載入 EfficientNet-B0 分類模型
# =========================

if not CLASS_CKPT_PATH.exists():
    raise FileNotFoundError(f"找不到分類權重：{CLASS_CKPT_PATH}")

classifier = build_model(MODEL_NAME, num_classes=len(class_names))

checkpoint = torch.load(CLASS_CKPT_PATH, map_location=DEVICE)

if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
    classifier.load_state_dict(checkpoint["model_state_dict"])
elif isinstance(checkpoint, dict) and "state_dict" in checkpoint:
    classifier.load_state_dict(checkpoint["state_dict"])
else:
    classifier.load_state_dict(checkpoint)

classifier.to(DEVICE)
classifier.eval()

print("[OK] Classifier loaded:", CLASS_CKPT_PATH)
print("[INFO] Classes:", class_names)


# =========================
# 品種分類前處理（對齊原本 valid/test transform）
# =========================

base_transform = transforms.Compose([
    transforms.Resize(int(224 * 1.14)),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225],
    ),
])


# =========================
# Stage 1：照片內容檢查
# =========================

def check_image_has_content(image: Image.Image):
    img_rgb = np.array(image.convert("RGB"))
    gray    = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)

    mean_brightness = float(np.mean(gray))
    std_brightness  = float(np.std(gray))
    edges           = cv2.Canny(gray, 50, 150)
    edge_ratio      = float(np.mean(edges > 0))

    too_dark      = mean_brightness < 20
    too_bright    = mean_brightness > 245
    too_flat      = std_brightness < 8
    too_few_edges = edge_ratio < 0.003

    has_content = not (too_dark or too_bright or too_flat or too_few_edges)

    if too_dark:
        message = "照片太暗，無法判斷是否有物體。"
    elif too_bright:
        message = "照片太亮，無法判斷是否有物體。"
    elif too_flat:
        message = "照片畫面過於單一，可能沒有明顯物體。"
    elif too_few_edges:
        message = "照片中沒有明顯邊緣或物體輪廓。"
    else:
        message = "照片中有明顯內容，可以進入鳳梨偵測。"

    return {
        "has_content"    : has_content,
        "message"        : message,
        "mean_brightness": mean_brightness,
        "std_brightness" : std_brightness,
        "edge_ratio"     : edge_ratio,
    }


# =========================
# Stage 2：YOLO 偵測鳳梨
# =========================

def detect_pineapple(image: Image.Image):
    results = detector.predict(
        image,
        imgsz=640,
        conf=DETECT_CONF_THRES,
        verbose=False,
    )

    if not results or results[0].boxes is None or len(results[0].boxes) == 0:
        return None

    boxes     = results[0].boxes.xyxy.cpu().numpy()
    confs     = results[0].boxes.conf.cpu().numpy()
    num_boxes = len(boxes)

    # 選面積最大的框
    best_idx, best_area = 0, -1
    for i, box in enumerate(boxes):
        x1, y1, x2, y2 = box
        area = max(0, x2 - x1) * max(0, y2 - y1)
        if area > best_area:
            best_area = area
            best_idx  = i

    x1, y1, x2, y2 = boxes[best_idx]
    conf = float(confs[best_idx])

    return {
        "bbox"      : [float(x1), float(y1), float(x2), float(y2)],
        "confidence": conf,
        "area"      : float(best_area),
        "num_boxes" : num_boxes,
    }


# =========================
# Stage 3：品種分類（使用原始完整圖片）
# YOLO 只當守門員，分類模型用完整圖，不受 crop 影響
# =========================

def classify_pineapple(image: Image.Image):
    image = image.convert("RGB")

    # TTA × 5
    tta_images = [
        image,
        ImageOps.mirror(image),
        ImageOps.flip(image),
        image.rotate(5),
        image.rotate(-5),
    ]

    probs_list = []
    with torch.no_grad():
        for img in tta_images:
            x = base_transform(img).unsqueeze(0).to(DEVICE)
            probs = torch.softmax(classifier(x), dim=1)[0].cpu().numpy()
            probs_list.append(probs)

    avg_probs  = np.mean(probs_list, axis=0)
    pred_idx   = int(np.argmax(avg_probs))
    pred_name  = class_names[pred_idx]
    confidence = float(avg_probs[pred_idx])

    all_probs = [
        {
            "class"      : name,
            "zh_name"    : ZH_NAMES.get(name, name),
            "probability": float(p),
        }
        for name, p in zip(class_names, avg_probs)
    ]

    return {
        "pred_class"    : pred_name,
        "pred_zh_name"  : ZH_NAMES.get(pred_name, pred_name),
        "confidence"    : confidence,
        "low_confidence": confidence < 0.65,
        "all_probs"     : all_probs,
    }


# =========================
# 首頁
# =========================

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status" : "ok",
        "message": "Three-stage pineapple server is running.",
        "stages" : [
            "Stage 1: check image has visible content",
            "Stage 2: YOLOv8n detect pineapple (gatekeeper only)",
            "Stage 3: EfficientNet-B0 classify variety (full image)",
        ],
        "detector"             : str(YOLO_PATH),
        "classifier"           : str(CLASS_CKPT_PATH),
        "detect_conf_threshold": DETECT_CONF_THRES,
        "classes"              : class_names,
    })


# =========================
# 推論 API
# =========================

@app.route("/predict", methods=["POST"])
def predict():
    if "image" not in request.files:
        return jsonify({
            "status" : "error",
            "message": "No image uploaded. Field name must be 'image'.",
        }), 400

    file = request.files["image"]

    try:
        image = Image.open(BytesIO(file.read())).convert("RGB")

        # ── Stage 1 ──────────────────────────────────────
        content_result = check_image_has_content(image)

        if not content_result["has_content"]:
            return jsonify({
                "status"        : "ok",
                "filename"      : file.filename,
                "stage"         : 1,
                "has_content"   : False,
                "is_pineapple"  : False,
                "message"       : content_result["message"],
                "content_check" : content_result,
                "det_confidence": 0.0,
                "bbox"          : None,
                "pred_class"    : None,
                "pred_zh_name"  : "照片中未偵測到明顯物體",
                "confidence"    : 0.0,
                "low_confidence": True,
                "all_probs"     : [],
            })

        # ── Stage 2 ──────────────────────────────────────
        detect_result = detect_pineapple(image)

        if detect_result is None:
            return jsonify({
                "status"        : "ok",
                "filename"      : file.filename,
                "stage"         : 2,
                "has_content"   : True,
                "is_pineapple"  : False,
                "message"       : "照片中有明顯內容，但未偵測到鳳梨，請重新拍攝或確認照片內容。",
                "content_check" : content_result,
                "det_confidence": 0.0,
                "bbox"          : None,
                "pred_class"    : None,
                "pred_zh_name"  : "未偵測到鳳梨",
                "confidence"    : 0.0,
                "low_confidence": True,
                "all_probs"     : [],
            })

        # ── 多顆鳳梨提醒 ──────────────────────────────────
        if detect_result["num_boxes"] > 3:
            return jsonify({
                "status"        : "ok",
                "filename"      : file.filename,
                "stage"         : 2,
                "has_content"   : True,
                "is_pineapple"  : True,
                "message"       : "偵測到多顆鳳梨，請一次拍攝一顆鳳梨以提高品種辨識準確度。",
                "content_check" : content_result,
                "det_confidence": detect_result["confidence"],
                "bbox"          : detect_result["bbox"],
                "num_boxes"     : detect_result["num_boxes"],
                "pred_class"    : None,
                "pred_zh_name"  : "偵測到多顆鳳梨",
                "confidence"    : 0.0,
                "low_confidence": True,
                "all_probs"     : [],
            })

        # ── Stage 3：用完整圖片分類（不 crop）────────────
        class_result = classify_pineapple(image)

        return jsonify({
            "status"        : "ok",
            "filename"      : file.filename,
            "stage"         : 3,
            "has_content"   : True,
            "is_pineapple"  : True,
            "message"       : "照片中有明顯內容，已偵測到鳳梨，並完成品種分類。",
            "content_check" : content_result,
            "det_confidence": detect_result["confidence"],
            "bbox"          : detect_result["bbox"],
            "num_boxes"     : detect_result["num_boxes"],
            **class_result,
        })

    except Exception as e:
        return jsonify({
            "status" : "error",
            "message": str(e),
        }), 500


# =========================
# Main
# =========================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)
