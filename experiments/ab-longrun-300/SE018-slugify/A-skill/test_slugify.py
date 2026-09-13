"""Tests for slugify — RED first, then GREEN after fix."""
import unittest

from slugify import slugify


class TestSlugify(unittest.TestCase):
    def test_hello_world(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_empty_string(self):
        self.assertEqual(slugify(""), "")

    def test_pure_punctuation(self):
        self.assertEqual(slugify("!!!"), "")
        self.assertEqual(slugify("---"), "")

    def test_leading_trailing_symbols(self):
        self.assertEqual(slugify("--Hello--"), "hello")
        self.assertEqual(slugify("  Hello  "), "hello")
        self.assertEqual(slugify("!!Hello!!"), "hello")

    def test_collapse_whitespace_and_punctuation(self):
        self.assertEqual(slugify("a   b"), "a-b")
        self.assertEqual(slugify("a---b"), "a-b")
        self.assertEqual(slugify("a, b! c?"), "a-b-c")
        self.assertEqual(slugify("  spaced   out  "), "spaced-out")

    def test_digits_preserved(self):
        self.assertEqual(slugify("Python 3.12"), "python-3-12")

    def test_unicode_nfkd_strategy(self):
        """NFKD strategy: diacritics stripped, then lowercased."""
        self.assertEqual(slugify("Café"), "cafe")
        self.assertEqual(slugify("naïve"), "naive")
        self.assertEqual(slugify("Über"), "uber")
        self.assertEqual(slugify("crème brûlée"), "creme-brulee")

    def test_already_slug(self):
        self.assertEqual(slugify("already-a-slug"), "already-a-slug")

    def test_mixed_case_and_spaces(self):
        self.assertEqual(slugify("The Quick Brown Fox"), "the-quick-brown-fox")


if __name__ == "__main__":
    unittest.main()
