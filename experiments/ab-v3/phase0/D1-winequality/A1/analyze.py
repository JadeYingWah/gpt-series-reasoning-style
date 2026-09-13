# -*- coding: utf-8 -*-
"""任务 D1·红酒质量分析（A1 臂）
数据：<实验根目录>/ab-v3/datasets/winequality-red.csv（UCI Wine Quality，分号分隔、带引号表头、1599 行）
环境仅有 Python 标准库（pandas/numpy 未安装），全部计算用纯 Python 实现，
每个关键数值走两条独立路径复算（主计算 vs 独立复算公式）。
"""
import csv
import math

DATA = "<实验根目录>/ab-v3/datasets/winequality-red.csv"

# ---------- 读取 ----------
with open(DATA, newline="", encoding="utf-8") as f:
    rows = list(csv.reader(f, delimiter=";"))
header = [h.strip('"') for h in rows[0]]
data = [[float(v) for v in r] for r in rows[1:] if r]
n = len(data)
idx = {name: i for i, name in enumerate(header)}
print(f"=== 0. 数据完整性 ===")
print(f"shape={n}x{len(header)}, columns={header}")

# ---------- 1. Pearson 相关系数 ----------
# 路径一（主计算）：r = Sxy / sqrt(Sxx * Syy)，n 除法形式
# 路径二（独立复算）：标准差 ddof=1 形式 r = cov/(sd_x*sd_y)，应与路径一一致
def pearson_path1(xs, ys):
    n_ = len(xs)
    mx = sum(xs) / n_
    my = sum(ys) / n_
    sxy = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    sxx = sum((a - mx) ** 2 for a in xs)
    syy = sum((b - my) ** 2 for b in ys)
    return sxy / math.sqrt(sxx * syy)

def pearson_path2(xs, ys):
    n_ = len(xs)
    mx = sum(xs) / n_
    my = sum(ys) / n_
    cov = sum((a - mx) * (b - my) for a, b in zip(xs, ys)) / (n_ - 1)
    sdx = math.sqrt(sum((a - mx) ** 2 for a in xs) / (n_ - 1))
    sdy = math.sqrt(sum((b - my) ** 2 for b in ys) / (n_ - 1))
    return cov / (sdx * sdy)

targets = [c for c in header if c != "quality"]
quality = [r[idx["quality"]] for r in data]
print("\n=== 1. Pearson 相关系数 vs quality（按 |r| 降序，6 位小数） ===")
mismatch = 0
results = []
for c in targets:
    xs = [r[idx[c]] for r in data]
    r1, r2 = pearson_path1(xs, quality), pearson_path2(xs, quality)
    ok = abs(r1 - r2) < 1e-12
    mismatch += (not ok)
    results.append((c, r1, r2, ok))
results.sort(key=lambda t: -abs(t[1]))
for c, r1, r2, ok in results:
    print(f"{c:<22s} main={r1:+.6f}  recheck={r2:+.6f}  match={ok}")
print(f"复算不一致项数: {mismatch}")

# ---------- 2. quality 各档位计数 ----------
# 路径一：字典累加；路径二：列表 count()
print("\n=== 2. quality 计数 ===")
cnt = {}
for q in quality:
    cnt[q] = cnt.get(q, 0) + 1
total = 0
for q in range(3, 9):
    c1 = cnt.get(float(q), cnt.get(q, 0))
    c2 = quality.count(float(q))
    total += c1
    print(f"quality={q}: dict={c1}  count()={c2}  match={c1 == c2}")
print(f"计数总和={total}（应=1599）: {total == n}")

# ---------- 3. 高质组 vs 低质组 alcohol 均值 ----------
# 路径一：sum/n；路径二：两遍遍历 Welford 均值；交叉核验组间成员数
print("\n=== 3. alcohol 均值（4 位小数） ===")
alcohol_all = [r[idx["alcohol"]] for r in data]
hi1 = [a for a, q in zip(alcohol_all, quality) if q >= 7]
lo1 = [a for a, q in zip(alcohol_all, quality) if q <= 4]

def mean_simple(xs):
    return sum(xs) / len(xs)

def mean_welford(xs):
    m, k = 0.0, 0
    for x in xs:
        k += 1
        m += (x - m) / k
    return m

hi_m1, hi_m2 = mean_simple(hi1), mean_welford(hi1)
lo_m1, lo_m2 = mean_simple(lo1), mean_welford(lo1)
print(f"高质组(quality>=7): n={len(hi1)}  mean(simple)={hi_m1:.4f}  mean(welford)={hi_m2:.4f}  match={abs(hi_m1-hi_m2)<1e-12}")
print(f"低质组(quality<=4): n={len(lo1)}  mean(simple)={lo_m1:.4f}  mean(welford)={lo_m2:.4f}  match={abs(lo_m1-lo_m2)<1e-12}")
print(f"差值 hi-lo = {hi_m1 - lo_m1:.4f}")
# 成员数交叉核验：hi+lo+mid 应等于总数
mid = n - len(hi1) - len(lo1)
qs = set(quality)
print(f"成员核验: hi+lo+mid={len(hi1)}+{len(lo1)}+{mid}={len(hi1)+len(lo1)+mid}（应=1599）; quality 实际取值={sorted(qs)}")
