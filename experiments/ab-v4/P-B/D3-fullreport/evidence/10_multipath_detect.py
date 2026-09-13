# -*- coding: utf-8 -*-
"""
多路径异常检测（4 条独立方法路径）—— A2+ 轻量+ · 全量报告分支
路径 A：全局鲁棒 z-score（median/MAD）—— 捕获全局极端离群
路径 B：滚动中位数残差（局部 IQR 尺度）—— 捕获局部偏离（对状态漂移鲁棒）
路径 C：季节-趋势分解残差（自实现：288 点日周期）—— 捕获偏离日内模式的点
路径 D：一阶差分鲁棒 z-score —— 捕获突变沿（尖峰起点/阶跃）

合并策略（全量报告分支）：主报告 = 四路径检出点全集合并（确保不漏报）；
高置信子集 = ≥2 条路径确认的区间（作为高优先级清单附列）。
数据按行序处理（row 10149 起有 11 行时间戳回绕重复，属数据自身特性）。
"""
import pandas as pd
import numpy as np
import json

DATA = "<实验根目录>/ab-v3/datasets/nab_machine_temp.csv"
OUTDIR = "<实验根目录>/ab-v4/P-B/D3-fullreport/evidence"

df = pd.read_csv(DATA)
v = df["value"].astype(float)
n = len(df)
idx = np.arange(n)

# ---------- 路径 A：全局 MAD z-score ----------
medA = v.median()
madA = (v - medA).abs().median()
zA = (v - medA).abs() / (1.4826 * madA)
TH_A = 5.0
flagA = set(idx[zA > TH_A])

# ---------- 路径 B：滚动中位数残差（局部 IQR 尺度） ----------
W = 72  # 6 小时
medB = v.rolling(W, center=True, min_periods=36).median()
q1 = v.rolling(W, center=True, min_periods=36).quantile(0.25)
q3 = v.rolling(W, center=True, min_periods=36).quantile(0.75)
sigB = (q3 - q1) / 1.349
zB = (v - medB).abs() / sigB.replace(0, np.nan)
TH_B = 4.5
flagB = set(idx[(zB > TH_B).fillna(False)])

# ---------- 路径 C：季节-趋势分解残差（自实现） ----------
P = 288  # 日周期（5min × 288）
trend = v.rolling(P, center=True, min_periods=P // 2).median()
deseas_base = v - trend
slot = (np.arange(n) * 5 // (60 * 24))  # 占位，下面按时刻分组
tod = pd.to_datetime(df["timestamp"]).dt.strftime("%H:%M")
seasonal = deseas_base.groupby(tod.values).transform("median")
residC = (v - trend - seasonal)
residC = residC.fillna(v - v.median())
madC = (residC - residC.median()).abs().median()
zC = (residC - residC.median()).abs() / (1.4826 * madC)
TH_C = 4.5
flagC = set(idx[zC > TH_C])

# ---------- 路径 D：一阶差分鲁棒 z-score ----------
d1 = v.diff()
madd = (d1 - d1.median()).abs().median()
zD = (d1 - d1.median()).abs() / (1.4826 * madd)
TH_D = 6.0
flagD = set(idx[(zD > TH_D).fillna(False)])

paths = {"A_global_madz": flagA, "B_rolling_med_resid": flagB,
         "C_seasonal_resid": flagC, "D_diff_madz": flagD}

# 落盘各路径检出点
rows = []
for name, s in paths.items():
    for i in sorted(s):
        rows.append({"path": name, "row": int(i), "timestamp": df["timestamp"].iloc[i],
                     "value": float(v.iloc[i]), "z": float([zA, zB, zC, zD][list(paths).index(name)].iloc[i])})
pd.DataFrame(rows).to_csv(f"{OUTDIR}/10_flags_per_path.csv", index=False)

# ---------- 合并为区间（全量合并分支） ----------
union = sorted(set().union(*paths.values()))
GAP = 6  # 相邻检出点间隔 ≤6 行（30 分钟）归入同一区间（尖峰前兆+主崩溃属同一事件）
groups = []
for i in union:
    if groups and i - groups[-1][-1] <= GAP:
        groups[-1].append(i)
    else:
        groups.append([i])

intervals = []
PAD = 2  # 报告边界外扩 ±2 行（10 分钟，保守度调节：宁可错报不可漏报），极值取报告区间内真实数据
for g in groups:
    lo, hi = g[0], g[-1]
    methods = [name for name, s in paths.items() if any(i in s for i in g)]
    plo, phi = max(0, lo - PAD), min(n - 1, hi + PAD)
    seg = v.iloc[plo:phi + 1]  # 极值在报告区间（外扩后）范围内计算，保证自洽
    peak_v, trough_v = float(seg.max()), float(seg.min())
    peak_i, trough_i = int(seg.idxmax()), int(seg.idxmin())
    # 主极值 = 鲁棒 z 更大的方向
    zpk = max(float(zA.iloc[peak_i]), float(zB.iloc[peak_i]) if not np.isnan(zB.iloc[peak_i]) else 0)
    ztr = max(float(zA.iloc[trough_i]), float(zB.iloc[trough_i]) if not np.isnan(zB.iloc[trough_i]) else 0)
    extreme = ("peak", peak_v, df["timestamp"].iloc[peak_i]) if zpk >= ztr else \
              ("trough", trough_v, df["timestamp"].iloc[trough_i])
    intervals.append({
        "start_row": int(plo), "end_row": int(phi),
        "raw_start_row": int(lo), "raw_end_row": int(hi),
        "start_time": df["timestamp"].iloc[plo], "end_time": df["timestamp"].iloc[phi],
        "n_points": phi - plo + 1,
        "extreme_type": extreme[0], "extreme_value": extreme[1], "extreme_time": extreme[2],
        "peak_value": peak_v, "trough_value": trough_v,
        "methods": methods, "n_methods": len(methods),
    })

iv = pd.DataFrame(intervals)
iv.to_csv(f"{OUTDIR}/10_intervals_full.csv", index=False)
hc = iv[iv["n_methods"] >= 2]
hc.to_csv(f"{OUTDIR}/10_intervals_highconf.csv", index=False)

summary = {
    "thresholds": {"A_global_madz": TH_A, "B_rolling_med_resid_local_iqr_z": TH_B,
                   "C_seasonal_resid_madz": TH_C, "D_diff_madz": TH_D},
    "params": {"rolling_window_B": W, "seasonal_period_C": P, "merge_gap_rows": GAP,
               "report_boundary_pad_rows": PAD},
    "n_flagged_per_path": {k: len(s) for k, s in paths.items()},
    "n_union_points": len(union),
    "n_intervals_full": len(iv),
    "n_intervals_highconf_ge2": int(len(hc)),
}
with open(f"{OUTDIR}/10_summary.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
print(json.dumps(summary, ensure_ascii=False, indent=2))
print(iv[["start_time", "end_time", "n_points", "extreme_type", "extreme_value", "n_methods"]].to_string())
