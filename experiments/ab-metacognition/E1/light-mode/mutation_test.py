#!/usr/bin/env python3
"""变异测试"""
import subprocess
import sys
import os
import shutil
import tempfile

TODO_PY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "todo.py")
TEST_PY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_todo.py")

MUTATIONS = [
    ("M01", "优先级排序权重 high 0→1", 'priority_order = {"high": 0,', 'priority_order = {"high": 1,'),
    ("M02", "next_id 起始 1→0", "return max([t[\"id\"] for t in todos], default=0) + 1", "return max([t[\"id\"] for t in todos], default=0)"),
    ("M03", "删除 os.replace 原子重命名", "os.replace(tmp, p)", "os.rename(tmp, p)"),
    ("M04", "done 不存在退出码 1→0", 'sys.exit(1)\n\n\ndef cmd_delete', 'sys.exit(0)\n\n\ndef cmd_delete'),
    ("M05", "list pending 过滤改为 done", 'if args.status == "pending":\n        todos = [t for t in todos if t["status"] == "pending"]', 'if args.status == "pending":\n        todos = [t for t in todos if t["status"] == "done"]'),
    ("M06", "默认优先级 normal→high", 'default="normal")', 'default="high")'),
    ("M07", "done 不修改状态", 't["status"] = "done"', 't["status"] = "pending"'),
    ("M08", "delete 不删除", "del todos[i]", "pass"),
    ("M09", "排序状态权重反转", "0 if t[\"status\"] == \"pending\" else 1", "1 if t[\"status\"] == \"pending\" else 0"),
    ("M10", "移除重复 done 友好提示分支", 'if t["status"] == "done":\n                print(f"#{args.id} 已经是完成状态")', 'if t["status"] == "done":\n                pass'),
]


def run_mutation(mid, desc, old, new):
    with open(TODO_PY, "r", encoding="utf-8") as f:
        original = f.read()

    if old not in original:
        print(f"[ERROR] {mid} {desc}: 找不到替换目标")
        return "ERROR"

    mutated = original.replace(old, new, 1)

    work_dir = tempfile.mkdtemp()
    try:
        mutated_path = os.path.join(work_dir, "todo.py")
        test_path = os.path.join(work_dir, "test_todo.py")
        shutil.copy2(TEST_PY, test_path)
        with open(mutated_path, "w", encoding="utf-8") as f:
            f.write(mutated)

        result = subprocess.run(
            [sys.executable, test_path],
            capture_output=True, text=True, cwd=work_dir,
            env={**os.environ, "PYTHONPATH": work_dir}
        )
        if result.returncode != 0:
            print(f"[KILLED] {mid} {desc}")
            return "KILLED"
        else:
            print(f"[SURVIVED] {mid} {desc}")
            return "SURVIVED"
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


if __name__ == "__main__":
    killed = 0
    total = len(MUTATIONS)
    for mid, desc, old, new in MUTATIONS:
        result = run_mutation(mid, desc, old, new)
        if result == "KILLED":
            killed += 1

    print(f"\n杀伤率: {killed}/{total} = {killed/total*100:.1f}%")
