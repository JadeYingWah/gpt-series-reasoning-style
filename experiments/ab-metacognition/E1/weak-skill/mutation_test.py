"""变异测试：对 todo.py 施加多个变异，运行 test_todo.py，统计杀伤率。"""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "todo.py")
TEST = os.path.join(HERE, "test_todo.py")

# 每个变异: (描述, 原字符串, 变异后字符串)
MUTATIONS = [
    ("M01 优先级排序权重 high 0→1", '"high": 0, "normal": 1', '"high": 1, "normal": 0'),
    ("M02 next_id 起始 1→0", "return 1\n    return max", "return 0\n    return max"),
    ("M03 删除 os.replace 原子重命名", "        os.replace(tmp_path, path)", "        pass  # mutated: no replace"),
    ("M04 done 不存在退出码 1→0", 'sys.exit(1)\n\n\ndef cmd_delete', 'sys.exit(0)\n\n\ndef cmd_delete'),
    ("M05 list pending 过滤改为 done", 'if status == "pending":\n        filtered = [t for t in todos if t["status"] == "pending"]',
     'if status == "pending":\n        filtered = [t for t in todos if t["status"] == "done"]'),
    ("M06 默认优先级 normal→high", 'default="normal",\n        help="优先级',
     'default="high",\n        help="优先级'),
    ("M07 done 不修改状态", 't["status"] = "done"', 't["status"] = "pending"  # mutated'),
    ("M08 delete 不删除", 'del todos[i]', 'pass  # mutated: no delete'),
    ("M09 排序状态权重反转", '0 if t["status"] == "pending" else 1',
     '1 if t["status"] == "pending" else 0'),
    ("M10 移除重复 done 友好提示分支", 'if t["status"] == "done":\n                print(f"#{t[\'id\']} 已经是已完成状态，无需重复标记。")\n                return',
     'if False:\n                pass  # mutated: removed duplicate check'),
]

killed = 0
survived = []
results = []

for desc, old, new in MUTATIONS:
    with open(SRC, "r", encoding="utf-8") as f:
        code = f.read()
    if old not in code:
        results.append((desc, "ERROR", "原字符串未找到"))
        survived.append(desc)
        continue
    mutated = code.replace(old, new, 1)
    d = tempfile.mkdtemp()
    try:
        with open(os.path.join(d, "todo.py"), "w", encoding="utf-8") as f:
            f.write(mutated)
        shutil.copy(TEST, os.path.join(d, "test_todo.py"))
        r = subprocess.run(
            [sys.executable, "test_todo.py"],
            cwd=d, capture_output=True, text=True, timeout=60
        )
        if r.returncode != 0:
            killed += 1
            results.append((desc, "KILLED", f"exit={r.returncode}"))
        else:
            survived.append(desc)
            results.append((desc, "SURVIVED", "测试未检出"))
    finally:
        shutil.rmtree(d, ignore_errors=True)

total = len(MUTATIONS)
rate = killed / total * 100
print("== 变异测试结果 ==")
for desc, status, detail in results:
    print(f"  [{status}] {desc}  ({detail})")
print(f"\n杀伤率: {killed}/{total} = {rate:.1f}%")
if survived:
    print("存活变异:", survived)
sys.exit(0 if rate >= 80 else 1)
