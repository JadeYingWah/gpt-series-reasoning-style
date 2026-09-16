"""测试公共工具：临时仓库夹具、CLI 子进程调用。"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# CLI 子进程需要能 import 到 gitlite 包
SUBPROCESS_ENV = {
    "PYTHONPATH": PROJECT_ROOT,
    "GITLITE_AUTHOR_NAME": "Test Author",
    "GITLITE_AUTHOR_EMAIL": "author@example.com",
}


def run_cli(cwd: str, *args: str):
    """在 cwd 下以子进程方式运行 gitlite CLI。返回 CompletedProcess。"""
    env = dict(os.environ)
    env.update(SUBPROCESS_ENV)
    return subprocess.run(
        [sys.executable, "-m", "gitlite", *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


class TempRepoTestCase(unittest.TestCase):
    """每个测试一个独立临时目录 + 已 init 的仓库，并 chdir 进仓库根
    （模拟真实 CLI 环境：相对路径相对当前目录解析）。"""

    def setUp(self):
        self._old_cwd = os.getcwd()
        # 固定作者身份，便于断言（commands 层从环境变量读取）
        self._old_env = {
            k: os.environ.get(k)
            for k in ("GITLITE_AUTHOR_NAME", "GITLITE_AUTHOR_EMAIL")
        }
        os.environ["GITLITE_AUTHOR_NAME"] = "Test Author"
        os.environ["GITLITE_AUTHOR_EMAIL"] = "author@example.com"

        self.tmp = tempfile.mkdtemp(prefix="gitlite-test-")
        from gitlite.repository import Repository

        self.repo = Repository.init(self.tmp)
        os.chdir(self.tmp)

    def tearDown(self):
        os.chdir(self._old_cwd)
        for k, v in self._old_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(self.tmp, ignore_errors=True)

    # -- 工作区文件小工具 ---------------------------------------------------

    def w(self, rel: str, content: str) -> str:
        """写入工作区文件（UTF-8），返回绝对路径。"""
        p = os.path.join(self.tmp, *rel.split("/"))
        parent = os.path.dirname(p)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="") as f:
            f.write(content)
        return p

    def r(self, rel: str):
        """读工作区文件（UTF-8），不存在返回 None。"""
        p = os.path.join(self.tmp, *rel.split("/"))
        if not os.path.exists(p):
            return None
        with open(p, "r", encoding="utf-8", newline="") as f:
            return f.read()

    def exists(self, rel: str) -> bool:
        return os.path.exists(os.path.join(self.tmp, *rel.split("/")))
