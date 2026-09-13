# -*- coding: utf-8 -*-
"""anonymize.py — Phase 0 匿名化：9 臂产物 → blind/<task>/submission-XX
- 随机映射（seed 固定可复现），映射只存 blind_mapping.json（不进 blind 目录）
- 剔除 PROMPT.md（含臂身份）；文本文件清洗臂标识 token
- 清洗后逐文件校验无残留
"""
import json
import os
import random
import re
import shutil

PHASE0 = "<实验根目录>/ab-v3/phase0"
BLIND = os.path.join(PHASE0, "blind")
TASKS = ["D1-winequality", "D2-cafe", "D3-nab"]
ARMS = ["Bprime", "A2", "A1"]

random.seed(20260913)
mapping = {}
for t in TASKS:
    order = ARMS[:]
    random.shuffle(order)
    for i, arm in enumerate(order, 1):
        mapping[f"{t}/{arm}"] = f"submission-{i:02d}"

TEXT_EXT = {".md", ".py", ".json", ".csv", ".txt", ".svg"}
# 清洗模式：完整臂 token、括号臂说明、独立臂词、"A 臂/B′ 臂"等
PATTERNS = [
    (re.compile(r"p0-D\d-(A1|A2|Bprime)[·,，、\s]*"), ""),
    (re.compile(r"p0-D\d-(A1|A2|Bprime)"), ""),
    (re.compile(r"[（(]\s*A\s*臂[^）)]*[）)]"), ""),
    (re.compile(r"[（(]\s*B[′′']?\s*臂[^）)]*[）)]"), ""),
    (re.compile(r"[（(]\s*Bprime[^）)]*[）)]"), ""),
    (re.compile(r"A\s*臂[·\s]*"), ""),
    (re.compile(r"B[′′']?\s*臂[·\s]*"), ""),
    (re.compile(r"Bprime\s*臂[·\s]*"), ""),
    (re.compile(r"skill\s*版本[:：]\s*gpt-series-reasoning-style\s*v?[\d.]+[^\n]*"), "skill 版本：（匿名化省略）"),
    (re.compile(r"执行者[:：]\s*[^\n·]*[·\n]"), ""),
]


def scrub(text):
    for pat, rep in PATTERNS:
        text = pat.sub(rep, text)
    return text


RESIDUAL = re.compile(r"p0-D\d-|Bprime|B′?\s*臂|A\s*臂|v1\.2\.1")

report = {}
for t in TASKS:
    tdir = os.path.join(BLIND, t)
    if os.path.isdir(tdir):
        shutil.rmtree(tdir)
    os.makedirs(tdir)
    for arm in ARMS:
        src = os.path.join(PHASE0, t, arm)
        sub = mapping[f"{t}/{arm}"]
        dst = os.path.join(tdir, sub)
        os.makedirs(dst)
        residuals = []
        for fn in os.listdir(src):
            if fn == "PROMPT.md":
                continue
            s, d = os.path.join(src, fn), os.path.join(dst, fn)
            ext = os.path.splitext(fn)[1].lower()
            if ext in TEXT_EXT:
                with open(s, encoding="utf-8", errors="replace") as fh:
                    text = fh.read()
                text = scrub(text)
                m = RESIDUAL.findall(text)
                if m:
                    residuals.append(f"{fn}: {sorted(set(m))}")
                with open(d, "w", encoding="utf-8", newline="") as fh:
                    fh.write(text)
            else:
                shutil.copyfile(s, d)
        report[f"{t}/{arm} -> {sub}"] = {"files": sorted(os.listdir(dst)), "residual_flags": residuals}

with open(os.path.join(PHASE0, "blind_mapping.json"), "w", encoding="utf-8") as fh:
    json.dump(mapping, fh, ensure_ascii=False, indent=2)
with open(os.path.join(PHASE0, "anonymize_report.json"), "w", encoding="utf-8") as fh:
    json.dump(report, fh, ensure_ascii=False, indent=2)

print("映射（保密，勿随 blind 目录分发）:")
for k, v in mapping.items():
    print(f"  {k:28s} -> {v}")
print("\n清洗校验:")
for k, r in report.items():
    flag = "OK" if not r["residual_flags"] else f"残留: {r['residual_flags']}"
    print(f"  {k:28s} files={len(r['files'])}  {flag}")
