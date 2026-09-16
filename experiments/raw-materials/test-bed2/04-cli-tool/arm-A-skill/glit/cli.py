# -*- coding: utf-8 -*-
"""CLI 入口：argparse 子命令，统一错误处理与退出码。

退出码：0 成功；1 业务错误或 diff 存在差异；2 参数错误（argparse 默认）。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import GlitError
from . import commands, diff as diff_mod
from .checkout import cmd_checkout
from .repo import Repo


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="glit", description="Git-lite: a minimal content-addressed VCS (educational)."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", help="create an empty glit repository")
    p.add_argument("path", nargs="?", default=None, help="target directory (default: cwd)")

    p = sub.add_parser("add", help="stage files or directories")
    p.add_argument("paths", nargs="+", help="files/directories to stage")

    p = sub.add_parser("commit", help="record staged snapshot")
    p.add_argument("-m", "--message", required=True, help="commit message")
    p.add_argument("--author", default=None, help="override author string")

    p = sub.add_parser("log", help="show commit history")
    p.add_argument("--oneline", action="store_true", help="one line per commit")

    p = sub.add_parser("diff", help="show changes")
    p.add_argument("--staged", action="store_true", help="diff index vs HEAD instead of workdir vs index")

    p = sub.add_parser("checkout", help="switch branches")
    p.add_argument("branch", help="branch name to switch to")

    p = sub.add_parser("branch", help="list or create branches")
    p.add_argument("name", nargs="?", default=None, help="branch to create")
    p.add_argument("-d", "--delete", action="store_true", help="delete a branch")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "init":
            print(commands.cmd_init(args.path))
            return 0

        repo = Repo.find(Path.cwd())

        if args.command == "add":
            commands.cmd_add(repo, args.paths)
            return 0
        if args.command == "commit":
            print(commands.cmd_commit(repo, args.message, args.author))
            return 0
        if args.command == "log":
            out = commands.cmd_log(repo, oneline=args.oneline)
            if out:
                print(out)
            return 0
        if args.command == "diff":
            has_diff, text = diff_mod.run_diff(repo, staged=args.staged)
            if text:
                sys.stdout.write(text if text.endswith("\n") else text + "\n")
            return 1 if has_diff else 0
        if args.command == "checkout":
            print(cmd_checkout(repo, args.branch))
            return 0
        if args.command == "branch":
            out = commands.cmd_branch(repo, args.name, delete=args.delete)
            if out:
                print(out)
            return 0
    except GlitError as e:
        print(f"glit: error: {e}", file=sys.stderr)
        return 1
    except (ValueError, OSError) as e:
        print(f"glit: error: {e}", file=sys.stderr)
        return 1

    parser.error(f"unknown command: {args.command}")  # pragma: no cover
    return 2  # pragma: no cover
