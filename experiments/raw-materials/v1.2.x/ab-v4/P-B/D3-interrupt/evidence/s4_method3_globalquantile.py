# -*- coding: utf-8 -*-
"""阶段3b 方法三：全局分位包络法（D3-interrupt）
机制独立性：不做任何局部/季节基线，直接用全序列分位数定义正常值域——
抓「超出历史正常值域」的极值（高值plateau如12-26的108、深谷如2.08/25.89）。
输出: evidence/s4_method3_points.csv, s4_method3_segments.json, s4_method3_summary.txt
"""
import pandas as pd
import numpy as np
import json

DATA = "<实验根目录>/ab-v3/datasets/nab_machine_temp.csv"
OUT = "<实验根目录>/ab-v4/P-B/D3-interrupt/evidence/"

Q_LOW = 0.005     # P0.5 下界
Q_HIGH = 0.995    # P99.5 上界
GAP_MERGE = 6

df = pd.read_csv(DATA)
df["timestamp"] = pd.to_datetime(df["timestamp"])
v = df["value"].astype(float)

lo = float(v.quantile(Q_LOW))
hi = float(v.quantile(Q_HIGH))
print(f"P{Q_LOW*100}={lo:.3f}, P{Q_HIGH*100}={hi:.3f}")

anom = (v < lo) | (v > hi)
anom_idx = np.where(anom)[0]
print(f"异常点: {len(anom_idx)}")

segments = []
if len(anom_idx) > 0:
    start = prev = anom_idx[0]
    for i in anom_idx[1:]:
        if i - prev <= GAP_MERGE:
            prev = i
        else:
            segments.append((start, prev))
            start = prev = i
    segments.append((start, prev))

seg_records = []
for s, e in segments:
    seg_v = v.iloc[s:e+1]
    peak_i = s + int(np.argmax(seg_v.values))
    trough_i = s + int(np.argmin(seg_v.values))
    seg_records.append({
        "start": str(df["timestamp"].iloc[s]),
        "end": str(df["timestamp"].iloc[e]),
        "n_points": int(e - s + 1),
        "peak": float(seg_v.max()), "peak_at": str(df["timestamp"].iloc[peak_i]),
        "trough": float(seg_v.min()), "trough_at": str(df["timestamp"].iloc[trough_i]),
    })

pd.DataFrame({
    "timestamp": df["timestamp"][anom_idx].values,
    "value": v[anom_idx].values,
}).to_csv(OUT + "s4_method3_points.csv", index=False)

with open(OUT + "s4_method3_segments.json", "w", encoding="utf-8") as f:
    json.dump({"params": {"q_low": Q_LOW, "q_high": Q_HIGH, "lower_bound": lo,
                          "upper_bound": hi, "gap_merge_points": GAP_MERGE},
               "n_anomaly_points": len(anom_idx),
               "n_segments": len(seg_records),
               "segments": seg_records}, f, ensure_ascii=False, indent=2)

lines = []
lines.append("=== 阶段3b 方法三：全局分位包络 ===")
lines.append(f"参数: 界=[P{Q_LOW*100}, P{Q_HIGH*100}]=[{lo:.3f}, {hi:.3f}], gap_merge={GAP_MERGE}")
lines.append(f"异常点: {len(anom_idx)} 个; 区段: {len(seg_records)} 个")
for r in seg_records:
    lines.append(f"  [{r['start']} ~ {r['end']}] n={r['n_points']} peak={r['peak']:.2f}@{r['peak_at']} trough={r['trough']:.2f}@{r['trough_at']}")
txt = "\n".join(lines)
with open(OUT + "s4_method3_summary.txt", "w", encoding="utf-8") as f:
    f.write(txt)
print(txt)
