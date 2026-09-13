# -*- coding: utf-8 -*-
"""交付验证：可检查完成标准逐项核验（失败以非零退出码结束）
①≥2 种独立方法脚本存在且 summary 齐全 ②合并区间数>0 且每区间四要素齐备
③report.md 区间表与 merged_intervals.csv 双向一致 ④抽查点核验 ⑤网格完整性
"""
import pandas as pd
import numpy as np
import json, os, re, sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
DATA = "<实验根目录>/ab-v3/datasets/nab_machine_temp.csv"
fails = []

def check(name, ok, detail=""):
    print(("PASS" if ok else "FAIL"), name, detail)
    if not ok:
        fails.append(name)

# ① 方法与证据文件
for m in ["m1", "m2", "m3"]:
    for suf in ["_intervals.csv", "_scores.csv", "_summary.json"]:
        check(f"{m}{suf} 存在", os.path.exists(f"{BASE}/{m}{suf}"))
summaries = {m: json.load(open(f"{BASE}/{m}_summary.json")) for m in ["m1", "m2", "m3"]}
n_methods_with_intervals = sum(1 for m in summaries if summaries[m]["n_intervals"] > 0)
check("≥2 独立方法产出区间", n_methods_with_intervals >= 2, f"={n_methods_with_intervals}")

# ② 合并区间
mdf = pd.read_csv(f"{BASE}/merged_intervals.csv")
check("合并区间数 > 0", len(mdf) > 0, f"={len(mdf)}")
four = mdf["start"].notna() & mdf["end"].notna() & mdf["kind"].notna() & \
       (mdf["peak"].notna() | mdf["trough"].notna())
check("每区间含起止/kind/极值四要素", bool(four.all()), f"完整 {int(four.sum())}/{len(mdf)}")

# ③ report.md 与 CSV 双向一致
report = open(f"{ROOT}/report.md", encoding="utf-8").read()
rows = re.findall(r"\|\s*(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s*\|\s*(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s*\|", report)
check("report 区间行数 == CSV 行数", len(rows) == len(mdf), f"report={len(rows)} csv={len(mdf)}")
csv_pairs = set(zip(mdf["start"], mdf["end"]))
rep_pairs = set(rows)
check("report 区间集合 == CSV 区间集合", csv_pairs == rep_pairs,
      f"仅CSV有={len(csv_pairs-rep_pairs)} 仅report有={len(rep_pairs-csv_pairs)}")
check("report 声明的区间数与实际一致",
      f"共 {len(mdf)} 个异常区间" in report or f"共{len(mdf)}个异常区间" in report)

# ④ 抽查点核验（12-16 17:25 值 2.085 必须被检出）
df = pd.read_csv(DATA, parse_dates=["timestamp"])
df = df.drop_duplicates(subset="timestamp", keep="first").sort_values("timestamp").reset_index(drop=True)
tgt = df.index[df["timestamp"] == "2013-12-16 17:25:00"][0]
for m in ["m1", "m2", "m3"]:
    sc = pd.read_csv(f"{BASE}/{m}_scores.csv")
    col = "score" if "score" in sc.columns else "diff"
    check(f"抽查点 12-16 17:25 被 {m} 检出", bool(sc.iloc[tgt]["anom"]),
          f"{col}={sc.iloc[tgt][col]}")
# 冻结平坦段被 M2 覆盖（2014-02-08 06:00 值）
tgt2 = df.index[df["timestamp"] == "2014-02-08 06:00:00"][0]
sc2 = pd.read_csv(f"{BASE}/m2_scores.csv")
check("抽查点 02-08 06:00(冻结平坦段) 被 M2 检出", bool(sc2.iloc[tgt2]["anom"]),
      f"value={df.iloc[tgt2]['value']:.2f} score={sc2.iloc[tgt2]['score']}")

# ⑤ 网格完整性
t = df["timestamp"]
check("清洗后网格完整(22683)", len(df) == 22683 and t.is_monotonic_increasing, f"n={len(df)}")

# ⑥ 交叉验证证据
cv = json.load(open(f"{BASE}/cross_validation.json"))
check("交叉验证 JSON 存在且含 3 对比较", len(cv["pairwise"]) == 3)
check("cross_validation.md 存在", os.path.exists(f"{BASE}/cross_validation.md"))
check("data_quality.md 存在", os.path.exists(f"{BASE}/data_quality.md"))

print("\n==>", "ALL PASS" if not fails else f"FAILED: {fails}")
sys.exit(0 if not fails else 1)
