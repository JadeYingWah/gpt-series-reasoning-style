# -*- coding: utf-8 -*-
"""ab-cycle2 24 臂产物盘点：输出每臂文件数/总字节/顶层文件清单。
Chrome profile 等临时目录单独聚合计数，不逐个展开。"""
import os, sys, io, json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = r"<实验根目录>\ab-cycle2"
BEDS = sorted(d for d in os.listdir(ROOT) if os.path.isdir(os.path.join(ROOT, d)) and not d.startswith(("_", "skill")))

# 临时物目录名特征（运行临时物，聚合计数）
TMP_HINTS = ("chrome-profile", "_chrome", "profile-", "_cdp", "_probe", "__pycache__", ".tmp")

SKIP_TOP = {"task.md", "spawn-A.md", "spawn-B.md"}  # 输入文件，非产物

def scan(arm_dir):
    n_files, n_bytes, tmp_files, tmp_bytes = 0, 0, 0, 0
    top = []  # (name, size, mtime_str)
    for dirpath, dirnames, filenames in os.walk(arm_dir):
        for f in filenames:
            p = os.path.join(dirpath, f)
            rel = os.path.relpath(p, arm_dir)
            try:
                sz = os.path.getsize(p)
            except OSError:
                sz = -1
            n_files += 1
            n_bytes += max(sz, 0)
            low = rel.lower()
            if any(h in low for h in TMP_HINTS):
                tmp_files += 1
                tmp_bytes += max(sz, 0)
            depth = rel.count(os.sep)
            if depth == 0 and f not in SKIP_TOP:
                import datetime
                mt = datetime.datetime.fromtimestamp(os.path.getmtime(p)).strftime("%m-%d %H:%M")
                top.append((f, sz, mt))
    return n_files, n_bytes, tmp_files, tmp_bytes, sorted(top)

rows = []
for bed in BEDS:
    for arm in ("A-skill", "B-noskill"):
        ad = os.path.join(ROOT, bed, arm)
        if not os.path.isdir(ad):
            rows.append(f"### {bed} / {arm}  <MISSING DIR>")
            continue
        nf, nb, tf, tb, top = scan(ad)
        human = f"{nb/1024/1024:.1f}MB" if nb > 1024*1024 else f"{nb/1024:.1f}KB"
        thuman = f"{tb/1024/1024:.1f}MB" if tb > 1024*1024 else f"{tb/1024:.1f}KB"
        rows.append(f"### {bed} / {arm}  文件={nf} 总量={human} (临时物 {tf} 个 {thuman})")
        for f, sz, mt in top:
            s = f"{sz/1024/1024:.1f}MB" if sz > 1024*1024 else f"{sz/1024:.1f}KB"
            rows.append(f"    {f:<44} {s:>10}  {mt}")
        rows.append("")

print("\n".join(rows))
