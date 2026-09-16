"""Tests for slugify. Unicode strategy: NFKD fold (Café -> cafe)."""
import unittest

from slugify import slugify


class TestSlugify(unittest.TestCase):
    def test_basic_sentence(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_consecutive_whitespace_and_punct_collapse(self):
        self.assertEqual(slugify("a   b"), "a-b")
        self.assertEqual(slugify("a,,, b!!!"), "a-b")
        self.assertEqual(slugify("  --  "), "")

    def test_strip_leading_trailing_hyphens(self):
        self.assertEqual(slugify("---Hello---"), "hello")
        self.assertEqual(slugify("!!!Hello!!!"), "hello")
        self.assertEqual(slugify(" Hello "), "hello")

    def test_empty_and_pure_punct(self):
        self.assertEqual(slugify(""), "")
        self.assertEqual(slugify("!!!"), "")
        self.assertEqual(slugify("   \t\n  "), "")

    def test_alphanumeric_and_hyphen_passthrough(self):
        self.assertEqual(slugify("foo-bar_42"), "foo-bar-42")
        self.assertEqual(slugify("abc123"), "abc123")

    def test_unicode_nfkd_fold(self):
        # Strategy: NFKD then drop non-ASCII — Café -> cafe
        self.assertEqual(slugify("Café"), "cafe")
        self.assertEqual(slugify("Ünïcödé"), "unicode")
        self.assertEqual(slugify("naïve café"), "naive-cafe")

    def test_already_slug(self):
        self.assertEqual(slugify("already-a-slug"), "already-a-slug")

    def test_mixed_case_lowered(self):
        self.assertEqual(slugify("MiXeD CaSe"), "mixed-case")


if __name__ == "__main__":
    unittest.main()
