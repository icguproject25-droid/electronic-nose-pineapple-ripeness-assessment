"""
debug_features.py
在樹莓派上執行，印出所有 demo_data 的 feature 值和校正規則觸發情況
用法：python debug_features.py
"""
import glob, json, os, pickle
import numpy as np
import pandas as pd

DEMO_DIR = "demo_data"
SENSORS = ["MQ2","MQ3","MQ9","MQ135","TGS2602"]
STAGE_TEXT = {0:"未熟",1:"初熟",2:"成熟",3:"過熟"}

def load_xlsx(path):
    raw = pd.read_excel(path, header=None)
    for i, row in raw.iterrows():
        if str(row.iloc[0]).strip() == "timestamp_ms":
            df = raw.iloc[i+1:].copy()
            df.columns = raw.iloc[i].tolist()
            df = df[~df["timestamp_ms"].astype(str).str.startswith("#")].reset_index(drop=True)
            for col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            return df

def safe_ratio(a,b): return float(a)/(float(b)+1e-9)
def safe_slope(x):
    if len(x)<2: return 0.0
    return float(np.polyfit(range(len(x)),x,1)[0])
def safe_mean_diff(x):
    if len(x)<2: return 0.0
    d=np.diff(x); return float(np.mean(d)) if len(d)>0 else 0.0
def safe_auc(x):
    fn=np.trapezoid if hasattr(np,"trapezoid") else np.trapz
    return float(fn(x))

def get_air(air_df):
    air={}
    for s in SENSORS:
        col=f"{s}_raw"
        if col in air_df.columns:
            arr=air_df[col].dropna().values.astype(float)
            arr=arr[np.isfinite(arr)]
            if len(arr)>0: air[s]=float(np.mean(arr))
    return air

def build_features(rows, air):
    data={s:np.array([r[s] for r in rows],dtype=float) for s in SENSORS}
    def base(s):
        v=air.get(s,1.0); return float(v) if v and np.isfinite(v) and v!=0 else 1.0
    feat={}
    feat["MQ2_MQ3_ratio"]=safe_ratio(np.mean(data["MQ2"]),np.mean(data["MQ3"]))
    feat["MQ3_MQ135_ratio"]=safe_ratio(np.mean(data["MQ3"]),np.mean(data["MQ135"]))
    feat["MQ2_auc_norm"]=safe_auc(data["MQ2"])/(len(data["MQ2"])*base("MQ2"))
    feat["MQ2_mean_norm"]=np.mean(data["MQ2"])/base("MQ2")
    feat["MQ3_range_norm"]=(np.max(data["MQ3"])-np.min(data["MQ3"]))/base("MQ3")
    feat["MQ3_std_norm"]=np.std(data["MQ3"])/base("MQ3")
    feat["MQ9_slope"]=safe_slope(data["MQ9"])
    feat["MQ9_min_norm"]=np.min(data["MQ9"])/base("MQ9")
    feat["MQ9_delta_mean"]=safe_mean_diff(data["MQ9"])
    feat["TGS2602_min_norm"]=np.min(data["TGS2602"])/base("TGS2602")
    feat["TGS2602_std_norm"]=np.std(data["TGS2602"])/base("TGS2602")
    return feat, data

# 掃描檔案
import re
air_map, pine_map = {}, {}
for f in sorted(glob.glob(os.path.join(DEMO_DIR, "pineapple_*.xlsx"))):
    base = os.path.basename(f)
    if "_air.xlsx" in base:
        m = re.search(r"^(pineapple_\w+_\d{8})_air\.xlsx$", base)
        if m: air_map[m.group(1)] = f
    else:
        m = re.search(r"^(pineapple_\w+_\d{8})_(.+)\.xlsx$", base)
        if m: pine_map[(m.group(1), m.group(2))] = f

with open("deploy_student.pkl","rb") as f:
    model = pickle.load(f)
with open("feature_columns.json") as f:
    feature_columns = json.load(f)

print("="*80)
print("DEBUG: feature 值 + 校正規則觸發分析")
print("="*80)

for (case_key, stage_label), pine_path in sorted(pine_map.items()):
    if case_key not in air_map:
        print(f"\n[{case_key} / {stage_label}] ❌ 找不到對應 air 檔，跳過")
        continue

    air_df = load_xlsx(air_map[case_key])
    air = get_air(air_df)
    pine_df = load_xlsx(pine_path).tail(30)
    rows=[]
    for _,row in pine_df.iterrows():
        try:
            r={s:float(row[f"{s}_raw"]) for s in SENSORS}
            if all(s in r for s in SENSORS): rows.append(r)
        except: pass
    if not rows:
        print(f"\n[{case_key} / {stage_label}] ❌ 沒有有效資料")
        continue

    feat, _ = build_features(rows, air)
    X = np.array([feat.get(fc,0.0) for fc in feature_columns],dtype=float).reshape(1,-1)
    raw_pred = int(model.predict(X)[0])
    proba = model.predict_proba(X)[0]

    p0=float(proba[0]); p1=float(proba[1]); p2=float(proba[2]); p3=float(proba[3])
    mq9_min      = float(feat.get("MQ9_min_norm",1.0))
    mq3_range    = float(feat.get("MQ3_range_norm",0.0))
    mq2_mean     = float(feat.get("MQ2_mean_norm",1.0))
    mq3_mq135    = float(feat.get("MQ3_MQ135_ratio",1.0))
    tgs_min      = float(feat.get("TGS2602_min_norm",1.0))

    # 校正規則
    unripe   = raw_pred==2 and mq9_min<0.87 and mq3_range>0.025 and p0>=0.25
    semiripe = raw_pred==2 and mq2_mean<0.75 and mq3_mq135>1.70 and p1>=0.15
    strong   = raw_pred==2 and p3>=0.10 and tgs_min>=1.05 and mq3_mq135>=2.08
    normal   = raw_pred==2 and p3>=0.11 and tgs_min>=0.97 and mq3_mq135>=2.00 and mq2_mean<=1.01
    soft     = raw_pred==2 and p3>=0.12 and p2<=0.75 and mq3_mq135>=2.00

    print(f"\n[{case_key} / {stage_label}]")
    print(f"  raw_pred={STAGE_TEXT[raw_pred]}  proba: 未熟={p0:.3f} 初熟={p1:.3f} 成熟={p2:.3f} 過熟={p3:.3f}")
    print(f"  MQ9_min_norm={mq9_min:.4f}  MQ3_range={mq3_range:.4f}  MQ2_mean={mq2_mean:.4f}")
    print(f"  MQ3/MQ135={mq3_mq135:.4f}  TGS2602_min={tgs_min:.4f}")
    print(f"  未熟校正: {unripe}  (條件: pred==2={raw_pred==2}, MQ9<0.87={mq9_min<0.87}, MQ3range>0.025={mq3_range>0.025}, p0>=0.25={p0>=0.25})")
    print(f"  初熟校正: {semiripe}  (條件: pred==2={raw_pred==2}, MQ2<0.75={mq2_mean<0.75}, ratio>1.70={mq3_mq135>1.70}, p1>=0.15={p1>=0.15})")
    print(f"  過熟-strong: {strong}  過熟-normal: {normal}  過熟-soft: {soft}")
    print(f"  → 最終會判成: ", end="")
    if unripe: print("未熟（未熟校正優先）")
    elif semiripe: print("初熟（初熟校正）")
    elif strong or normal or soft: print("過熟（過熟校正）")
    else: print(f"{STAGE_TEXT[raw_pred]}（無校正）")

print("\n" + "="*80)
