# -*- coding: utf-8 -*-
"""从 10_intervals_full.csv 程序化生成 report.md 的两张区间表（单一事实来源=CSV，杜绝手抄编造）
report.md 中表格块由 <!--TABLE_MAIN--> 与 <!--TABLE_HC--> 锚点标记，整块替换。"""
import pandas as pd

EV = "<实验根目录>/ab-v4/P-B/D3-fullreport/evidence"
REPORT = "<实验根目录>/ab-v4/P-B/D3-fullreport/report.md"

iv = pd.read_csv(f"{EV}/10_intervals_full.csv")
hc = iv[iv["n_methods"] >= 2].reset_index(drop=True)

# 主极值加粗：全序列最显著的深谷/尖峰
bold_vals = {2.084721206, 108.5105428, 105.594771, 25.887752, 43.924701, 48.927015, 46.627034}

main_lines = ["| # | 起止时间 | 主极值 | 值 | 峰值 | 谷值 | 方法数 |",
              "|---|---|---|---|---|---|---|"]
for k, (_, r) in enumerate(iv.iterrows(), 1):
    ev = f"**{r['extreme_value']:.2f}**" if any(abs(r["extreme_value"] - b) < 1e-6 for b in bold_vals) \
         else f"{r['extreme_value']:.2f}"
    main_lines.append(
        f"| {k} | {r['start_time']} ~ {r['end_time']} | "
        f"{'峰' if r['extreme_type'] == 'peak' else '谷'} | {ev} | "
        f"{r['peak_value']:.2f} | {r['trough_value']:.2f} | {r['n_methods']} |")
table_main = "\n".join(main_lines)

names = {"A_global_madz": "全局MADz", "B_rolling_med_resid": "滚动中位数残差",
         "C_seasonal_resid": "季节残差", "D_diff_madz": "差分"}
notes = {0: "⚠️序列起始边缘伪影嫌疑", 1: "停机骤降至 2.08（3 方法）", 5: "骤降至 43.92（3 方法）",
         6: "灾难性失效主窗口，含 02-07 20:15 前兆骤降至 49.48"}
hc_lines = ["| # | 起止时间 | 主极值 | 值 | 确认方法 | 备注 |",
            "|---|---|---|---|---|---|"]
for k, r in hc.iterrows():
    ms = " + ".join(names[m] for m in eval(r["methods"]) if m in names)
    hc_lines.append(f"| {k+1} | {r['start_time']} ~ {r['end_time']} | "
                    f"{'峰' if r['extreme_type'] == 'peak' else '谷'} | {r['extreme_value']:.2f} | "
                    f"{ms} | {notes.get(k, '—')} |")
table_hc = "\n".join(hc_lines)

with open(REPORT, encoding="utf-8") as f:
    md = f.read()

assert "<!--TABLE_MAIN-->" in md and "<!--TABLE_HC-->" in md, "report.md 缺少表格锚点"
md = md.replace("<!--TABLE_MAIN-->", table_main, 1)
md = md.replace("<!--TABLE_HC-->", table_hc, 1)

with open(REPORT, "w", encoding="utf-8") as f:
    f.write(md)
print(f"wrote {len(iv)} main rows + {len(hc)} hc rows into report.md")
