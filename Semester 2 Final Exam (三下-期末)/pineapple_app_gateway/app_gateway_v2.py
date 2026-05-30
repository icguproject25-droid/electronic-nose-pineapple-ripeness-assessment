"""
app_gateway_v2.py
放在 Raspberry Pi 的 ~/pineapple_app_gateway/ 資料夾

API:
  GET  /health
  POST /calibrate
  POST /scan
  GET  /status
  POST /scan_records
"""

import glob
import json
import pickle
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path

import numpy as np
import serial
from flask import Flask, jsonify, request


# ─────────────────────────────────────────
# 路徑設定
# ─────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent

# 你的專案如果是 pineapple_final，請用這個
PINEAPPLE_DIR = BASE_DIR.parent / "pineapple_final"

# 如果你之後改回 ~/pineapple，就改成這行：
# PINEAPPLE_DIR = BASE_DIR.parent / "pineapple"

MODEL_PATH = PINEAPPLE_DIR / "deploy_student.pkl"
FEATURES_PATH = PINEAPPLE_DIR / "feature_columns.json"
META_PATH = PINEAPPLE_DIR / "deploy_meta.json"
AIR_BASE_PATH = PINEAPPLE_DIR / "air_base.json"
RECORDS_PATH = BASE_DIR / "scan_records.json"


# ─────────────────────────────────────────
# 常數
# ─────────────────────────────────────────
WINDOW = 30
BAUD = 115200

GAS_SENSORS = ["MQ2", "MQ3", "MQ9", "MQ135", "TGS2602"]
BME_KEYS = ["Temp_C", "Humidity_pct", "Pressure_hPa"]
CALIBRATION_KEYS = GAS_SENSORS + BME_KEYS

STAGE_ZH = {
    0: "未熟",
    1: "初熟",
    2: "成熟",
    3: "過熟",
}

STAGE_EN = {
    0: "unripe",
    1: "transition",
    2: "ripe",
    3: "overripe",
}

SUGGESTION = {
    0: "建議再等待 3-5 天，鳳梨尚未成熟。",
    1: "建議再等 1-2 天，風味會更佳。",
    2: "立即食用，現在風味最佳！",
    3: "請盡快食用，避免繼續過熟。",
}


# ─────────────────────────────────────────
# 全域狀態
# ─────────────────────────────────────────
_lock = threading.Lock()
_state = {
    "status": "idle",
    "progress": 0,
    "result": None,
    "error": None,
    "scan_id": None,
}


def _set_state(**kwargs):
    with _lock:
        _state.update(kwargs)


def _get_state():
    with _lock:
        return dict(_state)


# ─────────────────────────────────────────
# 模型快取
# ─────────────────────────────────────────
_model = None
_features = None
_meta = None


def _load_model():
    global _model, _features, _meta

    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"模型檔案不存在：{MODEL_PATH}")

    if not FEATURES_PATH.exists():
        raise FileNotFoundError(f"特徵欄位不存在：{FEATURES_PATH}")

    with open(MODEL_PATH, "rb") as f:
        _model = pickle.load(f)

    with open(FEATURES_PATH, "r", encoding="utf-8") as f:
        _features = json.load(f)

    if META_PATH.exists():
        with open(META_PATH, "r", encoding="utf-8") as f:
            _meta = json.load(f)
    else:
        _meta = {}

    print(f"[Model] 載入完成，特徵數：{len(_features)}")


# ─────────────────────────────────────────
# 工具函式
# ─────────────────────────────────────────
def _safe_float(value, default=None):
    try:
        if value is None:
            return default
        v = float(value)
        if not np.isfinite(v):
            return default
        return v
    except Exception:
        return default


def _read_arduino_row(row):
    parsed = {
        "MQ2": _safe_float(row.get("MQ2_raw")),
        "MQ3": _safe_float(row.get("MQ3_raw")),
        "MQ9": _safe_float(row.get("MQ9_raw")),
        "MQ135": _safe_float(row.get("MQ135_raw")),
        "TGS2602": _safe_float(row.get("TGS2602_raw")),
        "Temp_C": _safe_float(row.get("Temp_C")),
        "Humidity_pct": _safe_float(row.get("Humidity_pct")),
        "Pressure_hPa": _safe_float(row.get("Pressure_hPa")),
    }

    for key in GAS_SENSORS:
        if parsed[key] is None:
            return None

    return parsed


def _get_arduino_port():
    return "COM5"


