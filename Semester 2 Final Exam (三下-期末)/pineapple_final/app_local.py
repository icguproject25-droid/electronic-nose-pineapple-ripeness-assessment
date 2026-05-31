# 匯入 Flask 需要用到的功能：建立網頁、渲染 HTML 字串、接收表單資料
from flask import Flask, render_template_string, request
# json 用來處理 Raspberry Pi 回傳的 JSON 格式資料
import json
# re 用來用正規表示式解析終端機輸出的文字
import re
# paramiko 用來透過 SSH 連線到 Raspberry Pi 執行指令
import paramiko
# shlex 用來把指令參數安全地加上引號，避免空白或特殊字元造成錯誤
import shlex

# 建立 Flask app，後面所有網頁路由都會掛在這個 app 上
app = Flask(__name__)

# ============================================================
# Raspberry Pi 設定
# ============================================================
# Raspberry Pi 的登入帳號
RPI_USER = "linguanyu"
# Raspberry Pi 的登入密碼（正式版建議改成環境變數，不要直接寫在程式裡）
RPI_PASSWORD = "DdoKk///23"
# Raspberry Pi 的 IP 位址，網路不同時這裡可能要改
RPI_IP = "172.20.10.2"
# Raspberry Pi 上成熟度辨識專案所在的資料夾
RPI_PROJECT_DIR = "/home/linguanyu/pineapple"

# 啟動 Raspberry Pi 專案裡的 Python 虛擬環境
RPI_ACTIVATE = "source .venv/bin/activate"
# 空氣基線校正程式名稱
AIR_SCRIPT = "calibrate_air_30s.py"
# 鳳梨成熟度推論程式名稱
INFER_SCRIPT = "inference_30s.py"


# ============================================================
# SSH 工具
# ============================================================
# 這個函式負責用 SSH 連到 Raspberry Pi，並執行指定的終端機指令
def run_remote_command(remote_cmd, timeout=420):
    # 建立 SSH 連線物件
    client = paramiko.SSHClient()
    # 第一次連線時自動接受 Raspberry Pi 的 host key
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        # 使用上面設定的 IP、帳號、密碼連線到 Raspberry Pi
        client.connect(
            hostname=RPI_IP,
            username=RPI_USER,
            password=RPI_PASSWORD,
            timeout=15,
            banner_timeout=15,
            auth_timeout=15,
        )
        # 在 Raspberry Pi 上執行傳進來的指令
        stdin, stdout, stderr = client.exec_command(remote_cmd, timeout=timeout)
        # 讀取正常輸出，並轉成文字
        out_text = stdout.read().decode("utf-8", errors="replace")
        # 讀取錯誤輸出，並轉成文字
        err_text = stderr.read().decode("utf-8", errors="replace")
        # 如果有正常輸出就先放進 output
        output = out_text or ""
        # 如果有錯誤訊息，也一起加到 output，方便網頁上顯示除錯資訊
        if err_text:
            output += "\n[stderr]\n" + err_text
        # 回傳整理過的輸出；如果完全沒有輸出，就顯示提示文字
        return output.strip() or "(沒有輸出)"
    # 如果 SSH 連線或指令執行失敗，就把錯誤訊息回傳給網頁
    except Exception as e:
        return f"執行失敗：{e}"
    # 不管成功或失敗，最後都要嘗試關閉 SSH 連線
    finally:
        try:
            client.close()
        except Exception:
            pass


# 這個函式專門用來執行 Raspberry Pi 專案資料夾裡的 Python script
def run_remote_script(script_name, args=""):
    # 把 script 名稱做安全處理，避免指令格式出錯
    safe_script = shlex.quote(script_name)
    # 去掉參數前後多餘空白
    safe_args = args.strip()
    # 組合要送到 Raspberry Pi 執行的完整指令
    remote_cmd = (
        f"cd {shlex.quote(RPI_PROJECT_DIR)} && "
        f"{RPI_ACTIVATE} && "
        f"python {safe_script} {safe_args}"
    )
    # 實際透過 SSH 執行組好的指令
    return run_remote_command(remote_cmd, timeout=420)


