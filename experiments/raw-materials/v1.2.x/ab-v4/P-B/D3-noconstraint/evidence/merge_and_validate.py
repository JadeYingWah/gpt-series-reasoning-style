# -*- coding: utf-8 -*-
"""合并与交叉验证：三方法区间取并集（跨方法重叠或间隔≤60min 合并），
每个合并区间标注贡献方法与确认数；输出点级 Jaccard 与区间级互相印证矩阵。
本臂为 no-constraint：合并结果全部进主报告，不做保守筛选。
输出: merged_intervals.csv, cross_validation.json, cross_validation.md
"""
import pandas as pd
import numpy as np
import json, os

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = "<实验根目录>/ab-v3/datasets/nab_machine_temp.csv"
MERGE_GAP_MIN = 60   # 跨方法合并容差（分钟）：可弥合方法边界差(各PAD=10min)，不黏连相邻独立事件

df = pd.read_csv(DATA, parse_dates=["timestamp"])
# 数据质量处置：原始文件含 12 行重复时间戳(2014-01-07 02:00-02:55, 两份值略异, 差≤1.9°C)
# 及 1 处乱序块 —— 统一保留首次出现并按时间稳定排序（详见 data_quality.md）
df = df.drop_duplicates(subset="timestamp", keep="first").sort_values("timestamp", kind="stable").reset_index(drop=True)
s = df["value"].astype(float)
ts = df["timestamp"]

def load(m):
    d = pd.read_csv(f"{BASE}/{m}_intervals.csv", parse_dates=["start", "end"])
    d["method"] = m
    return d

m1, m2, m3 = load("m1"), load("m2"), load("m3")
methods = {"m1": m1, "m2": m2, "m3": m3}

# ---- 区间级并集合并 ----
pool = pd.concat([m1, m2, m3], ignore_index=True).sort_values("start").reset_index(drop=True)
merged = []
cur = {"start": pool["start"][0], "end": pool["end"][0], "methods": {pool["method"][0]}}
for i in range(1, len(pool)):
    r = pool.iloc[i]
    if r["start"] <= cur["end"] + pd.Timedelta(minutes=MERGE_GAP_MIN):
        cur["end"] = max(cur["end"], r["end"])
        cur["methods"].add(r["method"])
    else:
        merged.append(cur)
        cur = {"start": r["start"], "end": r["end"], "methods": {r["method"]}}
merged.append(cur)

