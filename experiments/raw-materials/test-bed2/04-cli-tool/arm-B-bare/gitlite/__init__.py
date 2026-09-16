"""GitLite —— 一个内容寻址的迷你版本控制系统。

支持命令: init / add / commit / log / diff / checkout / branch
对象存储: SHA-256 内容寻址 + zlib 压缩，对象类型 blob / tree / commit
"""

from __future__ import annotations

__version__ = "1.0.0"

from .repository import Repository, RepositoryError  # noqa: F401
