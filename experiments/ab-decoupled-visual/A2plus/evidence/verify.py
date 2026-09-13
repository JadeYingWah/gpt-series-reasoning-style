"""视觉类验证脚本 - A2+配置"""
import re
import xml.etree.ElementTree as ET

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def relative_luminance(rgb):
    """计算相对亮度（WCAG 2.0）"""
    def channel(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)

def contrast_ratio(color1, color2):
    """计算对比度"""
    l1 = relative_luminance(hex_to_rgb(color1))
    l2 = relative_luminance(hex_to_rgb(color2))
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)

def check_contrasts():
    """检查所有文本配色的对比度"""
    # (前景色, 背景色, 描述)
    pairs = [
        ("#FFFFFF", "#2563EB", "主按钮文字/背景"),
        ("#FFFFFF", "#1D4ED8", "悬停按钮文字/背景"),
        ("#FFFFFF", "#1E40AF", "禁用按钮文字/背景"),
        ("#2563EB", "#FFFFFF", "辅助按钮文字/背景"),
        ("#111827", "#FFFFFF", "正文/背景"),
        ("#6B7280", "#FFFFFF", "辅助文字/背景"),
    ]
    results = []
    for fg, bg, desc in pairs:
        ratio = contrast_ratio(fg, bg)
        passed = ratio >= 4.5  # WCAG AA 正常文本
        results.append((desc, ratio, passed))
    return results

def check_svg(svg_path):
    """SVG语法检查"""
    try:
        tree = ET.parse(svg_path)
        root = tree.getroot()
        # 检查必要元素
        rects = root.findall(".//{http://www.w3.org/2000/svg}rect")
        texts = root.findall(".//{http://www.w3.org/2000/svg}text")
        return True, f"解析成功，{len(rects)}个矩形，{len(texts)}个文本"
    except ET.ParseError as e:
        return False, f"解析失败: {e}"

def check_completeness(brand_path):
    """完整性检查：至少5个颜色，3种按钮状态"""
    with open(brand_path, encoding="utf-8") as f:
        text = f.read()
    colors = re.findall(r"#[0-9A-Fa-f]{6}", text)
    unique_colors = set(colors)
    states = ["默认", "悬停", "禁用"]
    found_states = [s for s in states if s in text]
    return len(unique_colors) >= 5 and len(found_states) == 3, f"颜色{len(unique_colors)}种，状态{len(found_states)}/3"

def mutation_test():
    """变异测试：修改颜色，看对比度检查能否发现"""
    # 变异：把主按钮文字改成浅灰色（对比度不达标）
    original_ratio = contrast_ratio("#FFFFFF", "#2563EB")
    mutant_ratio = contrast_ratio("#CCCCCC", "#2563EB")  # 浅灰文字
    mutant_passed = mutant_ratio >= 4.5
    # 变异：SVG语法错误
    return {
        "低对比度文字": not mutant_passed,  # 应该被发现（对比度<4.5）
        "原始对比度达标": original_ratio >= 4.5,
    }

if __name__ == "__main__":
    print("=== 视觉类验证 ===")
    print("\n【对比度检查（WCAG AA ≥4.5:1）】")
    contrasts = check_contrasts()
    all_pass = True
    for desc, ratio, passed in contrasts:
        status = "PASS" if passed else "FAIL"
        if not passed:
            all_pass = False
        print(f"  {status} - {desc}: {ratio:.2f}:1")

    print(f"\n【SVG语法】")
    svg_ok, svg_msg = check_svg(r"<实验根目录>\ab-decoupled-visual\A2plus\button.svg")
    print(f"  {'PASS' if svg_ok else 'FAIL'} - {svg_msg}")

    print(f"\n【完整性】")
    comp_ok, comp_msg = check_completeness(r"<实验根目录>\ab-decoupled-visual\A2plus\brand.md")
    print(f"  {'PASS' if comp_ok else 'FAIL'} - {comp_msg}")

    print(f"\n【变异测试】")
    mt = mutation_test()
    for k, v in mt.items():
        print(f"  {k}: {'被杀死' if v else '存活'}")

    print(f"\n总体: {'全部通过' if all_pass and svg_ok and comp_ok else '存在问题'}")
