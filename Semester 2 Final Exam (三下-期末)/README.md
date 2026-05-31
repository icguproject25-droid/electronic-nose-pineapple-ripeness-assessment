<div align="center">

# 🍍 鳳梨智慧辨識系統 — 期末整合版
### Pineapple Smart Recognition System — Final Exam

*電子鼻成熟度辨識 × 影像品種辨識 × 整合 Web 介面 × 行動 App*

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.1+-000000?style=flat-square&logo=flask&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-ExtraTrees-F7931E?style=flat-square&logo=scikit-learn&logoColor=white)
![YOLOv8](https://img.shields.io/badge/YOLOv8-mAP@50_86%25-00BFFF?style=flat-square)
![EfficientNet](https://img.shields.io/badge/EfficientNet--B0-Acc_92.6%25-8A2BE2?style=flat-square)
![Raspberry Pi](https://img.shields.io/badge/Raspberry_Pi-3_Model_B-A22846?style=flat-square&logo=raspberry-pi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-VM_Backup-2496ED?style=flat-square&logo=docker&logoColor=white)

</div>

---

## 1. 本學期新增功能 What's New

相較於期中版本，期末新增了：

| 功能 | 說明 |
|------|------|
| 影像品種辨識 | YOLOv8 偵測 + EfficientNet-B0 分類，支援四種鳳梨品種 |
| App API Gateway | 行動 App 與網頁的統一 API 中繼服務 |
| 整合 Web 介面 | 一頁切換電子鼻成熟度 + 影像品種辨識兩大功能 |
| 推論校正機制 | 加入空氣防呆、早期熟度校正、過熟傾向提示 |
| Demo 模式完整化 | 可選擇 demo case 與成熟度標籤，無需硬體即可展示 |
| warmup 參數 | 支援 0 / 60 / 180 秒預熱，提升推論準確率 |
| **Docker 備援** | 影像品種辨識部署至學校 VM Docker，比賽現場筆電故障時仍可提供 API |

---

## 2. 系統架構 System Architecture

```
                        ┌──────────────────────────┐
                        │    使用者 / User            │
                        │  瀏覽器 / 手機 App           │
                        └───────────┬──────────────┘
                                    │
                    ┌───────────────▼─────────────────┐
                    │   整合 Web 介面 Port 8000          │
                    │   pineapple_unified_web/app.py   │
                    │   (Raspberry Pi)                 │
                    └──────┬─────────────┬────────────┘
                           │             │
             ┌─────────────▼──┐    ┌─────▼──────────────────┐
             │  電子鼻成熟度   │    │  App Gateway Port 5002  │
             │  Port 5000      │    │  pineapple_app_gateway  │
             │  pineapple_final│    │  (Raspberry Pi)         │
             │  app_local.py   │    └──────────┬─────────────┘
             │  (Raspberry Pi) │               │
             └────────┬────────┘               │
                      │              ┌──────────▼──────────────────────┐
             ┌────────▼────────┐     │  影像辨識 Port 5001              │
             │  inference_30s  │     │  pineapple_detection             │
             │  + calibrate    │     │  server_variety.py               │
             └────────┬────────┘     │                                  │
                      │              │  主要：Windows PC                 │
             ┌────────▼────────┐     │  備援：學校 VM Docker             │
             │  Arduino Mega   │     │        192.168.150.105:5001      │
             │  USB Serial     │     └──────────────────────────────────┘
             │  MQ2/3/9/135    │
             │  TGS2602 / BME  │
             └─────────────────┘
```

**Port 對照表：**

| 服務 | Port | 執行位置（主要） | 備援 | 主程式 |
|------|------|-----------------|------|--------|
| 電子鼻成熟度網頁 | 5000 | Raspberry Pi | — | `pineapple_final/app_local.py` |
| 影像品種辨識 API | 5001 | Windows PC | **學校 VM Docker** | `pineapple_detection/server_variety.py` |
| App API Gateway | 5002 | Raspberry Pi | — | `pineapple_app_gateway/app_gateway_v2.py` |
| 整合 Web 入口 | 8000 | Raspberry Pi | — | `整合網頁/pineapple_unified_web/app.py` |

---

## 3. 子系統說明 Sub-systems

| 資料夾 | 用途 |
|--------|------|
| `pineapple_final/` | **主系統**：電子鼻推論，部署於 Raspberry Pi |
| `pineapple_detection/` | 影像品種辨識伺服器，需較高算力，建議跑在 PC |
| `pineapple_app_gateway/` | App / Web 的 API 中繼，部署於 Raspberry Pi |
| `整合網頁/pineapple_unified_web/` | 整合入口網站，部署於 Raspberry Pi |
| `app/Consumer_pineapple-ripeness-main/` | 消費端 React Native App (Expo) |
| `enose_model_training/` | 模型訓練 Notebook 與部署包（離線使用） |
| `pineapple_deployment_system/` | Arduino 韌體（`use_this/use_this.ino`） |

---

## 4. 硬體需求 Hardware Requirements

| 元件 | 規格 |
|------|------|
| Raspberry Pi 3 Model B | 執行電子鼻推論主系統、Gateway、整合網頁 |
| Arduino Mega 2560 | 感測器訊號擷取，USB 接 RPi |
| MQ-2 / MQ-3 / MQ-9 / MQ-135 | VOC 氣體感測 |
| TGS2602 | 有機溶劑感測 |
| BME280（I²C） | 溫度 / 濕度 / 氣壓 |
| Windows PC（展示時） | 執行影像辨識伺服器（需 GPU 或 CPU PyTorch） |

---

## 5. 軟體需求 Software Requirements

### 5.1 Raspberry Pi（電子鼻主系統）

```
joblib==1.5.3
numpy==2.4.3
pandas==3.0.1
pyserial==3.5
scikit-learn==1.8.0
scipy==1.17.1
```

完整版：`pineapple_final/requirements_rpi.txt`

### 5.2 Raspberry Pi（App Gateway）

```
Flask==3.1.3
requests==2.33.1
```

完整版：`pineapple_app_gateway/requirements_gateway.txt`

### 5.3 PC（影像品種辨識）

```
ultralytics>=8.0.0
torch>=2.0.0
torchvision>=0.15.0
timm>=0.9.0
pillow>=9.0.0
```

完整版：`pineapple_detection/requirements.txt`

### 5.4 整合 Web 介面

```
Flask
```

無獨立 requirements，執行 `pip install flask` 即可。

---

## 6. 安裝 Installation

### 6.1 Arduino 韌體燒錄

1. 開啟 Arduino IDE 2.x
2. 開啟 `pineapple_deployment_system/use_this/use_this.ino`
3. 板子選 **Arduino Mega or Mega 2560**，選正確的 COM Port
4. 點 Upload

### 6.2 電子鼻主系統（Raspberry Pi）

```bash
# 從 PC 上傳到 RPi（取代舊版 pineapple 資料夾）
scp -r pineapple_final pi@<RPi-IP>:/home/pi/pineapple_final

# SSH 進 RPi
ssh pi@<RPi-IP>
cd ~/pineapple_final

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements_rpi.txt
```

### 6.3 App Gateway（Raspberry Pi）

```bash
scp -r pineapple_app_gateway pi@<RPi-IP>:/home/pi/pineapple_app_gateway

# 在 RPi 上
cd ~/pineapple_app_gateway
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements_gateway.txt
```

### 6.4 影像辨識伺服器（Windows PC）

```bash
cd pineapple_detection
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 6.5 整合 Web 介面（Raspberry Pi）

```bash
scp -r 整合網頁/pineapple_unified_web pi@<RPi-IP>:/home/pi/pineapple_unified_web
scp 整合網頁/start_pineapple_system.sh pi@<RPi-IP>:/home/pi/
scp 整合網頁/stop_pineapple_system.sh  pi@<RPi-IP>:/home/pi/

# 在 RPi 上
cd ~/pineapple_unified_web
python3 -m venv .venv
source .venv/bin/activate
pip install flask

chmod +x ~/start_pineapple_system.sh
chmod +x ~/stop_pineapple_system.sh
```

---

## 7. 快速開始 Quick Start

### 7.1 Demo 模式（無硬體，PC 直接執行）

不需 Arduino 或 RPi，用 `demo_data/` 內的預錄資料測試：

```bash
cd pineapple_final
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python app_local_demo_early_corrected_v4.py
# 瀏覽器開啟 http://localhost:5000
```

或用指令列測試特定成熟度：

```bash
# Demo 空氣校正
python calibrate_air_30s.py --demo --demo-case pineapple_03_20260214

# Demo 推論（可換 未熟 / 初熟 / 成熟 / 過熟）
python inference_30s.py --demo --demo-case pineapple_03_20260214 --demo-stage 成熟
```

**Demo 資料對照（`demo_data/` 中已提供）：**

| 鳳梨編號 | 日期 | 可用熟度 |
|----------|------|----------|
| pineapple_03 | 20260203 | 未熟 |
| pineapple_03 | 20260206–08 | 初熟 |
| pineapple_03 | 20260211 | 成熟 |
| pineapple_03 | 20260214 | 過熟 |
| pineapple_10 | 20260208 | 未熟 |
| pineapple_10 | 20260210 | 初熟 |
| pineapple_10 | 20260214 | 成熟 |
| pineapple_11 | 20260208 | 未熟 |
| pineapple_11 | 20260211 | 初熟 |

---

### 7.2 Raspberry Pi 即時偵測（需完整硬體）

```bash
# 在 RPi 上
cd ~/pineapple_final
source .venv/bin/activate

# Step 1：確認 Arduino 有被偵測到
ls /dev/ttyACM* /dev/ttyUSB*
# 應看到 /dev/ttyACM0

# Step 2：空氣基線校正（容器內不放鳳梨）
python calibrate_air_30s.py

# Step 3：放入鳳梨，選擇檢測模式
python inference_30s.py                    # 快速：直接 30 秒
python inference_30s.py --warmup-sec 60    # 標準：預熱 60 秒 + 推論 30 秒
python inference_30s.py --warmup-sec 180   # 完整：預熱 180 秒 + 推論 30 秒
```

---

### 7.3 網頁操作介面（Raspberry Pi Flask）

```bash
cd ~/pineapple_final
source .venv/bin/activate
python app_local.py
```

確認 `app_local.py` 頂部的設定：

```python
RPI_USER = "pi"                           # RPi 帳號
RPI_IP   = "192.168.0.152"               # RPi IP（依實際修改）
RPI_PROJECT_DIR = "/home/pi/pineapple_final"
```

瀏覽器開啟 `http://<RPi-IP>:5000`，頁面提供：快速檢測 / 標準檢測 / 完整檢測 / Demo 模式。

---

### 7.4 影像品種辨識伺服器（Windows PC）

```bash
cd pineapple_detection
.venv\Scripts\activate
python server_variety.py
# 確認終端機顯示 Running on http://0.0.0.0:5001
```

> 必須使用 `host="0.0.0.0"`，才能讓 RPi 連到此服務。

測試單張圖片：

```bash
# 使用 pipeline 腳本
python src/pipeline.py --image test_7.jpg --save

# 或用 curl 呼叫 API
curl -X POST http://localhost:5001/predict -F "file=@test_7.jpg"
```

---

### 7.5 Docker 備援：學校 VM 影像辨識（筆電無法執行時使用）

> **使用時機：** 比賽現場筆電環境不穩、GPU / CPU 無法執行模型時，切換到此備援路徑，App 或網頁改打學校 VM 的 API。

**部署步驟（只需做一次，已部署可跳過）：**

```bash
# 從 PC 上傳整個 pineapple_detection 資料夾到學校 VM
scp -r pineapple_detection csie@192.168.150.105:/home/csie/

# SSH 進 VM
ssh csie@192.168.150.105
cd ~/pineapple_detection

# 建立 Docker image 並啟動
docker compose build
docker compose up -d          # -d 背景執行
```

**確認 Container 狀態：**

```bash
docker ps
# 應看到：
# pineapple-detection   Up X days   0.0.0.0:5001->5001/tcp
```

**確認 API 是否正常：**

```bash
# 在 VM 本機測試
curl http://127.0.0.1:5001
# 應看到：{"message":"Three-stage pineapple server is running.","status":"ok",...}

# 測試推論（換成你的測試圖片）
curl -X POST -F "image=@dataset/valid/images/Pineapple08203_jpg.rf.xxx.jpg" \
  http://127.0.0.1:5001/predict
```

**從外部網路呼叫備援 API：**

```bash
curl -X POST http://192.168.150.105:5001/predict -F "image=@your_pineapple.jpg"
```

切換備援路徑：把 Gateway 或整合網頁中原本指向 Windows PC (`192.168.0.176:5001`) 的 URL 改為 `192.168.150.105:5001`。

**Docker logs 查看：**

```bash
docker logs pineapple-detection
# 正常啟動應包含：
# [OK] YOLO detector loaded: weights/yolov8n_pineapple_best.pt
# [OK] EfficientNet-B0 classifier loaded: weights/b0_focal_best.pth
# Running on http://0.0.0.0:5001
```

---

### 7.6 整合 Web 介面一鍵啟動（Raspberry Pi）

先在 Windows PC 啟動影像辨識伺服器（7.4），再在 RPi 執行：

```bash
~/start_pineapple_system.sh
```

腳本依序啟動三個服務並將 log 寫入 `~/pineapple_logs/`：

```
http://<RPi-IP>:5000   ← 電子鼻成熟度頁
http://<RPi-IP>:5002   ← 照片品種辨識頁
http://<RPi-IP>:8000   ← 整合入口網站
```

瀏覽器開啟 `http://<RPi-IP>:8000` 即可使用完整系統。

停止所有服務：

```bash
~/stop_pineapple_system.sh
```

---

## 8. 輸入 / 輸出格式 Input / Output Format

### 8.1 電子鼻推論

**Arduino Serial 輸出格式（115200 baud）：**

```
timestamp_ms,MQ2_raw,MQ3_raw,MQ9_raw,MQ135_raw,TGS2602_raw,TGS2620_raw,Temp_C,Humidity_pct,Pressure_hPa
```

**模型輸入特徵（11 個 30 秒窗口統計量）：**

```
MQ3_std_norm, MQ3_range_norm, MQ2_MQ3_ratio, MQ3_MQ135_ratio,
MQ9_slope, TGS2602_min_norm, MQ2_auc_norm, MQ2_mean_norm,
MQ9_min_norm, TGS2602_std_norm, MQ9_delta_mean
```

**推論輸出：**

```json
{
  "stage": 2,
  "label": "成熟",
  "raw_prediction": 2,
  "corrected_prediction": 2,
  "overripe_tendency": false,
  "air_guard_triggered": false,
  "probabilities": {
    "未熟": 0.04,
    "初熟": 0.08,
    "成熟": 0.82,
    "過熟": 0.06
  }
}
```

| Stage | 標籤 | 說明 |
|-------|------|------|
| 0 | 未熟 | 果實尚未成熟 |
| 1 | 初熟 | 開始成熟 |
| 2 | 成熟 | 最佳採收期 |
| 3 | 過熟 | 已過熟 |

---

### 8.2 影像品種辨識

**請求：** HTTP POST `http://<PC-IP>:5001/predict`，欄位 `file=<圖片>`

**推論 Pipeline：**

```
輸入圖片
    ↓
YOLOv8n — 偵測有無鳳梨
    → 未偵測到 → {"is_pineapple": false}
    → 偵測到   → crop bounding box（+10px padding）
    ↓
EfficientNet-B0 + TTA × 5
    ↓
輸出品種分類
```

**回應格式：**

```json
{
  "is_pineapple": true,
  "predicted_class": "jinzuan",
  "predicted_label_zh": "金鑽鳳梨",
  "confidence": 0.91,
  "all_probabilities": {
    "jinzuan": 0.91,
    "local": 0.04,
    "milk": 0.03,
    "watermelon": 0.02
  }
}
```

| 類別代碼 | 中文名稱 |
|----------|----------|
| `jinzuan` | 金鑽鳳梨 |
| `local` | 本土種鳳梨 |
| `milk` | 牛奶鳳梨 |
| `watermelon` | 西瓜鳳梨 |

---

## 9. 模型資訊 Model Information

### 9.1 電子鼻成熟度模型

| 項目 | 說明 |
|------|------|
| 演算法 | ExtraTreesClassifier |
| 部署檔案 | `pineapple_final/deploy_student.pkl` |
| 特徵數 | 11 個（30 秒窗口） |
| 訓練資料 | `enose_model_training/orkspace/data/` |
| 主訓練 Notebook | `enose_model_training/orkspace/labeling_perfect_final.ipynb` |

### 9.2 影像品種辨識模型

| 項目 | 說明 |
|------|------|
| 偵測模型 | YOLOv8n，mAP@50 ≈ 86%，訓練資料 4100 張（Roboflow） |
| 分類模型 | EfficientNet-B0（Focal Loss），Acc 88.9%（TTA 92.6%），270 張自行收集 |
| 偵測權重 | `pineapple_detection/weights/yolov8n_pineapple_best.pt` |
| 分類權重 | `pineapple_detection/weights/b0_focal_best.pth` |
| 訓練腳本 | `pineapple_detection/src/train_yolo.py` |

---

## 10. 專案結構 Project Structure

```
Semester 2 Final Exam (三下-期末)/
│
├── pineapple_final/                              # ★ 電子鼻推論主系統
│   ├── inference_30s.py                          # 即時推論（接 Arduino）
│   ├── calibrate_air_30s.py                      # 空氣基線校正
│   ├── app_local.py                              # Flask 網頁介面（含 Demo）
│   ├── app_local_demo_early_corrected_v4.py      # 舊版純 Demo 網頁
│   ├── inference_from_csv_updated.py             # 從 CSV 批次推論
│   ├── debug_features.py                         # 特徵值除錯工具
│   ├── deploy_student.pkl                        # 部署模型
│   ├── deploy_meta.json                          # 模型中繼資料
│   ├── feature_columns.json                      # 特徵欄位定義
│   ├── air_base.json                             # 空氣基線（校正後生成）
│   ├── requirements_rpi.txt
│   └── demo_data/                                # 預錄 Demo 資料（xlsx）
│
├── pineapple_detection/                          # ★ 影像品種辨識
│   ├── server_variety.py                         # Flask API 伺服器 (Port 5001)
│   ├── models.py                                 # EfficientNet-B0 定義
│   ├── class_names.json                          # 品種類別 (4 種)
│   ├── weights/
│   │   ├── yolov8n_pineapple_best.pt             # YOLOv8 偵測權重
│   │   └── b0_focal_best.pth                     # EfficientNet 分類權重
│   ├── src/
│   │   ├── pipeline.py                           # 兩階段推論 pipeline
│   │   ├── predict.py                            # 獨立單張圖片推論
│   │   ├── train_yolo.py                         # YOLOv8 訓練腳本
│   │   └── evaluate_yolo.py                      # 模型評估
│   ├── dataset/                                  # YOLO 格式訓練資料集
│   ├── outputs/                                  # 訓練輸出與評估結果
│   └── requirements.txt
│
├── pineapple_app_gateway/                        # ★ App / Web API Gateway
│   ├── app_gateway_v2.py                         # Gateway 主程式 (Port 5002)
│   ├── app_gateway.py                            # 舊版 Gateway
│   ├── requirements_gateway.txt
│   ├── start_server.sh
│   └── test_2.jpg                                # 測試用圖片
│
├── 整合網頁/                                      # ★ 整合 Web 介面
│   ├── pineapple_unified_web/
│   │   ├── app.py                                # 整合入口 Flask (Port 8000)
│   │   ├── templates/index.html                  # 主頁（含開場動畫、分頁）
│   │   └── static/style.css
│   ├── start_pineapple_system.sh                 # 一鍵啟動三個服務
│   └── stop_pineapple_system.sh                  # 一鍵停止三個服務
│
├── app/
│   └── Consumer_pineapple-ripeness-main/         # 消費端 App (Expo/React Native)
│
├── enose_model_training/                         # 模型訓練工作區
│   └── orkspace/
│       ├── labeling_perfect_final.ipynb          # 主訓練 Notebook
│       ├── data/                                 # 原始感測器資料
│       ├── deploy_rpi_et_30s_noday/              # 生產部署模型包（主要版本）
│       ├── models/ reports/ catboost_info/
│       ├── feature_columns.json
│       └── cutpoints.json
│
└── pineapple_deployment_system/
    └── use_this/use_this.ino                     # Arduino 搭配推論用韌體
```

---

## 11. 正式展示流程 Demo Presentation Flow

```
展示前準備
1. 確認 RPi 與 Windows PC 在同一 Wi-Fi
2. 查 RPi IP：ssh pi@<RPi-IP>，執行 hostname -I

Windows PC（先啟動，主要路徑）
3. cd pineapple_detection && .venv\Scripts\activate
4. python server_variety.py
   → 確認看到 Running on http://0.0.0.0:5001
   ※ 若筆電無法執行，改用 Docker 備援路徑（見下）

Docker 備援路徑（筆電失敗時）
3b. ssh csie@192.168.150.105
    docker ps   # 確認 pineapple-detection Up
    # 若 container 未啟動：
    cd ~/pineapple_detection && docker compose up -d
    # 把 Gateway / 整合網頁的 image API URL 改成 192.168.150.105:5001

Raspberry Pi（接著啟動）
5. ~/start_pineapple_system.sh
   → 等候約 10 秒，確認三個 port 啟動：
   ss -tulnp | grep python  # 應看到 5000, 5002, 8000

展示
6. 瀏覽器開啟 http://<RPi-IP>:8000
7. 分頁一：電子鼻成熟度辨識
   - 先展示 Demo 模式（選不同成熟度 xlsx）
   - 再接 Arduino，執行空氣校正 → 放鳳梨 → 標準檢測
8. 分頁二：照片品種辨識
   - 上傳鳳梨照片，等待辨識結果

展示結束
9. RPi：~/stop_pineapple_system.sh
10. Windows：Ctrl + C 停止 server_variety.py
    （若使用 Docker 備援：docker stop pineapple-detection 或保持執行）
```

---

## 12. 常見問題 Troubleshooting

**Q: 找不到 Arduino（`/dev/ttyACM*` 不存在）**

重新插 USB，並確認 Arduino 已上傳 `use_this.ino`。確認當前使用者有串口權限：

```bash
sudo usermod -a -G dialout $USER
# 重新登入後生效
```

---

**Q: `air_base.json` 找不到或推論觸發空氣防呆**

執行空氣校正，確認容器內沒有鳳梨：

```bash
python calibrate_air_30s.py
```

---

**Q: 整合網頁開啟，但分頁顯示「拒絕連線」**

確認三個服務都在跑：

```bash
ss -tulnp | grep python
# 應看到 5000, 5002, 8000
```

確認 `pineapple_unified_web/app.py` 內的 IP 是 RPi 的 IP，不是 `localhost`。

---

**Q: 照片辨識無法回傳結果**

1. 確認 Windows 端 `server_variety.py` 有啟動且使用 `host="0.0.0.0"`
2. 確認 RPi 與 Windows 在同一網路：`ping <Windows-IP>`
3. 若 Windows IP 改變，更新 Gateway 與整合網頁的 IP 設定

---

**Q: 影像辨識安裝 torch 失敗（無 GPU）**

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

---

**Q: 筆電無法執行影像辨識，如何切換 Docker 備援？**

1. 確認學校 VM 的 Docker container 正在執行：
   ```bash
   ssh csie@192.168.150.105
   docker ps   # 應看到 pineapple-detection Up
   ```
2. 若未執行，啟動它：
   ```bash
   cd ~/pineapple_detection && docker compose up -d
   ```
3. 修改 `pineapple_app_gateway/app_gateway_v2.py` 或整合網頁 `app.py` 中指向影像辨識的 URL，從
   `http://192.168.0.176:5001` 改為 `http://192.168.150.105:5001`，重啟服務。

---

**Q: Docker container 啟動後 API 無回應**

查看 logs 確認模型是否正確載入：

```bash
docker logs pineapple-detection
# 確認有 [OK] YOLO detector loaded 和 [OK] EfficientNet-B0 classifier loaded
```

若 weights 路徑錯誤，確認 `pineapple_detection/weights/` 內有：
- `yolov8n_pineapple_best.pt`
- `b0_focal_best.pth`

---

**Q: `Address already in use`**

```bash
~/stop_pineapple_system.sh
~/start_pineapple_system.sh
```

---

## 13. 系統限制與未來改進 Limitations

| 項目 | 狀態 | 說明 |
|------|------|------|
| 影像辨識需外部機器 | 已有備援 | 主要跑 Windows PC；**學校 VM Docker 作為備援**，筆電故障仍可服務 |
| 整合網頁用 iframe | 現有限制 | 內外頁風格略有差異 |
| IP 硬編碼 | 現有限制 | RPi 或 PC IP 改變時需手動更新設定 |
| Docker 備援需手動切換 | 現有限制 | 目前需手動修改 Gateway URL；未來可加入自動 fallback 邏輯 |

未來可改進方向：Gateway 加入自動偵測 PC 失敗並 fallback 到 Docker VM；將影像模型輕量化部署至 RPi；以真正 API 整合取代 iframe 架構。

---

## 14. 開發團隊 Team Members

長庚大學資訊工程學系

| 學號 | 姓名 |
|------|------|
| B1144143 | 陳玟妤 |
| B1229062 | 林冠妤 |
| B1229066 | 陳怡禎 |
| B1229068 | 廖文歆 |

指導教授：張哲維 教授

---

## 15. 授權 License

本專案採用 [MIT License](../LICENSE) 授權。
