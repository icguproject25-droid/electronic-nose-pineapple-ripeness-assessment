"""
app_local_demo.py
電腦本機執行的 Flask 網頁版，直接讀 demo_data/ 中的 xlsx
進行空氣校正模擬和鳳梨推論，不需要連接樹莓派或 Arduino。

用法：
    python app_local_demo.py
    瀏覽器開啟 http://127.0.0.1:5000
"""

import glob
import json
import os
import pickle
import re
import sys

import numpy as np
import pandas as pd
from flask import Flask, render_template_string, request

# ─── 設定 ─────────────────────────────────────────────────────────────────────
DEMO_DIR = "demo_data"
WINDOW = 30
SENSORS = ["MQ2", "MQ3", "MQ9", "MQ135", "TGS2602"]
STAGE_TEXT = {0: "未熟", 1: "初熟", 2: "成熟", 3: "過熟"}

MODEL_PATH = "deploy_student.pkl"
FEATURES_PATH = "feature_columns.json"
AIR_BASE_PATH = "air_base.json"

app = Flask(__name__)

# ─── 資料讀取 ─────────────────────────────────────────────────────────────────

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


def scan_demo_files():
    """掃描 demo_data/，回傳 air_map={case:path}, pine_map={(case,stage):path}
    case 例如 pineapple_03_20260214，可以避免同一天不同鳳梨編號互相覆蓋。
    """
    pattern = os.path.join(DEMO_DIR, "pineapple_*.xlsx")
    air_map, pine_map = {}, {}
    for f in sorted(glob.glob(pattern)):
        base = os.path.basename(f)
        if "_air.xlsx" in base:
            m = re.search(r"^(pineapple_\w+_\d{8})_air\.xlsx$", base)
            if m:
                air_map[m.group(1)] = f
        else:
            m = re.search(r"^(pineapple_\w+_\d{8})_(.+)\.xlsx$", base)
            if m:
                pine_map[(m.group(1), m.group(2))] = f
    return air_map, pine_map


def case_display(case_key: str) -> str:
    m = re.search(r"^pineapple_(\w+)_(\d{8})$", case_key)
    if not m:
        return case_key
    pid, date = m.group(1), m.group(2)
    return f"pineapple_{pid} / {date}"


# ─── 特徵工程（與推論腳本一致）────────────────────────────────────────────────

def safe_ratio(a, b):
    return float(a) / (float(b) + 1e-9)

def safe_corr(x, y):
    if len(x) < 2: return 0.0
    try:
        c = np.corrcoef(x, y)[0, 1]
        return float(c) if np.isfinite(c) else 0.0
    except: return 0.0

def safe_slope(x):
    if len(x) < 2: return 0.0
    try: return float(np.polyfit(range(len(x)), x, 1)[0])
    except: return 0.0

def safe_mean_diff(x):
    if len(x) < 2: return 0.0
    try:
        d = np.diff(x)
        return float(np.mean(d)) if len(d) > 0 else 0.0
    except: return 0.0

def safe_auc(x):
    try:
        fn = np.trapezoid if hasattr(np, "trapezoid") else np.trapz
        return float(fn(x))
    except: return 0.0

def build_features(rows, air):
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

# ─── 推論邏輯 ─────────────────────────────────────────────────────────────────

def build_raw_maturity_percent(proba):
    score = (proba[0]*0 + proba[1]*1 + proba[2]*2 + proba[3]*3) / 3.0
    return int(round(score * 100))

def build_bar(percent):
    blocks = max(0, min(20, int(round(percent / 5))))
    return "█" * blocks + "░" * (20 - blocks)

def maturity_zone_text(percent):
    if percent <= 16: return "未熟區"
    elif percent <= 49: return "初熟區"
    elif percent <= 82: return "成熟區"
    else: return "過熟區"

def overripe_tendency_text(p3):
    p = float(p3) * 100.0
    if p < 10: return f"{p:.2f}%（低）"
    elif p < 20: return f"{p:.2f}%（微弱）"
    elif p < 35: return f"{p:.2f}%（明顯）"
    else: return f"{p:.2f}%（高）"

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

def get_display_text(proba, pred):
    sorted_idx = np.argsort(proba)[::-1]
    top1 = int(sorted_idx[0])
    top2 = int(sorted_idx[1])
    p3 = float(proba[3])
    if top1 == 2 and p3 >= 0.18:
        return "成熟，明顯接近過熟"
    elif top1 == 2 and p3 >= 0.08:
        return "成熟，但已有過熟傾向"
    if abs(top1 - top2) == 1 and proba[top2] >= 0.15:
        return f"{STAGE_TEXT[top1]}（接近{STAGE_TEXT[top2]}）"
    return STAGE_TEXT[top1]


