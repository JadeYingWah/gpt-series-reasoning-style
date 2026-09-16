# -*- coding: utf-8 -*-
"""
方法 M4（机器学习路径：IsolationForest，与 M1-M3 统计路径独立）
特征: value / rolling_mean_12(1h) / rolling_std_12 / 日内相位 sin+cos
评分: decision_function 越小越异常；strict = 分位 0.5%, loose = 分位 1%（按 burn-in 后计）
burn-in 前 15% 不报；random_state=42 固定
输出: points_m4_{strict,loose}.csv, methods_iforest.json
"""
import pandas as pd, numpy as np, json
from sklearn.ensemble import IsolationForest

SRC = "<实验根目录>/ab-v3/datasets/nab_machine_temp.csv"
BURN_IN_FRAC = 0.15
TH = {"strict": 0.995, "loose": 0.99}   # 异常分位阈值

df = pd.read_csv(SRC)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.sort_values('timestamp').drop_duplicates('timestamp', keep='first').reset_index(drop=True)
x = df['value'].to_numpy(dtype=float)
n = len(df); burn_end = int(n * BURN_IN_FRAC)

s = pd.Series(x)
feats = pd.DataFrame({
    "value": x,
    "rm1h": s.rolling(12, center=True, min_periods=6).mean(),
    "rs1h": s.rolling(12, center=True, min_periods=6).std(),
})
tod = df['timestamp'].dt.hour * 60 + df['timestamp'].dt.minute
feats["tod_sin"] = np.sin(2 * np.pi * tod / 1440)
feats["tod_cos"] = np.cos(2 * np.pi * tod / 1440)
feats = feats.bfill().ffill()

iso = IsolationForest(n_estimators=300, random_state=42, n_jobs=-1)
iso.fit(feats)
score = -iso.decision_function(feats)   # 越大越异常

post = score[burn_end:]
th_s = np.quantile(post, TH["strict"])
th_l = np.quantile(post, TH["loose"])
idx = np.arange(n)
m4s = (score >= th_s) & (idx >= burn_end)
m4l = (score >= th_l) & (idx >= burn_end)

def to_points(mask):
    i = np.where(mask)[0]
    return pd.DataFrame({"idx": i, "timestamp": df['timestamp'].iloc[i].to_numpy(),
                         "value": x[i], "score": score[i]})

to_points(m4s).to_csv("points_m4_strict.csv", index=False)
to_points(m4l).to_csv("points_m4_loose.csv", index=False)
res = {"M4": {"method": "IsolationForest(value, rm1h, rs1h, tod_sin/cos), 300 trees, rs=42",
              "thresholds": {"strict_q": TH["strict"], "loose_q": TH["loose"],
                             "strict_score": float(th_s), "loose_score": float(th_l)},
              "n_points_strict": int(m4s.sum()), "n_points_loose": int(m4l.sum()),
              "cluster_days_strict": {str(k): int(v) for k, v in
                  to_points(m4s)['timestamp'].dt.floor('D').value_counts().sort_index().items()}}}
json.dump(res, open("methods_iforest.json", "w"), indent=2)
print(json.dumps(res, indent=2))
