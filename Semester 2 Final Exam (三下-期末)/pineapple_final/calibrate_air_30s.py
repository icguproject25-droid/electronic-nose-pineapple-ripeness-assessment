# 匯入 argparse，用來接收終端機參數，例如 --demo、--port
import argparse

# 匯入 glob，用來搜尋符合條件的檔案路徑，例如 /dev/ttyACM*
import glob

# 匯入 json，用來讀寫 air_base.json
import json

# 匯入 os，用來處理檔案路徑與檔名
import os

# 匯入 re，用來用正規表示式解析檔名或文字
import re

# 匯入 sys，用來在錯誤時結束程式
import sys

# 匯入 time，用來計算 30 秒校正時間與等待 Arduino 穩定
import time

# numpy 主要用來計算平均值，也可以判斷數值是否有效
import numpy as np

# serial 用來和 Arduino Mega 透過 USB Serial 溝通
import serial


# Arduino Serial 的 baud rate，要和 Arduino 程式設定一致
BAUD = 115200

# 空氣校正時間，這裡固定收集 30 秒
CALIB_SECONDS = 30

# demo 模式讀取 xlsx 的資料夾名稱
DEMO_DIR = "demo_data"

# 這些是我們電子鼻使用的氣體感測器欄位
SENSORS = ["MQ2", "MQ3", "MQ9", "MQ135", "TGS2602", "TGS2620"]

# 環境感測欄位，主要是 BME280 的溫度、濕度、氣壓
ENV_COLS = ["Temp_C", "Humidity_pct", "Pressure_hPa"]


def auto_detect_port():
    # 自動找 Arduino 的序列埠，Linux / Raspberry Pi 通常會出現在 /dev/ttyACM* 或 /dev/ttyUSB*
    ports = sorted(glob.glob("/dev/ttyACM*")) + sorted(glob.glob("/dev/ttyUSB*"))

    # 如果完全找不到序列埠，就代表 Arduino 可能沒接上或權限有問題
    if not ports:
        raise RuntimeError("找不到 Arduino 序列埠")

    # 回傳第一個找到的 port
    return ports[0]


def parse_header_line(line: str):
    # 把 Arduino 輸出的 CSV header 用逗號切開，並去掉前後空白
    return [x.strip() for x in line.split(",")]


def parse_data_line(line: str, header_cols: list):
    # 把一行 CSV 資料用逗號切開
    vals = [x.strip() for x in line.split(",")]

    # 如果資料欄位數量和 header 對不起來，就代表這行不是有效資料
    if len(vals) != len(header_cols):
        return None

    # 將 header 和資料值配成字典，方便後面用欄位名稱取值
    row = dict(zip(header_cols, vals))

    try:
        # 把需要的 sensor raw data 轉成 float
        # 如果 TGS2620 或環境欄位不存在，就用 np.nan 表示缺值
        return {
            "MQ2_raw": float(row["MQ2_raw"]),
            "MQ3_raw": float(row["MQ3_raw"]),
            "MQ9_raw": float(row["MQ9_raw"]),
            "MQ135_raw": float(row["MQ135_raw"]),
            "TGS2602_raw": float(row["TGS2602_raw"]),
            "TGS2620_raw": float(row.get("TGS2620_raw", np.nan)),
            "Temp_C": float(row.get("Temp_C", np.nan)),
            "Humidity_pct": float(row.get("Humidity_pct", np.nan)),
            "Pressure_hPa": float(row.get("Pressure_hPa", np.nan)),
        }

    except Exception:
        # 如果轉換失敗，代表這行資料格式怪怪的，直接略過
        return None


def normalize_case(pid: str, date: str) -> str:
    # 將使用者輸入的鳳梨編號和日期轉成統一 case key 格式
    # 例如 pid=03, date=20260214 -> pineapple_03_20260214
    pid = str(pid).strip().replace("pineapple_", "")
    return f"pineapple_{pid}_{date}"


def load_xlsx_sensor_df(path: str):
    # 只有 demo 模式才需要 pandas，實測模式不會用到。
    import pandas as pd

    # 讀取 xlsx，先不指定 header，因為檔案前面可能有說明文字
    raw = pd.read_excel(path, header=None)

    # 找到真正的 header 那一列，這裡用 timestamp_ms 當作起點
    header_row = None
    for i, row in raw.iterrows():
        if str(row.iloc[0]).strip() == "timestamp_ms":
            header_row = i
            break

    # 如果找不到 timestamp_ms，代表這個 xlsx 格式不是我們預期的格式
    if header_row is None:
        raise ValueError(f"找不到 timestamp_ms header：{path}")

    # 取 header 下一列開始當作真正的資料
    df = raw.iloc[header_row + 1:].copy()

    # 把剛剛找到的 header row 設成欄位名稱
    df.columns = raw.iloc[header_row].tolist()

    # 重設 index，讓資料從 0 開始
    df = df.reset_index(drop=True)

    # 過濾掉以 # 開頭的註解列
    df = df[~df["timestamp_ms"].astype(str).str.startswith("#")]
    df = df.reset_index(drop=True)

    # 將每個欄位盡量轉成數字，不能轉的就變成 NaN
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # 回傳整理好的 DataFrame
    return df


