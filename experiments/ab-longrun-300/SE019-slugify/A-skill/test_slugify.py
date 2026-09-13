"""Tests for slugify.

Unicode strategy (documented per task):
  NFKD-decompose, drop combining marks, then lowercase.
  "Café" -> "cafe" (not "café"). Non-ASCII letters without
  combining marks (e.g. CJK) are kept as-is after lower().
"""
import unittest

from slugify import slugify


class TestSlugifySpec(unittest.TestCase):
    def test_hello_world(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_collapse_runs(self):
        self.assertEqual(slugify("a  ---  b!!!c"), "a-b-c")
        self.assertEqual(slugify("foo   bar\tbaz"), "foo-bar-baz")

    def test_strip_edges(self):
        self.assertEqual(slugify("--Hello--"), "hello")
        self.assertEqual(slugify("!!Hello??"), "hello")
        self.assertEqual(slugify("  spaced  "), "spaced")

    def test_non_alnum_stripped(self):
        self.assertEqual(slugify("a@b#c$d"), "a-b-c-d")
        self.assertEqual(slugify("path/to/file.txt"), "path-to-file-txt")

    def test_empty_and_punct_only(self):
        self.assertEqual(slugify(""), "")
        self.assertEqual(slugify("   "), "")
        self.assertEqual(slugify("!!!"), "")
        self.assertEqual(slugify(" - "), "")

    def test_digits_kept(self):
        self.assertEqual(slugify("Chapter 12!"), "chapter-12")
        self.assertEqual(slugify("v1.2.3"), "v1-2-3")

    def test_unicode_nfkd_fold(self):
        # NFKD strategy: accents stripped
        self.assertEqual(slugify("Café"), "cafe")
        self.assertEqual(slugify("naïve"), "naive")
        self.assertEqual(slugify("Ångström"), "angstrom")
        self.assertEqual(slugify("Ünïcödé Slüg"), "unicode-slug")

    def test_unicode_letters_kept_when_no_mark(self):
        # CJK has no NFKD combining-mark strip; lower() leaves them
        self.assertEqual(slugify("中文标题"), "中文标题")
        self.assertEqual(slugify("日本語 Test"), "日本語-test")

    def test_mixed_word(self):
        self.assertEqual(slugify("Hello World Example"), "hello-world-example")
        self.assertEqual(slugify("Already-slugged"), "already-slugged")


if __name__ == "__main__":
    unittest.main()
