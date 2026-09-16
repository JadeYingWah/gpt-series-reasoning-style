#!/usr/bin/env python3
"""功能+边界测试"""
import subprocess
import sys
import os
import json
import tempfile

TEST_DIR = tempfile.mkdtemp()
DATA_FILE = os.path.join(TEST_DIR, "todos.json")
TODO_PY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "todo.py")


def run(*args):
    env = os.environ.copy()
    result = subprocess.run(
        [sys.executable, TODO_PY] + list(args),
        capture_output=True, text=True, cwd=TEST_DIR, env=env
    )
    return result


def test_add_and_list():
    r = run("add", "任务1", "--priority", "high")
    assert r.returncode == 0, f"add failed: {r.stderr}"
    assert "#1" in r.stdout

    r = run("add", "任务2")
    assert r.returncode == 0
    assert "#2" in r.stdout
    assert "normal" in r.stdout

    r = run("list")
    assert r.returncode == 0
    assert "任务1" in r.stdout
    assert "任务2" in r.stdout
    # high优先级排在前面
    assert r.stdout.index("任务1") < r.stdout.index("任务2")


def test_done():
    r = run("done", "1")
    assert r.returncode == 0
    assert "已完成" in r.stdout

    r = run("list")
    assert "任务1" not in r.stdout  # pending列表不包含已完成

    r = run("list", "--status", "all")
    assert "任务1" in r.stdout
    assert "[x]" in r.stdout


def test_duplicate_done():
    r = run("done", "1")
    assert r.returncode == 0
    assert "已经是完成状态" in r.stdout


def test_delete():
    r = run("delete", "2")
    assert r.returncode == 0
    assert "已删除" in r.stdout

    r = run("list")
    assert "任务2" not in r.stdout


def test_nonexistent_id():
    r = run("done", "999")
    assert r.returncode == 1
    assert "不存在" in r.stderr

    r = run("delete", "999")
    assert r.returncode == 1


def test_empty_list():
    # 先清空
    if os.path.exists(DATA_FILE):
        os.unlink(DATA_FILE)
    r = run("list")
    assert r.returncode == 0
    assert "暂无" in r.stdout


def test_invalid_priority():
    r = run("add", "test", "--priority", "urgent")
    assert r.returncode != 0  # argparse拒绝


def test_atomic_write():
    run("add", "原子测试")
    # 检查没有.tmp残留
    tmp_files = [f for f in os.listdir(TEST_DIR) if f.endswith(".tmp")]
    assert len(tmp_files) == 0, f"tmp文件残留: {tmp_files}"


def test_help():
    r = run("--help")
    assert r.returncode == 0
    assert "待办" in r.stdout


if __name__ == "__main__":
    tests = [
        test_add_and_list,
        test_done,
        test_duplicate_done,
        test_delete,
        test_nonexistent_id,
        test_empty_list,
        test_invalid_priority,
        test_atomic_write,
        test_help,
    ]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS: {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL: {t.__name__}: {e}")
            failed += 1
    print(f"\n{passed}/{passed+failed} passed")
    sys.exit(1 if failed else 0)
