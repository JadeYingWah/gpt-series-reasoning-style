"""对象存储层 —— GitLite 的核心抽象。

设计要点（自有的内容寻址格式，灵感来自 Git，实现独立）:

  序列化格式
      每个对象 = 头部 + 载荷
      头部   = "<type> <payload-size>\\n"   （ASCII，一行）
      载荷   = 类型相关的原始字节

  对象类型
      blob   文件内容的原样字节
      tree   目录快照，每行 "<mode> <oid> <name>\\n"，按名称字典序排序
      commit 提交元数据（tree/parent/author/committer）+ 提交说明

  寻址与落盘
      oid    = sha256(序列化后的完整字节)
      磁盘   = zlib 压缩后写入 <objects_dir>/<oid前2位>/<oid其余>
      内容寻址天然保证: 内容相同 => oid 相同 => 只存一份、可完整性校验

所有 I/O 均为二进制安全（bytes），不做任何换行符转换。
"""

from __future__ import annotations

import hashlib
import os
import zlib
from typing import Iterable, List, Tuple

BLOB = "blob"
TREE = "tree"
COMMIT = "commit"
OBJECT_TYPES = (BLOB, TREE, COMMIT)

MODE_FILE = "100644"
MODE_DIR = "40000"


class ObjectError(Exception):
    """对象存储相关错误。"""


# ----------------------------------------------------------------------
# 序列化 / 反序列化
# ----------------------------------------------------------------------

def serialize(obj_type: str, payload: bytes) -> bytes:
    """把 (类型, 载荷) 序列化为带头部的完整对象字节。"""
    if obj_type not in OBJECT_TYPES:
        raise ObjectError(f"unknown object type: {obj_type!r}")
    if not isinstance(payload, (bytes, bytearray)):
        raise ObjectError("object payload must be bytes")
    payload = bytes(payload)
    header = f"{obj_type} {len(payload)}\n".encode("ascii")
    return header + payload


