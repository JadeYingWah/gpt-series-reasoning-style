# -*- coding: utf-8 -*-
"""仓库层：定位、init、HEAD / 引用（refs）操作。"""
from __future__ import annotations

import json
import re
from pathlib import Path

from . import GlitError

GLIT_DIR = ".glit"
DEFAULT_BRANCH = "main"

# 分支名规则：字母数字 . _ / -，无路径穿越，无 .. ，不以 - 或 . 开头，不以 .lock 结尾
_BRANCH_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/=-]*$")


def validate_branch_name(name: str) -> str:
    if not name or not _BRANCH_RE.match(name):
        raise GlitError(f"invalid branch name: {name!r}")
    if ".." in name or "//" in name:
        raise GlitError(f"invalid branch name (contains '..' or '//'): {name!r}")
    if name.endswith("/"):
        raise GlitError(f"invalid branch name (trailing '/'): {name!r}")
    if name.endswith(".lock"):
        raise GlitError(f"invalid branch name (ends with '.lock'): {name!r}")
    if any(seg.startswith(".") for seg in name.split("/")):
        raise GlitError(f"invalid branch name (leading '.' in path segment): {name!r}")
    return name


class Repo:
    """指向一个已存在的 glit 仓库。"""

    def __init__(self, root: Path):
        self.root = root.resolve()
        self.glit_dir = self.root / GLIT_DIR
        self.objects_dir = self.glit_dir / "objects"
        self.refs_dir = self.glit_dir / "refs" / "heads"
        self.head_file = self.glit_dir / "HEAD"
        self.index_file = self.glit_dir / "index.json"

    # ---------- 定位 / 创建 ----------

    @classmethod
    def find(cls, start: Path) -> "Repo":
        """从 start 逐级向上查找 .glit 目录；找不到抛 GlitError。"""
        cur = start.resolve()
        while True:
            if (cur / GLIT_DIR).is_dir():
                return cls(cur)
            parent = cur.parent
            if parent == cur:  # 到达盘符根
                raise GlitError(
                    f"not a glit repository (or any of the parent directories): {start}"
                )
            cur = parent

    @classmethod
    def create(cls, path: Path) -> "Repo":
        root = path.resolve()
        glit_dir = root / GLIT_DIR
        if glit_dir.exists():
            raise GlitError(f"glit repository already exists in {root}")
        (glit_dir / "objects").mkdir(parents=True)
        (glit_dir / "refs" / "heads").mkdir(parents=True)
        (glit_dir / "HEAD").write_text(f"ref: refs/heads/{DEFAULT_BRANCH}\n", encoding="utf-8")
        (glit_dir / "index.json").write_text(
            json.dumps({"version": 1, "entries": {}}, sort_keys=True), encoding="utf-8"
        )
        return cls(root)

    # ---------- HEAD ----------

    def head_ref(self) -> str | None:
        """HEAD 指向的引用名（如 refs/heads/main）；解析失败返回 None。"""
        try:
            content = self.head_file.read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            return None
        if content.startswith("ref: "):
            return content[5:].strip()
        return None

    def current_branch(self) -> str | None:
        ref = self.head_ref()
        if ref and ref.startswith("refs/heads/"):
            return ref[len("refs/heads/"):]
        return None

    def head_commit(self) -> str | None:
        """当前 HEAD 解析出的 commit sha；仓库尚无提交时返回 None。"""
        ref = self.head_ref()
        if ref is None:
            # HEAD 直接存 sha（本工具不产生该状态，但读取保持兼容）
            try:
                content = self.head_file.read_text(encoding="utf-8").strip()
            except FileNotFoundError:
                return None
            return content or None
        return self.read_branch(self.current_branch()) if self.current_branch() else None

    def set_head_to_branch(self, branch: str) -> None:
        validate_branch_name(branch)
        self.head_file.write_text(f"ref: refs/heads/{branch}\n", encoding="utf-8")

    # ---------- 引用 ----------

    def read_branch(self, branch: str) -> str | None:
        path = self.refs_dir / branch
        if not path.is_file():
            return None
        content = path.read_text(encoding="utf-8").strip()
        return content or None

    def update_branch(self, branch: str, sha: str) -> None:
        validate_branch_name(branch)
        path = self.refs_dir / branch
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(sha + "\n", encoding="utf-8")

    def delete_branch(self, branch: str) -> None:
        validate_branch_name(branch)
        path = self.refs_dir / branch
        if not path.is_file():
            raise GlitError(f"branch '{branch}' does not exist")
        path.unlink()

    def list_branches(self) -> list[str]:
        """列出 refs/heads 下所有分支（含子目录，'/' 连接），字典序。"""
        names: list[str] = []
        if not self.refs_dir.is_dir():
            return names
        for p in sorted(self.refs_dir.rglob("*")):
            if p.is_file():
                names.append(p.relative_to(self.refs_dir).as_posix())
        return sorted(names)
