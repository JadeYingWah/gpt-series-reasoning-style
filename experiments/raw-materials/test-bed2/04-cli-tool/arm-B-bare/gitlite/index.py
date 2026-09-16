"""暂存区（index）层。

index 是工作区与提交历史之间的缓冲带，记录"下一次 commit 将包含什么"。

磁盘格式为 JSON:
    {
      "version": 1,
      "entries": {
        "<posix-relative-path>": {"oid": "<sha256>", "mode": "100644"}
      }
    }

路径统一使用 POSIX 风格（/）相对仓库根的表示，保证跨平台确定性。
"""

from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

INDEX_VERSION = 1
MODE_FILE = "100644"


class IndexError(Exception):
    """暂存区相关错误。"""


class Index:
    """内存中的暂存区，通过 load()/save() 与磁盘同步。"""

    def __init__(self, path: str):
        self.path = path
        # path -> {"oid": str, "mode": str}
        self.entries: Dict[str, Dict[str, str]] = {}

    # -- 磁盘 I/O -----------------------------------------------------------

    @classmethod
    def load(cls, path: str) -> "Index":
        idx = cls(path)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError as exc:
                    raise IndexError(f"corrupted index file: {path}") from exc
            if data.get("version") != INDEX_VERSION:
                raise IndexError(f"unsupported index version: {data.get('version')!r}")
            for p, e in data.get("entries", {}).items():
                idx.entries[p] = {"oid": e["oid"], "mode": e.get("mode", MODE_FILE)}
        return idx

    def save(self) -> None:
        data = {
            "version": INDEX_VERSION,
            "entries": {p: self.entries[p] for p in sorted(self.entries)},
        }
        parent = os.path.dirname(self.path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8", newline="") as f:
            json.dump(data, f, indent=2, sort_keys=False)
            f.write("\n")
        os.replace(tmp, self.path)

    # -- 条目操作 ------------------------------------------------------------

    def add(self, path: str, oid: str, mode: str = MODE_FILE) -> None:
        self.entries[path] = {"oid": oid, "mode": mode}

    def remove(self, path: str) -> bool:
        """移除条目；返回是否确实存在。"""
        return self.entries.pop(path, None) is not None

    def has(self, path: str) -> bool:
        return path in self.entries

    def get(self, path: str) -> Optional[Dict[str, str]]:
        return self.entries.get(path)

    def paths(self) -> List[str]:
        return sorted(self.entries)

    def as_oid_map(self) -> Dict[str, str]:
        """返回 {path: oid} 视图，便于与 tree 文件映射比较。"""
        return {p: e["oid"] for p, e in self.entries.items()}
