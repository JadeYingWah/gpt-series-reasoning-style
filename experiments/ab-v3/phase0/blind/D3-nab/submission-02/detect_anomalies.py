# -*- coding: utf-8 -*-
"""
D3 时序异常检测：NAB machine_temperature_system_failure
=====================================================
输入：<实验根目录>\\ab-v3\\datasets\\nab_machine_temp.csv（22695 行，5min 采样）
输出：anomaly_intervals.json + anomaly_overview.svg + 控制台报告

方法（三流，仅低位侧做 regime 检测，理由见 report.md）：
  A 点级：滚动中位数(10h) 基线 + 滚动 MAD 尺度，稳健 z>6。
          反 masking：sigma 截断到 [0.5*sigma_typ, sigma_typ]，
          防止持续异常段撑大自身局部尺度（首版教训：v_min=2.08 被吞）。
  B1 日级低位 regime：日中位数 vs 25 日中心窗中位数，
          dev<-8°C 且稳健 z>2.0（低位侧；高位平台在多时段复现、
          属运行包络，不作为 regime 异常）。
  B2 日级深谷 regime：日 P10 分位 vs 25 日中心窗中位数，
          捕获"半日低位平台"（如 2014-02-03，日中位数被稀释漏检）。
  区间装配：日级区间做水位修剪（1h 前向/后向中位数跨越 base-6°C），
          渐进型起始向后回溯扩展（跨午夜）；与 A 流区间按 6h 邻近合并。
运行：C:/Python314/python.exe detect_anomalies.py
依赖：仅 numpy
"""
import csv
import json
import os
from collections import OrderedDict

import numpy as np

DATA_PATH = r"<实验根目录>\ab-v3\datasets\nab_machine_temp.csv"
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ---- 参数 ----
W_MAIN = 121          # A 流基线窗 ≈ 10h
T_Z = 6.0             # A 流 z 阈值
SIGMA_FLOOR = 0.5     # sigma 下限系数
MIN_LEN = 2           # A 流区间最少点数
STRONG_SINGLE = 9.0   # 单点保留条件 z > 9
GAP_MERGE = 7         # A 流合并容忍（点 = 35min）
W_REGIME = 25         # B 流比较窗（日）
T_DAY_Z = 2.0         # B 流 z 阈值
T_DAY_ABS_MED = 8.0   # B1 绝对偏差下限 °C
T_DAY_ABS_P10 = 8.0   # B2 绝对偏差下限 °C
DAY_GAP_MERGE = 2     # regime 日合并容忍（日）
TRIM_ABS = 6.0        # 水位修剪阈值（base - 6°C）
TRIM_WIN = 12         # 修剪用 1h 中位数窗（点）
BOUND_GAP = 72        # A/B 区间合并距离上限（点 = 6h）
BACK_MAX = 3 * 288    # 起始回溯上限（3 日）


def load():
    ts, vals = [], []
    with open(DATA_PATH, newline="") as f:
        r = csv.reader(f)
        next(r)
        for row in r:
            ts.append(row[0])
            vals.append(float(row[1]))
    return ts, np.asarray(vals, dtype=float)


def quality_check(ts, v):
    n = len(v)
    gaps = []
    for i in range(n - 1):
        d = (np.datetime64(ts[i + 1]) - np.datetime64(ts[i])).astype(int) // 60
        if d != 5:
            gaps.append((ts[i], ts[i + 1], int(d)))
    return {
        "rows": n,
        "nan_or_inf": int((~np.isfinite(v)).sum()),
        "t_min": ts[0], "t_max": ts[-1],
        "non_5min_intervals": gaps,
        "duplicate_timestamps": len(ts) - len(set(ts)),
        "v_min": round(float(v.min()), 3), "v_max": round(float(v.max()), 3),
        "v_mean": round(float(v.mean()), 3),
        "v_median": round(float(np.median(v)), 3),
    }


def roll_centered(x, w, fn):
    half = w // 2
    out = np.full(len(x), np.nan)
    if len(x) < w:
        out[:] = fn(x[None, :])[0]
        return out
    res = fn(np.lib.stride_tricks.sliding_window_view(x, w))
    out[half:half + len(res)] = res
    out[:half] = out[half]
    out[half + len(res):] = out[half + len(res) - 1]
    return out


def fwd_med(x, w):
    """fwd_med[i] = median(x[i:i+w])，尾部用最后可用值。"""
    res = np.median(np.lib.stride_tricks.sliding_window_view(x, w), axis=1)
    out = np.full(len(x), res[-1])
    out[:len(res)] = res
    return out


