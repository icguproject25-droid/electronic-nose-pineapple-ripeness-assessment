<div align="center">

# 🍍 鳳梨智慧辨識系統 — 期末整合版
### Pineapple Smart Recognition System — Final Exam

*電子鼻成熟度辨識 × 影像品種辨識 × 整合 Web 介面 × 行動 App*

### [🎬 期末 Demo 影片](https://drive.google.com/file/d/1Z_MbwVsv4nYf6GSiNdPcTrRvedTm5LH4/view?usp=drivesdk)
### 🎬 [20260601 報告 Demo 影片](https://drive.google.com/file/d/1jPS8nS9LenRPj_xzRBxOc3c53piBs48R/view?usp=drivesdk)

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

| 功能 | 說明 |
|------|------|
| 影像品種辨識 | YOLOv8 偵測 + EfficientNet-B0 分類，支援四種鳳梨品種 |
| App API Gateway | 行動 App 與網頁的統一 API 中繼服務 |
| 整合 Web 介面 | 一頁切換電子鼻成熟度 + 影像品種辨識兩大功能 |
| 推論校正機制 | 加入空氣防呆、早期熟度校正、過熟傾向提示 |
| Demo 模式完整化 | 可選擇 demo case 與成熟度標籤，無需硬體即可展示 |
| warmup 參數 | 支援 0 / 60 / 180 秒預熱，提升推論準確率 |
| Docker 備援 | 影像品種辨識部署至學校 VM Docker，筆電故障時仍可提供 API |
| 農民端 App | 新增 `app/Farmer_pineapple-ripeness-main/`，提供批次掃描與報表管理架構 |

---

## 2. 系統架構 System Architecture

```text
使用者 / User
├── 瀏覽器 Browser
│   └── 整合 Web 介面 Port 8000
│       ├── 電子鼻成熟度 Web Port 5000
│       └── 影像品種辨識 API Port 5001
│
└── 手機 App Mobile Apps
    ├── 農民端 App Farmer App
    │   └── App Gateway / RPi API
    └── 消費端 App Consumer App
        └── App Gateway / RPi API

Raspberry Pi 3
├── pineapple_final/            # 電子鼻成熟度推論
├── pineapple_app_gateway/      # App / Web API Gateway
├── 整合網頁/                   # 整合入口網站
└── Arduino Mega 2560           # 感測器資料擷取

Windows PC / Docker VM
└── pineapple_detection/        # YOLOv8 + EfficientNet-B0 影像品種辨識
```

**Port 對照表：**

| 服務 | Port | 執行位置 | 主程式 |
|------|------|----------|--------|
| 電子鼻成熟度網頁 | 5000 | Raspberry Pi | `pineapple_final/app_local.py` |
| 影像品種辨識 API | 5001 | Windows PC / Docker VM | `pineapple_detection/server_variety.py` |
| App API Gateway | 5002 | Raspberry Pi | `pineapple_app_gateway/app_gateway_v2.py` |
| 整合 Web 入口 | 8000 | Raspberry Pi | `整合網頁/pineapple_unified_web/app.py` |

---

## 3. 子系統說明 Sub-systems

| 資料夾 | 用途 |
|--------|------|
| `pineapple_final/` | 電子鼻成熟度推論主系統，部署於 Raspberry Pi |
| `pineapple_detection/` | 影像品種辨識伺服器，跑在 Windows PC 或 Docker VM |
| `pineapple_app_gateway/` | App / Web 的 API 中繼服務 |
| `整合網頁/pineapple_unified_web/` | 整合入口網站 |
| `app/Consumer_pineapple-ripeness-main/` | 消費端 React Native App (Expo) |
| `app/Farmer_pineapple-ripeness-main/` | 農民端 React Native App (Expo)，批次掃描與報表管理 |
| `enose_model_training/` | 模型訓練 Notebook 與部署包 |
| `pineapple_deployment_system/` | Arduino 韌體 |

---

## 4. 硬體需求 Hardware Requirements

| 元件 | 規格 |
|------|------|
| Raspberry Pi 3 Model B | 執行電子鼻推論主系統、Gateway、整合網頁 |
| Arduino Mega 2560 | 感測器訊號擷取，USB 接 RPi |
| MQ-2 / MQ-3 / MQ-9 / MQ-135 | VOC 氣體感測 |
| TGS2602 | 有機溶劑感測 |
| BME280（I²C） | 溫度 / 濕度 / 氣壓 |
| Windows PC | 執行影像辨識伺服器 |

---

## 5. 軟體需求 Software Requirements

| 子系統 | 主要技術 |
|--------|----------|
| 電子鼻主系統 | Python、scikit-learn、pandas、pyserial |
| 影像品種辨識 | Python、Flask、YOLOv8、EfficientNet-B0、PyTorch |
| App Gateway | Python、Flask、requests |
| 整合 Web | Python、Flask |
| 農民端 App | Expo Router、React Native、TypeScript、Zustand、React Query |
| 消費端 App | Expo Router、React Native、TypeScript、Zustand |

---

## 6. 安裝 Installation

### 6.1 Arduino 韌體燒錄

```text
開啟 pineapple_deployment_system/use_this/use_this.ino
選擇 Arduino Mega or Mega 2560
選擇正確 COM Port
Upload
```

### 6.2 電子鼻主系統（Raspberry Pi）

```bash
cd ~/pineapple_final
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements_rpi.txt
```

