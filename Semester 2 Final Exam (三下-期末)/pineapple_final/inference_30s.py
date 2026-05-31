# 匯入需要用到的套件：參數解析、檔案搜尋、JSON、模型讀取、正規表示式、時間控制等等
import argparse
import glob
import json
import os
import pickle
import re
import sys
import time

# 匯入數值運算和 Arduino Serial 通訊需要的套件
import numpy as np
import serial

# ============================================================
# 基本參數設定
# ============================================================
# 每次推論使用 30 秒的資料窗口
WINDOW = 30

# Arduino Serial baud rate，要和 Arduino 程式設定一致
BAUD = 115200

# Demo 模式的資料夾名稱，裡面放以前存好的 xlsx 感測資料
DEMO_DIR = "demo_data"

# 模型目前使用的五個氣體感測器
SENSORS = ["MQ2", "MQ3", "MQ9", "MQ135", "TGS2602"]

# 成熟度 stage 對應的中文名稱，後面印結果會用到
STAGE_TEXT = {0: "未熟", 1: "初熟", 2: "成熟", 3: "過熟"}


# 自動尋找 Arduino 的序列埠，通常會是 /dev/ttyACM0 或 /dev/ttyUSB0
def auto_detect_port():
    ports = sorted(glob.glob("/dev/ttyACM*")) + sorted(glob.glob("/dev/ttyUSB*"))
    if not ports:
        raise RuntimeError("❌ 找不到 Arduino (/dev/ttyACM* 或 /dev/ttyUSB*)")
    return ports[0]


# 安全計算比值，分母加一個很小的數，避免除以 0
def safe_ratio(a, b):
    return float(a) / (float(b) + 1e-9)


# 安全計算兩組資料的相關係數，資料太少或計算失敗就回傳 0
def safe_corr(x, y):
    if len(x) < 2 or len(y) < 2:
        return 0.0
    try:
        c = np.corrcoef(x, y)[0, 1]
        return float(c) if np.isfinite(c) else 0.0
    except Exception:
        return 0.0


# 計算一段感測資料的斜率，用來看氣體訊號是上升還是下降
def safe_slope(x):
    if len(x) < 2:
        return 0.0
    try:
        return float(np.polyfit(range(len(x)), x, 1)[0])
    except Exception:
        return 0.0


# 計算相鄰資料差值的平均，觀察訊號變化速度
def safe_mean_diff(x):
    if len(x) < 2:
        return 0.0
    try:
        d = np.diff(x)
        return float(np.mean(d)) if len(d) > 0 else 0.0
    except Exception:
        return 0.0


# 計算曲線下面積 AUC，代表這段時間內訊號的累積量
def safe_auc(x):
    try:
        if hasattr(np, "trapezoid"):
            return float(np.trapezoid(x))
        return float(np.trapz(x))
    except Exception:
        return 0.0


# 印出推論窗口內的原始感測器摘要，方便確認資料有沒有正常
def print_sensor_summary(data):
    print("\n" + "=" * 60)
    print("📊 Raw sensor summary (inference window)")
    print("=" * 60)
    for s in SENSORS:
        arr = data[s]
        print(f"{s:8s} | mean={np.mean(arr):8.3f} | min={np.min(arr):8.3f} | max={np.max(arr):8.3f} | std={np.std(arr):8.3f}")


# 印出實際送進模型的特徵值，之後 debug 或報告展示會比較清楚
def print_feature_summary(features_order, feat):
    print("\n" + "=" * 60)
    print("🧪 Feature values used by model")
    print("=" * 60)
    for f in features_order:
        print(f"{f:28s} = {feat.get(f, 0.0):.6f}")


# 用四個 stage 的機率算出 0~100 的成熟度百分比
def build_raw_maturity_percent(proba):
    score = (proba[0] * 0 + proba[1] * 1 + proba[2] * 2 + proba[3] * 3) / 3.0
    return int(round(score * 100))


# 把百分比轉成文字版進度條，讓終端機輸出比較直覺
def build_bar(percent):
    blocks = int(round(percent / 5))
    blocks = max(0, min(20, blocks))
    return "█" * blocks + "░" * (20 - blocks)


