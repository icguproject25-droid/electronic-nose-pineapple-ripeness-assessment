# Pineapple App Gateway on Raspberry Pi 3
# 鳳梨辨識系統 App / Web Gateway 部署步驟

# 這個 pineapple_app_gateway 資料夾是 Raspberry Pi 3 上的網頁 / App 模擬入口。
# 主要用途是提供一個 Flask Web API 或簡易網頁介面，
# 讓使用者可以透過瀏覽器或手機端，把照片或請求送到 Raspberry Pi，
# 再由 Raspberry Pi 回傳辨識結果。

# 目前資料夾內容：
# app_gateway.py              Flask gateway 主程式
# requirements_gateway.txt    Gateway 需要安裝的 Python 套件
# test_2.jpg                  測試用圖片
# README.md                   部署與使用說明


# 1. 電腦端先確認資料夾位置

# 假設專案資料夾結構是：
# FINAL_PROJECT_DATA/
# └── pineapple_app_gateway/

# 請先確認 pineapple_app_gateway 裡面至少有：
# app_gateway.py
# requirements_gateway.txt
# test_2.jpg


# 2. 查 Raspberry Pi 目前 IP

# 在 Raspberry Pi 上打：
hostname -I

# 會看到類似：
# 192.168.0.152
# 或手機熱點時可能是：
# 172.20.10.2

# 後面 <raspberry_pi_ip> 請換成實際查到的 IP。


# 3. 從電腦上傳 pineapple_app_gateway 到 Raspberry Pi

# Windows PowerShell / CMD 執行：
# 注意：這是在 Windows 電腦打，不是在 Raspberry Pi 裡打。

scp -r C:\Users\user\Desktop\FINAL_PROJECT_DATA\pineapple_app_gateway <pi_user>@<raspberry_pi_ip>:/home/<pi_user>/

# 範例：
# scp -r C:\Users\user\Desktop\FINAL_PROJECT_DATA\pineapple_app_gateway pi@192.168.0.152:/home/pi/

# 如果 Raspberry Pi 連的是手機熱點，也可能是：
# scp -r C:\Users\user\Desktop\FINAL_PROJECT_DATA\pineapple_app_gateway pi@172.20.10.2:/home/pi/

# 上傳時會要求輸入 Raspberry Pi 的密碼。


# 4. SSH 連進 Raspberry Pi

ssh <pi_user>@<raspberry_pi_ip>

# 範例：
# ssh pi@192.168.0.152
# ssh pi@172.20.10.2


# 5. 進入 pineapple_app_gateway 資料夾

cd ~/pineapple_app_gateway

# 確認檔案有上傳成功：
ls

# 應該會看到：
# app_gateway.py
# requirements_gateway.txt
# test_2.jpg


# 6. 建立 Python 虛擬環境

# 如果 pineapple_app_gateway 裡面還沒有 .venv，就建立一個：
python3 -m venv .venv

# 啟動虛擬環境：
source .venv/bin/activate

# 成功後，終端機前面會出現：
# (.venv)


# 7. 更新 pip

python -m pip install --upgrade pip setuptools wheel


# 8. 安裝 Gateway 需要的套件

pip install -r requirements_gateway.txt

# 如果 requirements_gateway.txt 無法安裝，
# 可以先安裝 Flask 和常用套件：
pip install flask pillow numpy requests


# 9. 確認 Gateway 主程式是否存在

ls app_gateway.py

# 如果有看到 app_gateway.py，代表主程式存在。


# 10. 執行 Flask Gateway

python app_gateway.py

# 如果成功，通常會看到類似：
# Running on http://127.0.0.1:5001
# 或：
# Running on http://0.0.0.0:5001

# 如果程式設定的 port 不是 5001，請依照終端機顯示的 port 為主。


# 11. 從瀏覽器開啟 Gateway 網頁

# 如果 Raspberry Pi 的 IP 是 192.168.0.152，瀏覽器輸入：
http://192.168.0.152:5001

# 如果 Raspberry Pi 連的是手機熱點，IP 是 172.20.10.2，瀏覽器輸入：
http://172.20.10.2:5001

# 注意：
# 電腦、手機、Raspberry Pi 必須在同一個網路底下。
# 如果 Raspberry Pi 連手機熱點，電腦或手機也要連同一個手機熱點。


# 12. 使用測試圖片測試

# 如果 app_gateway.py 有提供上傳圖片功能，
# 可以使用資料夾內的 test_2.jpg 做測試。

# 也可以用 curl 測試，假設 API 路徑是 /predict：
curl -X POST -F "image=@test_2.jpg" http://127.0.0.1:5001/predict

# 如果要從其他電腦測試，請把 127.0.0.1 換成 Raspberry Pi 的 IP：
curl -X POST -F "image=@test_2.jpg" http://<raspberry_pi_ip>:5001/predict

# 範例：
# curl -X POST -F "image=@test_2.jpg" http://172.20.10.2:5001/predict


# 13. 如果 Gateway 需要呼叫成熟度辨識資料夾

