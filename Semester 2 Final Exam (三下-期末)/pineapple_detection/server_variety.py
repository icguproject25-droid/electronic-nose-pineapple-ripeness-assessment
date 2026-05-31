# 匯入 json，主要用來讀 class_names.json，以及回傳 JSON 結果
import json

# Path 可以比較方便處理檔案路徑，例如模型權重和類別檔
from pathlib import Path

# BytesIO 用來把上傳圖片的 bytes 轉成 PIL 可以讀的格式
from io import BytesIO

# cv2 主要用在照片內容檢查，例如轉灰階、Canny 邊緣偵測
import cv2

# numpy 用來計算亮度平均、標準差、機率平均等數值
import numpy as np

# torch 是 PyTorch，這裡用來載入 EfficientNet 分類模型並做推論
import torch

# PIL 用來讀取與處理圖片；ImageOps 用在 TTA 的水平/垂直翻轉
from PIL import Image, ImageOps

# torchvision transforms 是分類模型前處理，需和訓練時 valid/test transform 對齊
from torchvision import transforms

# Flask 負責建立 API server；request 讀取上傳檔案；jsonify 回傳 JSON
from flask import Flask, request, jsonify

# YOLO 用來載入 ultralytics YOLOv8n 鳳梨偵測模型
from ultralytics import YOLO

# 從自己的 models.py 匯入 build_model，用來建立 EfficientNet-B0 分類模型
from models import build_model


# =========================
# 基本設定
# =========================

# YOLO 鳳梨偵測模型權重位置
YOLO_PATH       = Path("weights/yolov8n_pineapple_best.pt")

# EfficientNet-B0 品種分類模型權重位置
CLASS_CKPT_PATH = Path("weights/b0_focal_best.pth")

# 類別名稱 json，例如 ["jinzuan", "local", "milk", "watermelon"]
CLASS_PATH      = Path("class_names.json")

# 分類模型名稱，這裡使用 EfficientNet-B0
MODEL_NAME = "efficientnet_b0"

# Raspberry Pi / VM 這邊先用 CPU 跑，避免沒有 GPU 時出錯
DEVICE     = torch.device("cpu")

# YOLO 偵測信心門檻
# 這裡設比較低，是為了減少俯拍、角度不好時漏偵測鳳梨的情況
DETECT_CONF_THRES = 0.05   # 降低門檻，避免漏偵測俯拍角度

# 英文類別對應中文品種名稱，方便前端或 Flask 頁面直接顯示中文
ZH_NAMES = {
    "jinzuan"   : "金鑽鳳梨",
    "local"     : "土鳳梨",
    "milk"      : "牛奶鳳梨",
    "watermelon": "西瓜鳳梨",
}


# =========================
# Flask App
# =========================

# 建立 Flask app，後面會用 route 定義首頁和 /predict API
app = Flask(__name__)


# =========================
# 載入類別名稱
# =========================

# 先確認 class_names.json 是否存在，避免後面模型輸出不知道對應哪個品種
if not CLASS_PATH.exists():
    raise FileNotFoundError(f"找不到類別檔：{CLASS_PATH}")

# 讀取類別名稱，後面分類結果會用 index 對應到這些名稱
with open(CLASS_PATH, "r", encoding="utf-8") as f:
    class_names = json.load(f)


# =========================
# 載入 YOLO 偵測模型
# =========================

# 確認 YOLO 權重是否存在
if not YOLO_PATH.exists():
    raise FileNotFoundError(f"找不到 YOLO 權重：{YOLO_PATH}")

# 載入 YOLOv8n 鳳梨偵測模型
# 這個模型只負責判斷圖片中有沒有鳳梨，以及抓出鳳梨框
detector = YOLO(str(YOLO_PATH))
print("[OK] YOLO detector loaded:", YOLO_PATH)


# =========================
# 載入 EfficientNet-B0 分類模型
# =========================

