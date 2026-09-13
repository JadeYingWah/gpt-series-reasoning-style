# -*- coding: utf-8 -*-
"""阶段1：数据加载与概览（D3-interrupt）
输出: evidence/s1_overview.txt
"""
import pandas as pd
import numpy as np

DATA = "<实验根目录>/ab-v3/datasets/nab_machine_temp.csv"

df = pd.read_csv(DATA)
lines = []
def w(s=""):
    lines.append(str(s))

w("=== 阶段1 数据概览 ===")
w(f"行数: {len(df)}")
w(f"列名: {list(df.columns)}")
w(f"dtypes:\n{df.dtypes}")
w(f"缺失值:\n{df.isna().sum()}")

df["timestamp"] = pd.to_datetime(df["timestamp"])
w(f"时间范围: {df['timestamp'].min()} -> {df['timestamp'].max()}")
dt = df["timestamp"].diff().dt.total_seconds().dropna()
w(f"采样间隔(秒): median={dt.median()}, min={dt.min()}, max={dt.max()}")
w(f"非中位间隔数量: {(dt != dt.median()).sum()}")
if (dt != dt.median()).any():
    idx = dt[dt != dt.median()].index
    w("非中位间隔示例(前10): ")
    for i in idx[:10]:
        w(f"  row {i}: gap={dt[i]}s  between {df['timestamp'].iloc[i-1]} and {df['timestamp'].iloc[i]}")

v = df["value"]
w(f"值统计: min={v.min():.4f} max={v.max():.4f} mean={v.mean():.4f} median={v.median():.4f} std={v.std():.4f}")
med = v.median()
mad = np.median(np.abs(v - med))
w(f"全局 median={med:.4f}, MAD={mad:.4f}")
w(f"全局分位数: 1%={v.quantile(0.01):.3f} 5%={v.quantile(0.05):.3f} 95%={v.quantile(0.95):.3f} 99%={v.quantile(0.99):.3f}")
w(f"重复时间戳数量: {df['timestamp'].duplicated().sum()}")
w(f"值-时间戳排序是否单调: {df['timestamp'].is_monotonic_increasing}")

out = "\n".join(lines)
with open("<实验根目录>/ab-v4/P-B/D3-interrupt/evidence/s1_overview.txt", "w", encoding="utf-8") as f:
    f.write(out)
print(out)