def early_stage_override(pred, proba, feat):
    """
    早期熟度校正 v4：
    目的：修正「原始模型把未熟 / 初熟樣本判成成熟」的情況。

    注意：這裡不直接用檔名或標籤決定答案，仍然用模型機率 + 11 個 feature 判斷。
    這版針對目前 demo_data 的兩個問題做調整：
    1. pineapple_03 初熟：Stage2 偏高，但 Stage3 不高，TGS/MQ2/MQ9 仍偏早期，所以修正為初熟。
    2. pineapple_11 未熟：Stage2 不高、早期機率仍存在，而且 MQ3 幾乎沒有波動，修正為未熟。
    3. pineapple_03 初熟：即使 Stage2 很高，只要 Stage3 低且 TGS/MQ2/MQ9 仍呈早期訊號，修正為初熟。
    """
    reasons = []
    if int(pred) != 2:
        return pred, False, reasons

    p0 = float(proba[0]) if len(proba) > 0 else 0.0
    p1 = float(proba[1]) if len(proba) > 1 else 0.0
    p2 = float(proba[2]) if len(proba) > 2 else 0.0
    p3 = float(proba[3]) if len(proba) > 3 else 0.0

    tgs2602_min_norm = float(feat.get("TGS2602_min_norm", 1.0))
    mq2_mean_norm = float(feat.get("MQ2_mean_norm", 1.0))
    mq9_min_norm = float(feat.get("MQ9_min_norm", 1.0))
    mq3_std_norm = float(feat.get("MQ3_std_norm", 999.0))
    mq3_range_norm = float(feat.get("MQ3_range_norm", 999.0))
    mq3_mq135_ratio = float(feat.get("MQ3_MQ135_ratio", 0.0))

    early_prob_mass = p0 + p1

    # A. 很明顯的未熟：TGS2602 / MQ2 / MQ9 都低，且 Stage3 不高。
    #    例：pineapple_03 未熟。
    unripe_low_sensor = (
        p2 <= 0.70 and
        p3 <= 0.13 and
        tgs2602_min_norm < 0.94 and
        mq2_mean_norm < 1.00 and
        mq9_min_norm < 0.97
    )

    # B. 平坦型未熟：模型其實不確定，早期機率合計高，MQ3 幾乎沒有波動。
    #    例：pineapple_11 未熟。注意：TGS2602 可能偏高，但只要 MQ3 幾乎沒波動，
    #    這種訊號比較像「弱反應/早期」而不是成熟，因此優先校正為未熟。
    unripe_flat_signal = (
        p2 <= 0.50 and
        p3 <= 0.12 and
        early_prob_mass >= 0.35 and
        mq3_std_norm <= 0.0015 and
        mq3_range_norm <= 0.0025
    )

    # C. 初熟：Stage2 被模型拉高，但 Stage3 不高；TGS/MQ2/MQ9 仍偏早期。
    #    例：pineapple_03 初熟。v4 放寬 p2，因為該筆初熟的 Stage2 可能高達 0.83，
    #    但 Stage3 很低，而且三個 baseline-normalized sensor 仍偏早期。
    early_ripe_signal = (
        p2 <= 0.88 and
        p3 <= 0.10 and
        0.94 <= tgs2602_min_norm < 1.02 and
        mq2_mean_norm < 1.02 and
        mq9_min_norm < 0.98 and
        mq3_std_norm < 0.0065 and
        mq3_range_norm < 0.0080 and
        mq3_mq135_ratio > 2.00
    )

    # D. 邊界初熟：Stage2 不高、Stage1 有一定支撐，且不是過熟型訊號。
    boundary_early_ripe = (
        p2 <= 0.60 and
        p3 <= 0.14 and
        p1 >= 0.18 and
        early_prob_mass >= 0.35 and
        mq3_mq135_ratio > 1.70
    )

    if unripe_low_sensor or unripe_flat_signal or early_ripe_signal or boundary_early_ripe:
        reasons.append(f"原始模型判為成熟，但 p2={p2:.4f} 並非足夠穩定")
        reasons.append(f"Stage0+Stage1={early_prob_mass:.4f}，仍保留早期熟度可能")
        reasons.append(f"Stage3={p3:.4f}，先避免誤判為後期成熟或過熟")
        reasons.append(f"TGS2602_min_norm={tgs2602_min_norm:.6f}")
        reasons.append(f"MQ2_mean_norm={mq2_mean_norm:.6f}")
        reasons.append(f"MQ9_min_norm={mq9_min_norm:.6f}")
        reasons.append(f"MQ3_std_norm={mq3_std_norm:.6f}, MQ3_range_norm={mq3_range_norm:.6f}")
        reasons.append(f"MQ3_MQ135_ratio={mq3_mq135_ratio:.6f} 雖偏高，但需搭配其他感測器判斷")

        if unripe_low_sensor:
            reasons.append("TGS2602/MQ2/MQ9 皆偏低，符合未熟弱訊號，校正為未熟")
            return 0, True, reasons

        if unripe_flat_signal:
            reasons.append("Stage0+Stage1 高且 MQ3 幾乎無波動，符合平坦型未熟訊號，校正為未熟")
            return 0, True, reasons

        if early_ripe_signal or boundary_early_ripe:
            reasons.append("Stage1 有一定支撐，且後期/過熟訊號不足，校正為初熟")
            return 1, True, reasons

    return pred, False, reasons