def scan_air_files(demo_dir=DEMO_DIR):
    # 搜尋 demo_data 裡所有 pineapple_*_air.xlsx 的空氣校正檔案
    pattern = os.path.join(demo_dir, "pineapple_*_air.xlsx")

    # 用字典存結果，key 是 case 名稱，value 是檔案路徑
    result = {}

    # 逐一檢查找到的檔案
    for f in sorted(glob.glob(pattern)):
        base = os.path.basename(f)

        # 從檔名抓出 pineapple_編號_日期 這種 case key
        m = re.search(r"^(pineapple_\w+_\d{8})_air\.xlsx$", base)
        if m:
            result[m.group(1)] = f

    # 回傳所有可用的 air demo 檔案
    return result


def compute_baseline_from_rows(rows):
    # 這個函式負責把收集到的空氣資料算成 baseline 平均值
    out = {}

    # 對每一個氣體感測器計算 raw 值平均
    for s in SENSORS:
        col = f"{s}_raw"

        # 取出有效數值，並排除 NaN
        arr = np.array([r[col] for r in rows if col in r and np.isfinite(r[col])], dtype=float)

        # 如果有資料就算平均，沒有資料就先給 1.0，避免後面除以 0 或缺欄位
        out[s] = float(np.mean(arr)) if len(arr) > 0 else 1.0

    # 對環境欄位也計算平均值，例如溫度、濕度、氣壓
    for k in ENV_COLS:
        arr = np.array([r[k] for r in rows if k in r and np.isfinite(r[k])], dtype=float)
        if len(arr) > 0:
            out[k] = float(np.mean(arr))

    # 回傳 baseline 結果，之後會存成 air_base.json
    return out


def run_demo_calibration(args):
    # Demo 模式：不讀 Arduino，而是讀以前存好的 xlsx 空氣資料
    print("=" * 60)
    print("🌫️ Air baseline calibration（demo xlsx mode）")
    print("=" * 60)

    # 掃描 demo_data 裡有哪些 air xlsx 檔案
    air_files = scan_air_files(args.demo_dir)

    # 如果完全找不到 demo air 檔，就不能進行 demo 校正
    if not air_files:
        raise RuntimeError(f"在 {args.demo_dir}/ 找不到任何 *_air.xlsx")

    # 先讀取使用者指定的 demo case
    case_key = args.demo_case

    # 如果使用者沒有直接給 case，但有給 pid 和 date，就幫他轉成 case_key
    if not case_key and args.pid and args.date:
        case_key = normalize_case(args.pid, args.date)

    # 如果使用者已指定 case，就確認這個 case 是否真的存在
    if case_key:
        if case_key not in air_files:
            print(f"❌ 找不到 {case_key} 的 air 檔案。")
            print("可用 case：")
            for k in sorted(air_files):
                print(" -", k)
            sys.exit(1)

    else:
        # 如果沒有指定 case，就列出所有可用檔案讓使用者選
        print("可用空氣校正檔案：")
        keys = sorted(air_files)
        for idx, k in enumerate(keys):
            print(f"  [{idx}] {k}  ({air_files[k]})")

        # 讓使用者輸入編號選擇 demo case
        case_key = keys[int(input("請輸入編號：").strip())]

    # 取得選定 case 對應的 xlsx 檔案路徑
    path = air_files[case_key]

    # 顯示目前使用的 demo 檔案資訊
    print(f"Demo mode: 使用歷史 air 資料，不讀取 Arduino 即時 Serial")
    print(f"Demo case: {case_key}")
    print(f"Air file: {path}")

    # 讀取 xlsx 成 DataFrame
    df = load_xlsx_sensor_df(path)

    # 取前 30 筆資料當作校正資料，如果資料不足 30 筆就全部使用
    df_win = df.head(CALIB_SECONDS) if len(df) >= CALIB_SECONDS else df

    # 將 DataFrame 轉成 rows list，格式要和即時 Serial 收到的資料接近
    rows = []
    for _, row in df_win.iterrows():
        r = {}

        # 讀取每個氣體感測器的 raw 欄位
        for s in SENSORS:
            col = f"{s}_raw"
            if col in df_win.columns:
                try:
                    r[col] = float(row[col])
                except Exception:
                    r[col] = np.nan

        # 讀取環境欄位，例如溫度、濕度、氣壓
        for k in ENV_COLS:
            if k in df_win.columns:
                try:
                    r[k] = float(row[k])
                except Exception:
                    r[k] = np.nan

        rows.append(r)

    # 如果沒有任何有效資料，就不能建立 baseline
    if not rows:
        raise RuntimeError("demo air 檔沒有有效資料，無法建立 air_base.json")

    # 計算 baseline 平均值
    out = compute_baseline_from_rows(rows)

    # 將 baseline 寫成 JSON 檔，給後面的 inference 使用
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    # 顯示校正完成結果
    print(f"共 {len(df)} 筆資料，使用前 {len(rows)} 筆計算 baseline")
    print(f"✅ {args.out} 已建立")
    print(json.dumps(out, ensure_ascii=False, indent=2))


