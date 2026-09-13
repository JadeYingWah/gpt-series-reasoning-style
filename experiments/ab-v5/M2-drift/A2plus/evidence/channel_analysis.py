# -*- coding: utf-8 -*-
"""A2+ 轻量+ 双路径交叉验证 · 方法A（数据类：Python 独立计算）
渠道 CTR 分析：完整性检查 + CTR + Wilson 95% 下界（保守口径）+ 排序。
运行: python channel_analysis.py
"""
import csv, math, sys, io

BASE = r"<实验根目录>\ab-v5\M2-drift\A2plus\evidence"
_buf = io.StringIO()

class _Tee:
    def __init__(self, *streams):
        self.streams = streams
    def write(self, s):
        for st in self.streams:
            try:
                st.write(s)
            except Exception:
                pass  # 单流失败（如 gbk 管道编码）不影响其他流
    def flush(self):
        for st in self.streams:
            try: st.flush()
            except Exception: pass

sys.stdout = _Tee(sys.stdout, _buf)  # 同时回传与写入 evidence 文件（harness stdout 通道不可靠时以文件为准）
Z = 1.959963985  # 95%

rows = list(csv.DictReader(open(BASE + r"\channel_data.csv", encoding="utf-8-sig")))

results = []
def check(name, ok, detail):
    results.append((name, "PASS" if ok else "FAIL", detail))

# --- 完整性检查（数据类必选验证前置） ---
check("完整性·行数=15", len(rows) == 15, f"rows={len(rows)}")
check("完整性·列数=3", all(len(r) == 3 for r in rows), f"cols={len(rows[0]) if rows else 0}")
bad_missing = [i for i, r in enumerate(rows) if not r["channel"] or r["impressions"] in ("", None) or r["clicks"] in ("", None)]
check("完整性·无缺失值", not bad_missing, f"缺失行={bad_missing or '无'}")
bad_range = []
for i, r in enumerate(rows):
    try:
        imp, clk = int(r["impressions"]), int(r["clicks"])
        if not (0 < clk < imp) or imp <= 0:
            bad_range.append(i)
    except ValueError:
        bad_range.append(i)
check("逻辑·0<clicks<impressions 且为整数", not bad_range, f"异常行={bad_range or '无'}")

# --- CTR + Wilson 下界 ---
def wilson_lower(clk, imp, z=Z):
    p = clk / imp
    denom = 1 + z * z / imp
    centre = p + z * z / (2 * imp)
    margin = z * math.sqrt(p * (1 - p) / imp + z * z / (4 * imp * imp))
    return (centre - margin) / denom

stats = []
for r in rows:
    imp, clk = int(r["impressions"]), int(r["clicks"])
    stats.append({
        "channel": r["channel"], "imp": imp, "clk": clk,
        "ctr": clk / imp, "wilson_lb": wilson_lower(clk, imp),
    })

by_ctr = sorted(stats, key=lambda s: -s["ctr"])
by_lb = sorted(stats, key=lambda s: -s["wilson_lb"])

tot_imp = sum(s["imp"] for s in stats)
tot_clk = sum(s["clk"] for s in stats)

print("方法A（程序化独立计算）")
print(f"{'渠道':<8}{'曝光':>8}{'点击':>7}{'CTR':>10}{'Wilson95下界':>14}")
for s in by_ctr:
    print(f"{s['channel']:<8}{s['imp']:>8}{s['clk']:>7}{s['ctr']*100:>9.4f}%{s['wilson_lb']*100:>13.4f}%")
print(f"\n总体: 曝光={tot_imp} 点击={tot_clk} 总CTR={tot_clk/tot_imp*100:.4f}%")
print(f"\nCTR排名Top3: {[(s['channel'], round(s['ctr']*100,4)) for s in by_ctr[:3]]}")
print(f"Wilson下界排名Top3: {[(s['channel'], round(s['wilson_lb']*100,4)) for s in by_lb[:3]]}")
print(f"小样本(n<2000)渠道: {[(s['channel'], s['imp'], round(s['wilson_lb']*100,2)) for s in stats if s['imp'] < 2000]}")
print(f"排名稳定性·CTR序与Wilson下界序Top3一致: {set(s['channel'] for s in by_ctr[:3]) == set(s['channel'] for s in by_lb[:3])}")

passed = sum(1 for r in results if r[1] == "PASS")
print("\n完整性/逻辑检查:")
for name, st, d in results:
    print(f"  [{st}] {name} — {d}")
print(f"结果: {passed}/{len(results)} PASS " + ("| ALL GREEN" if passed == len(results) else "| HAS FAIL"))

with open(BASE + r"\analysis_output.txt", "w", encoding="utf-8") as f:
    f.write(_buf.getvalue())
    f.write("\n(本文件由 channel_analysis.py 直接落盘生成)\n")
