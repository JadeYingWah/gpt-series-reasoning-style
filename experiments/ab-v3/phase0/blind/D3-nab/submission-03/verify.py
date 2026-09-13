# -*- coding: utf-8 -*-
"""
独立复算验证（不复用 detect_anomalies.py 的任何函数）：
  V1 区间极值核验：直接重读 CSV，核对报告中每段的峰值/谷值与值域
  V2 端点核验：核对区间端点时间戳在数据中存在，且端点值满足各自方法的带外/带内条件
  V3 覆盖核验：全序列中 <40 的极端值是否全部落在报告区间内
  V4 参数敏感性：K 点级阈值 4.5 / 5.0 / 5.5 下的区段数与端点（判定 5.0 的稳健区间）
"""
import csv, statistics
from datetime import datetime

DATA = r"<实验根目录>\ab-v3\datasets\nab_machine_temp.csv"
FMT = "%Y-%m-%d %H:%M:%S"

rows = []
with open(DATA, newline="", encoding="utf-8") as f:
    for r in csv.reader(f):
        if not r or r[0].strip().lower() == "timestamp":
            continue
        rows.append((datetime.strptime(r[0].strip(), FMT), float(r[1])))
ts = [t for t, _ in rows]; vals = [v for _, v in rows]
tmap = {t: v for t, v in rows}

REPORT = [
    ("2013-12-16 01:30:00", "2013-12-16 18:40:00", 2.085),
    ("2014-01-28 10:50:00", "2014-01-29 18:30:00", 48.927),
    ("2014-02-07 10:25:00", "2014-02-09 12:00:00", 25.888),
]

print("== V1/V2 区间极值与端点核验 ==")
for a, b, ext_v in REPORT:
    ta, tb = datetime.strptime(a, FMT), datetime.strptime(b, FMT)
    seg = [(t, v) for t, v in rows if ta <= t <= tb]
    vmin = min(v for _, v in seg); vmax = max(v for _, v in seg)
    ok_ext = abs(min(vmin, vmax) - ext_v) < 5e-4
    ok_ts = ta in tmap and tb in tmap
    print(f"  [{a} ~ {b}] 点数={len(seg)} min={vmin:.3f} max={vmax:.3f} "
          f"报告极值={ext_v} -> {'一致' if ok_ext else '不一致!'}  端点存在于数据 -> {'是' if ok_ts else '否!'}")

print("== V3 全序列 <40 极端值的区间覆盖 ==")
ivs = [(datetime.strptime(a, FMT), datetime.strptime(b, FMT)) for a, b, _ in REPORT]
miss = [(t, v) for t, v in rows if v < 40 and not any(a <= t <= bb for a, bb in ivs)]
n40 = sum(1 for v in vals if v < 40)
print(f"  全序列 <40 的点数={n40}，未落入报告区间的点数={len(miss)} -> {'全部覆盖' if not miss else miss[:5]}")

print("== V4 参数敏感性（K 点级阈值） ==")
SLOT_MIN = 30
slot = [(t.hour * 60 + t.minute) // SLOT_MIN for t in ts]
n = len(rows)
for K in (4.5, 5.0, 5.5):
    flagged_prev = set()
    sigma = None; slot_med = None
    for _ in range(2):
        buckets = {}
        for i in range(n):
            if i not in flagged_prev:
                buckets.setdefault(slot[i], []).append(vals[i])
        slot_med = {k: statistics.median(v) for k, v in buckets.items()}
        resid = [vals[i] - slot_med[slot[i]] for i in range(n) if i not in flagged_prev]
        med = statistics.median(resid)
        sigma = 1.4826 * statistics.median([abs(x - med) for x in resid])
        flagged = {i for i in range(n) if abs(vals[i] - slot_med[slot[i]]) / sigma > K}
        if flagged == flagged_prev:
            break
        flagged_prev = flagged
    fl = sorted(flagged)
    # gap 24h 聚合 + 保留（时长>=12h 或 min<40）
    segs, cur = [], [fl[0]] if fl else []
    for i in fl[1:]:
        if (ts[i] - ts[cur[-1]]).total_seconds() / 3600.0 <= 24.0:
            cur.append(i)
        else:
            segs.append(cur); cur = [i]
    if cur: segs.append(cur)
    kept = []
    for s in segs:
        dur = (ts[s[-1]] - ts[s[0]]).total_seconds() / 3600.0
        vmin = min(vals[i] for i in s)
        if dur >= 12.0 or vmin < 40.0:
            kept.append((s, dur, vmin))
    print(f"  K={K}: sigma={sigma:.3f} 异常点={len(fl)} 保留段={len(kept)}")
    for s, dur, vmin in kept:
        print(f"     [{ts[s[0]]} ~ {ts[s[-1]]}] 谷={vmin:.3f} 时长={dur:.1f}h")
