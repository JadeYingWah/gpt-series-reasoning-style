"""Tests for slugify — RED first, then GREEN after fix.

Unicode strategy (NFKD + ASCII fold):
  Letters with diacritics are NFKD-decomposed and combining marks stripped,
  so Café → cafe. Characters that cannot be folded to [a-z0-9] become
  separators (then collapsed/stripped), so Straße → stra-e and CJK is removed.
"""
import unittest

from slugify import slugify


class TestSlugifySpec(unittest.TestCase):
    # --- happy path / core examples from task.md ---
    def test_hello_world(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_simple_words(self):
        self.assertEqual(slugify("foo bar baz"), "foo-bar-baz")

    # --- collapse consecutive whitespace / punctuation ---
    def test_collapse_spaces(self):
        self.assertEqual(slugify("a   b"), "a-b")

    def test_collapse_mixed_punct_and_space(self):
        self.assertEqual(slugify("a, b! c?"), "a-b-c")

    def test_collapse_many_separators(self):
        self.assertEqual(slugify("foo--bar"), "foo-bar")
        self.assertEqual(slugify("foo!!!bar"), "foo-bar")
        self.assertEqual(slugify("foo , bar"), "foo-bar")

    # --- strip leading / trailing hyphens ---
    def test_strip_leading_symbols(self):
        self.assertEqual(slugify("--Hello"), "hello")

    def test_strip_trailing_symbols(self):
        self.assertEqual(slugify("World!!"), "world")

    def test_strip_both(self):
        self.assertEqual(slugify("-- Hello World --"), "hello-world")

    # --- empty / degenerate inputs ---
    def test_empty_string(self):
        self.assertEqual(slugify(""), "")

    def test_only_whitespace(self):
        self.assertEqual(slugify("   "), "")

    def test_only_punctuation(self):
        self.assertEqual(slugify("!!!???"), "")

    def test_only_symbols(self):
        self.assertEqual(slugify("@#$%^&*()"), "")

    # --- digits and mixed alnum ---
    def test_digits_kept(self):
        self.assertEqual(slugify("Python 3.12"), "python-3-12")

    def test_alnum_join(self):
        self.assertEqual(slugify("v2.0.1"), "v2-0-1")

    # --- Unicode: NFKD fold (Café → cafe) ---
    def test_unicode_nfd_fold_cafe(self):
        self.assertEqual(slugify("Café"), "cafe")

    def test_unicode_nfd_fold_naive(self):
        self.assertEqual(slugify("naïve"), "naive")

    def test_unicode_nfd_fold_german_ess(self):
        # NFKD leaves ß as-is (not "ss"). Non-ASCII becomes a separator,
        # then collapse/strip → "stra-e".
        self.assertEqual(slugify("Straße"), "stra-e")

    def test_unicode_cjk_stripped(self):
        # CJK has no NFKD ASCII fold → stripped.
        self.assertEqual(slugify("你好世界 hello"), "hello")

    def test_unicode_mixed(self):
        self.assertEqual(slugify("Café au lait!"), "cafe-au-lait")


if __name__ == "__main__":
    unittest.main()
