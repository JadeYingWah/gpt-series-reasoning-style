# -*- coding: utf-8 -*-
"""A2 轻量配置臂 · 独立验证（不依赖 apply 脚本的中间状态，直接读盘复检）
检查项:
  V1 config: A2 副本 configparser 解析, debug == 'false'
  V2 config: 逐键与原件比对——除 debug 外全部一致; 原件 debug == 'true'
  V3 config: 行级 diff 恰好 1 行变化, 且为 debug=true -> debug=false
  V4 csv: 表头与 id/name 列与原件逐行一致
  V5 csv: 全部 joined 匹配 ^\\d{4}-\\d{2}-\\d{2}$ 且 strptime 可解析(格式合法)
  V6 csv: 语义校验——每个新日期与原件原日期是同一日历日(多种原格式解析)
  V7 report: 与 A2 config 双向一致——config 每个 (section,key,value) 均在报告中;
             报告中每个键值对均存在于 config; 且不包含 debug=true
"""
import configparser
import difflib
import os
import re
import sys
from datetime import datetime

EVIDENCE_DIR = os.path.dirname(os.path.abspath(__file__))
A2_DIR = os.path.normpath(os.path.join(EVIDENCE_DIR, ".."))
SRC_DIR = os.path.normpath(os.path.join(A2_DIR, ".."))

results = []

def check(vid, desc, ok, detail=""):
    results.append((vid, ok))
    print(f"[{'PASS' if ok else 'FAIL'}] {vid} {desc}" + (f" | {detail}" if detail else ""))

def read(path):
    with open(path, "r", encoding="utf-8", newline="") as f:
        return f.read()

def parse_cfg_text(text):
    p = configparser.ConfigParser()
    p.read_string(text)
    return {(s, k): v for s in p.sections() for k, v in p.items(s)}

# ---- config ----
orig_cfg = read(os.path.join(SRC_DIR, "config.ini"))
new_cfg = read(os.path.join(A2_DIR, "config.ini"))
o_map, n_map = parse_cfg_text(orig_cfg), parse_cfg_text(new_cfg)

check("V1", "A2 config debug == false", n_map.get(("server", "debug")) == "false",
      f"debug={n_map.get(('server','debug'))}")
check("V2a", "original config debug == true", o_map.get(("server", "debug")) == "true")
diff_keys = {k: (o_map.get(k), n_map.get(k)) for k in set(o_map) | set(n_map)
             if o_map.get(k) != n_map.get(k)}
check("V2b", "only debug key differs", set(diff_keys) == {("server", "debug")}, str(diff_keys))

diff_lines = [l for l in difflib.unified_diff(orig_cfg.splitlines(), new_cfg.splitlines())
              if l.startswith(("+", "-")) and not l.startswith(("+++", "---"))]
ok3 = (len(diff_lines) == 2 and diff_lines[0] == "-debug=true" and diff_lines[1] == "+debug=false")
check("V3", "line diff exactly 1 line: debug=true -> debug=false", ok3, str(diff_lines))

# ---- csv ----
orig_csv = read(os.path.join(SRC_DIR, "users.csv")).splitlines()
new_csv = read(os.path.join(A2_DIR, "users.csv")).splitlines()
o_rows = [l.split(",") for l in orig_csv if l.strip()]
n_rows = [l.split(",") for l in new_csv if l.strip()]

check("V4", "header + id/name columns identical",
      o_rows[0] == n_rows[0]
      and all(o[0] == n[0] and o[1] == n[1] for o, n in zip(o_rows[1:], n_rows[1:]))
      and len(o_rows) == len(n_rows))

date_re = re.compile(r"^\d{4}-\d{2}-\d{2}$")
fmt_ok = all(date_re.match(n[2]) and datetime.strptime(n[2], "%Y-%m-%d") for n in n_rows[1:])
check("V5", "all joined match YYYY-MM-DD regex + strptime-valid", fmt_ok)

ACCEPTED = ["%Y/%m/%d", "%Y-%m-%d", "%Y.%m.%d"]
def parse_any(s):
    for fmt in ACCEPTED:
        try:
            return datetime.strptime(s.strip(), fmt).date()
        except ValueError:
            pass
    raise ValueError(s)

sem_ok = all(parse_any(o[2]) == parse_any(n[2]) for o, n in zip(o_rows[1:], n_rows[1:]))
check("V6", "semantic equality: same calendar date as original", sem_ok)

# ---- report ----
report = read(os.path.join(A2_DIR, "settings-report.txt"))

section = None
report_pairs = set()
for line in report.splitlines():
    line = line.strip()
    m = re.match(r"^\[(.+)\]$", line)
    if m:
        section = m.group(1)
        continue
    m = re.match(r"^([A-Za-z0-9_\-]+)=(.*)$", line)
    if m and section:
        report_pairs.add((section, m.group(1), m.group(2)))

cfg_pairs = {(s, k, v) for (s, k), v in n_map.items()}
check("V7a", "every config (section,key,value) present in report", cfg_pairs <= report_pairs,
      f"missing={cfg_pairs - report_pairs}")
check("V7b", "no phantom pairs in report", report_pairs <= cfg_pairs,
      f"extra={report_pairs - cfg_pairs}")
check("V7c", "report does NOT contain debug=true", "debug=true" not in report)
check("V7d", "report contains debug=false", "debug=false" in report)

# ---- summary ----
failed = [vid for vid, ok in results if not ok]
print(f"\nSUMMARY: {len(results) - len(failed)}/{len(results)} PASS"
      + (f"; FAILED: {failed}" if failed else " -> ALL GREEN"))
sys.exit(1 if failed else 0)
