# 🍍 Farmer Pineapple Ripeness App

本資料夾為農民端 App，已依據 `Tinazhen/Farmer_pineapple/expo/` 的主要 Expo / React Native 架構移植到：

```text
 electronic-nose-pineapple-ripeness-assessment/
└── Semester 2 Final Exam (三下-期末)/
    └── app/
        └── Farmer_pineapple-ripeness-main/
```

此 App 用於農民端批次建立、批次掃描、成熟度統計、報告查看與後端連線設定。

---

## 1. 來源與定位

| 項目 | 說明 |
|------|------|
| 來源參考 | `Tinazhen/Farmer_pineapple/expo/` |
| 目前位置 | `Semester 2 Final Exam (三下-期末)/app/Farmer_pineapple-ripeness-main/` |
| 技術 | Expo Router、React Native、TypeScript、React Query、Context Store |
| 使用者 | 農民、集貨場人員、專題展示人員 |
| 後端 | Raspberry Pi `pineapple_final/app_local.py` 或 Gateway API |

---

## 2. 專案架構

```text
Farmer_pineapple-ripeness-main/
├── app/                              # Expo Router 路由
│   ├── _layout.tsx                   # 全域 Root Layout、Provider、Stack
│   ├── login.tsx                     # 登入頁路由
│   ├── modal.tsx                     # 資訊彈窗
│   ├── (tabs)/                       # 底部 Tab 導航
│   │   ├── _layout.tsx               # Tab Layout
│   │   ├── index.tsx                 # 首頁 tab
│   │   ├── batches.tsx               # 批次 tab
│   │   ├── scan.tsx                  # 掃描入口 tab
│   │   ├── reports.tsx               # 報告 tab
│   │   └── settings.tsx              # 設定 tab
│   └── batches/
│       ├── create.tsx                # 建立批次
│       └── [batchId]/
│           ├── index.tsx             # 批次詳情
│           ├── scan.tsx              # 指定批次掃描
│           └── summary.tsx           # 指定批次摘要
│
├── components/                       # 共用元件
│   ├── AppButton.tsx                 # 共用按鈕
│   ├── DemoScrollView.tsx            # 展示用 ScrollView 包裝
│   ├── BatchCard.tsx                 # 舊版批次卡片保留
│   └── StatCard.tsx                  # 舊版統計卡片保留
│
├── constants/                        # 常數與樣式
│   ├── i18n.ts                       # 中英文文字表
│   └── theme.ts                      # 色彩、間距、字級
│
├── screens/                          # 畫面邏輯
│   ├── LoginScreen.tsx
│   ├── HomeScreen.tsx
│   ├── BatchesScreen.tsx
│   ├── ScanEntryScreen.tsx
│   ├── CreateBatchScreen.tsx
│   ├── BatchDetailScreen.tsx
│   ├── BatchScanScreen.tsx
│   ├── BatchSummaryScreen.tsx
│   ├── ReportsScreen.tsx
│   └── SettingsScreen.tsx
│
├── store/
│   └── app-store.tsx                 # AppProvider 與全域狀態管理
│
├── types/
│   ├── models.ts                     # 批次、樣本、設定型別
│   └── index.ts                      # 舊版型別保留
│
├── utils/
│   └── helpers.ts                    # ID、日期、數值工具
│
├── services/
│   └── api.ts                        # API 封裝 / mock fallback
│
├── scripts/
│   └── smoke-test.js                 # 結構完整性測試
│
├── app.json                          # Expo 設定
├── package.json                      # 套件與 scripts
├── tsconfig.json                     # TypeScript 設定
└── README.md                         # 本說明文件
```

---

## 3. 頁面路由

| 路由 | 對應畫面 | 說明 |
|------|----------|------|
| `/login` | `LoginScreen` | PIN 登入 / Demo 模式 |
| `/(tabs)` | Tab Layout | 底部導航 |
| `/(tabs)/index` | `HomeScreen` | 今日統計、快速掃描、最近批次 |
| `/(tabs)/batches` | `BatchesScreen` | 批次搜尋、批次列表 |
| `/(tabs)/scan` | `ScanEntryScreen` | 掃描入口 |
| `/(tabs)/reports` | `ReportsScreen` | 批次報告列表 |
| `/(tabs)/settings` | `SettingsScreen` | RPi URL、抽樣比例、語言設定 |
| `/batches/create` | `CreateBatchScreen` | 建立今日批次 |
| `/batches/[batchId]` | `BatchDetailScreen` | 單一批次詳情 |
| `/batches/[batchId]/scan` | `BatchScanScreen` | 指定批次掃描 |
| `/batches/[batchId]/summary` | `BatchSummaryScreen` | 指定批次摘要 |
| `/modal` | `ModalScreen` | App 資訊 |

