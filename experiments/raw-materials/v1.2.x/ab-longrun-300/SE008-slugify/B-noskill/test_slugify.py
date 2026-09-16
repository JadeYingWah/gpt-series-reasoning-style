"""Tests for slugify — RED first, then GREEN after fix."""
import unittest

from slugify import slugify


class TestSlugify(unittest.TestCase):
    # Spec examples
    def test_hello_world(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_collapse_whitespace_and_punctuation(self):
        self.assertEqual(slugify("foo   bar"), "foo-bar")
        self.assertEqual(slugify("foo,,,bar"), "foo-bar")
        self.assertEqual(slugify("foo -- bar !! baz"), "foo-bar-baz")

    def test_strip_leading_trailing_hyphens(self):
        self.assertEqual(slugify("--hello--"), "hello")
        self.assertEqual(slugify("!!!hello!!!"), "hello")
        self.assertEqual(slugify("  hello  "), "hello")

    def test_non_alnum_stripped(self):
        self.assertEqual(slugify("a@b#c"), "a-b-c")
        self.assertEqual(slugify("path/to/file"), "path-to-file")

    def test_empty_string(self):
        self.assertEqual(slugify(""), "")

    def test_pure_punctuation(self):
        self.assertEqual(slugify("!!!...???"), "")
        self.assertEqual(slugify("---"), "")

    def test_unicode_nfd_lowercase(self):
        # Strategy: NFKD + ASCII fold → cafe (not café)
        self.assertEqual(slugify("Café"), "cafe")
        self.assertEqual(slugify("Ñoño"), "nono")

    def test_already_slug(self):
        self.assertEqual(slugify("already-a-slug"), "already-a-slug")

    def test_numbers_preserved(self):
        self.assertEqual(slugify("Chapter 42: The End"), "chapter-42-the-end")

    def test_single_word(self):
        self.assertEqual(slugify("Python"), "python")


if __name__ == "__main__":
    unittest.main()
