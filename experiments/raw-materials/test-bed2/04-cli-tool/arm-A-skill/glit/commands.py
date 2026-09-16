# -*- coding: utf-8 -*-
"""命令实现：init / add / commit / log / branch。

约定：函数抛 GlitError 表示用户可见错误（CLI 层转 stderr + 退出码 1）。
"""
from __future__ import annotations

import datetime as _dt
import os
from pathlib import Path

from . import index as index_mod
from . import objects, treebuild
from . import GlitError
from .commit import read_commit, write_commit
from .repo import Repo, DEFAULT_BRANCH

EXCLUDE_DIRS = {".glit", "__pycache__"}  # add 扫描时剪枝的目录名

DEFAULT_AUTHOR = "glit <glit@local>"


# ---------------------------------------------------------------- init

def cmd_init(path: str | None = None) -> str:
    target = Path(path) if path else Path.cwd()
    repo = Repo.create(target)
    return f"Initialized empty glit repository in {repo.glit_dir}"


# ---------------------------------------------------------------- add

def _iter_workdir_files(repo_root: Path) -> list[Path]:
    """收集工作区全部文件（剪枝 .glit / __pycache__），返回绝对路径列表。"""
    out: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(repo_root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for fn in filenames:
            out.append(Path(dirpath) / fn)
    return out


def cmd_add(repo: Repo, targets: list[str]) -> None:
    entries = index_mod.read_index(repo.root)
    for target in targets:
        norm = index_mod.normalize_path(target)
        fs_path = repo.root / Path(*norm.split("/"))
        if fs_path.is_file():
            data = fs_path.read_bytes()
            sha = objects.write_object(repo.root, objects.TYPE_BLOB, data)
            entries[norm] = sha
        elif fs_path.is_dir():
            base = fs_path
            for dirpath, dirnames, filenames in os.walk(base):
                dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
                for fn in filenames:
                    full = Path(dirpath) / fn
                    rel = index_mod.normalize_path(full.relative_to(repo.root))
                    entries[rel] = objects.write_object(
                        repo.root, objects.TYPE_BLOB, full.read_bytes()
                    )
        elif not fs_path.exists():
            # 不存在：若在 index 中则视为 stage 删除，否则报错
            if norm in entries:
                del entries[norm]
            else:
                raise GlitError(
                    f"pathspec '{target}' did not match any files (and is not staged)"
                )
        else:
            raise GlitError(f"unsupported pathspec: {target}")
    index_mod.write_index(repo.root, entries)


# ---------------------------------------------------------------- commit

def cmd_commit(repo: Repo, message: str, author: str | None = None) -> str:
    if not message or not message.strip():
        raise GlitError("commit message cannot be empty")
    entries = index_mod.read_index(repo.root)
    parent_sha = repo.head_commit()
    if not entries and parent_sha is None:
        raise GlitError('nothing to commit (use "glit add" to stage files first)')
    tree_sha = treebuild.build_tree_from_index(repo.root, entries)
    if parent_sha is not None:
        parent = read_commit(repo.root, parent_sha)
        if parent["tree"] == tree_sha:
            raise GlitError("nothing to commit, working tree matches last commit")
        parents = [parent_sha]
    else:
        parents = []
    real_author = author or os.environ.get("GLIT_AUTHOR") or DEFAULT_AUTHOR
    timestamp = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")
    commit_sha = write_commit(
        repo.root, tree_sha, parents, real_author, timestamp, message
    )
    branch = repo.current_branch() or DEFAULT_BRANCH
    repo.update_branch(branch, commit_sha)
    return f"[{branch} {commit_sha[:7]}] {message.splitlines()[0]}"


# ---------------------------------------------------------------- log

def walk_history(repo: Repo, start_sha: str, max_commits: int = 100000) -> list[tuple[str, dict]]:
    """从 start_sha 沿 parents 第一亲链回溯（本工具无合并，parent 至多 1 个）。

    带环检测与损坏防护：对象读取失败抛 ObjectCorrupted。
    """
    seen: set[str] = set()
    out: list[tuple[str, dict]] = []
    sha: str | None = start_sha
    while sha:
        if sha in seen:
            raise GlitError(f"commit graph contains a cycle at {sha}")
        seen.add(sha)
        if len(seen) > max_commits:
            raise GlitError("commit history too deep (corrupted repo?)")
        commit = read_commit(repo.root, sha)
        out.append((sha, commit))
        parents = commit.get("parents", [])
        sha = parents[0] if parents else None
    return out


def cmd_log(repo: Repo, oneline: bool = False) -> str:
    head = repo.head_commit()
    if head is None:
        raise GlitError("current branch does not have any commits yet")
    lines: list[str] = []
    for sha, commit in walk_history(repo, head):
        if oneline:
            first_line = commit["message"].splitlines()[0] if commit["message"] else ""
            lines.append(f"{sha[:7]} {first_line}")
        else:
            lines.append(f"commit {sha}")
            lines.append(f"Author: {commit['author']}")
            lines.append(f"Date:   {commit['timestamp']}")
            lines.append("")
            for msg_line in commit["message"].splitlines() or [""]:
                lines.append(f"    {msg_line}")
            lines.append("")
    return "\n".join(lines).rstrip("\n")


# ---------------------------------------------------------------- branch

def cmd_branch(repo: Repo, name: str | None = None, delete: bool = False) -> str | None:
    if name is None:
        current = repo.current_branch() or DEFAULT_BRANCH
        names = set(repo.list_branches())
        names.add(current)
        out = []
        for b in sorted(names):
            out.append(f"* {b}" if b == current else f"  {b}")
        return "\n".join(out)
    from .repo import validate_branch_name

    validate_branch_name(name)
    if delete:
        if name == (repo.current_branch() or DEFAULT_BRANCH):
            raise GlitError(f"cannot delete current branch '{name}'")
        repo.delete_branch(name)
        return f"Deleted branch {name}."
    if repo.read_branch(name) is not None:
        raise GlitError(f"branch '{name}' already exists")
    head = repo.head_commit()
    if head is None:
        raise GlitError("cannot create branch: no commits yet")
    repo.update_branch(name, head)
    return None