def _open_serial_and_wait_header():
    port = _get_arduino_port()

    if not port:
        raise RuntimeError("找不到 Arduino，請確認 USB 連接")

    print(f"[Serial] 使用 port：{port}")

    ser = serial.Serial(port, BAUD, timeout=1)
    time.sleep(2)
#    ser.reset_input_buffer()

    header = None
    deadline = time.time() + 15

    while time.time() < deadline:
        line = ser.readline().decode("utf-8", errors="ignore").strip()

        if line.startswith("timestamp_ms,"):
            header = [x.strip() for x in line.split(",")]
            break

    if header is None:
        ser.close()
        raise RuntimeError("等不到 Arduino CSV header，請確認 use_this.ino 已燒錄")

    return ser, header, port


def _safe_ratio(a, b):
    return float(a) / (float(b) + 1e-9)


def _safe_corr(x, y):
    if len(x) < 2 or len(y) < 2:
        return 0.0
    try:
        c = np.corrcoef(x, y)[0, 1]
        return float(c) if np.isfinite(c) else 0.0
    except Exception:
        return 0.0


def _safe_slope(x):
    if len(x) < 2:
        return 0.0
    try:
        return float(np.polyfit(range(len(x)), x, 1)[0])
    except Exception:
        return 0.0


def _safe_mean_diff(x):
    if len(x) < 2:
        return 0.0
    try:
        d = np.diff(x)
        return float(np.mean(d)) if len(d) > 0 else 0.0
    except Exception:
        return 0.0


def _safe_auc(x):
    try:
        return float(np.trapz(x))
    except Exception:
        return 0.0


def _base_value(air, sensor_name):
    v = air.get(sensor_name, 1.0)
    if v is None or not np.isfinite(v) or v == 0:
        return 1.0
    return float(v)


def _build_features(rows, air):
    data = {
        s: np.array([r[s] for r in rows], dtype=float)
        for s in GAS_SENSORS
    }

    feat = {}

    feat["MQ2_MQ3_ratio"] = _safe_ratio(np.mean(data["MQ2"]), np.mean(data["MQ3"]))
    feat["MQ3_MQ135_ratio"] = _safe_ratio(np.mean(data["MQ3"]), np.mean(data["MQ135"]))
    feat["MQ3_TGS2602_ratio"] = _safe_ratio(np.mean(data["MQ3"]), np.mean(data["TGS2602"]))
    feat["MQ3_MQ135_correlation"] = _safe_corr(data["MQ3"], data["MQ135"])

    feat["MQ2_auc_norm"] = _safe_auc(data["MQ2"]) / (len(data["MQ2"]) * _base_value(air, "MQ2"))
    feat["MQ2_mean_norm"] = np.mean(data["MQ2"]) / _base_value(air, "MQ2")

    feat["MQ3_range_norm"] = (
        np.max(data["MQ3"]) - np.min(data["MQ3"])
    ) / _base_value(air, "MQ3")
    feat["MQ3_max_norm"] = np.max(data["MQ3"]) / _base_value(air, "MQ3")
    feat["MQ3_std_norm"] = np.std(data["MQ3"]) / _base_value(air, "MQ3")

    feat["MQ9_slope"] = _safe_slope(data["MQ9"])
    feat["MQ9_min_norm"] = np.min(data["MQ9"]) / _base_value(air, "MQ9")
    feat["MQ9_delta_mean"] = _safe_mean_diff(data["MQ9"])

    feat["TGS2602_min_norm"] = np.min(data["TGS2602"]) / _base_value(air, "TGS2602")
    feat["TGS2602_delta_std"] = (
        np.std(np.diff(data["TGS2602"]))
        if len(data["TGS2602"]) >= 2
        else 0.0
    )
    feat["TGS2602_std_norm"] = np.std(data["TGS2602"]) / _base_value(air, "TGS2602")

    return feat, data


