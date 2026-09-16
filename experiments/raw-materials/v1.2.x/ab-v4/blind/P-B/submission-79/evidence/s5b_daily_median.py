# -*- coding: utf-8 -*-
"""阶段4b 诊断：日中位数走势（判定 1 月底低值段是真异常还是 regime 漂移）
输出: evidence/s5b_daily_median.txt
"""
import pandas as pd
import numpy as np

DATA = "<实验根目录>/ab-v3/datasets/nab_machine_temp.csv"
OUT = "<实验根目录>/ab-v4/P-B/D3-interrupt/evidence/"

df = pd.read_csv(DATA)
df["timestamp"] = pd.to_datetime(df["timestamp"])
df["date"] = df["timestamp"].dt.date
daily = df.groupby("date")["value"].agg(["median", "mean", "min", "max", "count"])

lines = ["=== 日中位数走势诊断 ==="]
for date, row in daily.iterrows():
    lines.append(f"{date} median={row['median']:7.2f} mean={row['mean']:7.2f} min={row['min']:7.2f} max={row['max']:7.2f} n={row['count']}")
txt = "\n".join(lines)
with open(OUT + "s5b_daily_median.txt", "w", encoding="utf-8") as f:
    f.write(txt)
print(txt)
