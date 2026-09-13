# -*- coding: utf-8 -*-
"""D2 咖啡馆销售数据清洗（预注册规则 R1-R4），纯标准库实现"""
import csv
from collections import defaultdict

SRC = r"<实验根目录>\ab-v3\datasets\cafe_sales_dirty.csv"
OUT = r"<实验根目录>\ab-v3\phase0\D2-cafe\SUB"

BAD = {"ERROR", "UNKNOWN", ""}

def clean(s):
    v = (s or "").strip()
    return None if v in BAD else v

def num(s):
    v = clean(s)
    if v is None:
        return None
    try:
        return float(v)
    except ValueError:
        return None

n_total = 0
miss_ts0 = miss_q0 = miss_item0 = 0
r2_fixed = 0
mismatch = 0
rows = []  # (item, q, ppu, ts_final, ts_valid, item_valid, ts_raw)

with open(SRC, newline="", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        n_total += 1
        item = clean(row["Item"])
        q = num(row["Quantity"])
        ppu = num(row["Price Per Unit"])
        ts_raw = num(row["Total Spent"])

        if clean(row["Total Spent"]) is None:
            miss_ts0 += 1
        if clean(row["Quantity"]) is None:
            miss_q0 += 1
        if item is None:
            miss_item0 += 1

        ts = ts_raw
        # R2
        if ts is None and q is not None and ppu is not None:
            ts = q * ppu
            r2_fixed += 1
        ts_valid = ts is not None

        # Q5: 修复前两者均有效但不一致（差 > 0.005）
        if ts_raw is not None and q is not None and ppu is not None and abs(ts_raw - q * ppu) > 0.005:
            mismatch += 1

        rows.append((item, q, ppu, ts, ts_valid, item is not None, ts_raw))

rev_total = sum(r[3] for r in rows if r[4])
agg = defaultdict(lambda: [0, 0.0])
for item, q, ppu, ts, ts_valid, item_valid, ts_raw in rows:
    if item_valid and ts_valid:
        agg[item][0] += 1
        agg[item][1] += ts

lines = []
lines.append(f"total_rows={n_total}")
lines.append(f"Q1_R2_fixed_rows={r2_fixed}")
lines.append(f"Q1_ts_valid_after_R2={sum(1 for r in rows if r[4])}")
lines.append(f"Q2_total_revenue={rev_total:.2f}")
lines.append(f"Q4_missing_before_fix: TotalSpent={miss_ts0}, Quantity={miss_q0}, Item={miss_item0}")
lines.append(f"Q5_mismatch_rows={mismatch}")
lines.append("Q3_item_table [n, revenue] desc by revenue:")
for item, (n, rev) in sorted(agg.items(), key=lambda kv: -kv[1][1]):
    lines.append(f"  {item}: n={n}, revenue={rev:.2f}")

report = "\n".join(lines)
print(report)
with open(OUT + r"\_results.txt", "w", encoding="utf-8") as f:
    f.write(report + "\n")
