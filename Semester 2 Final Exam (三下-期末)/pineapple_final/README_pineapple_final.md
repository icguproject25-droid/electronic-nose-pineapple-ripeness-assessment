# Pineapple Ripeness Detection System README

這個資料夾是鳳梨電子鼻熟度辨識系統的部署版本，主要用途是讓 Raspberry Pi 3 透過 Arduino Mega 2560 接收感測器訊號，並使用已訓練好的模型判斷鳳梨熟度。

系統支援兩種模式：

- 實測模式：Arduino Mega 2560 實際讀取感測器資料，Raspberry Pi 3 執行空氣校正與 30 秒推論。
- Demo 模式：直接讀取 `demo_data/` 裡面的歷史 xlsx 資料，不需要接 Arduino，也可以展示模型推論結果。

---

## 1. 資料夾架構

目前專案資料夾建議放在 Raspberry Pi：

```bash
~/pineapple_final
```

資料夾內容如下：

```text
pineapple_final/
├── demo_data/                         # Demo 用歷史資料，放 pineapple_xx_日期_air.xlsx 與熟度資料 xlsx
├── air_base.json                      # 空氣 baseline，校正後會被更新
├── app_local_demo_early_correcte...py  # 舊版 demo 網頁，可保留備份
├── app_local.py                       # 主要網頁操作介面，可控制實測與 demo
├── calibrate_air_30s.py               # 實測 / demo 空氣校正程式
├── calibrate_air_from_csv.py          # 舊版 demo 空氣校正程式，可單獨讀 xlsx
├── debug_features.py                  # 除錯用，可查看 feature 數值
├── deploy_meta.json                   # 模型顯示規則與部署資訊
├── deploy_student.pkl                 # 已訓練好的熟度模型
├── feature_columns.json               # 模型輸入特徵欄位順序
├── inference_30s.py                   # 實測 / demo 鳳梨熟度推論程式
├── inference_from_csv_updated.py      # 舊版 demo 推論程式，可單獨讀 xlsx
└── requirements_rpi.txt               # Raspberry Pi 需要安裝的套件
```

不要隨便刪除這幾個檔案：

```text
deploy_student.pkl
feature_columns.json
deploy_meta.json
air_base.json
demo_data/
```

這些是模型推論和 demo 會用到的核心資料。

---

## 2. 硬體連接

實測模式需要接：

```text
Arduino Mega 2560 → USB → Raspberry Pi 3
```

Arduino Mega 2560 負責讀取感測器資料，並用 Serial 輸出 CSV 格式資料給 Raspberry Pi。

目前模型主要使用的感測器欄位：

```text
MQ2_raw
MQ3_raw
MQ9_raw
MQ135_raw
TGS2602_raw
```

空氣校正時也可能會記錄：

```text
TGS2620_raw
Temp_C
Humidity_pct
Pressure_hPa
```

Arduino 輸出的 CSV header 需要包含類似下面格式：

```text
timestamp_ms,MQ2_raw,MQ3_raw,MQ9_raw,MQ135_raw,TGS2602_raw,TGS2620_raw,Temp_C,Humidity_pct,Pressure_hPa
```

---

## 3. 第一次使用：建立環境

先進入專案資料夾：

```bash
cd ~/pineapple_final
```

建立 Python 虛擬環境：

```bash
python3 -m venv .venv
source .venv/bin/activate
```

安裝套件：

```bash
pip install --upgrade pip
pip install -r requirements_rpi.txt
```

如果沒有 `requirements_rpi.txt` 或安裝失敗，可以先手動安裝常用套件：

```bash
pip install numpy pandas scikit-learn pyserial flask paramiko openpyxl
```

確認目前有啟用虛擬環境：

```bash
which python
```

正常會看到路徑中有 `.venv`。

---

## 4. 實測模式操作流程

實測模式是正式 Demo 給老師看時最重要的流程。

### Step 1：接好 Arduino Mega 2560

把 Arduino Mega 2560 用 USB 接到 Raspberry Pi 3。

檢查序列埠：

```bash
ls /dev/ttyACM* /dev/ttyUSB*
```

常見會出現：

```text
/dev/ttyACM0
```

如果完全沒有出現，代表 Raspberry Pi 沒有抓到 Arduino，請重新插 USB 或確認 Arduino 是否有燒錄正確程式。

### Step 2：啟動環境

