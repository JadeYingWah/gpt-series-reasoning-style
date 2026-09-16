# -*- coding: utf-8 -*-
"""
01 数据获取：腾讯公开行情接口拉取 贵州茅台(600519.SH) 日线（2020-01-01 起）
输出:
  data/600519_daily_qfq.csv  前复权日线(指标/回测用)   [date,open,close,high,low,volume]
  data/600519_daily_raw.csv  不复权日线(公开报价核对用)
  data/fetch_meta.json       取数元信息 + 与独立第二源(westock, agentic_search 2026-09-16 返回)的自动交叉校验
仅用标准库。
数据源: web.ifzq.gtimg.cn (腾讯行情, 公开接口)
独立校验源: westock-data kline sh600519 (经 agentic_search 于 2026-09-16 15:46 CST 返回)
"""
import csv
import json
import os
import time
import urllib.request
from datetime import datetime, timezone, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
os.makedirs(DATA, exist_ok=True)

CST = timezone(timedelta(hours=8))
FETCH_TIME = datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S CST")

FIELDS = ["date", "open", "close", "high", "low", "volume"]

# 独立第二源锚点: westock-data kline sh600519 最近10个交易日 (agentic_search 2026-09-16 返回)
# 列: date, open, close, high, low, volume(手)
ANCHOR_WESTOCK = [
    ["2026-09-16", 1273.93, 1258.00, 1274.98, 1254.10, 26235],
    ["2026-09-15", 1281.00, 1272.75, 1284.50, 1271.28, 13762],
    ["2026-09-14", 1277.27, 1277.96, 1285.53, 1270.36, 16571],
    ["2026-09-11", 1285.15, 1275.16, 1286.15, 1263.01, 34801],
    ["2026-09-10", 1291.00, 1285.13, 1294.99, 1282.00, 18900],
    ["2026-09-09", 1305.01, 1290.88, 1309.30, 1286.68, 32226],
    ["2026-09-08", 1318.00, 1309.30, 1323.00, 1309.05, 17534],
    ["2026-09-07", 1324.00, 1316.01, 1333.60, 1312.66, 25250],
    ["2026-09-04", 1295.88, 1330.00, 1338.86, 1295.60, 45416],
    ["2026-09-03", 1297.50, 1298.88, 1305.00, 1293.02, 17748],
]


def http_get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://gu.qq.com/",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch_year(year: int, fq: str):
    """fq='qfq' 前复权 / 'raw' 不复权。返回 [{date,open,close,high,low,volume}]"""
    fq_param = "qfq" if fq == "qfq" else ""
    url = (f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?"
           f"param=sh600519,day,{year}-01-01,{year}-12-31,320,{fq_param}")
    j = http_get_json(url)
    d = j["data"]["sh600519"]
    key = "qfqday" if fq == "qfq" else "day"
    arr = d.get(key) or d.get("day")
    if arr is None:
        raise RuntimeError(f"{year} {fq}: 响应中无 {key} 键, 顶层键: {list(d.keys())}")
    rows = []
    for bar in arr:
        # 腾讯K线列序: [date, open, close, high, low, volume, ...]
        rows.append({
            "date": bar[0],
            "open": float(bar[1]),
            "close": float(bar[2]),
            "high": float(bar[3]),
            "low": float(bar[4]),
            "volume": float(bar[5]),
        })
    return rows


def fetch_realtime_bar():
    """腾讯实时快照 qt.gtimg.cn, GBK 编码, ~ 分隔。
    字段: [1]名称 [2]代码 [3]现价 [4]昨收 [5]今开 [6]量(手) [30]时间 [33]最高 [34]最低
    """
    url = "https://qt.gtimg.cn/q=sh600519"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        text = r.read().decode("gbk")
    f = text.split('"')[1].split("~")
    return {
        "name": f[1],
        "price": float(f[3]),
        "prev_close": float(f[4]),
        "open": float(f[5]),
        "volume_hand": float(f[6]),
        "quote_time": f[30],
        "high": float(f[33]),
        "low": float(f[34]),
    }


def append_today(rows, rt):
    """将当日实时 bar 追加到日线序列(仅当序列未含当日且复权连续性成立)。
    前复权口径下, 最新 bar 价格 = 不复权价格(除权日之外), 用昨收一致性做守卫。
    """
    last_date = rows[-1]["date"]
    bar_date = f"{rt['quote_time'][:4]}-{rt['quote_time'][4:6]}-{rt['quote_time'][6:8]}"
    if bar_date <= last_date:
        return rows, None
    # 复权连续性守卫: 序列最后一根的收盘必须等于快照昨收, 否则口径断裂, 不追加
    if abs(rows[-1]["close"] - rt["prev_close"]) > 0.01:
        return rows, f"复权连续性守卫触发: 序列末收盘 {rows[-1]['close']} != 快照昨收 {rt['prev_close']}, 未追加"
    bar = {"date": bar_date, "open": rt["open"], "close": rt["price"],
           "high": rt["high"], "low": rt["low"], "volume": rt["volume_hand"]}
    rows = rows + [bar]
    return rows, None