### 6.3 App Gateway（Raspberry Pi）

```bash
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

### 6.5 行動 App

```bash
cd app/Farmer_pineapple-ripeness-main
npm install
npm run start
```

```bash
cd app/Consumer_pineapple-ripeness-main/expo
npm install
npm run start
```

---

## 7. 快速開始 Quick Start

```bash
# 電子鼻主系統
cd pineapple_final
python app_local_demo_early_corrected_v4.py

# RPi 即時推論
python calibrate_air_30s.py
python inference_30s.py

# Gateway
cd ../pineapple_app_gateway
python app_gateway_v2.py

# 影像辨識
cd ../pineapple_detection
python server_variety.py

# 整合 Web
cd ../整合網頁
bash start_pineapple_system.sh
```

---

## 8. 行動 App Mobile Apps

系統整合兩個 Expo / React Native App，分別供農民與消費者使用。

### 8.1 農民端 App（Farmer App）

**程式碼路徑：** `app/Farmer_pineapple-ripeness-main/`

#### 專案架構

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
├── constants/                 # 全域設定
│   └── theme.ts
├── services/                  # API 封裝
│   └── api.ts
├── stores/                    # 狀態管理
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
cd app/Farmer_pineapple-ripeness-main
npm install
npm run start
npm run test
```

---

### 8.2 消費端 App（Consumer App）

**程式碼路徑：** `app/Consumer_pineapple-ripeness-main/expo/`

#### 專案架構

```text
Consumer_pineapple-ripeness-main/
└── expo/
    ├── app/
    ├── components/
    ├── constants/
    ├── contexts/
    ├── assets/
    ├── package.json
    └── README.md
```

#### 執行

```bash
cd app/Consumer_pineapple-ripeness-main/expo
npm install
npm run start
```

---

## 9. 輸入 / 輸出格式 Input / Output Format

### 9.1 電子鼻推論

**Arduino Serial 輸出格式：**

```text
timestamp_ms,MQ2_raw,MQ3_raw,MQ9_raw,MQ135_raw,TGS2602_raw,TGS2620_raw,Temp_C,Humidity_pct,Pressure_hPa
```

**推論輸出：**

```json
{
  "stage": 2,
  "label": "成熟",
  "confidence": 0.82
}
```

### 9.2 影像品種辨識

```http
POST http://<PC-IP>:5001/predict
```

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

| 模型 | 技術 | 位置 |
|------|------|------|
| 電子鼻成熟度模型 | ExtraTreesClassifier | `pineapple_final/deploy_student.pkl` |
| 影像偵測模型 | YOLOv8n | `pineapple_detection/weights/yolov8n_pineapple_best.pt` |
| 影像分類模型 | EfficientNet-B0 | `pineapple_detection/weights/b0_focal_best.pth` |

---

## 11. 專案結構 Project Structure

```text
Semester 2 Final Exam (三下-期末)/
│
├── pineapple_final/                              # 電子鼻推論主系統
├── pineapple_detection/                          # 影像品種辨識
├── pineapple_app_gateway/                        # App / Web API Gateway
├── 整合網頁/                                     # 整合 Web 介面
│
├── app/
│   ├── Consumer_pineapple-ripeness-main/         # 消費端 App
│   │   └── expo/
│   │
│   └── Farmer_pineapple-ripeness-main/           # 農民端 App
│       ├── app/
│       │   ├── _layout.tsx
│       │   ├── index.tsx
│       │   ├── batches.tsx
│       │   ├── batch-create.tsx
│       │   ├── batch-scan.tsx
│       │   ├── batch-summary.tsx
│       │   ├── reports.tsx
│       │   └── settings.tsx
│       ├── components/
│       │   ├── BatchCard.tsx
│       │   └── StatCard.tsx
│       ├── constants/
│       │   └── theme.ts
│       ├── services/
│       │   └── api.ts
│       ├── stores/
│       │   └── farmerStore.ts
│       ├── types/
│       │   └── index.ts
│       ├── scripts/
│       │   └── smoke-test.js
│       ├── app.json
│       ├── package.json
│       ├── tsconfig.json
│       └── README.md
│
├── enose_model_training/                         # 模型訓練工作區
└── pineapple_deployment_system/                  # Arduino 韌體
```

---

## 12. Demo 影片 Demo Video

- [🎬 期末整合 Demo 影片（Google Drive）](https://drive.google.com/file/d/1Z_MbwVsv4nYf6GSiNdPcTrRvedTm5LH4/view?usp=drivesdk)

---

## 13. 正式展示流程 Demo Presentation Flow

```text
1. 啟動影像辨識 server_variety.py
2. 啟動 Raspberry Pi 整合服務 start_pineapple_system.sh
3. 開啟整合 Web 介面 http://<RPi-IP>:8000
4. 開啟農民端 / 消費端 App
5. App 設定後端 URL
6. 執行掃描或 Demo 測試
```

---

## 14. 常見問題 Troubleshooting

**Q: 農民端 App 路徑在哪？**

```text
app/Farmer_pineapple-ripeness-main/
```

**Q: 農民端 App 如何執行？**

```bash
cd app/Farmer_pineapple-ripeness-main
npm install
npm run start
```

**Q: 農民端 App 如何測試？**

```bash
npm run test
```

**Q: 農民端 App 掃描後回傳 mock 資料？**

請到 Settings 確認後端 URL，並確認 RPi 上 `app_local.py` 已啟動。

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