---

## 4. 狀態資料結構

主要資料集中在：

```text
store/app-store.tsx
```

包含：

| 狀態 | 說明 |
|------|------|
| `isAuthenticated` | 是否已登入 |
| `isDemoMode` | 是否為 Demo 模式 |
| `batches` | 批次資料 |
| `samples` | 掃描樣本資料 |
| `settings` | 語言、後端 URL、抽樣比例、裝置設定 |
| `login()` | PIN 登入，預設 PIN：`1234` |
| `enterDemo()` | 直接進入 Demo 模式 |
| `createBatch()` | 建立批次 |
| `addSample()` | 新增掃描樣本 |
| `updateBatchStatus()` | 更新批次狀態 |
| `updateSettings()` | 更新設定 |

---

## 5. 後端 API 對接

目前農民端 App 保留後端設定入口，可在 `Settings` 頁面設定 Raspberry Pi URL。

預設 URL：

```text
http://172.20.10.2:5000
```

建議後端：

```text
GET  /ping
POST /scan/start
```

目前 `BatchScanScreen` 保留展示用 mock 掃描結果，正式接後端時可將掃描邏輯改成呼叫：

```text
services/api.ts
```

---

## 6. 安裝

### 6.1 進入資料夾

```bash
cd "Semester 2 Final Exam (三下-期末)/app/Farmer_pineapple-ripeness-main"
```

### 6.2 安裝套件

使用 npm：

```bash
npm install
```

或使用 bun：

```bash
bun install
```

---

## 7. 執行

### 7.1 啟動 Expo

```bash
npm run start
```

啟動後可選：

```text
w  Web 瀏覽器
 a  Android 裝置 / 模擬器
 i  iOS 模擬器（macOS）
```

### 7.2 Web 模式

```bash
npm run start-web
```

### 7.3 Android / iOS

```bash
npm run android
npm run ios
```

---

## 8. 測試

### 8.1 結構測試

```bash
npm run test
```

此測試會確認：

- `app/(tabs)` 路由是否存在。
- `app/batches/[batchId]` 動態路由是否存在。
- `screens/` 是否有對應畫面。
- `store/app-store.tsx`、`types/models.ts`、`utils/helpers.ts` 是否存在。
- `package.json` 必要 scripts 是否存在。

### 8.2 Lint

```bash
npm run lint
```

---

## 9. 使用流程

```text
開啟 App
    ↓
輸入 PIN 1234 或使用 Demo 模式
    ↓
進入首頁
    ↓
建立批次
    ↓
進入該批次掃描頁
    ↓
新增掃描樣本
    ↓
查看批次摘要
    ↓
標記完成並進入報告列表
```

---

## 10. 可執行檔案說明

本專案是 Expo / React Native App，沒有傳統 `.exe` 檔。

可執行入口為：

| 指令 | 用途 |
|------|------|
| `npm run start` | 啟動 Expo Dev Server |
| `npm run start-web` | Web 模式執行 |
| `npm run android` | Android 模擬器 / 裝置 |
| `npm run ios` | iOS 模擬器 |
| `npm run test` | 結構完整性測試 |
| `npm run lint` | 程式碼檢查 |

---

## 11. 與原始 `Tinazhen/Farmer_pineapple/expo` 的對應

| 原始架構 | 目前位置 |
|----------|----------|
| `expo/app/_layout.tsx` | `app/_layout.tsx` |
| `expo/app/login.tsx` | `app/login.tsx` |
| `expo/app/(tabs)/` | `app/(tabs)/` |
| `expo/app/batches/[batchId]/` | `app/batches/[batchId]/` |
| `expo/screens/` | `screens/` |
| `expo/store/app-store.tsx` | `store/app-store.tsx` |
| `expo/types/models.ts` | `types/models.ts` |
| `expo/constants/` | `constants/` |

---

## 12. 備註

此版本已將農民端 App 放入期末專案資料夾，方便期末展示與整合管理。若要完全同步 `Tinazhen/Farmer_pineapple/expo` 後續更新，建議之後以 GitHub subtree 或手動同步方式維護。
