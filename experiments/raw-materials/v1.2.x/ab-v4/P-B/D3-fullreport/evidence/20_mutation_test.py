# -*- coding: utf-8 -*-
"""
变异测试（鉴别力验证）：把「要防的错误」真实做一次，验证各检测路径会红。
在 4 段人工核验的干净对照区间中心注入合成异常：
  M1 单点尖峰 +40  → 预期 ≥1 条路径命中（D/A）
  M2 单点凹陷 -40  → 预期 ≥1 条路径命中（D/A）
  M3 6 点阶跃 -25  → 预期 ≥1 条路径命中（B/D）
  M0 对照（不注入）→ 统计误报基线
回答：这套检测若失效/阈值错设，本测试会不会红？——会。
"""
import pandas as pd
import numpy as np
import json

DATA = "<实验根目录>/ab-v3/datasets/nab_machine_temp.csv"
OUT = "<实验根目录>/ab-v4/P-B/D3-fullreport/evidence/20_mutation_test.json"

df = pd.read_csv(DATA)
ts = pd.to_datetime(df["timestamp"])

# 干净对照区间（人工核查：远离已知大幅波动区段，值域 70~95 平稳）
stretches = {
    "S1": ("2014-01-08 00:00:00", "2014-01-08 12:00:00"),
    "S2": ("2013-12-13 00:00:00", "2013-12-13 12:00:00"),
    "S3": ("2014-02-01 00:00:00", "2014-02-01 12:00:00"),
    "S4": ("2014-01-10 00:00:00", "2014-01-10 12:00:00"),
}


def run_paths(v):
    """与 10_multipath_detect.py 相同的 4 路径逻辑（独立复制以便自包含验证）"""
    n = len(v)
    v = pd.Series(v)
    medA = v.median(); madA = (v - medA).abs().median()
    zA = (v - medA).abs() / (1.4826 * madA)
    flagA = set(v.index[zA > 5.0])
    W = 72
    medB = v.rolling(W, center=True, min_periods=36).median()
    q1 = v.rolling(W, center=True, min_periods=36).quantile(0.25)
    q3 = v.rolling(W, center=True, min_periods=36).quantile(0.75)
    sigB = ((q3 - q1) / 1.349).replace(0, np.nan)
    zB = (v - medB).abs() / sigB
    flagB = set(v.index[(zB > 4.5).fillna(False)])
    P = 288
    trend = v.rolling(P, center=True, min_periods=P // 2).median()
    tod = pd.to_datetime(df["timestamp"]).dt.strftime("%H:%M")
    seasonal = (v - trend).groupby(tod.values).transform("median")
    residC = (v - trend - seasonal).fillna(v - v.median())
    madC = (residC - residC.median()).abs().median()
    zC = (residC - residC.median()).abs() / (1.4826 * madC)
    flagC = set(v.index[zC > 4.5])
    d1 = v.diff()
    madd = (d1 - d1.median()).abs().median()
    zD = (d1 - d1.median()).abs() / (1.4826 * madd)
    flagD = set(v.index[(zD > 6.0).fillna(False)])
    return {"A": flagA, "B": flagB, "C": flagC, "D": flagD}


def _put(arr, c, val):
    arr[c:c + (len(val) if hasattr(val, "__len__") else 1)] = val
    return arr


results = {}
for sname, (t0, t1) in stretches.items():
    i0, i1 = ts.searchsorted(pd.Timestamp(t0)), ts.searchsorted(pd.Timestamp(t1))
    base = df["value"].astype(float).copy().values
    center = (i0 + i1) // 2
    seg = {}
    for mut, mutate in [("M0_ctrl", lambda arr, c: arr),
                        ("M1_spike+40", lambda arr, c: _put(arr, c, arr[c] + 40)),
                        ("M2_dip-40", lambda arr, c: _put(arr, c, arr[c] - 40)),
                        ("M3_step-25x6", lambda arr, c: _put(arr, c, arr[c:c + 6] - 25))]:
        arr = base.copy()
        arr = mutate(arr, center)
        flags = run_paths(arr)
        hit_center = {p: int(center in s or (center + 1 in s) or (center - 1 in s) or
                             any(center <= i <= center + 6 for i in s))
                      for p, s in flags.items()}
        seg[mut] = {"any_hit": any(hit_center.values()), "per_path": hit_center,
                    "n_flagged_total": {p: len(s) for p, s in flags.items()}}
    results[sname] = {"window": [t0, t1], "center_row": int(center), "tests": seg}


# 汇总判定
verdict = {
    "M1_spike_detected_all_stretches": all(results[s]["tests"]["M1_spike+40"]["any_hit"] for s in stretches),
    "M2_dip_detected_all_stretches": all(results[s]["tests"]["M2_dip-40"]["any_hit"] for s in stretches),
    "M3_step_detected_all_stretches": all(results[s]["tests"]["M3_step-25x6"]["any_hit"] for s in stretches),
    "M0_ctrl_false_positive_stretches": [s for s in stretches if results[s]["tests"]["M0_ctrl"]["any_hit"]],
}
results["VERDICT"] = verdict
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2, default=str)
print(json.dumps(verdict, ensure_ascii=False, indent=2))
for s in stretches:
    for m in ["M0_ctrl", "M1_spike+40", "M2_dip-40", "M3_step-25x6"]:
        print(s, m, results[s]["tests"][m]["any_hit"], results[s]["tests"][m]["per_path"])