# ─────────────────────────────────────────
# 後處理邏輯
# ─────────────────────────────────────────
def _air_or_no_sample_guard(feat, proba):
    mq2_mean_norm = float(feat.get("MQ2_mean_norm", 999.0))
    mq9_min_norm = float(feat.get("MQ9_min_norm", 999.0))
    tgs2602_min_norm = float(feat.get("TGS2602_min_norm", 999.0))
    mq3_std_norm = float(feat.get("MQ3_std_norm", 999.0))
    tgs2602_std_norm = float(feat.get("TGS2602_std_norm", 999.0))
    mq9_slope = float(feat.get("MQ9_slope", 999.0))
    mq3_mq135_ratio = float(feat.get("MQ3_MQ135_ratio", 0.0))
    p3 = float(proba[3]) if len(proba) >= 4 else 0.0

    if tgs2602_min_norm > 1.02:
        return False
    if mq3_mq135_ratio > 2.00:
        return False
    if p3 >= 0.08 and mq3_mq135_ratio > 1.98:
        return False

    baseline_hits = sum([
        0.99 <= mq2_mean_norm <= 1.01,
        0.99 <= mq9_min_norm <= 1.01,
        0.99 <= tgs2602_min_norm <= 1.01,
    ])

    weak_signal_hits = sum([
        mq3_std_norm < 0.0028,
        tgs2602_std_norm < 0.0030,
        abs(mq9_slope) < 0.006,
    ])

    return baseline_hits == 3 and weak_signal_hits >= 2


def _early_stage_override(pred, proba, feat):
    if int(pred) != 2:
        return pred, False

    p0 = float(proba[0])
    p1 = float(proba[1])
    p2 = float(proba[2])
    p3 = float(proba[3])

    tgs = float(feat.get("TGS2602_min_norm", 1.0))
    mq2 = float(feat.get("MQ2_mean_norm", 1.0))
    mq9 = float(feat.get("MQ9_min_norm", 1.0))
    mq3s = float(feat.get("MQ3_std_norm", 999.0))
    mq3r = float(feat.get("MQ3_range_norm", 999.0))
    ratio = float(feat.get("MQ3_MQ135_ratio", 0.0))
    em = p0 + p1

    if p2 <= 0.70 and p3 <= 0.13 and tgs < 0.94 and mq2 < 1.00 and mq9 < 0.97:
        return 0, True

    if p2 <= 0.50 and p3 <= 0.12 and em >= 0.35 and mq3s <= 0.0015 and mq3r <= 0.0025:
        return 0, True

    if (
        p2 <= 0.88
        and p3 <= 0.10
        and 0.94 <= tgs < 1.02
        and mq2 < 1.02
        and mq9 < 0.98
        and mq3s < 0.0065
        and mq3r < 0.0080
        and ratio > 2.00
    ):
        return 1, True

    if p2 <= 0.60 and p3 <= 0.14 and p1 >= 0.18 and em >= 0.35 and ratio > 1.70:
        return 1, True

    return pred, False


def _overripe_override(pred, proba, feat):
    if int(pred) != 2:
        return pred, False

    p0, p1, p2, p3 = [float(proba[i]) for i in range(4)]

    ratio = float(feat.get("MQ3_MQ135_ratio", 0.0))
    tgs = float(feat.get("TGS2602_min_norm", 0.0))
    mq2 = float(feat.get("MQ2_mean_norm", 999.0))
    em = p0 + p1

    if em >= 0.30 and p2 <= 0.60:
        return pred, False

    strong = p3 >= 0.14 and p2 >= 0.60 and tgs >= 1.05 and ratio >= 2.08
    normal = p3 >= 0.15 and p2 >= 0.60 and ratio >= 2.00 and mq2 <= 1.02
    soft = p3 >= 0.15 and p2 >= 0.65 and ratio >= 2.00

    if strong or normal or soft:
        return 3, True

    return pred, False


def _build_raw_maturity_percent(proba):
    score = (proba[0] * 0 + proba[1] * 1 + proba[2] * 2 + proba[3] * 3) / 3.0
    return int(round(score * 100))


def _build_early_display_percent(final_pred, feat):
    tgs = float(feat.get("TGS2602_min_norm", 1.0))
    mq2 = float(feat.get("MQ2_mean_norm", 1.0))
    mq9 = float(feat.get("MQ9_min_norm", 1.0))

    if int(final_pred) == 0:
        strength = np.clip((tgs - 0.90) / 0.05, 0.0, 1.0)
        return int(round(15 + 10 * strength))

    if int(final_pred) == 1:
        strength = np.clip(
            (
                (tgs - 0.95) / 0.05
                + (1.0 - abs(mq2 - 1.0))
                + (1.0 - abs(mq9 - 1.0))
            )
            / 3.0,
            0.0,
            1.0,
        )
        return int(round(35 + 13 * strength))

    return None


