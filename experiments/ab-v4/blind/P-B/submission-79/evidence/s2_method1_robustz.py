# -*- coding: utf-8 -*-
"""阶段2 方法一：滚动中位数 + MAD 鲁棒 Z 阈值法（D3-interrupt）· v2
基线与尺度均滚动估计 -> 对水平漂移鲁棒。跑两档阈值（strict/loose）供交叉验证。
输出: evidence/s2_method1_points_{strict,loose}.csv, s2_method1_segments_{strict,loose}.json, s2_method1_summary.txt
"""
import pandas as pd
import numpy as np
import json

DATA = "<实验根目录>/ab-v3/datasets/nab_machine_temp.csv"
OUT = "<实验根目录>/ab-v4/P-B/D3-interrupt/evidence/"

WINDOW = 61          # 滚动窗口 61 点 ≈ 5 小时（5 分钟采样）
GAP_MERGE = 6        # 相邻异常点间隔 <= 6 点(30分钟)合并为同一区段
TIERS = {"strict": 5.0, "loose": 3.5}   # 两档阈值

df = pd.read_csv(DATA)
df["timestamp"] = pd.to_datetime(df["timestamp"])
mono = int(df["timestamp"].is_monotonic_increasing)  # -1/0/1
print(f"时间轴单调标志(按原行序): {mono}")

v = df["value"].astype(float)

roll_med = v.rolling(WINDOW, center=True, min_periods=1).median()
abs_dev = (v - roll_med).abs()
roll_mad = abs_dev.rolling(WINDOW, center=True, min_periods=1).median()
global_mad = float(np.median(np.abs(v - v.median())))
roll_mad_eff = roll_mad.clip(lower=0.25 * global_mad)

robust_z = (v - roll_med) / (1.4826 * roll_mad_eff)

summary = []
summary.append("=== 阶段2 方法一：滚动中位数+MAD 鲁棒 Z (v2) ===")
summary.append(f"参数: window={WINDOW}(~5h), gap_merge={GAP_MERGE}点(30min), MAD下限=0.25*全局MAD={0.25*global_mad:.4f}")
summary.append(f"全局 MAD={global_mad:.4f}")
summary.append(f"数据卫生: 时间轴按原行序单调标志={mono}(pandas int 语义, -1=无法判定), 重复时间戳=12, 回退=1处(row10149)——滚动窗口按原行序计算,时间基本递增,影响有限")

for tier, zt in TIERS.items():
    anom = robust_z.abs() > zt
    anom_idx = np.where(anom)[0]

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
        seg_z = robust_z.iloc[s:e+1]
        peak_i = int(np.argmax(seg_v.values))
        trough_i = int(np.argmin(seg_v.values))
        peak_i_global = s + peak_i
        trough_i_global = s + trough_i
        seg_records.append({
            "start": str(df["timestamp"].iloc[s]),
            "end": str(df["timestamp"].iloc[e]),
            "n_points": int(e - s + 1),
            "peak": float(seg_v.max()), "peak_at": str(df["timestamp"].iloc[peak_i_global]),
            "trough": float(seg_v.min()), "trough_at": str(df["timestamp"].iloc[trough_i_global]),
            "max_abs_z": float(seg_z.abs().max()),
        })

    pd.DataFrame({
        "timestamp": df["timestamp"][anom_idx].values,
        "value": v[anom_idx].values,
        "robust_z": robust_z[anom_idx].values,
    }).to_csv(OUT + f"s2_method1_points_{tier}.csv", index=False)

    with open(OUT + f"s2_method1_segments_{tier}.json", "w", encoding="utf-8") as f:
        json.dump({"params": {"window": WINDOW, "z_threshold": zt,
                              "gap_merge_points": GAP_MERGE, "mad_floor": "0.25*global_MAD"},
                   "n_anomaly_points": len(anom_idx),
                   "n_segments": len(seg_records),
                   "segments": seg_records}, f, ensure_ascii=False, indent=2)

    summary.append(f"\n--- 档位 {tier}: z>{zt} ---")
    summary.append(f"异常点: {len(anom_idx)} 个; 区段: {len(seg_records)} 个")
    for r in seg_records:
        summary.append(f"  [{r['start']} ~ {r['end']}] n={r['n_points']} peak={r['peak']:.2f}@{r['peak_at']} trough={r['trough']:.2f}@{r['trough_at']} max|z|={r['max_abs_z']:.1f}")

txt = "\n".join(summary)
with open(OUT + "s2_method1_summary.txt", "w", encoding="utf-8") as f:
    f.write(txt)
print(txt)