# 根據成熟度百分比轉成區段文字
def maturity_zone_text(percent):
    if percent <= 16:
        return "未熟區"
    elif percent <= 49:
        return "初熟區"
    elif percent <= 82:
        return "成熟區"
    else:
        return "過熟區"


# 根據 Stage 3 的機率，顯示過熟傾向程度
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


# 如果第一高和第二高的 stage 很接近，就顯示「接近某階段」
def get_closest_stage_text(proba, pred):
    sorted_idx = np.argsort(proba)[::-1]
    top1 = int(sorted_idx[0])
    top2 = int(sorted_idx[1])
    if abs(top1 - top2) == 1 and proba[top2] >= 0.15:
        return f"{STAGE_TEXT[top1]}（接近{STAGE_TEXT[top2]}）"
    return STAGE_TEXT[top1]


# 依照模型機率和 meta 設定，產生最後要顯示給使用者看的文字
def get_display_text_from_meta(proba, pred, meta):
    if len(proba) >= 4:
        sorted_idx = np.argsort(proba)[::-1]
        top1 = int(sorted_idx[0])
        p3 = float(proba[3])
        if top1 == 2 and p3 >= 0.18:
            return "成熟，明顯接近過熟"
        elif top1 == 2 and p3 >= 0.08:
            return "成熟，但已有過熟傾向"

    policy = meta.get("display_policy", {}) if isinstance(meta, dict) else {}
    mode = policy.get("mode", "base")
    if mode == "base":
        return get_closest_stage_text(proba, pred)
    if mode == "s3_sensitive":
        rule = policy.get("rule", {})
        trigger_pred_stage = int(rule.get("trigger_pred_stage", 2))
        s3_min_proba = float(rule.get("s3_min_proba", 0.08))
        s2s3_min_sum = float(rule.get("s2s3_min_sum", 0.66))
        custom_text = rule.get("display_text", "成熟，但已有過熟傾向")
        if pred == trigger_pred_stage and len(proba) >= 4 and float(proba[3]) >= s3_min_proba and float(proba[2] + proba[3]) >= s2s3_min_sum:
            return custom_text
        return get_closest_stage_text(proba, pred)
    return get_closest_stage_text(proba, pred)


# 印出四個成熟度類別的機率，讓使用者知道模型是怎麼判斷的
def print_probabilities(proba):
    print("\n" + "=" * 60)
    print("📈 詳細機率")
    print("=" * 60)
    for i, p in enumerate(proba):
        print(f"Stage {i}（{STAGE_TEXT[i]}）: {p:.4f} ({p*100:.2f}%)")
    print("-" * 60)
    sorted_idx = np.argsort(proba)[::-1]
    top1 = int(sorted_idx[0])
    top2 = int(sorted_idx[1])
    gap = float(proba[top1] - proba[top2])
    print(f"Top-1: Stage {top1}（{STAGE_TEXT[top1]}）")
    print(f"Top-2: Stage {top2}（{STAGE_TEXT[top2]}）")
    print(f"Probability gap = {gap:.4f}")
    if gap < 0.10:
        print("⚠️ 這是一個邊界案例，前兩類非常接近")
    elif gap < 0.20:
        print("ℹ️ 這顆鳳梨有一點接近次高類別")
    else:
        print("✅ 這次預測相對明確")


# 空氣/無樣本防呆，避免只有空氣時也被系統誤判成熟度
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
    return (baseline_hits == 3 and weak_signal_hits >= 2), reasons


