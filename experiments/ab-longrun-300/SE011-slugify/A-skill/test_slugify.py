"""Tests for slugify — TDD RED then GREEN."""
import unittest

from slugify import slugify


class TestSlugify(unittest.TestCase):
    def test_basic_hello_world(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_lowercases(self):
        self.assertEqual(slugify("ABC"), "abc")
        self.assertEqual(slugify("MiXeD"), "mixed")

    def test_collapse_whitespace_and_punct(self):
        self.assertEqual(slugify("a   b"), "a-b")
        self.assertEqual(slugify("a...b"), "a-b")
        self.assertEqual(slugify("a  --  ,,,  b"), "a-b")
        self.assertEqual(slugify("foo---bar"), "foo-bar")

    def test_strip_leading_trailing_dashes(self):
        self.assertEqual(slugify("---hello---"), "hello")
        self.assertEqual(slugify("!!!hello!!!"), "hello")
        self.assertEqual(slugify("  hello  "), "hello")

    def test_empty_and_pure_separators(self):
        self.assertEqual(slugify(""), "")
        self.assertEqual(slugify("!!!"), "")
        self.assertEqual(slugify("   "), "")
        self.assertEqual(slugify("---"), "")

    def test_digits_kept(self):
        self.assertEqual(slugify("abc 123"), "abc-123")
        self.assertEqual(slugify("v1.2.3"), "v1-2-3")

    def test_unicode_nfkd_strategy(self):
        # Strategy: NFKD normalize then drop non-ASCII combining/base leftovers
        # so Café -> cafe (not café).
        self.assertEqual(slugify("Café"), "cafe")
        self.assertEqual(slugify("naïve"), "naive")
        self.assertEqual(slugify("Ünïcode"), "unicode")
        # CJK / non-decomposable letters are stripped (ASCII slug).
        self.assertEqual(slugify("中文"), "")

    def test_mixed_content(self):
        self.assertEqual(slugify("Hello, World! Café 123"), "hello-world-cafe-123")
        self.assertEqual(slugify("  --Hello,  World!---  "), "hello-world")

    def test_single_word(self):
        self.assertEqual(slugify("hello"), "hello")


if __name__ == "__main__":
    unittest.main()
