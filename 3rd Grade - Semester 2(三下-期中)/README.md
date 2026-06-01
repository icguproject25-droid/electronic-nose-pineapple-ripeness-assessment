<div align="center">

# 🍍 鳳梨成熟度辨識系統 — 期中版
### Pineapple Ripeness Detection System — Midterm

### [🎬 期中 Demo 影片](https://drive.google.com/file/d/1zQTGWSUGKHxx7ukhSpP41EWQJNEOJPet/view?usp=drivesdk)

*電子鼻 × 邊緣運算 × 機器學習 | Electronic Nose × Edge Computing × Machine Learning*

![Python](https://img.shields.io/badge/Python-3.7+-3776AB?style=flat-square&logo=python&logoColor=white)
![Arduino](https://img.shields.io/badge/Arduino-Mega_2560-00979D?style=flat-square&logo=arduino&logoColor=white)
![Raspberry Pi](https://img.shields.io/badge/Raspberry_Pi-3_Model_B-A22846?style=flat-square&logo=raspberry-pi&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-ExtraTrees-F7931E?style=flat-square&logo=scikit-learn&logoColor=white)
![React Native](https://img.shields.io/badge/React_Native-Expo-61DAFB?style=flat-square&logo=react&logoColor=black)
![Flask](https://img.shields.io/badge/Flask-2.0+-000000?style=flat-square&logo=flask&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

</div>

---

## 1. 專案簡介 Project Overview

本系統為**非破壞性鳳梨成熟度辨識系統**，結合電子鼻氣體感測器陣列、Arduino Mega、Raspberry Pi 3 以及機器學習模型，透過量測鳳梨周圍揮發性有機化合物（VOC）訊號，輸出**四階段成熟度分類結果**，協助農民、驗收人員與消費者進行快速且客觀的成熟度判定。

| 使用者 | 使用情境 |
|--------|----------|
| 農民 | 採收與分級前快速判斷，減少農損 |
| 驗收人員 | 降低主觀經驗差異，提供量化依據 |
| 消費者 | 判斷是否適合立即食用 |

---

## 2. 功能特色 Features

- 非破壞性：無需切開鳳梨，30 秒完成一次推論
- 邊緣運算：ExtraTrees 模型部署於 Raspberry Pi 3，不依賴雲端
- 後處理校正：空氣防呆（Guard Baseline）+ 過熟覆寫（Override）
- 行動 App：農民端（批次管理）+ 消費端（品種資訊、歷史紀錄）
- Flask 模擬介面：可透過瀏覽器遠端觸發校正與推論

---

## 3. 系統架構 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│            使用者介面層 User Interface Layer                  │
│  消費端 App (React Native) │ 農民端 App │ Flask 模擬介面       │
├─────────────────────────────────────────────────────────────┤
│            應用服務層 Application Service Layer               │
│          SSH 遠端控制 │ API 服務 │ 結果紀錄 / 報表             │
├─────────────────────────────────────────────────────────────┤
│            運算處理層 Processing Layer                        │
│   Raspberry Pi 3 │ 特徵工程 │ ExtraTrees 推論 │ 後處理邏輯    │
├─────────────────────────────────────────────────────────────┤
│            資料傳輸層 Data Transfer Layer                     │
│          USB Serial (115200 baud) │ I²C (BME280)              │
├─────────────────────────────────────────────────────────────┤
│            感測層 Sensing Layer                               │
│   Arduino Mega 2560 │ MQ 系列感測器 │ TGS 系列 │ BME280       │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. 硬體需求 Hardware Requirements

| 元件 | 規格 | 用途 |
|------|------|------|
| Arduino Mega 2560 | ATmega2560, 16MHz | 感測器資料擷取 |
| Raspberry Pi 3 Model B | 1.2GHz 四核, 1GB RAM | 邊緣推論主機 |
| MQ-2 | 煙霧 / 可燃氣體 | VOC 特徵擷取 |
| MQ-3 | 酒精 / 乙醇 | 酒精類揮發物偵測 |
| MQ-9 | CO / 可燃氣體 | 一氧化碳類特徵 |
| MQ-135 | 空氣品質 / 氨氣 | 氨氣類揮發物 |
| TGS2602 | VOC / 氨氣 | 核心 VOC 特徵（模型權重最高） |
| TGS2620 | 酒精 / 有機溶劑 | 有機溶劑類特徵 |
| BME280 | 溫度 / 濕度 / 氣壓（I²C） | 環境監測 |
| USB Type A-B | — | Arduino ↔ Raspberry Pi |

**接線說明：**
- 氣體感測器（MQ / TGS）：類比訊號輸出 → Arduino `A0–A5`（10-bit ADC）
- BME280：I²C → Arduino `SDA / SCL`
- Arduino → RPi：USB Serial `/dev/ttyACM0`，115200 baud

---

## 5. 軟體需求 Software Requirements

```
Python 3.7+
scikit-learn
numpy
pandas
flask
paramiko
pyserial
joblib
```

---

## 6. 安裝 Installation

### 6.1 Arduino 韌體燒錄

1. 開啟 Arduino IDE 1.8+
2. 開啟 `pineapple_deployment_system/use_this.ino`
3. 板子選 **Arduino Mega or Mega 2560**，選對應 COM Port
4. 點 Upload

### 6.2 Raspberry Pi 部署環境

```bash
# SSH 進 Raspberry Pi 後
cd ~/pineapple_deployment_system

python3 -m venv .venv
source .venv/bin/activate

pip install scikit-learn numpy pandas flask paramiko pyserial joblib
```

確認以下檔案都在同一目錄：

```
deploy_student.pkl
feature_columns.json
deploy_meta.json
```

### 6.3 App（農民端 / 消費端）

```bash
# 農民端
cd App/Farmer_pineapple-main/expo
bun install        # 或 npm install
bunx expo start

# 消費端
cd App/Consumer_pineapple-ripeness-main/expo
bun install
bunx expo start
```

---

## 7. 快速開始 Quick Start

### 7.1 即時偵測（需完整硬體）

**步驟一：空氣基線校正**（首次使用或環境改變時執行）

```bash
cd ~/pineapple_deployment_system
source .venv/bin/activate

# 預設暖機 60 秒，校正 30 秒
python3 calibrate_air_30s.py

# 首次使用建議暖機 180 秒
python3 calibrate_air_30s.py --warmup-sec 180
```

校正完成後產生 `air_base.json`（空氣基線數值）。

**步驟二：鳳梨成熟度推論**

```bash
# 將鳳梨置於感測器前約 5 cm
python3 inference_30s.py
```

系統收集 30 秒後輸出成熟度結果。

### 7.2 Flask 模擬介面（開發 / 展示用）

```bash
python3 app_local.py
# 瀏覽器開啟 http://<RPi-IP>:5000
```

介面提供：Air Baseline 校正按鈕、開始推論、四階段機率長條圖。

---

## 8. 輸入 / 輸出格式 Input / Output Format

### 8.1 Arduino Serial 輸出（115200 baud）

```
timestamp_ms, MQ2_raw, MQ3_raw, MQ9_raw, MQ135_raw, TGS2602_raw, TGS2620_raw, Temp_C, Humidity_pct, Pressure_hPa
```

### 8.2 模型輸入特徵（11 個，30 秒窗口統計量）

```
MQ3_std_norm, MQ3_range_norm, MQ2_MQ3_ratio, MQ3_MQ135_ratio,
MQ9_slope, TGS2602_min_norm, MQ2_auc_norm, MQ2_mean_norm,
MQ9_min_norm, TGS2602_std_norm, MQ9_delta_mean
```

### 8.3 推論輸出

```json
{
  "stage": 2,
  "label": "完熟",
  "confidence": 0.79,
  "probabilities": {
    "Stage 0（未熟）": 0.03,
    "Stage 1（初熟）": 0.12,
    "Stage 2（完熟）": 0.79,
    "Stage 3（過熟）": 0.06
  }
}
```

| Stage | 標籤 | 建議 |
|-------|------|------|
| 0 | 未熟 | 再等 3–5 天 |
| 1 | 初熟 | 再等 1–2 天 |
| 2 | 完熟 | 立即食用 |
| 3 | 過熟 | 盡快食用 |

---

## 9. 機器學習模型 Model Information

### 9.1 訓練流程

```
VOC 量測資料
     │
     ▼
特徵工程（159 項 PID-specific + 7 項 shared-by-date）
     │
     ▼
CatBoost（Teacher）──── 知識蒸餾 ────▶ ExtraTrees（Student）
                                              │
                                              ▼
                                 MI 篩選 11 項核心特徵 → 部署推論
```

### 9.2 訓練資料

| 項目 | 數值 |
|------|------|
| 鳳梨數量 | 14 顆（金鑽鳳梨） |
| Stage 0（未熟） | 32 筆 |
| Stage 1（初熟） | 25 筆 |
| Stage 2（完熟） | 29 筆 |
| Stage 3（過熟） | 21 筆 → 69 筆（Pseudo Labeling 補強） |

### 9.3 模型效能

| 指標 | 數值 |
|------|------|
| LOGO 交叉驗證平均準確率 | **86.15%** |
| Macro F1 Score | **83.09%** |
| 含後處理樣本準確率 | **80.49%** |
| 部署模型大小 | 6.2 MB |

### 9.4 後處理邏輯

```
Guard Baseline（空氣防呆）
  └─ 若感測值接近 air_base.json 基準線
     → 強制輸出 Stage 0，避免空氣被誤判為成熟

Override 邏輯（過熟覆寫）
  └─ 若模型預測 Stage 2 且 TGS2602 / MQ3 特徵超過閾值
     → 覆寫為 Stage 3（過熟）
```

---

## 10. 行動 App Mobile Apps

### 10.1 農民端 App

**路徑：** `App/Farmer_pineapple-main/expo/`

| 頁面 | 功能 |
|------|------|
| 首頁 Home | 今日掃描數、今日異常數、進行中批次數；快速入口 |
| 批次管理 Batches | 列出所有批次（draft / testing / done） |
| 建立批次 | 填寫批次名稱、田區、品種、用途（外銷 / 內銷 / 加工） |
| 批次掃描 Scan | 呼叫 RPi API，取得成熟度、糖度 Brix、黑心病風險、異常旗標 |
| 批次摘要 Summary | 成熟度圓餅圖、批次統計、匯出報告 |
| 設定 Settings | RPi 後端 URL、語言（zh / en）、糖度閾值 |

**API 端點（呼叫 RPi Port 5000）：**

```
GET  /ping        → 確認後端是否上線
POST /scan/start  → 觸發 30 秒掃描
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

**設定後端 URL：**
```
http://172.20.10.2:5000    # 手機熱點環境
http://192.168.0.152:5000  # 一般 Wi-Fi 環境
```

### 10.2 消費端 App

**路徑：** `App/Consumer_pineapple-ripeness-main/expo/`

| 頁面 | 功能 |
|------|------|
| 掃描流程 processing → result | 偵測動畫、音效；顯示成熟度結果；可提交回饋 |
| 品種介紹 varieties | 四種鳳梨品種介紹（金鑽／本土／牛奶／西瓜） |
| 知識庫 knowledge-base | 鳳梨農業知識 |
| 季節指南 seasonal-guide | 各品種產季與採購建議 |
| 趣味問答 trivia | 鳳梨趣味知識卡片 |
| 歷史記錄 history | 過去掃描紀錄；可補提交人工回饋 |
| 待上傳 pending-uploads | 離線暫存紀錄，連線後批次同步 |

---

## 11. 專案結構 Project Structure

```
3rd Grade - Semester 2 (三下-期中)/
│
├── arduino_mega_data_collection/          # Arduino 資料擷取韌體
│   ├── air_baseline_collection.ino        # 空氣基線資料蒐集
│   └── pineapple_sample_collection.ino    # 鳳梨樣本資料蒐集
│
├── enose_model_training/
│   └── orkspace/                          # 模型訓練工作區（注：實際資料夾名稱）
│       ├── data/                          # 原始量測資料（Excel）
│       ├── deploy_rpi_et_30s_noday/       # 生產部署用模型包（主要版本）
│       ├── deploy_rpi_et_30s_noday_s3_sensitive/ # 過熟敏感版本
│       ├── models/                        # 所有訓練版本的模型檔案
│       ├── reports/                       # 訓練報表與評估結果
│       ├── labeling_perfect_final.ipynb   # 主訓練 Notebook（標注 + 特徵 + 訓練）
│       ├── feature_columns.json           # 11 項部署特徵欄位定義
│       ├── cutpoints.json                 # CatBoost 閾值設定
│       ├── model_final.pkl                # 最終訓練模型
│       └── stage_timeline.png             # 成熟度時間軸圖
│
├── pineapple_deployment_system/           # Raspberry Pi 部署系統
│   ├── app_local.py                       # Flask 模擬測試介面
│   ├── calibrate_air_30s.py               # 空氣基線校正主程式
│   ├── inference_30s.py                   # 30 秒窗口推論主程式
│   └── use_this.ino                       # Arduino 搭配推論用韌體
│
├── App/
│   ├── Consumer_pineapple-ripeness-main/  # 消費端 App (Expo/React Native)
│   └── Farmer_pineapple-main/             # 農民端 App (Expo/React Native)
│
└── files(設計文件&簡報)/                  # 期中報告 PDF 與設計規格書
```

> `orkspace` 為實際資料夾名稱；`noday` 代表不使用日期特徵的部署版本。

---

## 12. 常見問題 Troubleshooting

**Q: 找不到 Arduino（`/dev/ttyACM*` 不存在）**

重新插 USB 並確認 Arduino 已上傳 `use_this.ino`，並給當前使用者串口權限：

```bash
sudo usermod -a -G dialout $USER
# 重新登入後生效
```

---

**Q: 推論結果持續輸出 Stage 0（空氣防呆觸發）**

感測器未偵測到有效揮發物，可能原因：
1. 鳳梨未放入感測腔體，或距離太遠
2. `air_base.json` 基線不準確 → 重新執行 `calibrate_air_30s.py`
3. 感測器暖機不足 → 等待 60–180 秒後重新推論

---

**Q: Flask 介面打不開（無法連到 RPi）**

確認 `app_local.py` 使用 `host="0.0.0.0"` 啟動，並確認手機 / 電腦與 RPi 在同一 Wi-Fi 下：

```python
app.run(host="0.0.0.0", port=5000, debug=False)
```

---

**Q: 農民端 App 掃描後回傳模擬資料**

App 內建 fallback 邏輯：後端離線時自動回傳亂數模擬值。至「設定」頁面確認 RPi IP 填寫正確，並確認 `app_local.py` 正在執行。

---

## 13. 開發團隊 Team Members

本專題由長庚大學（Chang Gung University）學生共同開發：

| 學號 | 姓名 |
|------|------|
| B1144143 | 陳玟妤 |
| B1229062 | 林冠妤 |
| B1229066 | 陳怡禎 |
| B1229068 | 廖文歆 |

---

## 14. 授權 License

本專案採用 [MIT License](../../LICENSE) 授權。
