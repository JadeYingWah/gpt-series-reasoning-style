#!/usr/bin/env python3
"""ab-v4 D3 客观检查：报告区间 vs NAB 官方标注（±60min 容差，与 Phase 0 预注册口径一致）"""
import json, re, csv, sys
from pathlib import Path
from datetime import datetime, timedelta

V4 = Path(r"<实验根目录>\ab-v4")
LABELS = json.loads((V4 / "truth" / "nab_combined_labels.json").read_text(encoding="utf-8"))
# machine_temperature_system_failure 的官方标注点（NAB combined_labels）
KEY = [k for k in LABELS if "machine_temperature" in k][0]
OFFICIAL = [datetime.strptime(t, "%Y-%m-%d %H:%M:%S") for t in LABELS[KEY]]
TOL = timedelta(minutes=60)

def parse_ts(s):
    s = s.strip().strip("[]() ")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None

def extract_intervals(report_text):
    """从 report.md 提取 [起, 止] 区间——含 Phase 0 教训修复：>7d 的行是元数据描述非检测区间，剔除"""
    intervals = []
    for line in report_text.splitlines():
        stamps = re.findall(r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(?::\d{2})?", line)
        if len(stamps) >= 2:
            a, b = parse_ts(stamps[0]), parse_ts(stamps[-1])
            if a and b and a <= b:
                # Phase 0 教训：跨度 >7 天的行是数据范围描述（元数据），不是检测区间
                if (b - a) > timedelta(days=7):
                    continue
                intervals.append((a, b))
    return intervals

def hit_count(intervals):
    """官方标注点落入任一报告区间（±TOL）即命中；返回 (recall 命中数, detail)"""
    detail = []
    hits = 0
    for lab in OFFICIAL:
        matched_idx = None
        for i, (a, b) in enumerate(intervals):
            if a - TOL <= lab <= b + TOL:
                matched_idx = i
                break
        detail.append({"label": lab.strftime("%Y-%m-%d %H:%M"), "hit": matched_idx is not None, "interval_idx": matched_idx})
        if matched_idx is not None:
            hits += 1
    return hits, detail

def main():
    out = {}
    for arm in ["D3-conservative", "D3-noconstraint", "D3-fullreport", "D3-interrupt"]:
        rpt = V4 / "P-B" / arm / "report.md"
        if not rpt.exists():
            out[arm] = {"exists": False}
            continue
        text = rpt.read_text(encoding="utf-8")
        intervals = extract_intervals(text)
        hits, detail = hit_count(intervals)
        n = len(intervals)
        out[arm] = {
            "exists": True,
            "n_intervals_parsed": n,
            "official_points": len(OFFICIAL),
            "hits": hits,
            "recall": round(hits / len(OFFICIAL), 4) if n else 0.0,
            "precision": round(hits / n, 4) if n else 0.0,
            "detail": detail,
            "note": "宽松解析（含表格行/候选区间行），正式判分须人工剔除附录候选后重算",
        }
    print(json.dumps(out, ensure_ascii=False, indent=2))
    (V4 / "truth" / "objective_d3_auto.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()
