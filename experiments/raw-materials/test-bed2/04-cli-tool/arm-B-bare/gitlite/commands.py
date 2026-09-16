"""命令实现层：init / add / commit / log / diff / checkout / branch。

每个 cmd_* 返回进程退出码（0 成功；1 业务性失败，如 nothing to commit）。
仓库/对象/参数类错误通过异常抛出，由 cli.main 统一捕获处理。
"""

from __future__ import annotations

import datetime
import os
import re
import sys
import time
from typing import Dict, List, Optional, Tuple

from .diff import _split_lines, unified_diff
from .objects import (
    BLOB,
    COMMIT,
    MODE_FILE,
    ObjectError,
    blob_oid,
    format_commit_payload,
    parse_commit,
)
from .repository import (
    REPO_DIRNAME,
    Repository,
    RepositoryError,
)

_AUTHOR_RE = re.compile(r"^(.*) <([^>]*)> (\d+) ([+-]\d{4})$")


# ----------------------------------------------------------------------
# 小工具
# ----------------------------------------------------------------------

def _local_tz_string(ts: int) -> str:
    """本地时区的 "+0800" 风格表示。"""
    off = -time.timezone if time.localtime(ts).tm_isdst == 0 else -time.altzone
    sign = "+" if off >= 0 else "-"
    off = abs(off)
    return f"{sign}{off // 3600:02d}{(off % 3600) // 60:02d}"


def _author_string() -> str:
    """从环境变量取作者身份，缺省 GitLite User。返回 "Name <email> ts tz" 格式。"""
    name = os.environ.get("GITLITE_AUTHOR_NAME", "GitLite User")
    email = os.environ.get("GITLITE_AUTHOR_EMAIL", "gitlite@example.com")
    ts = int(time.time())
    tz = _local_tz_string(ts)
    return f"{name} <{email}> {ts} {tz}"


def split_author(author: str) -> Tuple[str, Optional[int], str]:
    """"Name <email> ts tz" -> ("Name <email>", ts, tz)。"""
    m = _AUTHOR_RE.match(author.strip())
    if not m:
        return author.strip(), None, ""
    return f"{m.group(1).strip()} <{m.group(2)}>", int(m.group(3)), m.group(4)


def _first_line(message: str) -> str:
    return message.strip().splitlines()[0] if message.strip() else ""


def _to_relpath(repo: Repository, raw: str) -> str:
    """把命令行路径规范化为仓库根的 POSIX 相对路径，越界/非法则报错。"""
    p = os.path.abspath(raw)
    root = repo.root
    if not (p == root or p.startswith(root + os.sep)):
        raise RepositoryError(f"path '{raw}' is outside the repository")
    rel = os.path.relpath(p, root).replace(os.sep, "/")
    if rel == REPO_DIRNAME or rel.startswith(REPO_DIRNAME + "/"):
        raise RepositoryError(f"cannot operate on files inside {REPO_DIRNAME}")
    return rel


def _collect_dir_files(repo: Repository, abs_dir: str) -> List[str]:
    """递归收集目录下的全部文件（POSIX 相对路径），跳过 .gitlite。"""
    out: List[str] = []
    root = repo.root
    for dirpath, dirnames, filenames in os.walk(abs_dir):
        if os.path.abspath(dirpath) == root:
            dirnames[:] = [d for d in dirnames if d != REPO_DIRNAME]
        for fn in filenames:
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            out.append(rel)
    return sorted(out)


def _stage_file(repo: Repository, index, rel: str) -> None:
    full = repo.worktree_path(rel)
    with open(full, "rb") as f:
        content = f.read()
    oid = repo.objects.store(BLOB, content)
    index.add(rel, oid)


# ----------------------------------------------------------------------
# init
# ----------------------------------------------------------------------

def cmd_init(directory: str = ".") -> int:
    root = os.path.abspath(directory)
    existed = os.path.isdir(os.path.join(root, REPO_DIRNAME))
    repo = Repository.init(root)
    verb = "reinitialized existing" if existed else "initialized empty"
    print(f"{verb} gitlite repository in {repo.lite_dir}")
    return 0


# ----------------------------------------------------------------------
# add
# ----------------------------------------------------------------------

def cmd_add(repo: Repository, paths: List[str]) -> int:
    index = repo.load_index()
    for raw in paths:
        p = os.path.abspath(raw)
        root = repo.root
        if not (p == root or p.startswith(root + os.sep)):
            raise RepositoryError(f"path '{raw}' is outside the repository")
        if os.path.isdir(p):
            rels = _collect_dir_files(repo, p)
            if not rels:
                continue
            for rel in rels:
                _stage_file(repo, index, rel)
        elif os.path.isfile(p):
            rel = os.path.relpath(p, root).replace(os.sep, "/")
            if rel == REPO_DIRNAME or rel.startswith(REPO_DIRNAME + "/"):
                raise RepositoryError(f"cannot operate on files inside {REPO_DIRNAME}")
            _stage_file(repo, index, rel)
        else:
            # 不存在: 已跟踪的路径视为"暂存一次删除"，否则报错
            try:
                rel = _to_relpath(repo, raw)
            except RepositoryError:
                raise
            if index.has(rel):
                index.remove(rel)
            else:
                raise RepositoryError(
                    f"pathspec '{raw}' did not match any files"
                )
    index.save()
    return 0


