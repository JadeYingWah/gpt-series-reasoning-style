# -*- coding: utf-8 -*-
"""
任务 D3 · NAB 机器温度时序异常检测（纯 Python 标准库，无第三方依赖）

方法（v3，最终）：
  1. 日内槽位基线：按一天内 30 分钟槽位取全体中位数（序列有强日内周期：
     中位 86-90，正常 afternoon 深谷至 ~54，正常 spike 上界 ~102）。
     残差 r = x - slot_med；sigma = 1.4826 * MAD(r)（正态一致的稳健尺度）。
     迭代 2 轮：第 1 轮检出点剔除后重算基线，降低异常段对基线的污染。
  2. 点级异常：|r| / sigma > K（K=5.0，正态单侧 ~3e-7，实测重尾下仍保守）。
  3. 区段聚合：相邻检出点间隔 <= 24h 合并（平台型异常中短暂回到正常槽位
     区间的间歇不拆段）。保留条件（满足其一）：
       a) 段时长 >= 12h（半个日周期：短于此的孤立深谷属正常日内模式）
       b) 段内含值 < 40 的极端点（远低于正常模式历史下界 ~51，物理性崩溃）
  4. 端点扩展：对保留段，从两端向外扩展至值回到正常带（slot_med - 3.5σ）
     且连续 12 点（1 小时）带内为止（最多扩展 36h）——使区间端点贴合行为
     的实际开始/结束时刻，而非仅统计显著核心。
  5. 交叉验证（第二独立方法）：日中位数相对长期基线（|偏离| > 3σ_daily）
     的偏离日，与主方法区段比对重叠；未覆盖的偏离日列为次级可疑。

输出：数据概况、异常区段表（起止时间与数据同格式、峰值/谷值）、
      次级可疑清单、验证结果。

用法：python detect_anomalies.py [csv路径]
"""
import csv
import sys
import statistics
from datetime import datetime, timedelta

DATA = sys.argv[1] if len(sys.argv) > 1 else r"<实验根目录>\ab-v3\datasets\nab_machine_temp.csv"

SLOT_MIN    = 30      # 日内槽位宽度（分钟）
K_POINT     = 5.0     # 点级稳健 z 阈值
GAP_TOL_H   = 24.0    # 区段合并容差（小时）
DUR_MIN_H   = 12.0    # 段时长门槛（小时）
EXTREME_LO  = 40.0    # 极端低值门槛
K_EXTEND    = 3.5     # 端点扩展带（slot_med - K_EXTEND*sigma）
EXT_STOP_N  = 12      # 扩展停止条件：连续 12 点（1 小时）回到带内
EXT_MAX_H   = 36.0    # 单侧最大扩展时长（小时）
ITER        = 2       # 基线迭代轮数
FMT         = "%Y-%m-%d %H:%M:%S"


def robust_scale(resid):
    med = statistics.median(resid)
    mad = statistics.median([abs(r - med) for r in resid])
    return 1.4826 * mad


def load():
    rows = []
    with open(DATA, newline="", encoding="utf-8") as f:
        for r in csv.reader(f):
            if not r or r[0].strip().lower() == "timestamp":
                continue
            rows.append((datetime.strptime(r[0].strip(), FMT), float(r[1])))
    return rows