# 確認品種分類模型權重是否存在
if not CLASS_CKPT_PATH.exists():
    raise FileNotFoundError(f"找不到分類權重：{CLASS_CKPT_PATH}")

# 依照類別數建立分類模型
classifier = build_model(MODEL_NAME, num_classes=len(class_names))

# 載入訓練好的模型權重，map_location=CPU 代表即使沒有 GPU 也可以跑
checkpoint = torch.load(CLASS_CKPT_PATH, map_location=DEVICE)

# 不同訓練程式存模型的 key 可能不一樣，所以這裡做幾種格式相容
if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
    classifier.load_state_dict(checkpoint["model_state_dict"])
elif isinstance(checkpoint, dict) and "state_dict" in checkpoint:
    classifier.load_state_dict(checkpoint["state_dict"])
else:
    classifier.load_state_dict(checkpoint)

# 把模型放到指定裝置，這裡是 CPU
classifier.to(DEVICE)

# 設成 eval 模式，避免 dropout / batchnorm 影響推論結果
classifier.eval()

print("[OK] Classifier loaded:", CLASS_CKPT_PATH)
print("[INFO] Classes:", class_names)


# =========================
# 品種分類前處理（對齊原本 valid/test transform）
# =========================

# 這段前處理要和訓練時驗證/測試的 transform 對齊
# 圖片先 resize，再 center crop 成 224x224，最後轉 tensor 並做 ImageNet normalize
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
    # 先把圖片轉成 RGB numpy array，方便給 OpenCV 處理
    img_rgb = np.array(image.convert("RGB"))

    # 轉成灰階，後面用來算亮度和邊緣
    gray    = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)

    # 計算平均亮度，用來判斷圖片是不是太暗或太亮
    mean_brightness = float(np.mean(gray))

    # 計算亮度標準差，太低代表整張圖可能很平、沒有明顯內容
    std_brightness  = float(np.std(gray))

    # 用 Canny 找邊緣，判斷圖片裡有沒有明顯物體輪廓
    edges           = cv2.Canny(gray, 50, 150)

    # edge_ratio 代表邊緣像素比例，太低代表可能沒什麼物體
    edge_ratio      = float(np.mean(edges > 0))

    # 以下是一些簡單的圖片品質判斷條件
    too_dark      = mean_brightness < 20
    too_bright    = mean_brightness > 245
    too_flat      = std_brightness < 8
    too_few_edges = edge_ratio < 0.003

    # 只要符合上面任一種問題，就先判定這張圖內容不足
    has_content = not (too_dark or too_bright or too_flat or too_few_edges)

    # 根據不同狀況回傳比較好懂的提示訊息
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

    # 回傳檢查結果與一些數值，前端也可以拿來 debug 或顯示
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
    # 使用 YOLO 模型偵測圖片中的鳳梨
    # imgsz=640 是 YOLO 推論尺寸，conf 使用前面設定的低門檻
    results = detector.predict(
        image,
        imgsz=640,
        conf=DETECT_CONF_THRES,
        verbose=False,
    )

    # 如果完全沒有偵測框，就代表沒有找到鳳梨
    if not results or results[0].boxes is None or len(results[0].boxes) == 0:
        return None

    # 取出所有偵測框座標、信心分數，以及偵測到的框數
    boxes     = results[0].boxes.xyxy.cpu().numpy()
    confs     = results[0].boxes.conf.cpu().numpy()
    num_boxes = len(boxes)

    # 選面積最大的框
    # 因為主要希望一次辨識一顆鳳梨，所以取最大的鳳梨框當主要物件
    best_idx, best_area = 0, -1
    for i, box in enumerate(boxes):
        x1, y1, x2, y2 = box
        area = max(0, x2 - x1) * max(0, y2 - y1)
        if area > best_area:
            best_area = area
            best_idx  = i

    # 取出最佳框的座標與信心分數
    x1, y1, x2, y2 = boxes[best_idx]
    conf = float(confs[best_idx])

    # 回傳偵測結果，bbox 可以給前端畫框使用
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
    # 分類模型需要 RGB 圖片
    image = image.convert("RGB")

    # TTA × 5
    # Test-Time Augmentation：同一張圖片做幾種簡單變化後平均結果
    # 這樣可以讓分類結果比較穩一點
    tta_images = [
        image,
        ImageOps.mirror(image),
        ImageOps.flip(image),
        image.rotate(5),
        image.rotate(-5),
    ]

    # 收集每個 TTA 圖片的預測機率
    probs_list = []

    # 推論時不需要計算梯度，可以省記憶體和加快速度
    with torch.no_grad():
        for img in tta_images:
            # 套用前處理，並增加 batch 維度
            x = base_transform(img).unsqueeze(0).to(DEVICE)

            # 模型輸出 logits，softmax 後轉成各品種機率
            probs = torch.softmax(classifier(x), dim=1)[0].cpu().numpy()
            probs_list.append(probs)

    # 將五次 TTA 的機率平均，當作最後分類機率
    avg_probs  = np.mean(probs_list, axis=0)

    # 找出最高機率的類別
    pred_idx   = int(np.argmax(avg_probs))
    pred_name  = class_names[pred_idx]
    confidence = float(avg_probs[pred_idx])

    # 整理所有類別的機率，方便前端顯示每一類分數
    all_probs = [
        {
            "class"      : name,
            "zh_name"    : ZH_NAMES.get(name, name),
            "probability": float(p),
        }
        for name, p in zip(class_names, avg_probs)
    ]

    # low_confidence 用來提醒分類信心不足，前端可以顯示警告
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
    # 首頁不做推論，只回傳目前 server 狀態與模型資訊
    # 這樣可以用瀏覽器或 curl 確認 API 是否有成功啟動
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
    # 檢查使用者有沒有用 image 這個欄位上傳圖片
    if "image" not in request.files:
        return jsonify({
            "status" : "error",
            "message": "No image uploaded. Field name must be 'image'.",
        }), 400

    # 取出上傳的圖片檔案
    file = request.files["image"]

    try:
        # 將上傳圖片讀成 PIL Image，並統一轉成 RGB
        image = Image.open(BytesIO(file.read())).convert("RGB")

        # ── Stage 1 ──────────────────────────────────────
        # 第一階段：先檢查照片是否真的有內容
        # 如果太暗、太亮、太平或沒有邊緣，就不進入 YOLO
        content_result = check_image_has_content(image)

        if not content_result["has_content"]:
            # 圖片內容不足時，直接回傳，不做鳳梨偵測和品種分類
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
        # 第二階段：用 YOLO 判斷圖片中是否有鳳梨
        detect_result = detect_pineapple(image)

        if detect_result is None:
            # 圖片有內容，但 YOLO 沒有偵測到鳳梨
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
        # 如果偵測到太多顆鳳梨，就提醒使用者一次拍一顆
        # 這樣可以避免分類模型不知道要看哪一顆
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
        # 第三階段：通過前兩關後，再使用 EfficientNet-B0 分類品種
        # 這裡刻意使用完整圖片，不使用 YOLO crop，避免 crop 影響品種特徵
        class_result = classify_pineapple(image)

        # 最後把三階段結果全部整理成 JSON 回傳給前端或 App
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
        # 如果圖片讀取、模型推論或其他地方出錯，就回傳 error 給前端
        return jsonify({
            "status" : "error",
            "message": str(e),
        }), 500


# =========================
# Main
# =========================

if __name__ == "__main__":
    # 啟動 Flask server
    # host=0.0.0.0 代表同一個區域網路的其他裝置也可以連到這台 server
    # port=5001 是照片品種辨識 API 使用的連接埠
    app.run(host="0.0.0.0", port=5001, debug=False)
