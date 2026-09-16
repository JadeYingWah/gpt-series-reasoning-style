"""视觉类验证 - 解耦版"""
import re, xml.etree.ElementTree as ET

def hex_to_rgb(h):
    h = h.lstrip('#'); return tuple(int(h[i:i+2], 16) for i in (0,2,4))
def lum(rgb):
    def c(v):
        v = v/255.0; return v/12.92 if v <= 0.03928 else ((v+0.055)/1.055)**2.4
    return 0.2126*c(rgb[0]) + 0.7152*c(rgb[1]) + 0.0722*c(rgb[2])
def ratio(c1, c2):
    l1, l2 = lum(hex_to_rgb(c1)), lum(hex_to_rgb(c2))
    return (max(l1,l2)+0.05)/(min(l1,l2)+0.05)

pairs = [
    ("#FFFFFF", "#4F46E5", "主按钮"),
    ("#FFFFFF", "#4338CA", "悬停按钮"),
    ("#FFFFFF", "#3730A3", "禁用按钮"),
    ("#1F2937", "#FFFFFF", "正文"),
    ("#6B7280", "#FFFFFF", "辅助文字"),
]
print("=== 对比度 ===")
allok = True
for fg, bg, desc in pairs:
    r = ratio(fg, bg)
    ok = r >= 4.5
    allok = allok and ok
    print(f"  {'PASS' if ok else 'FAIL'} - {desc}: {r:.2f}:1")

print("\n=== SVG语法 ===")
try:
    t = ET.parse(r"<实验根目录>\ab-decoupled-visual\Decoupled\button.svg")
    print(f"  PASS - 解析成功")
except Exception as e:
    print(f"  FAIL - {e}"); allok = False

print("\n=== 完整性 ===")
with open(r"<实验根目录>\ab-decoupled-visual\Decoupled\brand.md", encoding="utf-8") as f:
    text = f.read()
colors = set(re.findall(r"#[0-9A-Fa-f]{6}", text))
states = sum(1 for s in ["默认", "悬停", "禁用"] if s in text)
comp_ok = len(colors) >= 5 and states == 3
allok = allok and comp_ok
print(f"  {'PASS' if comp_ok else 'FAIL'} - 颜色{len(colors)}种，状态{states}/3")

print(f"\n总体: {'全部通过' if allok else '存在问题'}")
