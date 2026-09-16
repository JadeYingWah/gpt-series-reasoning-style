# -*- coding: utf-8 -*-
"""M3: 跳变(一阶差分) + 全局极值分位数——独立方法 3（结构不同：对变化率与全局分布敏感）
路径A: |Δx| > Q99.9(差分) 判跳变；路径B: x 超出全局 [Q0.05, Q99.95] 判极值。
输出: m3_scores.csv, m3_intervals.csv, m3_summary.json
"""
import pandas as pd
import numpy as np
import json, os

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = "<实验根目录>/ab-v3/datasets/nab_machine_temp.csv"
GAP = 6
PAD = 2

df = pd.read_csv(DATA, parse_dates=["timestamp"])
# 数据质量处置：原始文件含 12 行重复时间戳(2014-01-07 02:00-02:55, 两份值略异, 差≤1.9°C)
# 及 1 处乱序块 —— 统一保留首次出现并按时间稳定排序（详见 data_quality.md）
df = df.drop_duplicates(subset="timestamp", keep="first").sort_values("timestamp", kind="stable").reset_index(drop=True)
s = df["value"].astype(float)
ts = df["timestamp"]

d = s.diff().abs()
q_d = float(d.quantile(0.999))
jump = d > q_d

q_hi, q_lo = float(s.quantile(0.9995)), float(s.quantile(0.0005))
extreme = (s > q_hi) | (s < q_lo)

anom = (jump | extreme).values
idx = np.flatnonzero(anom)

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
        kind = "spike" if abs(peak - np.median(s)) >= abs(trough - np.median(s)) else "trough"
        intervals.append({
            "start": ts.iloc[a].strftime("%Y-%m-%d %H:%M:%S"),
            "end":   ts.iloc[b].strftime("%Y-%m-%d %H:%M:%S"),
            "peak": round(peak, 3), "trough": round(trough, 3), "kind": kind,
            "n_anom_points": len(g),
            "max_jump": round(float(d.iloc[g].max()), 3),
        })

pd.DataFrame({"timestamp": ts, "value": s, "diff": d.round(3),
              "jump": jump, "extreme": extreme, "anom": anom}).to_csv(f"{BASE}/m3_scores.csv", index=False)
pd.DataFrame(intervals).to_csv(f"{BASE}/m3_intervals.csv", index=False)
json.dump({"method": "M3 jump(diff>Q99.9) + global extreme(Q0.05/Q99.95)",
           "q_diff_999": round(q_d, 3), "q_hi_9995": round(q_hi, 3), "q_lo_0005": round(q_lo, 3),
           "n_anom_points": int(anom.sum()), "n_intervals": len(intervals)},
          open(f"{BASE}/m3_summary.json", "w"), indent=2, ensure_ascii=False)
print("M3 anom points:", int(anom.sum()), "intervals:", len(intervals))
print("jump thr:", round(q_d,3), "extreme range:", round(q_lo,3), "~", round(q_hi,3))
for it in intervals: print(it)
