# -*- coding: utf-8 -*-
"""
D2 咖啡馆销售数据清洗 · A1
按预注册规则执行：
  R1  字段值 strip 后为 ERROR / UNKNOWN / 空字符串 → 视为缺失
  R2  Total Spent 缺失但 Quantity 与 Price Per Unit 均有效 → Total Spent = Quantity × Price Per Unit
  R3  金额分析只用 R2 后 Total Spent 有效的行
  R4  按 Item 的分析只用 Item 有效的行
双独立实现交叉验证：实现A = 纯 Python + Decimal（权威）；实现B = pandas + float（核对）。
数据文件: <实验根目录>/ab-v3/datasets/cafe_sales_dirty.csv（只读）
"""
import csv
from decimal import Decimal

DATA = "<实验根目录>/ab-v3/datasets/cafe_sales_dirty.csv"
MISSING_TOKENS = {"ERROR", "UNKNOWN", ""}  # R1（strip 后比对）


def is_missing(raw):
    return (raw or "").strip() in MISSING_TOKENS


def to_dec(raw):
    """有效则返回 Decimal，否则 None。R1 已含非数值检查（探查确认数值列无非数值脏格式）。"""
    s = (raw or "").strip()
    if s in MISSING_TOKENS:
        return None
    try:
        return Decimal(s)
    except Exception:
        return None


