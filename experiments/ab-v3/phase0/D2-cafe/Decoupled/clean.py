"""
D2 咖啡销售数据清洗 - 解耦版配置
验证层：Python独立计算 + 3种独立方法交叉验证 + 变异测试
流程层：全部省略（无门禁/审查/参照系）
"""
import csv
import json
import os
import random
from collections import defaultdict

SRC = r"<实验根目录>\ab-v3\datasets\cafe_sales_dirty.csv"
MISSING_TOKENS = {"ERROR", "UNKNOWN", ""}

def is_missing(val):
    return val is None or val.strip() in MISSING_TOKENS

def parse_float(val):
    if is_missing(val):
        return None
    try:
        return float(val)
    except ValueError:
        return None

# ========== 方法1：csv逐行处理（主方法）==========
def method1_csv_reader():
    repaired = 0
    valid_rows = 0
    total_revenue = 0.0
    missing_ts = missing_qty = missing_item = 0
    inconsistent = 0
    item_revenue = defaultdict(float)
    item_count = defaultdict(int)
    valid_ts_missing_item_rev = 0.0
    valid_ts_missing_item_cnt = 0

    with open(SRC, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ts = parse_float(row["Total Spent"])
            qty = parse_float(row["Quantity"])
            ppu = parse_float(row["Price Per Unit"])
            item = row["Item"].strip() if not is_missing(row["Item"]) else None

            if ts is None:
                missing_ts += 1
            if qty is None:
                missing_qty += 1
            if item is None:
                missing_item += 1

            # 修复TS：缺失但Qty和PPU都有效时
            if ts is None and qty is not None and ppu is not None:
                ts = qty * ppu
                repaired += 1

            # 不一致检查
            if ts is not None and qty is not None and ppu is not None:
                if abs(ts - qty * ppu) > 0.01:
                    inconsistent += 1

            # 有效行（有有效TS）
            if ts is not None:
                valid_rows += 1
                total_revenue += ts
                if item:
                    item_revenue[item] += ts
                    item_count[item] += 1
                else:
                    valid_ts_missing_item_rev += ts
                    valid_ts_missing_item_cnt += 1

    return {
        "repaired": repaired,
        "valid_rows": valid_rows,
        "total_revenue": round(total_revenue, 2),
        "missing_ts": missing_ts,
        "missing_qty": missing_qty,
        "missing_item": missing_item,
        "inconsistent": inconsistent,
        "item_revenue": dict(item_revenue),
        "item_count": dict(item_count),
        "valid_ts_missing_item_rev": round(valid_ts_missing_item_rev, 2),
        "valid_ts_missing_item_cnt": valid_ts_missing_item_cnt,
    }

# ========== 方法2：纯Python列表推导（独立实现，不同代码结构）==========
def method2_list_comprehension():
    with open(SRC, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    def get(row, key):
        v = row[key]
        return None if is_missing(v) else float(v)

    # 预处理：修复TS
    processed = []
    for r in rows:
        ts, qty, ppu = get(r, "Total Spent"), get(r, "Quantity"), get(r, "Price Per Unit")
        item = None if is_missing(r["Item"]) else r["Item"].strip()
        repaired_flag = False
        if ts is None and qty is not None and ppu is not None:
            ts = qty * ppu
            repaired_flag = True
        processed.append((ts, qty, ppu, item, repaired_flag))

    repaired = sum(1 for p in processed if p[4])
    valid = [p for p in processed if p[0] is not None]
    total_rev = sum(p[0] for p in valid)
    missing_ts = sum(1 for p in processed if p[0] is None and not p[4])  # 原始缺失
    # 注意：方法2的missing_ts统计口径需要和方法1一致（原始缺失，不含修复后）
    missing_ts_raw = sum(1 for r in rows if get(r, "Total Spent") is None)
    missing_qty = sum(1 for r in rows if get(r, "Quantity") is None)
    missing_item = sum(1 for r in rows if is_missing(r["Item"]))
    inconsistent = sum(1 for p in processed if p[0] is not None and p[1] is not None and p[2] is not None and abs(p[0] - p[1]*p[2]) > 0.01)

    item_rev = defaultdict(float)
    item_cnt = defaultdict(int)
    unclassified_rev = 0.0
    unclassified_cnt = 0
    for ts, qty, ppu, item, _ in valid:
        if item:
            item_rev[item] += ts
            item_cnt[item] += 1
        else:
            unclassified_rev += ts
            unclassified_cnt += 1

    return {
        "repaired": repaired,
        "valid_rows": len(valid),
        "total_revenue": round(total_rev, 2),
        "missing_ts": missing_ts_raw,
        "missing_qty": missing_qty,
        "missing_item": missing_item,
        "inconsistent": inconsistent,
        "item_revenue": dict(item_rev),
        "item_count": dict(item_cnt),
        "valid_ts_missing_item_rev": round(unclassified_rev, 2),
        "valid_ts_missing_item_cnt": unclassified_cnt,
    }

# ========== 方法3：收入分解公式验证（第三种独立路径）==========
def method3_formula_decomposition():
    """将总收入分解为'原始有效TS收入' + '修复TS收入'，独立求和验证"""
    raw_valid_revenue = 0.0
    repaired_revenue = 0.0
    repaired = 0
    with open(SRC, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ts = parse_float(row["Total Spent"])
            qty = parse_float(row["Quantity"])
            ppu = parse_float(row["Price Per Unit"])
            if ts is not None:
                raw_valid_revenue += ts
            elif qty is not None and ppu is not None:
                repaired_revenue += qty * ppu
                repaired += 1
    total = raw_valid_revenue + repaired_revenue
    return {
        "raw_valid_revenue": round(raw_valid_revenue, 2),
        "repaired_revenue": round(repaired_revenue, 2),
        "total_revenue": round(total, 2),
        "repaired": repaired,
    }

# ========== 变异测试：注入错误验证检测能力 ==========
def mutation_test():
    """复制数据，注入已知错误，验证清洗逻辑能发现"""
    import tempfile, os, shutil
    tmp = os.path.join(os.path.dirname(__file__), "evidence", "mutated_data.csv")
    shutil.copy(SRC, tmp)

    # 注入错误：修改第100行的Total Spent为错误值
    lines = []
    with open(tmp, encoding="utf-8") as f:
        lines = f.readlines()
    # 第101行（第100条数据，跳过表头）注入错误：把TS改成99999.99
    original_line = lines[100]
    parts = original_line.strip().split(",")
    parts[4] = "99999.99"  # Total Spent列
    lines[100] = ",".join(parts) + "\n"
    with open(tmp, "w", encoding="utf-8") as f:
        f.writelines(lines)

    # 用方法1的逻辑检测变异数据
    inconsistent_found = 0
    with open(tmp, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            ts = parse_float(row["Total Spent"])
            qty = parse_float(row["Quantity"])
            ppu = parse_float(row["Price Per Unit"])
            if ts is not None and qty is not None and ppu is not None:
                if abs(ts - qty * ppu) > 0.01:
                    inconsistent_found += 1

    os.remove(tmp)
    return {
        "mutation_injected": True,
        "inconsistent_detected": inconsistent_found,
        "test_passed": inconsistent_found >= 1,
    }

# ========== 主执行 ==========
if __name__ == "__main__":
    print("=== 方法1：csv逐行处理 ===")
    r1 = method1_csv_reader()
    print(f"  修复: {r1['repaired']}, 有效行: {r1['valid_rows']}, 总收入: {r1['total_revenue']}")
    print(f"  缺失TS/Qty/Item: {r1['missing_ts']}/{r1['missing_qty']}/{r1['missing_item']}")
    print(f"  不一致: {r1['inconsistent']}")

    print("\n=== 方法2：列表推导独立实现 ===")
    r2 = method2_list_comprehension()
    print(f"  修复: {r2['repaired']}, 有效行: {r2['valid_rows']}, 总收入: {r2['total_revenue']}")
    print(f"  缺失TS/Qty/Item: {r2['missing_ts']}/{r2['missing_qty']}/{r2['missing_item']}")
    print(f"  不一致: {r2['inconsistent']}")

    print("\n=== 方法3：收入分解公式 ===")
    r3 = method3_formula_decomposition()
    print(f"  原始有效收入: {r3['raw_valid_revenue']}, 修复收入: {r3['repaired_revenue']}")
    print(f"  总收入: {r3['total_revenue']}, 修复数: {r3['repaired']}")

    print("\n=== 变异测试 ===")
    mt = mutation_test()
    print(f"  注入错误后检测到不一致: {mt['inconsistent_detected']}, 测试通过: {mt['test_passed']}")

    # 交叉验证一致性检查
    print("\n=== 交叉验证一致性 ===")
    agree = (
        r1["total_revenue"] == r2["total_revenue"] == r3["total_revenue"]
        and r1["valid_rows"] == r2["valid_rows"]
        and r1["repaired"] == r2["repaired"] == r3["repaired"]
        and r1["missing_ts"] == r2["missing_ts"]
        and r1["missing_qty"] == r2["missing_qty"]
        and r1["missing_item"] == r2["missing_item"]
        and r1["inconsistent"] == r2["inconsistent"]
    )
    print(f"  核心指标三方法一致: {agree}")

    # 保存结果
    results = {
        "method1": r1,
        "method2": r2,
        "method3": r3,
        "mutation_test": mt,
        "cross_validation_agree": agree,
    }
    with open(os.path.join(os.path.dirname(__file__), "evidence", "results.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("\n结果已保存到 evidence/results.json")
