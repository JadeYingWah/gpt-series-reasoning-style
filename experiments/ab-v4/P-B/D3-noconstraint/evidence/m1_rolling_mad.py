# -*- coding: utf-8 -*-
"""M1: 滚动稳健 z 分数（滚动中位数 + MAD）——独立方法 1
输出: m1_scores.csv(全序列分数), m1_intervals.csv(点级→区间), m1_summary.json
"""
import pandas as pd
import numpy as np
import json, os

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = "<实验根目录>/ab-v3/datasets/nab_machine_temp.csv"
W = 72          # 滚动窗口 = 72 点 = 6 小时
MINP = 36       # 半窗即可出值
TH = 6.0        # 稳健 z 阈值（依据见 m1_threshold 探查输出）
GAP = 6         # 区间聚合允许的最大间断 = 6 点 = 30 分钟
PAD = 2         # 区间前后各扩 2 点 = 10 分钟上下文

df = pd.read_csv(DATA, parse_dates=["timestamp"])
# 数据质量处置：原始文件含 12 行重复时间戳(2014-01-07 02:00-02:55, 两份值略异, 差≤1.9°C)
# 及 1 处乱序块 —— 统一保留首次出现并按时间稳定排序（详见 data_quality.md）
df = df.drop_duplicates(subset="timestamp", keep="first").sort_values("timestamp", kind="stable").reset_index(drop=True)
s = df["value"].astype(float)

med = s.rolling(W, min_periods=MINP, center=True).median()
dev = (s - med).abs()
mad = dev.rolling(W, min_periods=MINP, center=True).median()
score = dev / (1.4826 * mad.replace(0, np.nan) + 1e-9)

thr_quantiles = score.quantile([0.90, 0.99, 0.999, 0.9999]).round(2).to_dict()

anom = (score > TH).fillna(False)
idx = np.flatnonzero(anom.values)

# 点级异常 → 连续片段（允许 GAP 间断）→ 加 PAD 上下文 → 时间区间
intervals = []
if len(idx) > 0:
    groups = [[idx[0]]]
    for i in idx[1:]:
        if i - groups[-1][-1] <= GAP:
            groups[-1].append(i)
        else:
            groups.append([i])
    for g in groups:
        a, b = max(g[0] - PAD, 0), min(g[-1] + PAD, len(s) - 1)
        seg = s.iloc[a:b + 1]
        peak, trough = float(seg.max()), float(seg.min())
        kind = "spike" if abs(peak - med.iloc[a:b+1].median()) >= abs(trough - med.iloc[a:b+1].median()) else "trough"
        intervals.append({
            "start": df["timestamp"].iloc[a].strftime("%Y-%m-%d %H:%M:%S"),
            "end":   df["timestamp"].iloc[b].strftime("%Y-%m-%d %H:%M:%S"),
            "peak": round(peak, 3), "trough": round(trough, 3), "kind": kind,
            "n_anom_points": len(g), "max_score": round(float(score.iloc[g].max()), 2),
        })

pd.DataFrame({"timestamp": df["timestamp"], "value": s,
              "score": score.round(3), "anom": anom}).to_csv(f"{BASE}/m1_scores.csv", index=False)
pd.DataFrame(intervals).to_csv(f"{BASE}/m1_intervals.csv", index=False)
json.dump({"method": "M1 rolling-median+MAD robust z", "window": W, "threshold": TH,
           "score_quantiles": thr_quantiles, "n_anom_points": int(anom.sum()),
           "n_intervals": len(intervals)},
          open(f"{BASE}/m1_summary.json", "w"), indent=2, ensure_ascii=False)
print("M1 anom points:", int(anom.sum()), "intervals:", len(intervals))
print("score quantiles:", thr_quantiles)
for it in intervals: print(it)