# 掃描 Raspberry Pi 上 demo_data 裡有哪些可以用的 xlsx demo 檔
def scan_remote_demo_files():
    """掃描 Pi 上 pineapple/demo_data 的 xlsx 檔，給 demo 下拉選單用。"""
    # 這裡放一小段會在 Raspberry Pi 上執行的 Python 程式，用來列出 demo 檔案
    py = r'''
import glob, os, re, json
DEMO_DIR="demo_data"
air=[]
pine=[]
for f in sorted(glob.glob(os.path.join(DEMO_DIR,"pineapple_*.xlsx"))):
    b=os.path.basename(f)
    m=re.search(r"^(pineapple_\w+_\d{8})_air\.xlsx$", b)
    if m:
        air.append(m.group(1)); continue
    m=re.search(r"^(pineapple_\w+_\d{8})_(.+)\.xlsx$", b)
    if m:
        pine.append([m.group(1), m.group(2)])
print(json.dumps({"air":air,"pine":pine}, ensure_ascii=False))
'''
    # 把上面那段 Python 程式包成遠端終端機指令
    cmd = (
        f"cd {shlex.quote(RPI_PROJECT_DIR)} && "
        f"python - <<'PYREMOTE'\n{py}\nPYREMOTE"
    )
    # 執行掃描 demo 檔案的遠端指令
    out = run_remote_command(cmd, timeout=30)
    try:
        # 從遠端輸出中抓出 JSON 物件
        m = re.search(r"(\{[\s\S]*\})", out)
        if not m:
            raise ValueError(out)
        # 把 JSON 字串轉成 Python dictionary
        data = json.loads(m.group(1))
        # 整理空氣校正 demo 清單，並去除重複
        air = sorted(set(data.get("air", [])))
        # 整理鳳梨推論 demo 清單
        pine = sorted([tuple(x) for x in data.get("pine", [])])
        # 回傳空氣 demo 和鳳梨 demo 的檔案清單
        return air, pine
    except Exception:
        # 如果掃描失敗，就回傳空清單，避免整個網頁掛掉
        return [], []


# ============================================================
# 小工具
# ============================================================
# 把 stage 數字轉成中文成熟度名稱
def stage_name(stage):
    return {0: "未熟", 1: "初熟", 2: "成熟", 3: "過熟"}.get(stage, f"Stage {stage}")


# 根據 stage 回傳對應顏色，讓網頁長條圖比較直觀
def stage_color(stage):
    return {0: "#3b82f6", 1: "#22c55e", 2: "#f59e0b", 3: "#ef4444"}.get(stage, "#6b7280")


# 把 demo 檔案名稱整理成比較好讀的顯示文字
def case_display(case_key: str) -> str:
    m = re.search(r"^pineapple_(\w+)_(\d{8})$", case_key or "")
    if not m:
        return case_key
    return f"pineapple_{m.group(1)} / {m.group(2)}"


# 根據判定文字選擇結果標籤的 CSS 顏色 class
def badge_class_from_text(text: str):
    if not text:
        return "tag-gray"
    if "無有效鳳梨訊號" in text:
        return "tag-orange"
    if "過熟" in text:
        return "tag-red"
    if "成熟" in text:
        return "tag-amber"
    if "初熟" in text:
        return "tag-green"
    if "未熟" in text:
        return "tag-blue"
    return "tag-gray"


# 根據前置累積秒數顯示目前是哪一種檢測模式
def mode_name_from_warmup(warmup_sec: int):
    if warmup_sec <= 0:
        return "快速檢測"
    if warmup_sec == 60:
        return "標準檢測"
    if warmup_sec == 180:
        return "完整檢測"
    return f"自訂檢測（前置 {warmup_sec} 秒）"


# ============================================================
# 解析 air / inference 結果
# ============================================================
# 解析空氣校正程式的終端機輸出，整理成網頁可以顯示的資料
def parse_air_output(output: str):
    # 先建立預設結果，避免解析失敗時沒有欄位可以顯示
    data = {"type": "air", "success": False, "port": None, "baseline": None, "raw_output": output}
    # 從輸出中找 Arduino 使用的序列埠
    m_port = re.search(r"Arduino port:\s*(.+)", output)
    if m_port:
        data["port"] = m_port.group(1).strip()
    # 如果是 demo 模式，就抓出目前使用的 demo case
    m_case = re.search(r"Demo case:\s*(.+)", output)
    if m_case:
        data["demo_case"] = m_case.group(1).strip()
    # 從輸出最後抓出 air baseline 的 JSON 內容
    m_json = re.search(r"(\{[\s\S]*\})\s*$", output.strip())
    if m_json:
        try:
            # 把 baseline JSON 轉成 Python dictionary
            data["baseline"] = json.loads(m_json.group(1))
            # 解析成功就標記為成功
            data["success"] = True
        except Exception:
            pass
    # 回傳解析好的推論結果
    return data


