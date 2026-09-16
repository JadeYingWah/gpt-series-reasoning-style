# -*- coding: utf-8 -*-
"""暂存区（index）：扁平 {posix_path: blob_sha} 映射，持久化为 .glit/index.json。

路径统一以 '/' 分隔存储（跨平台确定性），磁盘操作时再转为本地分隔符。
"""
from __future__ import annotations

import json
from pathlib import Path, PurePosixPath

INDEX_VERSION = 1


def normalize_path(p: str | Path) -> str:
    """把任意路径规范化为仓库内相对 posix 路径字符串。"""
    s = str(p).replace("\\", "/").strip("/")
    pp = PurePosixPath(s)
    if pp.is_absolute() or ".." in pp.parts:
        raise ValueError(f"path escapes repository: {p}")
    return str(pp)


def read_index(repo_root: Path) -> dict[str, str]:
    index_file = repo_root / ".glit" / "index.json"
    try:
        data = json.loads(index_file.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    if data.get("version") != INDEX_VERSION:
        raise ValueError(f"unsupported index version: {data.get('version')}")
    return dict(data.get("entries", {}))


def write_index(repo_root: Path, entries: dict[str, str]) -> None:
    index_file = repo_root / ".glit" / "index.json"
    payload = json.dumps(
        {"version": INDEX_VERSION, "entries": dict(entries)},
        sort_keys=True,
        ensure_ascii=False,
    )
    index_file.write_text(payload, encoding="utf-8")