# ---------------- 实现A：纯 Python + Decimal ----------------
rows = []
with open(DATA, newline="", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        rows.append(row)

n_total = len(rows)

# 修复前缺失统计（Q4）
miss_ts = sum(1 for r in rows if is_missing(r["Total Spent"]))
miss_qty = sum(1 for r in rows if is_missing(r["Quantity"]))
miss_item = sum(1 for r in rows if is_missing(r["Item"]))

# R2 修复
r2_fixed = 0
parsed = []  # (item_valid, item, qty, ppu, ts_orig, ts_after)
for r in rows:
    qty = to_dec(r["Quantity"])
    ppu = to_dec(r["Price Per Unit"])
    ts_o = to_dec(r["Total Spent"])
    ts = ts_o
    if ts is None and qty is not None and ppu is not None:
        ts = qty * ppu
        r2_fixed += 1
    item_raw = r["Item"].strip()
    item_valid = not is_missing(r["Item"])
    parsed.append((item_valid, item_raw, qty, ppu, ts_o, ts))

# Q1
ts_valid_after = sum(1 for p in parsed if p[5] is not None)

# Q2 总收入（R3：只用 R2 后 Total Spent 有效的行）
total_revenue = sum((p[5] for p in parsed if p[5] is not None), Decimal("0"))

# Q3 按 Item（R4：只用 Item 有效的行；收入同时受 R3 约束）
# 口径M(主)：交易数 = Item 有效行数；收入 = Item 有效 且 Total Spent(R2后)有效 之和
# 口径S(备)：交易数 = Item 有效 且 Total Spent(R2后)有效 行数（与收入同行数）
agg_m = {}   # item -> [count_rows, revenue]
agg_s = {}   # item -> [count_ts_valid, revenue]
for item_valid, item, qty, ppu, ts_o, ts in parsed:
    if not item_valid:
        continue
    key = item
    agg_m.setdefault(key, [0, Decimal("0")])
    agg_m[key][0] += 1
    if ts is not None:
        agg_m[key][1] += ts
        agg_s.setdefault(key, [0, Decimal("0")])
        agg_s[key][0] += 1
        agg_s[key][1] += ts
    else:
        agg_s.setdefault(key, [0, Decimal("0")])
table_m = sorted(agg_m.items(), key=lambda kv: (-kv[1][1], kv[0]))
table_s = sorted(agg_s.items(), key=lambda kv: (-kv[1][1], kv[0]))

# Q5 修复前不一致：TS、Q、PPU 均有效 且 |TS - Q*PPU| > 0.005
inconsistent = 0
max_diff = Decimal("0")
for item_valid, item, qty, ppu, ts_o, ts in parsed:
    if ts_o is not None and qty is not None and ppu is not None:
        diff = abs(ts_o - qty * ppu)
        if diff > Decimal("0.005"):
            inconsistent += 1
            if diff > max_diff:
                max_diff = diff

# ---------------- 实现B：sqlite3（标准库 SQL 引擎，独立计算路径） ----------------
# 注：pandas 未安装且任务书限定"python 及已装库可用"，故用 sqlite3 做独立实现交叉验证。
import sqlite3

con = sqlite3.connect(":memory:")
con.execute("""CREATE TABLE txn (
    txnid TEXT, item TEXT, qty TEXT, ppu TEXT, ts TEXT)""")
with open(DATA, newline="", encoding="utf-8-sig") as f:
    dr = csv.DictReader(f)
    data_rows = [(r["Transaction ID"], (r["Item"] or "").strip(),
                  (r["Quantity"] or "").strip(), (r["Price Per Unit"] or "").strip(),
                  (r["Total Spent"] or "").strip()) for r in dr]
con.executemany("INSERT INTO txn VALUES (?,?,?,?,?)", data_rows)

SQL_BASE = """
WITH base AS (
  SELECT item,
         CASE WHEN item IN ('ERROR','UNKNOWN','') THEN NULL ELSE item END AS item_ok,
         CASE WHEN qty  IN ('ERROR','UNKNOWN','') THEN NULL ELSE CAST(qty  AS REAL) END AS q,
         CASE WHEN ppu  IN ('ERROR','UNKNOWN','') THEN NULL ELSE CAST(ppu  AS REAL) END AS p,
         CASE WHEN ts   IN ('ERROR','UNKNOWN','') THEN NULL ELSE CAST(ts   AS REAL) END AS t0
  FROM txn), r2 AS (
  SELECT *, CASE WHEN t0 IS NULL AND q IS NOT NULL AND p IS NOT NULL
                 THEN q * p ELSE t0 END AS t1 FROM base)
"""
b_miss = dict(con.execute(SQL_BASE + """SELECT 'TS', SUM(t0 IS NULL) FROM r2
    UNION ALL SELECT 'Qty', SUM(q IS NULL) FROM r2
    UNION ALL SELECT 'Item', SUM(item_ok IS NULL) FROM r2""").fetchall())
b_fixed, b_ts_valid = con.execute(SQL_BASE + """SELECT SUM(t0 IS NULL AND q IS NOT NULL AND p IS NOT NULL),
       SUM(t1 IS NOT NULL) FROM r2""").fetchone()
b_rev = con.execute(SQL_BASE + "SELECT ROUND(SUM(t1),2) FROM r2 WHERE t1 IS NOT NULL").fetchone()[0]
b_incons = con.execute(SQL_BASE + """SELECT COUNT(*) FROM r2
    WHERE t0 IS NOT NULL AND q IS NOT NULL AND p IS NOT NULL AND ABS(t0 - q*p) > 0.005""").fetchone()[0]
b_tbl = con.execute(SQL_BASE + """SELECT item, SUM(item_ok IS NOT NULL) AS cnt_m,
       SUM(CASE WHEN item_ok IS NOT NULL AND t1 IS NOT NULL THEN 1 ELSE 0 END) AS cnt_s,
       ROUND(SUM(CASE WHEN item_ok IS NOT NULL AND t1 IS NOT NULL THEN t1 ELSE 0 END),2) AS rev
    FROM r2 WHERE item_ok IS NOT NULL GROUP BY item ORDER BY rev DESC, item""").fetchall()

# ---------------- 交叉验证 ----------------
print("=" * 64)
print("实现A（纯 Python + Decimal，权威）")
print("=" * 64)
print(f"[Q4] 修复前缺失  Total Spent={miss_ts}  Quantity={miss_qty}  Item={miss_item}")
print(f"[Q1] R2 修复行数={r2_fixed}   R2 后 Total Spent 有效行数={ts_valid_after}")
print(f"[Q2] 总收入 = {total_revenue:.2f}")
print(f"[Q5] 修复前不一致行数(差>0.005) = {inconsistent}  (最大差={max_diff})")
print("[Q3] 按 Item 表（口径M：交易数=Item有效行数；收入=R3口径）按收入降序：")
for k, (c, rev) in table_m:
    print(f"     {k:<10} 交易数={c:<6} 收入={rev:.2f}")
print("[Q3-备] 口径S：交易数=Item有效且TS(R2后)有效 行数：")
for k, (c, rev) in table_s:
    print(f"     {k:<10} 交易数={c:<6} 收入={rev:.2f}")

print()
print("=" * 64)
print("交叉验证（实现B sqlite3 vs 实现A）")
print("=" * 64)
checks = [
    ("Q4 TS 缺失", b_miss["TS"], miss_ts),
    ("Q4 Qty 缺失", b_miss["Qty"], miss_qty),
    ("Q4 Item 缺失", b_miss["Item"], miss_item),
    ("Q1 R2修复", b_fixed, r2_fixed),
    ("Q1 TS有效", b_ts_valid, ts_valid_after),
    ("Q2 总收入", b_rev, float(total_revenue)),
    ("Q5 不一致", b_incons, inconsistent),
]
ok = True
for name, b, a in checks:
    match = abs(b - a) < 1e-6
    ok &= match
    print(f"  {name}: A={a}  B={b}  {'一致' if match else '***不一致***'}")
rev_b_tbl = {k: (int(cm), int(cs), float(rev)) for k, cm, cs, rev in b_tbl}
for k, (c, rev) in table_s:
    bcm, bcs, brev = rev_b_tbl[k]
    m1 = (bcs == c) and abs(brev - float(rev)) < 0.01
    ok &= m1
    print(f"  Q3 {k}: A=({c},{float(rev):.2f})  B口径S=({bcs},{brev})  {'一致' if m1 else '***不一致***'}")
cnt_ok = all(rev_b_tbl[k][0] == v[0] for k, v in agg_m.items())
ok &= cnt_ok
print(f"  Q3 口径M 计数: {'一致' if cnt_ok else '***不一致***'}")
print()
print("交叉验证总结:", "全部一致 PASS" if ok else "存在不一致 FAIL")
