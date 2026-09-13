# -*- coding: utf-8 -*-
"""
D2 咖啡馆销售数据清�? + 分析
预注册规则：
  R1 字段�? strip 后为 ERROR / UNKNOWN / 空字符串 -> 视为缺失
  R2 Total Spent 缺失�? Quantity �? Price Per Unit 均有�? -> Total Spent = Quantity * Price Per Unit
  R3 金额分析只用 R2 �? Total Spent 有效的行
  R4 �? Item 的分析只�? Item 有效的行
本脚本含两套独立实现（纯Python csv / sqlite3 SQL），输出双结果与交叉比对�?
"""
import csv
import sys

DATA = r"<ʵ���Ŀ¼>\ab-v3\datasets\cafe_sales_dirty.csv"
MISSING_TOKENS = {"error", "unknown", ""}


def is_missing(raw):
    return str(raw).strip().lower() in MISSING_TOKENS


def parse_num(raw):
    """有效数�?�返�? float，否�? None�?"""
    if is_missing(raw):
        return None
    try:
        return float(str(raw).strip())
    except ValueError:
        return None


# ---------------- 实现 B：纯 Python csv（独立基准实现） ----------------
def run_pure_python(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        idx = {name: i for i, name in enumerate(header)}
        for r in reader:
            if not any(cell.strip() for cell in r):
                continue
            rows.append(r)
    n = len(rows)

    def col(r, name):
        return r[idx[name]]

    # Q4: 修复前缺失统�?
    miss_ts = sum(1 for r in rows if is_missing(col(r, "Total Spent")))
    miss_qty = sum(1 for r in rows if is_missing(col(r, "Quantity")))
    miss_item = sum(1 for r in rows if is_missing(col(r, "Item")))

    # Q1: R2 修复
    repaired = 0
    ts_valid_after = 0
    for r in rows:
        ts = parse_num(col(r, "Total Spent"))
        q = parse_num(col(r, "Quantity"))
        p = parse_num(col(r, "Price Per Unit"))
        if ts is None and q is not None and p is not None:
            ts = q * p
            repaired += 1
        if ts is not None:
            ts_valid_after += 1
            r[idx["Total Spent"]] = repr(ts)  # 写回修复值，供后续统�?

    # Q2: 总收入（R3�?
    total_revenue = sum(
        parse_num(col(r, "Total Spent"))
        for r in rows
        if parse_num(col(r, "Total Spent")) is not None
    )

    # Q3: �? Item（R4 + R3 口径：Item 有效�? Total Spent 有效�?
    agg = {}
    agg_all = {}  # 参�?�口径：�? Item 有效即计�?
    for r in rows:
        item_raw = col(r, "Item").strip()
        if is_missing(item_raw):
            continue
        item = item_raw
        ts = parse_num(col(r, "Total Spent"))
        agg.setdefault(item, [0, 0.0])
        agg_all.setdefault(item, [0, 0.0])
        agg_all[item][0] += 1
        if ts is not None:
            agg[item][0] += 1
            agg[item][1] += ts

    # Q5: TS �? Q*P 均有效但不一致（�?>0.005），按原始数�?
    inconsistent = 0
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)
        for r in reader:
            if not any(cell.strip() for cell in r):
                continue
            ts = parse_num(r[idx["Total Spent"]])
            q = parse_num(r[idx["Quantity"]])
            p = parse_num(r[idx["Price Per Unit"]])
            if ts is not None and q is not None and p is not None and abs(ts - q * p) > 0.005:
                inconsistent += 1

    return {
        "rows": n,
        "q1_repaired": repaired,
        "q1_ts_valid_after": ts_valid_after,
        "q2_total_revenue": round(total_revenue, 2),
        "q3_item": dict(sorted(agg.items(), key=lambda kv: -kv[1][1])),
        "q3_item_allcount_ref": {k: v[0] for k, v in sorted(agg_all.items())},
        "q4": {"Total Spent": miss_ts, "Quantity": miss_qty, "Item": miss_item},
        "q5_inconsistent": inconsistent,
    }


