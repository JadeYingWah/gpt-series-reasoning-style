"""SCOPE01 A臂 — 一键复跑全部验证，生成 verify/report.txt
复跑：python run_all.py
"""
from pathlib import Path

from PIL import Image

import verify_pixels as vp

ROOT = Path(__file__).resolve().parent

PLAIN = [
    ("shot-800x600.png", "无头 Chrome 直接渲染 · 800x600"),
    ("shot-1280x800.png", "无头 Chrome 直接渲染 · 1280x800"),
    ("shot-500x667.png", "无头 Chrome 直接渲染 · 500x667"),
]
IFRAME = [("shot-responsive-375x667.png", (0, 0, 375, 667), "iframe 精确视口 · 375x667")]


def main():
    out = ["SCOPE01 A臂 · art.html 渲染验证报告", "=" * 46, ""]
    overall = True

    out += ["## 一、无头 Chrome 直接渲染（真实浏览器渲染 + 像素断言）", ""]
    for name, note in PLAIN:
        img = Image.open(ROOT / name).convert("RGB")
        lines, ok = vp.analyze(img, f"{name} — {note}")
        out += lines + [""]
        overall = overall and ok

    out += ["## 二、iframe 精确视口渲染（绕开 Chrome 最小窗口宽度限制）", ""]
    for name, crop, note in IFRAME:
        img = Image.open(ROOT / name).convert("RGB")
        x, y, w, h = crop
        lines, ok = vp.analyze(img.crop((x, y, x + w, y + h)), f"{name} — {note} [crop={crop}]")
        out += lines + [""]
        overall = overall and ok

    out += [
        "## 三、无头 Chrome 最小窗口宽度钳制 · 取证说明",
        "",
        "无头 Chrome 在 Windows 下把 --window-size 宽度钳制到约 500px，再按请求宽度裁切输出。",
        "因此 shot-375x667.png（已归档为 artifacts/window-clamped-375x667.png）中的圆",
        "看似「偏右且被截断」，而非居中——这是取证工具的假象，不是 art.html 的缺陷。",
        "证明：prove_clamp.py 逐像素比对 375 宽输出与 500 宽输出的左侧 375 列。",
        "",
    ]
    clamp = (ROOT / "clamp-evidence.txt").read_text(encoding="utf-8").strip()
    out += ["```", clamp, "```", ""]
    out += ["## 总判定", "", f"RESULT: {'PASS' if overall else 'FAIL'}（第一节 + 第二节全部用例）", ""]

    (ROOT / "report.txt").write_text("\n".join(out), encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
