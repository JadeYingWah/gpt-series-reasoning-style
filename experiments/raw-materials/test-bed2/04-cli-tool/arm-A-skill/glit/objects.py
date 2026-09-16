# -*- coding: utf-8 -*-
"""对象存储层：写入 / 读取 / 校验。

对象格式（自定义，见包 docstring）：
  - 内容寻址：SHA-1(header + payload) 作为对象名
  - zlib 压缩落盘
  - 读取时全量校验：magic、版本、长度、哈希 —— 任一不符即抛 ObjectCorrupted
"""
from __future__ import annotations

import hashlib
import os
import struct
import zlib
from pathlib import Path

from . import GlitError

MAGIC = b"GLIT"
FORMAT_VERSION = 1
TYPE_BLOB = 1
TYPE_TREE = 2
TYPE_COMMIT = 3

_HEADER_FMT = ">4sBBI"  # magic, version, type, payload_len


class ObjectCorrupted(GlitError):
    """对象库内容损坏（magic/版本/长度/哈希校验失败）。"""


def _build_full(obj_type: int, payload: bytes) -> bytes:
    header = struct.pack(
        _HEADER_FMT, MAGIC, FORMAT_VERSION, obj_type, len(payload)
    )
    return header + payload


def hash_object(obj_type: int, payload: bytes) -> str:
    """计算对象名（不落盘）。"""
    return hashlib.sha1(_build_full(obj_type, payload)).hexdigest()


def write_object(repo_root: Path, obj_type: int, payload: bytes) -> str:
    """写入对象（内容寻址，幂等），返回对象 sha。"""
    full = _build_full(obj_type, payload)
    sha = hashlib.sha1(full).hexdigest()
    objects_dir = repo_root / ".glit" / "objects"
    obj_dir = objects_dir / sha[:2]
    obj_path = obj_dir / sha[2:]
    if obj_path.exists():
        return sha  # 内容寻址：已存在即同一对象，无需重写
    obj_dir.mkdir(parents=True, exist_ok=True)
    stored = zlib.compress(full, 9)
    tmp_path = obj_path.with_suffix(".tmp")
    with open(tmp_path, "wb") as f:
        f.write(stored)
    os.replace(tmp_path, obj_path)  # 原子落盘
    return sha


def read_object(repo_root: Path, sha: str) -> tuple[int, bytes]:
    """按 sha 读取对象，返回 (obj_type, payload)。全量校验，损坏即抛错。"""
    if len(sha) != 40 or any(c not in "0123456789abcdef" for c in sha):
        raise ObjectCorrupted(f"invalid object name: {sha!r}")
    obj_path = repo_root / ".glit" / "objects" / sha[:2] / sha[2:]
    if not obj_path.exists():
        raise ObjectCorrupted(f"object not found: {sha}")
    with open(obj_path, "rb") as f:
        stored = f.read()
    try:
        full = zlib.decompress(stored)
    except zlib.error as e:
        raise ObjectCorrupted(f"object {sha}: zlib decompress failed: {e}") from e
    if len(full) < struct.calcsize(_HEADER_FMT):
        raise ObjectCorrupted(f"object {sha}: header truncated")
    magic, version, obj_type, payload_len = struct.unpack(_HEADER_FMT, full[: struct.calcsize(_HEADER_FMT)])
    if magic != MAGIC:
        raise ObjectCorrupted(f"object {sha}: bad magic {magic!r}")
    if version != FORMAT_VERSION:
        raise ObjectCorrupted(f"object {sha}: unsupported format version {version}")
    payload = full[struct.calcsize(_HEADER_FMT):]
    if len(payload) != payload_len:
        raise ObjectCorrupted(
            f"object {sha}: payload length mismatch (header={payload_len}, actual={len(payload)})"
        )
    if hashlib.sha1(full).hexdigest() != sha:
        raise ObjectCorrupted(f"object {sha}: hash mismatch (content corrupted)")
    return obj_type, payload
