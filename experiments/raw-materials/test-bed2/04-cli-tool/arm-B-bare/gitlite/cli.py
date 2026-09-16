"""命令行入口：argparse 定义 + 统一错误处理。

用法:
    python -m gitlite <command> [args]
"""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from . import commands
from .index import IndexError as GitLiteIndexError
from .objects import ObjectError
from .repository import Repository, RepositoryError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gitlite",
        description="GitLite —— 一个内容寻址的迷你版本控制系统（Git 的教学级实现）",
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")
    sub.required = True

    sp = sub.add_parser("init", help="创建一个空的 GitLite 仓库")
    sp.add_argument("directory", nargs="?", default=".", help="仓库位置（默认当前目录）")

    sp = sub.add_parser("add", help="把文件或目录加入暂存区（已跟踪文件的删除也会被暂存）")
    sp.add_argument("paths", nargs="+", metavar="<path>")

    sp = sub.add_parser("commit", help="把暂存区记录为一次提交")
    sp.add_argument("-m", "--message", required=True, help="提交说明")

    sp = sub.add_parser("log", help="沿 parent 链查看提交历史")
    sp.add_argument("target", nargs="?", default=None, help="分支名或提交哈希（默认 HEAD）")

    sp = sub.add_parser("diff", help="查看差异（默认: 工作区 vs 暂存区）")
    sp.add_argument(
        "--staged", action="store_true", help="比较暂存区与 HEAD（等价 git diff --cached）"
    )

    sp = sub.add_parser(
        "checkout", help="切换分支 / 检出提交（分离 HEAD）/ 恢复工作区文件"
    )
    sp.add_argument(
        "args", nargs="+", metavar="<branch|commit|path>",
        help="分支名、提交哈希，或 '--' 后跟要恢复的文件路径",
    )

    sp = sub.add_parser("branch", help="列出 / 创建 / 删除分支")
    sp.add_argument("name", nargs="?", default=None, help="要创建或删除的分支名")
    group = sp.add_mutually_exclusive_group()
    group.add_argument("-d", dest="delete", action="store_const", const="-d",
                       help="删除分支（要求已合并）")
    group.add_argument("-D", dest="delete", action="store_const", const="-D",
                       help="强制删除分支")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "init":
            return commands.cmd_init(args.directory)

        repo = Repository.find()
        if args.command == "add":
            return commands.cmd_add(repo, args.paths)
        if args.command == "commit":
            return commands.cmd_commit(repo, args.message)
        if args.command == "log":
            return commands.cmd_log(repo, args.target)
        if args.command == "diff":
            return commands.cmd_diff(repo, staged=args.staged)
        if args.command == "checkout":
            return commands.cmd_checkout(repo, args.args)
        if args.command == "branch":
            return commands.cmd_branch(repo, name=args.name, delete=args.delete)
        raise RepositoryError(f"unknown command: {args.command}")
    except (RepositoryError, ObjectError, GitLiteIndexError) as exc:
        print(f"gitlite: error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
