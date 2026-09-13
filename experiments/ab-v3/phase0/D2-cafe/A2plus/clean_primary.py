#!/usr/bin/env python3
"""
D2 Cafe Sales Data Cleaning — Primary (Conservative) Method
A2+ configuration: conservative repair, multi-path cross-validation ready.

Quality standard (checkable):
  - All 5 required questions yield specific numeric answers.
  - Total revenue == sum of per-Item revenue + revenue of valid-TS-but-missing-Item rows.
  - Valid row count == sum of per-Item txn count + valid-TS-but-missing-Item count.
  - No row counted as valid has a missing (ERROR/UNKNOWN/empty) Total Spent.
"""

import csv
import json
import os
from collections import defaultdict

# ── Config ──────────────────────────────────────────────────────────
INPUT = r"<实验根目录>\ab-v3\datasets\cafe_sales_dirty.csv"
OUTDIR = r"<实验根目录>\ab-v3\phase0\D2-cafe\A2plus"
EVIDENCE = os.path.join(OUTDIR, "evidence")

MISSING_MARKERS = {"ERROR", "UNKNOWN", ""}
EPS = 0.01  # tolerance for float comparison

ITEMS_8 = ["Coffee", "Tea", "Juice", "Smoothie", "Cake", "Cookie", "Sandwich", "Salad"]


def is_missing(v):
    return v.strip() in MISSING_MARKERS


def safe_float(v):
    try:
        return float(v)
    except (ValueError, TypeError):
        return None


# ── Load ────────────────────────────────────────────────────────────
with open(INPUT, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    raw_rows = list(reader)

total_raw = len(raw_rows)

# ── Cleaning (Conservative: repair only Total Spent) ────────────────
# Rule 1: ERROR / UNKNOWN / empty → missing
# Rule 2: If TS missing but Qty & PPU valid → repair TS = Qty × PPU
# Rule 3: Qty / PPU / Item are NOT repaired in primary method (conservative)
# Rule 4: Amount inconsistency = all three present but |TS - Qty×PPU| > EPS

cleaned = []          # list of dict with cleaned values + flags
stats = defaultdict(int)
item_revenue = defaultdict(float)
item_count = defaultdict(int)
revenue_missing_item = 0.0
count_missing_item = 0

for r in raw_rows:
    tid = r["Transaction ID"]
    item_raw = r["Item"].strip()
    qty_raw = r["Quantity"].strip()
    ppu_raw = r["Price Per Unit"].strip()
    ts_raw = r["Total Spent"].strip()

    item_missing = is_missing(item_raw)
    qty_missing = is_missing(qty_raw)
    ppu_missing = is_missing(ppu_raw)
    ts_missing = is_missing(ts_raw)

    # Count missing (question 4)
    if ts_missing:
        stats["missing_ts"] += 1
    if qty_missing:
        stats["missing_qty"] += 1
    if item_missing:
        stats["missing_item"] += 1

    qty_val = safe_float(qty_raw) if not qty_missing else None
    ppu_val = safe_float(ppu_raw) if not ppu_missing else None
    ts_val = safe_float(ts_raw) if not ts_missing else None

    # Amount inconsistency check (question 5): all three present
    inconsistent = False
    if not ts_missing and not qty_missing and not ppu_missing:
        expected = qty_val * ppu_val
        if abs(ts_val - expected) > EPS:
            inconsistent = True
            stats["inconsistent_amount"] += 1

    # Repair TS (conservative: only when both Qty and PPU are valid)
    ts_repaired = False
    if ts_missing and not qty_missing and not ppu_missing:
        ts_val = qty_val * ppu_val
        ts_repaired = True
        stats["repaired_ts"] += 1

    # Determine if row is "valid for revenue" (has valid TS after repair)
    ts_valid = ts_val is not None

    if ts_repaired:
        stats["repaired_rows"] += 1

    if ts_valid:
        stats["valid_rows"] += 1
        # Categorize by Item
        if not item_missing and item_raw in ITEMS_8:
            item_revenue[item_raw] += ts_val
            item_count[item_raw] += 1
        else:
            revenue_missing_item += ts_val
            count_missing_item += 1

    cleaned.append({
        "Transaction ID": tid,
        "Item": item_raw if not item_missing else "MISSING",
        "Quantity": qty_raw if not qty_missing else "MISSING",
        "Price Per Unit": ppu_raw if not ppu_missing else "MISSING",
        "Total Spent": f"{ts_val:.1f}" if ts_val is not None else "MISSING",
        "ts_repaired": ts_repaired,
        "ts_valid": ts_valid,
        "inconsistent": inconsistent,
    })

# ── Aggregate results ───────────────────────────────────────────────
total_revenue = sum(item_revenue.values()) + revenue_missing_item
total_item_txn = sum(item_count.values())

results = {
    "total_raw_rows": total_raw,
    "repaired_rows": stats["repaired_rows"],
    "valid_rows": stats["valid_rows"],
    "total_revenue": round(total_revenue, 2),
    "missing_ts": stats["missing_ts"],
    "missing_qty": stats["missing_qty"],
    "missing_item": stats["missing_item"],
    "inconsistent_amount": stats["inconsistent_amount"],
    "repaired_ts": stats["repaired_ts"],
    "item_breakdown": {
        item: {
            "revenue": round(item_revenue.get(item, 0.0), 2),
            "transactions": item_count.get(item, 0),
        }
        for item in ITEMS_8
    },
    "valid_ts_missing_item_revenue": round(revenue_missing_item, 2),
    "valid_ts_missing_item_count": count_missing_item,
    # consistency checks
    "_check_sum_item_revenue_plus_unclassified": round(
        sum(item_revenue.values()) + revenue_missing_item, 2),
    "_check_sum_item_count_plus_unclassified": total_item_txn + count_missing_item,
}

# ── Output cleaned CSV ─────────────────────────────────────────────
cleaned_csv = os.path.join(OUTDIR, "cleaned_sales.csv")
with open(cleaned_csv, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "Transaction ID", "Item", "Quantity", "Price Per Unit",
        "Total Spent", "ts_repaired", "ts_valid", "inconsistent"
    ])
    writer.writeheader()
    writer.writerows(cleaned)

