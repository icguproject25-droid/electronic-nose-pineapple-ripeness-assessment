"""
inference_from_csv.py
從 demo_data/ 資料夾讀取指定日期的鳳梨 xlsx，搭配 air_base.json 做推論。

用法：
    python inference_from_csv.py --case pineapple_10_20260208 --stage 未熟
    python inference_from_csv.py          # 互動式選擇
    python inference_from_csv.py --pid 10 --date 20260208 --stage 未熟
"""

import argparse
import glob
import json
import os
import pickle
import re
import sys

import numpy as np
import pandas as pd

DEMO_DIR = "demo_data"
WINDOW = 30
SENSORS = ["MQ2", "MQ3", "MQ9", "MQ135", "TGS2602"]

STAGE_TEXT = {0: "未熟", 1: "初熟", 2: "成熟", 3: "過熟"}
STAGE_FROM_TEXT = {"未熟": 0, "初熟": 1, "成熟": 2, "過熟": 3}


# ─── 工具函式（與 inference_30s_1.py 保持一致）───────────────────────────────

def safe_ratio(a, b):
    return float(a) / (float(b) + 1e-9)


def safe_corr(x, y):
    if len(x) < 2:
        return 0.0
    try:
        c = np.corrcoef(x, y)[0, 1]
        return float(c) if np.isfinite(c) else 0.0
    except Exception:
        return 0.0


def safe_slope(x):
    if len(x) < 2:
        return 0.0
    try:
        return float(np.polyfit(range(len(x)), x, 1)[0])
    except Exception:
        return 0.0


def safe_mean_diff(x):
    if len(x) < 2:
        return 0.0
    try:
        d = np.diff(x)
        return float(np.mean(d)) if len(d) > 0 else 0.0
    except Exception:
        return 0.0


def safe_auc(x):
    try:
        fn = np.trapezoid if hasattr(np, "trapezoid") else np.trapz
        return float(fn(x))
    except Exception:
        return 0.0


def load_xlsx_sensor_df(path: str) -> pd.DataFrame:
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


def scan_pineapple_files():
    """回傳 {(case_key, stage_text): path}，case_key 例如 pineapple_03_20260214。"""
    pattern = os.path.join(DEMO_DIR, "pineapple_*.xlsx")
    files = sorted(glob.glob(pattern))
    result = {}
    for f in files:
        base = os.path.basename(f)
        if "_air.xlsx" in base:
            continue
        m = re.search(r"^(pineapple_\w+_\d{8})_(.+)\.xlsx$", base)
        if m:
            result[(m.group(1), m.group(2))] = f
    return result


def normalize_case(pid: str, date: str) -> str:
    pid = str(pid).strip().replace("pineapple_", "")
    return f"pineapple_{pid}_{date}"

def build_features(rows: list, air: dict) -> dict:
    data = {s: np.array([r[s] for r in rows], dtype=float) for s in SENSORS}

    def base(s):
        v = air.get(s, 1.0)
        return float(v) if v and np.isfinite(v) and v != 0 else 1.0

    feat = {}
    feat["MQ2_MQ3_ratio"] = safe_ratio(np.mean(data["MQ2"]), np.mean(data["MQ3"]))
    feat["MQ3_MQ135_ratio"] = safe_ratio(np.mean(data["MQ3"]), np.mean(data["MQ135"]))
    feat["MQ3_TGS2602_ratio"] = safe_ratio(np.mean(data["MQ3"]), np.mean(data["TGS2602"]))
    feat["MQ3_MQ135_correlation"] = safe_corr(data["MQ3"], data["MQ135"])

    feat["MQ2_auc_norm"] = safe_auc(data["MQ2"]) / (len(data["MQ2"]) * base("MQ2"))
    feat["MQ2_mean_norm"] = np.mean(data["MQ2"]) / base("MQ2")

    feat["MQ3_range_norm"] = (np.max(data["MQ3"]) - np.min(data["MQ3"])) / base("MQ3")
    feat["MQ3_max_norm"] = np.max(data["MQ3"]) / base("MQ3")
    feat["MQ3_std_norm"] = np.std(data["MQ3"]) / base("MQ3")

    feat["MQ9_slope"] = safe_slope(data["MQ9"])
    feat["MQ9_min_norm"] = np.min(data["MQ9"]) / base("MQ9")
    feat["MQ9_delta_mean"] = safe_mean_diff(data["MQ9"])

    feat["TGS2602_min_norm"] = np.min(data["TGS2602"]) / base("TGS2602")
    feat["TGS2602_delta_std"] = np.std(np.diff(data["TGS2602"])) if len(data["TGS2602"]) >= 2 else 0.0
    feat["TGS2602_std_norm"] = np.std(data["TGS2602"]) / base("TGS2602")

    return feat, data


