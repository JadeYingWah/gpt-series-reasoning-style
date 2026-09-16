#!/usr/bin/env python3
"""单文件命令行待办事项管理工具（零外部依赖，仅标准库）。

用法:
    python todo.py add <内容> [--priority high|normal|low]
    python todo.py list [--status pending|done|all]
    python todo.py done <id>
    python todo.py delete <id>
    python todo.py --help
"""

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime

# 数据文件默认放在脚本同目录，避免硬编码绝对路径
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "todo.json")

# 优先级权重，用于排序：high > normal > low
PRIORITY_ORDER = {"high": 0, "normal": 1, "low": 2}


def load_todos(path=None):
    """从 JSON 文件加载待办列表；文件不存在时返回空列表。"""
    if path is None:
        path = DATA_FILE
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_todos(todos, path=None):
    """原子写入：先写临时文件，再 os.replace 重命名，避免中途崩溃损坏数据。"""
    if path is None:
        path = DATA_FILE
    dir_name = os.path.dirname(path) or "."
    fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp", prefix="todo_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(todos, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)
    except Exception:
        # 写入失败时清理临时文件
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def next_id(todos):
    """生成下一个 ID：取现有最大 ID + 1，空列表从 1 开始。"""
    if not todos:
        return 1
    return max(t["id"] for t in todos) + 1


def cmd_add(args):
    """添加待办事项。"""
    todos = load_todos()
    item = {
        "id": next_id(todos),
        "content": args.content,
        "priority": args.priority,
        "status": "pending",
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    todos.append(item)
    save_todos(todos)
    print(f"已添加 #{item['id']}: {item['content']} (优先级: {item['priority']})")


def cmd_list(args):
    """列出待办事项，按 未完成优先 → 优先级 → 创建时间 排序。"""
    todos = load_todos()
    status = args.status

    # 按状态过滤
    if status == "pending":
        filtered = [t for t in todos if t["status"] == "pending"]
    elif status == "done":
        filtered = [t for t in todos if t["status"] == "done"]
    else:  # all
        filtered = todos

    # 排序：未完成优先(status pending=0, done=1) → 优先级权重 → 创建时间
    filtered.sort(key=lambda t: (
        0 if t["status"] == "pending" else 1,
        PRIORITY_ORDER.get(t["priority"], 99),
        t.get("created_at", ""),
    ))

    if not filtered:
        print("（暂无待办事项）")
        return

    for t in filtered:
        mark = " " if t["status"] == "pending" else "x"
        print(f"[{mark}] #{t['id']} [{t['priority']}] {t['content']}  (创建: {t['created_at']})")


def cmd_done(args):
    """标记指定 ID 为已完成；ID 不存在退出码 1；重复标记给出友好提示。"""
    todos = load_todos()
    for t in todos:
        if t["id"] == args.id:
            if t["status"] == "done":
                print(f"#{t['id']} 已经是已完成状态，无需重复标记。")
                return
            t["status"] = "done"
            save_todos(todos)
            print(f"已完成 #{t['id']}: {t['content']}")
            return
    print(f"错误：ID {args.id} 不存在。", file=sys.stderr)
    sys.exit(1)


def cmd_delete(args):
    """删除指定 ID；ID 不存在退出码 1。"""
    todos = load_todos()
    for i, t in enumerate(todos):
        if t["id"] == args.id:
            del todos[i]
            save_todos(todos)
            print(f"已删除 #{t['id']}: {t['content']}")
            return
    print(f"错误：ID {args.id} 不存在。", file=sys.stderr)
    sys.exit(1)


def build_parser():
    """构建 argparse 解析器，含子命令与 --help。"""
    parser = argparse.ArgumentParser(
        description="单文件命令行待办事项管理工具（零外部依赖）"
    )
    subparsers = parser.add_subparsers(dest="command", help="可用子命令")

    # add
    p_add = subparsers.add_parser("add", help="添加待办事项")
    p_add.add_argument("content", help="待办内容")
    p_add.add_argument(
        "--priority",
        choices=["high", "normal", "low"],
        default="normal",
        help="优先级（默认 normal）",
    )
    p_add.set_defaults(func=cmd_add)

    # list
    p_list = subparsers.add_parser("list", help="列出待办事项")
    p_list.add_argument(
        "--status",
        choices=["pending", "done", "all"],
        default="pending",
        help="过滤状态（默认 pending）",
    )
    p_list.set_defaults(func=cmd_list)

    # done
    p_done = subparsers.add_parser("done", help="标记为已完成")
    p_done.add_argument("id", type=int, help="事项 ID")
    p_done.set_defaults(func=cmd_done)

    # delete
    p_delete = subparsers.add_parser("delete", help="删除事项")
    p_delete.add_argument("id", type=int, help="事项 ID")
    p_delete.set_defaults(func=cmd_delete)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()
