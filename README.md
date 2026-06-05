<div align="center">

# 🍍 PineNose：鳳梨成熟度與品種辨識系統
### Pineapple Ripeness & Variety Detection System

### [🎬 期中 Demo 影片](https://drive.google.com/file/d/1zQTGWSUGKHxx7ukhSpP41EWQJNEOJPet/view?usp=drivesdk)
### [🎬 期末 Demo 影片](https://drive.google.com/file/d/1Z_MbwVsv4nYf6GSiNdPcTrRvedTm5LH4/view?usp=drivesdk)
### ［🎬 20260601 報告 Demo 影片］（https://drive.google.com/file/d/1jPS8nS9LenRPj_xzRBxOc3c53piBs48R/view?usp=drivesdk）

*電子鼻 × 邊緣運算 × 機器學習 × 影像辨識 × 行動 App*

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

本系統為**非破壞性鳳梨智慧辨識系統**，整合電子鼻成熟度辨識、影像品種辨識、Raspberry Pi 邊緣推論、Flask API、整合 Web 介面，以及農民端 / 消費端行動 App。

| 功能 | 方法 | 輸出 |
|------|------|------|
| 電子鼻成熟度辨識 | 氣體感測器陣列 + ExtraTrees 機器學習 | 四階段成熟度：未熟 / 初熟 / 成熟 / 過熟 |
| 影像品種辨識 | YOLOv8 偵測 + EfficientNet-B0 分類 | 四種鳳梨品種：金鑽 / 本土 / 牛奶 / 西瓜 |
| 農民端 App | Expo / React Native | 批次掃描、批次摘要、報告管理 |
| 消費端 App | Expo / React Native | 品種查詢、掃描紀錄、知識內容 |

---

## 2. 功能特色 Features

- 非破壞性檢測：無需切開鳳梨，使用氣體感測訊號推論成熟度
- 邊緣運算部署：電子鼻模型部署於 Raspberry Pi
- Demo 模式：無硬體時可使用預錄資料展示推論流程
- 影像品種辨識：手機或網頁上傳照片後辨識鳳梨品種
- 整合 Web 介面：集中展示電子鼻成熟度與影像品種辨識
- 行動 App：農民端與消費端分流設計
- Docker 備援：影像辨識服務可部署至學校 VM Docker

---

## 3. 系統架構 System Architecture

```text
使用者介面層 User Interface
├── 整合 Web 介面
├── 農民端 App Farmer App
└── 消費端 App Consumer App

API 服務層 API Service
├── pineapple_app_gateway/       # App / Web API Gateway
├── pineapple_final/             # 電子鼻成熟度推論 API / Web
└── pineapple_detection/         # 影像品種辨識 API

硬體與模型層 Hardware / Model
├── Arduino Mega 2560
├── MQ2 / MQ3 / MQ9 / MQ135 / TGS2602 / BME280
├── Raspberry Pi 3
├── ExtraTrees 成熟度模型
├── YOLOv8 鳳梨偵測模型
└── EfficientNet-B0 品種分類模型
```

**各子系統說明：**

| 子系統 | 路徑 | 用途 |
|--------|------|------|
| 電子鼻推論主系統 | `Semester 2 Final Exam (三下-期末)/pineapple_final/` | 部署於 RPi，校準與成熟度推論 |
| App API Gateway | `Semester 2 Final Exam (三下-期末)/pineapple_app_gateway/` | 行動 App 與 Web 的 Flask 中繼 API |
| 影像品種辨識 | `Semester 2 Final Exam (三下-期末)/pineapple_detection/` | YOLOv8 + EfficientNet-B0 影像辨識 |
| 整合 Web 介面 | `Semester 2 Final Exam (三下-期末)/整合網頁/` | 一頁整合推論結果 |
| 農民端 App | `Semester 2 Final Exam (三下-期末)/app/Farmer_pineapple-ripeness-main/` | React Native / Expo，批次掃描與報表管理 |
| 消費端 App | `Semester 2 Final Exam (三下-期末)/app/Consumer_pineapple-ripeness-main/expo/` | React Native / Expo，品種查詢與掃描紀錄 |
| 期中版部署 | `3rd Grade - Semester 2 (三下-期中)/pineapple_deployment_system/` | 期中展示用，已由期末版取代 |

---

## 4. 硬體需求 Hardware Requirements

| 元件 | 規格 | 用途 |
|------|------|------|
| Arduino Mega 2560 | ATmega2560 | 感測器訊號擷取 |
| Raspberry Pi 3 Model B | 1.2 GHz 四核，1 GB RAM | 邊緣推論主機 |
| MQ-2 | 可燃氣體、煙霧 | VOC 感測 |
| MQ-3 | 酒精、乙醇 | VOC 感測 |
| MQ-9 | CO、可燃氣體 | VOC 感測 |
| MQ-135 | 空氣品質 | VOC 感測 |
| TGS2602 | 有機溶劑、乙醇 | VOC 感測 |
| BME280 | 溫度、濕度、氣壓 | 環境補償 |
| Windows PC / Docker VM | PyTorch / Flask | 影像品種辨識服務 |

---