# ----------------------------------------------------------------------
# commit
# ----------------------------------------------------------------------

def cmd_commit(repo: Repository, message: str) -> int:
    if not message or not message.strip():
        raise RepositoryError("empty commit message (use -m \"<message>\")")
    index = repo.load_index()
    head_oid = repo.head_commit_oid()
    head_tree_oid = repo.commit_tree_oid(head_oid) if head_oid else None

    if head_oid is None and not index.entries:
        print('nothing to commit (stage files with "gitlite add" first)')
        return 1

    tree_oid = repo.build_tree_from_entries(
        {p: (e["oid"], e["mode"]) for p, e in index.entries.items()}
    )
    if head_tree_oid == tree_oid:
        print("nothing to commit, working tree clean")
        return 1

    author = _author_string()
    parents = [head_oid] if head_oid else []
    payload = format_commit_payload(tree_oid, parents, author, author, message)
    commit_oid = repo.objects.store(COMMIT, payload)

    if repo.head_is_detached():
        repo._write_lite_file("HEAD", commit_oid + "\n")
        branch_label = "detached HEAD"
        print(
            "warning: you are in detached HEAD state; "
            "this commit does not belong to any branch"
        )
    else:
        repo.write_ref(repo.head_target() or "", commit_oid)
        branch_label = repo.current_branch() or "?"
    print(f"[{branch_label} {commit_oid[:8]}] {_first_line(message)}")
    return 0


# ----------------------------------------------------------------------
# log
# ----------------------------------------------------------------------

def cmd_log(repo: Repository, target: Optional[str] = None) -> int:
    if target is not None:
        start = repo.resolve_revision(target)
        if start is None:
            raise RepositoryError(f"unknown revision: {target}")
    else:
        start = repo.head_commit_oid()
        if start is None:
            raise RepositoryError(
                "your current branch does not have any commits yet"
            )

    seen = set()
    oid = start
    first = True
    while oid:
        if oid in seen:
            break
        seen.add(oid)
        _t, payload = repo.objects.read(oid)
        info = parse_commit(payload)
        if not first:
            print()
        first = False
        ident, ts, tz = split_author(info["author"])
        print(f"commit {oid}")
        if ts is not None:
            dt = datetime.datetime.fromtimestamp(
                ts, tz=datetime.datetime.now().astimezone().tzinfo
            )
            print(f"Author: {ident}")
            print(f"Date:   {dt.strftime('%Y-%m-%d %H:%M:%S')} {tz}")
        else:
            print(f"Author: {ident}")
        print()
        for line in info["message"].rstrip("\n").splitlines():
            print(f"    {line}")
        oid = info["parents"][0] if info["parents"] else None
    return 0


# ----------------------------------------------------------------------
# diff
# ----------------------------------------------------------------------

def _diff_block(
    repo: Repository,
    path: str,
    old: Tuple[Optional[str], bytes],
    new: Tuple[Optional[str], bytes],
    mode: str,
) -> List[str]:
    """单个文件的 diff 输出块。old/new: (oid 可为 None, 内容字节)。"""
    old_oid, old_bytes = old
    new_oid, new_bytes = new
    if old_bytes == new_bytes:
        return []

    header = [f"diff --gitlite a/{path} b/{path}"]
    if old_oid and new_oid:
        header.append(f"index {old_oid[:8]}..{new_oid[:8]} {mode}")
    elif old_oid:
        header.append(f"index {old_oid[:8]}..{'0' * 8} {mode}")
    elif new_oid:
        header.append(f"index {'0' * 8}..{new_oid[:8]} {mode}")

    if b"\x00" in old_bytes or b"\x00" in new_bytes:
        return header + ["Binary files a/%s and b/%s differ" % (path, path)]

    from_label = f"a/{path}" if old_oid else "/dev/null"
    to_label = f"b/{path}" if new_oid else "/dev/null"
    body = unified_diff(
        _split_lines(old_bytes.decode("utf-8", "replace")),
        _split_lines(new_bytes.decode("utf-8", "replace")),
        from_label,
        to_label,
    )
    return header + body


