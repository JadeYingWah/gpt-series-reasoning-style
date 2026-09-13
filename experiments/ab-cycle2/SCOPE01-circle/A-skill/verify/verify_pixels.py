"""SCOPE01 A臂 — art.html 像素级验证
对无头 Chrome 截图做客观断言：颜色、居中、圆度、面积。
支持 --crop x,y,w,h 以校验收紧在 iframe 内的区域。

用法：
  python verify_pixels.py                      # 校验 verify/ 下所有 shot-*.png
  python verify_pixels.py --crop 0,0,375,667 shot-responsive.png
"""
import math
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
FILL = (47, 111, 237)      # #2f6fed
BG = (244, 244, 246)       # #f4f4f6
TOL = 12                   # 允许抗锯齿/色彩管理误差


def near(px, target, tol=TOL):
    return all(abs(px[i] - target[i]) <= tol for i in range(3))


def analyze(img, label):
    w, h = img.size
    px = img.load()

    fill_pts = []
    bad = 0
    for y in range(h):
        for x in range(w):
            p = px[x, y]
            if near(p, FILL):
                fill_pts.append((x, y))
            elif not near(p, BG):
                bad += 1

    lines = [f"# {label}  viewport={w}x{h}"]
    if not fill_pts:
        lines.append("FAIL 未找到任何圆形填充像素")
        return lines, False

    xs = [p[0] for p in fill_pts]
    ys = [p[1] for p in fill_pts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    bw, bh = x1 - x0 + 1, y1 - y0 + 1
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    area = len(fill_pts)
    area_ideal = math.pi * (bw / 2) * (bh / 2)
    ok = True

    ratio = bw / bh
    lines.append(f"包围盒 w={bw} h={bh} 宽高比={ratio:.4f}")
    if not (0.97 <= ratio <= 1.03):
        ok = False
        lines.append("FAIL 宽高比偏离 1（不是圆）")
    else:
        lines.append("PASS 宽高比在 ±3% 内 -> 圆形轮廓")

    fill_ratio = area / area_ideal
    lines.append(f"填充像素={area} 理论 πr²={area_ideal:.0f} 面积比={fill_ratio:.4f}")
    if not (0.96 <= fill_ratio <= 1.02):
        ok = False
        lines.append("FAIL 面积比偏离 1（非实心圆）")
    else:
        lines.append("PASS 面积比在容差内 -> 实心圆盘")

    dcx, dcy = abs(cx - w / 2), abs(cy - h / 2)
    lines.append(f"圆心=({cx:.1f},{cy:.1f}) 视口中心=({w/2:.1f},{h/2:.1f}) 偏差=({dcx:.1f},{dcy:.1f})")
    if dcx <= 2 and dcy <= 2:
        lines.append("PASS 圆心与视口中心重合（±2px）")
    else:
        ok = False
        lines.append("FAIL 圆心未居中")

    lines.append(f"中心像素={px[w//2, h//2]} 期望≈{FILL}")
    lines.append(f"四角像素={px[0,0]} {px[w-1,0]} {px[0,h-1]} {px[w-1,h-1]} 期望≈{BG}")
    if not near(px[w // 2, h // 2], FILL):
        ok = False
        lines.append("FAIL 中心非填充色")
    if not all(near(px[c], BG) for c in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]):
        ok = False
        lines.append("FAIL 角落非背景色")

    lines.append(f"非填充/非背景的杂色像素={bad}（抗锯齿边缘，允许 >0）")
    lines.append("RESULT: " + ("PASS" if ok else "FAIL"))
    return lines, ok


def parse_crop(argv):
    crop = None
    rest = []
    i = 0
    while i < len(argv):
        if argv[i] == "--crop":
            crop = tuple(int(v) for v in argv[i + 1].split(","))
            i += 2
            continue
        rest.append(argv[i])
        i += 1
    return crop, rest


def main():
    crop, names = parse_crop(sys.argv[1:])
    if names:
        shots = [ROOT / n for n in names]
    else:
        shots = sorted(ROOT.glob("shot-*.png"))

    out = []
    overall = True
    for s in shots:
        img = Image.open(s).convert("RGB")
        label = s.name + (f" [crop={crop}]" if crop else "")
        if crop:
            x, y, cw, ch = crop
            img = img.crop((x, y, x + cw, y + ch))
        lines, ok = analyze(img, label)
        out += lines + [""]
        overall = overall and ok

    text = "\n".join(out)
    (ROOT / "report.txt").write_text(text, encoding="utf-8")
    print(text)
    sys.exit(0 if overall else 1)


if __name__ == "__main__":
    main()
