<div align="center">

# 🍍 PineNose：鳳梨成熟度與品種辨識系統
### Pineapple Ripeness & Variety Detection System

### [🎬 期中 Demo 影片](https://drive.google.com/file/d/1zQTGWSUGKHxx7ukhSpP41EWQJNEOJPet/view?usp=drivesdk)
### [🎬 期末 Demo 影片](https://drive.google.com/file/d/1Z_MbwVsv4nYf6GSiNdPcTrRvedTm5LH4/view?usp=drivesdk)

*電子鼻 × 邊緣運算 × 機器學習 × 影像辨識*
*Electronic Nose × Edge Computing × Machine Learning × Image Recognition*

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&logo=python&logoColor=white)
![Arduino](https://img.shields.io/badge/Arduino-Mega_2560-00979D?style=flat-square&logo=arduino&logoColor=white)
![Raspberry Pi](https://img.shields.io/badge/Raspberry_Pi-3_Model_B-A22846?style=flat-square&logo=raspberry-pi&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-ExtraTrees-F7931E?style=flat-square&logo=scikit-learn&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0+-000000?style=flat-square&logo=flask&logoColor=white)
![React Native](https://img.shields.io/badge/React_Native-Expo-61DAFB?style=flat-square&logo=react&logoColor=black)
![Docker](https://img.shields.io/badge/Docker-VM_Backup-2496ED?style=flat-square&logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

</div>

---

## 1. 專案概述 Project Overview

本系統為**非破壞性鳳梨智慧辨識系統**，整合兩大核心功能：

| 功能 | 方法 | 輸出 |
|------|------|------|
| **電子鼻成熟度辨識** | 氣體感測器陣列 + ExtraTrees 機器學習 | 四階段成熟度（未熟／初熟／成熟／過熟） |
| **影像品種辨識** | YOLOv8 偵測 + EfficientNet-B0 分類 | 四種鳳梨品種（金鑽／本土／牛奶／西瓜） |

系統由 Arduino Mega 2560 採集 VOC（揮發性有機化合物）訊號，傳至 Raspberry Pi 3 進行邊緣推論，並透過 Flask API 串接農民端與消費端行動應用程式。

---

## 2. 功能特色 Features

- 非破壞性檢測：無需切開鳳梨，30 秒完成一次推論
- 邊緣運算部署：模型直接跑在 Raspberry Pi 3，不依賴雲端
- Demo 模式：無硬體亦可用預錄 CSV 資料測試
- 影像品種辨識：手機拍照即可辨識鳳梨品種
- 整合 Web 介面：一頁整合電子鼻推論 + 品種辨識結果
- 行動 App：農民端（採收決策）+ 消費端（品種查詢）
- **Docker 備援**：影像辨識模型部署至學校 VM Docker，比賽現場筆電故障時仍可提供 API 服務

---

## 3. 系統架構 System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                  使用者介面層 User Interface                       │
│  農民端 App (Expo/RN)  消費端 App (Expo/RN)  整合 Web 介面        │
├──────────────────────────────────────────────────────────────────┤
│                  API 服務層 API Service                           │
│           pineapple_app_gateway  (Flask, Port 5002)              │
│        ┌──────────────────────┬──────────────────────┐          │
│        ▼                      ▼                      ▼           │
│  Raspberry Pi 3         影像辨識 Port 5001       整合 Web 介面    │
│  pineapple_final        ┌─ Windows PC ─────┐    pineapple_      │
│  (inference_30s.py)     │  server_variety  │    unified_web     │
│                         └─ 學校 VM Docker ─┘    /app.py         │
│                           192.168.150.105        Port 8000       │
├──────────────────────────────────────────────────────────────────┤
│                  感測 / 資料層 Sensing                            │
│    Arduino Mega 2560 → USB Serial (115200 baud) → RPi 3          │
│    MQ2 | MQ3 | MQ9 | MQ135 | TGS2602 | BME280                   │
└──────────────────────────────────────────────────────────────────┘
```

**各子系統說明：**

| 子系統 | 路徑 | 用途 |
|--------|------|------|
| 電子鼻推論主系統 | `Semester 2 Final Exam (三下-期末)/pineapple_final/` | 部署於 RPi，校準 + 推論主程式 |
| App API Gateway | `Semester 2 Final Exam (三下-期末)/pineapple_app_gateway/` | 行動 App 的 Flask 中繼 API |
| 影像品種辨識（主要） | `Semester 2 Final Exam (三下-期末)/pineapple_detection/` | YOLOv8 + EfficientNet-B0，跑在 PC |
| **影像品種辨識（備援）** | 學校 VM Docker `192.168.150.105:5001` | **同上服務，Docker 化備援** |
| 整合 Web 介面 | `Semester 2 Final Exam (三下-期末)/整合網頁/` | 一頁整合所有推論結果 |
| 消費端 App | `Semester 2 Final Exam (三下-期末)/app/` | React Native (Expo) |
| 農民端 App | `Tinazhen/Farmer_pineapple` / `3rd Grade - Semester 2 (三下-期中)/App/Farmer_pineapple-main/` | React Native (Expo)，批次掃描與報表管理 |
| 期中版部署 | `3rd Grade - Semester 2 (三下-期中)/pineapple_deployment_system/` | 期中展示用，已由期末版取代 |

---

## 4. 硬體需求 Hardware Requirements

| 元件 | 規格 | 用途 |
|------|------|------|
| Arduino Mega 2560 | ATmega2560，54 數位腳 | 感測器訊號擷取 |
| Raspberry Pi 3 Model B | 1.2 GHz 四核，1 GB RAM | 邊緣推論主機 |
| MQ-2 | 可燃氣體、煙霧 | VOC 感測 |
| MQ-3 | 酒精、乙醇 | VOC 感測 |
| MQ-9 | CO、可燃氣體 | VOC 感測 |
| MQ-135 | 空氣品質（NH3、CO2） | VOC 感測 |
| TGS2602 | 有機溶劑、乙醇 | VOC 感測 |
| BME280 | 溫度、濕度、氣壓（I²C） | 環境補償 |
| USB Type-B 線 | — | Arduino ↔ RPi 串列傳輸 |

---

## 5. 軟體需求 Software Requirements

### 5.1 Raspberry Pi 3 主系統

```
Python 3.9+
joblib==1.5.3
numpy==2.4.3
pandas==3.0.1
pyserial==3.5
scikit-learn==1.8.0
scipy==1.17.1
```

> 完整版：`Semester 2 Final Exam (三下-期末)/pineapple_final/requirements_rpi.txt`

### 5.2 App API Gateway（一般 PC / 伺服器）

```
Flask==3.1.3
requests==2.33.1
```

> 完整版：`Semester 2 Final Exam (三下-期末)/pineapple_app_gateway/requirements_gateway.txt`

### 5.3 影像品種辨識伺服器

```
ultralytics>=8.0.0   # YOLOv8
torch>=2.0.0
torchvision>=0.15.0
timm>=0.9.0          # EfficientNet-B0
pillow>=9.0.0
```

> 完整版：`Semester 2 Final Exam (三下-期末)/pineapple_detection/requirements.txt`

### 5.4 Docker 備援（學校 VM）

```
Docker Engine 20.10+
docker compose v2
```

影像辨識服務容器化後部署至學校 VM（`192.168.150.105`），無需在本機安裝 Python 套件，`docker compose build` 時自動安裝。

### 5.5 Arduino IDE

Arduino IDE 2.x，無需額外安裝函式庫。

---

## 6. 安裝 Installation

### 6.1 複製專案

```bash
git clone https://github.com/Tiffanyxxx3238/electronic-nose-pineapple-ripeness-assessment.git
cd electronic-nose-pineapple-ripeness-assessment
```

### 6.2 安裝 Raspberry Pi 主系統套件

```bash
cd "Semester 2 Final Exam (三下-期末)/pineapple_final"
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements_rpi.txt
```

### 6.3 安裝 App Gateway 套件（PC 端）

```bash
cd "Semester 2 Final Exam (三下-期末)/pineapple_app_gateway"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements_gateway.txt
```

### 6.4 安裝影像辨識套件

```bash
cd "Semester 2 Final Exam (三下-期末)/pineapple_detection"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 6.5 燒錄 Arduino 韌體

1. 開啟 Arduino IDE
2. 開啟 `Semester 2 Final Exam (三下-期末)/pineapple_deployment_system/use_this/use_this.ino`
3. 選擇板子：**Arduino Mega or Mega 2560**
4. 選擇對應的 COM Port
5. 上傳（Upload）

---

## 7. 快速開始 Quick Start

### 7.1 Demo 模式（無硬體，使用預錄資料）

不需要 Arduino 或 RPi，直接在 PC 上測試推論邏輯：

```bash
cd "Semester 2 Final Exam (三下-期末)/pineapple_final"
source .venv/bin/activate
python app_local_demo_early_corrected_v4.py
```

瀏覽器開啟 `http://localhost:5000`，可從 `demo_data/` 資料夾選取樣本 CSV（如 `pineapple_03_20260211_成熟.xlsx`）進行推論。

**Demo 資料對照表：**

| 檔名日期 | 標籤 |
|----------|------|
| `*_20260203_未熟.xlsx` | Stage 0：未熟 |
| `*_20260206_初熟.xlsx` | Stage 1：初熟 |
| `*_20260211_成熟.xlsx` | Stage 2：成熟 |
| `*_20260214_過熟.xlsx` | Stage 3：過熟 |

---

### 7.2 Raspberry Pi 即時偵測（需完整硬體）

**步驟一：空氣基線校正**（首次使用或更換環境時執行）

```bash
# 在 RPi 上執行，Arduino 接好後
cd ~/pineapple_final
source .venv/bin/activate
python calibrate_air_30s.py
```

等待 30 秒採集完成，生成 `air_base.json`。

**步驟二：即時推論**

```bash
python inference_30s.py
```

程式會偵測 USB 串口，讀取 30 秒感測資料，輸出成熟度結果。

**步驟三（選用）：啟動 Flask 本機介面**

```bash
python app_local.py
# 瀏覽器開啟 http://<RPi-IP>:5000
```

---

### 7.3 影像品種辨識伺服器

```bash
cd "Semester 2 Final Exam (三下-期末)/pineapple_detection"
source .venv/bin/activate
python server_variety.py
# 伺服器啟動於 http://localhost:5001
```

測試推論（以 `test_7.jpg` 為例）：

```bash
curl -X POST http://localhost:5001/predict \
  -F "file=@test_7.jpg"
```

---

### 7.4 App API Gateway

```bash
cd "Semester 2 Final Exam (三下-期末)/pineapple_app_gateway"
source .venv/bin/activate
python app_gateway_v2.py
# Gateway 啟動於 http://localhost:5000
```

Gateway 會將請求轉發至 RPi（電子鼻推論）與影像辨識伺服器。

---

### 7.5 Docker 備援：學校 VM 影像辨識

> **使用時機：** 比賽現場筆電無法執行模型時，切換至此備援路徑。影像辨識服務已預先容器化部署至學校 VM。

**部署（僅需做一次）：**

```bash
# 從 PC 上傳至學校 VM
scp -r "Semester 2 Final Exam (三下-期末)/pineapple_detection" \
    csie@192.168.150.105:/home/csie/

# 在 VM 上建立並啟動 container
ssh csie@192.168.150.105
cd ~/pineapple_detection
docker compose build
docker compose up -d
```

**確認服務正常：**

```bash
# 在 VM 上確認 container 執行中
docker ps
# 應看到：pineapple-detection   Up X days   0.0.0.0:5001->5001/tcp

# 查看 logs 確認模型載入
docker logs pineapple-detection
# 應看到：[OK] YOLO detector loaded
#         [OK] EfficientNet-B0 classifier loaded
#         Running on http://0.0.0.0:5001

# 測試 API
curl http://192.168.150.105:5001
curl -X POST http://192.168.150.105:5001/predict -F "image=@test_7.jpg"
```

**切換備援路徑：** 把 `pineapple_app_gateway/app_gateway_v2.py` 或整合網頁 `app.py` 中影像辨識的 URL 從 `http://192.168.0.176:5001` 改為 `http://192.168.150.105:5001`，重啟 Gateway 服務即可。

---

### 7.6 整合 Web 介面

```bash
cd "Semester 2 Final Exam (三下-期末)/整合網頁"
bash start_pineapple_system.sh
# 瀏覽器開啟 http://<RPi-IP>:8000
```

---

## 8. 行動 App Mobile Apps

系統共有兩個 Expo / React Native App，分別針對農民與消費者。

### 8.1 農民端 App（Farmer App）

**路徑：** `3rd Grade - Semester 2 (三下-期中)/App/Farmer_pineapple-main/expo/`  
**獨立 Repo：** [`Tinazhen/Farmer_pineapple`](https://github.com/Tinazhen/Farmer_pineapple)

**定位：** 供農民在田間或倉庫使用，管理採收批次、逐批掃描鳳梨並輸出報告。

#### 架構

```text
Farmer_pineapple/
├── app/                 # Expo Router 頁面
├── components/          # 共用 UI 元件與圖表
├── stores/              # 批次與掃描狀態管理
├── services/            # API 呼叫與後端連線
└── assets/              # 圖片、圖示等靜態資源
```

#### 畫面與功能

| 頁面 | 功能說明 |
|------|----------|
| **首頁 Home** | 今日掃描總數、今日異常數、進行中批次數；快速入口「開始掃描」／「新建批次」；最近批次列表 |
| **批次管理 Batches** | 列出所有批次（狀態：草稿 draft / 進行中 testing / 完成 done）；可進入批次詳情 |
| **建立批次** | 填寫批次名稱、田區、品種、採收量、用途（外銷 / 內銷 / 加工）、採樣目標數 |
| **批次掃描 Scan** | 對接 RPi API，取得每顆鳳梨的成熟度（unripe / ripe / overripe）、糖度 TSS Brix、黑心病風險（low / med / high）、異常旗標（normal / isolate） |
| **批次摘要 Summary** | 成熟度分佈圓餅圖（RipenessPieChart）；批次統計；匯出報告 |
| **報告 Reports** | 歷史批次報告列表 |
| **設定 Settings** | RPi 後端 URL、語言（zh / en）、糖度閾值（外銷 Brix、內銷 Brix）、採樣比例 |

#### API 串接（呼叫 RPi 後端）

```
GET  /ping          → 確認後端是否上線
POST /scan/start    → 觸發 30 秒掃描，回傳推論結果
```

**`/scan/start` 回傳格式：**

```json
{
  "ripeness": "ripe",
  "tss_brix": 14.5,
  "blackheart_risk": "low",
  "anomaly_flag": "normal"
}
```

> 若後端離線，App 會自動 fallback 至本機亂數模擬結果供展示。

#### 安裝與執行

```bash
cd "3rd Grade - Semester 2 (三下-期中)/App/Farmer_pineapple-main/expo"
bun install          # 或 npm install
bunx expo start      # 掃描 QR code 用 Expo Go 開啟
```

首次使用請至「設定」頁面填入 Raspberry Pi 的 IP：

```
http://172.20.10.2:5000    # 手機熱點環境
http://192.168.0.152:5000  # 一般 Wi-Fi 環境
```

**技術棧：** Expo Router（檔案路由）、TypeScript、Zustand（狀態管理）、React Query、expo-image-picker、react-native-svg（圓餅圖）

---

### 8.2 消費端 App（Consumer App）

**路徑（期中）：** `3rd Grade - Semester 2 (三下-期中)/App/Consumer_pineapple-ripeness-main/expo/`
**路徑（期末）：** `Semester 2 Final Exam (三下-期末)/app/Consumer_pineapple-ripeness-main/expo/`

**定位：** 供消費者使用，查詢鳳梨品種資訊、提交掃描紀錄、檢視歷史記錄。

#### 畫面與功能

| 頁面 | 功能說明 |
|------|----------|
| **首頁 index** | App 入口，進入主要功能 |
| **掃描 processing → result** | 掃描流程（含偵測動畫、音效 beep.mp3）；顯示成熟度結果，可提交回饋 |
| **品種介紹 varieties** | 四種鳳梨品種（金鑽／本土／牛奶／西瓜）介紹；點入 variety-detail 查看詳細說明 |
| **知識庫 knowledge-base** | 鳳梨相關農業知識 |
| **季節指南 seasonal-guide** | 各品種產季與採購建議 |
| **趣味問答 trivia** | 鳳梨趣味小知識卡片 |
| **糖度計算 calculator** | 甜度相關換算工具 |
| **歷史記錄 history** | 過去掃描紀錄列表；點入 history-detail 查看單筆詳情及提交人工回饋 |
| **待上傳 pending-uploads** | 離線時未能上傳的掃描紀錄，連線後批次同步 |
| **操作說明 instruction** | App 使用教學 |

#### API 串接

```
POST /scan_records               → 上傳掃描紀錄（含感測器原始數值）
POST /scan_records/{id}/feedback → 提交人工回饋（correct_label）
GET  /scan_records/export.xlsx   → 匯出歷史紀錄 Excel
```

**上傳 payload 包含：**

```json
{
  "timestamp_iso": "2026-05-31T10:00:00.000Z",
  "fruit_id": "PA-001",
  "MQ2_raw": 312, "MQ3_raw": 189, "MQ9_raw": 254,
  "MQ135_raw": 401, "TGS2602_raw": 178,
  "Temp_C": 26.3, "Humidity_pct": 68.1, "Pressure_hPa": 1013.2,
  "ripeness_pred": "ripe",
  "confidence": 0.82,
  "anomaly_flag": "none",
  "locale": "zh-TW",
  "device_id": "xxxx-xxxx",
  "app_version": "1.0.0"
}
```

#### 安裝與執行

```bash
cd "3rd Grade - Semester 2 (三下-期中)/App/Consumer_pineapple-ripeness-main/expo"
bun install          # 或 npm install
bunx expo start
```

在 App 設定頁填入後端 API base URL（Gateway 或 RPi 直接 IP）。

**技術棧：** Expo Router、TypeScript、Zustand、多語言 Context（zh / en）、expo-av（音效）、expo-file-system、expo-sharing（匯出）

---

## 9. 輸入 / 輸出格式 Input / Output Format

### 9.1 電子鼻推論

**輸入：** Arduino 透過 USB Serial 以 115200 baud 持續傳輸，每筆資料包含：

```
MQ2, MQ3, MQ9, MQ135, TGS2602, temperature, humidity, pressure
```

**模型特徵（11 個，30 秒窗口統計量）：**

```
MQ3_std_norm, MQ3_range_norm, MQ2_MQ3_ratio, MQ3_MQ135_ratio,
MQ9_slope, TGS2602_min_norm, MQ2_auc_norm, MQ2_mean_norm,
MQ9_min_norm, TGS2602_std_norm, MQ9_delta_mean
```

**輸出：**

```json
{
  "stage": 2,
  "label": "成熟",
  "confidence": 0.82
}
```

| Stage | 中文標籤 | 說明 |
|-------|----------|------|
| 0 | 未熟 | 果實尚未成熟 |
| 1 | 初熟 | 開始成熟 |
| 2 | 成熟 | 最佳採收期 |
| 3 | 過熟 | 已過熟 |

---

### 9.2 影像品種辨識

**輸入：** 鳳梨照片（JPG / PNG），透過 HTTP POST 上傳至 `/predict`

**輸出：**

```json
{
  "is_pineapple": true,
  "predicted_class": "jinzuan",
  "predicted_label_zh": "金鑽鳳梨",
  "confidence": 0.91
}
```

| 類別代碼 | 中文名稱 |
|----------|----------|
| `jinzuan` | 金鑽鳳梨 |
| `local` | 本土種鳳梨 |
| `milk` | 牛奶鳳梨 |
| `watermelon` | 西瓜鳳梨 |

---

## 10. 專案結構 Project Structure

```
electronic-nose-pineapple-ripeness-assessment/
│
├── 3rd Grade - Semester 2 (三下-期中)/          # 期中成果（歷史版本）
│   ├── arduino_mega_data_collection/            # Arduino 感測器韌體
│   │   ├── air_baseline_collection.ino          # 空氣基線資料蒐集
│   │   └── pineapple_sample_collection.ino      # 鳳梨樣本資料蒐集
│   ├── enose_model_training/
│   │   └── orkspace/                            # 模型訓練工作區
│   │       ├── data/                            # 原始量測資料
│   │       ├── deploy_rpi_et_30s_noday/         # 生產部署用模型（RPi）
│   │       ├── models/                          # 儲存的模型檔案
│   │       ├── reports/                         # 訓練報表與評估結果
│   │       ├── labeling_perfect_final.ipynb     # 標注與訓練 Notebook
│   │       ├── feature_columns.json             # 特徵欄位定義
│   │       ├── cutpoints.json                   # 閾值設定
│   │       └── model_final.pkl                  # 訓練完成的模型
│   ├── pineapple_deployment_system/             # 期中 RPi 部署（已由期末版取代）
│   │   ├── app_local.py                         # Flask 本機介面
│   │   ├── calibrate_air_30s.py                 # 空氣基線校正
│   │   ├── inference_30s.py                     # 30 秒即時推論
│   │   └── use_this.ino                         # 搭配推論用的 Arduino 韌體
│   ├── App/
│   │   ├── Consumer_pineapple-ripeness-main/    # 消費端 App (Expo)
│   │   └── Farmer_pineapple-main/               # 農民端 App (Expo)
│   └── files(設計文件&簡報)/                    # 期中報告與設計文件
│
├── Semester 2 Final Exam (三下-期末)/            # 期末成果（現行版本）
│   ├── pineapple_final/                         # ★ 電子鼻推論主系統（RPi 部署）
│   │   ├── inference_30s.py                     # 30 秒即時推論（接 Arduino）
│   │   ├── calibrate_air_30s.py                 # 空氣基線校正
│   │   ├── app_local.py                         # Flask 本機介面
│   │   ├── app_local_demo_early_corrected_v4.py # Demo 模式（無需硬體）
│   │   ├── inference_from_csv_updated.py        # 從 CSV 批次推論
│   │   ├── deploy_student.pkl                   # 部署模型檔案
│   │   ├── deploy_meta.json                     # 模型中繼資料與特徵清單
│   │   ├── feature_columns.json                 # 特徵欄位定義
│   │   ├── air_base.json                        # 空氣基線（校正後生成）
│   │   ├── requirements_rpi.txt                 # RPi Python 套件
│   │   └── demo_data/                           # 預錄 Demo 資料（四個成熟度）
│   │
│   ├── pineapple_detection/                     # ★ 影像品種辨識伺服器
│   │   ├── server_variety.py                    # Flask 推論 API (Port 5001)
│   │   ├── models.py                            # EfficientNet-B0 模型定義
│   │   ├── class_names.json                     # 品種類別對照（4 種）
│   │   ├── weights/
│   │   │   ├── b0_focal_best.pth                # EfficientNet-B0 品種分類權重
│   │   │   └── yolov8n_pineapple_best.pt        # YOLOv8 鳳梨偵測權重
│   │   ├── src/
│   │   │   ├── pipeline.py                      # 推論 pipeline（偵測→分類）
│   │   │   └── predict.py                       # 單張圖片推論腳本
│   │   ├── dataset/                             # 訓練資料集（YOLO 格式）
│   │   └── requirements.txt                     # 影像辨識 Python 套件
│   │
│   ├── pineapple_app_gateway/                   # ★ App API Gateway（行動端介面）
│   │   ├── app_gateway_v2.py                    # Gateway 主程式（轉發 RPi + 影像）
│   │   ├── requirements_gateway.txt             # Gateway 套件
│   │   └── start_server.sh                      # 一鍵啟動腳本
│   │
│   ├── 整合網頁/                                # ★ 整合 Web 介面
│   │   ├── pineapple_unified_web/app.py         # 整合網頁 Flask 主程式
│   │   ├── start_pineapple_system.sh            # 一鍵啟動整合系統
│   │   └── stop_pineapple_system.sh             # 一鍵停止整合系統
│   │
│   ├── app/
│   │   ├── Consumer_pineapple-ripeness-main/    # 消費端 App (Expo/React Native)
│   │   └── Farmer_pineapple-main/               # 農民端 App 架構參考 Tinazhen/Farmer_pineapple
│   │
│   ├── enose_model_training/                    # 模型訓練工作區（同期中，更新版）
│   └── pineapple_deployment_system/             # RPi 韌體目錄
│       └── use_this/use_this.ino                # 搭配推論用的 Arduino 韌體
│
└── README.md
```

> **注意：** `enose_model_training/orkspace/` 中的 `orkspace` 為實際資料夾名稱（非筆誤修正後的版本），`nodeay` / `noday` 均代表「不使用 day 特徵（日期特徵）」的模型變體。

---

## 11. 模型資訊 Model Information

### 11.1 電子鼻成熟度模型

| 項目 | 說明 |
|------|------|
| 演算法 | ExtraTreesClassifier (scikit-learn) |
| 輸入窗口 | 30 秒（~50 筆取樣） |
| 特徵數量 | 11 個統計特徵 |
| 分類類別 | 4 類（未熟／初熟／成熟／過熟） |
| 部署限制 | 不使用日期特徵，支援單次攜帶式推論 |
| 模型檔案 | `pineapple_final/deploy_student.pkl` |
| 中繼資料 | `pineapple_final/deploy_meta.json` |

**特徵工程：** 對每個 30 秒窗口計算 MQ2、MQ3、MQ9、MQ135、TGS2602 的統計量（mean、std、min、range、AUC、slope、delta\_mean）並正規化，再從中挑選 top-11 特徵。

### 11.2 影像品種辨識模型

| 項目 | 說明 |
|------|------|
| 偵測模型 | YOLOv8n（判斷畫面中是否有鳳梨） |
| 分類模型 | EfficientNet-B0（Focal Loss 微調） |
| 訓練資料 | `pineapple_detection/dataset/`（YOLO 格式） |
| 分類類別 | 4 種（金鑽／本土種／牛奶／西瓜） |
| 訓練報告 | `pineapple_detection/outputs/` |

**推論 Pipeline：**
1. YOLOv8 偵測鳳梨是否存在於圖片中
2. 裁切偵測到的區域（Bounding Box）
3. EfficientNet-B0 對裁切圖進行品種分類

---

## 12. Demo 影片與截圖 Demo Video & Screenshots

- [期中 Demo 影片（Google Drive）](https://drive.google.com/file/d/1zQTGWSUGKHxx7ukhSpP41EWQJNEOJPet/view?usp=drivesdk)
- [期末 Demo 影片（Google Drive）](https://drive.google.com/file/d/1Z_MbwVsv4nYf6GSiNdPcTrRvedTm5LH4/view?usp=drivesdk)
- 成熟度時間軸圖：`enose_model_training/orkspace/stage_timeline.png`

---

## 13. 常見問題 Troubleshooting

**Q: `inference_30s.py` 找不到 Arduino 串口**

```
SerialException: could not open port ...
```

檢查 Arduino 是否接上，並確認 `/dev/ttyUSB0`（Linux）或 `COM3`（Windows）正確。可在程式頂端修改 `SERIAL_PORT` 變數。

---

**Q: `app_local_demo_early_corrected_v4.py` 啟動後網頁空白**

確認 `demo_data/` 資料夾中有 `.xlsx` 檔案，並且 `deploy_student.pkl` 與 `deploy_meta.json` 存在於同一目錄。

---

**Q: 影像辨識伺服器啟動失敗（CUDA / torch 錯誤）**

若無 GPU，確認已安裝 CPU 版本的 PyTorch：

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

---

**Q: `calibrate_air_30s.py` 校正後 `air_base.json` 仍為空**

確認電子鼻裝置已置於空氣中（遠離鳳梨），且 Arduino 已上傳 `use_this.ino` 韌體。

---

**Q: 農民端 App 掃描後回傳 mock 資料而非真實推論**

App 內建 fallback 邏輯：後端離線時自動回傳亂數模擬值。請至「設定」頁面確認後端 URL 填寫正確（如 `http://172.20.10.2:5000`），並確認 RPi 上的 `app_local.py` 正在執行且可 ping 通。

---

**Q: 農民端 App 顯示「Login」頁面無法進入**

直接點選登入按鈕即可（目前無需真實帳密驗證，為展示用介面）。

---

**Q: 消費端 App 上傳掃描紀錄失敗，進入 pending-uploads**

確認後端 Gateway 或 RPi API 的 URL 設定正確，且與手機在同一網路下。待網路恢復後，至「待上傳」頁面手動觸發批次重傳。

---

**Q: 比賽現場筆電無法執行影像辨識，如何切換 Docker 備援？**

1. SSH 進學校 VM，確認 container 執行中：
   ```bash
   ssh csie@192.168.150.105
   docker ps   # 應看到 pineapple-detection Up
   ```
2. 若 container 未執行，重新啟動：
   ```bash
   cd ~/pineapple_detection && docker compose up -d
   ```
3. 修改 `pineapple_app_gateway/app_gateway_v2.py` 或整合網頁 `app.py` 中的影像辨識 URL：
   - 改前：`http://192.168.0.176:5001`
   - 改後：`http://192.168.150.105:5001`
4. 重啟 RPi 上的 Gateway 服務，展示即可繼續。

---

**Q: Docker container logs 顯示模型載入失敗**

確認 VM 上 `~/pineapple_detection/weights/` 內有以下兩個檔案：

```
yolov8n_pineapple_best.pt
b0_focal_best.pth
```

若缺少，重新上傳：

```bash
scp -r "Semester 2 Final Exam (三下-期末)/pineapple_detection/weights" \
    csie@192.168.150.105:/home/csie/pineapple_detection/
```

然後重建 container：

```bash
docker compose down && docker compose up -d
```

---

## 14. 開發團隊 Team Members

本專題由長庚大學（Chang Gung University）學生共同開發：

| 學號 | 姓名 |
|------|------|
| B1144143 | 陳玟妤 |
| B1229062 | 林冠妤 |
| B1229066 | 陳怡禎 |
| B1229068 | 廖文歆 |

---

## 15. 授權 License

本專案採用 [MIT License](LICENSE) 授權。
