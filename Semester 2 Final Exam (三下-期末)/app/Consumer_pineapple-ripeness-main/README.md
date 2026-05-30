# 🍍 鳳梨成熟度與品種辨識智慧檢測系統 APP

## 專案簡介

本專案為一套結合物聯網（IoT）、機器學習（Machine Learning）、影像辨識（Computer Vision）與跨平台行動應用程式技術所開發之智慧農業系統，主要目標為協助使用者快速判斷鳳梨成熟度及辨識鳳梨品種。

系統透過 Raspberry Pi 與多種氣體感測器蒐集鳳梨釋放之揮發性有機化合物（VOC）資訊，搭配訓練完成之成熟度分類模型，進行成熟階段預測；同時結合 EfficientNet-B0 深度學習模型，透過照片辨識鳳梨品種，最終將結果整合至 React Native 開發之 APP 中呈現。

本系統旨在提供農民、農產品業者及一般消費者一套方便、快速且具科學依據的鳳梨品質檢測工具。

---

# 專案特色

## 🍍 氣味成熟度辨識

利用多組氣體感測器偵測鳳梨成熟過程中所釋放之氣體變化，透過機器學習模型分析成熟程度。

辨識結果包含：

* 未熟（Unripe）
* 初熟（Early Ripe）
* 成熟（Ripe）
* 過熟（Overripe）

並提供：

* 成熟度百分比
* 模型信心值
* 感測器數據摘要
* 檢測建議

---

## 📸 鳳梨品種辨識

使用者可透過：

* 手機拍照
* 相簿上傳

進行品種辨識。

目前支援：

* 金鑽鳳梨
* 土鳳梨
* 牛奶鳳梨
* 西瓜鳳梨

辨識結果包含：

* 品種名稱
* 品種中文名稱
* 信心分數
* 各品種機率分布

---

## 📖 鳳梨知識庫

提供鳳梨相關知識內容：

* 品種介紹
* 生長環境
* 採收時機
* 保存方式
* 熟度判斷技巧

讓使用者在檢測之餘也能獲得農業知識。

---

## 🌱 當季導覽

提供：

* 鳳梨產季資訊
* 推薦品種
* 盛產時間
* 購買建議

協助使用者了解不同時期適合購買之鳳梨種類。

---

## 🧮 品質評分系統

根據成熟度與感測器分析結果，自動計算品質評分。

提供：

* 品質分數
* 評級結果
* 建議食用時機

---

## 🎮 鳳梨小知識問答

透過互動問答方式增加使用者對鳳梨相關知識的了解。

內容包含：

* 品種辨識
* 農業知識
* 採收知識
* 保存技巧

---

## 📚 歷史紀錄管理

自動保存檢測結果。

可查詢：

* 檢測日期
* 檢測時間
* 成熟度結果
* 品種辨識結果
* 品質評分
* 信心分數

---

## 🌐 多國語系支援

透過 Language Context 提供：

* 中文
* English

語言切換功能。

---

# 系統架構

```text
使用者 APP
      │
      │ HTTP API
      ▼
 Raspberry Pi Gateway
      │
 ┌────┴────┐
 ▼         ▼

成熟度模型   品種辨識模型
(MQ感測器)  (EfficientNet-B0)

 ▼         ▼

成熟度結果   品種結果

      ▼
 APP 顯示結果
```

---

# 技術架構

## 前端技術

* React Native
* Expo
* Expo Router
* TypeScript

---

## 狀態管理

使用 React Context API：

* CalibrationContext
* SensorContext
* HistoryContext
* UploadQueueContext
* LanguageContext
* TriviaContext

---

## 本地儲存

* AsyncStorage

用於儲存：

* API 設定
* 歷史紀錄
* 語言設定
* 裝置資訊

---

## 後端通訊

* RESTful API
* Fetch API

主要功能：

* 啟動感測
* 查詢進度
* 取得成熟度結果
* 上傳照片辨識

---

## AI 模型

### 成熟度辨識模型

輸入資料：

* MQ2
* MQ3
* MQ9
* MQ135
* TGS2602
* 溫度
* 濕度
* 氣壓

輸出：

* 未熟
* 初熟
* 成熟
* 過熟

---

### 品種辨識模型

模型：

EfficientNet-B0

輸入：

鳳梨照片

輸出：

* 金鑽鳳梨
* 土鳳梨
* 牛奶鳳梨
* 西瓜鳳梨

