# -*- coding: utf-8 -*-
"""
方法 M1 / M2（统计路径，纯 numpy+pandas，独立于 ML 路径）
M1  全局鲁棒 z-score（median/MAD）——捕获全局离群（骤降/骤升型）
M2  相位基线残差法（time-of-day 相位 + 滚动 10 天历史窗）——捕获上下文/渐变型异常
两方法各输出 strict / loose 两档阈值点集，供保守度裁决。
burn-in：前 15% 点（对齐 NAB 文献惯例）不参与报警。
输出: methods_statistical.json, points_m1.csv, points_m2.csv
"""
import pandas as pd, numpy as np, json

SRC = "<实验根目录>/ab-v3/datasets/nab_machine_temp.csv"
BURN_IN_FRAC = 0.15
PHASE_WIN_DAYS = 10            # M2 训练窗：过去 10 天
TH = {"M1": {"strict": 6.0, "loose": 4.5},
      "M2": {"strict": 6.0, "loose": 4.5}}   # 鲁棒 z 阈值（strict 保守档）

df = pd.read_csv(SRC)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.sort_values('timestamp').drop_duplicates('timestamp', keep='first').reset_index(drop=True)
x = df['value'].to_numpy()
n = len(df)
burn_end = int(n * BURN_IN_FRAC)

# ---------- M1: 全局 MAD z ----------
med = np.median(x)
mad = np.median(np.abs(x - med)) * 1.4826
z1 = (x - med) / mad
m1_strict = (np.abs(z1) >= TH["M1"]["strict"]) & (np.arange(n) >= burn_end)
m1_loose  = (np.abs(z1) >= TH["M1"]["loose"])  & (np.arange(n) >= burn_end)

# ---------- M2: 相位基线残差 ----------
tod = df['timestamp'].dt.strftime('%H:%M').to_numpy()
z2 = np.full(n, np.nan)
for phase in np.unique(tod):
    idx = np.where(tod == phase)[0]
    for i in idx:
        sel = (idx >= max(0, i - PHASE_WIN_DAYS * 288)) & (idx < i)
        hist = x[idx[sel]]
        if len(hist) < 5:   # 每相位每天1点，10天窗最多10点
            continue
        hmed = np.median(hist)
        hmad = np.median(np.abs(hist - hmed)) * 1.4826
        if hmad < 0.5:      # 相位点数少，MAD 易为 0；设最小波动尺度 0.5F 防爆 z
            hmad = 0.5
        z2[i] = (x[i] - hmed) / hmad
valid = ~np.isnan(z2)
m2_strict = valid & (np.abs(z2) >= TH["M2"]["strict"]) & (np.arange(n) >= burn_end)
m2_loose  = valid & (np.abs(z2) >= TH["M2"]["loose"])  & (np.arange(n) >= burn_end)

def to_points(mask, score):
    idx = np.where(mask)[0]
    return pd.DataFrame({"idx": idx,
                         "timestamp": df['timestamp'].iloc[idx].to_numpy(),
                         "value": x[idx],
                         "score": score[idx]})

p1s, p1l = to_points(m1_strict, z1), to_points(m1_loose, z1)
p2s, p2l = to_points(m2_strict, z2), to_points(m2_loose, z2)
p1s.to_csv("points_m1_strict.csv", index=False); p1l.to_csv("points_m1_loose.csv", index=False)
p2s.to_csv("points_m2_strict.csv", index=False); p2l.to_csv("points_m2_loose.csv", index=False)

res = {
    "burn_in": {"frac": BURN_IN_FRAC, "end_idx": burn_end,
                "end_time": str(df['timestamp'].iloc[burn_end - 1])},
    "M1": {"method": "global robust z (median/MAD)",
           "thresholds": TH["M1"],
           "n_points_strict": int(m1_strict.sum()), "n_points_loose": int(m1_loose.sum()),
           "median": float(med), "mad_sigma": float(mad)},
    "M2": {"method": "phase-of-day baseline residual (10d rolling hist, median/MAD)",
           "thresholds": TH["M2"], "phase_window_days": PHASE_WIN_DAYS,
           "n_points_strict": int(m2_strict.sum()), "n_points_loose": int(m2_loose.sum())},
}
json.dump(res, open("methods_statistical.json", "w"), indent=2)
print(json.dumps(res, indent=2))
print("\nM1 strict time span:", p1s['timestamp'].min() if len(p1s) else None, "->", p1s['timestamp'].max() if len(p1s) else None)
print("M2 strict time span:", p2s['timestamp'].min() if len(p2s) else None, "->", p2s['timestamp'].max() if len(p2s) else None)
print("M1 strict clusters:", p1s['timestamp'].dt.floor('D').value_counts().sort_index().to_dict())
print("M2 strict clusters:", p2s['timestamp'].dt.floor('D').value_counts().sort_index().to_dict())
print("M1 loose clusters:", p1l['timestamp'].dt.floor('D').value_counts().sort_index().to_dict())
print("M2 loose clusters:", p2l['timestamp'].dt.floor('D').value_counts().sort_index().to_dict())
