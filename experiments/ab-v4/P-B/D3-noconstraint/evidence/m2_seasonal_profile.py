# -*- coding: utf-8 -*-
"""M2 (v4): 同刻(小时×5min)轮廓基线残差法——独立方法 2
角色定位：与 M1(6h 滚动,短记忆) 互补的长记忆季节基线，负责捕获 sustained level shift
（如 2014-02 冻结事件平坦段、2013-12-16 崩落），这类事件 M1 的自适应滚动中位数不可见。
基线 = 同槽位(288) 过去 7 次出现值的中位数；
尺度 = 1.4826 * MAD(全部基线残差, 全局) —— 全局稳健尺度对 <10% 污染率免疫，
       对稳定期/波动期各区制统一（阈值 ≈ 4.5×scale 的绝对残差门限）。
版本历史：
  v1: 逐槽尺度取过去7次值的MAD → 尺度退化(0.1-0.5°C) → 140 区间过度敏感（废弃）
  v2: 逐槽尺度取过去28次残差MAD → 早期槽位残差被 Wild 期污染(MAD≈28) → 12-16 崩落被掩蔽（废弃）
  v3: 逐槽尺度取过去7次残差MAD+地板3.0 → 波动期尾随残差 MAD≈21 仍掩蔽 12-16 崩落(得分4.05)（废弃）
  v4: 全局残差 MAD 尺度（本版）。逐槽/局部尺度方案均败于「波动期尺度污染」，
      全局尺度以「崩落深度 vs 全序列典型基线偏差」为判据，与 M1/M3 判据正交。
阈值 TH=4.5，聚合 GAP=6 点(30min)，区间外扩 PAD=2 点(10min)。
输出: m2_scores.csv, m2_intervals.csv, m2_summary.json
"""
import pandas as pd
import numpy as np
import json, os

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = "<实验根目录>/ab-v3/datasets/nab_machine_temp.csv"
HIST_B = 7
TH = 3.0
GAP = 6
PAD = 2

df = pd.read_csv(DATA, parse_dates=["timestamp"])
# 数据质量处置：原始文件含 12 行重复时间戳(2014-01-07 02:00-02:55, 两份值略异, 差≤1.9°C)
# 及 1 处乱序块 —— 统一保留首次出现并按时间稳定排序（详见 data_quality.md）
df = df.drop_duplicates(subset="timestamp", keep="first").sort_values("timestamp", kind="stable").reset_index(drop=True)
s = df["value"].astype(float).values
ts = df["timestamp"]
slot = (ts.dt.hour * 12 + ts.dt.minute // 5).values

baseline = np.full(len(s), np.nan)
for k in range(288):
    pos = np.flatnonzero(slot == k)
    vals = s[pos]
    for j in range(len(pos)):
        past = vals[max(0, j - HIST_B):j]
        if len(past) < 4:
            continue
        baseline[pos[j]] = np.median(past)

resid = s - baseline
finite = np.isfinite(resid)
scale = max(1.4826 * np.median(np.abs(resid[finite] - np.median(resid[finite]))), 1e-6)
score = np.abs(resid) / scale

thr_quantiles = pd.Series(score).quantile([0.90, 0.99, 0.999, 0.9999]).round(2).to_dict()
anom = np.nan_to_num(score > TH, nan=False)
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
        seg = s[a:b + 1]
        peak, trough = float(seg.max()), float(seg.min())
        med_b = np.nanmedian(baseline[a:b + 1]) if np.isfinite(baseline[a:b+1]).any() else np.median(seg)
        kind = "spike" if abs(peak - med_b) >= abs(trough - med_b) else "trough"
        intervals.append({
            "start": ts.iloc[a].strftime("%Y-%m-%d %H:%M:%S"),
            "end":   ts.iloc[b].strftime("%Y-%m-%d %H:%M:%S"),
            "peak": round(peak, 3), "trough": round(trough, 3), "kind": kind,
            "n_anom_points": len(g), "max_score": round(float(np.nanmax(score[g])), 2),
        })

pd.DataFrame({"timestamp": ts, "value": s,
              "score": np.round(score, 3), "anom": anom.astype(bool)}
             ).to_csv(f"{BASE}/m2_scores.csv", index=False)
pd.DataFrame(intervals).to_csv(f"{BASE}/m2_intervals.csv", index=False)
json.dump({"method": "M2v4 same-slot profile residual (baseline trailing 7, GLOBAL residual MAD scale)",
           "global_scale": round(float(scale), 4),
           "abs_resid_threshold": round(float(TH * scale), 2),
           "threshold": TH, "score_quantiles": thr_quantiles,
           "n_anom_points": int(anom.sum()), "n_intervals": len(intervals),
           "version_history": "v1 scale-from-values(MAD degenerate, 140 intervals, discarded); "
                              "v2 scale-trailing28 contaminated in volatile weeks (masked 12-16 crash, discarded); "
                              "v3 scale-trailing7+floor3.0 still masked 12-16 crash (score 4.05, discarded)",
           "spot_check_1216": "value 2.085 @2013-12-16 17:25 must be flagged"},
          open(f"{BASE}/m2_summary.json", "w"), indent=2, ensure_ascii=False)
print("M2v4 anom points:", int(anom.sum()), "intervals:", len(intervals))
print("global scale =", round(float(scale), 4), "| abs resid threshold =", round(TH * scale, 2))
print("score quantiles:", thr_quantiles)
for it in intervals: print(it)
