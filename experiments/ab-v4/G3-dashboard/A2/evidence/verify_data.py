# -*- coding: utf-8 -*-
"""数据独立复算：从 index.html 提取 SALES 数组，独立计算各筛选范围的指标卡预期值。"""
import json
import re
import sys
from pathlib import Path

HTML = Path(__file__).resolve().parent.parent / "index.html"

def extract_sales():
    m = re.search(r"var\s+SALES\s*=\s*\[([^\]]+)\]", HTML.read_text(encoding="utf-8"))
    if not m:
        sys.exit("FAIL: 未在 index.html 中找到 SALES 数组")
    return [int(x) for x in m.group(1).split(",")]

def nice_avg(v):
    return round(round(v * 10) / 10, 1)

def main():
    sales = extract_sales()
    assert len(sales) == 12, f"FAIL: 应为 12 个月，实际 {len(sales)}"
    assert all(isinstance(v, int) and 0 < v < 10000 for v in sales), "FAIL: 数值超出合理区间"
    months = [f"{i+1}月" for i in range(12)]
    ranges = {"all": (0, 11), "q1": (0, 2), "q2": (3, 5), "q3": (6, 8), "q4": (9, 11)}
    out = {}
    for key, (a, b) in ranges.items():
        d = sales[a:b+1]
        total = sum(d)
        peak = max(d)
        out[key] = {
            "total": total,
            "avg_display": nice_avg(total / len(d)),
            "peak_month": months[a + d.index(peak)],
            "peak_value": peak,
            "n_months": len(d),
            "min_month": months[a], "max_month": months[b],
        }
    print(json.dumps({"sales": sales, "expected": out}, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