def _build_final_display_percent(raw_pct, final_pred, override_used, proba, feat):
    if not override_used or final_pred != 3:
        return raw_pct

    p3 = float(proba[3])
    tgs = float(feat.get("TGS2602_min_norm", 1.0))
    ratio = float(feat.get("MQ3_MQ135_ratio", 1.0))

    p3_s = np.clip((p3 - 0.08) / 0.22, 0.0, 1.0)
    tgs_s = np.clip((tgs - 0.970) / 0.165, 0.0, 1.0)
    r_s = np.clip((ratio - 2.00) / 0.18, 0.0, 1.0)

    strength = (p3_s + tgs_s + r_s) / 3.0
    pct = int(round(83 + 17 * strength))

    return max(raw_pct, max(83, min(100, pct)))


def _get_display_text(proba, pred):
    sorted_idx = np.argsort(proba)[::-1]
    top1 = int(sorted_idx[0])
    top2 = int(sorted_idx[1])
    p3 = float(proba[3])

    if top1 == 2 and p3 >= 0.18:
        return "成熟，明顯接近過熟"

    if top1 == 2 and p3 >= 0.08:
        return "成熟，但已有過熟傾向"

    if abs(top1 - top2) == 1 and proba[top2] >= 0.15:
        return f"{STAGE_ZH[top1]}（接近{STAGE_ZH[top2]}）"

    return STAGE_ZH[top1]


# ─────────────────────────────────────────
# 推論核心
# ─────────────────────────────────────────
def _run_inference(warmup_sec: int, scan_id: str):
    try:
        if _model is None or _features is None:
            _set_state(status="error", error="MODEL_NOT_LOADED")
            return

        if not AIR_BASE_PATH.exists():
            _set_state(status="error", error="NO_AIR_BASE")
            return

        with open(AIR_BASE_PATH, "r", encoding="utf-8") as f:
            air = json.load(f)

        ser, header, port = _open_serial_and_wait_header()

        total_sec = warmup_sec + WINDOW
        all_rows = []
        t0 = time.time()

        while time.time() - t0 < total_sec:
            line = ser.readline().decode("utf-8", errors="ignore").strip()

            if not line:
                continue

            if line[0] in ("#", "✅", "❌", "📋", "⏱", "🍍", "="):
                continue

            vals = [x.strip() for x in line.split(",")]

            if len(vals) != len(header):
                continue

            row = dict(zip(header, vals))
            parsed = _read_arduino_row(row)

            if parsed is None:
                continue

            all_rows.append(parsed)

            elapsed = time.time() - t0
            progress = min(99, int(elapsed / total_sec * 100))
            _set_state(progress=progress)

        ser.close()

        if not all_rows:
            _set_state(status="error", error="沒有收集到任何感測資料")
            return

        rows = all_rows[-WINDOW:] if len(all_rows) > WINDOW else all_rows

        feat, data = _build_features(rows, air)

        X = np.array([feat.get(f, 0.0) for f in _features], dtype=float).reshape(1, -1)

        raw_pred = int(_model.predict(X)[0])

        if hasattr(_model, "predict_proba"):
            proba = _model.predict_proba(X)[0]
        else:
            proba = np.zeros(4, dtype=float)
            proba[raw_pred] = 1.0

        guard_triggered = _air_or_no_sample_guard(feat, proba)
        display_text = _get_display_text(proba, raw_pred)

        final_pred, early_used = _early_stage_override(raw_pred, proba, feat)
        override_used = False

        if early_used:
            if final_pred == 0:
                display_text = "未熟（接近初熟）"
            elif final_pred == 1:
                display_text = "初熟（接近成熟）"
            else:
                display_text = STAGE_ZH.get(final_pred, str(final_pred))
        else:
            final_pred, override_used = _overripe_override(raw_pred, proba, feat)

            if override_used:
                display_text = "過熟"

        raw_pct = _build_raw_maturity_percent(proba)

        if early_used:
            final_pct = _build_early_display_percent(final_pred, feat)
            if final_pct is None:
                final_pct = raw_pct
        else:
            final_pct = _build_final_display_percent(
                raw_pct,
                final_pred,
                override_used,
                proba,
                feat,
            )

        sensor_means = {
            s: float(np.mean(data[s]))
            for s in GAS_SENSORS
        }

        sensor_raw = {
            "MQ2": sensor_means["MQ2"],
            "MQ3": sensor_means["MQ3"],
            "MQ9": sensor_means["MQ9"],
            "MQ135": sensor_means["MQ135"],
            "TGS2602": sensor_means["TGS2602"],
        }

        sensor_percent = {
            s: round(min(100.0, sensor_means[s] / 1023.0 * 100.0), 2)
            for s in GAS_SENSORS
        }

        temp_values = [r["Temp_C"] for r in rows if r.get("Temp_C") is not None]
        humidity_values = [r["Humidity_pct"] for r in rows if r.get("Humidity_pct") is not None]
        pressure_values = [r["Pressure_hPa"] for r in rows if r.get("Pressure_hPa") is not None]

        environment = {
            "temperature": round(float(np.mean(temp_values)), 2) if temp_values else None,
            "humidity": round(float(np.mean(humidity_values)), 2) if humidity_values else None,
            "pressure": round(float(np.mean(pressure_values)), 2) if pressure_values else None,
        }

        result = {
            "id": scan_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",

            "stage": final_pred,
            "ripeness": STAGE_EN[final_pred],
            "label_zh": STAGE_ZH[final_pred],
            "display_text": display_text,
            "percent": final_pct,

            "ripenessLabelZh": display_text,
            "ripenessLabelEn": STAGE_EN[final_pred].capitalize(),
            "maturityPercent": final_pct,
            "confidence": round(float(np.max(proba)), 4),

            "probabilities": {
                "stage0": round(float(proba[0]), 4),
                "stage1": round(float(proba[1]), 4),
                "stage2": round(float(proba[2]), 4),
                "stage3": round(float(proba[3]), 4),
            },

            "sensor_percent": sensor_percent,
            "sensor_raw": sensor_raw,

            "environment": environment,

            "suggestion": SUGGESTION.get(final_pred, ""),
            "suggestions": [SUGGESTION.get(final_pred, "")],

            "guard_triggered": guard_triggered,
            "override_used": override_used,

            "debug": {
                "raw_pred": raw_pred,
                "final_pred": final_pred,
                "early_override_used": early_used,
                "overripe_override_used": override_used,
                "feature_values": feat,
                "air_base": air,
                "arduino_port": port,
            },
        }

        _set_state(status="done", progress=100, result=result, error=None)

        print(f"[Scan] 完成：{STAGE_ZH[final_pred]} ({final_pct}%)")

    except Exception as e:
        print(f"[Scan] 錯誤：{e}")
        _set_state(status="error", error=str(e))


