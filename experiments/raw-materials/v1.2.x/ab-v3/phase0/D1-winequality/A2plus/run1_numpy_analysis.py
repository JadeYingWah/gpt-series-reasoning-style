"""
Run 1 — 主实现（numpy 路径）
方法：numpy.genfromtxt 读入 → numpy.corrcoef 计算 Pearson → numpy 统计分组均值
输出：evidence/run1_results.json + 控制台摘要
"""
import numpy as np
import json
import os

DATA = r"<实验根目录>\ab-v3\datasets\winequality-red.csv"
OUT_DIR = r"<实验根目录>\ab-v3\phase0\D1-winequality\A2plus\evidence"

# 1. 读取（跳过表头，分号分隔）
data = np.genfromtxt(DATA, delimiter=";", skip_header=1, dtype=float)
assert data.shape == (1599, 12), f"Unexpected shape: {data.shape}"

features = [
    "fixed acidity", "volatile acidity", "citric acid", "residual sugar",
    "chlorides", "free sulfur dioxide", "total sulfur dioxide", "density",
    "pH", "sulphates", "alcohol"
]
quality = data[:, 11]
X = data[:, :11]

# 2. Pearson 相关系数（numpy.corrcoef）
corr_matrix = np.corrcoef(X, quality, rowvar=False)
# 最后一列是 quality 与各特征的相关
corr_with_quality = corr_matrix[:11, 11]

# 排序：按绝对值从大到小
order = np.argsort(-np.abs(corr_with_quality))
correlations = []
for idx in order:
    correlations.append({
        "feature": features[idx],
        "pearson": round(float(corr_with_quality[idx]), 6)
    })

# 3. quality 各档位计数
quality_int = quality.astype(int)
counts = {}
for q in range(3, 9):
    counts[q] = int(np.sum(quality_int == q))

# 4. 高质组(quality>=7) vs 低质组(quality<=4) 的 alcohol 均值
alcohol = X[:, 10]  # alcohol 是第11列(index 10)
high_mask = quality >= 7
low_mask = quality <= 4
alcohol_high = float(np.mean(alcohol[high_mask]))
alcohol_low = float(np.mean(alcohol[low_mask]))
diff = alcohol_high - alcohol_low

n_high = int(np.sum(high_mask))
n_low = int(np.sum(low_mask))

results = {
    "run": "run1_numpy",
    "n_rows": int(data.shape[0]),
    "n_cols": int(data.shape[1]),
    "correlations": correlations,
    "quality_counts": counts,
    "alcohol_high_quality": round(alcohol_high, 4),
    "alcohol_low_quality": round(alcohol_low, 4),
    "alcohol_diff": round(diff, 4),
    "n_high_quality": n_high,
    "n_low_quality": n_low,
}

os.makedirs(OUT_DIR, exist_ok=True)
with open(os.path.join(OUT_DIR, "run1_results.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("=== Run 1 (numpy) ===")
print(f"Rows: {results['n_rows']}, Cols: {results['n_cols']}")
print("\nPearson correlations (sorted by |r|):")
for c in correlations:
    print(f"  {c['feature']:25s} {c['pearson']:+.6f}")
print(f"\nQuality counts: {counts}")
print(f"\nAlcohol high(>=7): {alcohol_high:.4f} (n={n_high})")
print(f"Alcohol low(<=4):  {alcohol_low:.4f} (n={n_low})")
print(f"Difference:        {diff:.4f}")
