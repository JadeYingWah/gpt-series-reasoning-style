#!/usr/bin/env python3
"""待办事项 CLI 工具"""
import argparse
import json
import os
import sys
from datetime import datetime

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "todos.json")


def load_todos():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_todos(todos):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)


def next_id(todos):
    return max([t["id"] for t in todos], default=0) + 1


def cmd_add(args):
    todos = load_todos()
    todo = {
        "id": next_id(todos),
        "content": args.content,
        "priority": args.priority,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
    }
    todos.append(todo)
    save_todos(todos)
    print(f"已添加 #{todo['id']}: {todo['content']} (优先级: {todo['priority']})")


def cmd_list(args):
    todos = load_todos()
    if args.status == "pending":
        todos = [t for t in todos if t["status"] == "pending"]
    elif args.status == "done":
        todos = [t for t in todos if t["status"] == "done"]

    if not todos:
        print("（暂无待办事项）")
        return

    priority_order = {"high": 0, "normal": 1, "low": 2}
    todos.sort(key=lambda t: (0 if t["status"] == "pending" else 1, priority_order.get(t["priority"], 1), t["created_at"]))

    for t in todos:
        mark = "[x]" if t["status"] == "done" else "[ ]"
        print(f"{mark} #{t['id']} [{t['priority']}] {t['content']}  (创建: {t['created_at']})")


def cmd_done(args):
    todos = load_todos()
    for t in todos:
        if t["id"] == args.id:
            if t["status"] == "done":
                print(f"#{args.id} 已经是完成状态")
            else:
                t["status"] = "done"
                save_todos(todos)
                print(f"已完成 #{args.id}: {t['content']}")
            return
    print(f"错误: 不存在 ID 为 {args.id} 的事项", file=sys.stderr)
    sys.exit(1)


def cmd_delete(args):
    todos = load_todos()
    for i, t in enumerate(todos):
        if t["id"] == args.id:
            del todos[i]
            save_todos(todos)
            print(f"已删除 #{args.id}: {t['content']}")
            return
    print(f"错误: 不存在 ID 为 {args.id} 的事项", file=sys.stderr)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="待办事项 CLI 工具")
    subparsers = parser.add_subparsers(dest="command")

    add_parser = subparsers.add_parser("add", help="添加待办事项")
    add_parser.add_argument("content", help="待办内容")
    add_parser.add_argument("--priority", choices=["high", "normal", "low"], default="normal")
    add_parser.set_defaults(func=cmd_add)

    list_parser = subparsers.add_parser("list", help="列出待办事项")
    list_parser.add_argument("--status", choices=["pending", "done", "all"], default="pending")
    list_parser.set_defaults(func=cmd_list)

    done_parser = subparsers.add_parser("done", help="标记为已完成")
    done_parser.add_argument("id", type=int)
    done_parser.set_defaults(func=cmd_done)

    delete_parser = subparsers.add_parser("delete", help="删除事项")
    delete_parser.add_argument("id", type=int)
    delete_parser.set_defaults(func=cmd_delete)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()
