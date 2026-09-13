# -*- coding: utf-8 -*-
"""阶段4 交叉验证与保守合并（D3-interrupt）
四个检测结果矩阵比对（3 个独立机制）：
  M1 = 方法一 滚动鲁棒Z（loose z3.5 检出即算 M1 票, strict z5 为其强子集）
  M2 = 方法二 季节基线残差 v3
  M3 = 方法三 全局分位包络
保守度调节规则（可检查,依据 s5b 日中位数诊断: 正常带80~100,深谷/高位日之后均回归）：
  主报告准入 R1: 簇获得 >=2 个独立机制票
  主报告准入 R2: 单机制票, 但簇内偏离全局中位数 > 4*全局MAD(21.2) 的点数 >= 6（持续>=30min 的深偏离）
  主报告准入 R3: 单一 M3 票, 且簇内 M3 包络越界点数 >= 6（持续>=30min 超出 P0.5/P99.5 值域）
  其余 -> 附录候选
输出: evidence/s5_clusters.json, s5_crossvalidate_summary.txt
"""
import pandas as pd
import numpy as np
import json

DATA = "<实验根目录>/ab-v3/datasets/nab_machine_temp.csv"
OUT = "<实验根目录>/ab-v4/P-B/D3-interrupt/evidence/"
GAP = pd.Timedelta(minutes=30)

df = pd.read_csv(DATA)
df["timestamp"] = pd.to_datetime(df["timestamp"])
ts = df["timestamp"]
v = df["value"].astype(float)
global_med = float(v.median())
global_mad = float(np.median(np.abs(v - global_med)))

def load_segs(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)["segments"]

m1s = load_segs(OUT + "s2_method1_segments_strict.json")
m1l = load_segs(OUT + "s2_method1_segments_loose.json")
m2  = load_segs(OUT + "s3_method2_segments.json")
m3  = load_segs(OUT + "s4_method3_segments.json")

def ns(seg):
    return (pd.Timestamp(seg["start"]).value, pd.Timestamp(seg["end"]).value)

# 簇 = 区间并集（间隙 <= 30min 合并）；每簇记录机制票
events = []  # (mech, start, end, seg)
for mech, segs in (("M1", m1l), ("M2", m2), ("M3", m3)):
    for s in segs:
        a, b = ns(s)
        events.append((mech, a, b, s))
events.sort(key=lambda e: e[1])

clusters = []
for mech, a, b, seg in events:
    if clusters and a <= clusters[-1]["end"] + GAP.value:
        c = clusters[-1]
        c["end"] = max(c["end"], b)
        c["mechs"].add(mech)
        c["members"].append((mech, seg))
    else:
        clusters.append({"start": a, "end": b, "mechs": {mech}, "members": [(mech, seg)]})

ts_ns = df["timestamp"].astype("datetime64[ns]").astype("int64").values  # ns since epoch（非严格递增,含1处回退）
records = []
for c in clusters:
    idx = np.where((ts_ns >= c["start"]) & (ts_ns <= c["end"]))[0]
    i0, i1 = int(idx[0]), int(idx[-1])
    seg_v = v.iloc[i0:i1+1]
    peak_i = i0 + int(np.argmax(seg_v.values))
    trough_i = i0 + int(np.argmin(seg_v.values))
    dev = float((seg_v - global_med).abs().max())
    n_dev_gt_4mad = int(((seg_v - global_med).abs() > 4 * global_mad).sum())
    m3_pts = sum(int(seg.get("n_points", 0)) for m, seg in c["members"] if m == "M3")
    mechs = sorted(c["mechs"])
    n_mech = len(mechs)
    m1_strict = any(seg.get("max_abs_z", 0) > 5.0 for m, seg in c["members"] if m == "M1")
    # 保守准入判定
    r1 = n_mech >= 2
    r2 = (n_mech == 1) and n_dev_gt_4mad >= 6
    r3 = (mechs == ["M3"]) and m3_pts >= 6
    rule = "R1" if r1 else ("R2" if r2 else ("R3" if r3 else "-"))
    records.append({
        "start": str(ts.iloc[i0]), "end": str(ts.iloc[i1]),
        "n_points": int(i1 - i0 + 1),
        "peak": float(seg_v.max()), "peak_at": str(ts.iloc[peak_i]),
        "trough": float(seg_v.min()), "trough_at": str(ts.iloc[trough_i]),
        "mechs": mechs, "m1_strict": bool(m1_strict),
        "max_dev_from_median": round(dev, 2),
        "n_points_dev_gt_4mad": n_dev_gt_4mad,
        "m3_envelope_points": m3_pts,
        "main_report": bool(r1 or r2 or r3), "rule": rule,
    })

main = [r for r in records if r["main_report"]]
cand = [r for r in records if not r["main_report"]]

with open(OUT + "s5_clusters.json", "w", encoding="utf-8") as f:
    json.dump({"global_median": global_med, "global_mad": global_mad,
               "n_clusters": len(records),
               "main_report_segments": main, "candidate_segments": cand}, f, ensure_ascii=False, indent=2)

lines = []
lines.append("=== 阶段4 交叉验证与保守合并 ===")
lines.append(f"全局 median={global_med:.4f}, MAD={global_mad:.4f}, 3*MAD={3*global_mad:.4f}")
lines.append(f"簇总数: {len(records)}; 主报告: {len(main)}; 附录候选: {len(cand)}")
lines.append("")
lines.append("--- 主报告区段 ---")
for r in main:
    lines.append(f"  [{r['start']} ~ {r['end']}] n={r['n_points']} peak={r['peak']:.2f}@{r['peak_at']} trough={r['trough']:.2f}@{r['trough_at']} mechs={','.join(r['mechs'])}({'strict' if r['m1_strict'] else 'loose' if 'M1' in r['mechs'] else '-'}) rule={r['rule']} maxdev={r['max_dev_from_median']}")
lines.append("")
lines.append("--- 附录候选 ---")
for r in cand:
    lines.append(f"  [{r['start']} ~ {r['end']}] n={r['n_points']} peak={r['peak']:.2f} trough={r['trough']:.2f} mechs={','.join(r['mechs'])} maxdev={r['max_dev_from_median']}")
txt = "\n".join(lines)
with open(OUT + "s5_crossvalidate_summary.txt", "w", encoding="utf-8") as f:
    f.write(txt)
print(txt)