def build_raw_maturity_percent(proba):
    score = (proba[0]*0 + proba[1]*1 + proba[2]*2 + proba[3]*3) / 3.0
    return int(round(score * 100))


def build_bar(percent):
    blocks = max(0, min(20, int(round(percent / 5))))
    return "█" * blocks + "░" * (20 - blocks)


def maturity_zone_text(percent):
    if percent <= 16:
        return "未熟區"
    elif percent <= 49:
        return "初熟區"
    elif percent <= 82:
        return "成熟區"
    else:
        return "過熟區"


def overripe_tendency_text(p3):
    p = float(p3) * 100.0
    if p < 10:
        return f"{p:.2f}%（低）"
    elif p < 20:
        return f"{p:.2f}%（微弱）"
    elif p < 35:
        return f"{p:.2f}%（明顯）"
    else:
        return f"{p:.2f}%（高）"


def air_or_no_sample_guard(feat, proba=None):
    reasons = []
    mq2_mean_norm = float(feat.get("MQ2_mean_norm", 999.0))
    mq9_min_norm = float(feat.get("MQ9_min_norm", 999.0))
    tgs2602_min_norm = float(feat.get("TGS2602_min_norm", 999.0))
    mq3_std_norm = float(feat.get("MQ3_std_norm", 999.0))
    tgs2602_std_norm = float(feat.get("TGS2602_std_norm", 999.0))
    mq9_slope = float(feat.get("MQ9_slope", 999.0))
    mq3_mq135_ratio = float(feat.get("MQ3_MQ135_ratio", 0.0))
    p3 = float(proba[3]) if proba is not None and len(proba) >= 4 else 0.0

    if tgs2602_min_norm > 1.02:
        return False, ["TGS2602_min_norm 高於 1.02，視為有效樣本"]
    if mq3_mq135_ratio > 2.00:
        return False, ["MQ3_MQ135_ratio 高於 2.00，視為有效樣本"]
    if p3 >= 0.08 and mq3_mq135_ratio > 1.98:
        return False, [f"Stage3={p3:.4f} 且 MQ3_MQ135_ratio 偏高，視為有效樣本"]

    baseline_hits = 0
    weak_signal_hits = 0
    if 0.99 <= mq2_mean_norm <= 1.01:
        baseline_hits += 1
        reasons.append(f"MQ2_mean_norm={mq2_mean_norm:.6f} 非常接近 baseline")
    if 0.99 <= mq9_min_norm <= 1.01:
        baseline_hits += 1
        reasons.append(f"MQ9_min_norm={mq9_min_norm:.6f} 非常接近 baseline")
    if 0.99 <= tgs2602_min_norm <= 1.01:
        baseline_hits += 1
        reasons.append(f"TGS2602_min_norm={tgs2602_min_norm:.6f} 非常接近 baseline")
    if mq3_std_norm < 0.0028:
        weak_signal_hits += 1
        reasons.append(f"MQ3_std_norm={mq3_std_norm:.6f} 波動很小")
    if tgs2602_std_norm < 0.0030:
        weak_signal_hits += 1
        reasons.append(f"TGS2602_std_norm={tgs2602_std_norm:.6f} 波動很小")
    if abs(mq9_slope) < 0.006:
        weak_signal_hits += 1
        reasons.append(f"MQ9_slope={mq9_slope:.6f} 幾乎無趨勢")

    trigger = (baseline_hits == 3 and weak_signal_hits >= 2)
    return trigger, reasons


