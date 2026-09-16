#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DIR02 A 臂实跑渲染验证（确定性定帧）。

问题：无头 Chrome 的 --virtual-time-budget 截图并不能可靠推进 CSS 动画时钟
（实测：4 个不同预算的截图里，天空昼夜层纹丝不动）。
做法：把 art.html 复制到临时目录，注入一段「暂停并定帧」脚本：
    document.getAnimations().forEach(a => {a.pause(); a.currentTime = T});
    svg.pauseAnimations(); svg.setCurrentTime(T/1000);
再截图，即可得到确定性的 t=T 帧。产物 art.html 本身不含该脚本。

运行： python verify_render.py
"""
import os, re, shutil, subprocess, sys
from PIL import Image, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, "art.html")
SHOTS = os.path.join(HERE, "_shots")
TMP = os.path.join(SHOTS, "_probe")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

INJECT = """
<script>
addEventListener('load', function(){
  var T = %d;
  try { document.getAnimations().forEach(function(a){ a.pause(); a.currentTime = T; }); } catch(e){}
  try { var s = document.querySelector('svg'); s.pauseAnimations(); s.setCurrentTime(T/1000); } catch(e){}
});
</script>
"""

FAILS = []
def check(name, ok, detail):
    print(f"[{'PASS' if ok else 'FAIL'}] {name} :: {detail}")
    if not ok:
        FAILS.append(name)

def render(phase_ms):
    os.makedirs(TMP, exist_ok=True)
    src = open(ART, encoding="utf-8").read()
    html = src.replace("</body>", INJECT % phase_ms + "</body>")
    path = os.path.join(TMP, f"phase-{phase_ms}.html")
    open(path, "w", encoding="utf-8").write(html)
    out = os.path.join(SHOTS, f"locked-{phase_ms}.png")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--force-device-scale-factor=1", "--window-size=760,760",
                    "--virtual-time-budget=3000", f"--screenshot={out}",
                    "file:///" + path.replace("\\", "/")],
                   capture_output=True)
    return out

def px(im, x, y):
    return im.convert("RGB").getpixel((x, y))

def diff_px(a, b, box, thr=8):
    d = ImageChops.difference(a.crop(box), b.crop(box)).convert("L")
    h = d.histogram()
    return sum(h[thr + 1:])

PHASES = [0, 750, 1500, 3000, 4500, 6000, 10800]
print("# 渲染相位帧（注入定帧脚本，确定性）：", PHASES, "ms\n")
frames = {}
for p in PHASES:
    f = render(p)
    if not os.path.isfile(f):
        check(f"渲染 t={p}ms", False, "未生成截图")
        sys.exit(1)
    frames[p] = Image.open(f).convert("RGB")
    print(f"  已生成 {os.path.basename(f)}  ({os.path.getsize(f)} bytes)")

# ---- 天空昼夜：夜里应显著变暗，黎明应回暖变亮 ----
def lum(im):
    r, g, b = px(im, 20, 30)
    return r + g + b

L = {p: lum(im) for p, im in frames.items()}
print(f"\n[INFO] 左上角天空亮度(RGB和) 随相位: {L}")
# 12s 循环里「满夜」窗口为 28%~60%（3.36s~7.2s），取 4.5s 与 6.0s 作为夜样本
dark = min(L[4500], L[6000])
dusk = L[0]        # t=0 黄昏层完全不透明
dawn = L[10800]    # 90% 黎明层主导
check("天空昼夜循环真的在变(定性)", L[4500] < 200 and L[6000] < 200,
      f"t=4.5s={L[4500]}, t=6.0s={L[6000]}（阈值<200 视为暗夜）")
check("黄昏/黎明明显亮于夜", dusk > dark + 120 and dawn > dark + 120,
      f"黄昏={dusk} 黎明={dawn} 夜={dark}")

# ---- 附肢独立周期：同一触手在 t=0 / t=0.75s（3s 周期的 1/4）应位移 ----
box_tent = (300, 400, 420, 560)
d_tent = diff_px(frames[0], frames[750], box_tent)
check("触手(附肢)在运动", d_tent > 200, f"t=0 vs t=0.75s 触手区差异像素 {d_tent}")

# ---- 视差层：远(20s)/中(12s)/近(7s) 速度不同 → 同一时间位移量不同 ----
box_far = (0, 630, 760, 700)     # 山脊
box_near = (0, 540, 760, 630)    # 近景云
d_far = diff_px(frames[0], frames[3000], box_far)
d_near = diff_px(frames[0], frames[3000], box_near)
check("远景层在运动", d_far > 200, f"远层 t=0 vs t=3s 差异 {d_far}")
check("近景层在运动", d_near > 200, f"近层 t=0 vs t=3s 差异 {d_near}")
check("两层视差速度不同", abs(d_far - d_near) > 500,
      f"同 3s 内 远景位移差异 {d_far} vs 近景 {d_near}（应显著不同）")

# ---- 载具升降：6s 周期，t=0 与 t=3s 应上下位移 ----
box_ship = (200, 40, 560, 480)
d_ship = diff_px(frames[0], frames[3000], box_ship)
check("载具(气球)在升降", d_ship > 500, f"t=0 vs t=3s 载具区差异 {d_ship}")

print()
if FAILS:
    print(f"### 渲染验证：{len(FAILS)} 项未通过 -> {FAILS}")
    sys.exit(1)
print("### 渲染验证：全部通过")