def bwd_med(x, w):
    """bwd_med[i] = median(x[i-w+1:i+1])，头部用最早可用值。"""
    res = np.median(np.lib.stride_tricks.sliding_window_view(x, w), axis=1)
    out = np.full(len(x), res[0])
    out[w - 1:] = res
    return out


def merge_idx_regions(idx, gap):
    if len(idx) == 0:
        return []
    groups, start, prev = [], idx[0], idx[0]
    for i in idx[1:]:
        if i - prev > gap:
            groups.append((start, prev)); start = i
        prev = i
    groups.append((start, prev))
    return groups


def main():
    ts, v = load()
    n = len(v)
    q = quality_check(ts, v)
    print("== 数据体检 ==")
    print(json.dumps(q, ensure_ascii=False, indent=1))

    # ---------- A 流 ----------
    med = roll_centered(v, W_MAIN, lambda w: np.median(w, axis=1))
    mad = roll_centered(
        v, W_MAIN,
        lambda w: np.median(np.abs(w - np.median(w, axis=1)[:, None]), axis=1))
    sigma_local = 1.4826 * mad + 1e-6
    sigma_typ = float(np.median(sigma_local))
    sigma = np.clip(sigma_local, SIGMA_FLOOR * sigma_typ, sigma_typ)
    z = np.abs(v - med) / sigma

    print("\n== A 流定标 ==")
    print(f"sigma_typ={sigma_typ:.3f}")
    print("z 敏感性（旗标点数）:",
          {t: int((z > t).sum()) for t in (3.5, 5, 6, 8, 10)})

    a_regions = []
    for a, b in merge_idx_regions(np.where(z > T_Z)[0], GAP_MERGE):
        if (b - a + 1 >= MIN_LEN) or (z[a:b + 1].max() > STRONG_SINGLE):
            a_regions.append([a, b])
    print("\n== A 流区间（z>%.1f）==" % T_Z)
    for a, b in a_regions:
        seg = v[a:b + 1]
        print(f"  [{ts[a]} .. {ts[b]}] n={b-a+1} peak={seg.max():.2f} "
              f"valley={seg.min():.2f} zmax={z[a:b+1].max():.1f}")

    # ---------- B 流 ----------
    days = [t[:10] for t in ts]
    day_list = list(OrderedDict.fromkeys(days))
    nd = len(day_list)
    day_arr = np.array(days)
    day_med = np.array([np.median(v[day_arr == d]) for d in day_list])
    day_p10 = np.array([np.percentile(v[day_arr == d], 10) for d in day_list])

    def day_base(x):
        base = np.full(nd, np.nan)
        for i in range(nd):
            lo, hi = max(0, i - W_REGIME // 2), min(nd, i + W_REGIME // 2 + 1)
            base[i] = np.median(x[lo:hi])
        return base

    dev_med = day_med - day_base(day_med)
    dev_p10 = day_p10 - day_base(day_p10)
    s_med = 1.4826 * float(np.median(np.abs(dev_med - np.median(dev_med)))) + 1e-6
    s_p10 = 1.4826 * float(np.median(np.abs(dev_p10 - np.median(dev_p10)))) + 1e-6
    flag_med = (dev_med < -T_DAY_ABS_MED) & \
               ((np.median(dev_med) - dev_med) / s_med > T_DAY_Z)
    flag_p10 = (dev_p10 < -T_DAY_ABS_P10) & \
               ((np.median(dev_p10) - dev_p10) / s_p10 > T_DAY_Z)
    day_flag = flag_med | flag_p10   # 仅低位侧

    print("\n== B 流定标 ==")
    print(f"s_med={s_med:.2f}°C s_p10={s_p10:.2f}°C")
    print("B1 日中位数低位旗标:",
          [(day_list[i], round(dev_med[i], 1)) for i in np.where(flag_med)[0]])
    print("B2 日P10低位旗标:",
          [(day_list[i], round(dev_p10[i], 1)) for i in np.where(flag_p10)[0]])

    day_bounds = {}
    for d in day_list:
        w_ = np.where(day_arr == d)[0]
        day_bounds[d] = (int(w_[0]), int(w_[-1]))

    bm = bwd_med(v, TRIM_WIN)   # 全序列 1h 后向中位数
    fm = fwd_med(v, TRIM_WIN)   # 全序列 1h 前向中位数

    # ---------- B 区间装配 + 水位修剪 ----------
    b_regions = []
    for a, b in merge_idx_regions(np.where(day_flag)[0], DAY_GAP_MERGE):
        d1, d2 = day_list[a], day_list[b]
        s0, e0 = day_bounds[d1][0], day_bounds[d2][1]
        base = float(np.median(v[max(0, s0 - 288):s0]))
        thr = base - TRIM_ABS
        # 起始：若日界处已在低位 → 向后回溯（渐进起始）；否则前向修剪
        if bm[s0] < thr:
            st = s0
            while st > 0 and st > s0 - BACK_MAX and bm[st - 1] < thr:
                st -= 1
        else:
            cand = np.where(fm[s0:e0 + 1] < thr)[0]
            st = s0 + int(cand[0]) if len(cand) else s0
        # 结束：旗标末日内最后一个 1h 后向中位数 < thr 的点
        #（限制在旗标日内：恢复后的正常波动/孤立下探不再拖长区间）
        cand = np.where(bm[s0:e0 + 1] < thr)[0]
        en = s0 + int(cand[-1]) if len(cand) else e0
        b_regions.append([st, en])
        print(f"B 区间日界 [{d1}..{d2}] base={base:.1f} thr={thr:.1f} "
              f"修剪后 [{ts[st]} .. {ts[en]}]")

    # ---------- 合并 ----------
    regions = [[a, b] for a, b in a_regions] + \
              [[a, b] for a, b in b_regions]
    regions.sort(key=lambda r: r[0])
    merged = []
    for a, b in regions:
        if merged and a - merged[-1][1] <= BOUND_GAP:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])

    print("\n== 最终异常区间 ==")
    out = []
    for a, b in merged:
        seg = v[a:b + 1]
        rec = OrderedDict(
            start=ts[a], end=ts[b], points=int(b - a + 1),
            peak=round(float(seg.max()), 2),
            peak_time=ts[a + int(seg.argmax())],
            valley=round(float(seg.min()), 2),
            valley_time=ts[a + int(seg.argmin())],
        )
        out.append(rec)
        print(json.dumps(rec, ensure_ascii=False))

    with open(os.path.join(OUT_DIR, "anomaly_intervals.json"), "w",
              encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    # ---------- SVG 总览图 ----------
    try:
        draw_svg(ts, v, merged, q)
        print("\n已写出 anomaly_overview.svg")
    except Exception as e:  # noqa
        print("SVG 绘制失败（不影响检测）:", e)


def draw_svg(ts, v, regions, q):
    W, H = 1660, 420
    L, R, T, B = 60, 10, 20, 40
    x = np.linspace(L, W - R, len(v))
    ymin, ymax = 0.0, float(v.max()) + 5
    yy = T + (H - T - B) * (1 - (v - ymin) / (ymax - ymin))
    pts = " ".join(f"{x[i]:.1f},{yy[i]:.1f}" for i in range(0, len(v), 2))
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
         f'font-family="monospace" font-size="12">',
         f'<rect width="{W}" height="{H}" fill="white"/>']
    for g in (0, 25, 50, 75, 100):
        gy = T + (H - T - B) * (1 - g / (ymax - ymin))
        s.append(f'<line x1="{L}" y1="{gy:.0f}" x2="{W-R}" y2="{gy:.0f}" '
                 f'stroke="#ddd"/>')
        s.append(f'<text x="{L-6}" y="{gy+4:.0f}" text-anchor="end" '
                 f'fill="#666">{g}</text>')
    for a, b in regions:
        s.append(f'<rect x="{x[a]-1:.1f}" y="{T}" width="{x[b]-x[a]+2:.1f}" '
                 f'height="{H-T-B}" fill="rgba(220,40,40,0.30)"/>')
    s.append(f'<polyline points="{pts}" fill="none" stroke="#246" '
             f'stroke-width="1"/>')
    days = sorted({t[:10] for t in ts})
    for d in days[::7]:
        i = ts.index(d + " 00:00:00") if d + " 00:00:00" in ts else \
            next(j for j, t in enumerate(ts) if t[:10] == d)
        s.append(f'<line x1="{x[i]:.1f}" y1="{T}" x2="{x[i]:.1f}" '
                 f'y2="{H-B}" stroke="#eee"/>')
        s.append(f'<text x="{x[i]:.1f}" y="{H-B+16}" text-anchor="middle" '
                 f'fill="#666">{d[5:]}</text>')
    s.append(f'<text x="{L}" y="14" fill="#333">'
             f'machine_temperature 2013-12-02 .. 2014-02-19 '
             f'(red=detected anomaly intervals)</text>')
    s.append("</svg>")
    with open(os.path.join(OUT_DIR, "anomaly_overview.svg"), "w",
              encoding="utf-8") as f:
        f.write("\n".join(s))


if __name__ == "__main__":
    main()
