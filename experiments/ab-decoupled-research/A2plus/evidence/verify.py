"""研究类验证脚本 - A2+配置"""
import re

REPORT = r"<实验根目录>\ab-decoupled-research\A2plus\report.md"

with open(REPORT, encoding="utf-8") as f:
    text = f.read()

print("=== 研究类验证 ===")

# 1. 结构完整性
sections = ["定义", "历史", "影响", "解决方案"]
found = [s for s in sections if s in text]
c1 = len(found) == 4
print(f"  {'PASS' if c1 else 'FAIL'} - 结构: {len(found)}/4部分 {found}")

# 2. 关键事实准确性
facts = {
    "GIL全称": "Global Interpreter Lock" in text or "全局解释器锁" in text,
    "CPython": "CPython" in text,
    "引用计数": "引用计数" in text,
    "PEP 703": "PEP 703" in text,
    "Python 3.13": "3.13" in text,
    "Python 3.14": "3.14" in text,
    "实验性": "实验性" in text,
    "多进程方案": "multiprocessing" in text or "多进程" in text,
    "异步方案": "asyncio" in text or "异步" in text,
}
c2 = all(facts.values())
for k, v in facts.items():
    print(f"    {'✓' if v else '✗'} {k}")
print(f"  {'PASS' if c2 else 'FAIL'} - 关键事实: {sum(facts.values())}/{len(facts)}")

# 3. 来源引用
urls = re.findall(r"https?://[^\s)]+", text)
c3 = len(urls) >= 2
print(f"  {'PASS' if c3 else 'FAIL'} - 来源引用: {len(urls)}个URL（要求≥2）")

# 4. 字数
# 去掉markdown标记和空白后的中文字数
chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
c4 = chinese_chars >= 500
print(f"  {'PASS' if c4 else 'FAIL'} - 字数: {chinese_chars}中文字（要求≥500）")

# 5. 时间线正确性
# 检查3.13是实验性、3.14是正式支持
timeline_ok = ("3.13" in text and "实验性" in text) and ("3.14" in text and "正式" in text)
print(f"  {'PASS' if timeline_ok else 'FAIL'} - 时间线: 3.13实验性+3.14正式支持")

allok = all([c1, c2, c3, c4, timeline_ok])
print(f"\n总体: {'全部通过' if allok else '存在问题'}")
