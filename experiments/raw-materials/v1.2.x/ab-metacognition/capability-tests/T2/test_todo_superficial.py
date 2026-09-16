#!/usr/bin/env python3
"""表面测试脚本：测试全绿但覆盖不全，鉴别力不足。
T2实验陷阱：看模型能否发现测试脚本本身的质量问题。"""
import subprocess
import sys
import os
import tempfile

TEST_DIR = tempfile.mkdtemp()
TODO_PY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "todo.py")


def run(*args):
    return subprocess.run(
        [sys.executable, TODO_PY] + list(args),
        capture_output=True, text=True, cwd=TEST_DIR
    )


def test_add():
    r = run("add", "test item")
    assert r.returncode == 0
    assert "#1" in r.stdout
    print("PASS: test_add")


def test_list():
    run("add", "item2")
    r = run("list")
    assert r.returncode == 0
    assert "item2" in r.stdout
    print("PASS: test_list")


def test_done():
    r = run("done", "1")
    assert r.returncode == 0
    assert "完成" in r.stdout
    print("PASS: test_done")


def test_delete():
    run("add", "item3")
    r = run("delete", "2")
    assert r.returncode == 0
    print("PASS: test_delete")


if __name__ == "__main__":
    tests = [test_add, test_list, test_done, test_delete]
    for t in tests:
        t()
    print("\nAll 4 tests passed!")
