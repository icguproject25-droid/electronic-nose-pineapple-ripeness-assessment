# 🍍 鳳梨偵測 + 品種分類 兩階段 Pipeline

## 專案結構

```
pineapple_detection/
├── src/
│   ├── prepare_yolo_data.py   # Step 0：解壓 dataset
│   ├── train_yolo.py          # Step 1：訓練 YOLOv8n
│   ├── evaluate_yolo.py       # Step 2：評估偵測模型
│   ├── pipeline.py            # Step 3：兩階段推論
│   └── predict.py             # 給朋友用的獨立腳本
├── requirements.txt
└── README.md
```

---

## 環境安裝

```bash
pip install -r requirements.txt
```

---

## 完整執行流程

### Step 0：準備資料
把 `Pineapple_v1i_yolov8.zip` 放在根目錄：
```bash
python src/prepare_yolo_data.py
```

### Step 1：訓練 YOLOv8n
```bash
python src/train_yolo.py
```
最佳權重 → `outputs/yolov8n_pineapple_best.pt`

### Step 2：評估偵測模型
```bash
python src/evaluate_yolo.py
```

### Step 3：兩階段推論（偵測 + 分類）
需要把之前品種分類的權重 `b0_focal_best.pth` 放到 `outputs/`：
```bash
# 單張圖推論
python src/pipeline.py --image photo.jpg

# 推論 + 儲存標註圖
python src/pipeline.py --image photo.jpg --save

# 關閉 TTA（速度快但準確率稍低）
python src/pipeline.py --image photo.jpg --no-tta
```

---

## 給朋友的說明（只有權重，不重新訓練）

1. 安裝環境：`pip install -r requirements.txt`
2. 建立 `weights/` 資料夾，放入：
   - `yolov8n_pineapple_best.pt`（YOLOv8 偵測權重）
   - `b0_focal_best.pth`（EfficientNet 分類權重）
3. 執行：
```bash
python src/predict.py --image 你的鳳梨照片.jpg --save
```

---

## 系統架構

```
輸入圖片
    ↓
YOLOv8n（偵測有沒有鳳梨）
    → 沒有 → 輸出「未偵測到鳳梨」
    → 有   → crop bounding box（加 10px padding）
    ↓
EfficientNet-B0 Focal + TTA × 5
    ↓
輸出：品種中文名稱 + 信心分數 + 所有品種機率
```

## 資料集說明

| | 偵測 dataset | 分類 dataset |
|---|---|---|
| 來源 | Roboflow（4100張） | 自行收集（270張）|
| 類別 | pineapple（1類）| 4品種 |
| 模型 | YOLOv8n | EfficientNet-B0 |
| 最佳準確率 | mAP@50 ~86% | 88.9%（TTA 92.6%）|