```bash
cd ~/pineapple_final
source .venv/bin/activate
```

### Step 3：做空氣校正

請先確認容器內沒有鳳梨，只量空氣。

```bash
python calibrate_air_30s.py
```

程式會收集 30 秒空氣資料，完成後產生或更新：

```text
air_base.json
```

這個檔案是後面推論時的 baseline，所以實測前建議先做一次空氣校正。

### Step 4：放入鳳梨，執行推論

快速檢測，直接收集 30 秒：

```bash
python inference_30s.py
```

標準檢測，先讓氣味累積 60 秒，再取最後 30 秒推論：

```bash
python inference_30s.py --warmup-sec 60
```

完整檢測，先讓氣味累積 180 秒，再取最後 30 秒推論：

```bash
python inference_30s.py --warmup-sec 180
```

輸出結果會包含：

```text
成熟度判定
原始模型分類
校正後分類
成熟度條
成熟區段
過熟傾向
四類機率
原始感測器摘要
模型特徵值
空氣/無樣本防呆
過熟校正
早期熟度校正
```

---

## 5. Demo 模式操作流程

Demo 模式適合沒有接 Arduino、或只是要展示系統畫面時使用。

Demo 檔案需要放在：

```bash
demo_data/
```

檔名格式建議如下：

```text
pineapple_03_20260214_air.xlsx
pineapple_03_20260214_未熟.xlsx
pineapple_03_20260214_初熟.xlsx
pineapple_03_20260214_成熟.xlsx
pineapple_03_20260214_過熟.xlsx
```

其中：

```text
pineapple_03_20260214
```

就是 demo case 名稱。

### Demo 空氣校正

```bash
cd ~/pineapple_final
source .venv/bin/activate
python calibrate_air_30s.py --demo --demo-case pineapple_03_20260214
```

成功後一樣會更新：

```text
air_base.json
```

### Demo 鳳梨推論

```bash
python inference_30s.py --demo --demo-case pineapple_03_20260214 --demo-stage 初熟
```

也可以換成其他熟度標籤：

```bash
python inference_30s.py --demo --demo-case pineapple_03_20260214 --demo-stage 未熟
python inference_30s.py --demo --demo-case pineapple_03_20260214 --demo-stage 成熟
python inference_30s.py --demo --demo-case pineapple_03_20260214 --demo-stage 過熟
```

注意：`--demo-stage` 要和 xlsx 檔名最後的熟度文字一致。

---

## 6. 使用網頁操作介面

`app_local.py` 是給同學或展示時使用的網頁介面，可以按按鈕執行空氣校正、實測推論，也可以選擇 demo 檔案。

### 重要設定

打開 `app_local.py`，確認最上方 Raspberry Pi 設定正確：

```python
RPI_USER = "你的樹莓派帳號"
RPI_PASSWORD = "你的樹莓派密碼"
RPI_IP = "你的樹莓派IP"
RPI_PROJECT_DIR = "/home/你的帳號/pineapple_final"
```

如果你的資料夾叫 `pineapple_final`，請確認 `RPI_PROJECT_DIR` 不要還停在舊的：

```python
RPI_PROJECT_DIR = "/home/linguanyu/pineapple_final"
```

### 在電腦本機執行網頁

如果 `app_local.py` 是放在電腦端，並透過 SSH 控制 Raspberry Pi，請在電腦端執行：

```bash
python app_local.py
```

瀏覽器打開：

```text
http://127.0.0.1:5000
```

### 在 Raspberry Pi 上執行網頁

如果要直接在 Raspberry Pi 上開網頁，也可以執行：

```bash
cd ~/pineapple_final
source .venv/bin/activate
python app_local.py
```

如果程式設定為 `host="127.0.0.1"`，只能在 Raspberry Pi 本機看。

若要讓同一個 Wi-Fi 下的手機或電腦也能開，請把程式最後改成：

```python
app.run(host="0.0.0.0", port=5000, debug=False)
```

然後用瀏覽器開：

```text
http://樹莓派IP:5000
```

例如：

```text
http://172.20.10.2:5000
```

---

## 7. 網頁按鈕功能說明

網頁主要會有這幾種操作：

```text
空氣校正（30 秒）
快速檢測（直接 30 秒）
標準檢測（前置累積 60 秒 + 最後 30 秒推論）
完整檢測（前置累積 180 秒 + 最後 30 秒推論）
Demo 空氣校正
Demo 鳳梨推論
```