## 5. 軟體需求 Software Requirements

| 子系統 | 主要技術 |
|--------|----------|
| 電子鼻主系統 | Python、pandas、pyserial、scikit-learn |
| App Gateway | Flask、requests |
| 影像品種辨識 | Python、Flask、YOLOv8、PyTorch、EfficientNet-B0 |
| 整合 Web | Flask、HTML、CSS |
| 農民端 App | Expo Router、React Native、TypeScript、Zustand、React Query |
| 消費端 App | Expo Router、React Native、TypeScript、Zustand |
| Docker 備援 | Docker Engine、docker compose |

---

## 6. 安裝 Installation

### 6.1 複製專案

```bash
git clone https://github.com/Tinazhen/electronic-nose-pineapple-ripeness-assessment.git
cd electronic-nose-pineapple-ripeness-assessment
```

### 6.2 安裝 Raspberry Pi 主系統套件

```bash
cd "Semester 2 Final Exam (三下-期末)/pineapple_final"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements_rpi.txt
```

### 6.3 安裝 App Gateway 套件

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

### 6.5 安裝農民端 App

```bash
cd "Semester 2 Final Exam (三下-期末)/app/Farmer_pineapple-ripeness-main"
npm install
npm run start
```

### 6.6 安裝消費端 App

```bash
cd "Semester 2 Final Exam (三下-期末)/app/Consumer_pineapple-ripeness-main/expo"
npm install
npm run start
```

---

## 7. 快速開始 Quick Start

### 7.1 Demo 模式

```bash
cd "Semester 2 Final Exam (三下-期末)/pineapple_final"
source .venv/bin/activate
python app_local_demo_early_corrected_v4.py
```

### 7.2 Raspberry Pi 即時偵測

```bash
cd ~/pineapple_final
source .venv/bin/activate
python calibrate_air_30s.py
python inference_30s.py
```

### 7.3 影像品種辨識伺服器

```bash
cd "Semester 2 Final Exam (三下-期末)/pineapple_detection"
source .venv/bin/activate
python server_variety.py
```

### 7.4 App API Gateway

```bash
cd "Semester 2 Final Exam (三下-期末)/pineapple_app_gateway"
source .venv/bin/activate
python app_gateway_v2.py
```

### 7.5 整合 Web 介面

```bash
cd "Semester 2 Final Exam (三下-期末)/整合網頁"
bash start_pineapple_system.sh
```

---

## 8. 行動 App Mobile Apps

系統共有兩個 Expo / React Native App：農民端與消費端。

### 8.1 農民端 App（Farmer App）

**路徑：** `Semester 2 Final Exam (三下-期末)/app/Farmer_pineapple-ripeness-main/`

#### 架構

```text
Farmer_pineapple-ripeness-main/
├── app/                       # Expo Router 頁面
│   ├── _layout.tsx            # 全域路由設定
│   ├── index.tsx              # 農民端首頁
│   ├── batches.tsx            # 批次管理頁
│   ├── batch-create.tsx       # 建立批次頁
│   ├── batch-scan.tsx         # 批次掃描頁
│   ├── batch-summary.tsx      # 批次摘要頁
│   ├── reports.tsx            # 報告列表頁
│   └── settings.tsx           # 設定頁
├── components/                # 共用 UI 元件
│   ├── BatchCard.tsx
│   └── StatCard.tsx
├── constants/                 # 全域樣式設定
│   └── theme.ts
├── services/                  # API 封裝
│   └── api.ts
├── stores/                    # Zustand 狀態管理
│   └── farmerStore.ts
├── types/                     # TypeScript 型別
│   └── index.ts
├── scripts/                   # 測試腳本
│   └── smoke-test.js
├── app.json
├── package.json
├── tsconfig.json
└── README.md
```

#### 頁面架構

| 頁面 | 路由 | 用途 |
|------|------|------|
| Home | `/` | 農民端首頁與批次入口 |
| Batches | `/batches` | 批次管理 |
| Batch Create | `/batch-create` | 建立批次 |
| Batch Scan | `/batch-scan` | 批次掃描 |
| Batch Summary | `/batch-summary` | 批次摘要 |
| Reports | `/reports` | 報告列表 |
| Settings | `/settings` | 後端 URL 與參數設定 |

#### API 串接

```http
GET  /ping
POST /scan/start
```

#### 執行與測試

```bash
cd "Semester 2 Final Exam (三下-期末)/app/Farmer_pineapple-ripeness-main"
npm install
npm run start
npm run test
```

---

### 8.2 消費端 App（Consumer App）

**路徑：** `Semester 2 Final Exam (三下-期末)/app/Consumer_pineapple-ripeness-main/expo/`

#### 架構

```text
Consumer_pineapple-ripeness-main/
└── expo/
    ├── app/                   # Expo Router 頁面
    ├── components/            # 共用 UI 元件
    ├── constants/             # 樣式與常數
    ├── contexts/              # App 狀態 Context
    ├── assets/                # 靜態資源
    ├── app.json
    ├── package.json
    └── README.md
```

#### 執行

```bash
cd "Semester 2 Final Exam (三下-期末)/app/Consumer_pineapple-ripeness-main/expo"
npm install
npm run start
```

