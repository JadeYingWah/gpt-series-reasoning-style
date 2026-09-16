# -*- coding: utf-8 -*-
r"""D1-winequality SUB：红酒理化数据集分析
数据：<实验根目录>\ab-v3\datasets\winequality-red.csv（分号分隔、带引号表头、1599 行）
必答：
1) 11 项理化指标与 quality 的 Pearson 相关系数（6 位小数），按 |r| 降序
2) quality 各档位（3~8）样本计数
3) quality>=7 与 quality<=4 两组的 alcohol 均值（4 位小数）及差值
验证：pandas corr 与 numpy 手工 Pearson 公式、scipy.pearsonr 三方互验；
      计数用 value_counts 与布尔求和互验；行数/缺失/重复一并核查。
"""
import csv
import numpy as np
import pandas as pd
from scipy import stats

DATA = r"<实验根目录>\ab-v3\datasets\winequality-red.csv"

# ---------- 加载 ----------
df = pd.read_csv(DATA, sep=";", header=0)
print("shape =", df.shape)
print("columns =", list(df.columns))
print("missing total =", int(df.isna().sum().sum()))
print("duplicated rows =", int(df.duplicated().sum()))

FEATURES = [c for c in df.columns if c != "quality"]
assert len(FEATURES) == 11, FEATURES

# ---------- Q1: Pearson 相关系数（6 位小数，按 |r| 降序） ----------
rows = []
for f in FEATURES:
    r_pd = df[f].corr(df["quality"], method="pearson")          # pandas
    r_np = np.corrcoef(df[f].to_numpy(float), df["quality"].to_numpy(float))[0, 1]  # numpy
    r_sp = stats.pearsonr(df[f].to_numpy(float), df["quality"].to_numpy(float))[0]  # scipy
    # 手工公式（纯 numpy，独立于 corrcoef）
    x = df[f].to_numpy(float); y = df["quality"].to_numpy(float)
    r_man = ((x - x.mean()) * (y - y.mean())).sum() / np.sqrt(((x - x.mean())**2).sum() * ((y - y.mean())**2).sum())
    assert max(abs(r_pd - r_np), abs(r_pd - r_sp), abs(r_pd - r_man)) < 1e-12, f
    rows.append((f, r_pd))

rows.sort(key=lambda t: abs(t[1]), reverse=True)
print("\n== Q1 Pearson r with quality (sorted by |r| desc) ==")
q1_lines = []
for f, r in rows:
    q1_lines.append(f"{f}: {r:.6f}")
    print(q1_lines[-1])

# ---------- Q2: quality 各档位计数 ----------
print("\n== Q2 quality counts ==")
vc = df["quality"].value_counts().sort_index()
counts = {int(k): int(v) for k, v in vc.items()}
total = sum(counts.values())
q2_lines = [f"quality={k}: {counts.get(k, 0)}" for k in range(3, 9)]
q2_lines.append(f"total: {total} (rows={len(df)})")
for line in q2_lines:
    print(line)
# 布尔求和独立互验
for k in range(3, 9):
    bs = int((df["quality"] == k).sum())
    assert bs == counts.get(k, 0), k

# ---------- Q3: 高质/低质组 alcohol 均值 ----------
hi = df.loc[df["quality"] >= 7, "alcohol"]
lo = df.loc[df["quality"] <= 4, "alcohol"]
m_hi, m_lo = hi.mean(), lo.mean()
print("\n== Q3 alcohol means ==")
print(f"high(quality>=7): n={len(hi)}, mean={m_hi:.4f}")
print(f"low (quality<=4): n={len(lo)}, mean={m_lo:.4f}")
print(f"difference (high-low): {m_hi - m_lo:.4f}")
# numpy 独立互验
x = df["alcohol"].to_numpy(float); q = df["quality"].to_numpy(float)
assert abs(x[q >= 7].mean() - m_hi) < 1e-12 and abs(x[q <= 4].mean() - m_lo) < 1e-12

print("\nALL CHECKS PASSED")
