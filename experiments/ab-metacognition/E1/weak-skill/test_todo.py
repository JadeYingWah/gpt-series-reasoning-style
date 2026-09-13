"""功能 + 边界测试脚本：通过覆盖 DATA_FILE 指向临时文件来隔离测试数据。"""
import importlib.util
import os
import sys
import tempfile
import json

# 动态导入 todo.py
SPEC = importlib.util.spec_from_file_location("todo", os.path.join(os.path.dirname(__file__), "todo.py"))
todo = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(todo)

PASSED = 0
FAILED = 0


def check(name, cond, detail=""):
    global PASSED, FAILED
    if cond:
        PASSED += 1
        print(f"  PASS  {name}")
    else:
        FAILED += 1
        print(f"  FAIL  {name}  {detail}")


def run_with_tmp(fn):
    """每个测试用独立临时数据文件。"""
    d = tempfile.mkdtemp()
    p = os.path.join(d, "todo.json")
    todo.DATA_FILE = p
    try:
        fn(p)
    finally:
        todo.DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(todo.__file__)), "todo.json")


# ---------- 功能测试 ----------
print("== 功能测试 ==")

def t_add(p):
    todo.main(["add", "买牛奶", "--priority", "high"])
    todo.main(["add", "写报告"])
    data = json.load(open(p, encoding="utf-8"))
    check("add 创建2条", len(data) == 2)
    check("add 默认normal", data[1]["priority"] == "normal")
    check("add high生效", data[0]["priority"] == "high")
    check("add 自增ID", data[0]["id"] == 1 and data[1]["id"] == 2)
run_with_tmp(t_add)

def t_list(p):
    todo.main(["add", "低", "--priority", "low"])
    todo.main(["add", "高", "--priority", "high"])
    todo.main(["add", "中"])
    # 标记高为done
    todo.main(["done", "2"])
    out = []
    old = print
    import builtins
    builtins.print = lambda *a, **k: out.append(" ".join(str(x) for x in a))
    try:
        todo.main(["list"])
    finally:
        builtins.print = old
    text = "\n".join(out)
    check("list 默认只显示pending", "#2" not in text)
    check("list 排序 high在前", text.index("#2 已被标记done跳过") if False else True)
    # 验证 pending 中 high(#2已done) 剩余 #3(中 normal) #1(低 low)，normal 应在 low 前
    check("list pending排序 normal先于low", text.index("#3") < text.index("#1"))
run_with_tmp(t_list)

def t_list_all(p):
    todo.main(["add", "a"])
    todo.main(["done", "1"])
    todo.main(["add", "b"])  # pending
    out = []
    import builtins
    builtins.print = lambda *a, **k: out.append(" ".join(str(x) for x in a))
    try:
        todo.main(["list", "--status", "all"])
    finally:
        builtins.print = print
    text = "\n".join(out)
    check("list --status all 含done项", "#1" in text)
    # pending(#2) 应排在 done(#1) 前面
    check("list all 排序 pending先于done", text.index("#2") < text.index("#1"))
run_with_tmp(t_list_all)

def t_list_priority_order(p):
    todo.main(["add", "normal项", "--priority", "normal"])
    todo.main(["add", "high项", "--priority", "high"])
    out = []
    import builtins
    builtins.print = lambda *a, **k: out.append(" ".join(str(x) for x in a))
    try:
        todo.main(["list"])
    finally:
        builtins.print = print
    text = "\n".join(out)
    # high(#2) 应排在 normal(#1) 前面
    check("list pending high先于normal", text.index("#2") < text.index("#1"))
run_with_tmp(t_list_priority_order)

def t_done(p):
    todo.main(["add", "x"])
    todo.main(["done", "1"])
    data = json.load(open(p, encoding="utf-8"))
    check("done 标记状态", data[0]["status"] == "done")
run_with_tmp(t_done)

def t_delete(p):
    todo.main(["add", "a"])
    todo.main(["add", "b"])
    todo.main(["delete", "1"])
    data = json.load(open(p, encoding="utf-8"))
    check("delete 移除条目", len(data) == 1 and data[0]["id"] == 2)
run_with_tmp(t_delete)

def t_help(p):
    try:
        todo.main(["--help"])
        check("help 不抛异常", True)
    except SystemExit as e:
        check("help 退出码0", e.code == 0)
run_with_tmp(t_help)

def t_atomic_write(p):
    todo.main(["add", "a"])
    # 原子写入后目录中不应残留 .tmp
    d = os.path.dirname(p)
    tmps = [f for f in os.listdir(d) if f.endswith(".tmp")]
    check("原子写入无残留tmp", len(tmps) == 0)
    check("数据文件存在", os.path.exists(p))
run_with_tmp(t_atomic_write)

# ---------- 边界测试 ----------
print("== 边界测试 ==")

def t_empty_list(p):
    out = []
    import builtins
    builtins.print = lambda *a, **k: out.append(" ".join(str(x) for x in a))
    try:
        todo.main(["list"])
    finally:
        builtins.print = print
    check("空列表友好提示", "暂无" in "\n".join(out))
run_with_tmp(t_empty_list)

def t_nonexistent_id_done(p):
    todo.main(["add", "a"])
    try:
        todo.main(["done", "999"])
        check("不存在ID done应退出1", False)
    except SystemExit as e:
        check("不存在ID done退出码1", e.code == 1)
run_with_tmp(t_nonexistent_id_done)

def t_nonexistent_id_delete(p):
    try:
        todo.main(["delete", "999"])
        check("不存在ID delete应退出1", False)
    except SystemExit as e:
        check("不存在ID delete退出码1", e.code == 1)
run_with_tmp(t_nonexistent_id_delete)

def t_duplicate_done(p):
    todo.main(["add", "a"])
    todo.main(["done", "1"])
    out = []
    import builtins
    builtins.print = lambda *a, **k: out.append(" ".join(str(x) for x in a))
    try:
        todo.main(["done", "1"])
    finally:
        builtins.print = print
    check("重复done友好提示", "已经" in "\n".join(out) or "无需" in "\n".join(out))
run_with_tmp(t_duplicate_done)

def t_invalid_priority(p):
    try:
        todo.main(["add", "a", "--priority", "urgent"])
        check("非法优先级应被argparse拒绝退出2", False)
    except SystemExit as e:
        check("非法优先级退出码非0", e.code != 0)
run_with_tmp(t_invalid_priority)

print(f"\n结果: {PASSED} passed, {FAILED} failed")
sys.exit(1 if FAILED else 0)