---

## 9. 輸入 / 輸出格式 Input / Output Format

### 9.1 電子鼻推論

**輸入：** Arduino 透過 USB Serial 以 115200 baud 持續傳輸感測器資料。

```text
MQ2, MQ3, MQ9, MQ135, TGS2602, temperature, humidity, pressure
```

**輸出：**

```json
{
  "stage": 2,
  "label": "成熟",
  "confidence": 0.82
}
```

### 9.2 影像品種辨識

**輸入：** 鳳梨照片（JPG / PNG），透過 HTTP POST 上傳至 `/predict`。

**輸出：**

```json
{
  "is_pineapple": true,
  "predicted_class": "jinzuan",
  "predicted_label_zh": "金鑽鳳梨",
  "confidence": 0.91
}
```

---

## 10. 專案結構 Project Structure

```text
electronic-nose-pineapple-ripeness-assessment/
│
├── 3rd Grade - Semester 2 (三下-期中)/          # 期中成果
│   ├── arduino_mega_data_collection/            # Arduino 感測器韌體
│   ├── enose_model_training/                    # 期中模型訓練
│   ├── pineapple_deployment_system/             # 期中 RPi 部署
│   ├── App/                                     # 期中 App
│   └── files(設計文件&簡報)/                    # 文件與簡報
│
├── Semester 2 Final Exam (三下-期末)/            # 期末成果
│   ├── pineapple_final/                         # 電子鼻推論主系統
│   ├── pineapple_detection/                     # 影像品種辨識伺服器
│   ├── pineapple_app_gateway/                   # App API Gateway
│   ├── 整合網頁/                                # 整合 Web 介面
│   ├── app/
│   │   ├── Consumer_pineapple-ripeness-main/    # 消費端 App
│   │   │   └── expo/
│   │   └── Farmer_pineapple-ripeness-main/      # 農民端 App
│   │       ├── app/
│   │       │   ├── _layout.tsx
│   │       │   ├── index.tsx
│   │       │   ├── batches.tsx
│   │       │   ├── batch-create.tsx
│   │       │   ├── batch-scan.tsx
│   │       │   ├── batch-summary.tsx
│   │       │   ├── reports.tsx
│   │       │   └── settings.tsx
│   │       ├── components/
│   │       │   ├── BatchCard.tsx
│   │       │   └── StatCard.tsx
│   │       ├── constants/
│   │       │   └── theme.ts
│   │       ├── services/
│   │       │   └── api.ts
│   │       ├── stores/
│   │       │   └── farmerStore.ts
│   │       ├── types/
│   │       │   └── index.ts
│   │       ├── scripts/
│   │       │   └── smoke-test.js
│   │       ├── app.json
│   │       ├── package.json
│   │       ├── tsconfig.json
│   │       └── README.md
│   ├── enose_model_training/                    # 模型訓練工作區
│   └── pineapple_deployment_system/             # Arduino 韌體
│
└── README.md
```

---

## 11. 模型資訊 Model Information

### 11.1 電子鼻成熟度模型

| 項目 | 說明 |
|------|------|
| 演算法 | ExtraTreesClassifier |
| 輸入窗口 | 30 秒 |
| 特徵數量 | 11 個統計特徵 |
| 分類類別 | 未熟 / 初熟 / 成熟 / 過熟 |
| 模型檔案 | `Semester 2 Final Exam (三下-期末)/pineapple_final/deploy_student.pkl` |

### 11.2 影像品種辨識模型

| 項目 | 說明 |
|------|------|
| 偵測模型 | YOLOv8n |
| 分類模型 | EfficientNet-B0 |
| 分類類別 | 金鑽 / 本土種 / 牛奶 / 西瓜 |
| 權重位置 | `Semester 2 Final Exam (三下-期末)/pineapple_detection/weights/` |

---

## 12. Demo 影片與截圖 Demo Video & Screenshots

- [期中 Demo 影片（Google Drive）](https://drive.google.com/file/d/1zQTGWSUGKHxx7ukhSpP41EWQJNEOJPet/view?usp=drivesdk)
- [期末 Demo 影片（Google Drive）](https://drive.google.com/file/d/1Z_MbwVsv4nYf6GSiNdPcTrRvedTm5LH4/view?usp=drivesdk)

---

## 13. 常見問題 Troubleshooting

**Q: 農民端 App 路徑在哪？**

```text
Semester 2 Final Exam (三下-期末)/app/Farmer_pineapple-ripeness-main/
```

**Q: 農民端 App 如何執行？**

```bash
cd "Semester 2 Final Exam (三下-期末)/app/Farmer_pineapple-ripeness-main"
npm install
npm run start
```

**Q: 農民端 App 如何測試？**

```bash
npm run test
```

**Q: `inference_30s.py` 找不到 Arduino 串口？**

檢查 Arduino 是否接上，並確認 `/dev/ttyUSB0`、`/dev/ttyACM0` 或 Windows COM Port 正確。

**Q: 影像辨識伺服器啟動失敗？**

若無 GPU，可安裝 CPU 版 PyTorch：

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
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
