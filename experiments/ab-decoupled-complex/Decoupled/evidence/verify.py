"""Complex verification - Decoupled"""
import re

with open(r"<实验根目录>\ab-decoupled-complex\Decoupled\index.html", encoding="utf-8") as f:
    c = f.read()

print("=== Complex Verification ===")
checks = [
    ("HTML结构", "<!DOCTYPE html>" in c and "</html>" in c),
    ("三模块", all(m in c for m in ["收入", "支出", "结余"])),
    ("可视化", "<canvas" in c and "getContext" in c),
    ("响应式", "@media" in c and "viewport" in c),
    ("示例数据", "const D" in c or "trend" in c),
    ("CSS括号", c.count("{") == c.count("}")),
    ("JS括号", c.count("(") == c.count(")")),
    ("DOM渲染", "createElement" in c and "appendChild" in c),
]
allok = True
for name, ok in checks:
    allok = allok and ok
    print(f"  {'PASS' if ok else 'FAIL'} - {name}")
print(f"\nOverall: {'ALL PASS' if allok else 'ISSUES'}")
