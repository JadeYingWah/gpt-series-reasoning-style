"""
Run 2 — 独立验证路径 A（纯 Python 标准库 + 公式推导）
方法：csv 模块读入 → 手动实现 Pearson 公式 r = Σ((x-x̄)(y-ȳ)) / sqrt(Σ(x-x̄)²·Σ(y-ȳ)²)
      → 手动计数 → 手动均值
不依赖 numpy，确保与 Run1 完全独立的计算路径。
输出：evidence/run2_results.json + 控制台摘要
"""
import csv
import math
import json
import os

DATA = r"<实验根目录>\ab-v3\datasets\winequality-red.csv"
OUT_DIR = r"<实验根目录>\ab-v3\phase0\D1-winequality\A2plus\evidence"

features = [
    "fixed acidity", "volatile acidity", "citric acid", "residual sugar",
    "chlorides", "free sulfur dioxide", "total sulfur dioxide", "density",
    "pH", "sulphates", "alcohol"
]

# 1. 读取
rows = []
with open(DATA, "r", encoding="utf-8") as f:
    reader = csv.reader(f, delimiter=";")
    header = next(reader)
    for row in reader:
        rows.append([float(v) for v in row])

n = len(rows)
assert n == 1599, f"Expected 1599 rows, got {n}"

# 提取列
cols = list(zip(*rows))  # 12 columns
quality_col = cols[11]
feature_cols = cols[:11]

# 2. 手动 Pearson
def pearson(x, y):
    """手动实现 Pearson 相关系数"""
    n = len(x)
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    num = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
    den_x = sum((xi - mean_x) ** 2 for xi in x)
    den_y = sum((yi - mean_y) ** 2 for yi in y)
    return num / math.sqrt(den_x * den_y)

correlations_raw = []
for i, feat in enumerate(features):
    r = pearson(feature_cols[i], quality_col)
    correlations_raw.append((feat, r))

# 按绝对值排序
correlations_raw.sort(key=lambda t: -abs(t[1]))
correlations = [{"feature": f, "pearson": round(r, 6)} for f, r in correlations_raw]

# 3. quality 计数
counts = {q: 0 for q in range(3, 9)}
for q in quality_col:
    qi = int(q)
    if qi in counts:
        counts[qi] += 1

# 4. alcohol 分组均值（alcohol 是 index 10）
alcohol_col = feature_cols[10]
high_vals = [a for a, q in zip(alcohol_col, quality_col) if q >= 7]
low_vals = [a for a, q in zip(alcohol_col, quality_col) if q <= 4]
alcohol_high = sum(high_vals) / len(high_vals)
alcohol_low = sum(low_vals) / len(low_vals)
diff = alcohol_high - alcohol_low

results = {
    "run": "run2_pure_python",
    "n_rows": n,
    "n_cols": 12,
    "correlations": correlations,
    "quality_counts": counts,
    "alcohol_high_quality": round(alcohol_high, 4),
    "alcohol_low_quality": round(alcohol_low, 4),
    "alcohol_diff": round(diff, 4),
    "n_high_quality": len(high_vals),
    "n_low_quality": len(low_vals),
}

os.makedirs(OUT_DIR, exist_ok=True)
with open(os.path.join(OUT_DIR, "run2_results.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("=== Run 2 (pure Python formula) ===")
print(f"Rows: {n}")
print("\nPearson correlations (sorted by |r|):")
for c in correlations:
    print(f"  {c['feature']:25s} {c['pearson']:+.6f}")
print(f"\nQuality counts: {counts}")
print(f"\nAlcohol high(>=7): {alcohol_high:.4f} (n={len(high_vals)})")
print(f"Alcohol low(<=4):  {alcohol_low:.4f} (n={len(low_vals)})")
print(f"Difference:        {diff:.4f}")
