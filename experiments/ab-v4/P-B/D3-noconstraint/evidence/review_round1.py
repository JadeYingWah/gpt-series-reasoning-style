# -*- coding: utf-8 -*-
"""第 1 轮循环审查：数据准确性抽查——独立重算每个报告区间的极值并与报告值比对"""
import pandas as pd
import numpy as np
import os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
df = pd.read_csv("<实验根目录>/ab-v3/datasets/nab_machine_temp.csv", parse_dates=["timestamp"])
df = df.drop_duplicates(subset="timestamp", keep="first").sort_values("timestamp").reset_index(drop=True)
ts, s = df["timestamp"], df["value"].astype(float)

m = pd.read_csv(f"{BASE}/merged_intervals.csv")
bad = 0
for i, r in m.iterrows():
    a = pd.Timestamp(r["start"]); b = pd.Timestamp(r["end"])
    assert a < b, f"row {i}: start>=end"
    span = s[(ts >= a - pd.Timedelta(minutes=5)) & (ts <= b + pd.Timedelta(minutes=5))]
    pk, tr = float(span.max()), float(span.min())
    ok_peak = pd.isna(r["peak"]) or abs(pk - r["peak"]) < 0.01
    ok_trough = pd.isna(r["trough"]) or abs(tr - r["trough"]) < 0.01
    if not (ok_peak and ok_trough):
        bad += 1
        print(f"MISMATCH row {i+1} {r['start']}: report peak={r['peak']} trough={r['trough']} | recomputed {pk:.3f}/{tr:.3f}")
    # 时间都在数据范围内
    assert a >= ts.min() and b <= ts.max(), f"row {i}: out of range"
print(f"区间极值复核: {len(m)-bad}/{len(m)} 一致; 时间边界与范围检查通过")
sys.exit(1 if bad else 0)
