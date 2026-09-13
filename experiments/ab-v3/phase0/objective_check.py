# -*- coding: utf-8 -*-
"""objective_check.py — Phase 0 客观比对脚本（协议 9.4 后处理第 3 步）
9 臂产物 vs 冻结真值（<实验根目录>/ab-v3/truth/frozen/*.json）
输出：<实验根目录>/ab-v3/phase0/objective_results.json + 控制台摘要
仅用 stdlib。真值文件与数据集一律只读。
"""
import csv
import io
import json
import os
import re
import sys
from datetime import datetime, timedelta

BASE = "<实验根目录>/ab-v3"
FROZEN = os.path.join(BASE, "truth", "frozen")
PHASE0 = os.path.join(BASE, "phase0")

ARMS = {
    "D1-winequality": ["Bprime", "A2", "A1"],
    "D2-cafe": ["Bprime", "A2", "A1"],
    "D3-nab": ["Bprime", "A2", "A1"],
}


def norm(text):
    """归一化：全角->半角、去空格/逗号/不间断空格、Unicode minus -> -"""
    table = str.maketrans({
        "\u2212": "-", "\u00a0": "", " ": "", ",": "", "\uff0c": "",
        "\uff1a": ":", "\u3000": "", "（": "(", "）": ")",
    })
    return text.translate(table)


def read_report(task, arm):
    p = os.path.join(PHASE0, task, arm, "report.md")
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as fh:
        return fh.read()


def check_numbers(text_norm, values, fmt="{:.6f}"):
    """检查每个数字的 6 位格式与去尾零格式是否出现在归一化文本中"""
    out = {}
    for label, v in values.items():
        s6 = fmt.format(abs(v))
        s_trim = s6.rstrip("0").rstrip(".") if "." in s6 else s6
        out[label] = (s6 in text_norm) or (len(s_trim) >= 3 and s_trim in text_norm)
    return out


# ---------------- D1 ----------------
def check_d1(arm, truth):
    rep = read_report("D1-winequality", arm)
    if rep is None:
        return {"exists": False}
    t = norm(rep)
    res = {"exists": True}
    # Q1 相关系数（11 项 |r|）
    corr = {name: r for name, r in truth["pearson_vs_quality_sorted_by_absdesc"]}
    hits = check_numbers(t, corr)
    res["q1_corr_11items"] = hits
    res["q1_all_found"] = all(hits.values())
    # 符号抽查：alcohol 为正、volatile acidity 为负
    res["q1_sign_alcohol_pos"] = ("+0.476166" in t) or ("0.476166" in t and "-0.476166" not in t)
    res["q1_sign_volatile_neg"] = ("-0.390558" in t)
    # 排序抽查：alcohol 的 r 出现位置早于 volatile acidity
    ia = t.find("0.476166"); iv = t.find("0.390558")
    res["q1_order_top2"] = (ia != -1 and iv != -1 and ia < iv)
    # Q2 计数（高特异性数字）
    counts = {f"q{q}": c for q, c in truth["quality_counts"].items()}
    chits = check_numbers(t, counts, fmt="{:.0f}")
    res["q2_counts"] = chits
    res["q2_all_found"] = all(chits.values())
    res["q2_total_1599"] = ("1599" in t)
    # Q3 均值与差值
    m_hits = check_numbers(t, {"hi": truth["alcohol_mean_q_ge7"], "lo": truth["alcohol_mean_q_le4"]})
    res["q3_means"] = m_hits
    # 差值：真值 1.3021（舍入序），全精度 1.3022 —— 两者均记为舍入伪差内
    res["q3_diff_1.3021"] = ("1.3021" in t)
    res["q3_diff_1.3022"] = ("1.3022" in t)
    res["q3_diff_ok"] = res["q3_diff_1.3021"] or res["q3_diff_1.3022"]
    return res


# ---------------- D2 ----------------
def check_d2(arm, truth):
    rep = read_report("D2-cafe", arm)
    if rep is None:
        return {"exists": False}
    t = norm(rep)
    res = {"exists": True}
    res["q1_repaired_462"] = "462" in t
    res["q1_valid_9960"] = "9960" in t
    res["q2_revenue_88952.00"] = ("88952.00" in t) or ("88952" in t)
    m = truth["missing_pre_repair"]
    q4 = check_numbers(t, {"TS": m["Total Spent"], "Qty": m["Quantity"], "Item": m["Item"]}, fmt="{:.0f}")
    res["q4_missing"] = q4
    res["q4_all_found"] = all(q4.values())
    # Q5 = 0：检查归一化文本中 "不一致" 相关行是否给出 0（宽松：含 "0行" 或 "=0"）
    res["q5_zero"] = bool(re.search(r"不一致[^。\n]{0,30}?0行|0行[^。\n]{0,30}?不一致|=0|为0", t)) or ("不一致" in t and "0" in t)
    # Q3 收入 8 项（与口径无关，硬指标）
    rev = {name: r for name, _c, r in truth["item_table_count_revenue_desc"]}
    rhits = check_numbers(t, rev)
    res["q3_revenue_8items"] = rhits
    res["q3_revenue_all_found"] = all(rhits.values())
    # Q3 计数口径 S（真值口径）
    cntS = {name: c for name, c, _r in truth["item_table_count_revenue_desc"]}
    shits = check_numbers(t, cntS, fmt="{:.0f}")
    res["q3_countS_8items"] = shits
    res["q3_countS_all_found"] = all(shits.values())
    # 口径 M（9031 分布）是否也并列出现
    cntM = {name: c + [3, 8, 5, 4, 2, 6, 4, 5][i] for i, (name, c, _r)
            in enumerate(truth["item_table_count_revenue_desc"])}
    mhits = check_numbers(t, cntM, fmt="{:.0f}")
    res["q3_countM_also_noted"] = sum(mhits.values())
    return res


