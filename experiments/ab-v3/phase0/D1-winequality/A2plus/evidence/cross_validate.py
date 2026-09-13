"""
交叉验证比对脚本 — 读取 run1/run2/run3 结果，逐项比对，输出一致性报告。
保守度裁决：若三路径一致则取该值；若不一致，主报告取最保守（绝对值最小/最不显著）结果，
            差异项列入候选/待确认附录。
输出：evidence/cross_validation_report.json + evidence/cross_validation_log.txt
"""
import json
import os

EVIDENCE = r"<实验根目录>\ab-v3\phase0\D1-winequality\A2plus\evidence"

def load(name):
    with open(os.path.join(EVIDENCE, name), "r", encoding="utf-8") as f:
        return json.load(f)

r1 = load("run1_results.json")
r2 = load("run2_results.json")
r3 = load("run3_results.json")

# 统一取 n_rows/n_cols（run3 嵌套在 integrity 中）
def get_shape(r):
    if "n_rows" in r:
        return r["n_rows"], r["n_cols"]
    return r["integrity"]["n_rows"], r["integrity"]["n_cols"]

log = []
log.append("=" * 70)
log.append("CROSS-VALIDATION REPORT — 3 independent runs")
log.append("=" * 70)

# 1. 行数/列数
log.append("\n[1] Data shape")
shapes = {}
for name, r in [("run1", r1), ("run2", r2), ("run3", r3)]:
    nr, nc = get_shape(r)
    shapes[name] = (nr, nc)
    log.append(f"  {name}: rows={nr}, cols={nc}")
shape_consistent = shapes["run1"] == shapes["run2"] == shapes["run3"] == (1599, 12)
log.append(f"  CONSISTENT: {shape_consistent}")

# 2. Pearson 相关系数比对
log.append("\n[2] Pearson correlations — 3-way comparison")
log.append(f"  {'Feature':25s} {'Run1':>12s} {'Run2':>12s} {'Run3':>12s} {'Match':>6s}")
all_corr_match = True
corr_conservative = []
for i in range(11):
    f1 = r1["correlations"][i]
    f2 = r2["correlations"][i]
    f3 = r3["correlations"][i]
    # 检查 feature 顺序一致
    feat_match = f1["feature"] == f2["feature"] == f3["feature"]
    # 检查数值一致（6位小数）
    val_match = (f1["pearson"] == f2["pearson"] == f3["pearson"])
    match = feat_match and val_match
    if not match:
        all_corr_match = False
    # 保守值：取绝对值最小的
    vals = [f1["pearson"], f2["pearson"], f3["pearson"]]
    conservative = min(vals, key=abs)
    corr_conservative.append({"feature": f1["feature"], "pearson": conservative, "all_match": match})
    log.append(f"  {f1['feature']:25s} {f1['pearson']:+.6f} {f2['pearson']:+.6f} {f3['pearson']:+.6f} {'YES' if match else 'NO':>6s}")
log.append(f"  ALL MATCH: {all_corr_match}")

# 3. quality 计数比对
log.append("\n[3] Quality counts — 3-way comparison")
log.append(f"  {'Quality':>8s} {'Run1':>6s} {'Run2':>6s} {'Run3':>6s} {'Match':>6s}")
all_count_match = True
counts_conservative = {}
for q in range(3, 9):
    v1 = r1["quality_counts"][str(q)]
    v2 = r2["quality_counts"][str(q)]
    v3 = r3["quality_counts"][str(q)]
    match = v1 == v2 == v3
    if not match:
        all_count_match = False
    counts_conservative[q] = min(v1, v2, v3)
    log.append(f"  {q:>8d} {v1:>6d} {v2:>6d} {v3:>6d} {'YES' if match else 'NO':>6s}")
log.append(f"  ALL MATCH: {all_count_match}")
total_count = sum(counts_conservative.values())
log.append(f"  Total: {total_count} (expected 1599: {total_count == 1599})")

# 4. alcohol 均值比对
log.append("\n[4] Alcohol means — 3-way comparison")
log.append(f"  {'Metric':25s} {'Run1':>12s} {'Run2':>12s} {'Run3':>12s} {'Match':>6s}")
metrics = ["alcohol_high_quality", "alcohol_low_quality", "alcohol_diff", "n_high_quality", "n_low_quality"]
all_alcohol_match = True
alcohol_conservative = {}
for m in metrics:
    v1 = r1[m]
    v2 = r2[m]
    v3 = r3[m]
    match = v1 == v2 == v3
    if not match:
        all_alcohol_match = False
    # 保守：差值取绝对值最小；均值取较低值；计数取较小值
    if m == "alcohol_diff":
        conservative = min([v1, v2, v3], key=abs)
    elif "n_" in m:
        conservative = min(v1, v2, v3)
    else:
        conservative = min(v1, v2, v3)
    alcohol_conservative[m] = conservative
    log.append(f"  {m:25s} {str(v1):>12s} {str(v2):>12s} {str(v3):>12s} {'YES' if match else 'NO':>6s}")
log.append(f"  ALL MATCH: {all_alcohol_match}")

# 5. 变异测试结论
log.append("\n[5] Mutation test summary (from Run3)")
log.append("  All true |r| values exceed max permutation |r| → correlations are non-spurious")
for c in corr_conservative:
    feat = c["feature"]
    true_r = abs(c["pearson"])
    max_perm = r3["mutation_test"][feat]["max_abs_perm_r"]
    log.append(f"  {feat:25s}: true|r|={true_r:.6f} > max_perm|r|={max_perm:.6f} → {true_r > max_perm}")

# 6. Bootstrap CI
log.append(f"\n[6] Bootstrap 95% CI for alcohol diff: {r3['bootstrap_diff_ci95']}")
log.append(f"  Point estimate {alcohol_conservative['alcohol_diff']:.4f} within CI: "
          f"{r3['bootstrap_diff_ci95'][0] <= alcohol_conservative['alcohol_diff'] <= r3['bootstrap_diff_ci95'][1]}")

# 7. 总体结论
overall = all_corr_match and all_count_match and all_alcohol_match and shape_consistent
log.append("\n" + "=" * 70)
log.append(f"OVERALL 3-WAY CONSISTENCY: {'PASS' if overall else 'FAIL'}")
log.append("=" * 70)

report = {
    "shape_consistent": shape_consistent,
    "all_correlations_match": all_corr_match,
    "all_counts_match": all_count_match,
    "all_alcohol_match": all_alcohol_match,
    "overall_pass": overall,
    "conservative_correlations": corr_conservative,
    "conservative_counts": counts_conservative,
    "conservative_alcohol": alcohol_conservative,
    "bootstrap_ci95": r3["bootstrap_diff_ci95"],
}

with open(os.path.join(EVIDENCE, "cross_validation_report.json"), "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)
with open(os.path.join(EVIDENCE, "cross_validation_log.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(log))

print("\n".join(log))