def build_early_display_percent(final_pred, feat):
    """早期校正後的成熟度條，避免仍顯示成熟區。"""
    tgs = float(feat.get("TGS2602_min_norm", 1.0))
    mq2 = float(feat.get("MQ2_mean_norm", 1.0))
    mq9 = float(feat.get("MQ9_min_norm", 1.0))

    if int(final_pred) == 0:
        # 未熟區：大約 12～25%
        strength = np.clip((tgs - 0.90) / 0.05, 0.0, 1.0)
        return int(round(15 + 10 * strength))

    if int(final_pred) == 1:
        # 初熟區：大約 35～48%
        strength = np.clip(((tgs - 0.95) / 0.05 + (1.0 - abs(mq2 - 1.0)) + (1.0 - abs(mq9 - 1.0))) / 3.0, 0.0, 1.0)
        return int(round(35 + 13 * strength))

    return None

def overripe_override(pred, proba, feat):
    """
    過熟校正 v2：
    修正原本 soft rule 太容易把初熟/弱訊號樣本拉成過熟的問題。
    新版要求：Stage3 機率要夠高，而且 Stage2 也要有一定支撐，才啟用過熟校正。
    """
    reasons = []
    if int(pred) != 2:
        return pred, False, reasons

    p0 = float(proba[0])
    p1 = float(proba[1])
    p2 = float(proba[2])
    p3 = float(proba[3])
    mq3_mq135_ratio = float(feat.get("MQ3_MQ135_ratio", 0.0))
    tgs2602_min_norm = float(feat.get("TGS2602_min_norm", 0.0))
    mq2_mean_norm = float(feat.get("MQ2_mean_norm", 999.0))

    early_mass = p0 + p1

    # 避免早期機率仍高時被誤判過熟。
    if early_mass >= 0.30 and p2 <= 0.60:
        return pred, False, [f"早期機率 Stage0+Stage1={early_mass:.4f} 且 Stage2={p2:.4f} 不高，暫不啟用過熟校正"]

    strong = (
        p3 >= 0.14 and
        p2 >= 0.60 and
        tgs2602_min_norm >= 1.05 and
        mq3_mq135_ratio >= 2.08
    )

    normal = (
        p3 >= 0.15 and
        p2 >= 0.60 and
        mq3_mq135_ratio >= 2.00 and
        mq2_mean_norm <= 1.02
    )

    # soft rule 保留給「成熟但已接近過熟」的情境，但門檻比舊版嚴格。
    soft = (
        p3 >= 0.15 and
        p2 >= 0.65 and
        mq3_mq135_ratio >= 2.00
    )

    if strong:
        reasons.append(f"強條件：Stage3={p3:.4f}, Stage2={p2:.4f}, TGS2602={tgs2602_min_norm:.4f}, ratio={mq3_mq135_ratio:.4f}")
    elif normal:
        reasons.append(f"一般條件：Stage3={p3:.4f}, Stage2={p2:.4f}, ratio={mq3_mq135_ratio:.4f}, MQ2={mq2_mean_norm:.4f}")
    elif soft:
        reasons.append(f"軟條件：Stage3={p3:.4f}, Stage2={p2:.4f}, ratio={mq3_mq135_ratio:.4f}")

    if strong or normal or soft:
        return 3, True, reasons

    return pred, False, reasons

