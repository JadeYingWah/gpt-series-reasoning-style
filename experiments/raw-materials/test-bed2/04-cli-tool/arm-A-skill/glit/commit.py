# -*- coding: utf-8 -*-
"""commit 对象的读写。payload（JSON，UTF-8）：
    {"tree": sha, "parents": [sha, ...], "author": str,
     "timestamp": ISO8601, "message": str}
"""
from __future__ import annotations

import json
from pathlib import Path

from . import objects
from . import GlitError


def write_commit(
    repo_root: Path,
    tree_sha: str,
    parents: list[str],
    author: str,
    timestamp: str,
    message: str,
) -> str:
    payload = json.dumps(
        {
            "tree": tree_sha,
            "parents": parents,
            "author": author,
            "timestamp": timestamp,
            "message": message,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return objects.write_object(repo_root, objects.TYPE_COMMIT, payload)


def read_commit(repo_root: Path, commit_sha: str) -> dict:
    obj_type, payload = objects.read_object(repo_root, commit_sha)
    if obj_type != objects.TYPE_COMMIT:
        raise objects.ObjectCorrupted(f"object {commit_sha} is not a commit")
    return json.loads(payload.decode("utf-8"))
