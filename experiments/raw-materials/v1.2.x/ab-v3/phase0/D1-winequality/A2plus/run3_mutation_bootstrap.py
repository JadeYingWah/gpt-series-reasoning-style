"""
Run 3 — 独立验证路径 B（numpy 变异测试 + 数据完整性 + 自助法）
方法：
  (a) 用"中心化后点积"方式重新计算 Pearson（与 corrcoef 不同的调用路径）
  (b) 变异测试：打乱 quality 标签后相关系数应趋近于 0（验证计算非平凡）
  (c) 数据完整性检查：无 NaN/Inf、行数、quality 取值范围
  (d) 自助法(Bootstrap)估计 alcohol 差值的 95% CI，验证差值稳健性
输出：evidence/run3_results.json + evidence/run3_mutation_log.txt + 控制台摘要
"""
import numpy as np
import json
import os

DATA = r"<实验根目录>\ab-v3\datasets\winequality-red.csv"
OUT_DIR = r"<实验根目录>\ab-v3\phase0\D1-winequality\A2plus\evidence"

features = [
    "fixed acidity", "volatile acidity", "citric acid", "residual sugar",
    "chlorides", "free sulfur dioxide", "total sulfur dioxide", "density",
    "pH", "sulphates", "alcohol"
]

rng = np.random.default_rng(seed=42)

# 1. 读取
data = np.genfromtxt(DATA, delimiter=";", skip_header=1, dtype=float)
n_rows, n_cols = data.shape

# 数据完整性检查
integrity = {
    "n_rows": int(n_rows),
    "n_cols": int(n_cols),
    "has_nan": bool(np.isnan(data).any()),
    "has_inf": bool(np.isinf(data).any()),
    "quality_min": int(data[:, 11].min()),
    "quality_max": int(data[:, 11].max()),
    "quality_unique": sorted([int(x) for x in np.unique(data[:, 11])]),
}

quality = data[:, 11]
X = data[:, :11]

# 2. 方法(a)：中心化点积法计算 Pearson（独立于 corrcoef 的调用路径）
def pearson_centered(x, y):
    xc = x - x.mean()
    yc = y - y.mean()
    return float(np.dot(xc, yc) / (np.sqrt(np.dot(xc, xc)) * np.sqrt(np.dot(yc, yc))))

correlations_raw = []
for i, feat in enumerate(features):
    r = pearson_centered(X[:, i], quality)
    correlations_raw.append((feat, r))
correlations_raw.sort(key=lambda t: -abs(t[1]))
correlations = [{"feature": f, "pearson": round(r, 6)} for f, r in correlations_raw]

# 3. 方法(b)：变异测试 — 打乱 quality 后相关系数应趋近 0
mutation_log = []
n_perm = 1000
perm_corrs = {feat: [] for feat in features}
for _ in range(n_perm):
    q_perm = rng.permutation(quality)
    for i, feat in enumerate(features):
        perm_corrs[feat].append(pearson_centered(X[:, i], q_perm))

mutation_results = {}
for feat in features:
    arr = np.array(perm_corrs[feat])
    mutation_results[feat] = {
        "mean_abs_perm_r": round(float(np.mean(np.abs(arr))), 6),
        "max_abs_perm_r": round(float(np.max(np.abs(arr))), 6),
    }
mutation_log.append(f"Mutation test: {n_perm} permutations of quality labels")
mutation_log.append(f"{'Feature':25s} {'mean|r|_perm':>15s} {'max|r|_perm':>15s} {'true_r':>12s}")
for feat, r in correlations_raw:
    m = mutation_results[feat]
    mutation_log.append(f"{feat:25s} {m['mean_abs_perm_r']:15.6f} {m['max_abs_perm_r']:15.6f} {r:+.6f}")

# 4. quality 计数
counts = {}
for q in range(3, 9):
    counts[q] = int(np.sum(quality.astype(int) == q))

# 5. alcohol 分组均值
alcohol = X[:, 10]
high_mask = quality >= 7
low_mask = quality <= 4
alcohol_high = float(np.mean(alcohol[high_mask]))
alcohol_low = float(np.mean(alcohol[low_mask]))
diff = alcohol_high - alcohol_low
n_high = int(np.sum(high_mask))
n_low = int(np.sum(low_mask))

# 6. 方法(d)：Bootstrap 95% CI for alcohol difference
high_vals = alcohol[high_mask]
low_vals = alcohol[low_mask]
boot_diffs = []
for _ in range(10000):
    h = rng.choice(high_vals, size=len(high_vals), replace=True)
    l = rng.choice(low_vals, size=len(low_vals), replace=True)
    boot_diffs.append(h.mean() - l.mean())
boot_diffs = np.array(boot_diffs)
ci_lower = float(np.percentile(boot_diffs, 2.5))
ci_upper = float(np.percentile(boot_diffs, 97.5))

results = {
    "run": "run3_numpy_mutation_bootstrap",
    "integrity": integrity,
    "correlations": correlations,
    "quality_counts": counts,
    "alcohol_high_quality": round(alcohol_high, 4),
    "alcohol_low_quality": round(alcohol_low, 4),
    "alcohol_diff": round(diff, 4),
    "n_high_quality": n_high,
    "n_low_quality": n_low,
    "bootstrap_diff_ci95": [round(ci_lower, 4), round(ci_upper, 4)],
    "mutation_test": mutation_results,
}

os.makedirs(OUT_DIR, exist_ok=True)
with open(os.path.join(OUT_DIR, "run3_results.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
with open(os.path.join(OUT_DIR, "run3_mutation_log.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(mutation_log))

print("=== Run 3 (numpy centered-dot + mutation + bootstrap) ===")
print(f"Integrity: {integrity}")
print("\nPearson correlations (sorted by |r|):")
for c in correlations:
    print(f"  {c['feature']:25s} {c['pearson']:+.6f}")
print(f"\nQuality counts: {counts}")
print(f"\nAlcohol high(>=7): {alcohol_high:.4f} (n={n_high})")
print(f"Alcohol low(<=4):  {alcohol_low:.4f} (n={n_low})")
print(f"Difference:        {diff:.4f}")
print(f"Bootstrap 95% CI for diff: [{ci_lower:.4f}, {ci_upper:.4f}]")
print("\nMutation test (first 3 features):")
for feat, r in correlations_raw[:3]:
    m = mutation_results[feat]
    print(f"  {feat}: true_r={r:+.6f}, perm mean|r|={m['mean_abs_perm_r']:.6f}, max|r|={m['max_abs_perm_r']:.6f}")
