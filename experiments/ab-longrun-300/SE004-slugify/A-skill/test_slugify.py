"""Tests for slugify — written RED against the broken seed, kept for GREEN."""
import unittest

from slugify import slugify


class TestSlugify(unittest.TestCase):
    def test_hello_world(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_empty_string(self):
        self.assertEqual(slugify(""), "")

    def test_collapse_runs_of_whitespace_and_punctuation(self):
        self.assertEqual(slugify("a   b"), "a-b")
        self.assertEqual(slugify("a!!!b"), "a-b")
        self.assertEqual(slugify("a ,. b"), "a-b")
        self.assertEqual(slugify("a\n\t b"), "a-b")

    def test_strip_leading_and_trailing_separators(self):
        self.assertEqual(slugify("--Hello--"), "hello")
        self.assertEqual(slugify("!!Hello!!"), "hello")
        self.assertEqual(slugify("  Hello  "), "hello")

    def test_non_alnum_stripped(self):
        self.assertEqual(slugify("foo@bar#baz"), "foo-bar-baz")
        self.assertEqual(slugify("C++ / Python"), "c-python")

    def test_only_punctuation(self):
        self.assertEqual(slugify("!!!"), "")
        self.assertEqual(slugify("   "), "")
        self.assertEqual(slugify("---"), "")

    def test_already_slugish(self):
        self.assertEqual(slugify("hello-world"), "hello-world")

    def test_unicode_nfkd_strategy(self):
        # Strategy: NFKD + drop combining marks, then lower.
        # Café -> cafe ; Ünïcödé -> unicode ; naïve -> naive
        self.assertEqual(slugify("Café"), "cafe")
        self.assertEqual(slugify("Ünïcödé"), "unicode")
        self.assertEqual(slugify("naïve"), "naive")

    def test_unicode_cjk_passthrough_as_non_alnum(self):
        # CJK letters are not ASCII alnum; under NFKD-strip they are
        # removed (only [A-Za-z0-9] survive). Documented choice.
        self.assertEqual(slugify("中文"), "")

    def test_mixed_content(self):
        self.assertEqual(slugify("  My Café — Menu! 2024  "), "my-cafe-menu-2024")


if __name__ == "__main__":
    unittest.main()
