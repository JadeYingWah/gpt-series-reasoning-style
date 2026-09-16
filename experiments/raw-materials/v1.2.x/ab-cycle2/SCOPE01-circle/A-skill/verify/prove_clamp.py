"""取证：无头 Chrome --window-size=375,667 是否被最小窗口宽度（500px）钳制后裁切。
方法：分别以 375、500 渲染同一页面，比较 375 图与 500 图左侧 375 列是否逐像素一致。
"""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent


def main():
    a = Image.open(ROOT / "shot-375x667.png").convert("RGB")
    b = Image.open(ROOT / "shot-500x667.png").convert("RGB")
    print(f"A(375) size={a.size}  B(500) size={b.size}")

    w = min(a.size[0], b.size[0])
    h = min(a.size[1], b.size[1])
    pa, pb = a.load(), b.load()

    diff = 0
    first = None
    for y in range(h):
        for x in range(w):
            if pa[x, y] != pb[x, y]:
                diff += 1
                if first is None:
                    first = (x, y, pa[x, y], pb[x, y])

    total = w * h
    print(f"重叠区域 {w}x{h}={total} 像素，不一致={diff} ({diff/total*100:.4f}%)")
    if first:
        print(f"首个不一致像素: {first}")
    print("结论: " + ("A 是 B 的左侧裁切（同一渲染）-> 375 窗口被钳制到 500 后按 375 裁切"
                     if diff == 0 else "两者非同一渲染，需另作解释"))


if __name__ == "__main__":
    main()
