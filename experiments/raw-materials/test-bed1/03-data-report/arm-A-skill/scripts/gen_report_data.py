# -*- coding: utf-8 -*-
"""生成 3 地区 x 12 个月销售数据并计算关键指标。

可复现：固定随机种子 SEED=42。
输出：同目录 data.json（报告数据源）+ 控制台关键数字摘要。
运行：python gen_report_data.py
"""
import json
import os
import random

SEED = 42
random.seed(SEED)

MONTHS = [f"2025-{m:02d}" for m in range(1, 13)]

# 各地区基准销售额（万元）与月增长率（%），带季节因子
REGIONS = {
    "华东": {"base": 820.0, "growth": 1.8, "vol": 0.06},
    "华南": {"base": 610.0, "growth": 2.6, "vol": 0.08},
    "华北": {"base": 430.0, "growth": 1.2, "vol": 0.10},
}

# 季节因子：2 月春节低谷，6 月年中促销小峰，11-12 月旺季
SEASON = [0.92, 0.78, 1.02, 1.00, 1.03, 1.10, 0.98, 0.97, 1.02, 1.05, 1.14, 1.19]


def gen_data():
    data = {}
    for region, p in REGIONS.items():
        series = []
        for i in range(12):
            v = p["base"] * ((1 + p["growth"] / 100) ** i) * SEASON[i]
            v *= 1 + random.uniform(-p["vol"], p["vol"])
            series.append(round(v, 1))
        data[region] = series
    return data


def metrics(data):
    grand_total = 0.0
    region_totals = {}
    region_cagr = {}
    region_avg_mom = {}
    for region, series in data.items():
        total = sum(series)
        region_totals[region] = round(total, 1)
        grand_total += total
        # 口径A：复合月均增长率（首月末月几何折算）
        region_cagr[region] = round((series[-1] / series[0]) ** (1 / 11) - 1, 6)
        # 口径B：逐月环比算术平均
        moms = [series[i] / series[i - 1] - 1 for i in range(1, 12)]
        region_avg_mom[region] = round(sum(moms) / len(moms), 6)

    # 全盘合计后的整体月均增长
    monthly_total = [round(sum(data[r][m] for r in data), 1) for m in range(12)]
    all_cagr = (monthly_total[-1] / monthly_total[0]) ** (1 / 11) - 1
    all_moms = [monthly_total[m] / monthly_total[m - 1] - 1 for m in range(1, 12)]
    best = max(region_totals, key=region_totals.get)

    return {
        "grand_total": round(grand_total, 1),
        "region_totals": region_totals,
        "best_region": best,
        "region_cagr": region_cagr,
        "region_avg_mom": region_avg_mom,
        "monthly_total": monthly_total,
        "all_cagr": round(all_cagr, 6),
        "all_avg_mom": round(sum(all_moms) / len(all_moms), 6),
        "all_mom_series": [round(x, 6) for x in all_moms],
    }


def main():
    out_dir = os.path.dirname(os.path.abspath(__file__))
    data = gen_data()
    m = metrics(data)
    payload = {
        "seed": SEED,
        "months": MONTHS,
        "data": data,
        **m,
    }
    path = os.path.join(out_dir, "data.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print("=== 关键数字摘要（口径：万元）===")
    for r, s in data.items():
        print(f"{r}: 首月={s[0]:>7.1f}  末月={s[-1]:>7.1f}  年合计={m['region_totals'][r]:>8.1f}")
    print(f"全盘月合计: {m['monthly_total']}")
    print(f"总销售额   = {m['grand_total']}")
    print(f"最高地区   = {m['best_region']} ({m['region_totals'][m['best_region']]} 万元, "
          f"占比 {m['region_totals'][m['best_region']] / m['grand_total'] * 100:.1f}%)")
    print(f"整体复合月均增长(口径A) = {m['all_cagr'] * 100:.2f}%/月")
    print(f"整体环比均值(口径B)     = {m['all_avg_mom'] * 100:.2f}%/月")
    for r in data:
        print(f"  {r}: 口径A={m['region_cagr'][r]*100:.2f}%/月  口径B={m['region_avg_mom'][r]*100:.2f}%/月")
    print(f"\ndata.json 已写入: {path}")


if __name__ == "__main__":
    main()