實測按鈕會呼叫：

```text
calibrate_air_30s.py
inference_30s.py
```

Demo 按鈕會呼叫：

```text
calibrate_air_30s.py --demo --demo-case ...
inference_30s.py --demo --demo-case ... --demo-stage ...
```

網頁會把終端機輸出的文字解析成卡片、成熟度條、四類機率、感測器摘要和特徵值。

---

## 8. 推論結果怎麼看

模型共有四個熟度階段：

```text
Stage 0：未熟
Stage 1：初熟
Stage 2：成熟
Stage 3：過熟
```

畫面上會看到：

```text
原始模型分類：模型直接預測的結果
校正後分類：加入防呆、早期校正、過熟校正後的結果
成熟度條：用百分比方式呈現熟度
成熟區段：未熟區 / 初熟區 / 成熟區 / 過熟區
過熟傾向：Stage 3 機率的提示
```

如果看到：

```text
成熟，但已有過熟傾向
成熟，明顯接近過熟
```

代表模型最高仍可能是成熟，但 Stage 3 機率已經有一定程度，因此顯示成比較符合實際狀態的文字。

如果看到：

```text
空氣 / 無樣本防呆已觸發
```

代表目前感測器訊號太接近空氣 baseline，系統判斷可能沒有放入有效鳳梨樣本。

---

## 9. 常見問題

### 問題 1：找不到 Arduino

錯誤類似：

```text
找不到 Arduino (/dev/ttyACM* 或 /dev/ttyUSB*)
```

請檢查：

```bash
ls /dev/ttyACM* /dev/ttyUSB*
```

如果沒有任何裝置，請重新插 Arduino USB，或確認 Arduino 有正常供電。

### 問題 2：找不到 air_base.json

請先執行空氣校正：

```bash
python calibrate_air_30s.py
```

或 demo 空氣校正：

```bash
python calibrate_air_30s.py --demo --demo-case pineapple_03_20260214
```

### 問題 3：找不到 demo xlsx

請確認檔案放在：

```bash
~/pineapple_final/demo_data
```

並確認檔名格式正確：

```text
pineapple_編號_日期_air.xlsx
pineapple_編號_日期_熟度.xlsx
```

例如：

```text
pineapple_03_20260214_air.xlsx
pineapple_03_20260214_初熟.xlsx
```

### 問題 4：網頁打不開

先確認 Flask 有跑起來：

```bash
python app_local.py
```

如果要從手機或其他電腦開，確認 `app.run` 是：

```python
app.run(host="0.0.0.0", port=5000, debug=False)
```

然後確認手機和 Raspberry Pi 在同一個 Wi-Fi。

### 問題 5：模型檔案缺少

如果出現找不到模型或 feature 檔案，請確認資料夾內有：

```text
deploy_student.pkl
feature_columns.json
deploy_meta.json
```

---

## 10. 建議展示流程

正式 Demo 可以照這個順序：

```text
1. 先開網頁 app_local.py
2. 說明系統有實測模式和 demo 模式
3. 先用 demo 模式展示不同熟度結果
4. 接著接上 Arduino Mega 2560
5. 執行空氣校正 30 秒
6. 放入鳳梨
7. 執行快速檢測或標準檢測
8. 觀看成熟度判定、成熟度條、四類機率和校正依據
```

如果現場時間很短，建議使用：

```text
Demo 模式 + 快速檢測
```

如果現場想要比較穩定，建議使用：

```text
空氣校正 30 秒 + 標準檢測 60 秒 warmup + 30 秒推論
```

---

## 11. 快速指令整理

進入專案：

```bash
cd ~/pineapple_final
source .venv/bin/activate
```

實測空氣校正：

```bash
python calibrate_air_30s.py
```

實測推論：

```bash
python inference_30s.py
```

實測標準推論：

```bash
python inference_30s.py --warmup-sec 60
```

Demo 空氣校正：

```bash
python calibrate_air_30s.py --demo --demo-case pineapple_03_20260214
```

Demo 推論：

```bash
python inference_30s.py --demo --demo-case pineapple_03_20260214 --demo-stage 初熟
```

開啟網頁：

```bash
python app_local.py
```

瀏覽器：

```text
http://127.0.0.1:5000
```

或：

```text
http://樹莓派IP:5000
```
