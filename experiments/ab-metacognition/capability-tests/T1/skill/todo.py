#!/usr/bin/env python3
"""极简待办 CLI — add / list / done / delete，JSON 持久化，零依赖。

用法:
    python todo.py add "买牛奶"
    python todo.py list
    python todo.py done 1
    python todo.py delete 1
"""

import argparse
import json
import os
import sys
from datetime import datetime

# 数据文件与脚本同目录，避免 CWD 漂移导致数据丢失
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "todos.json")


# ── 持久化 ──────────────────────────────────────────────

def load_todos() -> list:
    """读取待办列表；文件不存在或损坏时返回空列表（容错，不崩溃）。"""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_todos(todos: list) -> None:
    """原子写入：先写临时文件再替换，防止中途崩溃导致数据损坏。"""
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DATA_FILE)


def next_id(todos: list) -> int:
    return max((t["id"] for t in todos), default=0) + 1


def find_todo(todos: list, todo_id: int):
    for t in todos:
        if t["id"] == todo_id:
            return t
    return None


# ── 命令实现 ────────────────────────────────────────────

def cmd_add(args):
    todos = load_todos()
    text = args.text.strip()
    if not text:
        print("[!] 待办内容不能为空", file=sys.stderr)
        sys.exit(1)
    todo = {
        "id": next_id(todos),
        "text": text,
        "done": False,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    todos.append(todo)
    save_todos(todos)
    print(f"[+] 已添加 #{todo['id']}: {todo['text']}")


def cmd_list(args):
    todos = load_todos()
    if not todos:
        print("（暂无待办）")
        return
    for t in todos:
        mark = "x" if t.get("done") else " "
        print(f"[{mark}] #{t['id']}  {t['text']}")


def cmd_done(args):
    todos = load_todos()
    t = find_todo(todos, args.id)
    if t is None:
        print(f"[!] 未找到 #{args.id}", file=sys.stderr)
        sys.exit(1)
    if t.get("done"):
        print(f"[=] #{t['id']} 已经是完成状态")
        return
    t["done"] = True
    save_todos(todos)
    print(f"[v] 已完成 #{t['id']}: {t['text']}")


def cmd_delete(args):
    todos = load_todos()
    before = len(todos)
    todos = [t for t in todos if t["id"] != args.id]
    if len(todos) == before:
        print(f"[!] 未找到 #{args.id}", file=sys.stderr)
        sys.exit(1)
    save_todos(todos)
    print(f"[-] 已删除 #{args.id}")


# ── CLI 入口 ────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="极简待办 CLI（零依赖）")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="添加待办")
    p_add.add_argument("text", help="待办内容")
    p_add.set_defaults(func=cmd_add)

    p_list = sub.add_parser("list", help="列出所有待办")
    p_list.set_defaults(func=cmd_list)

    p_done = sub.add_parser("done", help="标记待办为已完成")
    p_done.add_argument("id", type=int, help="待办 ID")
    p_done.set_defaults(func=cmd_done)

    p_del = sub.add_parser("delete", help="删除待办")
    p_del.add_argument("id", type=int, help="待办 ID")
    p_del.set_defaults(func=cmd_delete)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
