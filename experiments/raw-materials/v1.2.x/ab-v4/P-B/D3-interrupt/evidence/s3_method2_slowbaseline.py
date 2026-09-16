# -*- coding: utf-8 -*-
"""阶段3 方法二 v3：季节基线(time-of-day 跨天中位数) + 迭代清理MAD（D3-interrupt）
与方法一机制独立：基线来自「同一时刻跨多天的分布」而非邻域窗口——
对昼夜周期免疫，抓水平漂移/长plateau/突发大跌大涨。
v1(24h慢基线)昼夜周期误报过多(65段)被否；v2全局MAD被深谷异常污染(scale=7.83,阈值31.3)高值漂移漏检；
v3=迭代剔除>3.5*scale的异常点后重估MAD(2轮),k=3.5。
输出: evidence/s3_method2_points.csv, s3_method2_segments.json, s3_method2_summary.txt
"""
import pandas as pd
import numpy as np
import json

DATA = "<实验根目录>/ab-v3/datasets/nab_machine_temp.csv"
OUT = "<实验根目录>/ab-v4/P-B/D3-interrupt/evidence/"

TOD_HALFWIN = 3         # 同时刻 ±3 点(±15min) 跨天邻域
RESID_K = 3.5           # 残差超限倍数
GAP_MERGE = 6           # 区段合并间隔 30 分钟
WEAK_SINGLE = 6.0       # 单点区段: max|resid| < WEAK_SINGLE*scale 则视为弱单点剔除

df = pd.read_csv(DATA)
df["timestamp"] = pd.to_datetime(df["timestamp"])
v = df["value"].astype(float)
tod = df["timestamp"].dt.hour * 60 + df["timestamp"].dt.minute  # 分钟 of day

# 季节基线：每行的基线 = time-of-day 在 [tod-15, tod+15] 内所有样本的中位数
tod_vals = tod.values
v_vals = v.values
n = len(df)
baseline = np.empty(n)
lo = tod_vals - TOD_HALFWIN * 5
hi = tod_vals + TOD_HALFWIN * 5
# 用排序后的 (tod, value) 数组做范围查询
order = np.argsort(tod_vals, kind="stable")
tod_sorted = tod_vals[order]
v_sorted = v_vals[order]
for i in range(n):
    l = np.searchsorted(tod_sorted, lo[i], side="left")
    r = np.searchsorted(tod_sorted, hi[i], side="right")
    baseline[i] = np.median(v_sorted[l:r])

resid = v_vals - baseline
# v3: 迭代清理 MAD——把大异常点从尺度估计中剔除后重估(2轮)
rmed0 = np.median(resid)
rmad = float(np.median(np.abs(resid - rmed0)))
scale = 1.4826 * rmad
iters = []
for _ in range(2):
    keep = np.abs(resid - rmed0) <= 3.5 * scale
    rmed0 = np.median(resid[keep])
    rmad = float(np.median(np.abs(resid[keep] - rmed0)))
    scale = 1.4826 * rmad
    iters.append(f"keep={keep.sum()}/{n}, MAD={rmad:.4f}, scale={scale:.4f}")
print(f"迭代清理: {'; '.join(iters)}")
print(f"残差 MAD={rmad:.4f}, scale={scale:.4f}, 阈值=±{RESID_K*scale:.4f}")

anom = np.abs(resid) > RESID_K * scale
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
n_dropped = 0
for s, e in segments:
    seg_v = v_vals[s:e+1]
    seg_r = resid[s:e+1]
    npts = e - s + 1
    max_abs_r = float(np.abs(seg_r).max())
    if npts == 1 and max_abs_r < WEAK_SINGLE * scale:
        n_dropped += 1
        continue
    peak_i = s + int(np.argmax(seg_v))
    trough_i = s + int(np.argmin(seg_v))
    seg_records.append({
        "start": str(df["timestamp"].iloc[s]),
        "end": str(df["timestamp"].iloc[e]),
        "n_points": int(npts),
        "peak": float(seg_v.max()), "peak_at": str(df["timestamp"].iloc[peak_i]),
        "trough": float(seg_v.min()), "trough_at": str(df["timestamp"].iloc[trough_i]),
        "max_abs_resid": max_abs_r,
        "mean_resid": float(seg_r.mean()),
    })

pd.DataFrame({
    "timestamp": df["timestamp"][anom_idx].values,
    "value": v_vals[anom_idx],
    "resid": resid[anom_idx],
}).to_csv(OUT + "s3_method2_points.csv", index=False)

with open(OUT + "s3_method2_segments.json", "w", encoding="utf-8") as f:
    json.dump({"params": {"tod_halfwin_points": TOD_HALFWIN, "resid_k": RESID_K,
                          "gap_merge_points": GAP_MERGE, "weak_single_cut": f"{WEAK_SINGLE}*scale",
                          "mad_clean_iters": iters,
                          "resid_mad": rmad, "threshold_abs_resid": RESID_K * scale},
               "n_anomaly_points": len(anom_idx), "n_weak_single_dropped": n_dropped,
               "n_segments": len(seg_records),
               "segments": seg_records}, f, ensure_ascii=False, indent=2)

lines = []
lines.append("=== 阶段3 方法二 v3：季节基线(time-of-day) + 迭代清理MAD ===")
lines.append("v1 否决: 24h慢基线昼夜周期误报65段; v2 否决: 全局MAD被深谷污染阈值31.3过高,高值漂移漏检")
lines.append(f"v3 参数: tod_halfwin={TOD_HALFWIN}点(±15min跨天邻域), resid_k={RESID_K}, 迭代清理2轮(剔>3.5*scale重估)")
lines.append(f"最终 resid_MAD={rmad:.4f}, scale={scale:.4f}, 阈值=±{RESID_K*scale:.4f}, 弱单点剔除<{WEAK_SINGLE*scale:.2f}")
lines.append(f"异常点: {len(anom_idx)} 个; 剔除弱单点: {n_dropped} 个; 区段: {len(seg_records)} 个")
for r in seg_records:
    lines.append(f"  [{r['start']} ~ {r['end']}] n={r['n_points']} peak={r['peak']:.2f}@{r['peak_at']} trough={r['trough']:.2f}@{r['trough_at']} max|resid|={r['max_abs_resid']:.2f} mean={r['mean_resid']:.2f}")
txt = "\n".join(lines)
with open(OUT + "s3_method2_summary.txt", "w", encoding="utf-8") as f:
    f.write(txt)
print(txt)