def cmd_diff(repo: Repository, staged: bool = False) -> int:
    index = repo.load_index()
    blocks: List[str] = []

    if staged:
        head_oid = repo.head_commit_oid()
        head_files = repo.commit_tree_files(head_oid) if head_oid else {}
        all_paths = sorted(set(head_files) | set(index.entries))
        for path in all_paths:
            old_entry = head_files.get(path)          # (oid, mode) 或 None
            new_entry = index.entries.get(path)       # {"oid","mode"} 或 None
            if old_entry:
                old = (old_entry[0], repo.objects.read(old_entry[0])[1])
            else:
                old = (None, b"")
            if new_entry:
                new = (new_entry["oid"], repo.objects.read(new_entry["oid"])[1])
            else:
                new = (None, b"")
            if new_entry:
                mode = new_entry["mode"]
            elif old_entry:
                mode = old_entry[1]
            else:
                mode = MODE_FILE
            blocks.extend(_diff_block(repo, path, old, new, mode))
    else:
        # 工作区 vs 暂存区（不显示 untracked 文件，与 git 语义一致）
        for path in index.paths():
            entry = index.entries[path]
            old_oid = entry["oid"]
            _t, old_bytes = repo.objects.read(old_oid)
            wt = repo.read_worktree_file(path)
            if wt is None:
                # 已跟踪文件在工作区被删除
                new = (None, b"")
            else:
                # 工作区内容即时计算 oid（不落盘），与 git diff 的 index 行为一致
                new = (blob_oid(wt), wt)
            blocks.extend(_diff_block(repo, path, (old_oid, old_bytes), new, entry["mode"]))

    if not blocks:
        return 0
    print("\n".join(blocks))
    return 1


# ----------------------------------------------------------------------
# checkout
# ----------------------------------------------------------------------

def cmd_checkout(repo: Repository, args: List[str]) -> int:
    if "--" in args:
        i = args.index("--")
        names, paths = args[:i], args[i + 1:]
        if names:
            raise RepositoryError("usage: gitlite checkout -- <path> [<path>...]")
        if not paths:
            raise RepositoryError("missing path after '--'")
        return _restore_files(repo, paths)

    if len(args) != 1:
        raise RepositoryError(
            "usage: gitlite checkout <branch|commit|path>  or  "
            "gitlite checkout -- <path> [<path>...]"
        )
    name = args[0]

    branch_oid = repo.read_ref(f"refs/heads/{name}")
    if branch_oid:
        return _switch_branch(repo, name, branch_oid)

    oid = repo.resolve_revision(name)
    if oid:
        return _checkout_detached(repo, oid)

    return _restore_files(repo, [name])


def _switch_branch(repo: Repository, branch: str, oid: str) -> int:
    repo.checkout_sync(repo.commit_tree_files(oid))
    repo._write_lite_file("HEAD", f"ref: refs/heads/{branch}\n")
    print(f"switched to branch '{branch}'")
    return 0


def _checkout_detached(repo: Repository, oid: str) -> int:
    _t, payload = repo.objects.read(oid)
    msg = _first_line(parse_commit(payload)["message"])
    repo.checkout_sync(repo.commit_tree_files(oid))
    repo._write_lite_file("HEAD", oid + "\n")
    print(f"note: switching to '{oid[:8]}' (detached HEAD)")
    print(f"HEAD is now at {oid[:8]} {msg}")
    return 0


def _restore_files(repo: Repository, paths: List[str]) -> int:
    index = repo.load_index()
    for raw in paths:
        rel = _to_relpath(repo, raw)
        entry = index.get(rel)
        if entry is None:
            raise RepositoryError(
                f"pathspec '{raw}' did not match any file(s) known to gitlite"
            )
        _t, payload = repo.objects.read(entry["oid"])
        repo.write_worktree_file(rel, payload)
    return 0


# ----------------------------------------------------------------------
# branch
# ----------------------------------------------------------------------

def cmd_branch(repo: Repository, name: Optional[str] = None, delete: Optional[str] = None) -> int:
    if name is None and delete is None:
        current = repo.current_branch()
        for branch in repo.branch_names():
            mark = "*" if branch == current else " "
            print(f"{mark} {branch}")
        return 0

    if delete:
        return _delete_branch(repo, name, delete)

    return _create_branch(repo, name)


def _create_branch(repo: Repository, name: Optional[str]) -> int:
    if not name:
        raise RepositoryError("branch name required")
    if "/" in name and (name.startswith("/") or name.endswith("/") or "//" in name):
        raise RepositoryError(f"invalid branch name: '{name}'")
    head_oid = repo.head_commit_oid()
    if head_oid is None:
        raise RepositoryError(
            "not a valid object name: 'HEAD' (a branch must point at a commit)"
        )
    ref = f"refs/heads/{name}"
    if repo.read_ref(ref):
        raise RepositoryError(f"a branch named '{name}' already exists")
    repo.write_ref(ref, head_oid)
    return 0


def _delete_branch(repo: Repository, name: Optional[str], mode: str) -> int:
    if not name:
        raise RepositoryError("branch name required")
    ref = f"refs/heads/{name}"
    oid = repo.read_ref(ref)
    if oid is None:
        raise RepositoryError(f"branch '{name}' not found")
    if name == repo.current_branch():
        raise RepositoryError(f"cannot delete current branch '{name}'")
    if mode == "-d":
        head_oid = repo.head_commit_oid()
        if head_oid is None or not repo.is_ancestor(oid, head_oid):
            raise RepositoryError(
                f"the branch '{name}' is not fully merged; "
                "use -D to force deletion"
            )
    repo.delete_ref(ref)
    print(f"deleted branch {name} (was {oid[:8]})")
    return 0