# ---------------- 实现 A：sqlite3（独�? SQL 计算引擎�? ----------------
def run_sqlite(path):
    import sqlite3

    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = [r for r in reader if any(c.strip() for c in r)]

    con = sqlite3.connect(":memory:")
    con.execute(
        'CREATE TABLE t ("Transaction ID" TEXT, Item TEXT, Quantity TEXT, '
        '"Price Per Unit" TEXT, "Total Spent" TEXT, "Payment Method" TEXT, '
        'Location TEXT, "Transaction Date" TEXT)'
    )
    con.executemany(
        'INSERT INTO t VALUES (?,?,?,?,?,?,?,?)',
        [tuple(r[i] for i in range(len(header))) for r in rows],
    )

    def num(col):
        return (f"CASE WHEN upper(trim({col})) IN ('ERROR','UNKNOWN','') OR trim({col}) IS NULL "
                f"THEN NULL ELSE CAST(trim({col}) AS REAL) END")

    ts0, q0, p0 = num('"Total Spent"'), num("Quantity"), num('"Price Per Unit"')
    item_ok = ("upper(trim(Item)) NOT IN ('ERROR','UNKNOWN','') AND trim(Item) IS NOT NULL")

    q = f"""
    WITH base AS (
      SELECT {ts0} AS ts0, {q0} AS q0, {p0} AS p0,
             CASE WHEN {item_ok} THEN trim(Item) END AS item
      FROM t
    ),
    fixed AS (
      SELECT *, CASE WHEN ts0 IS NULL AND q0 IS NOT NULL AND p0 IS NOT NULL
                     THEN q0 * p0 ELSE ts0 END AS ts1
      FROM base
    )
    SELECT
      (SELECT COUNT(*) FROM fixed),
      (SELECT COUNT(*) FROM fixed WHERE ts0 IS NULL AND q0 IS NOT NULL AND p0 IS NOT NULL),
      (SELECT COUNT(*) FROM fixed WHERE ts1 IS NOT NULL),
      (SELECT ROUND(SUM(ts1), 2) FROM fixed WHERE ts1 IS NOT NULL),
      (SELECT COUNT(*) FROM fixed WHERE ts0 IS NOT NULL AND q0 IS NOT NULL AND p0 IS NOT NULL
         AND ABS(ts0 - q0 * p0) > 0.005)
    """
    nrows, repaired, ts_valid_after, total_rev, inconsistent = con.execute(q).fetchone()

    miss = {}
    for col in ('"Total Spent"', "Quantity", "Item"):
        cnt = con.execute(
            f"SELECT COUNT(*) FROM t WHERE upper(trim({col})) IN ('ERROR','UNKNOWN','') "
            f"OR trim({col}) IS NULL"
        ).fetchone()[0]
        miss[col.strip('"')] = cnt

    base_sql = (
        f"SELECT {ts0} AS ts0, {q0} AS q0, {p0} AS p0, "
        f"CASE WHEN {item_ok} THEN trim(Item) END AS item FROM t"
    )
    item_rows2 = con.execute(f"""
        SELECT item, COUNT(ts1), ROUND(SUM(ts1), 2)
        FROM (SELECT *, CASE WHEN ts0 IS NULL AND q0 IS NOT NULL AND p0 IS NOT NULL
                             THEN q0 * p0 ELSE ts0 END AS ts1 FROM ({base_sql}))
        WHERE item IS NOT NULL AND ts1 IS NOT NULL GROUP BY item ORDER BY SUM(ts1) DESC
    """).fetchall()
    ref_all = dict(con.execute(
        f'SELECT item, COUNT(*) FROM t WHERE {item_ok} GROUP BY item'
    ).fetchall())
    con.close()

    return {
        "rows": nrows,
        "q1_repaired": repaired,
        "q1_ts_valid_after": ts_valid_after,
        "q2_total_revenue": total_rev,
        "q3_item": {k: [c, r] for k, c, r in item_rows2},
        "q3_item_allcount_ref": ref_all,
        "q4": miss,
        "q5_inconsistent": inconsistent,
    }


def main():
    res_pure = run_pure_python(DATA)
    res_sql = run_sqlite(DATA)

    def cmp(a, b, path=""):
        diffs = []
        if isinstance(a, dict) and isinstance(b, dict):
            for k in set(a) | set(b):
                diffs += cmp(a.get(k), b.get(k), f"{path}.{k}")
        elif isinstance(a, (int, float)) and isinstance(b, (int, float)):
            if abs(a - b) > 1e-6:
                diffs.append(f"{path}: pure={a} sqlite={b}")
        elif a != b:
            diffs.append(f"{path}: pure={a} pandas={b}")
        return diffs

    diffs = cmp(res_pure, res_sql)
    print("=== 交叉验证 ===")
    print("两套独立实现差异:", diffs if diffs else "无（全部�?致）")

    print("\n=== 结果（sqlite 实现�? ===")
    for k, v in res_sql.items():
        print(f"{k}: {v}")

    print("\n=== Q3 收入降序表（有效交易�?, 收入�? ===")
    for item, (cnt, rev) in res_sql["q3_item"].items():
        print(f"{item}\t{cnt}\t{rev:.2f}")

    # �?出码：不�?致则�? 0，供验证流程捕获
    sys.exit(1 if diffs else 0)


if __name__ == "__main__":
    main()
