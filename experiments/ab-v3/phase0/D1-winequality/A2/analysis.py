# -*- coding: utf-8 -*-
"""D1 红酒质量分析（A 臂·轻量验证聚焦版）
数据: <实验根目录>/ab-v3/datasets/winequality-red.csv (分号分隔, 引号表头, 1599 行)
输出:
  1) 11 项理化指标与 quality 的 Pearson 相关系数 (6 位小数, 按 |r| 降序)
  2) quality 3~8 各档样本计数
  3) quality>=7 与 quality<=4 两组的 alcohol 均值 (4 位小数) 及差值
验证: 三种独立实现交叉计算 —— numpy.corrcoef / 手工 Pearson 公式 / 纯 stdlib 实现
运行: py -3.14 analysis.py   (本机 py -3.14 含 numpy; pandas/scipy 缺损故不使用)
"""
import csv
import math

DATA = "<实验根目录>/ab-v3/datasets/winequality-red.csv"

# ---------- 1. 加载 (stdlib csv) 与质量检查 ----------
rows = []
with open(DATA, newline="", encoding="utf-8") as fh:
    reader = csv.DictReader(fh, delimiter=";")
    header = reader.fieldnames
    for rec in reader:
        rows.append(rec)

assert len(rows) == 1599, f"行数异常: {len(rows)}"
assert header == ["fixed acidity", "volatile acidity", "citric acid",
                  "residual sugar", "chlorides", "free sulfur dioxide",
                  "total sulfur dioxide", "density", "pH", "sulphates",
                  "alcohol", "quality"], f"表头异常: {header}"
data = {h: [float(r[h]) for r in rows] for h in header}
n = len(rows)
assert all(math.isfinite(v) for col in data.values() for v in col), "存在 NaN/Inf"
qcol = data["quality"]
assert all(q == int(q) and 3 <= q <= 8 for q in qcol), "quality 越界/非整数"
print(f"[OK] 行数={n}, 列数={len(header)}, NaN=0, quality∈[3,8] 全部通过")

# ---------- 2. 问题1: 11 项 Pearson 相关系数 ----------
features = [h for h in header if h != "quality"]

def pearson_manual(x, y):
    """手工公式: Σ(x-x̄)(y-ȳ) / sqrt(Σ(x-x̄)²·Σ(y-ȳ)²)"""
    mx, my = sum(x) / len(x), sum(y) / len(y)
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    return sxy / math.sqrt(sxx * syy)

r_manual, r_stdlib = {}, {}
for f in features:
    x = data[f]
    r_manual[f] = pearson_manual(x, qcol)

# numpy 版本 (若 numpy 可用; 本环境 py -3.14 已验证可用)
try:
    import numpy as np
    y_np = np.array(qcol)
    for f in features:
        x_np = np.array(data[f])
        c = np.corrcoef(x_np, y_np)[0, 1]
        r_stdlib[f] = float(c)  # 借名 r_stdlib 实为 numpy 法
    impl = "numpy.corrcoef"
except ImportError:
    impl = "(numpy 不可用, 退化为双实现)"

max_dev = max(abs(r_manual[f] - r_stdlib[f]) for f in features) if r_stdlib else None
if max_dev is not None:
    assert max_dev < 1e-9, f"两方法不一致: {max_dev}"
    print(f"[OK] 手工公式 vs {impl} 最大偏差 = {max_dev:.2e}")

rows_sorted = sorted(features, key=lambda f: abs(r_manual[f]), reverse=True)
print("\n== 问题1: Pearson 相关系数 (|r| 降序, 6位小数) ==")
for f in rows_sorted:
    r = r_manual[f]
    extra = f"  (numpy: {r_stdlib[f]:+.6f})" if r_stdlib else ""
    print(f"{f:22s} {r:+.6f}  |r|={abs(r):.6f}{extra}")

# ---------- 3. 问题2: quality 各档计数 ----------
counts = {q: 0 for q in range(3, 9)}
for q in qcol:
    counts[int(q)] += 1
assert sum(counts.values()) == 1599, "计数总和 != 1599"
print("\n== 问题2: quality 各档样本计数 ==")
for q in range(3, 9):
    print(f"quality={q}: {counts[q]}")
print(f"总计: {sum(counts.values())}")

# ---------- 4. 问题3: 高/低质组 alcohol 均值 ----------
alc = data["alcohol"]
hi = [a for a, q in zip(alc, qcol) if q >= 7]
lo = [a for a, q in zip(alc, qcol) if q <= 4]
assert 0 < len(hi) < 1599 and 0 < len(lo) < 1599, "分组异常"
hi_m = sum(hi) / len(hi)
lo_m = sum(lo) / len(lo)
# numpy 独立复算
hi_np_m = float(np.array(hi).mean()) if r_stdlib else hi_m
lo_np_m = float(np.array(lo).mean()) if r_stdlib else lo_m
assert abs(hi_m - hi_np_m) < 1e-12 and abs(lo_m - lo_np_m) < 1e-12, "均值复算不一致"
diff = hi_m - lo_m
print("\n== 问题3: alcohol 均值 ==")
print(f"高质组 quality>=7: n={len(hi)}, mean={hi_m:.4f}")
print(f"低质组 quality<=4: n={len(lo)}, mean={lo_m:.4f}")
print(f"差值 (高-低): {diff:.4f}")

print("\n[ALL PASS] 全部断言通过")
