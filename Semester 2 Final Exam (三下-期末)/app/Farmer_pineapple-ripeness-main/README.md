# 🍍 Farmer Pineapple Ripeness App

農民端 App 是 `electronic-nose-pineapple-ripeness-assessment` 期末整合版中的行動端子系統，主要提供農民或集貨場人員進行批次建立、逐顆掃描、成熟度統計與報告查看。

本專案參考消費端 App 的 Expo / React Native 架構建立，並針對農民端使用情境調整為批次管理流程。

---

## 1. 專案位置

```text
electronic-nose-pineapple-ripeness-assessment/
└── Semester 2 Final Exam (三下-期末)/
    └── app/
        └── Farmer_pineapple-ripeness-main/
```

---

## 2. 專案架構

```text
Farmer_pineapple-ripeness-main/
├── app/                       # Expo Router 頁面
│   ├── _layout.tsx            # 全域路由設定與 React Query Provider
│   ├── index.tsx              # 農民端首頁
│   ├── batches.tsx            # 批次管理頁
│   ├── batch-create.tsx       # 建立批次頁
│   ├── batch-scan.tsx         # 批次掃描頁
│   ├── batch-summary.tsx      # 批次摘要頁
│   ├── reports.tsx            # 報告列表頁
│   └── settings.tsx           # 後端 URL 與參數設定頁
├── components/                # 共用 UI 元件
│   ├── BatchCard.tsx          # 批次卡片元件
│   └── StatCard.tsx           # 統計卡片元件
├── constants/
│   └── theme.ts               # 顏色、間距、圓角、字級設定
├── services/
│   └── api.ts                 # RPi / Gateway API 呼叫封裝
├── stores/
│   └── farmerStore.ts         # Zustand 狀態管理
├── types/
│   └── index.ts               # 共用 TypeScript 型別
├── scripts/
│   └── smoke-test.js          # 專案完整性測試腳本
├── app.json                   # Expo App 設定
├── package.json               # 套件與執行指令
├── tsconfig.json              # TypeScript 設定
└── README.md                  # 安裝、執行、測試說明
```

---

## 3. 功能頁面

| 頁面 | 路由 | 說明 |
|------|------|------|
| 首頁 | `/` | 顯示掃描數、異常數、進行中批次與快速入口 |
| 批次管理 | `/batches` | 顯示全部批次，可選擇批次進入摘要 |
| 建立批次 | `/batch-create` | 建立田區、品種、用途與採樣目標 |
| 批次掃描 | `/batch-scan` | 呼叫後端 `/scan/start` 取得推論結果 |
| 批次摘要 | `/batch-summary` | 統計未熟、成熟、過熟、異常與平均糖度 |
| 報告列表 | `/reports` | 查看完成或已有掃描紀錄的批次 |
| 設定 | `/settings` | 設定後端 URL、糖度門檻並測試 `/ping` |

---

## 4. API 串接

農民端 App 主要呼叫 Raspberry Pi 或 App Gateway。

```http
GET  /ping
POST /scan/start
```

### 4.1 `/ping`

用途：確認後端是否在線。

設定頁會使用此 API 測試手機是否可以連到 Raspberry Pi。

### 4.2 `/scan/start`

用途：觸發一次 30 秒電子鼻掃描。

範例回傳：

```json
{
  "ripeness": "ripe",
  "tss_brix": 14.5,
  "blackheart_risk": "low",
  "anomaly_flag": "normal",
  "confidence": 0.82
}
```

若後端離線，`services/api.ts` 會自動產生 mock 結果，方便展示 App 流程。正式測試時請確認 Raspberry Pi 後端已啟動。

---

## 5. 安裝方式

### 5.1 安裝 Node.js

建議安裝 Node.js LTS 版本。

確認版本：

```bash
node -v
npm -v
```

### 5.2 進入專案資料夾

```bash
cd "Semester 2 Final Exam (三下-期末)/app/Farmer_pineapple-ripeness-main"
```