rows = []
for c in merged:
    span = (ts >= c["start"] - pd.Timedelta(minutes=5)) & (ts <= c["end"] + pd.Timedelta(minutes=5))
    vals = s[span]
    peak, trough = float(vals.max()), float(vals.min())
    # kind 双参照规则：ref_d=开始前 24h~2h（前一天常态），ref_r=开始前 2h~30min（起坡前临近水平），
    # 各算 dev_hi/dev_lo，取跨参照最大偏差定方向（避免长 depression 内 ref 被事件自身污染）
    pre_d = s[(ts >= c["start"] - pd.Timedelta(hours=24, minutes=30)) & (ts <= c["start"] - pd.Timedelta(hours=2))]
    pre_r = s[(ts >= c["start"] - pd.Timedelta(hours=2)) & (ts <= c["start"] - pd.Timedelta(minutes=30))]
    ref_d = float(pre_d.median()) if len(pre_d) >= 3 else float(s.median())
    ref_r = float(pre_r.median()) if len(pre_r) >= 3 else ref_d
    dev_hi = max(peak - ref_d, peak - ref_r)
    dev_lo = max(ref_d - trough, ref_r - trough)
    kind = "spike" if dev_hi >= dev_lo else "trough"
    ms = sorted(c["methods"])
    rows.append({
        "start": c["start"].strftime("%Y-%m-%d %H:%M:%S"),
        "end": c["end"].strftime("%Y-%m-%d %H:%M:%S"),
        "kind": kind,
        "peak": round(peak, 3) if kind == "spike" else "",
        "trough": round(trough, 3) if kind == "trough" else "",
        "duration_min": int((c["end"] - c["start"]).total_seconds() // 60) + 5,
        "methods_confirmed": "+".join(ms),
        "n_methods": len(ms),
    })
mdf = pd.DataFrame(rows)
mdf.to_csv(f"{BASE}/merged_intervals.csv", index=False)

# ---- 点级一致性 ----
def points(m):
    d = pd.read_csv(f"{BASE}/{m}_scores.csv")
    return set(np.flatnonzero(d["anom"].values.astype(bool)))

P = {m: points(m) for m in methods}
def jac(a, b):
    inter = len(P[a] & P[b]); uni = len(P[a] | P[b])
    return round(inter / uni, 4) if uni else 0.0
def shared_intervals(ma, mb):
    A = methods[ma]; B = methods[mb]; n = 0
    for _, a in A.iterrows():
        if ((B["start"] <= a["end"]) & (B["end"] >= a["start"])).any():
            n += 1
    return n

pair_stats = {}
for a, b in [("m1", "m2"), ("m1", "m3"), ("m2", "m3")]:
    pair_stats[f"{a}-{b}"] = {
        "point_jaccard": jac(a, b),
        "point_intersection": len(P[a] & P[b]),
        f"{a}_points": len(P[a]), f"{b}_points": len(P[b]),
        f"{a}_intervals_confirmed_by_{b}": shared_intervals(a, b),
        f"{b}_intervals_confirmed_by_{a}": shared_intervals(b, a),
        f"{a}_n_intervals": len(methods[a]), f"{b}_n_intervals": len(methods[b]),
    }

summary = {
    "merge_rule": f"union of m1/m2/m3 intervals; merge when overlap or gap<={MERGE_GAP_MIN}min",
    "n_intervals_per_method": {m: len(methods[m]) for m in methods},
    "n_anom_points_per_method": {m: len(P[m]) for m in methods},
    "n_merged_intervals": len(mdf),
    "n_confirmed_by_ge2": int((mdf["n_methods"] >= 2).sum()),
    "n_single_method": int((mdf["n_methods"] == 1).sum()),
    "pairwise": pair_stats,
}
json.dump(summary, open(f"{BASE}/cross_validation.json", "w"), indent=2, ensure_ascii=False)

# ---- 人类可读交叉验证报告 ----
lines = ["# 多路径交叉验证证据\n",
         "## 方法间点级一致性（Jaccard / 印证数）\n",
         "| 方法对 | 点级Jaccard | 点交集 | 区间互相印证 |\n|---|---|---|---|"]
for k, v in pair_stats.items():
    a, b = k.split("-")
    lines.append(f"| {a} vs {b} | {v['point_jaccard']} | {v['point_intersection']} | "
                 f"{a}:{v[f'{a}_intervals_confirmed_by_{b}']}/{v[f'{a}_n_intervals']} 被{b}印证; "
                 f"{b}:{v[f'{b}_intervals_confirmed_by_{a}']}/{v[f'{b}_n_intervals']} 被{a}印证 |")
lines.append(f"\n## 合并结果\n- 合并后区间数: {len(mdf)}（≥2 方法确认: {summary['n_confirmed_by_ge2']}, 仅单方法: {summary['n_single_method']}）")
lines.append("- 合并规则: 跨方法区间重叠或间隔≤60min 则合并（无保守筛选，全部区间进主报告）")
lines.append("\n## 各合并区间的方法确认情况\n")
cols = list(mdf.columns)
lines.append("| " + " | ".join(cols) + " |")
lines.append("|" + "---|" * len(cols))
for _, r in mdf.iterrows():
    lines.append("| " + " | ".join(str(r[c]) for c in cols) + " |")
open(f"{BASE}/cross_validation.md", "w", encoding="utf-8").write("\n".join(lines) + "\n")

print(json.dumps(summary, indent=2, ensure_ascii=False)[:2000])
print("merged intervals:", len(mdf))
print(mdf.to_string(index=False))