# ─────────────────────────────────────────
# 空氣校正
# ─────────────────────────────────────────
def _run_calibration():
    try:
        ser, header, port = _open_serial_and_wait_header()

        all_rows = []
        t0 = time.time()

        while time.time() - t0 < 30:
            line = ser.readline().decode("utf-8", errors="ignore").strip()

            if not line:
                continue

            if line[0] in ("#", "✅", "❌", "📋", "⏱", "🍍", "="):
                continue

            vals = [x.strip() for x in line.split(",")]

            if len(vals) != len(header):
                continue

            row = dict(zip(header, vals))
            parsed = _read_arduino_row(row)

            if parsed is None:
                continue

            all_rows.append(parsed)

            progress = min(99, int((time.time() - t0) / 30 * 100))
            _set_state(progress=progress)

        ser.close()

        if not all_rows:
            _set_state(status="error", error="校正期間沒有收到資料")
            return

        air = {}

        for key in CALIBRATION_KEYS:
            values = [r[key] for r in all_rows if r.get(key) is not None]
            if values:
                air[key] = float(np.mean(values))

        air["_meta"] = {
            "created_at": datetime.utcnow().isoformat() + "Z",
            "duration_sec": 30,
            "sample_count": len(all_rows),
            "arduino_port": port,
            "gas_sensors": GAS_SENSORS,
            "environment_keys": BME_KEYS,
        }

        with open(AIR_BASE_PATH, "w", encoding="utf-8") as f:
            json.dump(air, f, indent=2, ensure_ascii=False)

        print(f"[Calibrate] 完成，air_base.json 已儲存：{air}")

        _set_state(status="idle", progress=100, result=None, error=None)

    except Exception as e:
        print(f"[Calibrate] 錯誤：{e}")
        _set_state(status="error", error=str(e))


# ─────────────────────────────────────────
# Flask App
# ─────────────────────────────────────────
app = Flask(__name__)


@app.after_request
def _cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, ngrok-skip-browser-warning"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