# 解析成熟度推論程式的終端機輸出，整理成前端頁面需要的資料
def parse_infer_output(output: str):
    # 建立推論結果的預設資料結構，後面會慢慢把解析到的內容填進去
    data = {
        "type": "infer", "success": False, "port": None, "feature_count": None,
        "target_window": None, "warmup_sec": None, "measure_mode": None,
        "demo_case": None, "demo_stage": None, "display_text": None,
        "raw_stage": None, "raw_stage_text": None, "final_stage": None, "final_stage_text": None,
        "raw_maturity_percent": None, "final_maturity_percent": None,
        "maturity_zone": None, "overripe_tendency": None,
        "guard_triggered": False, "early_override_used": False, "override_used": False,
        "guard_reasons": [], "early_override_reasons": [], "override_reasons": [],
        "probabilities": [], "sensor_summary": [], "feature_values": [], "raw_output": output,
    }

    # 這裡集中放要從輸出中抓的基本欄位和對應的正規表示式
    patterns = {
        "port": r"Arduino port:\s*(.+)",
        "feature_count": r"Feature count:\s*(\d+)",
        "target_window": r"Target window:\s*(\d+)\s*sec",
        "warmup_sec": r"Warmup sec:\s*(\d+)",
        "display_text": r"成熟度判定：(.+)",
        "maturity_zone": r"成熟區段：(.+)",
        "overripe_tendency": r"過熟傾向：(.+)",
    }
    # 逐一套用上面的 pattern，把有找到的欄位填進 data
    for key, pat in patterns.items():
        # 用正規表示式在輸出文字中找資料
        m = re.search(pat, output)
        if m:
            val = m.group(1).strip()
            # 這幾個欄位應該是數字，所以轉成 int
            if key in ["feature_count", "target_window", "warmup_sec"]:
                val = int(val)
            data[key] = val

    # 如果有抓到 warmup 秒數，就順便轉成模式名稱
    if data["warmup_sec"] is not None:
        data["measure_mode"] = mode_name_from_warmup(data["warmup_sec"])

    # 如果輸出是 demo 模式，就抓出 demo 日期和標籤
    m_demo = re.search(r"【模擬模式】日期：(.+?)\s+標籤：(.+)", output)
    if m_demo:
        data["demo_case"] = m_demo.group(1).strip()
        data["demo_stage"] = m_demo.group(2).strip()
        data["measure_mode"] = "Demo 模擬模式"

    # 抓出模型原始預測的 stage
    m_raw = re.search(r"原始模型分類：Stage\s*(\d+)\s*（(.+?)）", output)
    if m_raw:
        data["raw_stage"] = int(m_raw.group(1))
        data["raw_stage_text"] = m_raw.group(2).strip()

    # 抓出校正後的最終 stage
    m_final = re.search(r"校正後分類：Stage\s*(\d+)\s*（(.+?)）", output)
    if m_final:
        data["final_stage"] = int(m_final.group(1))
        data["final_stage_text"] = m_final.group(2).strip()
    # 如果校正後沒有 stage，就用 None 表示
    if "校正後分類：—" in output:
        data["final_stage"] = None
        data["final_stage_text"] = None

    # 抓出原始成熟度百分比
    m_raw_bar = re.search(r"原始成熟度條：\[.*?\]\s*(\d+)%", output)
    if m_raw_bar:
        data["raw_maturity_percent"] = int(m_raw_bar.group(1))
    # 抓出校正後成熟度百分比
    m_final_bar = re.search(r"校正後成熟度條：\[.*?\]\s*(\d+)%", output)
    if m_final_bar:
        data["final_maturity_percent"] = int(m_final_bar.group(1))
    if data["raw_maturity_percent"] is None and data["final_maturity_percent"] is None:
        # 有些輸出只有一條成熟度條，所以另外處理
        m_single_bar = re.search(r"成熟度條：\[.*?\]\s*(\d+)%", output)
        if m_single_bar:
            data["final_maturity_percent"] = int(m_single_bar.group(1))
    if data["raw_maturity_percent"] is None and data["final_maturity_percent"] is not None:
        data["raw_maturity_percent"] = data["final_maturity_percent"]

    # 判斷空氣或無樣本防呆規則是否有被觸發
    data["guard_triggered"] = "空氣/無樣本防呆：✅ 已觸發" in output
    # 判斷早期熟度校正是否有被啟用
    data["early_override_used"] = "早期熟度校正：✅ 已啟用" in output
    # 判斷過熟校正是否有被啟用
    data["override_used"] = "過熟校正：✅ 已啟用" in output

    # 抓出四個 Stage 的機率數值，等等用來畫長條圖
    prob_matches = re.findall(r"Stage\s*(\d+)\s*（.*?）:\s*([0-9.]+)\s*\(([0-9.]+)%\)", output)
    # 把機率資料整理成 list，每個 stage 都包含名稱、機率、百分比和顏色
    data["probabilities"] = [{
        "stage": int(i), "stage_text": stage_name(int(i)), "prob": float(p),
        "percent": float(pct), "color": stage_color(int(i))
    } for i, p, pct in prob_matches]

    m_sensor_block = re.search(r"Raw sensor summary.*?\n=+\n([\s\S]*?)\n=+\n.*?Feature values used by model", output)
    if m_sensor_block:
        # 用來存每個 sensor 的 mean/min/max/std
        parsed = []
        # 逐行解析感測器摘要
        for line in m_sensor_block.group(1).strip().splitlines():
            m = re.match(r"([A-Za-z0-9_]+)\s*\|\s*mean=\s*([0-9.\-]+)\s*\|\s*min=\s*([0-9.\-]+)\s*\|\s*max=\s*([0-9.\-]+)\s*\|\s*std=\s*([0-9.\-]+)", line.strip())
            # 如果該行格式符合，就加入 sensor summary
            if m:
                parsed.append({"name": m.group(1), "mean": float(m.group(2)), "min": float(m.group(3)), "max": float(m.group(4)), "std": float(m.group(5))})
        # 把解析完的感測器摘要放進 data
        data["sensor_summary"] = parsed

    m_feat_block = re.search(r"Feature values used by model.*?\n=+\n([\s\S]*?)\n=+\n.*?(?:詳細機率|Class probabilities)", output)
    if m_feat_block:
        # 用來存放每個 feature 的名稱和數值
        feats = []
        # 逐行解析 feature value
        for line in m_feat_block.group(1).strip().splitlines():
            if "=" in line:
                name, val = line.split("=", 1)
                # 嘗試把 feature value 轉成 float
                try:
                    value = float(val.strip())
                except Exception:
                    value = val.strip()
                feats.append({"name": name.strip(), "value": value})
        # 把解析完的特徵值放進 data
        data["feature_values"] = feats

    # current_mode 用來判斷目前正在讀哪一種校正依據
    current_mode = None
    # 逐行掃描輸出，整理 guard / early / overripe 的判定理由
    for raw_line in output.splitlines():
        line = raw_line.strip()
        # 接下來的 - 開頭文字屬於空氣/無樣本防呆依據
        if line.startswith("判定依據："):
            current_mode = "guard"; continue
        # 接下來的 - 開頭文字屬於早期校正依據
        if line.startswith("早期校正依據："):
            current_mode = "early"; continue
        # 接下來的 - 開頭文字屬於過熟校正依據
        if line.startswith("校正依據："):
            current_mode = "override"; continue
        # 遇到分隔線或結束文字，就停止目前的依據區塊
        if line.startswith("=") or line.startswith("Program finished") or line.startswith("🍍 結果"):
            current_mode = None; continue
        # 把 - 開頭的理由加入對應的 list
        if line.startswith("- "):
            if current_mode == "guard": data["guard_reasons"].append(line[2:].strip())
            elif current_mode == "early": data["early_override_reasons"].append(line[2:].strip())
            elif current_mode == "override": data["override_reasons"].append(line[2:].strip())

    # 只要有抓到判定文字或 stage，就算推論解析成功
    if data["display_text"] or data["raw_stage"] is not None:
        data["success"] = True
    # 回傳解析好的推論結果
    return data


