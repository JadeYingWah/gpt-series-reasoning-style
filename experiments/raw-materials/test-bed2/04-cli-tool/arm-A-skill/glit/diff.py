# -*- coding: utf-8 -*-
"""diff 实现。

两种模式：
  - 默认：工作区 vs 暂存区（index）
  - --staged：暂存区 vs HEAD 提交快照

文本 diff 用 difflib.unified_diff；含 NUL 字节或非 UTF-8 的文件判为二进制。
返回 (has_diff, text)；CLI 层对 has_diff 以退出码 1 表达。
"""
from __future__ import annotations

import difflib
import os
from pathlib import Path

from . import index as index_mod
from . import objects, treebuild
from .repo import Repo

EXCLUDE_DIRS = {".glit", "__pycache__"}


def _is_binary(data: bytes) -> bool:
    if b"\x00" in data:
        return True
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return True
    return False


def _read_blob_text(repo_root: Path, sha: str | None) -> str | None:
    """读 blob 内容为文本；sha 为 None（新增/删除侧缺失）或二进制返回 None。"""
    if sha is None:
        return None
    obj_type, payload = objects.read_object(repo_root, sha)
    assert obj_type == objects.TYPE_BLOB
    if _is_binary(payload):
        return None
    return payload.decode("utf-8")


def _read_workdir_bytes(repo_root: Path, rel_posix: str) -> bytes | None:
    fs = repo_root / Path(*rel_posix.split("/"))
    if not fs.is_file():
        return None
    return fs.read_bytes()


def _unified(path: str, old_bytes: bytes | None, new_bytes: bytes | None) -> str | None:
    """生成单个 path 的 unified diff；无差异返回 None；二进制返回占位说明。"""
    if old_bytes is not None and new_bytes is not None and old_bytes == new_bytes:
        return None
    if (old_bytes is not None and _is_binary(old_bytes)) or (
        new_bytes is not None and _is_binary(new_bytes)
    ):
        a = "a/" + path if old_bytes is not None else "/dev/null"
        b = "b/" + path if new_bytes is not None else "/dev/null"
        return f"Binary files {a} and {b} differ\n"

    def to_lines(data: bytes | None) -> list[str]:
        if data is None:
            return []
        text = data.decode("utf-8", errors="replace")
        lines = text.splitlines(keepends=True)
        if lines and not lines[-1].endswith("\n"):
            lines[-1] += "\n\\ No newline at end of file\n"
        return lines

    old_lines = to_lines(old_bytes)
    new_lines = to_lines(new_bytes)
    fromfile = "a/" + path if old_bytes is not None else "/dev/null"
    tofile = "b/" + path if new_bytes is not None else "/dev/null"
    diff = difflib.unified_diff(
        old_lines, new_lines, fromfile=fromfile, tofile=tofile, lineterm="\n"
    )
    return "".join(diff)


def _collect_workdir(repo_root: Path) -> dict[str, bytes | None]:
    """工作区全部文件的 {posix_path: bytes}。"""
    out: dict[str, bytes | None] = {}
    for dirpath, dirnames, filenames in os.walk(repo_root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for fn in filenames:
            full = Path(dirpath) / fn
            rel = index_mod.normalize_path(full.relative_to(repo_root))
            out[rel] = full.read_bytes()
    return out


def diff_workdir_index(repo: Repo) -> tuple[bool, str]:
    """工作区 vs 暂存区。未跟踪文件不显示（与 git 一致）。"""
    entries = index_mod.read_index(repo.root)
    chunks: list[str] = []
    for path in sorted(entries):
        old = objects.read_object(repo.root, entries[path])[1]
        new = _read_workdir_bytes(repo.root, path)
        chunk = _unified(path, old, new)
        if chunk:
            chunks.append(chunk)
    return bool(chunks), "".join(chunks)


def diff_index_head(repo: Repo) -> tuple[bool, str]:
    """暂存区 vs HEAD 提交快照。"""
    entries = index_mod.read_index(repo.root)
    head_sha = repo.head_commit()
    head_files: dict[str, str] = treebuild.flatten_commit(repo.root, head_sha) if head_sha else {}
    chunks: list[str] = []
    for path in sorted(set(entries) | set(head_files)):
        old = objects.read_object(repo.root, head_files[path])[1] if path in head_files else None
        new = objects.read_object(repo.root, entries[path])[1] if path in entries else None
        chunk = _unified(path, old, new)
        if chunk:
            chunks.append(chunk)
    return bool(chunks), "".join(chunks)


def run_diff(repo: Repo, staged: bool) -> tuple[bool, str]:
    return diff_index_head(repo) if staged else diff_workdir_index(repo)
