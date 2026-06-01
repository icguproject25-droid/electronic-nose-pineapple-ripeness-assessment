<div align="center">

# 🍍 鳳梨智慧辨識系統 — 期末整合版
### Pineapple Smart Recognition System — Final Exam

*電子鼻成熟度辨識 × 影像品種辨識 × 整合 Web 介面 × 行動 App*

### [🎬 期末 Demo 影片](https://drive.google.com/file/d/1Z_MbwVsv4nYf6GSiNdPcTrRvedTm5LH4/view?usp=drivesdk)

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
| **Docker 備援** | 影像品種辨識部署至學校 VM Docker，支援多人之商用使用(較穩定)，比賽現場筆電故障時仍可提供 API |

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
| `app/Farmer_pineapple-main/` | 農民端 React Native App (Expo)，批次掃描與報表管理 |
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

### 5.5 行動 App

```
Expo Router
TypeScript
Zustand
React Query
react-native-svg
```

---

## 6. 安裝 Installation

### 6.1 Arduino 韌體燒錄

1. 開啟 Arduino IDE 2.x
2. 開啟 `pineapple_deployment_system/use_this/use_this.ino`
3. 板子選 **Arduino Mega or Mega 2560**，選正確的 COM Port
4. 點 Upload

### 6.2 電子鼻主系統（Raspberry Pi）

```bash
scp -r pineapple_final pi@<RPi-IP>:/home/pi/pineapple_final
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

```bash
cd pineapple_final
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python app_local_demo_early_corrected_v4.py
```

### 7.2 Raspberry Pi 即時偵測（需完整硬體）

```bash
cd ~/pineapple_final
source .venv/bin/activate
ls /dev/ttyACM* /dev/ttyUSB*
python calibrate_air_30s.py
python inference_30s.py
python inference_30s.py --warmup-sec 60
python inference_30s.py --warmup-sec 180
```

### 7.3 網頁操作介面（Raspberry Pi Flask）

```bash
cd ~/pineapple_final
source .venv/bin/activate
python app_local.py
```

瀏覽器開啟 `http://<RPi-IP>:5000`。

### 7.4 影像品種辨識伺服器（Windows PC）

```bash
cd pineapple_detection
.venv\Scripts\activate
python server_variety.py
```

### 7.5 Docker 備援：學校 VM 影像辨識

```bash
ssh csie@192.168.150.105
cd ~/pineapple_detection
docker compose build
docker compose up -d
docker ps
```

### 7.6 整合 Web 介面一鍵啟動（Raspberry Pi）

```bash
~/start_pineapple_system.sh
# http://<RPi-IP>:8000
~/stop_pineapple_system.sh
```

---

## 8. 行動 App Mobile Apps

系統整合兩個 Expo / React Native App，分別供農民與消費者使用。兩者皆透過 Wi-Fi 與 Raspberry Pi（或 App Gateway）通訊。

---

### 8.1 農民端 App（Farmer App）