# 這裡是整個 Flask 頁面的 HTML/CSS/JavaScript，直接用字串存在 Python 裡
HTML_PAGE = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Pineapple Ripeness Detector</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root{--bg:#f4f7fb;--card:#fff;--line:#e5e7eb;--text:#1f2937;--muted:#6b7280;--shadow:0 10px 30px rgba(0,0,0,.08);}*{box-sizing:border-box}body{font-family:Arial,sans-serif;background:var(--bg);margin:0;padding:28px;color:var(--text)}.container{max-width:1200px;margin:auto}.card{background:var(--card);border-radius:20px;padding:24px;margin-bottom:20px;box-shadow:var(--shadow)}h1,h2,h3{margin-top:0;margin-bottom:12px}.header{display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px}.small{color:var(--muted);font-size:14px;line-height:1.6}.btn-row{display:flex;gap:12px;flex-wrap:wrap;align-items:stretch}.mode-card{background:#f9fafb;border:1px solid var(--line);border-radius:16px;padding:14px;min-width:250px;flex:1}.mode-title{font-size:15px;font-weight:800;margin-bottom:8px}.mode-desc{font-size:13px;color:var(--muted);margin-bottom:12px;line-height:1.6}button{width:100%;font-size:15px;padding:14px 18px;border:none;border-radius:14px;cursor:pointer;background:#2563eb;color:white;font-weight:700;box-shadow:0 8px 18px rgba(37,99,235,.22)}button:hover{filter:brightness(.96)}button.air{background:#0891b2}button.std{background:#7c3aed}button.full{background:#ea580c}button.demo{background:#16a34a}select{width:100%;padding:11px 13px;border-radius:12px;border:1px solid var(--line);background:white;font-size:15px}.result-big{font-size:30px;font-weight:800;margin-bottom:8px}.tag{display:inline-block;padding:8px 12px;border-radius:999px;font-size:13px;font-weight:700;margin-right:8px;margin-bottom:8px}.tag-green{background:#dcfce7;color:#166534}.tag-blue{background:#dbeafe;color:#1d4ed8}.tag-orange{background:#ffedd5;color:#c2410c}.tag-red{background:#fee2e2;color:#b91c1c}.tag-amber{background:#fef3c7;color:#92400e}.tag-purple{background:#ede9fe;color:#6d28d9}.tag-gray{background:#f3f4f6;color:#374151}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px}.mini-card{background:#f9fafb;border-radius:14px;padding:16px;border:1px solid var(--line)}.mini-title{font-size:13px;color:var(--muted);margin-bottom:8px}.mini-value{font-size:24px;font-weight:800}.mono{font-family:Consolas,monospace}.table{width:100%;border-collapse:collapse}.table th,.table td{border-bottom:1px solid var(--line);padding:10px 8px;text-align:left;font-size:14px}.bar-wrap{background:#e5e7eb;border-radius:999px;overflow:hidden;height:18px;margin-top:8px}.bar{height:18px;background:linear-gradient(90deg,#3b82f6,#22c55e,#f59e0b,#ef4444)}.bar-gray{height:18px;background:linear-gradient(90deg,#94a3b8,#64748b)}.section-line{height:1px;background:var(--line);margin:20px 0}.prob-row{margin-bottom:14px}.prob-label{display:flex;justify-content:space-between;gap:12px;margin-bottom:6px;font-size:14px}.prob-bg{background:#e5e7eb;height:14px;border-radius:999px;overflow:hidden}.prob-fill{height:14px;border-radius:999px}.reason-list{margin:0;padding-left:20px;color:#374151}.reason-list li{margin-bottom:8px;line-height:1.5}details{margin-top:18px}summary{cursor:pointer;font-weight:700}pre{background:#111827;color:#d1fae5;padding:16px;border-radius:14px;overflow-x:auto;white-space:pre-wrap;word-wrap:break-word;line-height:1.5}.loading{display:none;position:fixed;inset:0;background:rgba(255,255,255,.72);z-index:9999;align-items:center;justify-content:center;backdrop-filter:blur(3px)}.loading-box{background:white;padding:24px 28px;border-radius:18px;box-shadow:var(--shadow);text-align:center;min-width:320px}.spinner{width:46px;height:46px;border:5px solid #dbeafe;border-top:5px solid #2563eb;border-radius:50%;margin:0 auto 14px;animation:spin 1s linear infinite}@keyframes spin{to{transform:rotate(360deg)}}
</style>
<script>
function showLoading(msg,submsg){document.getElementById('loading-text').innerText=msg;document.getElementById('loading-subtext').innerText=submsg||'請稍候...';document.getElementById('loading-overlay').style.display='flex';}
const pineKeys={{ pine_keys_json|safe }};
function updateDemoStages(){const d=document.getElementById('demo_case');const s=document.getElementById('demo_stage');if(!d||!s)return;const val=d.value;s.innerHTML='';pineKeys.filter(x=>x[0]===val).forEach(x=>{const o=document.createElement('option');o.value=x[1];o.text=x[1];s.appendChild(o);});}
</script>
</head>
<body>
<div id="loading-overlay" class="loading"><div class="loading-box"><div class="spinner"></div><div id="loading-text" style="font-weight:800;font-size:18px;">執行中，請稍候...</div><div id="loading-subtext" class="small" style="margin-top:8px;">空氣校正約 30 秒，鳳梨量測依模式而定</div></div></div>
<div class="container">
<div class="card"><div class="header"><div><h1>🍍 Pineapple Ripeness Detector</h1><div class="small">本機端網頁版（透過 SSH 控制 Raspberry Pi）｜已整合實測模式與 Demo 模擬模式</div></div><div class="small">Raspberry Pi：{{ user }}@{{ ip }}<br>路徑：{{ rpi_dir }}</div></div></div>

<div class="card"><h2>實測模式：Arduino Mega 2560 即時量測</h2>
<div class="btn-row" style="margin-bottom:14px;"><form method="post" action="/air" onsubmit="showLoading('🌫️ 正在進行空氣校正...','將收集 30 秒空氣 baseline')" style="width:100%;"><button class="air" type="submit">🌫️ 空氣校正（30 秒）</button></form></div>
<div class="btn-row">
<div class="mode-card"><div class="mode-title">快速檢測</div><div class="mode-desc">不做前置累積，直接量 30 秒。</div><form method="post" action="/infer" onsubmit="showLoading('🍍 快速檢測中...','前置累積 0 秒，量測窗口 30 秒')"><input type="hidden" name="warmup_sec" value="0"><button type="submit">🍍 直接 30 秒</button></form></div>
<div class="mode-card"><div class="mode-title">標準檢測</div><div class="mode-desc">先讓氣味累積 60 秒，再取最後 30 秒推論。</div><form method="post" action="/infer" onsubmit="showLoading('⏳ 標準檢測中...','前置累積 60 秒，之後取最後 30 秒')"><input type="hidden" name="warmup_sec" value="60"><button class="std" type="submit">⏳ 先等 60 秒再測</button></form></div>
<div class="mode-card"><div class="mode-title">完整檢測</div><div class="mode-desc">先讓氣味累積 180 秒，再取最後 30 秒推論。</div><form method="post" action="/infer" onsubmit="showLoading('🧪 完整檢測中...','前置累積 180 秒，之後取最後 30 秒')"><input type="hidden" name="warmup_sec" value="180"><button class="full" type="submit">🧪 先等 180 秒再測</button></form></div>
</div></div>

<div class="card"><h2>Demo 模式：讀取 Raspberry Pi 上的 demo_data/xlsx</h2>
{% if not air_cases and not pine_keys %}<div class="tag tag-orange">沒有掃描到 demo_data/*.xlsx。請確認資料已上傳到 Pi 的 pineapple/demo_data。</div>{% endif %}
<div class="btn-row">
<div class="mode-card"><div class="mode-title">Demo 空氣校正</div><div class="mode-desc">從 demo_data 選一個 *_air.xlsx 建立 air_base.json。</div><form method="post" action="/demo_air" onsubmit="showLoading('🌫️ Demo 空氣校正中...','讀取 xlsx 並更新 air_base.json')"><select name="demo_case_air">{% for c in air_cases %}<option value="{{ c }}" {% if c==selected_air_case %}selected{% endif %}>{{ display_map.get(c,c) }}</option>{% endfor %}</select><div style="height:10px"></div><button class="demo" type="submit">🌫️ Demo 空氣校正</button></form></div>
<div class="mode-card"><div class="mode-title">Demo 鳳梨推論</div><div class="mode-desc">先選鳳梨資料與熟度標籤，使用同一套模型與校正規則推論。</div><form method="post" action="/demo_infer" onsubmit="showLoading('🍍 Demo 推論中...','讀取 xlsx 並執行模型推論')"><select name="demo_case" id="demo_case" onchange="updateDemoStages()">{% for c in pine_cases %}<option value="{{ c }}" {% if c==selected_pine_case %}selected{% endif %}>{{ display_map.get(c,c) }}</option>{% endfor %}</select><div style="height:10px"></div><select name="demo_stage" id="demo_stage">{% for c,s in pine_keys %}<option value="{{ s }}" data-case="{{ c }}" {% if c==selected_pine_case and s==selected_stage %}selected{% endif %}>{{ s }}</option>{% endfor %}</select><div style="height:10px"></div><button class="demo" type="submit">🍍 Demo 推論</button></form></div>
</div></div>

{% if mode == 'air' and parsed %}<div class="card"><h2>空氣校正結果</h2>{% if parsed.success %}<div class="tag tag-green">✅ air_base.json 建立成功</div>{% if parsed.port %}<div class="tag tag-blue">Port：{{ parsed.port }}</div>{% endif %}{% if parsed.demo_case %}<div class="tag tag-purple">Demo：{{ parsed.demo_case }}</div>{% endif %}<div class="grid" style="margin-top:18px;">{% for k,v in parsed.baseline.items() %}<div class="mini-card"><div class="mini-title">{{ k }}</div><div class="mini-value mono">{{ '%.3f'|format(v) if v is number else v }}</div></div>{% endfor %}</div>{% else %}<div class="tag tag-orange">⚠️ 無法解析 air baseline 結果</div>{% endif %}<details><summary>查看原始終端輸出</summary><pre>{{ output }}</pre></details></div>{% endif %}

{% if mode == 'infer' and parsed %}<div class="card"><h2>量測結果</h2>{% if parsed.success %}<div class="result-big">🍍 {{ parsed.display_text }}</div><div style="margin-bottom:12px;"><span class="tag {{ badge_class }}">判定：{{ parsed.display_text }}</span>{% if parsed.measure_mode %}<span class="tag tag-purple">模式：{{ parsed.measure_mode }}</span>{% endif %}{% if parsed.demo_case %}<span class="tag tag-blue">資料：{{ parsed.demo_case }}</span>{% endif %}{% if parsed.demo_stage %}<span class="tag tag-purple">標籤：{{ parsed.demo_stage }}</span>{% endif %}{% if parsed.guard_triggered %}<span class="tag tag-orange">空氣 / 無樣本防呆已觸發</span>{% endif %}{% if parsed.early_override_used %}<span class="tag tag-green">早期熟度校正已啟用</span>{% endif %}{% if parsed.override_used %}<span class="tag tag-red">過熟校正已啟用</span>{% endif %}</div><div class="small">{% if parsed.port %}Port：{{ parsed.port }}{% endif %}{% if parsed.target_window %}｜窗口：{{ parsed.target_window }} 秒{% endif %}{% if parsed.warmup_sec is not none %}｜前置累積：{{ parsed.warmup_sec }} 秒{% endif %}{% if parsed.feature_count %}｜Feature count：{{ parsed.feature_count }}{% endif %}</div><div class="section-line"></div>
<div class="grid"><div class="mini-card"><div class="mini-title">原始模型分類</div><div class="mini-value">{% if parsed.raw_stage is not none %}Stage {{ parsed.raw_stage }}（{{ parsed.raw_stage_text }}）{% else %}—{% endif %}</div></div><div class="mini-card"><div class="mini-title">校正後分類</div><div class="mini-value">{% if parsed.final_stage is not none %}Stage {{ parsed.final_stage }}（{{ parsed.final_stage_text }}）{% else %}—{% endif %}</div></div><div class="mini-card"><div class="mini-title">成熟區段</div><div class="mini-value">{{ parsed.maturity_zone or '—' }}</div></div><div class="mini-card"><div class="mini-title">過熟傾向</div><div class="mini-value">{{ parsed.overripe_tendency or '—' }}</div></div></div>
<div class="section-line"></div>{% if parsed.raw_maturity_percent is not none and parsed.final_maturity_percent is not none and parsed.raw_maturity_percent != parsed.final_maturity_percent %}<h3>成熟度條</h3><div class="small">原始成熟度條：{{ parsed.raw_maturity_percent }}%</div><div class="bar-wrap"><div class="bar-gray" style="width:{{ parsed.raw_maturity_percent }}%;"></div></div><div style="height:14px"></div><div class="small">校正後成熟度條：{{ parsed.final_maturity_percent }}%</div><div class="bar-wrap"><div class="bar" style="width:{{ parsed.final_maturity_percent }}%;"></div></div>{% elif parsed.final_maturity_percent is not none %}<h3>成熟度條</h3><div class="small">{{ parsed.final_maturity_percent }}%</div><div class="bar-wrap"><div class="bar" style="width:{{ parsed.final_maturity_percent }}%;"></div></div>{% endif %}
{% if parsed.probabilities %}<div class="section-line"></div><h3>四類機率</h3>{% for p in parsed.probabilities %}<div class="prob-row"><div class="prob-label"><span>Stage {{ p.stage }}（{{ p.stage_text }}）</span><span>{{ '%.2f'|format(p.percent) }}%</span></div><div class="prob-bg"><div class="prob-fill" style="width:{{ p.percent }}%;background:{{ p.color }};"></div></div></div>{% endfor %}{% endif %}
{% if parsed.guard_reasons %}<div class="section-line"></div><h3>空氣 / 無樣本防呆依據</h3><ul class="reason-list">{% for r in parsed.guard_reasons %}<li>{{ r }}</li>{% endfor %}</ul>{% endif %}{% if parsed.early_override_reasons %}<div class="section-line"></div><h3>早期熟度校正依據</h3><ul class="reason-list">{% for r in parsed.early_override_reasons %}<li>{{ r }}</li>{% endfor %}</ul>{% endif %}{% if parsed.override_reasons %}<div class="section-line"></div><h3>過熟校正依據</h3><ul class="reason-list">{% for r in parsed.override_reasons %}<li>{{ r }}</li>{% endfor %}</ul>{% endif %}
{% if parsed.sensor_summary %}<div class="section-line"></div><h3>原始感測器摘要</h3><table class="table"><thead><tr><th>Sensor</th><th>Mean</th><th>Min</th><th>Max</th><th>Std</th></tr></thead><tbody>{% for s in parsed.sensor_summary %}<tr><td>{{ s.name }}</td><td>{{ '%.3f'|format(s.mean) }}</td><td>{{ '%.3f'|format(s.min) }}</td><td>{{ '%.3f'|format(s.max) }}</td><td>{{ '%.3f'|format(s.std) }}</td></tr>{% endfor %}</tbody></table>{% endif %}
{% if parsed.feature_values %}<div class="section-line"></div><details><summary>查看模型特徵值</summary><div class="grid" style="margin-top:14px;">{% for f in parsed.feature_values %}<div class="mini-card"><div class="mini-title">{{ f.name }}</div><div class="mono" style="font-size:18px;font-weight:700;">{% if f.value is number %}{{ '%.6f'|format(f.value) }}{% else %}{{ f.value }}{% endif %}</div></div>{% endfor %}</div></details>{% endif %}{% else %}<div class="tag tag-orange">⚠️ 無法解析推論結果，請查看原始輸出</div>{% endif %}<details><summary>查看原始終端輸出</summary><pre>{{ output }}</pre></details></div>{% endif %}

{% if mode == 'none' %}<div class="card"><h2>目前狀態</h2><div class="small">尚未執行操作，請先點上方按鈕。</div></div>{% endif %}
</div>
<script>updateDemoStages();</script>
</body></html>
"""


# 把目前資料丟進 HTML template，產生最後要回傳給瀏覽器的頁面
def render_page(output="", parsed=None, mode="none", selected_air_case="", selected_pine_case="", selected_stage="", badge_class="tag-gray"):
    # 每次 render 頁面時，都重新掃描 Raspberry Pi 上的 demo 檔案
    air_cases, pine_keys = scan_remote_demo_files()
    # 取出所有不重複的鳳梨 demo case
    pine_cases = sorted(set(c for c, _ in pine_keys))
    # 建立檔名到顯示文字的對照表
    display_map = {k: case_display(k) for k in set(air_cases + pine_cases)}
    # 使用 Flask 的 render_template_string 把 HTML 字串和資料合成網頁
    return render_template_string(
        HTML_PAGE,
        output=output, parsed=parsed, mode=mode,
        user=RPI_USER, ip=RPI_IP, rpi_dir=RPI_PROJECT_DIR,
        air_cases=air_cases, pine_keys=pine_keys, pine_cases=pine_cases,
        pine_keys_json=json.dumps(pine_keys, ensure_ascii=False), display_map=display_map,
        selected_air_case=selected_air_case or (air_cases[0] if air_cases else ""),
        selected_pine_case=selected_pine_case or (pine_cases[0] if pine_cases else ""),
        selected_stage=selected_stage or (pine_keys[0][1] if pine_keys else ""),
        badge_class=badge_class,
    )


# 首頁路由：使用者打開網頁時會先進到這裡
@app.route("/")
# 顯示初始頁面，目前還沒有執行任何檢測
def index():
    return render_page()


# 空氣校正路由：按下空氣校正按鈕後會送 POST 到這裡
@app.route("/air", methods=["POST"])
# 執行 Raspberry Pi 上的空氣校正程式，並顯示解析後結果
def run_air():
    # 遠端執行 calibrate_air_30s.py
    output = run_remote_script(AIR_SCRIPT)
    # 解析空氣校正的輸出
    parsed = parse_air_output(output)
    return render_page(output=output, parsed=parsed, mode="air")


# 實測推論路由：按下快速/標準/完整檢測時會送 POST 到這裡
@app.route("/infer", methods=["POST"])
# 根據表單給的 warmup 秒數執行成熟度推論
def run_infer():
    # 從表單取得前置累積秒數，預設為 0 秒
    warmup_sec = request.form.get("warmup_sec", "0").strip()
    # 如果收到的不是數字，就改回 0，避免指令錯誤
    if not warmup_sec.isdigit():
        warmup_sec = "0"
    # 組成要傳給 inference_30s.py 的參數
    args = f"--warmup-sec {int(warmup_sec)}"
    # 遠端執行 inference_30s.py
    output = run_remote_script(INFER_SCRIPT, args=args)
    # 解析推論結果文字
    parsed = parse_infer_output(output)
    if parsed.get("warmup_sec") is None:
        parsed["warmup_sec"] = int(warmup_sec)
        parsed["measure_mode"] = mode_name_from_warmup(int(warmup_sec))
    return render_page(output=output, parsed=parsed, mode="infer", badge_class=badge_class_from_text(parsed.get("display_text", "")))


# Demo 空氣校正路由：使用 xlsx demo 檔建立 air baseline
@app.route("/demo_air", methods=["POST"])
# 執行 demo 模式的空氣校正
def run_demo_air():
    # 從下拉選單取得使用者選的空氣 demo case
    demo_case = request.form.get("demo_case_air", "").strip()
    # 組成 demo 空氣校正需要的參數
    args = f"--demo --demo-case {shlex.quote(demo_case)}"
    output = run_remote_script(AIR_SCRIPT, args=args)
    # 解析空氣校正的輸出
    parsed = parse_air_output(output)
    return render_page(output=output, parsed=parsed, mode="air", selected_air_case=demo_case)


# Demo 推論路由：使用 demo_data 的 xlsx 檔做鳳梨成熟度推論
@app.route("/demo_infer", methods=["POST"])
# 執行 demo 模式的鳳梨成熟度推論
def run_demo_infer():
    # 取得使用者選的鳳梨 demo case
    demo_case = request.form.get("demo_case", "").strip()
    # 取得使用者選的 demo 熟度標籤
    demo_stage = request.form.get("demo_stage", "").strip()
    # 組成 demo 推論需要的參數
    args = f"--demo --demo-case {shlex.quote(demo_case)} --demo-stage {shlex.quote(demo_stage)}"
    # 遠端執行 inference_30s.py
    output = run_remote_script(INFER_SCRIPT, args=args)
    # 解析推論結果文字
    parsed = parse_infer_output(output)
    return render_page(
        output=output, parsed=parsed, mode="infer",
        selected_pine_case=demo_case, selected_stage=demo_stage,
        badge_class=badge_class_from_text(parsed.get("display_text", "")),
    )


# 如果這個檔案是直接被執行，就啟動 Flask 伺服器
if __name__ == "__main__":
    # 在終端機顯示啟動提示
    print("Local Web App Running")
    # 提醒使用者可以用瀏覽器打開這個網址
    print("Open Browser: http://127.0.0.1:5000")
    # 啟動 Flask，host=0.0.0.0 表示同網路其他裝置也可以連進來
    app.run(host="0.0.0.0", port=5000, debug=False)
