#!/bin/bash

echo "🍍 Starting Pineapple Smart System..."

# 先建立 logs 資料夾，方便看錯誤
mkdir -p ~/pineapple_logs

echo "1. Starting ripeness detector..."
cd ~/pineapple
source .venv/bin/activate
nohup python app_local.py > ~/pineapple_logs/ripeness.log 2>&1 &
deactivate

sleep 2

echo "2. Starting photo gateway..."
cd ~/pineapple_app_gateway
# 如果這個資料夾也有 .venv，就用這段
if [ -d ".venv" ]; then
    source .venv/bin/activate
    nohup python app_gateway.py > ~/pineapple_logs/photo_gateway.log 2>&1 &
    deactivate
else
    nohup python3 app_gateway.py > ~/pineapple_logs/photo_gateway.log 2>&1 &
fi

sleep 2

echo "3. Starting unified web..."
cd ~/pineapple_unified_web
source .venv/bin/activate
nohup python app.py > ~/pineapple_logs/unified_web.log 2>&1 &
deactivate

sleep 2

echo "========================================"
echo "All Raspberry Pi services started!"
echo ""
echo "成熟度辨識頁： http://192.168.0.152:5000"
echo "照片呈現頁：   http://192.168.0.152:5002"
echo "整合主網頁：   http://192.168.0.152:8000"
echo "========================================"