**程式碼路徑：** `app/Farmer_pineapple-main/`  
**參考 Repo：** [`Tinazhen/Farmer_pineapple`](https://github.com/Tinazhen/Farmer_pineapple)

**定位：** 供農民在田間或倉庫操作，管理採收批次、逐批掃描鳳梨、追蹤今日異常數，並匯出報告。

#### 架構

```text
Farmer_pineapple-main/
├── app/                 # Expo Router 頁面
├── components/          # 共用 UI 元件與圖表
├── stores/              # 批次與掃描狀態管理
├── services/            # API 呼叫與後端連線
├── assets/              # 圖片、圖示等靜態資源
├── package.json
└── README.md
```

#### 頁面架構

| 頁面 | 用途 |
|------|------|
| Home | 農民端首頁與批次入口 |
| Batches | 批次管理 |
| Batch Create | 建立批次 |
| Batch Scan | 批次掃描 |
| Batch Summary | 批次摘要 |
| Reports | 報告列表 |
| Settings | 後端 URL 與參數設定 |

#### API 串接

```http
GET  /ping
POST /scan/start
```

#### 安裝與啟動

```bash
cd app/Farmer_pineapple-main
bun install            # 或 npm install
bunx expo start        # 掃 QR code 以 Expo Go 開啟
```

---

### 8.2 消費端 App（Consumer App）

**程式碼路徑：** `app/Consumer_pineapple-ripeness-main/expo/`

**定位：** 供消費者使用，查詢鳳梨品種、提交掃描紀錄並瀏覽歷史記錄。

#### 頁面與功能

| 頁面 | 功能說明 |
|------|----------|
| **首頁 index** | App 入口，進入各主要功能 |
| **掃描流程 processing → result** | 偵測動畫；掃描完成後顯示成熟度結果；可提交人工回饋 |
| **品種介紹 varieties** | 四種鳳梨品種列表；點入 variety-detail 查詳情 |
| **知識庫 knowledge-base** | 鳳梨農業知識文章 |
| **季節指南 seasonal-guide** | 各品種產季與採購建議 |
| **趣味問答 trivia** | 鳳梨趣味小知識卡片 |
| **糖度計算 calculator** | 甜度換算工具 |
| **歷史記錄 history / history-detail** | 過去掃描紀錄列表；單筆詳情頁可補提交人工回饋 |
| **待上傳 pending-uploads** | 離線時暫存的掃描紀錄，連線後批次同步 |
| **操作說明 instruction** | App 使用教學 |

#### API 串接

```http
POST /scan_records
POST /scan_records/{id}/feedback
GET  /scan_records/export.xlsx
```

#### 安裝與啟動

```bash
cd app/Consumer_pineapple-ripeness-main/expo
bun install
bunx expo start
```

---

## 9. 輸入 / 輸出格式 Input / Output Format

### 9.1 電子鼻推論

**Arduino Serial 輸出格式（115200 baud）：**

```text
timestamp_ms,MQ2_raw,MQ3_raw,MQ9_raw,MQ135_raw,TGS2602_raw,TGS2620_raw,Temp_C,Humidity_pct,Pressure_hPa
```

**模型輸入特徵（11 個 30 秒窗口統計量）：**

```text
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

### 9.2 影像品種辨識

**請求：** HTTP POST `http://<PC-IP>:5001/predict`，欄位 `file=<圖片>`

**推論 Pipeline：**

```text
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
  "confidence": 0.91
}
```

---

## 10. 模型資訊 Model Information

### 10.1 電子鼻成熟度模型

| 項目 | 說明 |
|------|------|
| 演算法 | ExtraTreesClassifier |
| 部署檔案 | `pineapple_final/deploy_student.pkl` |
| 特徵數 | 11 個（30 秒窗口） |
| 訓練資料 | `enose_model_training/orkspace/data/` |
| 主訓練 Notebook | `enose_model_training/orkspace/labeling_perfect_final.ipynb` |

### 10.2 影像品種辨識模型

| 項目 | 說明 |
|------|------|
| 偵測模型 | YOLOv8n |
| 分類模型 | EfficientNet-B0 |
| 偵測權重 | `pineapple_detection/weights/yolov8n_pineapple_best.pt` |
| 分類權重 | `pineapple_detection/weights/b0_focal_best.pth` |
| 訓練腳本 | `pineapple_detection/src/train_yolo.py` |

---

## 11. 專案結構 Project Structure

```text
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
│   ├── src/
│   ├── dataset/
│   ├── outputs/
│   └── requirements.txt
│
├── pineapple_app_gateway/                        # ★ App / Web API Gateway
│   ├── app_gateway_v2.py                         # Gateway 主程式 (Port 5002)
│   ├── app_gateway.py                            # 舊版 Gateway
│   ├── requirements_gateway.txt
│   ├── start_server.sh
│   └── test_2.jpg
│
├── 整合網頁/                                      # ★ 整合 Web 介面
│   ├── pineapple_unified_web/
│   │   ├── app.py                                # 整合入口 Flask (Port 8000)
│   │   ├── templates/index.html
│   │   └── static/style.css
│   ├── start_pineapple_system.sh
│   └── stop_pineapple_system.sh
│
├── app/
│   ├── Consumer_pineapple-ripeness-main/         # 消費端 App (Expo/React Native)
│   │   └── expo/
│   └── Farmer_pineapple-main/                    # 農民端 App (Expo/React Native)
│       ├── app/                                  # 頁面路由
│       ├── components/                           # 共用元件與圖表
│       ├── stores/                               # 狀態管理
│       ├── services/                             # API 連線
│       ├── assets/                               # 靜態資源
│       ├── package.json
│       └── README.md
│
├── enose_model_training/                         # 模型訓練工作區
│   └── orkspace/
│       ├── labeling_perfect_final.ipynb
│       ├── data/
│       ├── deploy_rpi_et_30s_noday/
│       ├── models/ reports/ catboost_info/
│       ├── feature_columns.json
│       └── cutpoints.json
│
└── pineapple_deployment_system/
    └── use_this/use_this.ino                     # Arduino 搭配推論用韌體
```

---

## 12. Demo 影片 Demo Video

- [🎬 期末整合 Demo 影片（Google Drive）](https://drive.google.com/file/d/1Z_MbwVsv4nYf6GSiNdPcTrRvedTm5LH4/view?usp=drivesdk)

---

## 13. 正式展示流程 Demo Presentation Flow

```text
展示前準備
1. 確認 RPi 與 Windows PC 在同一 Wi-Fi
2. 查 RPi IP：ssh pi@<RPi-IP>，執行 hostname -I

Windows PC（先啟動，主要路徑）
3. cd pineapple_detection && .venv\Scripts\activate
4. python server_variety.py

Docker 備援路徑（筆電失敗時）
3b. ssh csie@192.168.150.105
    docker ps
    cd ~/pineapple_detection && docker compose up -d

Raspberry Pi（接著啟動）
5. ~/start_pineapple_system.sh

展示
6. 瀏覽器開啟 http://<RPi-IP>:8000
7. 分頁一：電子鼻成熟度辨識
8. 分頁二：照片品種辨識

展示結束
9. RPi：~/stop_pineapple_system.sh
10. Windows：Ctrl + C 停止 server_variety.py
```

---

## 14. 常見問題 Troubleshooting

**Q: 找不到 Arduino（`/dev/ttyACM*` 不存在）**

```bash
sudo usermod -a -G dialout $USER
# 重新登入後生效
```

**Q: `air_base.json` 找不到或推論觸發空氣防呆**

```bash
python calibrate_air_30s.py
```

**Q: 整合網頁開啟，但分頁顯示「拒絕連線」**

```bash
ss -tulnp | grep python
# 應看到 5000, 5002, 8000
```

**Q: 照片辨識無法回傳結果**

確認 Windows 端 `server_variety.py` 有啟動且使用 `host="0.0.0.0"`，並確認 RPi 與 Windows 在同一網路。

**Q: 筆電無法執行影像辨識，如何切換 Docker 備援？**

將 `pineapple_app_gateway/app_gateway_v2.py` 或整合網頁 `app.py` 的影像辨識 URL 改為 `http://192.168.150.105:5001`，重啟服務。

**Q: 農民端 App 掃描後回傳 mock 資料而非真實推論**

請至「設定」頁面確認後端 URL 填入正確的 RPi IP，並確認 RPi 上 `app_local.py` 正在執行。

---

## 15. 系統限制與未來改進 Limitations

| 項目 | 狀態 | 說明 |
|------|------|------|
| 影像辨識需外部機器 | 已有備援 | 主要跑 Windows PC；學校 VM Docker 作為備援 |
| 整合網頁用 iframe | 現有限制 | 內外頁風格略有差異 |
| IP 硬編碼 | 現有限制 | RPi 或 PC IP 改變時需手動更新設定 |
| Docker 備援需手動切換 | 現有限制 | 目前需手動修改 Gateway URL；未來可加入自動 fallback 邏輯 |

---

## 16. 開發團隊 Team Members

長庚大學資訊工程學系

| 學號 | 姓名 |
|------|------|
| B1144143 | 陳玟妤 |
| B1229062 | 林冠妤 |
| B1229066 | 陳怡禎 |
| B1229068 | 廖文歆 |

指導教授：張哲維 教授

---

## 17. 授權 License

本專案採用 [MIT License](../LICENSE) 授權。
