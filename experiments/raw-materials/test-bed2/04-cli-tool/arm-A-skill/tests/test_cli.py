# -*- coding: utf-8 -*-
"""端到端冒烟：用 subprocess 真实执行 `python -m glit`，验证 CLI 与退出码。"""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _run(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(PROJECT_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    env.pop("GLIT_AUTHOR", None)
    return subprocess.run(
        [sys.executable, "-m", "glit", *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
    )


class CliEndToEndTest(unittest.TestCase):
    """subprocess 级全链路：init -> add -> commit -> log -> diff -> branch -> checkout。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="glit-e2e-"))
        self.addCleanup(self._cleanup)

    def _cleanup(self):
        import shutil

        shutil.rmtree(self.tmp, ignore_errors=True)

    def _expect(self, args, code=0):
        r = _run(args, self.tmp)
        self.assertEqual(
            r.returncode, code, f"glit {args}: exit={r.returncode}, stderr={r.stderr!r}"
        )
        return r

    def test_full_workflow(self):
        self._expect(["init"])
        (self.tmp / "a.txt").write_text("v1\n", encoding="utf-8", newline="")
        (self.tmp / "src").mkdir()
        (self.tmp / "src" / "m.py").write_text("print(1)\n", encoding="utf-8", newline="")
        self._expect(["add", "a.txt", "src"])

        r = self._expect(["commit", "-m", "c1"])
        self.assertIn("[main ", r.stdout)
        self.assertIn("c1", r.stdout)

        r = self._expect(["log", "--oneline"])
        self.assertRegex(r.stdout, r"^[0-9a-f]{7} c1\n$")

        # 修改 -> 默认 diff 有差异（退出码 1）
        (self.tmp / "a.txt").write_text("v2\n", encoding="utf-8", newline="")
        r = self._expect(["diff"], code=1)
        self.assertIn("+v2", r.stdout)

        # 暂存后 --staged 才有差异
        self._expect(["add", "a.txt"])
        self._expect(["diff"])
        r = self._expect(["diff", "--staged"], code=1)
        self.assertIn("+v2", r.stdout)
        self._expect(["commit", "-m", "c2"])

        # 分支创建 / 切换 / 隔离
        self._expect(["branch", "dev"])
        r = self._expect(["branch"])
        self.assertEqual(r.stdout.rstrip("\n").splitlines(), ["  dev", "* main"])
        self._expect(["checkout", "dev"])
        (self.tmp / "b.txt").write_text("B\n", encoding="utf-8", newline="")
        self._expect(["add", "b.txt"])
        self._expect(["commit", "-m", "dev adds b"])
        self._expect(["checkout", "main"])
        self.assertFalse((self.tmp / "b.txt").exists())
        r = self._expect(["log", "--oneline"])
        self.assertNotIn("dev adds b", r.stdout)
        self._expect(["checkout", "dev"])
        self.assertTrue((self.tmp / "b.txt").exists())

    def test_error_exit_codes(self):
        # 仓库外
        r = _run(["log"], self.tmp)
        self.assertEqual(r.returncode, 1)
        self.assertIn("not a glit repository", r.stderr)

        self._expect(["init"])
        # 无提交时各命令的错误路径
        r = self._expect(["log"], code=1)
        self.assertIn("does not have any commits", r.stderr)
        r = self._expect(["commit", "-m", "x"], code=1)
        self.assertIn("nothing to commit", r.stderr)
        r = self._expect(["add", "ghost"], code=1)
        self.assertIn("did not match", r.stderr)
        r = self._expect(["checkout", "ghost"], code=1)
        self.assertIn("does not exist", r.stderr)
        r = self._expect(["branch", "-d", "ghost"], code=1)
        self.assertIn("does not exist", r.stderr)

    def test_glit_dir_never_tracked(self):
        self._expect(["init"])
        self._expect(["add", "."])
        self._expect(["commit", "-m", "empty repo commit is rejected"], code=1)
        # add . 在空仓库（无用户文件）时 index 为空 -> 首提交被拒
        (self.tmp / "f.txt").write_text("1", encoding="utf-8")
        self._expect(["add", "."])
        self._expect(["commit", "-m", "c1"])
        # .glit 不应出现在任何对象里：add . 两次，.glit 下的文件数不应增长
        before = sum(1 for _ in (self.tmp / ".glit" / "objects").rglob("*") if _.is_file())
        self._expect(["add", "."])
        after = sum(1 for _ in (self.tmp / ".glit" / "objects").rglob("*") if _.is_file())
        self.assertEqual(before, after)

    def test_py_module_entry(self):
        r = _run(["--help"], self.tmp)
        self.assertEqual(r.returncode, 0)
        self.assertIn("init", r.stdout)
        for cmd in ("add", "commit", "log", "diff", "checkout", "branch"):
            self.assertIn(cmd, r.stdout)


if __name__ == "__main__":
    unittest.main()