# 如果 app_gateway.py 會呼叫 pineapple 裡面的成熟度辨識程式，
# 請確認 Raspberry Pi 上同時存在：
# ~/pineapple
# ~/pineapple_app_gateway

# 也就是：
ls ~/pineapple
ls ~/pineapple_app_gateway

# pineapple 裡面應該要有：
# calibrate_air_30s.py
# inference_30s.py
# deploy_student.pkl
# deploy_meta.json
# feature_columns.json

# pineapple_app_gateway 裡面應該要有：
# app_gateway.py
# requirements_gateway.txt


# 14. 如果 app_gateway.py 需要修改 pineapple 路徑

# 可以用 nano 開啟：
nano app_gateway.py

# 檢查裡面有沒有寫到 pineapple 的路徑。
# 如果有類似：
# /home/某個使用者/pineapple

# 請改成比較通用的寫法：
# /home/<pi_user>/pineapple

# 或在程式中用 pathlib / Path.home() 取得使用者家目錄。


# 15. 常見問題：瀏覽器打不開網頁

# 先確認 Flask Gateway 有沒有正在執行：
python app_gateway.py

# 再確認 Raspberry Pi IP：
hostname -I

# 再確認 port 是否正確。
# 如果終端機顯示 5001，就開：
# http://<raspberry_pi_ip>:5001

# 如果終端機顯示 5000，就開：
# http://<raspberry_pi_ip>:5000


# 16. 常見問題：只能在 Raspberry Pi 自己打開，其他電腦打不開

# 可能是 app_gateway.py 只綁定 127.0.0.1。
# Flask 啟動時建議使用：
# host="0.0.0.0"

# app_gateway.py 最下面應該類似：
# app.run(host="0.0.0.0", port=5001, debug=False)

# 如果是：
# app.run(host="127.0.0.1", port=5001)
# 其他電腦會連不到。


# 17. 常見問題：ModuleNotFoundError

# 代表目前 venv 裡沒有安裝需要的套件。
# 先確認有啟動 venv：
source .venv/bin/activate

# 再重新安裝：
pip install -r requirements_gateway.txt


# 18. 常見問題：Address already in use

# 代表 port 已經被其他程式占用。
# 可以先查誰在用 5001：
sudo lsof -i :5001

# 或：
sudo ss -tulpn | grep 5001

# 如果確定可以停止舊程式，可以用 Ctrl + C 停止目前執行中的 Flask。
# 如果是在背景執行，找到 PID 後可以停止：
kill <PID>


# 19. 常見問題：上傳圖片後沒有結果

# 可能原因：
# 1. uploads 資料夾不存在
# 2. app_gateway.py 內的模型路徑不正確
# 3. app_gateway.py 呼叫的 pineapple 資料夾不存在
# 4. 沒有啟動正確的 venv
# 5. 缺少需要的 Python 套件

# 可以先建立 uploads 資料夾：
mkdir -p uploads

# 再重新執行：
python app_gateway.py


# 20. 建議的資料夾位置

# Raspberry Pi 上建議放成這樣：
# /home/<pi_user>/
# ├── pineapple/
# │   ├── calibrate_air_30s.py
# │   ├── inference_30s.py
# │   ├── deploy_student.pkl
# │   ├── deploy_meta.json
# │   └── feature_columns.json
# │
# └── pineapple_app_gateway/
#     ├── app_gateway.py
#     ├── requirements_gateway.txt
#     └── test_2.jpg


# 21. 每次重新開機後的啟動流程

cd ~/pineapple_app_gateway
source .venv/bin/activate
python app_gateway.py

# 然後在瀏覽器開：
# http://<raspberry_pi_ip>:5001


# 22. 使用手機熱點展示時的流程

# 1. 手機開啟熱點
# 2. Raspberry Pi 連上手機熱點
# 3. 在 Raspberry Pi 上查 IP：
hostname -I

# 4. 啟動 Gateway：
cd ~/pineapple_app_gateway
source .venv/bin/activate
python app_gateway.py

# 5. 在手機或電腦瀏覽器開：
# http://<raspberry_pi_ip>:5001


# 23. 備份 Raspberry Pi 上的 pineapple_app_gateway

# 在 Raspberry Pi 上打包：
cd ~
tar -czvf pineapple_app_gateway_backup.tar.gz pineapple_app_gateway --exclude='pineapple_app_gateway/.venv'

# 在 Windows PowerShell 下載到電腦：
scp <pi_user>@<raspberry_pi_ip>:/home/<pi_user>/pineapple_app_gateway_backup.tar.gz C:\Users\user\Desktop\

# 注意：
# tar 和 scp 都是複製/打包，不會刪除 Raspberry Pi 上的原始資料。
# .venv 不建議一起打包，因為那是 Raspberry Pi Linux 環境，不適合直接拿到 Windows 用。


# 24. 最短執行流程

cd ~/pineapple_app_gateway
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements_gateway.txt
python app_gateway.py