# 早期熟度校正：避免未熟/初熟 demo 與實測樣本被原始模型拉成成熟
def early_stage_override(pred, proba, feat):
    """早期熟度校正：避免未熟/初熟 demo 與實測樣本被原始模型拉成成熟。"""
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

    unripe_low_sensor = (
        p2 <= 0.70 and p3 <= 0.13 and
        tgs2602_min_norm < 0.94 and mq2_mean_norm < 1.00 and mq9_min_norm < 0.97
    )

    unripe_flat_signal = (
        p2 <= 0.50 and p3 <= 0.12 and early_prob_mass >= 0.35 and
        mq3_std_norm <= 0.0015 and mq3_range_norm <= 0.0025
    )

    early_ripe_signal = (
        p2 <= 0.88 and p3 <= 0.10 and
        0.94 <= tgs2602_min_norm < 1.02 and mq2_mean_norm < 1.02 and mq9_min_norm < 0.98 and
        mq3_std_norm < 0.0065 and mq3_range_norm < 0.0080 and mq3_mq135_ratio > 2.00
    )

    boundary_early_ripe = (
        p2 <= 0.60 and p3 <= 0.14 and p1 >= 0.18 and early_prob_mass >= 0.35 and mq3_mq135_ratio > 1.70
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


# 早期校正後，重新計算適合顯示的成熟度百分比
def build_early_display_percent(final_pred, feat):
    tgs = float(feat.get("TGS2602_min_norm", 1.0))
    mq2 = float(feat.get("MQ2_mean_norm", 1.0))
    mq9 = float(feat.get("MQ9_min_norm", 1.0))

    if int(final_pred) == 0:
        strength = np.clip((tgs - 0.90) / 0.05, 0.0, 1.0)
        return int(round(15 + 10 * strength))
    if int(final_pred) == 1:
        strength = np.clip(((tgs - 0.95) / 0.05 + (1.0 - abs(mq2 - 1.0)) + (1.0 - abs(mq9 - 1.0))) / 3.0, 0.0, 1.0)
        return int(round(35 + 13 * strength))
    return None


# 過熟校正：如果模型原本判成熟，但過熟訊號很明顯，就可能校正為過熟
def overripe_override(pred, proba, feat):
    """過熟校正 v2：避免早期訊號還很高時被 soft rule 拉成過熟。"""
    reasons = []
    if int(pred) != 2:
        return pred, False, reasons

    p0, p1, p2, p3 = [float(proba[i]) for i in range(4)]
    mq3_mq135_ratio = float(feat.get("MQ3_MQ135_ratio", 0.0))
    tgs2602_min_norm = float(feat.get("TGS2602_min_norm", 0.0))
    mq2_mean_norm = float(feat.get("MQ2_mean_norm", 999.0))
    early_mass = p0 + p1

    if early_mass >= 0.30 and p2 <= 0.60:
        return pred, False, [f"早期機率 Stage0+Stage1={early_mass:.4f} 且 Stage2={p2:.4f} 不高，暫不啟用過熟校正"]

    strong = p3 >= 0.14 and p2 >= 0.60 and tgs2602_min_norm >= 1.05 and mq3_mq135_ratio >= 2.08
    normal = p3 >= 0.15 and p2 >= 0.60 and mq3_mq135_ratio >= 2.00 and mq2_mean_norm <= 1.02
    soft = p3 >= 0.15 and p2 >= 0.65 and mq3_mq135_ratio >= 2.00

    if strong:
        reasons.append(f"強條件：Stage3={p3:.4f}, Stage2={p2:.4f}, TGS2602={tgs2602_min_norm:.4f}, ratio={mq3_mq135_ratio:.4f}")
    elif normal:
        reasons.append(f"一般條件：Stage3={p3:.4f}, Stage2={p2:.4f}, ratio={mq3_mq135_ratio:.4f}, MQ2={mq2_mean_norm:.4f}")
    elif soft:
        reasons.append(f"軟條件：Stage3={p3:.4f}, Stage2={p2:.4f}, ratio={mq3_mq135_ratio:.4f}")

    if strong or normal or soft:
        return 3, True, reasons
    return pred, False, reasons


# 如果啟用過熟校正，會把成熟度條提高到過熟區間；沒啟用就保留原始百分比
def build_final_display_percent(raw_percent, final_pred, override_used, proba, feat):
    if not override_used or final_pred != 3:
        return raw_percent
    p3 = float(proba[3])
    tgs = float(feat.get("TGS2602_min_norm", 1.0))
    ratio = float(feat.get("MQ3_MQ135_ratio", 1.0))
    p3_score = np.clip((p3 - 0.08) / 0.22, 0.0, 1.0)
    tgs_score = np.clip((tgs - 0.970) / 0.165, 0.0, 1.0)
    ratio_score = np.clip((ratio - 2.00) / 0.18, 0.0, 1.0)
    override_strength = (p3_score + tgs_score + ratio_score) / 3.0
    override_percent = int(round(83 + 17 * override_strength))
    override_percent = max(83, min(100, override_percent))
    return max(raw_percent, override_percent)


# 將 Arduino 傳來的一列資料轉成模型需要的五個感測器數值
def parse_sensor_row(row_dict):
    try:
        return {"MQ2": float(row_dict["MQ2_raw"]), "MQ3": float(row_dict["MQ3_raw"]), "MQ9": float(row_dict["MQ9_raw"]), "MQ135": float(row_dict["MQ135_raw"]), "TGS2602": float(row_dict["TGS2602_raw"])}
    except Exception:
        return None


# 取得 air baseline 裡的基準值，如果資料不正常就用 1.0 防止錯誤
def base_value(air, sensor_name):
    v = air.get(sensor_name, 1.0)
    if v is None or not np.isfinite(v) or v == 0:
        return 1.0
    return float(v)


# 根據 30 秒原始感測資料和 air baseline，建立模型需要的特徵
def build_features(rows, air):
    data = {s: np.array([r[s] for r in rows], dtype=float) for s in SENSORS}
    feat = {}
    feat["MQ2_MQ3_ratio"] = safe_ratio(np.mean(data["MQ2"]), np.mean(data["MQ3"]))
    feat["MQ3_MQ135_ratio"] = safe_ratio(np.mean(data["MQ3"]), np.mean(data["MQ135"]))
    feat["MQ3_TGS2602_ratio"] = safe_ratio(np.mean(data["MQ3"]), np.mean(data["TGS2602"]))
    feat["MQ3_MQ135_correlation"] = safe_corr(data["MQ3"], data["MQ135"])
    feat["MQ2_auc_norm"] = safe_auc(data["MQ2"]) / (len(data["MQ2"]) * base_value(air, "MQ2"))
    feat["MQ2_mean_norm"] = np.mean(data["MQ2"]) / base_value(air, "MQ2")
    feat["MQ3_range_norm"] = (np.max(data["MQ3"]) - np.min(data["MQ3"])) / base_value(air, "MQ3")
    feat["MQ3_max_norm"] = np.max(data["MQ3"]) / base_value(air, "MQ3")
    feat["MQ3_std_norm"] = np.std(data["MQ3"]) / base_value(air, "MQ3")
    feat["MQ9_slope"] = safe_slope(data["MQ9"])
    feat["MQ9_min_norm"] = np.min(data["MQ9"]) / base_value(air, "MQ9")
    feat["MQ9_delta_mean"] = safe_mean_diff(data["MQ9"])
    feat["TGS2602_min_norm"] = np.min(data["TGS2602"]) / base_value(air, "TGS2602")
    feat["TGS2602_delta_std"] = np.std(np.diff(data["TGS2602"])) if len(data["TGS2602"]) >= 2 else 0.0
    feat["TGS2602_std_norm"] = np.std(data["TGS2602"]) / base_value(air, "TGS2602")
    return feat, data


# 將鳳梨編號和日期整理成 demo 檔案使用的 case key 格式
def normalize_case(pid: str, date: str) -> str:
    pid = str(pid).strip().replace("pineapple_", "")
    return f"pineapple_{pid}_{date}"


# Demo 模式用：讀取 xlsx 檔案，找到 timestamp_ms 這一列作為資料表 header
def load_xlsx_sensor_df(path: str):
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


# 掃描 demo_data 資料夾內所有鳳梨樣本 xlsx，排除 air 校正檔
def scan_pineapple_files(demo_dir=DEMO_DIR):
    pattern = os.path.join(demo_dir, "pineapple_*.xlsx")
    result = {}
    for f in sorted(glob.glob(pattern)):
        base = os.path.basename(f)
        if "_air.xlsx" in base:
            continue
        m = re.search(r"^(pineapple_\w+_\d{8})_(.+)\.xlsx$", base)
        if m:
            result[(m.group(1), m.group(2))] = f
    return result


# Demo 模式：從 xlsx 讀取鳳梨資料，不讀 Arduino 即時 Serial
def collect_rows_from_demo(args):
    pine_files = scan_pineapple_files(args.demo_dir)
    if not pine_files:
        raise RuntimeError(f"在 {args.demo_dir}/ 找不到任何鳳梨 xlsx")

    keys = sorted(pine_files.keys())
    case_key = args.demo_case
    if not case_key and args.pid and args.date:
        case_key = normalize_case(args.pid, args.date)

    if case_key:
        candidates = [(c, s) for (c, s) in keys if c == case_key]
        if args.demo_stage:
            candidates = [(c, s) for (c, s) in candidates if s == args.demo_stage]
        if not candidates:
            print(f"❌ 找不到 {case_key} / {args.demo_stage or ''} 的鳳梨資料")
            print("可用資料：")
            for c, s in keys:
                print(f" - {c} / {s}")
            sys.exit(1)
        if len(candidates) > 1:
            print("同 case 有多個熟度，請選擇：")
            for idx, (c, s) in enumerate(candidates):
                print(f"  [{idx}] {c}  {s}")
            key = candidates[int(input("請輸入編號：").strip())]
        else:
            key = candidates[0]
    else:
        print("可用鳳梨測試檔案：")
        for idx, (c, s) in enumerate(keys):
            print(f"  [{idx}] {c}  {s}  ({pine_files[(c, s)]})")
        key = keys[int(input("請輸入編號：").strip())]

    case_key, stage_label = key
    path = pine_files[key]
    print(f"Demo mode: 使用歷史鳳梨資料，不讀取 Arduino 即時 Serial")
    print(f"Demo case: {case_key}")
    print(f"Demo label: {stage_label}")
    print(f"Pineapple file: {path}")

    df = load_xlsx_sensor_df(path)
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
        raise RuntimeError("推論窗口沒有有效 demo 感測資料")

    print(f"Total demo rows = {len(df)}")
    print(f"Rows used for inference = {len(rows)} (first {WINDOW} rows)")
    return rows, case_key, stage_label


# 實測模式：從 Arduino Serial 收集資料，並取最後 30 秒做模型推論
def collect_rows_from_serial(args):
    WARMUP_SEC = max(0, int(args.warmup_sec))
    TOTAL_SEC = WARMUP_SEC + WINDOW
    print(f"Warmup sec: {WARMUP_SEC}")
    print(f"Collect mode: collect total {TOTAL_SEC} sec, use last {WINDOW} sec for inference")

    port = args.port or auto_detect_port()
    print("Arduino port:", port)
    ser = serial.Serial(port, BAUD, timeout=1)
    time.sleep(2)
    ser.reset_input_buffer()

    header = None
    print("等待 CSV header ...")
    while True:
        line = ser.readline().decode("utf-8", errors="ignore").strip()
        if not line:
            continue
        if line.startswith("timestamp_ms,"):
            header = [x.strip() for x in line.split(",")]
            print("CSV header detected")
            break

    all_rows = []
    t0 = time.time()
    last_print_sec = -1
    if WARMUP_SEC > 0:
        print(f"開始前置累積 {WARMUP_SEC} 秒，之後取最後 {WINDOW} 秒做推論...")
    else:
        print(f"直接收集 {WINDOW} 秒做推論...")

    while time.time() - t0 < TOTAL_SEC:
        line = ser.readline().decode("utf-8", errors="ignore").strip()
        if not line:
            continue
        if line.startswith(("#", "✅", "❌", "📋", "⏱", "🍍", "===")):
            continue
        vals = [x.strip() for x in line.split(",")]
        if len(vals) != len(header):
            continue
        row = dict(zip(header, vals))
        parsed = parse_sensor_row(row)
        if parsed is None:
            continue
        all_rows.append(parsed)
        elapsed = int(time.time() - t0)
        if elapsed != last_print_sec:
            last_print_sec = elapsed
            if elapsed < WARMUP_SEC:
                print(f"Warmup {elapsed}/{WARMUP_SEC} sec | total_rows={len(all_rows)}", end="\r")
            else:
                infer_elapsed = max(0, min(WINDOW, elapsed - WARMUP_SEC))
                print(f"Collecting inference window {infer_elapsed}/{WINDOW} sec | total_rows={len(all_rows)}", end="\r")
    print()

    if not all_rows:
        raise RuntimeError("❌ 沒有收集到任何有效感測資料")
    rows = all_rows[-WINDOW:] if len(all_rows) > WINDOW else all_rows
    print(f"Total collected rows = {len(all_rows)}")
    print(f"Rows used for inference = {len(rows)} (last window)")
    if not rows:
        raise RuntimeError("❌ 推論窗口沒有有效資料")
    return rows, None, None


# 讀取 JSON 檔，如果沒有檔案就回傳空字典，避免程式直接中斷
def load_json_or_empty(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


# 主程式：負責解析參數、收集資料、載入模型、建立特徵、推論和輸出結果
def main():
    # 建立命令列參數，讓使用者可以選擇實測模式、Demo 模式、模型檔案等
    parser = argparse.ArgumentParser()
    parser.add_argument("--warmup-sec", type=int, default=0, help="前置累積秒數")
    parser.add_argument("--port", type=str, default=None, help="指定 Arduino port，例如 /dev/ttyACM0")
    parser.add_argument("--air", type=str, default="air_base.json", help="air baseline JSON 路徑")
    parser.add_argument("--model", type=str, default="deploy_student.pkl")
    parser.add_argument("--features", type=str, default="feature_columns.json")
    parser.add_argument("--meta", type=str, default="deploy_meta.json")
    parser.add_argument("--demo", action="store_true", help="使用 demo_data/*.xlsx，不讀取 Arduino")
    parser.add_argument("--demo-dir", type=str, default=DEMO_DIR, help="demo xlsx 資料夾")
    parser.add_argument("--demo-case", "--case", dest="demo_case", type=str, default=None, help="例如 pineapple_03_20260214")
    parser.add_argument("--demo-stage", "--stage", dest="demo_stage", type=str, default=None, help="熟度標籤，例如 未熟 / 初熟 / 成熟 / 過熟")
    parser.add_argument("--pid", type=str, default=None, help="鳳梨編號，例如 03")
    parser.add_argument("--date", type=str, default=None, help="日期，例如 20260214")
    args = parser.parse_args()

    print("🍍 Pineapple ripeness detection (30 sec mode)")
    # 如果有 demo 相關參數，就走 Demo xlsx 模式；否則就讀 Arduino 即時資料
    if args.demo or args.demo_case or args.demo_stage or (args.pid and args.date):
        print("Mode: DEMO xlsx mode")
        print("Warmup sec: 0")
        print(f"Collect mode: use first {WINDOW} rows for inference")
        rows, demo_case, demo_stage = collect_rows_from_demo(args)
    else:
        print("Mode: REAL Arduino Serial mode")
        rows, demo_case, demo_stage = collect_rows_from_serial(args)

    # 載入訓練好的模型檔案
    with open(args.model, "rb") as f:
        model = pickle.load(f)

    # 載入模型需要的特徵欄位順序，順序要和訓練時一致
    with open(args.features, "r", encoding="utf-8") as f:
        feature_columns = json.load(f)

    # 載入模型相關設定，例如 target window、顯示規則等等
    meta = load_json_or_empty(args.meta)

    # 載入 air baseline，後面做特徵正規化會用到
    with open(args.air, "r", encoding="utf-8") as f:
        air = json.load(f)

    print("Model loaded")
    print(f"Feature count: {len(feature_columns)}")
    print(f"Target window: {meta.get('target_window_sec', WINDOW) if isinstance(meta, dict) else WINDOW} sec")
    print(f"Air baseline loaded from {args.air}")

    # 將原始資料轉成模型特徵，並印出摘要方便檢查
    feat, data = build_features(rows, air)
    print_sensor_summary(data)
    print_feature_summary(feature_columns, feat)

    # 按照 feature_columns 的順序組成模型輸入 X
    X = np.array([feat.get(f, 0.0) for f in feature_columns], dtype=float).reshape(1, -1)

    # 取得模型原始分類結果
    raw_pred = int(model.predict(X)[0])

    # 如果模型有 predict_proba，就輸出四類機率；沒有的話就只給預測類別 100%
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(X)[0]
    else:
        proba = np.zeros(4, dtype=float)
        proba[raw_pred] = 1.0

    print_probabilities(proba)

    # 防呆檢查：判斷是否像空氣或沒有有效鳳梨訊號
    guard_triggered, guard_reasons = air_or_no_sample_guard(feat, proba=proba)
    display_text = get_display_text_from_meta(proba, raw_pred, meta)

    # 先做早期熟度校正，避免未熟/初熟被誤判為成熟
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
        # 如果沒有啟用早期校正，再檢查是否需要過熟校正
        final_pred, override_used, override_reasons = overripe_override(raw_pred, proba, feat)
        if override_used:
            display_text = "過熟"

    # 計算原始與最後顯示用的成熟度百分比
    raw_maturity_percent = build_raw_maturity_percent(proba)
    if early_override_used:
        final_maturity_percent = build_early_display_percent(final_pred, feat)
        if final_maturity_percent is None:
            final_maturity_percent = raw_maturity_percent
    else:
        final_maturity_percent = build_final_display_percent(raw_maturity_percent, final_pred, override_used, proba, feat)

    final_maturity_bar = build_bar(final_maturity_percent)
    zone_text = maturity_zone_text(final_maturity_percent)
    overripe_text = overripe_tendency_text(proba[3])

    # 最後整理並印出結果，Flask 網頁會解析這些文字
    print("\n" + "=" * 60)
    print("🍍 結果")
    print("=" * 60)
    if demo_case:
        print(f"【模擬模式】日期：{demo_case}  標籤：{demo_stage}")

    if guard_triggered:
        print("成熟度判定：⚠️ 無有效鳳梨訊號")
        print(f"原始模型分類：Stage {raw_pred}（{STAGE_TEXT[raw_pred]}）")
        print("校正後分類：—")
        print(f"成熟度條：[ {build_bar(raw_maturity_percent)} ] {raw_maturity_percent}%")
        print(f"成熟區段：{maturity_zone_text(raw_maturity_percent)}")
        print(f"過熟傾向：{overripe_text}")
        print("空氣/無樣本防呆：✅ 已觸發")
        print("判定依據：")
        for r in guard_reasons:
            print(f" - {r}")
    else:
        print(f"成熟度判定：{display_text}")
        print(f"原始模型分類：Stage {raw_pred}（{STAGE_TEXT[raw_pred]}）")
        print(f"校正後分類：Stage {final_pred}（{STAGE_TEXT[final_pred]}）")
        if raw_maturity_percent != final_maturity_percent:
            print(f"原始成熟度條：[ {build_bar(raw_maturity_percent)} ] {raw_maturity_percent}%")
            print(f"校正後成熟度條：[ {final_maturity_bar} ] {final_maturity_percent}%")
        else:
            print(f"成熟度條：[ {final_maturity_bar} ] {final_maturity_percent}%")
        print(f"成熟區段：{zone_text}")
        print(f"過熟傾向：{overripe_text}")
        print("空氣/無樣本防呆：— 未觸發")

        if early_override_used:
            print("早期熟度校正：✅ 已啟用")
            print("早期校正依據：")
            for r in early_override_reasons:
                print(f" - {r}")
        else:
            print("早期熟度校正：— 未啟用")

        if override_used:
            print("過熟校正：✅ 已啟用")
            print("校正依據：")
            for r in override_reasons:
                print(f" - {r}")
        else:
            print("過熟校正：— 未啟用")

    print("=" * 60)
    print("Program finished")


# 只有直接執行這支檔案時，才會呼叫 main()
if __name__ == "__main__":
    main()
