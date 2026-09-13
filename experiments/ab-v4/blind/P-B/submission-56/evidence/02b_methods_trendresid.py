# -*- coding: utf-8 -*-
"""
方法 M3（趋势分离残差路径，纯 numpy，与 M1 全局分布/M2 相位基线均独立）
trend = 中心移动平均(25 点 ≈ 2h)；resid = x - trend
resid 尺度：burn-in 后残差的 MAD，迭代剔除 >5·MAD 的污染点后重估
z3 = resid / (1.4826·sigma_resid)；strict |z|>=6, loose |z|>=4.5；burn-in 前 15% 不报
输出: points_m3_{strict,loose}.csv, methods_trendresid.json
"""
import pandas as pd, numpy as np, json

SRC = "<实验根目录>/ab-v3/datasets/nab_machine_temp.csv"
BURN_IN_FRAC = 0.15
WIN = 25
TH = {"strict": 6.0, "loose": 4.5}

df = pd.read_csv(SRC)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.sort_values('timestamp').drop_duplicates('timestamp', keep='first').reset_index(drop=True)
x = df['value'].to_numpy(dtype=float)
n = len(df)
burn_end = int(n * BURN_IN_FRAC)

s = pd.Series(x)
trend = s.rolling(WIN, center=True, min_periods=WIN // 2).median().to_numpy()
resid = x - trend

# 鲁棒尺度：迭代剔除污染
r = resid[burn_end:]
r = r[~np.isnan(r)]
for _ in range(3):
    m = np.median(r); d = np.median(np.abs(r - m)) * 1.4826
    keep = np.abs(r - m) <= 5 * d
    if keep.all():
        break
    r = r[keep]
sigma = np.median(np.abs(r - np.median(r))) * 1.4826
z3 = resid / sigma
z3[np.isnan(z3)] = 0

idx = np.arange(n)
m3_strict = (np.abs(z3) >= TH["strict"]) & (idx >= burn_end)
m3_loose = (np.abs(z3) >= TH["loose"]) & (idx >= burn_end)

def to_points(mask):
    i = np.where(mask)[0]
    return pd.DataFrame({"idx": i, "timestamp": df['timestamp'].iloc[i].to_numpy(),
                         "value": x[i], "score": z3[i]})

to_points(m3_strict).to_csv("points_m3_strict.csv", index=False)
to_points(m3_loose).to_csv("points_m3_loose.csv", index=False)
res = {"M3": {"method": "local trend (25pt rolling median) residual robust z",
              "thresholds": TH, "sigma_resid": float(sigma),
              "n_points_strict": int(m3_strict.sum()), "n_points_loose": int(m3_loose.sum()),
              "cluster_days_strict": {str(k): int(v) for k, v in
                  to_points(m3_strict)['timestamp'].dt.floor('D').value_counts().sort_index().items()},
              "cluster_days_loose": {str(k): int(v) for k, v in
                  to_points(m3_loose)['timestamp'].dt.floor('D').value_counts().sort_index().items()}}}
json.dump(res, open("methods_trendresid.json", "w"), indent=2)
print(json.dumps(res, indent=2))