def deserialize(raw: bytes) -> Tuple[str, bytes]:
    """解析完整对象字节，返回 (类型, 载荷)。头部与载荷长度强校验。"""
    sep = raw.find(b"\n")
    if sep < 0:
        raise ObjectError("malformed object: missing header terminator")
    header = raw[:sep]
    try:
        type_b, size_b = header.split(b" ", 1)
        obj_type = type_b.decode("ascii")
        size = int(size_b.decode("ascii"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise ObjectError(f"malformed object header: {header!r}") from exc
    if obj_type not in OBJECT_TYPES:
        raise ObjectError(f"unknown object type: {obj_type!r}")
    payload = raw[sep + 1:]
    if len(payload) != size:
        raise ObjectError(
            f"object size mismatch: header says {size}, payload is {len(payload)}"
        )
    return obj_type, payload


def hash_raw(raw: bytes) -> str:
    """对象字节的寻址哈希（SHA-256 hex）。"""
    return hashlib.sha256(raw).hexdigest()


def blob_oid(payload: bytes) -> str:
    """计算内容对应的 blob oid（不落盘）。"""
    return hash_raw(serialize(BLOB, payload))


# ----------------------------------------------------------------------
# 对象库
# ----------------------------------------------------------------------

class ObjectStore:
    """内容寻址对象库，落盘于 objects_dir。"""

    def __init__(self, objects_dir: str):
        self.objects_dir = objects_dir

    def _object_path(self, oid: str) -> str:
        return os.path.join(self.objects_dir, oid[:2], oid[2:])

    def write_raw(self, raw: bytes) -> str:
        """写入任意对象字节（先序列化），返回其 oid。幂等。"""
        oid = hash_raw(raw)
        path = self._object_path(oid)
        if not os.path.exists(path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            tmp = path + ".tmp"
            with open(tmp, "wb") as f:
                f.write(zlib.compress(raw))
            os.replace(tmp, path)
        return oid

    def store(self, obj_type: str, payload: bytes) -> str:
        """序列化并落盘一个对象，返回 oid。"""
        return self.write_raw(serialize(obj_type, payload))

    def has(self, oid: str) -> bool:
        return os.path.isfile(self._object_path(oid))

    def read_raw(self, oid: str) -> bytes:
        path = self._object_path(oid)
        if not os.path.isfile(path):
            raise ObjectError(f"object not found: {oid}")
        with open(path, "rb") as f:
            data = zlib.decompress(f.read())
        # 完整性校验: 内容寻址库中 oid 必须等于内容的哈希
        actual = hash_raw(data)
        if actual != oid:
            raise ObjectError(f"object corrupted: {oid} (hash mismatch: {actual})")
        return data

    def read(self, oid: str) -> Tuple[str, bytes]:
        return deserialize(self.read_raw(oid))

    def prefixes(self, prefix: str) -> List[str]:
        """列出匹配给定十六进制前缀的全部 oid（前缀 >= 2 字符可定位分桶）。"""
        if len(prefix) < 2:
            return []
        bucket = os.path.join(self.objects_dir, prefix[:2])
        if not os.path.isdir(bucket):
            return []
        rest = prefix[2:]
        return sorted(prefix[:2] + name for name in os.listdir(bucket) if name.startswith(rest))


# ----------------------------------------------------------------------
# tree 对象的构建与解析
# ----------------------------------------------------------------------

def build_tree_payload(entries: Iterable[Tuple[str, str, str]]) -> bytes:
    """entries: (mode, oid, name) -> 确定性排序的 tree 载荷。"""
    lines = [
        f"{mode} {oid} {name}".encode("utf-8")
        for mode, oid, name in sorted(entries, key=lambda e: e[2])
    ]
    if not lines:
        return b""
    return b"\n".join(lines) + b"\n"


def parse_tree(payload: bytes) -> List[Tuple[str, str, str]]:
    """tree 载荷 -> [(mode, oid, name), ...]。名称允许包含空格。"""
    entries: List[Tuple[str, str, str]] = []
    for line in payload.split(b"\n"):
        if not line:
            continue
        try:
            mode_b, rest = line.split(b" ", 1)
            oid_b, name_b = rest.split(b" ", 1)
        except ValueError as exc:
            raise ObjectError(f"malformed tree entry: {line!r}") from exc
        entries.append(
            (
                mode_b.decode("ascii"),
                oid_b.decode("ascii"),
                name_b.decode("utf-8", "surrogateescape"),
            )
        )
    return entries


# ----------------------------------------------------------------------
# commit 对象的构建与解析
# ----------------------------------------------------------------------

def format_commit_payload(
    tree_oid: str,
    parents: List[str],
    author: str,
    committer: str,
    message: str,
) -> bytes:
    """构建 commit 载荷。author/committer 形如 "Name <email> <ts> <tz>"。"""
    lines = [f"tree {tree_oid}"]
    for p in parents:
        lines.append(f"parent {p}")
    lines.append(f"author {author}")
    lines.append(f"committer {committer}")
    body = message.strip()
    return ("\n".join(lines) + "\n\n" + body + "\n").encode("utf-8")


def parse_commit(payload: bytes) -> dict:
    """commit 载荷 -> {"tree", "parents", "author", "committer", "message"}。"""
    text = payload.decode("utf-8", "surrogateescape")
    head, _sep, message = text.partition("\n\n")
    info = {
        "tree": None,
        "parents": [],
        "author": "",
        "committer": "",
        "message": message,
    }
    for line in head.splitlines():
        if not line:
            continue
        key, _s, value = line.partition(" ")
        if key == "tree":
            info["tree"] = value
        elif key == "parent":
            info["parents"].append(value)
        elif key in ("author", "committer"):
            info[key] = value
    if info["tree"] is None:
        raise ObjectError("malformed commit: missing tree header")
    return info
