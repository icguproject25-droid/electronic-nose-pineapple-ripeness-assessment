<div align="center">

# 🍍 鳳梨成熟度辨識系統
### Pineapple Ripeness Detection System

*電子鼻 × 邊緣運算 × 機器學習 | Electronic Nose × Edge Computing × Machine Learning*

![Python](https://img.shields.io/badge/Python-3.7+-3776AB?style=flat-square&logo=python&logoColor=white)
![Arduino](https://img.shields.io/badge/Arduino-Mega_2560-00979D?style=flat-square&logo=arduino&logoColor=white)
![Raspberry Pi](https://img.shields.io/badge/Raspberry_Pi-3_Model_B-A22846?style=flat-square&logo=raspberry-pi&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-ExtraTrees-F7931E?style=flat-square&logo=scikit-learn&logoColor=white)
![React Native](https://img.shields.io/badge/React_Native-App-61DAFB?style=flat-square&logo=react&logoColor=black)
![Flask](https://img.shields.io/badge/Flask-2.0+-000000?style=flat-square&logo=flask&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Version](https://img.shields.io/badge/Version-v1.0-blue?style=flat-square)

</div>

---

## 📖 專案簡介

本系統為**非破壞性鳳梨成熟度辨識系統**，結合電子鼻氣體感測器陣列、Arduino Mega、Raspberry Pi 3 以及機器學習模型，透過量測鳳梨周圍揮發性有機化合物（VOC）訊號，輸出**四階段成熟度分類結果**，協助農民、驗收人員與消費者進行快速且客觀的成熟度判定。

### 🎯 目標使用者

| 使用者 | 使用情境 |
|--------|----------|
| 🌾 **農民** | 採收與分級前快速判斷，減少農損 |
| 🔍 **驗收人員** | 降低主觀經驗差異，提供量化依據 |
| 🛒 **消費者** | 判斷是否適合立即食用 |

### 🍍 成熟度分級說明

| Stage | 說明 | 建議 |
|-------|------|------|
| **Stage 0** | 未成熟 | 再等 3–5 天 |
| **Stage 1** | 初熟 | 再等 1–2 天 |
| **Stage 2** | 完熟 | 立即食用 ✅ |
| **Stage 3** | 過熟 | 盡快食用 ⚠️ |

---

## 🏗️ 系統架構
┌─────────────────────────────────────────────────────────────┐
│ 👤 使用者端 User Interface Layer │
│ 消費端 App (React Native) │ 農民端 App │ Flask 模擬介面 │
├─────────────────────────────────────────────────────────────┤
│ 🌐 應用服務層 Application Service Layer │
│ SSH 遠端控制 │ API 服務 │ 結果紀錄 / 報表 │
├─────────────────────────────────────────────────────────────┤
│ 🖥️ 運算處理層 Processing Layer │
│ Raspberry Pi 3 │ 特徵工程 │ ExtraTrees 推論 │ 後處理邏輯 │
├─────────────────────────────────────────────────────────────┤
│ 🔌 資料傳輸層 Data Transfer Layer │
│ USB Serial (115200 baud) │ I²C (BME280) │
├─────────────────────────────────────────────────────────────┤
│ 🔬 感測層 Sensing Layer │
│ Arduino Mega 2560 │ MQ 系列感測器 │ TGS 系列 │ BME280 │
└─────────────────────────────────────────────────────────────┘


---

## 🔧 硬體需求

### 元件清單

| 元件 | 規格 | 數量 | 用途 |
|------|------|------|------|
| Arduino Mega 2560 | ATmega2560, 16MHz | 1 | 感測器資料擷取 |
| Raspberry Pi 3 Model B | 1.2GHz Quad-Core, 1GB RAM | 1 | 邊緣運算、模型推論 |
| MQ-2 氣體感測器 | 煙霧 / 可燃氣體 | 1 | VOC 特徵擷取 |
| MQ-3 氣體感測器 | 酒精 / 乙醇 ⭐ | 1 | 酒精類揮發物偵測 |
| MQ-9 氣體感測器 | CO / 可燃氣體 | 1 | 一氧化碳類特徵 |
| MQ-135 氣體感測器 | 空氣品質 / 氨氣 | 1 | 氨氣類揮發物 |
| TGS2602 感測器 | VOC / 氨氣 ⭐⭐ | 1 | 核心 VOC 特徵（模型權重最高） |
| TGS2620 感測器 | 酒精 / 有機溶劑 | 1 | 有機溶劑類特徵 |
| BME280 | 溫度 / 濕度 / 氣壓 | 1 | 環境監測 |
| 麵包板 + 杜邦線 | 標準尺寸 | 若干 | 電路連接 |
| USB Type A-B 連接線 | — | 1 | Arduino ↔ Raspberry Pi |
| 電源供應器 | 5V 2.5A | 1 | Raspberry Pi 供電 |

### 硬體接線說明

- **氣體感測器（MQ / TGS）**：類比訊號輸出，連接至 Arduino `A0–A5`（10-bit ADC）
- **BME280**：I²C 協定，連接至 Arduino `SDA / SCL`
- **Arduino → Raspberry Pi**：USB Serial，`/dev/ttyACM0`，115200 baud

---

## 💻 軟體需求

### 開發環境

| 類別 | 規格 |
|------|------|
| Raspberry Pi OS | Debian-based Linux（最新穩定版） |
| Python | 3.7+ |
| Arduino IDE | 1.8+ |
| 版本控制 | Git / GitHub |

### Python 套件安裝

```bash
pip install scikit-learn numpy pandas flask paramiko pyserial
```

或使用 `requirements.txt`：

```bash
pip install -r requirements.txt
```

### 專案檔案結構
📦 pineapple-ripeness-detection
├── 📄 deploystudent.pkl # ExtraTrees 部署模型 (6.2 MB)
├── 📄 featurecolumns.json # 11 項部署特徵名稱清單
├── 📄 deploymeta.json # 模型元資料 (Stage 映射)
├── 📄 airbase.json # 空氣基準線參數（校正後產生）
├── 📄 requirements.txt # Python 相依套件清單
├── 🐍 calibrate_air_30s.py # 空氣基線校正主程式
├── 🐍 inference_30s.py # 30 秒窗口推論主程式
├── 🐍 applocal.py # Flask 模擬測試介面
└── 📁 app/
├── 📁 consumer/ # 消費端 React Native App
│ ├── Home.tsx
│ ├── ScanProcess.tsx
│ ├── Result.tsx
│ └── History.tsx
└── 📁 farmer/ # 農民端 React Native App
├── FarmerHome.tsx
├── BatchCreate.tsx
├── BatchScan.tsx
├── BatchResult.tsx
└── ReportAnalysis.tsx

---

## 🚀 使用方式

### Step 1｜硬體連接

1. 依接線圖將六種氣體感測器連接至 Arduino `A0–A5`
2. 將 BME280 以 I²C 接至 Arduino `SDA / SCL`
3. 以 USB 線連接 Arduino Mega 與 Raspberry Pi 3
4. 確認裝置路徑（通常為 `/dev/ttyACM0`）

### Step 2｜部署環境設定（Raspberry Pi）

```bash
# 建立 Python 虛擬環境
python3 -m venv venv
source venv/bin/activate

# 安裝相依套件
pip install -r requirements.txt

# 確認模型檔案與 JSON 設定檔皆在同一目錄
ls deploystudent.pkl featurecolumns.json deploymeta.json
```

### Step 3｜空氣基線校正

> ⚠️ 每次量測前，或環境條件明顯改變時，須重新執行校正

```bash
# 預設暖機 60 秒，校正 30 秒
python3 calibrate_air_30s.py

# 首次使用建議暖機 180 秒
python3 calibrate_air_30s.py --warmup-sec 180
```

校正完成後產生 `airbase.json`，格式如下：

```json
{
  "MQ2":     { "mean": 450.2, "std": 12.3, "min": 420, "max": 480 },
  "MQ3":     { "mean": 380.5, "std": 15.1, "min": 350, "max": 410 },
  "MQ9":     { "mean": 312.0, "std": 10.2, "min": 290, "max": 335 },
  "MQ135":   { "mean": 520.1, "std": 18.4, "min": 490, "max": 555 },
  "TGS2602": { "mean": 280.3, "std":  9.7, "min": 260, "max": 300 },
  "TGS2620": { "mean": 410.6, "std": 13.5, "min": 385, "max": 435 }
}
```

### Step 4｜成熟度推論

```bash
# 將鳳梨置於感測器前約 5 cm，執行推論
python3 inference_30s.py
```

系統累積 30 秒感測窗口後輸出：
[推論結果]
Stage 0 機率: 0.03
Stage 1 機率: 0.12
Stage 2 機率: 0.79 ← argmax
Stage 3 機率: 0.06

✅ 最終判定：Stage 2（完熟）— 建議立即食用