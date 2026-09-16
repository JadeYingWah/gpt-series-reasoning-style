"""CLI 端到端测试：以子进程方式跑真实命令行（覆盖 argparse 与退出码）。"""

import os
import tempfile
import unittest

from .helpers import run_cli


class CLITest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="gitlite-cli-")

    def tearDown(self):
        import shutil

        shutil.rmtree(self.tmp, ignore_errors=True)

    def w(self, rel, content):
        p = os.path.join(self.tmp, *rel.split("/"))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="") as f:
            f.write(content)
        return p

    def r(self, rel):
        p = os.path.join(self.tmp, *rel.split("/"))
        if not os.path.exists(p):
            return None
        with open(p, "r", encoding="utf-8", newline="") as f:
            return f.read()

    # ------------------------------------------------------------------

    def test_full_workflow(self):
        # init
        r = run_cli(self.tmp, "init")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("initialized empty gitlite repository", r.stdout)
        # 重复 init 幂等
        r = run_cli(self.tmp, "init")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("reinitialized", r.stdout)

        # add + commit
        self.w("a.txt", "hello v1\n")
        self.w("src/main.py", "print('hi')\n")
        r = run_cli(self.tmp, "add", ".")
        self.assertEqual(r.returncode, 0, r.stderr)
        r = run_cli(self.tmp, "commit", "-m", "first commit")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("[main", r.stdout)

        # log
        r = run_cli(self.tmp, "log")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("commit ", r.stdout)
        self.assertIn("first commit", r.stdout)
        self.assertIn("Test Author <author@example.com>", r.stdout)

        # branch + checkout
        r = run_cli(self.tmp, "branch", "dev")
        self.assertEqual(r.returncode, 0, r.stderr)
        r = run_cli(self.tmp, "checkout", "dev")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("switched to branch 'dev'", r.stdout)

        # 在 dev 上提交
        self.w("b.txt", "dev file\n")
        r = run_cli(self.tmp, "add", "b.txt")
        self.assertEqual(r.returncode, 0, r.stderr)
        r = run_cli(self.tmp, "commit", "-m", "dev commit")
        self.assertEqual(r.returncode, 0, r.stderr)

        # 切回 main：b.txt 消失
        r = run_cli(self.tmp, "checkout", "main")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIsNone(self.r("b.txt"))
        # 切回 dev：b.txt 回来
        r = run_cli(self.tmp, "checkout", "dev")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.r("b.txt"), "dev file\n")

        # diff（工作区修改）
        self.w("b.txt", "dev file v2\n")
        r = run_cli(self.tmp, "diff")
        self.assertEqual(r.returncode, 1)  # 有差异 -> 退出码 1
        self.assertIn("-dev file", r.stdout)
        self.assertIn("+dev file v2", r.stdout)

        # checkout -- 恢复
        r = run_cli(self.tmp, "checkout", "--", "b.txt")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.r("b.txt"), "dev file\n")

        # diff --staged
        self.w("c.txt", "new staged\n")
        r = run_cli(self.tmp, "add", "c.txt")
        self.assertEqual(r.returncode, 0, r.stderr)
        r = run_cli(self.tmp, "diff", "--staged")
        self.assertEqual(r.returncode, 1)
        self.assertIn("+new staged", r.stdout)
        # 提交后再切换（暂存未提交的变更会被 checkout 拒绝）
        r = run_cli(self.tmp, "commit", "-m", "dev staged file")
        self.assertEqual(r.returncode, 0, r.stderr)

        # branch 列表
        r = run_cli(self.tmp, "branch")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("* dev", r.stdout)
        self.assertIn("main", r.stdout)

        # 切回 main 后: dev 含 main 没有的提交 -> -d 拒绝, -D 成功
        r = run_cli(self.tmp, "checkout", "main")
        self.assertEqual(r.returncode, 0, r.stderr)
        r = run_cli(self.tmp, "branch", "-d", "dev")
        self.assertEqual(r.returncode, 1)
        self.assertIn("error", r.stderr)
        r = run_cli(self.tmp, "branch", "-D", "dev")
        self.assertEqual(r.returncode, 0, r.stderr)
        r = run_cli(self.tmp, "branch")
        self.assertNotIn("dev", r.stdout)
        self.assertIn("* main", r.stdout)

    def test_detached_checkout_via_cli(self):
        run_cli(self.tmp, "init")
        self.w("a.txt", "1\n")
        run_cli(self.tmp, "add", "a.txt")
        run_cli(self.tmp, "commit", "-m", "c1")
        import subprocess
        import sys

        # 取完整 hash（通过 log 输出解析）
        r = run_cli(self.tmp, "log")
        oid = r.stdout.split("commit ")[1].split("\n")[0].strip()
        r = run_cli(self.tmp, "checkout", oid[:8])
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("detached", r.stdout)
        r = run_cli(self.tmp, "checkout", "main")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_error_cases_exit_1(self):
        run_cli(self.tmp, "init")
        # 空仓库 commit
        r = run_cli(self.tmp, "commit", "-m", "x")
        self.assertEqual(r.returncode, 1)
        self.assertIn("nothing to commit", r.stdout)
        # 空仓库 log
        r = run_cli(self.tmp, "log")
        self.assertEqual(r.returncode, 1)
        self.assertIn("error", r.stderr)
        # add 不存在的文件
        r = run_cli(self.tmp, "add", "ghost.txt")
        self.assertEqual(r.returncode, 1)
        self.assertIn("error", r.stderr)
        # checkout 不存在的分支
        self.w("a.txt", "1\n")
        run_cli(self.tmp, "add", "a.txt")
        run_cli(self.tmp, "commit", "-m", "c1")
        r = run_cli(self.tmp, "checkout", "ghost")
        self.assertEqual(r.returncode, 1)
        self.assertIn("error", r.stderr)
        # 无 -m 的 commit
        r = run_cli(self.tmp, "commit")
        self.assertEqual(r.returncode, 2)  # argparse 参数错误

    def test_init_in_new_directory(self):
        target = os.path.join(self.tmp, "fresh-repo")
        r = run_cli(self.tmp, "init", "fresh-repo")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(
            os.path.isdir(os.path.join(target, ".gitlite", "objects"))
        )

    def test_run_from_subdirectory(self):
        # 在仓库子目录内执行命令也应正确定位仓库根
        run_cli(self.tmp, "init")
        self.w("sub/inner.txt", "data\n")
        r = run_cli(os.path.join(self.tmp, "sub"), "add", "inner.txt")
        self.assertEqual(r.returncode, 0, r.stderr)
        r = run_cli(os.path.join(self.tmp, "sub"), "commit", "-m", "from subdir")
        self.assertEqual(r.returncode, 0, r.stderr)
        r = run_cli(os.path.join(self.tmp, "sub"), "log")
        self.assertIn("from subdir", r.stdout)


if __name__ == "__main__":
    unittest.main()
