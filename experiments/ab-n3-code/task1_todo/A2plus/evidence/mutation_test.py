"""变异测试 - 待办CLI"""
import os, shutil, subprocess, sys, json

SRC = r"<实验根目录>\ab-n3-code\task1_todo\A2plus\todo.py"
TEST_DIR = r"<实验根目录>\ab-n3-code\task1_todo\A2plus\evidence\mutants"

def run(script, *args):
    r = subprocess.run([sys.executable, script] + list(args), capture_output=True, text=True, cwd=os.path.dirname(script))
    return r.stdout + r.stderr, r.returncode

def test_add(script):
    out, _ = run(script, "add", "测试")
    return "已添加" in out

def test_done(script):
    run(script, "add", "任务A")
    run(script, "done", "1")
    out, _ = run(script, "list", "-a")
    return "✓" in out and "任务A" in out

def test_delete(script):
    run(script, "add", "任务B")
    out, _ = run(script, "delete", "1")
    return "已删除" in out

def test_persistence(script):
    run(script, "add", "持久化测试")
    out1, _ = run(script, "list", "-a")
    return "持久化测试" in out1

def make_mutant(name, transform):
    os.makedirs(TEST_DIR, exist_ok=True)
    with open(SRC, encoding="utf-8") as f:
        code = f.read()
    path = os.path.join(TEST_DIR, f"m_{name}.py")
    with open(path, "w", encoding="utf-8") as f:
        f.write(transform(code))
    return path

if __name__ == "__main__":
    mutants = [
        ("原始", None),
        ("去掉done", lambda c: c.replace('t["done"] = True', 't["done"] = False  # M')),
        ("去掉delete", lambda c: c.replace("todos.pop(i)", "pass  # M")),
        ("不持久化", lambda c: c.replace("save_todos(todos)", "# save_todos(todos)  # M")),
    ]
    tests = [("add", test_add), ("done", test_done), ("delete", test_delete), ("持久化", test_persistence)]
    for mname, mfunc in mutants:
        print(f"\n【{mname}】")
        script = SRC if mfunc is None else make_mutant(mname, mfunc)
        # 清理测试数据
        todo_file = os.path.join(os.path.dirname(script), "todos.json")
        if os.path.exists(todo_file):
            os.remove(todo_file)
        results = {}
        for tname, tfunc in tests:
            ok = tfunc(script)
            results[tname] = ok
            print(f"  {'PASS' if ok else 'FAIL'} - {tname}")
        if mfunc:
            killed = not all(results.values())
            print(f"  >>> {'被杀死' if killed else '存活'} (失败项: {[k for k,v in results.items() if not v]})")