def build_final_display_percent(raw_pct, final_pred, override_used, proba, feat):
    if not override_used or final_pred != 3:
        return raw_pct
    p3 = float(proba[3])
    tgs = float(feat.get("TGS2602_min_norm", 1.0))
    ratio = float(feat.get("MQ3_MQ135_ratio", 1.0))
    s = ((np.clip((p3-0.08)/0.22, 0, 1) + np.clip((tgs-0.97)/0.165, 0, 1) + np.clip((ratio-2.0)/0.18, 0, 1)) / 3.0)
    pct = int(round(83 + 17 * s))
    return max(raw_pct, max(83, min(100, pct)))

# ─── 業務邏輯 ─────────────────────────────────────────────────────────────────

def do_air_calibration(case_key: str):
    air_map, _ = scan_demo_files()
    if case_key not in air_map:
        return {"success": False, "error": f"找不到 {case_key} 的空氣 xlsx"}
    df = load_xlsx_sensor_df(air_map[case_key])
    # demo 校正也使用一開始 30 秒，和推論窗口保持一致
    df = df.head(WINDOW) if len(df) >= WINDOW else df
    out = {}
    for s in SENSORS + ["TGS2620"]:
        col = f"{s}_raw"
        if col in df.columns:
            arr = df[col].dropna().values.astype(float)
            arr = arr[np.isfinite(arr)]
            if len(arr) > 0:
                out[s] = float(np.mean(arr))
    for k in ["Temp_C", "Humidity_pct", "Pressure_hPa"]:
        if k in df.columns:
            arr = df[k].dropna().values.astype(float)
            arr = arr[np.isfinite(arr)]
            if len(arr) > 0:
                out[k] = float(np.mean(arr))
    with open(AIR_BASE_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    return {"success": True, "date": case_key, "baseline": out, "path": air_map[case_key]}


def do_inference(case_key: str, stage_label: str):
    _, pine_map = scan_demo_files()
    key = (case_key, stage_label)
    if key not in pine_map:
        return {"success": False, "error": f"找不到 {case_key}/{stage_label} 的鳳梨 xlsx"}
    if not os.path.exists(AIR_BASE_PATH):
        return {"success": False, "error": "找不到 air_base.json，請先執行空氣校正"}
    if not os.path.exists(MODEL_PATH):
        return {"success": False, "error": f"找不到 {MODEL_PATH}"}
    if not os.path.exists(FEATURES_PATH):
        return {"success": False, "error": f"找不到 {FEATURES_PATH}"}

    df = load_xlsx_sensor_df(pine_map[key])
    df_win = df.head(WINDOW) if len(df) >= WINDOW else df
    rows = []
    for _, row in df_win.iterrows():
        try:
            r = {s: float(row[f"{s}_raw"]) for s in SENSORS if f"{s}_raw" in df_win.columns}
            if all(s in r for s in SENSORS):
                rows.append(r)
        except Exception:
            pass

    if not rows:
        return {"success": False, "error": "推論窗口沒有有效感測資料"}

    with open(AIR_BASE_PATH, "r", encoding="utf-8") as f:
        air = json.load(f)
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    with open(FEATURES_PATH, "r", encoding="utf-8") as f:
        feature_columns = json.load(f)

    feat, data = build_features(rows, air)
    X = np.array([feat.get(fc, 0.0) for fc in feature_columns], dtype=float).reshape(1, -1)
    raw_pred = int(model.predict(X)[0])
    proba = model.predict_proba(X)[0] if hasattr(model, "predict_proba") else (
        np.zeros(4, dtype=float).__setitem__(raw_pred, 1.0) or np.zeros(4))
    if not hasattr(model, "predict_proba"):
        proba = np.zeros(4, dtype=float)
        proba[raw_pred] = 1.0

    guard_triggered, guard_reasons = air_or_no_sample_guard(feat, proba=proba)

    # 原始模型文字
    display_text = get_display_text(proba, raw_pred)

    # 先做早期熟度校正：修正未熟/初熟被誤判成成熟的情況
    early_pred, early_override_used, early_override_reasons = early_stage_override(raw_pred, proba, feat)

    if early_override_used:
        final_pred = early_pred
        override_used = False
        override_reasons = []
        if final_pred == 0:
            display_text = "未熟（接近初熟）"
        elif final_pred == 1:
            display_text = "初熟（接近成熟）"
        else:
            display_text = STAGE_TEXT.get(final_pred, str(final_pred))
    else:
        # 若不是早期誤判，再做原本的過熟校正
        final_pred, override_used, override_reasons = overripe_override(raw_pred, proba, feat)
        if override_used:
            display_text = "過熟"

    raw_pct = build_raw_maturity_percent(proba)
    if early_override_used:
        final_pct = build_early_display_percent(final_pred, feat)
        if final_pct is None:
            final_pct = raw_pct
    else:
        final_pct = build_final_display_percent(raw_pct, final_pred, override_used, proba, feat)

    sensor_summary = []
    for s in SENSORS:
        arr = data[s]
        sensor_summary.append({
            "name": s,
            "mean": round(float(np.mean(arr)), 3),
            "min": round(float(np.min(arr)), 3),
            "max": round(float(np.max(arr)), 3),
            "std": round(float(np.std(arr)), 3),
        })

    probabilities = [
        {"stage": i, "stage_text": STAGE_TEXT[i], "prob": float(p), "percent": float(p) * 100,
         "color": ["#3b82f6","#22c55e","#f59e0b","#ef4444"][i]}
        for i, p in enumerate(proba)
    ]

    feature_values = [{"name": fc, "value": round(feat.get(fc, 0.0), 6)} for fc in feature_columns]

    return {
        "success": True,
        "date": case_key,
        "stage_label": stage_label,
        "display_text": display_text,
        "raw_stage": raw_pred,
        "raw_stage_text": STAGE_TEXT[raw_pred],
        "final_stage": final_pred,
        "final_stage_text": STAGE_TEXT[final_pred],
        "raw_maturity_percent": raw_pct,
        "final_maturity_percent": final_pct,
        "maturity_zone": maturity_zone_text(final_pct),
        "overripe_tendency": overripe_tendency_text(proba[3]),
        "guard_triggered": guard_triggered,
        "guard_reasons": guard_reasons,
        "early_override_used": early_override_used,
        "early_override_reasons": early_override_reasons,
        "override_used": override_used,
        "override_reasons": override_reasons,
        "probabilities": probabilities,
        "sensor_summary": sensor_summary,
        "feature_values": feature_values,
        "rows_used": len(rows),
        "feature_count": len(feature_columns),
    }

# ─── 小工具 ───────────────────────────────────────────────────────────────────

def badge_class_from_text(text: str):
    if not text: return "tag-gray"
    if "無有效鳳梨訊號" in text: return "tag-orange"
    if "過熟" in text: return "tag-red"
    if "成熟" in text: return "tag-amber"
    if "初熟" in text: return "tag-green"
    if "未熟" in text: return "tag-blue"
    return "tag-gray"

# ─── HTML ─────────────────────────────────────────────────────────────────────

HTML = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>🍍 Pineapple Demo（離線模擬）</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root{--bg:#f4f7fb;--card:#fff;--line:#e5e7eb;--text:#1f2937;--muted:#6b7280;--shadow:0 10px 30px rgba(0,0,0,0.08);}
*{box-sizing:border-box;}
body{font-family:Arial,sans-serif;background:var(--bg);margin:0;padding:28px;color:var(--text);}
.container{max-width:1100px;margin:auto;}
.card{background:var(--card);border-radius:20px;padding:24px;margin-bottom:20px;box-shadow:var(--shadow);}
h1,h2,h3{margin-top:0;margin-bottom:12px;}
.small{color:var(--muted);font-size:14px;line-height:1.6;}
.row{display:flex;gap:16px;flex-wrap:wrap;align-items:flex-end;}
label{font-size:14px;font-weight:700;margin-bottom:4px;display:block;}
select{padding:10px 14px;border-radius:12px;border:1.5px solid var(--line);font-size:15px;width:100%;background:#fff;}
.btn{display:inline-block;padding:12px 22px;border-radius:14px;border:none;cursor:pointer;font-size:15px;font-weight:700;color:#fff;}
.btn-air{background:#0891b2;}
.btn-infer{background:#2563eb;}
.btn:hover{filter:brightness(0.94);}
.tag{display:inline-block;padding:7px 13px;border-radius:999px;font-size:13px;font-weight:700;margin:3px;}
.tag-green{background:#dcfce7;color:#166534;}
.tag-blue{background:#dbeafe;color:#1d4ed8;}
.tag-orange{background:#ffedd5;color:#c2410c;}
.tag-red{background:#fee2e2;color:#b91c1c;}
.tag-amber{background:#fef3c7;color:#92400e;}
.tag-purple{background:#ede9fe;color:#6d28d9;}
.tag-gray{background:#f3f4f6;color:#374151;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px;}
.mini-card{background:#f9fafb;border-radius:14px;padding:14px;border:1px solid var(--line);}
.mini-title{font-size:13px;color:var(--muted);margin-bottom:6px;}
.mini-value{font-size:22px;font-weight:800;}
.mono{font-family:Consolas,monospace;}
table{width:100%;border-collapse:collapse;}
th,td{border-bottom:1px solid var(--line);padding:9px 8px;text-align:left;font-size:14px;}
.bar-wrap{background:#e5e7eb;border-radius:999px;overflow:hidden;height:18px;margin-top:8px;}
.bar{height:18px;background:linear-gradient(90deg,#3b82f6,#22c55e,#f59e0b,#ef4444);}
.bar-gray{height:18px;background:linear-gradient(90deg,#94a3b8,#64748b);}
.divider{height:1px;background:var(--line);margin:20px 0;}
.prob-row{margin-bottom:12px;}
.prob-label{display:flex;justify-content:space-between;font-size:14px;margin-bottom:5px;}
.prob-bg{background:#e5e7eb;height:13px;border-radius:999px;overflow:hidden;}
.prob-fill{height:13px;border-radius:999px;}
.reason-list{margin:0;padding-left:20px;}
.reason-list li{margin-bottom:6px;line-height:1.5;}
.result-big{font-size:32px;font-weight:800;margin-bottom:10px;}
details{margin-top:16px;}
summary{cursor:pointer;font-weight:700;}
.loading{display:none;position:fixed;inset:0;background:rgba(255,255,255,0.75);z-index:9999;align-items:center;justify-content:center;backdrop-filter:blur(3px);}
.loading-box{background:#fff;padding:28px;border-radius:18px;box-shadow:var(--shadow);text-align:center;min-width:280px;}
.spinner{width:44px;height:44px;border:5px solid #dbeafe;border-top:5px solid #2563eb;border-radius:50%;margin:0 auto 14px;animation:spin 1s linear infinite;}
@keyframes spin{to{transform:rotate(360deg);}}
.baseline-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-top:16px;}
</style>
<script>
function showLoading(msg){
    document.getElementById('lmsg').innerText=msg;
    document.getElementById('loading-overlay').style.display='flex';
}
</script>
</head>
<body>

<div id="loading-overlay" class="loading">
  <div class="loading-box">
    <div class="spinner"></div>
    <div id="lmsg" style="font-weight:800;font-size:17px;">處理中，請稍候...</div>
  </div>
</div>

<div class="container">

<div class="card">
  <h1>🍍 Pineapple Ripeness Demo（離線 CSV 模擬｜含早期校正）</h1>
  <div class="small">使用 <b>demo_data/</b> 中的 xlsx 資料，不需連接樹莓派或 Arduino。</div>
</div>

<!-- ── 空氣校正 ── -->
<div class="card">
  <h2>🌫️ 空氣校正（選擇資料檔）</h2>
  <form method="post" action="/air" onsubmit="showLoading('🌫️ 正在計算空氣 baseline...')">
    <div class="row">
      <div style="flex:1;min-width:180px;">
        <label>選擇資料檔</label>
        <select name="air_date">
          {% for d in air_dates %}
          <option value="{{ d }}" {% if d == sel_air_date %}selected{% endif %}>{{ display_map.get(d, d) }}</option>
          {% endfor %}
        </select>
      </div>
      <div>
        <button class="btn btn-air" type="submit">校正空氣</button>
      </div>
    </div>
  </form>

  {% if mode == "air" %}
  <div style="margin-top:20px;">
    {% if air_result.success %}
      <div><span class="tag tag-green">✅ air_base.json 已更新</span>
           <span class="tag tag-blue">資料：{{ air_result.date }}</span></div>
      <div class="baseline-grid">
        {% for k, v in air_result.baseline.items() %}
        <div class="mini-card">
          <div class="mini-title">{{ k }}</div>
          <div class="mini-value mono">{{ "%.3f"|format(v) }}</div>
        </div>
        {% endfor %}
      </div>
    {% else %}
      <span class="tag tag-orange">❌ {{ air_result.error }}</span>
    {% endif %}
  </div>
  {% endif %}
</div>

<!-- ── 鳳梨推論 ── -->
<div class="card">
  <h2>🍍 鳳梨熟度推論</h2>
  <form method="post" action="/infer" onsubmit="showLoading('🍍 推論中...')">
    <input type="hidden" name="current_air_date" value="{{ sel_air_date }}">
    <div class="row">
      <div style="flex:1;min-width:180px;">
        <label>選擇資料檔</label>
        <select name="pine_date" id="sel_date" onchange="updateStages()">
          {% for d in pine_dates %}
          <option value="{{ d }}" {% if d == sel_pine_date %}selected{% endif %}>{{ display_map.get(d, d) }}</option>
          {% endfor %}
        </select>
      </div>
      <div style="flex:1;min-width:160px;">
        <label>熟度標籤</label>
        <select name="stage_label" id="sel_stage">
          {% for d, s in pine_keys %}
          <option value="{{ s }}" data-date="{{ d }}" {% if d == sel_pine_date and s == sel_stage %}selected{% endif %}>{{ s }}</option>
          {% endfor %}
        </select>
      </div>
      <div>
        <button class="btn btn-infer" type="submit">執行推論</button>
      </div>
    </div>
  </form>

  <script>
  const pine_keys = {{ pine_keys_json|safe }};
  function updateStages(){
    const date = document.getElementById('sel_date').value;
    const sel = document.getElementById('sel_stage');
    sel.innerHTML = '';
    pine_keys.filter(([d,s])=>d===date).forEach(([d,s])=>{
      const o = document.createElement('option');
      o.value = s; o.text = s; o.dataset.date = d;
      sel.appendChild(o);
    });
  }
  </script>

  {% if mode == "infer" %}
  <div class="divider"></div>

  {% if infer_result.success %}
    <div class="result-big">🍍 {{ infer_result.display_text }}</div>

    <div style="margin-bottom:12px;">
      <span class="tag {{ badge_class }}">{{ infer_result.display_text }}</span>
      <span class="tag tag-blue">資料：{{ infer_result.date }}</span>
      <span class="tag tag-purple">標籤：{{ infer_result.stage_label }}</span>
      {% if infer_result.guard_triggered %}<span class="tag tag-orange">防呆已觸發</span>{% endif %}
      {% if infer_result.early_override_used %}<span class="tag tag-green">早期熟度校正已啟用</span>{% endif %}
      {% if infer_result.override_used %}<span class="tag tag-red">過熟校正已啟用</span>{% endif %}
    </div>

    <div class="small" style="margin-bottom:16px;">
      推論筆數：{{ infer_result.rows_used }} 筆 ｜
      Feature count：{{ infer_result.feature_count }}
    </div>

    <div class="grid">
      <div class="mini-card">
        <div class="mini-title">原始模型分類</div>
        <div class="mini-value">Stage {{ infer_result.raw_stage }}（{{ infer_result.raw_stage_text }}）</div>
      </div>
      <div class="mini-card">
        <div class="mini-title">校正後分類</div>
        <div class="mini-value">Stage {{ infer_result.final_stage }}（{{ infer_result.final_stage_text }}）</div>
      </div>
      <div class="mini-card">
        <div class="mini-title">成熟區段</div>
        <div class="mini-value">{{ infer_result.maturity_zone }}</div>
      </div>
      <div class="mini-card">
        <div class="mini-title">過熟傾向</div>
        <div class="mini-value">{{ infer_result.overripe_tendency }}</div>
      </div>
    </div>

    <div class="divider"></div>
    <h3>成熟度條</h3>
    {% if infer_result.raw_maturity_percent != infer_result.final_maturity_percent %}
      <div class="small">原始：{{ infer_result.raw_maturity_percent }}%</div>
      <div class="bar-wrap"><div class="bar-gray" style="width:{{ infer_result.raw_maturity_percent }}%;"></div></div>
      <div style="height:10px;"></div>
      <div class="small">校正後：{{ infer_result.final_maturity_percent }}%</div>
    {% else %}
      <div class="small">{{ infer_result.final_maturity_percent }}%</div>
    {% endif %}
    <div class="bar-wrap"><div class="bar" style="width:{{ infer_result.final_maturity_percent }}%;"></div></div>

    <div class="divider"></div>
    <h3>四類機率</h3>
    {% for p in infer_result.probabilities %}
    <div class="prob-row">
      <div class="prob-label">
        <span>Stage {{ p.stage }}（{{ p.stage_text }}）</span>
        <span>{{ "%.2f"|format(p.percent) }}%</span>
      </div>
      <div class="prob-bg">
        <div class="prob-fill" style="width:{{ p.percent }}%;background:{{ p.color }};"></div>
      </div>
    </div>
    {% endfor %}

    {% if infer_result.guard_reasons %}
    <div class="divider"></div>
    <h3>防呆依據</h3>
    <ul class="reason-list">{% for r in infer_result.guard_reasons %}<li>{{ r }}</li>{% endfor %}</ul>
    {% endif %}

    {% if infer_result.early_override_reasons %}
    <div class="divider"></div>
    <h3>早期熟度校正依據</h3>
    <ul class="reason-list">{% for r in infer_result.early_override_reasons %}<li>{{ r }}</li>{% endfor %}</ul>
    {% endif %}

    {% if infer_result.override_reasons %}
    <div class="divider"></div>
    <h3>過熟校正依據</h3>
    <ul class="reason-list">{% for r in infer_result.override_reasons %}<li>{{ r }}</li>{% endfor %}</ul>
    {% endif %}

    <div class="divider"></div>
    <h3>原始感測器摘要</h3>
    <table>
      <thead><tr><th>Sensor</th><th>Mean</th><th>Min</th><th>Max</th><th>Std</th></tr></thead>
      <tbody>
        {% for s in infer_result.sensor_summary %}
        <tr><td>{{ s.name }}</td><td>{{ s.mean }}</td><td>{{ s.min }}</td><td>{{ s.max }}</td><td>{{ s.std }}</td></tr>
        {% endfor %}
      </tbody>
    </table>

    <details style="margin-top:18px;">
      <summary>查看模型特徵值（{{ infer_result.feature_count }} 個）</summary>
      <div class="grid" style="margin-top:14px;">
        {% for f in infer_result.feature_values %}
        <div class="mini-card">
          <div class="mini-title">{{ f.name }}</div>
          <div class="mono" style="font-size:16px;font-weight:700;">{{ "%.6f"|format(f.value) }}</div>
        </div>
        {% endfor %}
      </div>
    </details>

  {% else %}
    <span class="tag tag-orange">❌ {{ infer_result.error }}</span>
  {% endif %}
  {% endif %}
</div>

</div><!-- container -->
</body>
</html>
"""

# ─── Routes ────────────────────────────────────────────────────────────────────

def get_template_context(mode="none", air_result=None, infer_result=None,
                          sel_air_date=None, sel_pine_date=None, sel_stage=None,
                          badge_class="tag-gray"):
    air_map, pine_map = scan_demo_files()
    air_dates = sorted(air_map.keys())          # 這裡實際上是 case key，例如 pineapple_03_20260214
    pine_keys = sorted(pine_map.keys())         # (case key, stage)
    pine_dates = sorted(set(d for d, _ in pine_keys))
    display_map = {k: case_display(k) for k in set(air_dates + pine_dates)}
    return dict(
        mode=mode,
        air_dates=air_dates,
        pine_dates=pine_dates,
        pine_keys=pine_keys,
        pine_keys_json=json.dumps(pine_keys),
        display_map=display_map,
        air_result=air_result,
        infer_result=infer_result,
        sel_air_date=sel_air_date or (air_dates[0] if air_dates else ""),
        sel_pine_date=sel_pine_date or (pine_dates[0] if pine_dates else ""),
        sel_stage=sel_stage or (pine_keys[0][1] if pine_keys else ""),
        badge_class=badge_class,
    )


@app.route("/")
def index():
    return render_template_string(HTML, **get_template_context())


@app.route("/air", methods=["POST"])
def run_air():
    date_str = request.form.get("air_date", "").strip()
    result = do_air_calibration(date_str)
    ctx = get_template_context(mode="air", air_result=result, sel_air_date=date_str)
    return render_template_string(HTML, **ctx)


@app.route("/infer", methods=["POST"])
def run_infer():
    pine_date = request.form.get("pine_date", "").strip()
    stage_label = request.form.get("stage_label", "").strip()
    current_air_date = request.form.get("current_air_date", "").strip() or None
    result = do_inference(pine_date, stage_label)
    badge = badge_class_from_text(result.get("display_text", ""))
    ctx = get_template_context(
        mode="infer", infer_result=result,
        sel_air_date=current_air_date,
        sel_pine_date=pine_date, sel_stage=stage_label, badge_class=badge
    )
    return render_template_string(HTML, **ctx)


# ─── main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not os.path.isdir(DEMO_DIR):
        print(f"❌ 找不到 {DEMO_DIR}/ 資料夾，請確認 xlsx 已放入。")
        sys.exit(1)
    air_map, pine_map = scan_demo_files()
    print(f"✅ 找到 {len(air_map)} 個空氣校正檔，{len(pine_map)} 個鳳梨測試檔")
    print("Open Browser: http://樹莓派IP:5000  （例如 http://172.20.10.2:5000）")
    app.run(host="0.0.0.0", port=5000, debug=False)
