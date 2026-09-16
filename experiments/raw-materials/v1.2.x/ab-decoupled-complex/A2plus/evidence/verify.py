"""复合类验证脚本 - A2+配置"""
import re

HTML = r"<实验根目录>\ab-decoupled-complex\A2plus\index.html"

with open(HTML, encoding="utf-8") as f:
    content = f.read()

print("=== 复合类验证 ===")

# 1. HTML结构检查
html_ok = "<!DOCTYPE html>" in content and "</html>" in content
print(f"  {'PASS' if html_ok else 'FAIL'} - HTML结构: DOCTYPE和闭合标签")

# 2. 三模块检查
modules = ["收入", "支出", "储蓄"]
found_modules = [m for m in modules if m in content]
c2 = len(found_modules) == 3
print(f"  {'PASS' if c2 else 'FAIL'} - 三模块: {found_modules}")

# 3. 数据可视化检查
has_canvas = "<canvas" in content
has_chart_js = "getContext" in content and "beginPath" in content
c3 = has_canvas and has_chart_js
print(f"  {'PASS' if c3 else 'FAIL'} - 数据可视化: canvas={has_canvas}, 绘图JS={has_chart_js}")

# 4. 响应式检查
has_media = "@media" in content
has_viewport = "viewport" in content
c4 = has_media and has_viewport
print(f"  {'PASS' if c4 else 'FAIL'} - 响应式: 媒体查询={has_media}, viewport={has_viewport}")

# 5. 示例数据检查
has_data = "const data" in content or "transactions" in content
has_income_data = "15000" in content or "income" in content
c5 = has_data and has_income_data
print(f"  {'PASS' if c5 else 'FAIL'} - 示例数据: 数据对象={has_data}")

# 6. CSS括号匹配
css_section = re.search(r"<style>(.*?)</style>", content, re.DOTALL)
if css_section:
    css = css_section.group(1)
    open_braces = css.count("{")
    close_braces = css.count("}")
    c6 = open_braces == close_braces
    print(f"  {'PASS' if c6 else 'FAIL'} - CSS括号: {open_braces}开/{close_braces}闭")
else:
    c6 = False
    print(f"  FAIL - CSS: 未找到style标签")

# 7. JS括号匹配
js_section = re.search(r"<script>(.*?)</script>", content, re.DOTALL)
if js_section:
    js = js_section.group(1)
    open_parens = js.count("(")
    close_parens = js.count(")")
    open_braces = js.count("{")
    close_braces = js.count("}")
    c7 = open_parens == close_parens and open_braces == close_braces
    print(f"  {'PASS' if c7 else 'FAIL'} - JS括号: (){open_parens}/{close_parens}, {{{open_braces}/{close_braces}")
else:
    c7 = False
    print(f"  FAIL - JS: 未找到script标签")

# 8. 交易列表功能
has_transaction_render = "createElement" in content and "appendChild" in content
c8 = has_transaction_render
print(f"  {'PASS' if c8 else 'FAIL'} - 交易渲染: DOM操作={has_transaction_render}")

allok = all([html_ok, c2, c3, c4, c5, c6, c7, c8])
print(f"\n总体: {'全部通过' if allok else '存在问题'}")
