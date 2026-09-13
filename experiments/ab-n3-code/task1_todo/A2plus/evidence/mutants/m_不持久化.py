#!/usr/bin/env python3
"""待办事项CLI工具"""
import argparse
import json
import os
import sys
from datetime import datetime

TODO_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "todos.json")

def load_todos():
    if not os.path.exists(TODO_FILE):
        return []
    with open(TODO_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def # save_todos(todos)  # M:
    with open(TODO_FILE, "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)

def add_task(text):
    todos = load_todos()
    task = {
        "id": len(todos) + 1,
        "text": text,
        "done": False,
        "created": datetime.now().isoformat()
    }
    todos.append(task)
    # save_todos(todos)  # M
    print(f"已添加: [{task['id']}] {text}")

def list_tasks(show_all=False):
    todos = load_todos()
    if not todos:
        print("暂无待办事项")
        return
    for t in todos:
        if show_all or not t["done"]:
            status = "✓" if t["done"] else " "
            print(f"[{status}] {t['id']}. {t['text']}")

def done_task(task_id):
    todos = load_todos()
    for t in todos:
        if t["id"] == task_id:
            t["done"] = True
            # save_todos(todos)  # M
            print(f"已完成: [{t['id']}] {t['text']}")
            return
    print(f"错误: 未找到ID为{task_id}的任务", file=sys.stderr)
    sys.exit(1)

def delete_task(task_id):
    todos = load_todos()
    for i, t in enumerate(todos):
        if t["id"] == task_id:
            removed = todos.pop(i)
            # save_todos(todos)  # M
            print(f"已删除: [{removed['id']}] {removed['text']}")
            return
    print(f"错误: 未找到ID为{task_id}的任务", file=sys.stderr)
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="待办事项CLI工具")
    sub = parser.add_subparsers(dest="command", required=True)

    add_p = sub.add_parser("add", help="添加待办")
    add_p.add_argument("text", help="待办内容")

    list_p = sub.add_parser("list", help="列出待办")
    list_p.add_argument("-a", "--all", action="store_true", help="显示全部（含已完成）")

    done_p = sub.add_parser("done", help="标记完成")
    done_p.add_argument("id", type=int, help="任务ID")

    del_p = sub.add_parser("delete", help="删除任务")
    del_p.add_argument("id", type=int, help="任务ID")

    args = parser.parse_args()

    if args.command == "add":
        add_task(args.text)
    elif args.command == "list":
        list_tasks(args.all)
    elif args.command == "done":
        done_task(args.id)
    elif args.command == "delete":
        delete_task(args.id)

if __name__ == "__main__":
    main()
