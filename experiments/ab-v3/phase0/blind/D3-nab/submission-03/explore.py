# -*- coding: utf-8 -*-
"""探索脚本：日内周期形态 + 关键时段原始值（仅打印，不写文件）"""
import csv, statistics
from datetime import datetime, timedelta

DATA = r"<实验根目录>\ab-v3\datasets\nab_machine_temp.csv"
rows = []
with open(DATA, newline="", encoding="utf-8") as f:
    for r in csv.reader(f):
        if not r or r[0].strip().lower() == "timestamp":
            continue
        rows.append((datetime.strptime(r[0].strip(), "%Y-%m-%d %H:%M:%S"), float(r[1])))

# 1) 按一天内 30 分钟槽位的分布（剔除 2-07 后的崩溃期与 12-15~12-17 停机期）
def in_bad(t):
    return (datetime(2013,12,15,17) <= t <= datetime(2013,12,17,18)) or (t >= datetime(2014,2,7,8))
norm = [(t,v) for t,v in rows if not in_bad(t)]
buckets = {}
for t,v in norm:
    k = (t.hour*60 + t.minute)//30
    buckets.setdefault(k, []).append(v)
print("== 日内 30 分钟槽：中位数 / P5 / P95 ==")
for k in sorted(buckets):
    vs = sorted(buckets[k])
    med = statistics.median(vs)
    p5, p95 = vs[int(0.05*len(vs))], vs[min(len(vs)-1,int(0.95*len(vs)))]
    print(f"{k*30//60:02d}:{k*30%60:02d}  med={med:6.2f}  p5={p5:6.2f}  p95={p95:6.2f}  n={len(vs)}")

# 2) 每日中位数
print("== 每日中位数 ==")
daily = {}
for t,v in rows:
    daily.setdefault(t.date(), []).append(v)
for d in sorted(daily):
    print(f"{d}  med={statistics.median(daily[d]):6.2f}  min={min(daily[d]):6.2f}  max={max(daily[d]):6.2f}")

# 3) 关键时段明细
def show(a, b, label, step=3):
    print(f"== {label} ==")
    for t,v in rows:
        if a <= t <= b and (t.minute % (5*step) == 0 or True):
            pass
    sub = [x for x in rows if a <= x[0] <= b]
    for i,(t,v) in enumerate(sub):
        if i % step == 0:
            print(f"{t}  {v:7.3f}")

show(datetime(2013,12,10,5), datetime(2013,12,11,9), "段3 12-10~12-11 波动期", 6)
show(datetime(2013,12,15,17), datetime(2013,12,17,18), "异常1 12-15~12-17 停机/平台", 12)
show(datetime(2014,1,27,13), datetime(2014,1,29,15), "异常2 1-27~1-29", 12)
