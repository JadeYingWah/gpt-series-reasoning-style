"""Research verification - Decoupled"""
import re

with open(r"<实验根目录>\ab-decoupled-research\Decoupled\report.md", encoding="utf-8") as f:
    text = f.read()

print("=== Research Verification ===")
sections = ["定义", "历史", "影响", "解决方案"]
found = [s for s in sections if s in text]
c1 = len(found) == 4
print(f"  {'PASS' if c1 else 'FAIL'} - Structure: {len(found)}/4")

facts = {
    "GIL全称": "Global Interpreter Lock" in text,
    "CPython": "CPython" in text,
    "引用计数": "引用计数" in text,
    "PEP 703": "PEP 703" in text,
    "3.13": "3.13" in text,
    "3.14": "3.14" in text,
    "实验性": "实验性" in text,
    "多进程": "多进程" in text or "multiprocessing" in text,
    "异步": "异步" in text or "asyncio" in text,
}
c2 = all(facts.values())
print(f"  {'PASS' if c2 else 'FAIL'} - Facts: {sum(facts.values())}/{len(facts)}")
for k, v in facts.items():
    if not v: print(f"    MISSING: {k}")

urls = re.findall(r"https?://[^\s)]+", text)
c3 = len(urls) >= 2
print(f"  {'PASS' if c3 else 'FAIL'} - Sources: {len(urls)} URLs")

chars = len(re.findall(r'[\u4e00-\u9fff]', text))
c4 = chars >= 300  # 解耦版字数要求降低
print(f"  {'PASS' if c4 else 'FAIL'} - Length: {chars} Chinese chars (>=300)")

timeline = ("3.13" in text and "实验性" in text) and ("3.14" in text and "正式" in text)
print(f"  {'PASS' if timeline else 'FAIL'} - Timeline: 3.13 experimental + 3.14 supported")

allok = all([c1, c2, c3, c4, timeline])
print(f"\nOverall: {'ALL PASS' if allok else 'ISSUES'}")
