# -*- coding: utf-8 -*-
"""数据获取脚本
主源：腾讯财经行情接口（前复权日线，分年窗口抓取合并）
备源：新浪财经行情接口（不复权日线）
输出：data/600519_daily.csv + data/meta.json
"""
import json
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)

CODE, NAME = "600519", "贵州茅台"
WINDOWS = [
    ("2023-01-01", "2023-12-31"),
    ("2024-01-01", "2024-12-31"),
    ("2025-01-01", "2025-12-31"),
    ("2026-01-01", "2026-12-31"),
]
HDRS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def http_json(url, tries=3):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=HDRS)
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.loads(r.read().decode("utf-8", "ignore"))
        except Exception as e:  # 保守重试：指数退避，最多3次
            last = e
            time.sleep(1.5 * (i + 1))
    raise RuntimeError(f"请求失败 {url}: {last!r}")


def fetch_tencent():
    """返回 {date: [date, open, close, high, low, volume(手)]}，前复权"""
    rows = {}
    for beg, end in WINDOWS:
        url = (f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?"
               f"param=sh{CODE},day,{beg},{end},320,qfq")
        d = http_json(url)["data"][f"sh{CODE}"]
        arr = d.get("qfqday") or d.get("day") or []
        for r in arr:
            rows[r[0]] = [r[0], r[1], r[2], r[3], r[4], r[5]]
    if len(rows) < 200:
        raise RuntimeError(f"腾讯接口返回行数过少: {len(rows)}")
    return rows


def fetch_sina():
    """备源：不复权"""
    url = (f"https://quotes.sina.cn/cn/api/json_v2.php/CN_MarketDataService.getKLineData"
           f"?symbol=sh{CODE}&scale=240&ma=no&datalen=1023")
    arr = http_json(url)
    rows = {r["day"]: [r["day"], r["open"], r["close"], r["high"], r["low"], r["volume"]]
            for r in arr}
    if len(rows) < 200:
        raise RuntimeError(f"新浪接口返回行数过少: {len(rows)}")
    return rows


src = None
try:
    rows = fetch_tencent()
    src = ("腾讯财经行情接口 web.ifzq.gtimg.cn", "前复权(qfq)")
except Exception as e:
    print("腾讯接口失败，切换新浪备源:", e)
    rows = fetch_sina()
    src = ("新浪财经行情接口 quotes.sina.cn", "不复权")

dates = sorted(rows)
recs = []
prev_close = None
for d in dates:
    _, o, c, h, l, v = rows[d]
    o, c, h, l, v = float(o), float(c), float(h), float(l), float(v)
    pct = (c / prev_close - 1) * 100 if prev_close else ""
    amp = (h - l) / prev_close * 100 if prev_close else ""
    chg = c - prev_close if prev_close else ""
    # 成交额近似：均价*股数（接口未直接提供）
    amount = (o + h + l + c) / 4 * v * 100
    recs.append([d, o, c, h, l, v, round(amount, 0), amp, pct, chg, ""])

cols = ["date", "open", "close", "high", "low", "volume",
        "amount", "amplitude", "pct_chg", "change", "turnover"]
out = DATA / f"{CODE}_daily.csv"
with open(out, "w", newline="", encoding="utf-8") as f:
    f.write(",".join(cols) + "\n")
    for r in recs:
        f.write(",".join(str(x) for x in r) + "\n")

# ---------- 数据校验 ----------
with open(out, encoding="utf-8") as f:
    lines = f.read().strip().split("\n")[1:]
prev = None
for ln in lines:
    p = ln.split(",")
    o, c, h, l = float(p[1]), float(p[2]), float(p[3]), float(p[4])
    assert h >= max(o, c) - 1e-6 and l <= min(o, c) + 1e-6, f"OHLC 异常 {p[0]}"
    assert l > 0, f"价格异常 {p[0]}"
    if prev:
        assert p[0] > prev, "日期乱序"
    prev = p[0]

meta = {
    "code": CODE, "name": NAME, "market": "上交所",
    "source": src[0], "fq": src[1], "klt": "日线",
    "first_date": recs[0][0], "last_date": recs[-1][0], "rows": len(recs),
    "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
}
(DATA / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"OK: {meta['rows']} rows, {meta['first_date']} -> {meta['last_date']}, source={src[0]}, fq={src[1]}")
