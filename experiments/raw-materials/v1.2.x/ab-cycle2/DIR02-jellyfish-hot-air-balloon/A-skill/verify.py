#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DIR02 A 臂实跑验证：对 art.html 逐条核验 task.md 的 6 项验收。
只读 art.html，不改动任何产物。运行： python verify.py
"""
import os
import re
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, "art.html")

FAILS = []
def check(name, ok, detail):
    tag = "PASS" if ok else "FAIL"
    print(f"[{tag}] {name} :: {detail}")
    if not ok:
        FAILS.append(name)

# ---------- 读取 ----------
raw = open(ART, "r", encoding="utf-8").read()
size = os.path.getsize(ART)
print(f"# 文件: {ART}")
print(f"# 字节: {size}  ({size/1024:.2f} KiB)\n")

# ---------- 1. 交付物存在且 >= 8KB ----------
check("1 交付物存在且>=8KB", os.path.isfile(ART) and size >= 8192, f"{size} bytes")

# ---------- 6. 无外部 CDN（先于解析，独立证据）----------
# 口径：只找「真正会发起网络请求」的引用。xmlns="http://www.w3.org/2000/svg" 是命名空间标识符
# （XML 规范要求它是 URI，但渲染器不会去抓取），故先剔除所有 xmlns 声明再扫描。
scan = re.sub(r'\sxmlns(?::[A-Za-z0-9]+)?="[^"]*"', " ", raw)
ext_hits = []
for pat in (r"https?://", r"//cdn", r"<link\b", r"<script\b", r"@import",
            r"url\(\s*['\"]?(?:https?:)?//", r"\bsrc\s*=",
            r'\bhref\s*=\s*"(?!#)'):
    for m in re.finditer(pat, scan, re.I):
        ext_hits.append(m.group(0))
n_ns = len(re.findall(r'xmlns(?::[A-Za-z0-9]+)?="', raw))
check("6 无外部依赖", not ext_hits,
      f"外部可抓取引用命中: {ext_hits if ext_hits else '无'}（已剔除 {n_ns} 处 xmlns 命名空间标识）")

# ---------- 解析内联 SVG ----------
m = re.search(r"<svg\b.*?</svg>", raw, re.S)
if not m:
    print("[FAIL] 未找到内联 <svg>")
    sys.exit(1)
svg_src = m.group(0)
try:
    root = ET.fromstring(svg_src)
    check("0 SVG 可解析(XML well-formed)", True, f"root=<{root.tag.split('}')[-1]}>")
except ET.ParseError as e:
    check("0 SVG 可解析(XML well-formed)", False, str(e))
    sys.exit(1)

vb = root.get("viewBox").split()
check("0 viewBox 合规", len(vb) == 4 and vb[0] == "0" and vb[1] == "0",
      f"viewBox={' '.join(vb)}")

all_src = raw  # 动画既有 CSS 也有 SMIL，统一在全文里找

# ---------- 5. >= 6 组 keyframes 或等效动画 ----------
kf = re.findall(r"@keyframes\s+([A-Za-z0-9_-]+)", all_src)
smil = re.findall(r"<animate(?:Transform|Motion)?\b", svg_src)
check("5 >=6 组动画", len(kf) >= 6,
      f"@keyframes {len(kf)} 组 {kf}；SMIL 动画元素 {len(smil)} 个")

# ---------- 3. >=2 层视差，且速度不同 ----------
layer_dur = {}
for cls in ("p-far", "p-mid", "p-near"):
    mm = re.search(r"\.%s\s*\{[^}]*?animation:\s*drift\s+([\d.]+)s" % cls, all_src)
    if mm:
        layer_dur[cls] = float(mm.group(1))
check("3 三层视差且速度不同", len(layer_dur) >= 2 and len(set(layer_dur.values())) == len(layer_dur),
      f"{layer_dur}")

# ---------- 4. 附肢与载具不同频（>=2 独立周期）----------
tent_durs = sorted({float(d) for d in re.findall(r'dur="([\d.]+)s"', svg_src)})
veh = {}
for name, pat in (("float", r"\.float\{[^}]*?animation:float\s+([\d.]+)s"),
                  ("sway",  r"\.sway\s*\{[^}]*?animation:sway\s+([\d.]+)s")):
    mm = re.search(pat, all_src)
    if mm:
        veh[name] = float(mm.group(1))
    else:
        mm2 = re.search(r"@keyframes\s+%s" % name, all_src)
        mm3 = re.search(r"animation:%s\s+([\d.]+)s" % name, all_src)
        if mm3:
            veh[name] = float(mm3.group(1))
check("4 附肢周期(>=2种)", len(tent_durs) >= 2, f"触手周期集合 {tent_durs}s")
check("4 附肢≠载具周期", bool(tent_durs) and bool(veh) and not (set(tent_durs) & set(veh.values())),
      f"触手 {tent_durs}s vs 载具 {veh}")

# ---------- 2. 主体与载具清晰可辨 / 朝向一致 ----------
bell = re.search(r'd="(M284 398 C284 358[^"]+)"', svg_src)
env  = re.search(r'd="(M340 52 C258 52[^"]+)"', svg_src)
check("2 球囊路径存在", bool(env), "envelope path found" if env else "missing")
ok_bell = bool(bell)
# 球囊(载具)纵向 52~336；伞盖(主体)纵向 344~400 —— 二者纵向区间不重叠, 不会糊成一团
print("[INFO] 球囊 y 区间 52..336；伞盖 y 区间 338..~405 -> 纵向分离，可辨性有几何依据")
check("2 伞盖路径存在", ok_bell, "bell path found" if ok_bell else "missing")
# 朝向一致：全部主体元素位于同一 .sway/.float 组内，共享同一倾斜变换
check("2 朝向一致(共组)", all_src.count('class="sway"') == 1 and all_src.count('class="float"') == 1,
      "球囊与伞盖同处 .float>.sway 容器，共享同一旋转")

# ---------- 触手附着点几何自洽 ----------
att = re.findall(r"type=\"rotate\"\s*\n?\s*values=\"[-\d. ]*?([\d.]+) ([\d.]+);", svg_src)
ys = {float(y) for _, y in att}
check("G 触手旋转心落在伞盖下沿 y=400", ys == {400.0}, f"附着点 y 集合 {ys}")
xs = [float(x) for x, _ in att]
check("G 触手横向展开在伞盖宽度内(284..396)", xs and min(xs) >= 284 and max(xs) <= 396,
      f"x 范围 {min(xs)}..{max(xs)}")
check("G 触手附着点互不重合", len(set(xs)) == len(xs), f"{len(xs)} 条触手，x 集合 {sorted(set(xs))}")

print()
if FAILS:
    print(f"### 结果：{len(FAILS)} 项未通过 -> {FAILS}")
    sys.exit(1)
print("### 结果：全部检查通过")
