#!/usr/bin/env python3
"""
Cross-Validation Comparison — Compare Method 1 (primary/conservative),
Method 2 (full repair), Method 3 (formula derivation) on core metrics.

Generates evidence/cross_validation_report.json with agreement matrix.
A2+ requirement: core conclusions must be confirmed by >=2 independent methods.
"""

import json
import os

EVIDENCE = r"<实验根目录>\ab-v3\phase0\D2-cafe\A2plus\evidence"

with open(os.path.join(EVIDENCE, "primary_results.json"), "r", encoding="utf-8") as f:
    m1 = json.load(f)
with open(os.path.join(EVIDENCE, "method2_results.json"), "r", encoding="utf-8") as f:
    m2 = json.load(f)
with open(os.path.join(EVIDENCE, "method3_results.json"), "r", encoding="utf-8") as f:
    m3 = json.load(f)

ITEMS = ["Coffee", "Tea", "Juice", "Smoothie", "Cake", "Cookie", "Sandwich", "Salad"]

# ── Core metric comparison ─────────────────────────────────────────
# Map methods to comparable values
comparisons = {}

# Total revenue:
# M1: total_revenue (all valid TS, including missing-item rows)
# M2: total_revenue_all_valid_ts (all valid TS after full repair)
# M3: derived_total_revenue (original + repaired, formula decomposition)
comparisons["total_revenue"] = {
    "method1_primary": m1["total_revenue"],
    "method2_fullrepair": m2["total_revenue_all_valid_ts"],
    "method3_formula": m3["formula_derivation"]["derived_total_revenue"],
}

# Valid rows (TS valid):
# M1: valid_rows
# M2: valid_rows_ts_any
# M3: derived_valid_count
comparisons["valid_rows_ts"] = {
    "method1_primary": m1["valid_rows"],
    "method2_fullrepair": m2["valid_rows_ts_any"],
    "method3_formula": m3["formula_derivation"]["derived_valid_count"],
}

# Missing counts (should be identical across all — raw data counting)
for metric in ["missing_ts", "missing_qty", "missing_item", "inconsistent_amount"]:
    comparisons[metric] = {
        "method1_primary": m1[metric],
        "method2_fullrepair": m2[metric],
        "method3_formula": m3[metric] if metric in m3 else m3.get(metric, "N/A"),
    }

# Repaired TS count
comparisons["repaired_ts"] = {
    "method1_primary": m1["repaired_ts"],
    "method2_fullrepair": m2["repaired_ts_only"],
    "method3_formula": m3["formula_derivation"]["repaired_count"],
}

# Per-item revenue and count
for item in ITEMS:
    comparisons[f"item_{item}_revenue"] = {
        "method1_primary": m1["item_breakdown"][item]["revenue"],
        "method2_fullrepair": m2["item_breakdown"][item]["revenue"],
        "method3_formula": round(
            m3["per_item_original"][item]["revenue"] + m3["per_item_repaired"][item]["revenue"], 2
        ),
    }
    comparisons[f"item_{item}_count"] = {
        "method1_primary": m1["item_breakdown"][item]["transactions"],
        "method2_fullrepair": m2["item_breakdown"][item]["transactions"],
        "method3_formula": m3["per_item_original"][item]["count"] + m3["per_item_repaired"][item]["count"],
    }

# ── Agreement check ────────────────────────────────────────────────
agreement = {}
all_pass = True
for metric, vals in comparisons.items():
    v1, v2, v3 = vals["method1_primary"], vals["method2_fullrepair"], vals["method3_formula"]
    if isinstance(v1, float):
        match = abs(v1 - v2) < 0.01 and abs(v1 - v3) < 0.01
    else:
        match = (v1 == v2 == v3)
    agreement[metric] = {
        "values": vals,
        "all_agree": match,
    }
    if not match:
        all_pass = False

# ── Candidate/pending items (Method 2 extra vs Method 1) ───────────
# Method 2 repairs Qty and PPU too, which may make additional rows "valid"
# in the full-repair sense. These are candidate additions not confirmed
# by the conservative method.
candidate = {
    "method2_extra_valid_rows_item_and_ts": m2["valid_rows_item_and_ts"],
    "method1_valid_rows_with_item": sum(m1["item_breakdown"][i]["transactions"] for i in ITEMS),
    "difference": m2["valid_rows_item_and_ts"] - sum(m1["item_breakdown"][i]["transactions"] for i in ITEMS),
    "explanation": "Method 2 repairs Qty/PPU, making rows with missing Qty/PPU but valid TS+Item count as 'fully valid'. Method 1 (conservative) only requires valid TS, so these rows ARE already counted in M1's valid_rows but may have missing Qty/PPU fields. The difference reflects different 'valid row' definitions, not different revenue.",
}

report = {
    "cross_validation_summary": {
        "all_core_metrics_agree": all_pass,
        "num_metrics_compared": len(comparisons),
        "num_agree": sum(1 for a in agreement.values() if a["all_agree"]),
        "num_disagree": sum(1 for a in agreement.values() if not a["all_agree"]),
    },
    "detailed_comparison": agreement,
    "candidate_pending": candidate,
    "conservative_decision": {
        "primary_method": "Method 1 (repair only TS, valid = has valid TS)",
        "reason": "Most conservative: only repairs the revenue target variable via deterministic formula; does not infer Qty/PPU. Rows with valid TS but missing Qty/PPU are still valid for revenue since TS is the actual charged amount.",
        "method2_role": "Cross-validation only — confirms revenue numbers are robust to repair strategy changes.",
        "method3_role": "Independent formula derivation + spot check — confirms calculations are arithmeticallv correct.",
    },
}

out = os.path.join(EVIDENCE, "cross_validation_report.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

# ── Print ──────────────────────────────────────────────────────────
print("=" * 60)
print("CROSS-VALIDATION REPORT")
print("=" * 60)
print(f"All core metrics agree: {all_pass}")
print(f"Metrics compared: {len(comparisons)}")
print(f"Agree: {report['cross_validation_summary']['num_agree']}")
print(f"Disagree: {report['cross_validation_summary']['num_disagree']}")
print()
print("Core metrics:")
for metric in ["total_revenue", "valid_rows_ts", "missing_ts", "missing_qty",
               "missing_item", "inconsistent_amount", "repaired_ts"]:
    a = agreement[metric]
    v = a["values"]
    status = "✓ AGREE" if a["all_agree"] else "✗ DISAGREE"
    print(f"  {metric:25s} M1={v['method1_primary']!s:>12s}  M2={v['method2_fullrepair']!s:>12s}  M3={v['method3_formula']!s:>12s}  {status}")
print()
print("Per-item revenue agreement:")
for item in ITEMS:
    a = agreement[f"item_{item}_revenue"]
    v = a["values"]
    status = "✓" if a["all_agree"] else "✗"
    print(f"  {item:12s} M1={v['method1_primary']:>10.2f}  M2={v['method2_fullrepair']:>10.2f}  M3={v['method3_formula']:>10.2f}  {status}")
print()
print(f"Candidate/pending (M2 extra valid item+TS rows): {candidate['difference']}")
print(f"\nOutput: {out}")