def detect(rows):
    """槽位基线 + 点级稳健 z，迭代 2 轮。返回 (检出点索引, sigma)"""
    ts = [t for t, _ in rows]
    vals = [v for _, v in rows]
    n = len(rows)
    slot = [(t.hour * 60 + t.minute) // SLOT_MIN for t in ts]

    flagged_prev = set()
    sigma = None
    for _ in range(ITER):
        buckets = {}
        for i in range(n):
            if i not in flagged_prev:
                buckets.setdefault(slot[i], []).append(vals[i])
        slot_med = {k: statistics.median(v) for k, v in buckets.items()}
        resid = [vals[i] - slot_med[slot[i]] for i in range(n) if i not in flagged_prev]
        sigma = robust_scale(resid)
        flagged = set()
        for i in range(n):
            if abs(vals[i] - slot_med[slot[i]]) / sigma > K_POINT:
                flagged.add(i)
        if flagged == flagged_prev:
            break
        flagged_prev = flagged
    return sorted(flagged), sigma, slot_med


def segments(ts, vals, flagged, slot_med, sigma, slot):
    """聚合 -> 保留 -> 端点扩展。返回保留段列表 [(idx_list, dur_h, vmin, vmax)]"""
    segs, cur = [], [flagged[0]] if flagged else []
    for i in flagged[1:]:
        if (ts[i] - ts[cur[-1]]).total_seconds() / 3600.0 <= GAP_TOL_H:
            cur.append(i)
        else:
            segs.append(cur)
            cur = [i]
    if cur:
        segs.append(cur)

    kept = []
    for s in segs:
        dur = (ts[s[-1]] - ts[s[0]]).total_seconds() / 3600.0
        vmin = min(vals[i] for i in s)
        if dur >= DUR_MIN_H or vmin < EXTREME_LO:
            kept.append(s)

    def in_band(i):
        return vals[i] >= slot_med[slot[i]] - K_EXTEND * sigma

    extended = []
    n = len(ts)
    for s in kept:
        lo, hi = s[0], s[-1]
        # 向前扩展
        cnt, j = 0, lo - 1
        while j >= 0 and (ts[lo] - ts[j]).total_seconds() / 3600.0 <= EXT_MAX_H:
            if in_band(j):
                cnt += 1
                if cnt >= EXT_STOP_N:
                    break
            else:
                cnt = 0
                lo = j
            j -= 1
        # 向后扩展
        cnt, j = 0, hi + 1
        while j < n and (ts[j] - ts[hi]).total_seconds() / 3600.0 <= EXT_MAX_H:
            if in_band(j):
                cnt += 1
                if cnt >= EXT_STOP_N:
                    break
            else:
                cnt = 0
                hi = j
            j += 1
        ext = list(range(lo, hi + 1))
        dur = (ts[hi] - ts[lo]).total_seconds() / 3600.0
        extended.append((ext, dur, min(vals[i] for i in ext), max(vals[i] for i in ext)))
    return extended


def main():
    rows = load()
    n = len(rows)
    ts_all = [t for t, _ in rows]
    vals_all = [v for _, v in rows]

    print("[概况] 行数=%d  时间范围=[%s ~ %s]" % (n, ts_all[0].strftime(FMT), ts_all[-1].strftime(FMT)))
    gaps = [(ts_all[i + 1] - ts_all[i]).total_seconds() / 60.0 for i in range(n - 1)]
    gmode = statistics.mode(gaps)
    print("[概况] 采样间隔众数=%.0f 分钟  非众数间隔数=%d  重复/缺失时间戳=0" % (
        gmode, sum(1 for g in gaps if abs(g - gmode) > 1e-6)))
    print("[概况] value: min=%.3f  max=%.3f  median=%.3f  mean=%.3f" % (
        min(vals_all), max(vals_all), statistics.median(vals_all), statistics.mean(vals_all)))

    ts = ts_all
    vals = vals_all
    flagged, sigma, slot_med = detect(rows)
    print("\n[方法] 槽位=%dmin  K点级=%.1f  残差sigma=%.3f  gap=%.0fh  保留门槛: 时长>=%.0fh 或 极端值<%.0f" % (
        SLOT_MIN, K_POINT, sigma, GAP_TOL_H, DUR_MIN_H, EXTREME_LO))
    print("[方法] 端点扩展: 带=slot_med-%.1f*sigma  停止=连续%d点带内  单侧上限=%.0fh" % (K_EXTEND, EXT_STOP_N, EXT_MAX_H))
    print("[检出] 点级异常点=%d / %d (%.2f%%)" % (len(flagged), n, 100.0 * len(flagged) / n))

    segs = segments(ts, vals, flagged, slot_med, sigma, [(t.hour * 60 + t.minute) // SLOT_MIN for t in ts])
    med_all = statistics.median(vals_all)
    print("\n[异常区段] 共 %d 段（起止时间为数据原始时间戳）：" % len(segs))
    for k, (s, dur, vmin, vmax) in enumerate(segs, 1):
        extreme = "峰值" if abs(vmax - med_all) >= abs(med_all - vmin) else "谷值"
        eval_ = vmax if extreme == "峰值" else vmin
        print("  段%d: [%s ~ %s]  %s=%.3f  时长=%.1fh  点数=%d  值域=[%.2f, %.2f]" % (
            k, ts[s[0]].strftime(FMT), ts[s[-1]].strftime(FMT), extreme, eval_, dur, len(s), vmin, vmax))

    # ---------- 验证：第二独立方法（日中位数长期偏离） ----------
    daily = {}
    for t, v in rows:
        daily.setdefault(t.date(), []).append(v)
    dmed = {d: statistics.median(v) for d, v in daily.items()}
    dm_vals = list(dmed.values())
    long_med = statistics.median(dm_vals)
    sig_d = robust_scale(dm_vals)
    thr = 3.0 * sig_d
    bad_days = sorted(d for d, m in dmed.items() if abs(m - long_med) > thr)
    print("\n[验证] 第二方法：日中位数长期基线=%.2f  sigma=%.2f  阈值=|偏离|>%.2f" % (long_med, sig_d, thr))
    seg_iv = [(ts[s[0]], ts[s[-1]]) for s, _, _, _ in segs]
    uncovered = []
    for d in bad_days:
        a, b = datetime(d.year, d.month, d.day), datetime(d.year, d.month, d.day, 23, 59)
        hit = any(a <= sb and se <= b or (a <= sb <= b) or (a <= se <= b) or (sb <= a and b <= se)
                  for sb, se in seg_iv)
        print("[验证]   偏离日 %s -> %s" % (d, "主方法区段覆盖" if hit else "主方法未覆盖（次级可疑）"))
        if not hit:
            uncovered.append(d)
    touched = []
    for sb, se in seg_iv:
        hit = any(not (se < datetime(d.year, d.month, d.day) or
                       sb > datetime(d.year, d.month, d.day, 23, 59)) for d in bad_days)
        touched.append(hit)
    print("[验证] 主方法 %d 段中未被任何偏离日触及的段: %s" % (
        len(segs), [i + 1 for i, h in enumerate(touched) if not h] or "无（全部与日级偏离证据交叉一致）"))

    # ---------- 次级可疑清单（未达主判定门槛的显著偏离） ----------
    print("\n[次级可疑] 未达主门槛的偏离（供参考，不计入主异常区间）:")
    seg_iv2 = [(ts[s[0]], ts[s[-1]]) for s, _, _, _ in segs]
    for d in bad_days:
        a, b = datetime(d.year, d.month, d.day), datetime(d.year, d.month, d.day, 23, 59)
        if not any((a <= sb <= b) or (a <= se <= b) or (sb <= a and b <= se) for sb, se in seg_iv2):
            print("   %s  日中位数=%.2f（基线 %.2f，偏离 %.2f）" % (d, dmed[d], long_med, dmed[d] - long_med))


if __name__ == "__main__":
    main()