---

# 專案目錄結構

```text
expo/
├── app/
├── assets/
├── components/
├── constants/
├── contexts/
├── mocks/
├── services/
├── types/
├── utils/
│
├── app.json
├── package.json
├── tsconfig.json
└── README.md
```

---

# 系統需求

## 軟體需求

### Node.js

建議版本：

```bash
Node.js 18+
```

下載：

https://nodejs.org/

---

### npm

Node.js 安裝後自動包含。

確認版本：

```bash
npm -v
```

---

### Git

確認：

```bash
git --version
```

下載：

https://git-scm.com/

---

### Expo CLI

安裝：

```bash
npm install -g expo-cli
```

---

# 環境建置

## 1. 下載專案

```bash
git clone <repository-url>
cd expo
```

---

## 2. 安裝套件

使用 npm：

```bash
npm install
```

或

```bash
npm install --legacy-peer-deps
```

若使用 Bun：

```bash
bun install
```

---

## 3. 啟動專案

```bash
npx expo start
```

或

```bash
npm start
```

啟動後可透過：

* Android Emulator
* iOS Simulator
* Expo Go

進行測試。

---

## Android 執行

```bash
npx expo run:android
```

---

## iOS 執行

```bash
npx expo run:ios
```

---

# Raspberry Pi 後端設定

本 APP 需搭配 Raspberry Pi 後端系統使用。

主要包含：

## 成熟度辨識 Gateway

預設：

```text
http://<raspberry_pi_ip>:5000
```

負責：

* 啟動檢測
* 查詢進度
* 回傳成熟度結果

---

## 品種辨識 API

預設：

```text
http://<raspberry_pi_ip>:5001
```

負責：

* 接收照片
* 執行模型推論
* 回傳品種辨識結果

---

# APP 操作流程

## 成熟度檢測

### Step 1

開啟 APP

### Step 2

進入主選單

### Step 3

選擇：

「開始檢測」

### Step 4

APP 呼叫 Raspberry Pi API

### Step 5

Raspberry Pi 收集 30 秒感測資料

### Step 6

模型執行成熟度分析

### Step 7

回傳結果至 APP

### Step 8

顯示：

* 成熟度
* 成熟百分比
* 信心值
* 建議資訊

---

## 品種辨識

### Step 1

進入品種辨識頁面

### Step 2

拍照或上傳圖片

### Step 3

送出照片

### Step 4

Raspberry Pi 執行 EfficientNet-B0 模型

### Step 5

回傳品種辨識結果

### Step 6

顯示：

* 品種名稱
* 信心分數
* 機率分布

---

# 主要頁面說明

| 頁面    | 功能        |
| ----- | --------- |
| 首頁    | APP 入口    |
| 主選單   | 功能導航      |
| 使用說明  | 教學與操作說明   |
| 資料處理中 | 顯示檢測進度    |
| 檢測結果  | 顯示成熟度分析   |
| 品種辨識  | 上傳照片辨識    |
| 品種介紹  | 顯示品種資訊    |
| 歷史紀錄  | 查看歷史結果    |
| 歷史詳情  | 查看單筆紀錄    |
| 知識庫   | 農業知識      |
| 當季指南  | 產季資訊      |
| 品質計算機 | 品質評估      |
| 小知識問答 | 互動學習      |
| 設定    | API 與系統設定 |

---

# 專案使用硬體

## 感測平台

* Raspberry Pi 3 / 4
* Arduino Mega 2560
* MQ2
* MQ3
* MQ9
* MQ135
* TGS2602
* BME280

---

## 其他設備

* Android 手機
* iPhone
* Wi-Fi 或手機熱點

---

# 未來擴充方向

## 資料庫整合

預計導入：

* MySQL
* PostgreSQL
* Firebase

實現：

* 雲端同步
* 多裝置存取
* 帳號登入

---

## AI 模型優化

* 增加更多鳳梨品種
* 提升成熟度辨識準確率
* 增加資料集規模
* 模型量化部署

---

## 系統功能擴充

* 即時感測監控
* 感測器健康檢查
* 檢測報告匯出 PDF
* QR Code 檢測紀錄
* 農產品品質追蹤

---

# 作者資訊

長庚大學資訊工程學系

畢業專題

智慧鳳梨成熟度與品種辨識系統

---

# 授權聲明

本專案僅供學術研究、教學展示及畢業專題使用。

未經授權不得作為商業用途。
