"""Tests for slugify — RED first, then GREEN after fix."""
import unittest

from slugify import slugify


class TestSlugify(unittest.TestCase):
    def test_basic_hello_world(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_empty_string(self):
        self.assertEqual(slugify(""), "")

    def test_collapse_whitespace_and_punctuation(self):
        self.assertEqual(slugify("a   b"), "a-b")
        self.assertEqual(slugify("a!!!b"), "a-b")
        self.assertEqual(slugify("a ,. b"), "a-b")
        self.assertEqual(slugify("a---b"), "a-b")

    def test_strip_leading_trailing_hyphens(self):
        self.assertEqual(slugify("--hello--"), "hello")
        self.assertEqual(slugify("  !!Hello!!  "), "hello")
        self.assertEqual(slugify("-a-"), "a")

    def test_strip_non_alnum_except_hyphen(self):
        self.assertEqual(slugify("foo_bar"), "foo-bar")
        self.assertEqual(slugify("foo@bar#baz"), "foo-bar-baz")

    def test_pure_punctuation_returns_empty(self):
        self.assertEqual(slugify("!!!"), "")
        self.assertEqual(slugify("   "), "")
        self.assertEqual(slugify("---"), "")
        self.assertEqual(slugify("@#$%^&*()"), "")

    def test_digits_preserved(self):
        self.assertEqual(slugify("abc 123"), "abc-123")
        self.assertEqual(slugify("42"), "42")

    def test_unicode_nfkd_cafe(self):
        # Strategy: NFKD normalize + strip combining marks → Café becomes cafe
        self.assertEqual(slugify("Café"), "cafe")
        self.assertEqual(slugify("naïve"), "naive")

    def test_unicode_letters_kept_when_no_decomposition(self):
        # Letters without NFKD ASCII decomposition are lowercased and kept
        self.assertEqual(slugify("Über"), "uber")
        self.assertEqual(slugify("Ångström"), "angstrom")

    def test_already_slug(self):
        self.assertEqual(slugify("already-a-slug"), "already-a-slug")

    def test_mixed_case_lowered(self):
        self.assertEqual(slugify("MiXeD CaSe"), "mixed-case")

    def test_single_word(self):
        self.assertEqual(slugify("Python"), "python")


if __name__ == "__main__":
    unittest.main()
