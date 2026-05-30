"""
calibrate_air_from_csv.py
從 demo_data/ 資料夾讀取指定日期的 air xlsx，計算空氣 baseline 並寫出 air_base.json。

用法：
    python calibrate_air_from_csv.py --date 20260201
    python calibrate_air_from_csv.py          # 自動掃描可用日期讓使用者選擇
"""

import argparse
import glob
import json
import os
import re
import sys

import numpy as np
import pandas as pd

DEMO_DIR = "demo_data"
SENSORS = ["MQ2", "MQ3", "MQ9", "MQ135", "TGS2602", "TGS2620"]
ENV_COLS = ["Temp_C", "Humidity_pct", "Pressure_hPa"]


# ─── 工具函式 ─────────────────────────────────────────────────────────────────

def load_xlsx_sensor_df(path: str) -> pd.DataFrame:
    """讀取含有 comment 首行的 xlsx，回傳以 timestamp_ms 為首欄的 DataFrame。"""
    raw = pd.read_excel(path, header=None)
    # 找 timestamp_ms 所在列
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

    # 跳過 comment 行（# 開頭）
    df = df[~df["timestamp_ms"].astype(str).str.startswith("#")]
    df = df.reset_index(drop=True)

    # 轉數值
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def scan_air_files():
    """掃描 demo_data/ 中所有 air xlsx，回傳 {date_str: path} dict。"""
    pattern = os.path.join(DEMO_DIR, "pineapple_*_air.xlsx")
    files = sorted(glob.glob(pattern))
    result = {}
    for f in files:
        m = re.search(r"pineapple_\w+_(\d{8})_air\.xlsx", os.path.basename(f))
        if m:
            result[m.group(1)] = f
    return result


def compute_baseline(df: pd.DataFrame) -> dict:
    out = {}
    for s in SENSORS:
        col = f"{s}_raw"
        if col in df.columns:
            arr = df[col].dropna().values.astype(float)
            arr = arr[np.isfinite(arr)]
            out[s] = float(np.mean(arr)) if len(arr) > 0 else 1.0
    for k in ENV_COLS:
        if k in df.columns:
            arr = df[k].dropna().values.astype(float)
            arr = arr[np.isfinite(arr)]
            if len(arr) > 0:
                out[k] = float(np.mean(arr))
    return out


# ─── main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", type=str, default=None,
                        help="日期字串，例如 20260201")
    parser.add_argument("--out", type=str, default="air_base.json",
                        help="輸出 JSON 路徑（預設 air_base.json）")
    args = parser.parse_args()

    print("=" * 60)
    print("🌫️  Air baseline calibration（CSV 模擬模式）")
    print("=" * 60)

    air_files = scan_air_files()
    if not air_files:
        print(f"❌ 在 {DEMO_DIR}/ 找不到任何 *_air.xlsx，請確認路徑。")
        sys.exit(1)

    # 選擇日期
    if args.date:
        date_str = args.date
        if date_str not in air_files:
            print(f"❌ 找不到日期 {date_str} 的 air 檔案。")
            print("可用日期：", list(air_files.keys()))
            sys.exit(1)
    else:
        print("可用空氣校正日期：")
        dates = sorted(air_files.keys())
        for idx, d in enumerate(dates):
            print(f"  [{idx}] {d}  ({air_files[d]})")
        choice = input("請輸入編號：").strip()
        try:
            date_str = dates[int(choice)]
        except Exception:
            print("❌ 無效選擇")
            sys.exit(1)

    path = air_files[date_str]
    print(f"\n讀取：{path}")

    df = load_xlsx_sensor_df(path)
    print(f"共 {len(df)} 筆資料，欄位：{df.columns.tolist()}")

    baseline = compute_baseline(df)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(baseline, f, ensure_ascii=False, indent=2)

    print(f"\n✅ {args.out} 已建立")
    print(json.dumps(baseline, ensure_ascii=False, indent=2))
    print("=" * 60)


if __name__ == "__main__":
    main()
