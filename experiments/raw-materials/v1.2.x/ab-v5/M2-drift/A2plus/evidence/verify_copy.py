# -*- coding: utf-8 -*-
"""A2+ 轻量+ 双路径交叉验证 · 方法A（程序化机械核验）
统计口径（最保守）：非空白字符数（含标点、数字、符号）。
运行: python verify_copy.py
"""
import re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BASE = r"<实验根目录>\ab-v5\M2-drift\A2plus"
TEXT = open(BASE + r"\copy.md", encoding="utf-8").read()

def seg(pattern):
    m = re.search(pattern, TEXT, re.S)
    return m.group(1).strip() if m else None

slogan = seg(r"## 主 slogan\s*\n+(.+?)\n+\s*##")
posts = re.findall(r"\*\*其[一二三][^*]*\*\*\s*\n+(.+?)(?=\n\n|\Z)", TEXT, re.S)
story = seg(r"## 产品故事[^\n]*\n+(.+?)\s*$")

def n(x):
    return len(re.sub(r"\s", "", x)) if x else -1

ORIGIN = ["云南", "保山", "高黎贡山"]
FLAVOR = ["柑橘", "茉莉", "红糖", "酸质"]
BANNED = ["匠心", "臻选", "尊享", "醇香", "馥郁", "极致", "奢华", "唤醒每一个清晨"]

results = []
def check(name, ok, detail):
    results.append((name, "PASS" if ok else "FAIL", detail))

check("结构·主slogan存在且非空", slogan is not None and n(slogan) > 0, f"len={n(slogan)}")
check("结构·短文案恰3条", len(posts) == 3, f"count={len(posts)}")
check("结构·故事恰1段存在", story is not None, f"len={n(story)}")
for i, p in enumerate(posts, 1):
    check(f"字数·短文案{i} ≤100(非空白,最保守口径)", 0 < n(p) <= 100, f"len={n(p)}")
check("字数·故事 195-205(约200字)", story is not None and 195 <= n(story) <= 205, f"len={n(story)}")
for i, p in enumerate(posts, 1):
    o = [w for w in ORIGIN if w in p]
    f = [w for w in FLAVOR if w in p]
    check(f"关键词·短文案{i}含产地词", len(o) > 0, "命中:" + (",".join(o) or "无"))
    check(f"关键词·短文案{i}含风味词", len(f) > 0, "命中:" + (",".join(f) or "无"))
o = [w for w in ORIGIN if w in (story or "")]
f = [w for w in FLAVOR if w in (story or "")]
check("关键词·故事含产地词", len(o) > 0, "命中:" + (",".join(o) or "无"))
check("关键词·故事含风味词", len(f) > 0, "命中:" + (",".join(f) or "无"))
hits = [w for w in BANNED if w in TEXT]
check("禁用词·浮夸词零命中(不装腔机械代理)", len(hits) == 0, "命中:" + (",".join(hits) or "无"))
check("差异化·3条短文案开头30字符互不重复", len({re.sub(r'\s', '', p)[:30] for p in posts}) == 3,
      f"去重后={len({re.sub(chr(92)+'s','',p)[:30] for p in posts})}")

passed = sum(1 for r in results if r[1] == "PASS")
print("方法A（程序化机械核验）")
print(f"统计口径: 非空白字符（含标点，最保守）")
for name, st, d in results:
    print(f"  [{st}] {name} — {d}")
print(f"结果: {passed}/{len(results)} PASS " + ("| ALL GREEN" if passed == len(results) else "| HAS FAIL"))
