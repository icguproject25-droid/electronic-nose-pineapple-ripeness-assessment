import argparse
import glob
import json
import os
import re
import sys
import time

import numpy as np
import serial

BAUD = 115200
CALIB_SECONDS = 30
DEMO_DIR = "demo_data"
SENSORS = ["MQ2", "MQ3", "MQ9", "MQ135", "TGS2602", "TGS2620"]
ENV_COLS = ["Temp_C", "Humidity_pct", "Pressure_hPa"]


def auto_detect_port():
    ports = sorted(glob.glob("/dev/ttyACM*")) + sorted(glob.glob("/dev/ttyUSB*"))
    if not ports:
        raise RuntimeError("找不到 Arduino 序列埠")
    return ports[0]


def parse_header_line(line: str):
    return [x.strip() for x in line.split(",")]


def parse_data_line(line: str, header_cols: list):
    vals = [x.strip() for x in line.split(",")]
    if len(vals) != len(header_cols):
        return None
    row = dict(zip(header_cols, vals))
    try:
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
        return None


def normalize_case(pid: str, date: str) -> str:
    pid = str(pid).strip().replace("pineapple_", "")
    return f"pineapple_{pid}_{date}"


def load_xlsx_sensor_df(path: str):
    # 只有 demo 模式才需要 pandas，實測模式不會用到。
    import pandas as pd

    raw = pd.read_excel(path, header=None)
    header_row = None
    for i, row in raw.iterrows():
        if str(row.iloc[0]).strip() == "timestamp_ms":
            header_row = i
            break
    if header_row is None:
        raise ValueError(f"找不到 timestamp_ms header：{path}")

    df = raw.iloc[header_row + 1:].copy()
    df.columns = raw.iloc[header_row].tolist()
    df = df.reset_index(drop=True)
    df = df[~df["timestamp_ms"].astype(str).str.startswith("#")]
    df = df.reset_index(drop=True)

    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def scan_air_files(demo_dir=DEMO_DIR):
    pattern = os.path.join(demo_dir, "pineapple_*_air.xlsx")
    result = {}
    for f in sorted(glob.glob(pattern)):
        base = os.path.basename(f)
        m = re.search(r"^(pineapple_\w+_\d{8})_air\.xlsx$", base)
        if m:
            result[m.group(1)] = f
    return result


def compute_baseline_from_rows(rows):
    out = {}
    for s in SENSORS:
        col = f"{s}_raw"
        arr = np.array([r[col] for r in rows if col in r and np.isfinite(r[col])], dtype=float)
        out[s] = float(np.mean(arr)) if len(arr) > 0 else 1.0

    for k in ENV_COLS:
        arr = np.array([r[k] for r in rows if k in r and np.isfinite(r[k])], dtype=float)
        if len(arr) > 0:
            out[k] = float(np.mean(arr))
    return out


def run_demo_calibration(args):
    print("=" * 60)
    print("🌫️ Air baseline calibration（demo xlsx mode）")
    print("=" * 60)

    air_files = scan_air_files(args.demo_dir)
    if not air_files:
        raise RuntimeError(f"在 {args.demo_dir}/ 找不到任何 *_air.xlsx")

    case_key = args.demo_case
    if not case_key and args.pid and args.date:
        case_key = normalize_case(args.pid, args.date)

    if case_key:
        if case_key not in air_files:
            print(f"❌ 找不到 {case_key} 的 air 檔案。")
            print("可用 case：")
            for k in sorted(air_files):
                print(" -", k)
            sys.exit(1)
    else:
        print("可用空氣校正檔案：")
        keys = sorted(air_files)
        for idx, k in enumerate(keys):
            print(f"  [{idx}] {k}  ({air_files[k]})")
        case_key = keys[int(input("請輸入編號：").strip())]

    path = air_files[case_key]
    print(f"Demo mode: 使用歷史 air 資料，不讀取 Arduino 即時 Serial")
    print(f"Demo case: {case_key}")
    print(f"Air file: {path}")

    df = load_xlsx_sensor_df(path)
    df_win = df.head(CALIB_SECONDS) if len(df) >= CALIB_SECONDS else df

    rows = []
    for _, row in df_win.iterrows():
        r = {}
        for s in SENSORS:
            col = f"{s}_raw"
            if col in df_win.columns:
                try:
                    r[col] = float(row[col])
                except Exception:
                    r[col] = np.nan
        for k in ENV_COLS:
            if k in df_win.columns:
                try:
                    r[k] = float(row[k])
                except Exception:
                    r[k] = np.nan
        rows.append(r)

    if not rows:
        raise RuntimeError("demo air 檔沒有有效資料，無法建立 air_base.json")

    out = compute_baseline_from_rows(rows)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"共 {len(df)} 筆資料，使用前 {len(rows)} 筆計算 baseline")
    print(f"✅ {args.out} 已建立")
    print(json.dumps(out, ensure_ascii=False, indent=2))


def run_real_calibration(args):
    print("=" * 60)
    print("🌫️ Air baseline calibration (30 sec)")
    print("=" * 60)
    print("請確認容器內沒有鳳梨，只量空氣。")
    print(f"將收集 {CALIB_SECONDS} 秒資料後輸出 {args.out}")
    print("-" * 60)

    port = args.port or auto_detect_port()
    print("Arduino port:", port)

    ser = serial.Serial(port, BAUD, timeout=1)
    time.sleep(2)

    header_cols = None
    print("等待 CSV header ...")

    while True:
        raw = ser.readline().decode("utf-8", errors="ignore").strip()
        if not raw:
            continue
        if raw.startswith("timestamp_ms,"):
            header_cols = parse_header_line(raw)
            print("✅ CSV header detected")
            break

    rows = []
    t0 = time.time()

    while time.time() - t0 < CALIB_SECONDS:
        raw = ser.readline().decode("utf-8", errors="ignore").strip()
        if not raw:
            continue
        if raw.startswith(("#", "✅", "📋", "⏱", "🍍", "===")):
            continue

        row = parse_data_line(raw, header_cols)
        if row is None:
            continue

        rows.append(row)
        elapsed = int(time.time() - t0)
        print(f"Collecting air baseline... {elapsed}/{CALIB_SECONDS} sec", end="\r")

    print()
    if len(rows) == 0:
        raise RuntimeError("沒有收集到有效資料，無法建立 air_base.json")

    out = compute_baseline_from_rows(rows)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"✅ {args.out} 已建立")
    print(json.dumps(out, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true", help="使用 demo_data/*.xlsx，不讀取 Arduino")
    parser.add_argument("--demo-dir", type=str, default=DEMO_DIR, help="demo xlsx 資料夾")
    parser.add_argument("--demo-case", "--case", dest="demo_case", type=str, default=None, help="例如 pineapple_03_20260214")
    parser.add_argument("--pid", type=str, default=None, help="鳳梨編號，例如 03")
    parser.add_argument("--date", type=str, default=None, help="日期，例如 20260214")
    parser.add_argument("--out", type=str, default="air_base.json", help="輸出 JSON 路徑")
    parser.add_argument("--port", type=str, default=None, help="指定 Arduino port，例如 /dev/ttyACM0")
    args = parser.parse_args()

    if args.demo or args.demo_case or (args.pid and args.date):
        run_demo_calibration(args)
    else:
        run_real_calibration(args)


if __name__ == "__main__":
    main()
