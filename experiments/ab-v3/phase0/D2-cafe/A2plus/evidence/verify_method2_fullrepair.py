#!/usr/bin/env python3
"""
Cross-Validation Method 2 — Full Repair + Independent Reimplementation

Differences from primary (Method 1):
  - Repairs ALL THREE fields (TS, Qty, PPU) using TS = Qty × PPU, not just TS.
  - Uses a different code structure: pure functions, list comprehensions,
    no defaultdict side effects — independent computation path.
  - "Valid row" definition: row has valid Item AND valid (orig/repaired) TS.
  - This is the LESS conservative method; its extra rows are "candidate/pending".

Purpose: verify that primary method's core numbers are robust when repair
strategy changes. If both agree on revenue/valid-count, conclusion is solid.
"""

import csv
import json
import os

INPUT = r"<实验根目录>\ab-v3\datasets\cafe_sales_dirty.csv"
EVIDENCE = r"<实验根目录>\ab-v3\phase0\D2-cafe\A2plus\evidence"

MISSING = {"ERROR", "UNKNOWN", ""}
ITEMS = ["Coffee", "Tea", "Juice", "Smoothie", "Cake", "Cookie", "Sandwich", "Salad"]
EPS = 0.01


def parse_row(r):
    """Return (item, qty, ppu, ts, item_miss, qty_miss, ppu_miss, ts_miss)."""
    item = r["Item"].strip()
    qty_s = r["Quantity"].strip()
    ppu_s = r["Price Per Unit"].strip()
    ts_s = r["Total Spent"].strip()
    return (
        item, qty_s, ppu_s, ts_s,
        item in MISSING, qty_s in MISSING, ppu_s in MISSING, ts_s in MISSING,
    )


def try_float(s):
    try:
        return float(s)
    except ValueError:
        return None


def repair(item, qty_s, ppu_s, ts_s, im, qm, pm, tm):
    """Full repair: derive any missing of {qty, ppu, ts} from the other two."""
    qty = try_float(qty_s) if not qm else None
    ppu = try_float(ppu_s) if not pm else None
    ts = try_float(ts_s) if not tm else None
    repaired = {"qty": False, "ppu": False, "ts": False}

    # Repair TS
    if tm and qty is not None and ppu is not None:
        ts = qty * ppu
        repaired["ts"] = True
    # Repair Qty
    if qm and ts is not None and ppu is not None and ppu != 0:
        qty = ts / ppu
        repaired["qty"] = True
    # Repair PPU
    if pm and ts is not None and qty is not None and qty != 0:
        ppu = ts / qty
        repaired["ppu"] = True

    return item, qty, ppu, ts, repaired


# Load
with open(INPUT, "r", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

# Process each row independently
parsed = [parse_row(r) for r in rows]
repaired_rows = [repair(*p) for p in parsed]

# Metrics
missing_ts = sum(1 for p in parsed if p[7])
missing_qty = sum(1 for p in parsed if p[5])
missing_item = sum(1 for p in parsed if p[4])

# Inconsistent: all three originally present, mismatch
inconsistent = sum(
    1 for p in parsed
    if not p[5] and not p[6] and not p[7]
    and abs(float(p[1]) * float(p[2]) - float(p[3])) > EPS
)

# Valid rows (full repair): item valid AND ts valid after repair
valid = [rr for rr in repaired_rows if rr[0] in ITEMS and rr[3] is not None]
valid_rows = len(valid)
total_revenue = sum(rr[3] for rr in valid)

# Also count rows with valid TS but missing item (for revenue cross-check)
valid_ts_any = [rr for rr in repaired_rows if rr[3] is not None]
valid_ts_count = len(valid_ts_any)
total_revenue_all_ts = sum(rr[3] for rr in valid_ts_any)

# Repaired row count (any field repaired)
any_repaired = sum(1 for rr in repaired_rows if any(rr[4].values()))
ts_repaired = sum(1 for rr in repaired_rows if rr[4]["ts"])

# Item breakdown
item_rev = {item: 0.0 for item in ITEMS}
item_cnt = {item: 0 for item in ITEMS}
for rr in valid:
    item_rev[rr[0]] += rr[3]
    item_cnt[rr[0]] += 1

results = {
    "method": "full_repair_independent",
    "total_raw": len(rows),
    "repaired_rows_any_field": any_repaired,
    "repaired_ts_only": ts_repaired,
    "valid_rows_item_and_ts": valid_rows,
    "valid_rows_ts_any": valid_ts_count,
    "total_revenue_item_valid": round(total_revenue, 2),
    "total_revenue_all_valid_ts": round(total_revenue_all_ts, 2),
    "missing_ts": missing_ts,
    "missing_qty": missing_qty,
    "missing_item": missing_item,
    "inconsistent_amount": inconsistent,
    "item_breakdown": {
        item: {"revenue": round(item_rev[item], 2), "transactions": item_cnt[item]}
        for item in ITEMS
    },
}

out = os.path.join(EVIDENCE, "method2_results.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print("=" * 60)
print("METHOD 2 (FULL REPAIR, INDEPENDENT) RESULTS")
print("=" * 60)
print(f"Total raw:              {results['total_raw']}")
print(f"Repaired (any field):   {results['repaired_rows_any_field']}")
print(f"Repaired (TS only):     {results['repaired_ts_only']}")
print(f"Valid (item+TS):        {results['valid_rows_item_and_ts']}")
print(f"Valid (TS any):         {results['valid_rows_ts_any']}")
print(f"Revenue (item valid):   {results['total_revenue_item_valid']}")
print(f"Revenue (all valid TS): {results['total_revenue_all_valid_ts']}")
print(f"Missing TS/Qty/Item:    {missing_ts}/{missing_qty}/{missing_item}")
print(f"Inconsistent:           {inconsistent}")
print()
for item in ITEMS:
    bd = results["item_breakdown"][item]
    print(f"  {item:12s}  rev={bd['revenue']:>10.2f}  txn={bd['transactions']:>5d}")
print(f"\nOutput: {out}")
