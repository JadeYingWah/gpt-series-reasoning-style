# -*- coding: utf-8 -*-
"""共享测试工具：临时仓库上下文、CLI 捕获运行器。"""
from __future__ import annotations

import contextlib
import io
import os
import tempfile
import unittest
from pathlib import Path

from glit.cli import main as cli_main
from glit.repo import Repo

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TempRepoTestCase(unittest.TestCase):
    """每个测试方法一个全新的临时仓库（已 init，cwd 已切换进去）。"""

    def setUp(self) -> None:
        self._old_cwd = os.getcwd()
        self.tmp = Path(tempfile.mkdtemp(prefix="glit-test-"))
        os.chdir(self.tmp)
        self.addCleanup(os.chdir, self._old_cwd)
        self.addCleanup(self._cleanup_tmp)
        run_cli("init")
        self.repo = Repo.find(self.tmp)

    def _cleanup_tmp(self) -> None:
        import shutil

        shutil.rmtree(self.tmp, ignore_errors=True)

    # ---- 常用断言辅助 ----

    def write(self, rel: str, content: str | bytes) -> Path:
        p = self.tmp / Path(*rel.split("/"))
        p.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            p.write_bytes(content)
        else:
            p.write_text(content, encoding="utf-8", newline="")  # 保留 \n，禁止 Windows 转换
        return p

    def read(self, rel: str) -> bytes:
        return (self.tmp / Path(*rel.split("/"))).read_bytes()

    def exists(self, rel: str) -> bool:
        return (self.tmp / Path(*rel.split("/"))).exists()


def run_cli(*args: str, cwd: Path | None = None) -> tuple[int, str, str]:
    """进程内调用 CLI，捕获 stdout/stderr，返回 (code, out, err)。"""
    old_cwd = os.getcwd()
    if cwd is not None:
        os.chdir(cwd)
    try:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = cli_main(list(args))
        return code, out.getvalue(), err.getvalue()
    finally:
        os.chdir(old_cwd)


def run_cli_expect(*args: str, code: int = 0, cwd: Path | None = None) -> str:
    got_code, out, err = run_cli(*args, cwd=cwd)
    if got_code != code:
        self_msg = f"cli {args!r}: expected exit {code}, got {got_code}; stderr={err!r}"
        raise AssertionError(self_msg)
    return out
