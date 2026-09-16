#!/usr/bin/env python3
"""极简待办 CLI：add / list / done / delete，JSON 持久化，零依赖。"""

import argparse
import json
import os
import sys
from datetime import datetime

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "todos.json")


def load_todos():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def save_todos(todos):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)


def next_id(todos):
    return max((t["id"] for t in todos), default=0) + 1


def cmd_add(args):
    todos = load_todos()
    todo = {
        "id": next_id(todos),
        "text": args.text,
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
        mark = "x" if t["done"] else " "
        print(f"[{mark}] #{t['id']}  {t['text']}")


def cmd_done(args):
    todos = load_todos()
    for t in todos:
        if t["id"] == args.id:
            t["done"] = True
            save_todos(todos)
            print(f"[v] 已完成 #{t['id']}: {t['text']}")
            return
    print(f"[!] 未找到 #{args.id}", file=sys.stderr)
    sys.exit(1)


def cmd_delete(args):
    todos = load_todos()
    new_todos = [t for t in todos if t["id"] != args.id]
    if len(new_todos) == len(todos):
        print(f"[!] 未找到 #{args.id}", file=sys.stderr)
        sys.exit(1)
    save_todos(new_todos)
    print(f"[-] 已删除 #{args.id}")


def main():
    parser = argparse.ArgumentParser(description="极简待办 CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="添加待办")
    p_add.add_argument("text", help="待办内容")
    p_add.set_defaults(func=cmd_add)

    p_list = sub.add_parser("list", help="列出所有待办")
    p_list.set_defaults(func=cmd_list)

    p_done = sub.add_parser("done", help="标记完成")
    p_done.add_argument("id", type=int, help="待办 ID")
    p_done.set_defaults(func=cmd_done)

    p_del = sub.add_parser("delete", help="删除待办")
    p_del.add_argument("id", type=int, help="待办 ID")
    p_del.set_defaults(func=cmd_delete)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
