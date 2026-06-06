# UC-12 系統進行模型推論

## 1. 使用案例名稱
系統進行模型推論

## 2. 案例簡述
系統在取得 30 秒感測資料後，載入基準線、特徵欄位與 ExtraTrees 模型，計算成熟度機率分布並輸出最終成熟度結果。

## 3. 參與角色
- 主要角色：系統、Raspberry Pi 3
- 次要角色：Arduino Mega、感測器陣列、ExtraTrees 模型、App

## 4. 前提
- 系統已完成 Air Baseline 校正。
- airbase.json 存在且有效。
- deploystudent.pkl 模型檔案存在。
- featurecolumns.json 存在。
- 系統已取得足夠的 30 秒感測資料。

## 5. 成功條件
- 系統成功計算 11 項部署特徵。
- ExtraTrees 模型成功輸出 Stage 0～Stage 3 機率分布。
- 系統完成 Guard Baseline 與 Override 後處理。
- 系統輸出最終成熟度結果。

## 6. 主要路徑：正常情節
1. TUCBW：系統接收到推論請求。
2. Raspberry Pi 3 載入 airbase.json。
3. Raspberry Pi 3 載入 deploystudent.pkl 模型。
4. Raspberry Pi 3 載入 featurecolumns.json。
5. 系統接收 Arduino 傳來的感測資料。
6. 系統累積 30 秒資料窗口。
7. 系統計算 11 項部署特徵。
8. 系統使用 airbase.json 進行歸一化。
9. ExtraTrees 模型輸出 Stage 0～Stage 3 機率分布。
10. 系統套用 Guard Baseline 規則。
11. 系統套用 Override 後處理規則。
12. TUCEW：系統輸出最終成熟度結果。

## 7. 例外路徑

### A1：模型檔案不存在
1. 系統接收到推論請求。
2. Raspberry Pi 3 嘗試載入 deploystudent.pkl。
3. 系統找不到模型檔案。
4. 系統中止推論並顯示「模型檔案不存在」。

### A2：featurecolumns.json 不存在
1. 系統嘗試載入特徵欄位設定檔。
2. 系統找不到 featurecolumns.json。
3. 系統中止推論並顯示「特徵欄位設定檔不存在」。

### A3：airbase.json 不存在或無效
1. 系統嘗試載入 airbase.json。
2. 系統發現基準線檔案不存在或內容無效。
3. 系統中止推論並顯示「請先執行 Air Baseline 校正」。

### A4：30 秒資料不足
1. 系統開始累積感測資料。
2. 系統在指定時間內未取得足夠資料。
3. 系統中止推論並顯示「資料不足，請重新掃描」。

### A5：推論程式執行失敗
1. 系統完成資料收集與特徵計算。
2. 推論程式 inference_30s.py 執行時發生錯誤。
3. 系統顯示「推論程式執行失敗」。

### A6：模型輸出結果格式錯誤
1. ExtraTrees 模型完成推論。
2. 系統發現輸出機率分布格式異常。
3. 系統中止結果顯示並提示「模型輸出格式錯誤」。
