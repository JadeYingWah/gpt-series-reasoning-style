# -*- coding: utf-8 -*-
"""诊断：打印关键时段的检出点明细（时间/值/槽位中位/z）"""
import csv, statistics
from datetime import datetime

DATA = r"<实验根目录>\ab-v3\datasets\nab_machine_temp.csv"
SLOT_MIN, K = 30, 5.0
FMT = "%Y-%m-%d %H:%M:%S"

rows = []
with open(DATA, newline="", encoding="utf-8") as f:
    for r in csv.reader(f):
        if not r or r[0].strip().lower() == "timestamp":
            continue
        rows.append((datetime.strptime(r[0].strip(), FMT), float(r[1])))
ts = [t for t, _ in rows]; vals = [v for _, v in rows]; n = len(rows)
slot = [(t.hour * 60 + t.minute) // SLOT_MIN for t in ts]

flagged_prev = set()
for it in range(2):
    buckets = {}
    for i in range(n):
        if i not in flagged_prev:
            buckets.setdefault(slot[i], []).append(vals[i])
    slot_med = {k: statistics.median(v) for k, v in buckets.items()}
    resid = [vals[i] - slot_med[slot[i]] for i in range(n) if i not in flagged_prev]
    med_r = statistics.median(resid)
    sig = 1.4826 * statistics.median([abs(r - med_r) for r in resid])
    flagged = set()
    for i in range(n):
        if abs(vals[i] - slot_med[slot[i]]) / sig > K:
            flagged.add(i)
    print(f"iter{it+1}: sigma={sig:.3f}  flagged={len(flagged)}")
    flagged_prev = flagged
flagged = sorted(flagged)

def dump(a, b, label):
    print(f"== {label} ==")
    for i in flagged:
        if a <= ts[i] <= b:
            z = (vals[i] - slot_med[slot[i]]) / sig
            print(f"  {ts[i]}  v={vals[i]:8.3f}  slot_med={slot_med[slot[i]]:6.2f}  z={z:7.2f}")

dump(datetime(2013,12,15,17), datetime(2013,12,17,0), "12-15 17:00 ~ 12-17 00:00")
dump(datetime(2014,1,27,0), datetime(2014,1,31,0), "1-27 ~ 1-30")
dump(datetime(2014,2,7,0), datetime(2014,2,10,0), "2-07 ~ 2-09")
dump(datetime(2013,12,10,0), datetime(2013,12,11,0), "12-10")
# 每段原始值范围
print("== 12-16 00:00~07:00 原始值 ==")
for t, v in rows:
    if datetime(2013,12,16,0) <= t <= datetime(2013,12,16,7,5) and t.minute % 15 == 0:
        print(f"  {t}  {v:8.3f}")
print("== 1-28 13:00~18:00 原始值 ==")
for t, v in rows:
    if datetime(2014,1,28,13) <= t <= datetime(2014,1,28,18) and t.minute % 5 == 0:
        print(f"  {t}  {v:8.3f}")