def get_closest_stage_text(proba, pred):
    sorted_idx = np.argsort(proba)[::-1]
    top1, top2 = int(sorted_idx[0]), int(sorted_idx[1])
    if abs(top1 - top2) == 1 and proba[top2] >= 0.15:
        return f"{STAGE_TEXT[top1]}（接近{STAGE_TEXT[top2]}）"
    return STAGE_TEXT[top1]


def get_display_text(proba, pred):
    sorted_idx = np.argsort(proba)[::-1]
    top1 = int(sorted_idx[0])
    p3 = float(proba[3])
    if top1 == 2 and p3 >= 0.18:
        return "成熟，明顯接近過熟"
    elif top1 == 2 and p3 >= 0.08:
        return "成熟，但已有過熟傾向"
    return get_closest_stage_text(proba, pred)


def overripe_override(pred, proba, feat):
    reasons = []
    if int(pred) != 2:
        return pred, False, reasons
    p3 = float(proba[3])
    p2 = float(proba[2])
    mq3_mq135_ratio = float(feat.get("MQ3_MQ135_ratio", 0.0))
    tgs2602_min_norm = float(feat.get("TGS2602_min_norm", 0.0))
    mq2_mean_norm = float(feat.get("MQ2_mean_norm", 999.0))

    strong_rule = p3 >= 0.10 and tgs2602_min_norm >= 1.05 and mq3_mq135_ratio >= 2.08
    normal_rule = p3 >= 0.11 and tgs2602_min_norm >= 0.97 and mq3_mq135_ratio >= 2.00 and mq2_mean_norm <= 1.01
    soft_rule = p3 >= 0.12 and p2 <= 0.75 and mq3_mq135_ratio >= 2.00

    if strong_rule:
        reasons.append(f"強條件：Stage3={p3:.4f}, TGS2602={tgs2602_min_norm:.4f}, ratio={mq3_mq135_ratio:.4f}")
    elif normal_rule:
        reasons.append(f"一般條件：Stage3={p3:.4f}, TGS2602={tgs2602_min_norm:.4f}, ratio={mq3_mq135_ratio:.4f}")
    elif soft_rule:
        reasons.append(f"軟條件：Stage3={p3:.4f}, Stage2={p2:.4f}, ratio={mq3_mq135_ratio:.4f}")

    if strong_rule or normal_rule or soft_rule:
        return 3, True, reasons
    return pred, False, reasons


def build_final_display_percent(raw_percent, final_pred, override_used, proba, feat):
    if not override_used or final_pred != 3:
        return raw_percent
    p3 = float(proba[3])
    tgs = float(feat.get("TGS2602_min_norm", 1.0))
    ratio = float(feat.get("MQ3_MQ135_ratio", 1.0))
    p3_score = np.clip((p3 - 0.08) / 0.22, 0.0, 1.0)
    tgs_score = np.clip((tgs - 0.970) / 0.165, 0.0, 1.0)
    ratio_score = np.clip((ratio - 2.00) / 0.18, 0.0, 1.0)
    strength = (p3_score + tgs_score + ratio_score) / 3.0
    pct = int(round(83 + 17 * strength))
    return max(raw_percent, max(83, min(100, pct)))


def print_sensor_summary(data):
    print("\n" + "=" * 60)
    print("📊 Raw sensor summary（推論窗口）")
    print("=" * 60)
    for s in SENSORS:
        arr = data[s]
        print(f"{s:8s} | mean={np.mean(arr):8.3f} | min={np.min(arr):8.3f} | "
              f"max={np.max(arr):8.3f} | std={np.std(arr):8.3f}")


def print_feature_summary(feature_columns, feat):
    print("\n" + "=" * 60)
    print("🧪 Feature values used by model")
    print("=" * 60)
    for f in feature_columns:
        print(f"{f:28s} = {feat.get(f, 0.0):.6f}")