def run_real_calibration(args):
    # 實測模式：真的從 Arduino Serial 讀取 30 秒空氣資料
    print("=" * 60)
    print("🌫️ Air baseline calibration (30 sec)")
    print("=" * 60)
    print("請確認容器內沒有鳳梨，只量空氣。")
    print(f"將收集 {CALIB_SECONDS} 秒資料後輸出 {args.out}")
    print("-" * 60)

    # 如果使用者有指定 port 就用指定的，沒有就自動偵測
    port = args.port or auto_detect_port()
    print("Arduino port:", port)

    # 開啟 Arduino Serial 連線
    ser = serial.Serial(port, BAUD, timeout=1)

    # 等 2 秒讓 Arduino 重啟或 Serial 穩定
    time.sleep(2)

    # 先準備 header_cols，等讀到 CSV header 後才知道欄位順序
    header_cols = None
    print("等待 CSV header ...")

    # 持續讀取直到遇到 timestamp_ms 開頭的 CSV header
    while True:
        raw = ser.readline().decode("utf-8", errors="ignore").strip()
        if not raw:
            continue

        # Arduino 輸出的 header 會以 timestamp_ms 開頭
        if raw.startswith("timestamp_ms,"):
            header_cols = parse_header_line(raw)
            print("✅ CSV header detected")
            break

    # rows 用來存 30 秒內收集到的有效資料
    rows = []

    # 記錄開始時間
    t0 = time.time()

    # 在 30 秒內持續讀取 Arduino Serial
    while time.time() - t0 < CALIB_SECONDS:
        raw = ser.readline().decode("utf-8", errors="ignore").strip()

        # 空行就略過
        if not raw:
            continue

        # 這些通常是 Arduino 的提示文字，不是 CSV 資料，所以略過
        if raw.startswith(("#", "✅", "📋", "⏱", "🍍", "===")):
            continue

        # 解析這一行 CSV 資料
        row = parse_data_line(raw, header_cols)

        # 如果解析失敗就略過
        if row is None:
            continue

        # 收集有效資料
        rows.append(row)

        # 顯示目前收集進度
        elapsed = int(time.time() - t0)
        print(f"Collecting air baseline... {elapsed}/{CALIB_SECONDS} sec", end="\r")

    print()

    # 如果 30 秒內都沒有有效資料，就停止並報錯
    if len(rows) == 0:
        raise RuntimeError("沒有收集到有效資料，無法建立 air_base.json")

    # 計算 air baseline
    out = compute_baseline_from_rows(rows)

    # 寫出 air_base.json
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    # 顯示校正完成結果
    print(f"✅ {args.out} 已建立")
    print(json.dumps(out, ensure_ascii=False, indent=2))


def main():
    # 建立 argparse，讓程式可以從終端機接收參數
    parser = argparse.ArgumentParser()

    # 是否使用 demo 模式，不讀取 Arduino
    parser.add_argument("--demo", action="store_true", help="使用 demo_data/*.xlsx，不讀取 Arduino")

    # demo xlsx 資料夾
    parser.add_argument("--demo-dir", type=str, default=DEMO_DIR, help="demo xlsx 資料夾")

    # 指定 demo case，例如 pineapple_03_20260214
    parser.add_argument("--demo-case", "--case", dest="demo_case", type=str, default=None, help="例如 pineapple_03_20260214")

    # 也可以只指定鳳梨編號，例如 03
    parser.add_argument("--pid", type=str, default=None, help="鳳梨編號，例如 03")

    # 搭配 pid 使用的日期，例如 20260214
    parser.add_argument("--date", type=str, default=None, help="日期，例如 20260214")

    # 指定輸出的 air baseline JSON 檔案名稱
    parser.add_argument("--out", type=str, default="air_base.json", help="輸出 JSON 路徑")

    # 指定 Arduino port，如果不指定就自動偵測
    parser.add_argument("--port", type=str, default=None, help="指定 Arduino port，例如 /dev/ttyACM0")

    # 解析終端機參數
    args = parser.parse_args()

    # 如果有使用 demo 參數、demo_case，或同時給 pid/date，就進入 demo 校正模式
    if args.demo or args.demo_case or (args.pid and args.date):
        run_demo_calibration(args)

    # 否則就進入實測模式，從 Arduino 即時讀取資料
    else:
        run_real_calibration(args)


# Python 程式進入點
if __name__ == "__main__":
    main()
