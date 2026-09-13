"""CLI 层：argparse 接口"""
import argparse
import sys
from .storage import TaskStore


def cmd_add(args, store):
    task = store.add(args.title, args.priority)
    print(f"[Added] #{task.id} [{task.priority}] {task.title}")


def cmd_done(args, store):
    task = store.complete(args.id)
    if task:
        print(f"[Done] #{task.id} {task.title}")
    else:
        print(f"[Error] Task #{args.id} not found", file=sys.stderr)
        sys.exit(1)


def cmd_delete(args, store):
    if store.delete(args.id):
        print(f"[Deleted] #{args.id}")
    else:
        print(f"[Error] Task #{args.id} not found", file=sys.stderr)
        sys.exit(1)


def cmd_list(args, store):
    tasks = store.list(only_pending=args.pending)
    if not tasks:
        print("(no tasks)")
        return
    for t in tasks:
        status = "x" if t.done else " "
        marker = {"high": "!", "normal": "-", "low": "v"}.get(t.priority, "-")
        print(f"  [{status}] #{t.id:3d} {marker} {t.title}")
    total = len(tasks)
    done = sum(1 for t in tasks if t.done)
    print(f"\n  {done}/{total} done")


def build_parser():
    parser = argparse.ArgumentParser(
        prog="todo",
        description="Simple todo CLI - add, complete, delete, list tasks",
    )
    parser.add_argument("--file", default="tasks.json", help="data file path (default: tasks.json)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="add a task")
    p_add.add_argument("title", help="task title")
    p_add.add_argument("-p", "--priority", choices=["low", "normal", "high"], default="normal")
    p_add.set_defaults(func=cmd_add)

    p_done = sub.add_parser("done", help="mark task as done")
    p_done.add_argument("id", type=int)
    p_done.set_defaults(func=cmd_done)

    p_del = sub.add_parser("delete", help="delete a task")
    p_del.add_argument("id", type=int)
    p_del.set_defaults(func=cmd_delete)

    p_list = sub.add_parser("list", help="list tasks")
    p_list.add_argument("--pending", action="store_true", help="show pending only")
    p_list.set_defaults(func=cmd_list)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    store = TaskStore(args.file)
    args.func(args, store)


if __name__ == "__main__":
    main()