def print_probabilities(proba):
    print("\n" + "=" * 60)
    print("📈 詳細機率")
    print("=" * 60)
    for i, p in enumerate(proba):
        print(f"Stage {i}（{STAGE_TEXT[i]}）: {p:.4f} ({p*100:.2f}%)")
    print("-" * 60)
    sorted_idx = np.argsort(proba)[::-1]
    top1, top2 = int(sorted_idx[0]), int(sorted_idx[1])
    gap = float(proba[top1] - proba[top2])
    print(f"Top-1: Stage {top1}（{STAGE_TEXT[top1]}）")
    print(f"Top-2: Stage {top2}（{STAGE_TEXT[top2]}）")
    print(f"Probability gap = {gap:.4f}")
    if gap < 0.10:
        print("⚠️ 邊界案例，前兩類非常接近")
    elif gap < 0.20:
        print("ℹ️ 有一點接近次高類別")
    else:
        print("✅ 預測相對明確")


# ─── main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", type=str, default=None, help="例如 pineapple_03_20260214")
    parser.add_argument("--pid", type=str, default=None, help="鳳梨編號，例如 03")
    parser.add_argument("--date", type=str, default=None, help="日期，例如 20260214")
    parser.add_argument("--stage", type=str, default=None, help="熟度標籤，例如 未熟 / 初熟 / 成熟 / 過熟")
    parser.add_argument("--air", type=str, default="air_base.json", help="air baseline JSON 路徑")
    parser.add_argument("--model", type=str, default="deploy_student.pkl")
    parser.add_argument("--features", type=str, default="feature_columns.json")
    args = parser.parse_args()

    print("=" * 60)
    print("🍍 Pineapple ripeness detection（CSV 模擬模式）")
    print("=" * 60)

    # ── 掃描鳳梨檔案 ──────────────────────────────────────────────────────────
    pine_files = scan_pineapple_files()
    if not pine_files:
        print(f"❌ 在 {DEMO_DIR}/ 找不到任何鳳梨 xlsx")
        sys.exit(1)

    keys = sorted(pine_files.keys())

    case_key = args.case
    if not case_key and args.pid and args.date:
        case_key = normalize_case(args.pid, args.date)

    if case_key:
        candidates = [(c, s) for (c, s) in keys if c == case_key]
        if not candidates:
            print(f"❌ 找不到 {case_key} 的鳳梨資料")
            print("可用 case：")
            for c, s in keys:
                print(f" - {c} / {s}")
            sys.exit(1)
        if args.stage:
            candidates = [(c, s) for (c, s) in candidates if s == args.stage]
            if not candidates:
                print(f"❌ 找不到 {case_key} / {args.stage}")
                sys.exit(1)
        if len(candidates) > 1:
            print("同 case 有多個熟度，請選擇：")
            for idx, (c, s) in enumerate(candidates):
                print(f"  [{idx}] {c}  {s}")
            key = candidates[int(input("請輸入編號：").strip())]
        else:
            key = candidates[0]
    elif args.date:
        candidates = [(c, s) for (c, s) in keys if args.date in c]
        if args.stage:
            candidates = [(c, s) for (c, s) in candidates if s == args.stage]
        if not candidates:
            print(f"❌ 找不到日期 {args.date} 的鳳梨資料")
            sys.exit(1)
        if len(candidates) > 1:
            print("同一日期有多個檔案，請選擇：")
            for idx, (c, s) in enumerate(candidates):
                print(f"  [{idx}] {c}  {s}")
            key = candidates[int(input("請輸入編號：").strip())]
        else:
            key = candidates[0]
    else:
        print("可用鳳梨測試檔案：")
        for idx, (c, s) in enumerate(keys):
            print(f"  [{idx}] {c}  {s}  ({pine_files[(c,s)]})")
        ch = input("請輸入編號：").strip()
        key = keys[int(ch)]

    case_key, stage_label = key
    date_str = case_key
    path = pine_files[key]
    print(f"\nCase：{case_key}  熟度標籤：{stage_label}")
    print(f"讀取：{path}")

    # ── 載入資料 ──────────────────────────────────────────────────────────────
    df = load_xlsx_sensor_df(path)
    print(f"共 {len(df)} 筆資料")

    # 取最後 WINDOW 筆（模擬 30 秒窗口）
    df_win = df.tail(WINDOW) if len(df) >= WINDOW else df
    rows = []
    for _, row in df_win.iterrows():
        try:
            r = {s: float(row[f"{s}_raw"]) for s in SENSORS if f"{s}_raw" in df_win.columns}
            if all(s in r for s in SENSORS):
                rows.append(r)
        except Exception:
            pass

    print(f"推論窗口：{len(rows)} 筆")
    if len(rows) == 0:
        print("❌ 沒有有效資料")
        sys.exit(1)

    # ── 載入 air_base.json ────────────────────────────────────────────────────
    if not os.path.exists(args.air):
        print(f"❌ 找不到 {args.air}，請先執行 calibrate_air_from_csv.py")
        sys.exit(1)
    with open(args.air, "r", encoding="utf-8") as f:
        air = json.load(f)
    print(f"Air baseline loaded from {args.air}")

    # ── 載入模型 & feature columns ────────────────────────────────────────────
    with open(args.model, "rb") as f:
        model = pickle.load(f)
    with open(args.features, "r", encoding="utf-8") as f:
        feature_columns = json.load(f)
    print(f"Model loaded | Feature count: {len(feature_columns)}")

    # ── 特徵工程 ──────────────────────────────────────────────────────────────
    feat, data = build_features(rows, air)
    print_sensor_summary(data)
    print_feature_summary(feature_columns, feat)

    # ── 推論 ──────────────────────────────────────────────────────────────────
    X = np.array([feat.get(f, 0.0) for f in feature_columns], dtype=float).reshape(1, -1)
    raw_pred = int(model.predict(X)[0])
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(X)[0]
    else:
        proba = np.zeros(4, dtype=float)
        proba[raw_pred] = 1.0

    print_probabilities(proba)

    # ── 防呆 & 校正 ───────────────────────────────────────────────────────────
    guard_triggered, guard_reasons = air_or_no_sample_guard(feat, proba=proba)
    display_text = get_display_text(proba, raw_pred)
    final_pred, override_used, override_reasons = overripe_override(raw_pred, proba, feat)
    if override_used:
        display_text = "過熟"

    raw_pct = build_raw_maturity_percent(proba)
    final_pct = build_final_display_percent(raw_pct, final_pred, override_used, proba, feat)

    # ── 結果輸出（保持與 inference_30s_1.py 完全相同的格式供 app 解析）────────
    print("\n" + "=" * 60)
    print("🍍 結果")
    print("=" * 60)
    print(f"【模擬模式】日期：{date_str}  標籤：{stage_label}")
    print(f"Warmup sec: 0")
    print(f"Feature count: {len(feature_columns)}")
    print(f"Target window: {WINDOW} sec")

    if guard_triggered:
        print("成熟度判定：⚠️ 無有效鳳梨訊號")
        print(f"原始模型分類：Stage {raw_pred}（{STAGE_TEXT[raw_pred]}）")
        print("校正後分類：—")
        print(f"成熟度條：[ {build_bar(raw_pct)} ] {raw_pct}%")
        print(f"成熟區段：{maturity_zone_text(raw_pct)}")
        print(f"過熱傾向：{overripe_tendency_text(proba[3])}")
        print("空氣/無樣本防呆：✅ 已觸發")
        print("判定依據：")
        for r in guard_reasons:
            print(f" - {r}")
    else:
        print(f"成熟度判定：{display_text}")
        print(f"原始模型分類：Stage {raw_pred}（{STAGE_TEXT[raw_pred]}）")
        print(f"校正後分類：Stage {final_pred}（{STAGE_TEXT[final_pred]}）")
        if override_used and final_pred == 3:
            print(f"原始成熟度條：[ {build_bar(raw_pct)} ] {raw_pct}%")
            print(f"校正後成熟度條：[ {build_bar(final_pct)} ] {final_pct}%")
        else:
            print(f"成熟度條：[ {build_bar(final_pct)} ] {final_pct}%")
        print(f"成熟區段：{maturity_zone_text(final_pct)}")
        print(f"過熱傾向：{overripe_tendency_text(proba[3])}")
        print("空氣/無樣本防呆：— 未觸發")
        if override_used:
            print("過熟校正：✅ 已啟用")
            print("校正依據：")
            for r in override_reasons:
                print(f" - {r}")
        else:
            print("過熟校正：— 未啟用")

    print("=" * 60)
    print("Program finished")


if __name__ == "__main__":
    main()
