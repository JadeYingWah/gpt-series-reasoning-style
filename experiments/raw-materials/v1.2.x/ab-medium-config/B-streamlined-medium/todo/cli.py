"""Todo CLI - 命令行接口"""
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
    done = sum(1 for t in tasks if t.done)
    print(f"\n  {done}/{len(tasks)} done")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="todo", description="Simple todo CLI")
    parser.add_argument("--file", default="tasks.json")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("add"); p.add_argument("title"); p.add_argument("-p", "--priority", choices=["low","normal","high"], default="normal"); p.set_defaults(func=cmd_add)
    p = sub.add_parser("done"); p.add_argument("id", type=int); p.set_defaults(func=cmd_done)
    p = sub.add_parser("delete"); p.add_argument("id", type=int); p.set_defaults(func=cmd_delete)
    p = sub.add_parser("list"); p.add_argument("--pending", action="store_true"); p.set_defaults(func=cmd_list)

    args = parser.parse_args(argv)
    args.func(args, TaskStore(args.file))


if __name__ == "__main__":
    main()
