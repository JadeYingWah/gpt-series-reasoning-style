"""仓库核心层：仓库定位/初始化、HEAD 与引用、tree 展开、检出同步。"""

from __future__ import annotations

import os
from typing import Dict, List, Optional, Tuple

from .index import Index
from .objects import (
    BLOB,
    COMMIT,
    MODE_DIR,
    MODE_FILE,
    TREE,
    ObjectStore,
    blob_oid,
    build_tree_payload,
    hash_raw,
    parse_commit,
    parse_tree,
    serialize,
)

REPO_DIRNAME = ".gitlite"
HEAD_FILE = "HEAD"
DEFAULT_BRANCH = "main"
_MIN_HASH_PREFIX = 4


class RepositoryError(Exception):
    """仓库操作相关错误。"""


class NotARepository(RepositoryError):
    """未在 gitlite 仓库内。"""


class Repository:
    """代表一个位于 <root>/.gitlite 的 GitLite 仓库。"""

    def __init__(self, root: str):
        self.root = os.path.abspath(root)
        self.lite_dir = os.path.join(self.root, REPO_DIRNAME)
        self.objects = ObjectStore(os.path.join(self.lite_dir, "objects"))

    # ------------------------------------------------------------------
    # 定位与初始化
    # ------------------------------------------------------------------

    @classmethod
    def find(cls, start: str = ".") -> "Repository":
        """从 start 目录向上查找最近的 .gitlite 目录。"""
        d = os.path.abspath(start)
        while True:
            if os.path.isdir(os.path.join(d, REPO_DIRNAME)):
                return cls(d)
            parent = os.path.dirname(d)
            if parent == d:
                raise NotARepository(
                    f"not a gitlite repository (or any parent directory up to filesystem root)"
                )
            d = parent

    @classmethod
    def init(cls, path: str = ".", branch: str = DEFAULT_BRANCH) -> "Repository":
        """在 path 创建仓库骨架（幂等：不覆盖已有 HEAD/refs）。"""
        repo = cls(path)
        os.makedirs(repo.objects.objects_dir, exist_ok=True)
        os.makedirs(os.path.join(repo.lite_dir, "refs", "heads"), exist_ok=True)
        head_path = os.path.join(repo.lite_dir, HEAD_FILE)
        if not os.path.exists(head_path):
            repo._write_lite_file(HEAD_FILE, f"ref: refs/heads/{branch}\n")
        return repo

    # ------------------------------------------------------------------
    # 仓库内小文件（HEAD / refs）读写
    # ------------------------------------------------------------------

    def _lite_path(self, *parts: str) -> str:
        return os.path.join(self.lite_dir, *parts)

    def _write_lite_file(self, rel: str, content: str) -> None:
        p = self._lite_path(*rel.split("/"))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="") as f:
            f.write(content)

    def _read_lite_file(self, rel: str) -> str:
        p = self._lite_path(*rel.split("/"))
        with open(p, "r", encoding="utf-8") as f:
            return f.read()

    # ------------------------------------------------------------------
    # 暂存区
    # ------------------------------------------------------------------

    @property
    def index_path(self) -> str:
        return self._lite_path("index")

    def load_index(self) -> Index:
        return Index.load(self.index_path)

    # ------------------------------------------------------------------
    # HEAD 与分支引用
    # ------------------------------------------------------------------

    def read_head(self) -> str:
        """返回 HEAD 内容: "ref: refs/heads/<branch>" 或裸 commit oid。"""
        return self._read_lite_file(HEAD_FILE).strip()

    def head_target(self) -> Optional[str]:
        """HEAD 符号指向的引用名；分离 HEAD 时返回 None。"""
        content = self.read_head()
        if content.startswith("ref: "):
            return content[5:].strip()
        return None

    def head_is_detached(self) -> bool:
        return self.head_target() is None

    def current_branch(self) -> Optional[str]:
        target = self.head_target()
        if target and target.startswith("refs/heads/"):
            return target[len("refs/heads/"):]
        return None

    def head_commit_oid(self) -> Optional[str]:
        """HEAD 指向的 commit oid；分支未出生（无提交）或空 HEAD 时为 None。"""
        if self.head_is_detached():
            oid = self.read_head()
            return oid or None
        return self.read_ref(self.head_target() or "")

    def ref_path(self, ref: str) -> str:
        return self._lite_path(*ref.split("/"))

    def read_ref(self, ref: str) -> Optional[str]:
        p = self.ref_path(ref)
        if not os.path.isfile(p):
            return None
        with open(p, "r", encoding="utf-8") as f:
            oid = f.read().strip()
        return oid or None

    def write_ref(self, ref: str, oid: str) -> None:
        self._write_lite_file(ref, oid + "\n")

    def delete_ref(self, ref: str) -> None:
        p = self.ref_path(ref)
        if os.path.exists(p):
            os.remove(p)

    def branch_names(self) -> List[str]:
        base = self._lite_path("refs", "heads")
        names: List[str] = []
        if not os.path.isdir(base):
            return names
        for dirpath, _dirnames, filenames in os.walk(base):
            for fn in filenames:
                full = os.path.join(dirpath, fn)
                rel = os.path.relpath(full, base).replace(os.sep, "/")
                names.append(rel)
        return sorted(names)

    def resolve_revision(self, name: str) -> Optional[str]:
        """把 name 解析为 commit oid。

        依次尝试: HEAD / 分支名 / commit 哈希（完整或 >=4 字符唯一前缀）。
        无法识别时返回 None（调用方可退化为按文件路径处理）。
        """
        if name == "HEAD":
            oid = self.head_commit_oid()
            if oid is None:
                raise RepositoryError("HEAD does not point to any commit yet")
            return oid
        oid = self.read_ref(f"refs/heads/{name}")
        if oid:
            return oid
        lowered = name.lower()
        if _MIN_HASH_PREFIX <= len(lowered) <= 64 and all(
            c in "0123456789abcdef" for c in lowered
        ):
            matches = self.objects.prefixes(lowered)
            if len(matches) > 1:
                raise RepositoryError(f"ambiguous revision: {name}")
            if len(matches) == 1:
                oid = matches[0]
                otype, _ = self.objects.read(oid)
                if otype != COMMIT:
                    raise RepositoryError(f"object {name} is a {otype}, not a commit")
                return oid
        return None

    # ------------------------------------------------------------------
    # tree / commit 相关
    # ------------------------------------------------------------------

    def read_tree_recursive(self, tree_oid: str) -> Dict[str, Tuple[str, str]]:
        """递归展开 tree，返回 {posix_path: (oid, mode)}（仅文件条目）。"""
        out: Dict[str, Tuple[str, str]] = {}
        stack: List[Tuple[str, str]] = [("", tree_oid)]
        while stack:
            prefix, tid = stack.pop()
            otype, payload = self.objects.read(tid)
            if otype != TREE:
                raise RepositoryError(f"expected a tree object, got {otype}: {tid}")
            for mode, oid, name in parse_tree(payload):
                rel = prefix + name
                if mode == MODE_DIR:
                    stack.append((rel + "/", oid))
                else:
                    out[rel] = (oid, mode)
        return out

    def commit_tree_files(self, commit_oid: str) -> Dict[str, Tuple[str, str]]:
        """返回一个 commit 对应的完整文件快照 {posix_path: (oid, mode)}。"""
        otype, payload = self.objects.read(commit_oid)
        if otype != COMMIT:
            raise RepositoryError(f"object {commit_oid} is a {otype}, not a commit")
        info = parse_commit(payload)
        return self.read_tree_recursive(info["tree"])

    def build_tree_from_entries(
        self, entries: Dict[str, Tuple[str, str]]
    ) -> str:
        """把 {posix_path: (oid, mode)} 的扁平映射构建为嵌套 tree，返回根 tree oid。"""

        root: Dict[str, object] = {}
        for path in sorted(entries):
            oid, mode = entries[path]
            parts = path.split("/")
            node = root
            for part in parts[:-1]:
                nxt = node.get(part)
                if not isinstance(nxt, dict):
                    nxt = {}
                    node[part] = nxt
                node = nxt
            node[parts[-1]] = (mode, oid)

        def write(node: Dict[str, object]) -> str:
            items: List[Tuple[str, str, str]] = []
            for name, value in node.items():
                if isinstance(value, dict):
                    items.append((MODE_DIR, write(value), name))
                else:
                    mode, oid = value  # type: ignore[misc]
                    items.append((mode, oid, name))
            return self.objects.store(TREE, build_tree_payload(items))

        return write(root)

    def commit_tree_oid(self, commit_oid: str) -> str:
        otype, payload = self.objects.read(commit_oid)
        if otype != COMMIT:
            raise RepositoryError(f"object {commit_oid} is a {otype}, not a commit")
        return parse_commit(payload)["tree"]

    def is_ancestor(self, ancestor_oid: str, descendant_oid: str) -> bool:
        """判断 ancestor 是否是 descendant 的祖先（沿 parent 链遍历）。"""
        stack = [descendant_oid]
        seen = set()
        while stack:
            oid = stack.pop()
            if oid == ancestor_oid:
                return True
            if oid in seen:
                continue
            seen.add(oid)
            _t, payload = self.objects.read(oid)
            stack.extend(parse_commit(payload)["parents"])
        return False

    # ------------------------------------------------------------------
    # 工作区操作
    # ------------------------------------------------------------------

    def worktree_path(self, posix_rel: str) -> str:
        return os.path.join(self.root, *posix_rel.split("/"))

    def read_worktree_file(self, posix_rel: str) -> Optional[bytes]:
        p = self.worktree_path(posix_rel)
        if not os.path.isfile(p):
            return None
        with open(p, "rb") as f:
            return f.read()

    def write_worktree_file(self, posix_rel: str, content: bytes) -> None:
        p = self.worktree_path(posix_rel)
        parent = os.path.dirname(p)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(p, "wb") as f:
            f.write(content)

    def remove_worktree_file(self, posix_rel: str) -> None:
        """删除工作区文件，并尽量清掉因此变空的父目录。"""
        p = self.worktree_path(posix_rel)
        if os.path.exists(p):
            os.remove(p)
        d = os.path.dirname(p)
        root = os.path.abspath(self.root)
        while d and os.path.abspath(d) != root:
            try:
                os.rmdir(d)
            except OSError:
                break
            d = os.path.dirname(d)

    def worktree_file_oid(self, posix_rel: str) -> Optional[str]:
        """计算工作区文件当前的 blob oid；文件不存在时返回 None。"""
        content = self.read_worktree_file(posix_rel)
        if content is None:
            return None
        return blob_oid(content)

    # ------------------------------------------------------------------
    # 检出同步（checkout 的核心：把工作区 + index 重置到目标快照）
    # ------------------------------------------------------------------

    def checkout_sync(self, target_files: Dict[str, Tuple[str, str]]) -> None:
        """把工作区与 index 安全地重置为 target_files 所示的快照。

        安全规则（保守策略，宁拒不删）:
          1. index 中每个条目，工作区文件必须与 index 完全一致
             （否则存在未暂存修改，拒绝检出）；
          2. index 与当前 HEAD 快照必须一致（存在已暂存未提交的变更，
             拒绝检出，避免暂存内容被静默丢弃）；
          3. 目标快照要新建的文件，若工作区已存在同名 untracked 文件
             且内容不同，拒绝检出。
        """
        idx = self.load_index()

        head_oid = self.head_commit_oid()
        head_files = self.commit_tree_files(head_oid) if head_oid else {}

        # 规则 2: 不允许带着"已暂存未提交"的变更切换
        if idx.as_oid_map() != {p: oid for p, (oid, _m) in head_files.items()}:
            raise RepositoryError(
                "you have staged but uncommitted changes; "
                "commit them before switching branches"
            )

        # 规则 1: 不允许存在未暂存修改（工作区 != index）
        for path, entry in sorted(idx.entries.items()):
            wt_oid = self.worktree_file_oid(path)
            if wt_oid != entry["oid"]:
                raise RepositoryError(
                    f"your local changes to '{path}' would be overwritten "
                    "by checkout; commit them first"
                )

        # 规则 3: 保护 untracked 文件
        for path, (oid, _mode) in sorted(target_files.items()):
            if path in head_files:
                continue
            wt_oid = self.worktree_file_oid(path)
            if wt_oid is not None and wt_oid != oid:
                raise RepositoryError(
                    f"untracked working tree file '{path}' would be "
                    "overwritten by checkout"
                )

        # 应用: 先删（当前快照有、目标没有的），再写（内容有差异的）
        for path in sorted(head_files):
            if path not in target_files:
                self.remove_worktree_file(path)
        for path, (oid, _mode) in sorted(target_files.items()):
            if self.worktree_file_oid(path) != oid:
                _t, payload = self.objects.read(oid)
                self.write_worktree_file(path, payload)

        # index 重置为目标快照
        new_idx = Index(self.index_path)
        for path, (oid, mode) in target_files.items():
            new_idx.add(path, oid, mode)
        new_idx.save()
