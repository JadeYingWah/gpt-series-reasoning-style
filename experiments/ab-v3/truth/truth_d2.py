# -*- coding: utf-8 -*-
"""D2 真值脚本：Dirty Cafe Sales — 按任务书预注册清洗规则（R1-R4）计算，输出冻结 JSON。
真值以冻结文件字节为准（<实验根目录>/ab-v3/datasets/cafe_sales_dirty.csv）。

预注册清洗规则（与任务书一致）：
R1 字段值 strip 后为 "ERROR" / "UNKNOWN" / "" 视为缺失（None）
R2 Total Spent 缺失但 Quantity 与 Price Per Unit 均有效 → Total Spent = Quantity × Price Per Unit
R3 金额分析仅用 R2 后 Total Spent 有效的行
R4 Item 分析仅用 Item 有效的行
"""
import csv, json, hashlib

SRC = "<实验根目录>/ab-v3/datasets/cafe_sales_dirty.csv"
OUT = "<实验根目录>/ab-v3/truth/frozen/d2_truth.json"

with open(SRC, "rb") as f:
    sha = hashlib.sha256(f.read()).hexdigest()

def norm(v):
    if v is None:
        return None
    v = v.strip()
    if v == "" or v.upper() in ("ERROR", "UNKNOWN"):
        return None
    return v

rows = []
with open(SRC, newline="", encoding="utf-8") as f:
    rdr = csv.DictReader(f)
    for rec in rdr:
        rows.append({k.strip(): norm(v) for k, v in rec.items()})

n_all = len(rows)
miss_total = sum(1 for r in rows if r["Total Spent"] is None)
miss_qty = sum(1 for r in rows if r["Quantity"] is None)
miss_item = sum(1 for r in rows if r["Item"] is None)

def fnum(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None

repaired = 0
for r in rows:
    t = fnum(r["Total Spent"]); q = fnum(r["Quantity"]); p = fnum(r["Price Per Unit"])
    if t is None and q is not None and p is not None:
        r["Total Spent"] = repr(round(q * p, 2))
        repaired += 1

money_rows = [r for r in rows if fnum(r["Total Spent"]) is not None]
total_revenue = round(sum(fnum(r["Total Spent"]) for r in money_rows), 2)

inconsistent = 0
for r in rows:
    t = fnum(r["Total Spent"]); q = fnum(r["Quantity"]); p = fnum(r["Price Per Unit"])
    if t is not None and q is not None and p is not None and abs(t - q * p) > 0.005:
        inconsistent += 1

by_item = {}
for r in money_rows:
    item = r["Item"]
    if item is None:
        continue
    c, s = by_item.get(item, (0, 0.0))
    by_item[item] = (c + 1, s + fnum(r["Total Spent"]))
item_table = sorted(
    [[k, c, round(s, 2)] for k, (c, s) in by_item.items()],
    key=lambda x: x[2], reverse=True,
)

out = {
    "task": "D2-cafe",
    "source_sha256": sha,
    "n_rows_all": n_all,
    "missing_pre_repair": {"Total Spent": miss_total, "Quantity": miss_qty, "Item": miss_item},
    "repaired_by_rule_R2": repaired,
    "n_rows_valid_total_after_R2": len(money_rows),
    "total_revenue_2dp": total_revenue,
    "total_vs_qty_price_inconsistent_rows": inconsistent,
    "item_table_count_revenue_desc": item_table,
}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print("D2 truth OK:", n_all, "rows ->", OUT)
print(json.dumps(out["missing_pre_repair"], ensure_ascii=False), "repaired:", repaired, "revenue:", total_revenue)
