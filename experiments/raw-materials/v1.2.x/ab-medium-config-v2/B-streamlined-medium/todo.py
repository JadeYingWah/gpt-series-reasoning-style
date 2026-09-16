#!/usr/bin/env python3
"""个人待办事项 CLI 工具 — 零依赖，仅使用 Python 标准库。

功能：
  add     添加任务（支持 --priority high/normal/low）
  done    标记任务完成
  delete  删除任务
  list    列出所有任务（默认按优先级+创建时间排序）

数据持久化：JSON 文件（默认 ~/.todo_cli.json，可通过 --data 指定）
"""

import argparse
import json
import os
import sys
from datetime import datetime

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------
PRIORITY_ORDER = {"high": 0, "normal": 1, "low": 2}
PRIORITY_LABELS = {"high": "高", "normal": "中", "low": "低"}
DEFAULT_DATA_FILE = os.path.join(os.path.expanduser("~"), ".todo_cli.json")


# ---------------------------------------------------------------------------
# 数据层
# ---------------------------------------------------------------------------
def load_tasks(path: str) -> list[dict]:
    """从 JSON 文件加载任务列表；文件不存在时返回空列表。"""
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            print(f"警告：数据文件 {path} 格式异常，将以空列表覆盖。", file=sys.stderr)
            return []
        return data
    except (json.JSONDecodeError, OSError) as exc:
        print(f"错误：无法读取数据文件 {path}：{exc}", file=sys.stderr)
        sys.exit(1)


def save_tasks(path: str, tasks: list[dict]) -> None:
    """将任务列表写入 JSON 文件（原子写入：先写临时文件再替换）。"""
    tmp_path = path + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)
    except OSError as exc:
        print(f"错误：无法写入数据文件 {path}：{exc}", file=sys.stderr)
        sys.exit(1)


def next_task_id(tasks: list[dict]) -> int:
    """生成下一个自增任务 ID。"""
    return max((t["id"] for t in tasks), default=0) + 1


# ---------------------------------------------------------------------------
# 业务逻辑
# ---------------------------------------------------------------------------
def cmd_add(args: argparse.Namespace) -> None:
    tasks = load_tasks(args.data)
    task = {
        "id": next_task_id(tasks),
        "title": args.title,
        "priority": args.priority,
        "done": False,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "completed_at": None,
    }
    tasks.append(task)
    save_tasks(args.data, tasks)
    print(f"已添加任务 #{task['id']}：{task['title']}（优先级：{PRIORITY_LABELS[task['priority']]}）")


def cmd_done(args: argparse.Namespace) -> None:
    tasks = load_tasks(args.data)
    for t in tasks:
        if t["id"] == args.id:
            if t["done"]:
                print(f"任务 #{args.id} 已经是完成状态。")
                return
            t["done"] = True
            t["completed_at"] = datetime.now().isoformat(timespec="seconds")
            save_tasks(args.data, tasks)
            print(f"已标记任务 #{args.id} 为完成：{t['title']}")
            return
    print(f"错误：未找到任务 #{args.id}。", file=sys.stderr)
    sys.exit(1)


def cmd_delete(args: argparse.Namespace) -> None:
    tasks = load_tasks(args.data)
    new_tasks = [t for t in tasks if t["id"] != args.id]
    if len(new_tasks) == len(tasks):
        print(f"错误：未找到任务 #{args.id}。", file=sys.stderr)
        sys.exit(1)
    save_tasks(args.data, new_tasks)
    print(f"已删除任务 #{args.id}。")


def cmd_list(args: argparse.Namespace) -> None:
    tasks = load_tasks(args.data)

    # 过滤
    if args.status == "pending":
        tasks = [t for t in tasks if not t["done"]]
    elif args.status == "done":
        tasks = [t for t in tasks if t["done"]]

    # 排序：未完成优先 → 优先级 → 创建时间
    tasks.sort(key=lambda t: (t["done"], PRIORITY_ORDER.get(t["priority"], 1), t["created_at"]))

    if not tasks:
        print("暂无任务。")
        return

    # 表头
    print(f"{'ID':>4}  {'状态':<4}  {'优先级':<4}  {'创建时间':<20}  标题")
    print("-" * 70)
    for t in tasks:
        status = "✓" if t["done"] else "○"
        pri = PRIORITY_LABELS.get(t["priority"], "?")
        created = t.get("created_at", "-")
        print(f"{t['id']:>4}  {status:<4}  {pri:<4}  {created:<20}  {t['title']}")


# ---------------------------------------------------------------------------
# CLI 解析
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="todo",
        description="个人待办事项 CLI 工具（零依赖）",
    )
    parser.add_argument(
        "--data",
        default=DEFAULT_DATA_FILE,
        help=f"数据文件路径（默认：{DEFAULT_DATA_FILE}）",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # add
    p_add = subparsers.add_parser("add", help="添加任务")
    p_add.add_argument("title", help="任务标题")
    p_add.add_argument(
        "--priority", "-p",
        choices=["high", "normal", "low"],
        default="normal",
        help="优先级（默认：normal）",
    )
    p_add.set_defaults(func=cmd_add)

    # done
    p_done = subparsers.add_parser("done", help="标记任务完成")
    p_done.add_argument("id", type=int, help="任务 ID")
    p_done.set_defaults(func=cmd_done)

    # delete
    p_del = subparsers.add_parser("delete", help="删除任务")
    p_del.add_argument("id", type=int, help="任务 ID")
    p_del.set_defaults(func=cmd_delete)

    # list
    p_list = subparsers.add_parser("list", help="列出任务")
    p_list.add_argument(
        "--status", "-s",
        choices=["all", "pending", "done"],
        default="all",
        help="按状态过滤（默认：all）",
    )
    p_list.set_defaults(func=cmd_list)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