# ---------------- D3 ----------------
def parse_intervals(task, arm):
    """优先 anomalies.csv；否则从 report.md 表格行抽时间戳，行内 min/max 作区间端点"""
    d = os.path.join(PHASE0, task, arm)
    ivs = []
    csvp = None
    for fn in os.listdir(d):
        if fn.lower().endswith(".csv"):
            csvp = os.path.join(d, fn)
    if csvp:
        with open(csvp, encoding="utf-8-sig") as fh:
            for row in csv.reader(fh):
                ts = [x for x in row if re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", x.strip())]
                if len(ts) >= 2:
                    a = datetime.strptime(ts[0], "%Y-%m-%d %H:%M:%S")
                    b = datetime.strptime(ts[1], "%Y-%m-%d %H:%M:%S")
                    ivs.append((min(a, b), max(a, b)))
        return ivs, os.path.basename(csvp)
    rep = read_report(task, arm)
    if rep is None:
        return [], None
    for line in rep.splitlines():
        if not line.strip().startswith("|"):
            continue
        ts = re.findall(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", line)
        if len(ts) >= 2:
            vals = [datetime.strptime(x, "%Y-%m-%d %H:%M:%S") for x in ts]
            s, e = min(vals), max(vals)
            # 过滤解析噪声：报告元数据行（如"时间范围"）会产生 >7 天的假区间；
            # 真实异常区间在本数据集上最长约 2 天。被过滤的行打印告警供人工复核。
            if (e - s).total_seconds() > 7 * 86400:
                print(f"  [parse-filter] 丢弃 >7d 的解析行: {s} ~ {e}  原行: {line.strip()[:80]}")
                continue
            ivs.append((s, e))
    return ivs, "report.md"


def check_d3(arm, truth):
    ivs, src = parse_intervals("D3-nab", arm)
    res = {"exists": bool(ivs), "interval_source": src, "n_reported": len(ivs)}
    if not ivs:
        return res
    tol = timedelta(hours=1)
    points = [datetime.strptime(p, "%Y-%m-%d %H:%M:%S") for p in truth["anomaly_points_labeled"]]
    detail = []
    hit_interval_idx = set()
    n_hits = 0
    for li, L in enumerate(points):
        got = None
        for i, (s, e) in enumerate(ivs):  # 报告顺序 = 先到先得
            if s <= L <= e or abs(s - L) <= tol or abs(e - L) <= tol:
                got = i
                break
        if got is not None:
            n_hits += 1
            hit_interval_idx.add(got)
        detail.append({"label": truth["anomaly_points_labeled"][li],
                       "hit": got is not None, "interval_idx": got})
    res["detail"] = detail
    res["recall"] = n_hits / len(points)
    res["precision"] = len(hit_interval_idx) / len(ivs)
    res["n_hits"] = n_hits
    return res


def main():
    results = {}
    with open(os.path.join(FROZEN, "d1_truth.json"), encoding="utf-8") as fh:
        d1 = json.load(fh)
    with open(os.path.join(FROZEN, "d2_truth.json"), encoding="utf-8") as fh:
        d2 = json.load(fh)
    with open(os.path.join(FROZEN, "d3_truth.json"), encoding="utf-8") as fh:
        d3 = json.load(fh)

    for task, arms in ARMS.items():
        for arm in arms:
            if not os.path.isdir(os.path.join(PHASE0, task, arm)):
                continue
            if task == "D1-winequality":
                r = check_d1(arm, d1)
            elif task == "D2-cafe":
                r = check_d2(arm, d2)
            else:
                r = check_d3(arm, d3)
            results[f"{task}/{arm}"] = r

    out = os.path.join(PHASE0, "objective_results.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(results, fh, ensure_ascii=False, indent=2)

    # 控制台摘要
    print("=" * 64)
    for key, r in results.items():
        print(f"\n[{key}]")
        if not r.get("exists"):
            print("  产物不存在")
            continue
        if key.startswith("D1"):
            print(f"  Q1 11项r全对: {r['q1_all_found']}  符号(a+/v-): {r['q1_sign_alcohol_pos']}/{r['q1_sign_volatile_neg']}  Top2序: {r['q1_order_top2']}")
            print(f"  Q2 计数全对: {r['q2_all_found']}  合计1599: {r['q2_total_1599']}")
            print(f"  Q3 均值对: {all(r['q3_means'].values())}  差值1.3021/1.3022: {r['q3_diff_1.3021']}/{r['q3_diff_1.3022']}")
        elif key.startswith("D2"):
            print(f"  Q1 462/9960: {r['q1_repaired_462']}/{r['q1_valid_9960']}  Q2 88952.00: {r['q2_revenue_88952.00']}")
            print(f"  Q4 缺失全对: {r['q4_all_found']}  Q5零: {r['q5_zero']}")
            print(f"  Q3 收入8项全对: {r['q3_revenue_all_found']}  计数口径S全对: {r['q3_countS_all_found']}  口径M并列出现数: {r['q3_countM_also_noted']}/8")
        else:
            if r["exists"]:
                print(f"  报告区间数: {r['n_reported']} (源: {r['interval_source']})  命中: {r['n_hits']}/4  recall={r['recall']:.2f}  precision={r['precision']:.2f}")
                for dd in r["detail"]:
                    print(f"    {dd['label']}  hit={dd['hit']}" + (f" <- 区间#{dd['interval_idx']}" if dd['hit'] else ""))
            else:
                print("  未解析到区间")
    print("\n结果已写入:", out)


if __name__ == "__main__":
    main()