def fetch_all(fq: str):
    merged = {}
    for y in range(2020, 2027):
        for r in fetch_year(y, fq):
            merged[r["date"]] = r
        time.sleep(0.4)
    rows = [merged[k] for k in sorted(merged)]
    return rows


def fetch_all_with_today(fq: str):
    rows = fetch_all(fq)
    rt = fetch_realtime_bar()
    rows, note = append_today(rows, rt)
    return rows, rt, note


def save_csv(rows, path):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)


def sanity_check(rows):
    problems = []
    if len(rows) < 1000:
        problems.append(f"行数过少: {len(rows)}")
    dates = [r["date"] for r in rows]
    if dates != sorted(dates):
        problems.append("日期非单调递增")
    if len(set(dates)) != len(dates):
        problems.append("日期重复")
    for r in rows:
        o, c, h, l = r["open"], r["close"], r["high"], r["low"]
        if min(o, c, h, l) <= 0:
            problems.append(f"{r['date']} 非正价格")
            break
        if h < l - 1e-6 or h < max(o, c) - 1e-6 or l > min(o, c) + 1e-6:
            problems.append(f"{r['date']} 高低开收关系异常")
            break
        if r["volume"] < 0:
            problems.append(f"{r['date']} 负成交量")
            break
    return problems


def cross_check(rows_qfq):
    """与独立第二源 westock 逐根核对最近10个交易日"""
    idx = {r["date"]: r for r in rows_qfq}
    results, mismatches = [], 0
    for a in ANCHOR_WESTOCK:
        date, wo, wc, wh, wl, wv = a
        r = idx.get(date)
        if r is None:
            results.append({"date": date, "status": "缺失"})
            mismatches += 1
            continue
        diffs = {
            "open": round(abs(r["open"] - wo), 4),
            "close": round(abs(r["close"] - wc), 4),
            "high": round(abs(r["high"] - wh), 4),
            "low": round(abs(r["low"] - wl), 4),
            "volume": round(abs(r["volume"] - wv) / max(wv, 1), 6),
        }
        ok = max(diffs["open"], diffs["close"], diffs["high"], diffs["low"]) <= 0.01 and diffs["volume"] <= 0.001
        results.append({"date": date, "status": "一致" if ok else "不一致", "max_abs_diff": diffs})
        mismatches += 0 if ok else 1
    return results, mismatches


def main():
    print("[..] 拉取前复权日线 (2020-2026, 分年请求)...")
    rows_qfq, rt, note1 = fetch_all_with_today("qfq")
    print("[..] 拉取不复权日线...")
    rows_raw, _, note2 = fetch_all_with_today("raw")
    if note1:
        print(f"[NOTE] qfq: {note1}")
    if note2:
        print(f"[NOTE] raw: {note2}")
    print(f"[OK] 实时快照: {rt['price']} ({rt['quote_time']}), 昨收 {rt['prev_close']}")

    p1 = sanity_check(rows_qfq)
    p2 = sanity_check(rows_raw)

    save_csv(rows_qfq, os.path.join(DATA, "600519_daily_qfq.csv"))
    save_csv(rows_raw, os.path.join(DATA, "600519_daily_raw.csv"))
    print(f"[OK] CSV 已保存: 前复权 {len(rows_qfq)} 行 / 不复权 {len(rows_raw)} 行")

    cc, n_bad = cross_check(rows_qfq)
    for c in cc:
        print(f"     校验 {c['date']}: {c['status']}"
              + (f" {c.get('max_abs_diff')}" if "max_abs_diff" in c else ""))

    last = rows_raw[-1]
    meta = {
        "stock_code": "600519.SH",
        "stock_name": "贵州茅台",
        "source": "腾讯公开行情接口 web.ifzq.gtimg.cn/appstock/app/fqkline/get (日K, 前复权/不复权)",
        "independent_check_source": "westock-data kline sh600519 (agentic_search 2026-09-16 15:46 CST 返回)",
        "fetch_time": FETCH_TIME,
        "rows_qfq": len(rows_qfq),
        "rows_raw": len(rows_raw),
        "date_start": rows_qfq[0]["date"],
        "date_end": rows_qfq[-1]["date"],
        "volume_unit": "手 (1手=100股)",
        "sanity_problems_qfq": p1,
        "sanity_problems_raw": p2,
        "cross_check_anchor_count": len(ANCHOR_WESTOCK),
        "cross_check_mismatch_count": n_bad,
        "cross_check_detail": cc,
        "realtime_snapshot": rt,
        "append_today_notes": {"qfq": note1, "raw": note2},
        "last_bar_raw": last,
        "last_bar_qfq": rows_qfq[-1],
    }
    with open(os.path.join(DATA, "fetch_meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"[OK] 区间 {meta['date_start']} ~ {meta['date_end']}")
    print(f"[OK] 最新K线(不复权): {last}")
    print(f"[OK] 独立源交叉校验: {len(ANCHOR_WESTOCK)} 根中 {n_bad} 根不一致")
    if p1 or p2 or n_bad:
        print("[WARN] 存在校验问题, 详见 fetch_meta.json")
        raise SystemExit(1)
    print("[OK] 全部校验通过")


if __name__ == "__main__":
    main()
