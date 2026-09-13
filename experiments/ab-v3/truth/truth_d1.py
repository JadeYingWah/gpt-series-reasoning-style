# -*- coding: utf-8 -*-
"""D1 真值脚本：UCI Wine Quality (red) — spawn 前独立计算，输出冻结 JSON。
真值以冻结文件字节为准（<实验根目录>/ab-v3/datasets/winequality-red.csv）。
"""
import csv, json, math, hashlib, sys

SRC = "<实验根目录>/ab-v3/datasets/winequality-red.csv"
OUT = "<实验根目录>/ab-v3/truth/frozen/d1_truth.json"

with open(SRC, "rb") as f:
    sha = hashlib.sha256(f.read()).hexdigest()

rows = []
with open(SRC, newline="", encoding="utf-8") as f:
    rdr = csv.reader(f, delimiter=";")
    header = [h.strip().strip('"') for h in next(rdr)]
    for rec in rdr:
        if not rec or all(not c.strip() for c in rec):
            continue
        rows.append([float(c) for c in rec])

qi = header.index("quality")
ai = header.index("alcohol")
n = len(rows)

def pearson(xs, ys):
    n_ = len(xs)
    mx = sum(xs) / n_
    my = sum(ys) / n_
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    sy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return cov / (sx * sy)

corr = {}
for j, name in enumerate(header):
    if j == qi:
        continue
    corr[name] = round(pearson([r[j] for r in rows], [r[qi] for r in rows]), 6)

corr_sorted = sorted(corr.items(), key=lambda kv: abs(kv[1]), reverse=True)

qcount = {}
for r in rows:
    qcount[int(r[qi])] = qcount.get(int(r[qi]), 0) + 1

hi = [r[ai] for r in rows if r[qi] >= 7]
lo = [r[ai] for r in rows if r[qi] <= 4]
m_hi = round(sum(hi) / len(hi), 4)
m_lo = round(sum(lo) / len(lo), 4)

out = {
    "task": "D1-winequality",
    "source_sha256": sha,
    "n_rows": n,
    "n_cols": len(header),
    "pearson_vs_quality_sorted_by_absdesc": [[k, v] for k, v in corr_sorted],
    "quality_counts": {str(k): v for k, v in sorted(qcount.items())},
    "alcohol_mean_q_ge7": m_hi,
    "alcohol_mean_q_le4": m_lo,
    "alcohol_mean_diff_hi_minus_lo": round(m_hi - m_lo, 4),
}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print("D1 truth OK:", n, "rows ->", OUT)