@app.route("/health", methods=["GET"])
def health():
    air_exists = AIR_BASE_PATH.exists()

    calibrated_at = None
    air_base_preview = None

    if air_exists:
        calibrated_at = datetime.utcfromtimestamp(
            AIR_BASE_PATH.stat().st_mtime
        ).isoformat() + "Z"

        try:
            with open(AIR_BASE_PATH, "r", encoding="utf-8") as f:
                air_base_preview = json.load(f)
        except Exception:
            air_base_preview = None

    ports = sorted(glob.glob("/dev/ttyACM*")) + sorted(glob.glob("/dev/ttyUSB*"))

    return jsonify({
        "status": "ok",
        "air_base_exists": air_exists,
        "air_calibrated_at": calibrated_at,
        "air_base_preview": air_base_preview,
        "model_exists": MODEL_PATH.exists(),
        "feature_columns_exists": FEATURES_PATH.exists(),
        "arduino_ports": ports,
        "pineapple_dir": str(PINEAPPLE_DIR),
        "time": datetime.utcnow().isoformat() + "Z",
    })


@app.route("/calibrate", methods=["POST", "OPTIONS"])
def calibrate():
    if request.method == "OPTIONS":
        return "", 204

    state = _get_state()

    if state["status"] in ("scanning", "calibrating"):
        return jsonify({"error": "BUSY"}), 409

    _set_state(status="calibrating", progress=0, result=None, error=None)

    t = threading.Thread(target=_run_calibration, daemon=True)
    t.start()

    return jsonify({
        "ok": True,
        "message": "空氣校正已開始，約 30 秒後完成",
    }), 200


@app.route("/scan", methods=["POST", "OPTIONS"])
def scan():
    if request.method == "OPTIONS":
        return "", 204

    state = _get_state()

    if state["status"] in ("scanning", "calibrating"):
        return jsonify({"error": "BUSY"}), 409

    if not AIR_BASE_PATH.exists():
        return jsonify({"error": "NO_AIR_BASE"}), 400

    data = request.get_json(silent=True) or {}

    warmup_sec = int(data.get("warmup_sec", 0))
    scan_id = str(uuid.uuid4())

    _set_state(
        status="scanning",
        progress=0,
        result=None,
        error=None,
        scan_id=scan_id,
    )

    t = threading.Thread(
        target=_run_inference,
        args=(warmup_sec, scan_id),
        daemon=True,
    )
    t.start()

    return jsonify({
        "ok": True,
        "scan_id": scan_id,
    }), 200


@app.route("/status", methods=["GET"])
def status():
    state = _get_state()

    return jsonify({
        "status": state["status"],
        "progress": state["progress"],
        "result": state["result"],
        "error": state["error"],
        "scan_id": state["scan_id"],
    })


@app.route("/scan_records", methods=["POST", "OPTIONS"])
def scan_records():
    if request.method == "OPTIONS":
        return "", 204

    payload = request.get_json(silent=True) or {}

    records = []

    if RECORDS_PATH.exists():
        try:
            with open(RECORDS_PATH, "r", encoding="utf-8") as f:
                records = json.load(f)
        except Exception:
            records = []

    record = {
        "id": payload.get("id", str(uuid.uuid4())),
        "saved_at": datetime.utcnow().isoformat() + "Z",
        "data": payload,
    }

    records.insert(0, record)

    with open(RECORDS_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"[Records] 已儲存紀錄：{record['id']}")

    return jsonify({
        "ok": True,
        "id": record["id"],
    }), 200


@app.route("/scan_records/<record_id>/feedback", methods=["POST", "OPTIONS"])
def feedback(record_id):
    if request.method == "OPTIONS":
        return "", 204

    payload = request.get_json(silent=True) or {}

    print(f"[Feedback] record={record_id} payload={payload}")

    return jsonify({"ok": True}), 200


# ─────────────────────────────────────────
# 啟動
# ─────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("🍍 Pineapple Gateway v2 啟動中")
    print(f"  PINEAPPLE_DIR : {PINEAPPLE_DIR}")
    print(f"  MODEL_PATH    : {MODEL_PATH}")
    print(f"  AIR_BASE_PATH : {AIR_BASE_PATH}")
    print(f"  RECORDS_PATH  : {RECORDS_PATH}")
    print("=" * 50)

    try:
        _load_model()
    except Exception as e:
        print(f"[WARNING] 模型載入失敗：{e}")
        print("請確認 deploy_student.pkl 和 feature_columns.json 存在於 pineapple 資料夾")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        threaded=True,
    )