"""Mutation test - todo CLI"""
import os, subprocess, sys

SRC = r"<实验根目录>\ab-n3-code\task1_todo\Decoupled\todo.py"
TEST_DIR = r"<实验根目录>\ab-n3-code\task1_todo\Decoupled\evidence\mutants"

def run(script, *args):
    r = subprocess.run([sys.executable, script] + list(args), capture_output=True, text=True, cwd=os.path.dirname(script))
    return r.stdout + r.stderr, r.returncode

def test_add(s):
    out, _ = run(s, "add", "test")
    return "Added" in out

def test_done(s):
    run(s, "add", "taskA")
    run(s, "done", "1")
    out, _ = run(s, "list", "-a")
    return "[x]" in out and "taskA" in out

def test_delete(s):
    run(s, "add", "taskB")
    out, _ = run(s, "delete", "1")
    return "Deleted" in out

def test_persist(s):
    run(s, "add", "persist_test")
    out, _ = run(s, "list", "-a")
    return "persist_test" in out

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
        ("original", None),
        ("no_done", lambda c: c.replace('x["done"] = True', 'x["done"] = False')),
        ("no_delete", lambda c: c.replace("t.pop(i)", "pass")),
        ("no_persist", lambda c: c.replace("save(t)", "# save(t)")),
    ]
    tests = [("add", test_add), ("done", test_done), ("delete", test_delete), ("persist", test_persist)]
    for mname, mfunc in mutants:
        print(f"\n[{mname}]")
        script = SRC if mfunc is None else make_mutant(mname, mfunc)
        tf = os.path.join(os.path.dirname(script), "todos.json")
        if os.path.exists(tf): os.remove(tf)
        results = {}
        for tname, tfunc in tests:
            ok = tfunc(script)
            results[tname] = ok
            print(f"  {'PASS' if ok else 'FAIL'} - {tname}")
        if mfunc:
            killed = not all(results.values())
            print(f"  >>> {'KILLED' if killed else 'SURVIVED'}")
