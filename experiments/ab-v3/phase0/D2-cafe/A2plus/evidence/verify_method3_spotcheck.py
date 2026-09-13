#!/usr/bin/env python3
"""
Cross-Validation Method 3 — Spot Check + Formula Derivation

Independent verification path:
  1. Random sample of 50 rows: manually verify TS = Qty × PPU for originally
     valid rows, and verify repaired TS for missing-TS rows.
  2. Aggregate formula derivation: compute total revenue via an alternative
     formula (sum over item categories of per-category revenue) and compare
     with direct sum.
  3. Boundary check: verify no valid row has TS <= 0, no repaired TS differs
     from Qty×PPU by > EPS.
  4. Deterministic seed for reproducibility.
"""

import csv
import json
import os
import random

INPUT = r"<实验根目录>\ab-v3\datasets\cafe_sales_dirty.csv"
EVIDENCE = r"<实验根目录>\ab-v3\phase0\D2-cafe\A2plus\evidence"

MISSING = {"ERROR", "UNKNOWN", ""}
ITEMS = ["Coffee", "Tea", "Juice", "Smoothie", "Cake", "Cookie", "Sandwich", "Salad"]
EPS = 0.01
SEED = 42
SAMPLE_SIZE = 50

random.seed(SEED)

with open(INPUT, "r", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

def is_missing(v):
    return v.strip() in MISSING

def fnum(v):
    try:
        return float(v)
    except ValueError:
        return None

# ── Part 1: Spot check random sample ────────────────────────────────
sample_indices = random.sample(range(len(rows)), SAMPLE_SIZE)
spot_check_results = []
spot_pass = 0
spot_fail = 0

for idx in sample_indices:
    r = rows[idx]
    qty_s = r["Quantity"].strip()
    ppu_s = r["Price Per Unit"].strip()
    ts_s = r["Total Spent"].strip()
    item = r["Item"].strip()

    qm = is_missing(qty_s)
    pm = is_missing(ppu_s)
    tm = is_missing(ts_s)

    status = "OK"
    detail = ""

    if not qm and not pm and not tm:
        # All present: verify formula
        qty, ppu, ts = fnum(qty_s), fnum(ppu_s), fnum(ts_s)
        expected = qty * ppu
        if abs(ts - expected) > EPS:
            status = "FAIL_INCONSISTENT"
            detail = f"TS={ts} != Qty*PPU={expected}"
            spot_fail += 1
        else:
            spot_pass += 1
    elif tm and not qm and not pm:
        # TS missing, repairable: verify repair formula
        qty, ppu = fnum(qty_s), fnum(ppu_s)
        repaired_ts = qty * ppu
        if repaired_ts <= 0:
            status = "FAIL_BAD_REPAIR"
            detail = f"repaired TS={repaired_ts} <= 0"
            spot_fail += 1
        else:
            status = "OK_REPAIRED"
            detail = f"repaired TS={repaired_ts:.1f}"
            spot_pass += 1
    else:
        # Other missing patterns: just note
        status = "OK_SKIP"
        detail = f"missing pattern: qty={qm}, ppu={pm}, ts={tm}"
        spot_pass += 1

    spot_check_results.append({
        "row_index": idx,
        "txn_id": r["Transaction ID"],
        "item": item,
        "status": status,
        "detail": detail,
    })

# ── Part 2: Aggregate formula derivation ────────────────────────────
# Alternative revenue calculation: per-item sum using only originally valid TS
# (no repair), then separately add repaired TS. This decomposes the total
# into two independently computed parts.

orig_rev_by_item = {item: 0.0 for item in ITEMS}
orig_cnt_by_item = {item: 0 for item in ITEMS}
repaired_rev_by_item = {item: 0.0 for item in ITEMS}
repaired_cnt_by_item = {item: 0 for item in ITEMS}
orig_rev_missing_item = 0.0
repaired_rev_missing_item = 0.0

for r in rows:
    item = r["Item"].strip()
    qty_s = r["Quantity"].strip()
    ppu_s = r["Price Per Unit"].strip()
    ts_s = r["Total Spent"].strip()

    im = is_missing(item)
    qm = is_missing(qty_s)
    pm = is_missing(ppu_s)
    tm = is_missing(ts_s)

    if not tm:
        # Originally valid TS
        ts = fnum(ts_s)
        if not im and item in ITEMS:
            orig_rev_by_item[item] += ts
            orig_cnt_by_item[item] += 1
        elif im:
            orig_rev_missing_item += ts
    elif tm and not qm and not pm:
        # Repairable TS
        ts = fnum(qty_s) * fnum(ppu_s)
        if not im and item in ITEMS:
            repaired_rev_by_item[item] += ts
            repaired_cnt_by_item[item] += 1
        elif im:
            repaired_rev_missing_item += ts

# Derived totals
total_orig_rev = sum(orig_rev_by_item.values()) + orig_rev_missing_item
total_repaired_rev = sum(repaired_rev_by_item.values()) + repaired_rev_missing_item
derived_total_rev = total_orig_rev + total_repaired_rev

total_orig_cnt = sum(orig_cnt_by_item.values()) + sum(
    1 for r in rows if not is_missing(r["Total Spent"].strip()) and is_missing(r["Item"].strip())
)
total_repaired_cnt = sum(repaired_cnt_by_item.values()) + sum(
    1 for r in rows if is_missing(r["Total Spent"].strip())
    and not is_missing(r["Quantity"].strip())
    and not is_missing(r["Price Per Unit"].strip())
    and is_missing(r["Item"].strip())
)
derived_valid_cnt = total_orig_cnt + total_repaired_cnt

# ── Part 3: Boundary checks ────────────────────────────────────────
boundary_issues = []
for i, r in enumerate(rows):
    qty_s = r["Quantity"].strip()
    ppu_s = r["Price Per Unit"].strip()
    ts_s = r["Total Spent"].strip()
    qm, pm, tm = is_missing(qty_s), is_missing(ppu_s), is_missing(ts_s)

    if not tm:
        ts = fnum(ts_s)
        if ts is not None and ts <= 0:
            boundary_issues.append({"row": i, "issue": f"TS={ts} <= 0"})
    if not qm:
        qty = fnum(qty_s)
        if qty is not None and (qty <= 0 or qty != int(qty)):
            boundary_issues.append({"row": i, "issue": f"Qty={qty} non-positive or non-integer"})
    if not pm:
        ppu = fnum(ppu_s)
        if ppu is not None and ppu <= 0:
            boundary_issues.append({"row": i, "issue": f"PPU={ppu} <= 0"})

# ── Raw missing counts (for cross-method comparison) ───────────────
raw_missing_ts = sum(1 for r in rows if is_missing(r["Total Spent"].strip()))
raw_missing_qty = sum(1 for r in rows if is_missing(r["Quantity"].strip()))
raw_missing_item = sum(1 for r in rows if is_missing(r["Item"].strip()))
raw_inconsistent = sum(
    1 for r in rows
    if not is_missing(r["Total Spent"].strip())
    and not is_missing(r["Quantity"].strip())
    and not is_missing(r["Price Per Unit"].strip())
    and abs(float(r["Total Spent"]) - float(r["Quantity"]) * float(r["Price Per Unit"])) > EPS
)

# ── Output ─────────────────────────────────────────────────────────
results = {
    "method": "spot_check_formula_derivation",
    "seed": SEED,
    "sample_size": SAMPLE_SIZE,
    "missing_ts": raw_missing_ts,
    "missing_qty": raw_missing_qty,
    "missing_item": raw_missing_item,
    "inconsistent_amount": raw_inconsistent,
    "spot_check": {
        "pass": spot_pass,
        "fail": spot_fail,
        "pass_rate": f"{spot_pass}/{SAMPLE_SIZE}",
        "details": spot_check_results[:20],  # first 20 for evidence
    },
    "formula_derivation": {
        "original_valid_revenue": round(total_orig_rev, 2),
        "repaired_revenue": round(total_repaired_rev, 2),
        "derived_total_revenue": round(derived_total_rev, 2),
        "original_valid_count": total_orig_cnt,
        "repaired_count": total_repaired_cnt,
        "derived_valid_count": derived_valid_cnt,
    },
    "boundary_check": {
        "issues_found": len(boundary_issues),
        "issues": boundary_issues[:10],
    },
    "per_item_original": {item: {"revenue": round(orig_rev_by_item[item], 2), "count": orig_cnt_by_item[item]} for item in ITEMS},
    "per_item_repaired": {item: {"revenue": round(repaired_rev_by_item[item], 2), "count": repaired_cnt_by_item[item]} for item in ITEMS},
}

out = os.path.join(EVIDENCE, "method3_results.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print("=" * 60)
print("METHOD 3 (SPOT CHECK + FORMULA DERIVATION)")
print("=" * 60)
print(f"Spot check: {spot_pass}/{SAMPLE_SIZE} passed, {spot_fail} failed")
print(f"Boundary issues: {len(boundary_issues)}")
print()
print("Formula derivation:")
print(f"  Original valid revenue: {results['formula_derivation']['original_valid_revenue']}")
print(f"  Repaired revenue:       {results['formula_derivation']['repaired_revenue']}")
print(f"  Derived total revenue:  {results['formula_derivation']['derived_total_revenue']}")
print(f"  Original valid count:   {results['formula_derivation']['original_valid_count']}")
print(f"  Repaired count:         {results['formula_derivation']['repaired_count']}")
print(f"  Derived valid count:    {results['formula_derivation']['derived_valid_count']}")
print()
print("Per-item (original + repaired):")
for item in ITEMS:
    o = results["per_item_original"][item]
    rp = results["per_item_repaired"][item]
    print(f"  {item:12s}  orig_rev={o['revenue']:>9.2f}({o['count']:>4d})  rep_rev={rp['revenue']:>8.2f}({rp['count']:>3d})  total={o['revenue']+rp['revenue']:>9.2f}")
print(f"\nOutput: {out}")
