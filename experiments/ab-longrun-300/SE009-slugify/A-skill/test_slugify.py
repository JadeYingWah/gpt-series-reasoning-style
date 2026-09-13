"""Tests for slugify — written before the fix (RED)."""
import unittest

from slugify import slugify


class TestSlugify(unittest.TestCase):
    # Core example from the spec
    def test_hello_world(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    # Collapse consecutive whitespace / punctuation into a single hyphen
    def test_collapse_whitespace(self):
        self.assertEqual(slugify("hello   world"), "hello-world")
        self.assertEqual(slugify("hello \t\n world"), "hello-world")

    def test_collapse_punctuation(self):
        self.assertEqual(slugify("hello!!!world"), "hello-world")
        self.assertEqual(slugify("hello ,.; world"), "hello-world")

    def test_mixed_separators(self):
        self.assertEqual(slugify("a  --  b"), "a-b")
        self.assertEqual(slugify("foo/bar\\baz"), "foo-bar-baz")

    # Strip leading / trailing hyphens
    def test_strip_leading_trailing(self):
        self.assertEqual(slugify("---hello---"), "hello")
        self.assertEqual(slugify("  !Hello, World!  "), "hello-world")

    # Non-alphanumeric stripped; empty input returns ""
    def test_empty_string(self):
        self.assertEqual(slugify(""), "")

    def test_pure_punctuation(self):
        self.assertEqual(slugify("!!!"), "")
        self.assertEqual(slugify("   \t  "), "")
        self.assertEqual(slugify("...---..."), "")

    def test_numbers_kept(self):
        self.assertEqual(slugify("Python 3.12"), "python-3-12")

    def test_already_slug(self):
        self.assertEqual(slugify("already-a-slug"), "already-a-slug")

    # Unicode policy: NFKD + strip combining marks + ASCII fold
    # Café -> cafe (not café)
    def test_unicode_nfkd_ascii_fold(self):
        self.assertEqual(slugify("Café"), "cafe")
        self.assertEqual(slugify("Ünïcödé"), "unicode")
        self.assertEqual(slugify("naïve"), "naive")

    def test_unicode_cjk_dropped_or_folded(self):
        # CJK has no NFKD ASCII fold; non-ASCII letters are removed after fold
        # so pure CJK collapses to empty (documented policy).
        self.assertEqual(slugify("中文"), "")
        self.assertEqual(slugify("日本語 test"), "test")

    def test_unicode_mixed_with_ascii(self):
        self.assertEqual(slugify("Café Crème!"), "cafe-creme")
        self.assertEqual(slugify("Ångström-unit"), "angstrom-unit")


if __name__ == "__main__":
    unittest.main()
