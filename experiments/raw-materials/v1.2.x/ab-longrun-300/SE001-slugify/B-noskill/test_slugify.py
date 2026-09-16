"""Tests for slugify — TDD RED first, then GREEN after fix."""
import unittest

from slugify import slugify


class TestSlugify(unittest.TestCase):
    def test_hello_world(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_empty_input(self):
        self.assertEqual(slugify(""), "")

    def test_collapse_whitespace_and_punct(self):
        self.assertEqual(slugify("a   b,,,_c"), "a-b-c")
        self.assertEqual(slugify("  many---separators  "), "many-separators")

    def test_strip_leading_trailing_hyphen(self):
        self.assertEqual(slugify("---lead and trail---"), "lead-and-trail")
        self.assertEqual(slugify("!!hello!!"), "hello")

    def test_pure_punctuation(self):
        self.assertEqual(slugify("!!!...***"), "")

    def test_unicode_lower_policy_nFKD(self):
        # Strategy: NFKD normalize then keep ASCII letters/digits.
        # Café -> cafe (é decomposes to e + combining acute, acute dropped).
        self.assertEqual(slugify("Café"), "cafe")

    def test_already_slug(self):
        self.assertEqual(slugify("already-a-slug"), "already-a-slug")

    def test_digits_preserved(self):
        self.assertEqual(slugify("Version 2.0 Release!"), "version-2-0-release")


if __name__ == "__main__":
    unittest.main()
