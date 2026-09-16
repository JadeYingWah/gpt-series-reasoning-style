# -*- coding: utf-8 -*-
"""checkout：分支切换（快照式，保守安全策略）。

安全策略（有意比 git 保守，见 README）：
  1. 当前 HEAD 快照中的任一文件在工作区被修改/删除 -> 拒绝切换
  2. 目标分支将覆盖一个当前 HEAD 不跟踪的工作区文件（未跟踪冲突）-> 拒绝切换
切换动作：
  - 删除旧快照独有文件（并尝试清理空目录）
  - 写入目标快照全部文件
  - index 重置为目标快照；HEAD 指向目标分支
"""
from __future__ import annotations

from pathlib import Path

from . import index as index_mod
from . import objects, treebuild
from . import GlitError
from .repo import Repo


def _workdir_status(repo: Repo, head_files: dict[str, str]) -> set[str]:
    """返回与 HEAD 快照不一致的跟踪路径集合（修改或缺失）。"""
    dirty: set[str] = set()
    for path, sha in head_files.items():
        fs = repo.root / Path(*path.split("/"))
        if not fs.is_file():
            dirty.add(path)
            continue
        data = fs.read_bytes()
        if objects.hash_object(objects.TYPE_BLOB, data) != sha:
            dirty.add(path)
    return dirty


def _cleanup_empty_dirs(repo: Repo, removed: list[str]) -> None:
    """删除文件后自底向上尝试清理空目录（到仓库根为止，失败静默）。"""
    for rel in removed:
        cur = (repo.root / Path(*rel.split("/"))).parent
        while cur != repo.root and cur != cur.parent:
            try:
                cur.rmdir()  # 仅当空目录才成功
            except OSError:
                break
            cur = cur.parent


def cmd_checkout(repo: Repo, target: str) -> str:
    from .repo import validate_branch_name

    validate_branch_name(target)
    target_sha = repo.read_branch(target)
    if target_sha is None:
        raise GlitError(f"branch '{target}' does not exist")
    current = repo.current_branch()
    if current == target:
        return f"Already on '{target}'"

    head_sha = repo.head_commit()
    head_files: dict[str, str] = treebuild.flatten_commit(repo.root, head_sha) if head_sha else {}
    target_files: dict[str, str] = treebuild.flatten_commit(repo.root, target_sha)

    # --- 安全检查 ---
    dirty = _workdir_status(repo, head_files)
    if dirty:
        sample = ", ".join(sorted(dirty)[:3])
        raise GlitError(
            "Your local changes to the following files would be overwritten by checkout: "
            f"{sample}\nPlease commit your changes before switching branches."
        )
    untracked_conflicts = sorted(
        p for p in target_files
        if p not in head_files and (repo.root / Path(*p.split("/"))).exists()
    )
    if untracked_conflicts:
        sample = ", ".join(untracked_conflicts[:3])
        raise GlitError(
            f"The following untracked working tree files would be overwritten by checkout: {sample}"
        )

    # --- 执行切换 ---
    removed: list[str] = []
    for path in head_files:
        if path not in target_files:
            fs = repo.root / Path(*path.split("/"))
            if fs.is_file():
                fs.unlink()
            removed.append(path)
    _cleanup_empty_dirs(repo, removed)

    for path, sha in target_files.items():
        fs = repo.root / Path(*path.split("/"))
        fs.parent.mkdir(parents=True, exist_ok=True)
        _, payload = objects.read_object(repo.root, sha)
        fs.write_bytes(payload)

    index_mod.write_index(repo.root, {p: s for p, s in target_files.items()})
    repo.set_head_to_branch(target)
    return f"Switched to branch '{target}'"