### 5.3 安裝套件

使用 npm：

```bash
npm install
```

或使用 bun：

```bash
bun install
```

---

## 6. 執行方式

### 6.1 啟動 Expo

```bash
npm run start
```

或：

```bash
npx expo start
```

啟動後可選擇：

- 使用 Expo Go 掃描 QR Code 在手機執行。
- 按 `w` 在 Web 瀏覽器開啟。
- 按 `a` 在 Android 模擬器開啟。
- 按 `i` 在 iOS 模擬器開啟（需 macOS）。

### 6.2 Web 模式

```bash
npm run start-web
```

此模式適合在電腦瀏覽器快速檢查畫面。

---

## 7. Raspberry Pi 後端設定

App 預設後端 URL：

```text
http://172.20.10.2:5000
```

若 Raspberry Pi IP 不同，請到 App 的「設定」頁修改。

常用範例：

```text
http://172.20.10.2:5000    # 手機熱點環境
http://192.168.0.152:5000  # 一般 Wi-Fi 環境
http://<RPi-IP>:5002       # App Gateway
```

後端啟動範例：

```bash
cd ~/pineapple_final
source .venv/bin/activate
python app_local.py
```

確認後端是否可連線：

```bash
curl http://<RPi-IP>:5000/ping
```

---

## 8. 測試方式

### 8.1 專案完整性測試

```bash
npm run test
```

此測試會檢查：

- 必要檔案是否存在。
- Expo Router 頁面是否存在。
- `package.json` 的必要 scripts 是否存在。

### 8.2 Lint 檢查

```bash
npm run lint
```

### 8.3 手動功能測試

1. 執行 `npm run start`。
2. 開啟 App 首頁。
3. 點選「新建批次」。
4. 建立批次後進入「批次掃描」。
5. 點選「開始 30 秒掃描」。
6. 若後端正常，會取得真實推論結果。
7. 若後端離線，會取得展示用 mock 結果。
8. 進入「批次摘要」確認統計數字是否更新。
9. 點選「完成批次並查看報告」。
10. 到「報告列表」確認批次出現。

---

## 9. 可執行檔案說明

本專案是 Expo / React Native App，沒有傳統 Windows `.exe` 可執行檔。

可執行入口如下：

| 類型 | 指令 | 說明 |
|------|------|------|
| 開發執行 | `npm run start` | 啟動 Expo Dev Server |
| Web 執行 | `npm run start-web` | 使用瀏覽器執行 |
| Android | `npm run android` | 開啟 Android 模擬器或裝置 |
| iOS | `npm run ios` | 開啟 iOS 模擬器 |
| 測試 | `npm run test` | 執行 smoke test |
| Lint | `npm run lint` | 檢查程式碼風格 |

若要產生正式安裝檔，建議使用 EAS Build：

```bash
npm install -g eas-cli
eas login
eas build -p android
```

產生 Android APK / AAB 後即可安裝到手機。

---

## 10. 程式碼註解說明

本專案主要程式檔皆加入詳細中文註解：

- `app/_layout.tsx`：說明路由與 Provider。
- `app/index.tsx`：說明首頁統計邏輯。
- `app/batch-create.tsx`：說明批次建立流程。
- `app/batch-scan.tsx`：說明掃描 API 流程。
- `app/batch-summary.tsx`：說明批次統計計算。
- `services/api.ts`：說明 `/ping`、`/scan/start` 與 mock fallback。
- `stores/farmerStore.ts`：說明批次、掃描紀錄與設定狀態管理。
- `types/index.ts`：說明資料結構與 API 回傳型別。

---

## 11. 後續可擴充項目

- 增加 CSV / PDF 匯出。
- 接正式後端資料庫保存批次紀錄。
- 加入登入與使用者權限。
- 加入離線暫存與恢復上傳。
- 加入更多統計圖表，例如長條圖與圓餅圖。
