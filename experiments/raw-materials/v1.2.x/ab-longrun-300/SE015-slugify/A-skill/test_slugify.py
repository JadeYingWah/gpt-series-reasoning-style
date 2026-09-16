"""Tests for slugify — TDD RED first, then GREEN after fix."""
import unittest

from slugify import slugify


class TestSlugifySpec(unittest.TestCase):
    """Spec: lower, collapse separators to single '-', strip edges, strip non-alnum."""

    def test_basic_punctuation_and_case(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_empty_input(self):
        self.assertEqual(slugify(""), "")

    def test_whitespace_only(self):
        self.assertEqual(slugify("   \t\n  "), "")

    def test_pure_punctuation(self):
        self.assertEqual(slugify("!!!...???"), "")

    def test_strip_leading_trailing_hyphens(self):
        self.assertEqual(slugify("---hello---"), "hello")
        self.assertEqual(slugify("!!Hello!!"), "hello")
        self.assertEqual(slugify("  --Hello--  "), "hello")

    def test_collapse_mixed_separators(self):
        self.assertEqual(slugify("foo   bar---baz!!qux"), "foo-bar-baz-qux")
        self.assertEqual(slugify("a/b\\c.d"), "a-b-c-d")
        self.assertEqual(slugify("one  --  two"), "one-two")

    def test_digits_and_alnum_mix(self):
        self.assertEqual(slugify("abc 123 XYZ"), "abc-123-xyz")
        self.assertEqual(slugify("v1.2.3"), "v1-2-3")

    def test_already_slug(self):
        self.assertEqual(slugify("hello-world"), "hello-world")

    def test_mixed_case_lowered(self):
        self.assertEqual(slugify("HeLLo"), "hello")

    def test_unicode_nfkd_strategy(self):
        """Strategy: NFKD + strip combining marks (Mn) → Café becomes cafe."""
        self.assertEqual(slugify("Café"), "cafe")
        self.assertEqual(slugify("CAFÉ"), "cafe")
        self.assertEqual(slugify("Ünïcödé"), "unicode")
        self.assertEqual(slugify("naïve test"), "naive-test")

    def test_unicode_letters_kept_as_alnum(self):
        """Unicode letters that have no NFKD fold (e.g. CJK) are kept."""
        self.assertEqual(slugify("你好世界"), "你好世界")
        self.assertEqual(slugify("你好 世界!"), "你好-世界")

    def test_only_hyphens(self):
        self.assertEqual(slugify("---"), "")


if __name__ == "__main__":
    unittest.main()
