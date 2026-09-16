# -*- coding: utf-8 -*-
"""
保守度裁决 + 交叉验证对照。
输入: points_m{1,2}[,_m3,_m4]_{strict,loose}.csv（存在哪个读哪个）
区段化: 同方法同档内，相邻异常点时间间隔 <= 60min 合并为一个区段。
主报告（最保守）: strict 档下被 >=2 独立方法检出（区段时间轴重叠）。
附录候选: strict 档仅 1 方法、或仅 loose 档检出的区段。
输出: segments_per_method.json, consensus_result.json, crosscheck_table.csv
"""
import pandas as pd, numpy as np, json, glob, os

MERGE_GAP = pd.Timedelta(minutes=60)

def load_points(path):
    df = pd.read_csv(path, parse_dates=["timestamp"])
    return df.sort_values("timestamp").reset_index(drop=True)

def to_segments(pts):
    """点 -> 区段 [{start,end,n_pts,min_value,max_value}]"""
    segs = []
    if len(pts) == 0:
        return segs
    start = prev = pts['timestamp'].iloc[0]
    cur = [0]
    for i in range(1, len(pts)):
        t = pts['timestamp'].iloc[i]
        if t - prev <= MERGE_GAP:
            cur.append(i)
        else:
            segs.append(cur); cur = [i]
        prev = t
    segs.append(cur)
    out = []
    for c in segs:
        sub = pts.iloc[c]
        out.append({
            "start": str(sub['timestamp'].iloc[0]),
            "end": str(sub['timestamp'].iloc[-1]),
            "n_pts": int(len(sub)),
            "min_value": float(sub['value'].min()),
            "max_value": float(sub['value'].max()),
        })
    return out

# 读入所有方法×档位点
files = {}
for tag in ["m1_strict", "m1_loose", "m2_strict", "m2_loose", "m3_strict", "m3_loose", "m4_strict", "m4_loose"]:
    p = f"points_{tag}.csv"
    if os.path.exists(p):
        files[tag] = load_points(p)

methods = sorted(set(t.rsplit("_", 1)[0] for t in files))
segs = {tag: to_segments(df) for tag, df in files.items()}
json.dump(segs, open("segments_per_method.json", "w"), indent=2)

def overlaps(a, b):
    return (pd.Timestamp(a["start"]) <= pd.Timestamp(b["end"])) and (pd.Timestamp(b["start"]) <= pd.Timestamp(a["end"]))

def group_consensus(seg_list, min_methods):
    """把各方法区段按时间重叠聚类，返回 >=min_methods 方法支持的组"""
    allsegs = []
    for tag, lst in seg_list.items():
        for s in lst:
            allsegs.append({**s, "method": tag})
    allsegs.sort(key=lambda s: pd.Timestamp(s["start"]))
    groups = []
    for s in allsegs:
        placed = False
        for g in groups:
            if any(overlaps(s, gs) for gs in g):
                g.append(s); placed = True; break
        if not placed:
            groups.append([s])
    # 迭代合并（组间可能因排序漏合）
    changed = True
    while changed:
        changed = False
        for i in range(len(groups)):
            for j in range(i + 1, len(groups)):
                if any(overlaps(a, b) for a in groups[i] for b in groups[j]):
                    groups[i].extend(groups[j]); del groups[j]; changed = True; break
            if changed: break
    out = []
    for g in groups:
        ms = set(s["method"].rsplit("_", 1)[0] for s in g)
        out.append({
            "start": min(s["start"] for s in g),
            "end": max(s["end"] for s in g),
            "methods_strict": sorted(set(s["method"] for s in g if s["method"].endswith("strict"))),
            "methods_loose_only": sorted(set(s["method"] for s in g) - set(s["method"] for s in g if s["method"].endswith("strict"))),
            "n_methods": len(ms),
            "min_value": min(s["min_value"] for s in g),
            "max_value": max(s["max_value"] for s in g),
        })
    return out

strict_segs = {t: s for t, s in segs.items() if t.endswith("strict")}
loose_segs = {t: s for t, s in segs.items() if t.endswith("loose")}
all_strict_groups = group_consensus(strict_segs, 1)

primary, appendix = [], []
for g in all_strict_groups:
    if g["n_methods"] >= 2:
        primary.append(g)
    else:
        appendix.append({**g, "reason": "strict 档仅 1 方法检出"})

# loose 档中未被任何 strict 组覆盖的候选
for tag, lst in loose_segs.items():
    for s in lst:
        covered = any(overlaps(s, g) for g in all_strict_groups)
        if not covered:
            appendix.append({**s, "reason": f"仅 {tag} (loose 档) 检出"})

json.dump({"primary": primary, "appendix": appendix},
          open("consensus_result.json", "w"), indent=2)

# 对照表
rows = []
for g in all_strict_groups:
    rows.append({"start": g["start"], "end": g["end"], "n_methods": g["n_methods"],
                 "methods": ";".join(g["methods_strict"] + g["methods_loose_only"]),
                 "min_value": round(g["min_value"], 2), "max_value": round(g["max_value"], 2),
                 "verdict": "PRIMARY" if g["n_methods"] >= 2 else "APPENDIX"})
pd.DataFrame(rows).to_csv("crosscheck_table.csv", index=False)
print("PRIMARY:", json.dumps(primary, indent=2))
print("\nAPPENDIX count:", len(appendix))
for a in appendix:
    print(" -", a.get("start"), a.get("end"), a.get("reason", ""))
