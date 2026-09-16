# -*- coding: utf-8 -*-
"""A2 轻量配置臂 · 应用修改（可复现脚本）
只读输入: M6-lightgate/config.ini, M6-lightgate/users.csv
写入输出: A2/config.ini, A2/users.csv, A2/settings-report.txt
"""
import configparser
import difflib
import os
from datetime import datetime

EVIDENCE_DIR = os.path.dirname(os.path.abspath(__file__))
A2_DIR = os.path.normpath(os.path.join(EVIDENCE_DIR, ".."))
SRC_DIR = os.path.normpath(os.path.join(A2_DIR, ".."))

SRC_CFG = os.path.join(SRC_DIR, "config.ini")
SRC_CSV = os.path.join(SRC_DIR, "users.csv")
NEW_CFG = os.path.join(A2_DIR, "config.ini")
NEW_CSV = os.path.join(A2_DIR, "users.csv")
NEW_RPT = os.path.join(A2_DIR, "settings-report.txt")

# ---------- 1. config.ini: debug=true -> false ----------
with open(SRC_CFG, "r", encoding="utf-8", newline="") as f:
    cfg_text = f.read()

assert cfg_text.count("debug=true") == 1, "expected exactly one 'debug=true'"
new_cfg_text = cfg_text.replace("debug=true", "debug=false")
with open(NEW_CFG, "w", encoding="utf-8", newline="") as f:
    f.write(new_cfg_text)

print("== diff config.ini (original -> A2) ==")
for line in difflib.unified_diff(
    cfg_text.splitlines(keepends=True),
    new_cfg_text.splitlines(keepends=True),
    fromfile="config.ini (orig)", tofile="config.ini (A2)",
):
    print(line.rstrip("\n"))

# ---------- 2. users.csv: unify dates to YYYY-MM-DD ----------
ACCEPTED_FORMATS = ["%Y/%m/%d", "%Y-%m-%d", "%Y.%m.%d"]

def parse_date(s):
    last_err = None
    for fmt in ACCEPTED_FORMATS:
        try:
            return datetime.strptime(s.strip(), fmt).date()
        except ValueError as e:
            last_err = e
    raise ValueError(f"unparseable date {s!r}: {last_err}")

with open(SRC_CSV, "r", encoding="utf-8", newline="") as f:
    csv_lines = f.read().splitlines(keepends=True)

out_lines = []
for i, line in enumerate(csv_lines):
    if i == 0:
        out_lines.append(line)  # header untouched
        continue
    if line.strip() == "":
        out_lines.append(line)
        continue
    parts = line.rstrip("\r\n").split(",")
    assert len(parts) == 3, f"row {i+1}: expected 3 columns, got {parts}"
    d = parse_date(parts[2])
    parts[2] = d.strftime("%Y-%m-%d")
    out_lines.append(",".join(parts) + "\n")

new_csv_text = "".join(out_lines)
with open(NEW_CSV, "w", encoding="utf-8", newline="") as f:
    f.write(new_csv_text)

print("== diff users.csv (original -> A2) ==")
for line in difflib.unified_diff(
    csv_lines,
    new_csv_text.splitlines(keepends=True),
    fromfile="users.csv (orig)", tofile="users.csv (A2)",
):
    print(line.rstrip("\n"))

# ---------- 3. settings-report.txt from the NEW config ----------
parser = configparser.ConfigParser()
with open(NEW_CFG, "r", encoding="utf-8") as f:
    parser.read_file(f)

report_lines = [
    "Settings Report",
    f"Source: config.ini (A2 copy)",
    f"Generated: {datetime.now().strftime('%Y-%m-%d')}",
    "",
]
n_items = 0
for section in parser.sections():
    report_lines.append(f"[{section}]")
    for key, value in parser.items(section):
        report_lines.append(f"{key}={value}")
        n_items += 1
    report_lines.append("")
report_lines.append(f"Total: {len(parser.sections())} sections, {n_items} items")
report_text = "\n".join(report_lines) + "\n"
with open(NEW_RPT, "w", encoding="utf-8", newline="") as f:
    f.write(report_text)

print("== settings-report.txt content ==")
print(report_text)
print("APPLY DONE")
