# -*- coding: utf-8 -*-
"""D3 真值脚本：NAB machine_temperature_system_failure — 提取官方标注异常窗口，输出冻结 JSON。
真值 = NAB 官方 combined_labels.json 中该数据集的窗口列表（第三方标注，非执行者生成）。
"""
import json, hashlib, csv

SRC = "<实验根目录>/ab-v3/datasets/nab_machine_temp.csv"
LBL = "<实验根目录>/ab-v3/datasets/nab_combined_labels.json"
OUT = "<实验根目录>/ab-v3/truth/frozen/d3_truth.json"

with open(SRC, "rb") as f:
    sha_data = hashlib.sha256(f.read()).hexdigest()
with open(LBL, "rb") as f:
    sha_lbl = hashlib.sha256(f.read()).hexdigest()

with open(LBL, encoding="utf-8") as f:
    labels = json.load(f)
key = "realKnownCause/machine_temperature_system_failure.csv"
# combined_labels.json 该条目为「异常时间点列表」（每处异常一个时间戳），非 [start,end] 区间对
anomaly_points = labels[key]

n_rows = 0
first_ts = last_ts = None
with open(SRC, newline="", encoding="utf-8") as f:
    rdr = csv.reader(f)
    next(rdr)
    for rec in rdr:
        if not rec or not rec[0].strip():
            continue
        n_rows += 1
        if first_ts is None:
            first_ts = rec[0]
        last_ts = rec[0]

out = {
    "task": "D3-nab",
    "data_sha256": sha_data,
    "labels_sha256": sha_lbl,
    "label_source": "NAB official combined_labels.json (third-party ground truth)",
    "n_rows": n_rows,
    "time_range": [first_ts, last_ts],
    "n_anomaly_points": len(anomaly_points),
    "anomaly_points_labeled": anomaly_points,
    "scoring_rule_preregistered": "报告的每个异常区间命中判定：区间包含某标注时间点，或区间起止任一端距某标注时间点 <=1 小时；每个标注点最多被一个报告区间计数（先到先得）；窗口级 recall=命中数/4，precision=命中区间数/报告区间总数",
}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print("D3 truth OK:", n_rows, "rows,", len(anomaly_points), "labeled anomaly points ->", OUT)
for p in anomaly_points:
    print("  ", p)