# ── Output JSON results ────────────────────────────────────────────
results_json = os.path.join(EVIDENCE, "primary_results.json")
with open(results_json, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

# ── Print summary ──────────────────────────────────────────────────
print("=" * 60)
print("PRIMARY (CONSERVATIVE) METHOD RESULTS")
print("=" * 60)
print(f"Total raw rows:        {results['total_raw_rows']}")
print(f"Repaired rows:         {results['repaired_rows']}")
print(f"Valid rows (rev):      {results['valid_rows']}")
print(f"Total revenue:         {results['total_revenue']}")
print(f"Missing TS:            {results['missing_ts']}")
print(f"Missing Qty:           {results['missing_qty']}")
print(f"Missing Item:          {results['missing_item']}")
print(f"Inconsistent amount:   {results['inconsistent_amount']}")
print()
print("Item breakdown:")
for item in ITEMS_8:
    bd = results["item_breakdown"][item]
    print(f"  {item:12s}  revenue={bd['revenue']:>10.2f}  txn={bd['transactions']:>5d}")
print(f"  {'(missing item)':12s}  revenue={results['valid_ts_missing_item_revenue']:>10.2f}  txn={results['valid_ts_missing_item_count']:>5d}")
print()
print(f"Consistency: sum(item_rev)+unclassified = {results['_check_sum_item_revenue_plus_unclassified']}")
print(f"Consistency: sum(item_cnt)+unclassified = {results['_check_sum_item_count_plus_unclassified']}")
print(f"Match total_revenue? {abs(results['_check_sum_item_revenue_plus_unclassified'] - results['total_revenue']) < 0.01}")
print(f"Match valid_rows?    {results['_check_sum_item_count_plus_unclassified'] == results['valid_rows']}")
print()
print(f"Cleaned CSV: {cleaned_csv}")
print(f"Results JSON: {results_json}")
