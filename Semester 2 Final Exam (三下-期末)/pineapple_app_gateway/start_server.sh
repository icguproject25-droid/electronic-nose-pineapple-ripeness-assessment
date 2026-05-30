#!/bin/bash
# start_server.sh
# 放在 ~/pineapple_app_gateway/ 資料夾
# 用法：bash start_server.sh
#
# 執行前請確認：
#   1. ngrok 已安裝並登入：
#      ngrok config add-authtoken <你的token>
#
#   2. pineapple 資料夾有：
#      deploy_student.pkl
#      feature_columns.json
#      air_base.json
#
#   3. 已安裝或可安裝 requirements：
#      pip install flask pyserial numpy

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$SCRIPT_DIR/.venv"

echo "======================================"
echo "🍍 鳳梨感測系統啟動腳本"
echo "======================================"

# 建立虛擬環境
if [ ! -d "$VENV_PATH" ]; then
    echo "[Setup] 建立虛擬環境..."
    python3 -m venv "$VENV_PATH"
fi

# 啟動虛擬環境
source "$VENV_PATH/bin/activate"

# 安裝套件
echo "[Setup] 安裝 Python 套件..."
pip install flask pyserial numpy --quiet

# 背景啟動 Flask
echo "[Flask] 啟動 app_gateway_v2.py (port 5000)..."
python "$SCRIPT_DIR/app_gateway_v2.py" &
FLASK_PID=$!

echo "[Flask] PID = $FLASK_PID"

# 等 Flask 完全啟動
sleep 3

# 確認 Flask 有在跑
if ! kill -0 $FLASK_PID 2>/dev/null; then
    echo "[ERROR] Flask 啟動失敗，請檢查錯誤訊息"
    exit 1
fi

echo "[Flask] 啟動成功，監聽 http://0.0.0.0:5000"

# 確認 ngrok 有安裝
if ! command -v ngrok &>/dev/null; then
    echo ""
    echo "[WARNING] ngrok 未安裝！"
    echo "請至 https://ngrok.com 下載並登入："
    echo ""
    echo "wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-arm.tgz"
    echo "tar xzf ngrok-v3-stable-linux-arm.tgz"
    echo "sudo mv ngrok /usr/local/bin/"
    echo "ngrok config add-authtoken <你的 token>"
    echo ""
    echo "Flask 仍在背景運行（PID=$FLASK_PID）"
    echo "區網連線：http://$(hostname -I | awk '{print $1}'):5000"
    echo ""

    wait $FLASK_PID
    exit 0
fi

# 啟動 ngrok
echo "[ngrok] 啟動 ngrok tunnel (port 5000)..."
ngrok http 5000 --log=stdout &
NGROK_PID=$!

# 等 ngrok 建立 tunnel
sleep 4

# 取得 ngrok 的公開 URL
NGROK_URL=$(
    curl -s http://localhost:4040/api/tunnels 2>/dev/null \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['tunnels'][0]['public_url'])" 2>/dev/null \
    || echo ""
)

echo ""
echo "======================================"
echo "✅ 系統已就緒！"
echo ""

if [ -n "$NGROK_URL" ]; then
    echo "🌐 ngrok 公開網址："
    echo "   $NGROK_URL"
    echo ""
    echo "請把這個網址貼到 APP 的設定頁面 Settings"
    echo "API Base URL = $NGROK_URL"
else
    echo "[WARNING] 無法自動取得 ngrok URL"
    echo "請至 http://localhost:4040 查看"
fi

echo ""
echo "📡 區網連線（同 Wi-Fi）："
echo "   http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "按 Ctrl+C 關閉所有服務"
echo "======================================"

# Ctrl+C 時關閉 Flask 和 ngrok
trap "echo '關閉服務...'; kill $FLASK_PID $NGROK_PID 2>/dev/null; exit 0" INT TERM

wait