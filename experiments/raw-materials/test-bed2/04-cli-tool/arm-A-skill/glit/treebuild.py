# -*- coding: utf-8 -*-
"""构树：把暂存区（扁平 path->sha 映射）转成嵌套 tree 对象，并提供 flatten 反操作。

tree 对象 payload（JSON，UTF-8）：
    {"entries": [{"mode": "100644", "name": "...", "sha": "...", "type": "blob"|"tree"}, ...]}
entries 按 name 的 UTF-8 字节序排序，保证跨平台确定性。
"""
from __future__ import annotations

import json
from pathlib import Path

from . import objects


def _sorted_bytes_key(name: str) -> bytes:
    return name.encode("utf-8")


def _build_node(repo_root: Path, node: dict) -> str:
    """递归把嵌套 dict 写成 tree 对象，返回 tree sha。

    node 的 key 是名字；值是 dict（子目录）或 str（blob sha）。
    """
    entries = []
    for name, value in sorted(node.items(), key=lambda kv: _sorted_bytes_key(kv[0])):
        if isinstance(value, dict):
            sha = _build_node(repo_root, value)
            entries.append({"mode": "040000", "name": name, "sha": sha, "type": "tree"})
        else:
            entries.append({"mode": "100644", "name": name, "sha": value, "type": "blob"})
    payload = json.dumps(
        {"entries": entries}, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return objects.write_object(repo_root, objects.TYPE_TREE, payload)


def build_tree_from_index(repo_root: Path, entries: dict[str, str]) -> str:
    """从暂存区构建（或复用）整棵 tree，返回根 tree sha。空 index -> 空树。"""
    nested: dict = {}
    for path, sha in entries.items():
        parts = path.split("/")
        cur = nested
        for seg in parts[:-1]:
            cur = cur.setdefault(seg, {})
            if not isinstance(cur, dict):
                raise ValueError(f"path conflict in index: {path}")
        cur[parts[-1]] = sha
    return _build_node(repo_root, nested)


def read_tree_payload(repo_root: Path, tree_sha: str) -> list[dict]:
    obj_type, payload = objects.read_object(repo_root, tree_sha)
    if obj_type != objects.TYPE_TREE:
        raise objects.ObjectCorrupted(f"object {tree_sha} is not a tree")
    return json.loads(payload.decode("utf-8"))["entries"]


def flatten_tree(repo_root: Path, tree_sha: str, _prefix: str = "") -> dict[str, str]:
    """递归展开 tree -> {posix_path: blob_sha}。"""
    result: dict[str, str] = {}
    for entry in read_tree_payload(repo_root, tree_sha):
        path = f"{_prefix}/{entry['name']}" if _prefix else entry["name"]
        if entry["type"] == "tree":
            result.update(flatten_tree(repo_root, entry["sha"], path))
        else:
            result[path] = entry["sha"]
    return result


def flatten_commit(repo_root: Path, commit_sha: str) -> dict[str, str]:
    """commit -> 根 tree -> {posix_path: blob_sha}。"""
    from .commit import read_commit  # 局部导入避免环

    commit = read_commit(repo_root, commit_sha)
    return flatten_tree(repo_root, commit["tree"])
