# -*- coding: utf-8 -*-
"""log 输出测试：空仓库报错、顺序、格式、oneline。"""
import re

from tests.helpers import TempRepoTestCase, run_cli, run_cli_expect


def _three_commits(self) -> list[str]:
    """做 3 次提交，返回 [sha1(旧), sha2, sha3(新)]。"""
    shas = []
    for i, name in enumerate(("a.txt", "b.txt", "c.txt")):
        self.write(name, name)
        run_cli_expect("add", name)
        out = run_cli_expect("commit", "-m", f"commit {i}")
        shas.append(out.split("[main ")[1].split("]")[0])
    return shas


class LogTest(TempRepoTestCase):
    def test_log_empty_repo_errors(self):
        code, _, err = run_cli("log")
        self.assertEqual(code, 1)
        self.assertIn("does not have any commits", err)

    def test_log_order_newest_first(self):
        shas = _three_commits(self)
        out = run_cli_expect("log", "--oneline")
        lines = out.strip().splitlines()
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[0].split()[0], shas[2])
        self.assertEqual(lines[1].split()[0], shas[1])
        self.assertEqual(lines[2].split()[0], shas[0])
        self.assertEqual(lines[0], f"{shas[2][:7]} commit 2")

    def test_log_full_format(self):
        _three_commits(self)
        out = run_cli_expect("log")
        # 行首锚定统计，避免消息文本 "commit 0" 干扰计数
        commit_headers = [l for l in out.splitlines() if l.startswith("commit ")]
        self.assertEqual(len(commit_headers), 3)
        self.assertEqual(out.count("Author: "), 3)
        self.assertEqual(out.count("Date:   "), 3)
        # 消息缩进 4 空格
        self.assertIn("\n    commit 0", out)
        # 新 -> 旧
        self.assertLess(out.index("commit 2"), out.index("commit 0"))

    def test_log_date_is_iso(self):
        _three_commits(self)
        out = run_cli_expect("log")
        m = re.search(r"Date:\s+(\S+)", out)
        self.assertIsNotNone(m)
        self.assertRegex(
            m.group(1), r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$"
        )

    def test_log_multiline_message_indented(self):
        self.write("a.txt", "A")
        run_cli_expect("add", "a.txt")
        run_cli_expect("commit", "-m", "subject\n\nbody line")
        out = run_cli_expect("log")
        self.assertIn("    subject", out)
        self.assertIn("    body line", out)


if __name__ == "__main__":
    unittest.main()
