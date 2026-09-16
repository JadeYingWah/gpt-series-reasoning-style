# -*- coding: utf-8 -*-
"""
独立复算交叉验证（与检测脚本不同的代码路径）：
1. 从 10_flags_per_path.csv 重建检出点集合 → 独立重跑合并逻辑（GAP=6, PAD=2）→ 与 10_intervals_full.csv 比对
2. 从原始 CSV 独立重算每个区间的 peak/trough/极值时间 → 与区间表比对
3. 验证高置信子集 = n_methods>=2
4. 验证报告时间格式与数据一致、区间不越界
"""
import pandas as pd
import numpy as np
import json

DATA = "<实验根目录>/ab-v3/datasets/nab_machine_temp.csv"
EV = "<实验根目录>/ab-v4/P-B/D3-fullreport/evidence"
OUT = f"{EV}/25_crosscheck.json"

df = pd.read_csv(DATA)
flags = pd.read_csv(f"{EV}/10_flags_per_path.csv")
iv = pd.read_csv(f"{EV}/10_intervals_full.csv")
hc = pd.read_csv(f"{EV}/10_intervals_highconf.csv")

checks = {}

# 1) 从 per-path 检出点独立重建区间
union = sorted(flags["row"].unique().tolist())
GAP, PAD = 6, 2
groups = []
for i in union:
    if groups and i - groups[-1][-1] <= GAP:
        groups[-1].append(i)
    else:
        groups.append([i])
rebuilt = []
for g in groups:
    lo, hi = max(0, g[0] - PAD), min(len(df) - 1, g[-1] + PAD)
    methods = sorted(set(flags[flags["row"].isin(g)]["path"]))
    rebuilt.append({"start_row": lo, "end_row": hi, "n_methods": len(methods)})
rebuilt_df = pd.DataFrame(rebuilt)

match = (len(rebuilt_df) == len(iv) and
         (rebuilt_df["start_row"].values == iv["start_row"].values).all() and
         (rebuilt_df["end_row"].values == iv["end_row"].values).all() and
         (rebuilt_df["n_methods"].values == iv["n_methods"].values).all())
checks["intervals_rebuild_match"] = bool(match)
checks["n_intervals"] = int(len(iv))

# 2) 独立重算每个区间的极值
v = df["value"].astype(float)
errs = []
for _, r in iv.iterrows():
    seg = v.iloc[int(r["start_row"]):int(r["end_row"]) + 1]
    if abs(float(seg.max()) - float(r["peak_value"])) > 1e-9:
        errs.append(f"row {r['start_row']}: peak mismatch {seg.max()} vs {r['peak_value']}")
    if abs(float(seg.min()) - float(r["trough_value"])) > 1e-9:
        errs.append(f"row {r['start_row']}: trough mismatch {seg.min()} vs {r['trough_value']}")
    extreme_val = float(seg.max()) if r["extreme_type"] == "peak" else float(seg.min())
    if abs(extreme_val - float(r["extreme_value"])) > 1e-9:
        errs.append(f"row {r['start_row']}: extreme mismatch")
    # 时间戳与数据一致
    if df["timestamp"].iloc[int(r["start_row"])] != r["start_time"]:
        errs.append(f"row {r['start_row']}: start_time mismatch")
    if df["timestamp"].iloc[int(r["end_row"])] != r["end_time"]:
        errs.append(f"row {r['start_row']}: end_time mismatch")
    # 极值时间落在区间内
    et = pd.Timestamp(r["extreme_time"])
    st, en = pd.Timestamp(r["start_time"]), pd.Timestamp(r["end_time"])
    if not (st <= et <= en):
        errs.append(f"row {r['start_row']}: extreme_time outside interval")
checks["extreme_and_time_errors"] = errs
checks["extreme_and_time_all_ok"] = len(errs) == 0

# 3) 高置信子集一致性
checks["highconf_match"] = bool(
    len(hc) == int((iv["n_methods"] >= 2).sum()) and
    (hc["start_row"].values == iv[iv["n_methods"] >= 2]["start_row"].values).all())

# 4) 格式与越界
fmt_ok = all(df["timestamp"].iloc[0] == iv["start_time"].min() or True for _ in [0])
bounds_ok = bool((iv["start_row"] >= 0).all() and (iv["end_row"] < len(df)).all())
checks["rows_in_bounds"] = bounds_ok
# 时间格式与数据原始格式一致（正则）
import re
pat = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")
fmt_ok = bool(iv["start_time"].map(lambda s: bool(pat.match(str(s)))).all() and
              iv["end_time"].map(lambda s: bool(pat.match(str(s)))).all())
checks["time_format_matches_data"] = fmt_ok

# 5) 主报告区间总覆盖率（信息性）
covered = sum(int(r["end_row"]) - int(r["start_row"]) + 1 for _, r in iv.iterrows())
checks["covered_points"] = int(covered)
checks["coverage_ratio"] = round(covered / len(df), 4)

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(checks, f, ensure_ascii=False, indent=2)
print(json.dumps(checks, ensure_ascii=False, indent=2))
