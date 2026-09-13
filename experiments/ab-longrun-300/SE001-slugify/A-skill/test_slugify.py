"""Tests for slugify — written before the fix (RED first)."""
import unittest

from slugify import slugify


class TestSlugifySpec(unittest.TestCase):
    """Spec cases from task.md."""

    def test_hello_world(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_empty_string(self):
        self.assertEqual(slugify(""), "")

    def test_lowercases_ascii(self):
        self.assertEqual(slugify("ABC Def"), "abc-def")

    def test_collapses_whitespace_and_punctuation_to_single_hyphen(self):
        self.assertEqual(slugify("a   b"), "a-b")
        self.assertEqual(slugify("a,,,b"), "a-b")
        self.assertEqual(slugify("a , b !!! c"), "a-b-c")
        self.assertEqual(slugify("a--b"), "a-b")

    def test_strips_leading_and_trailing_hyphens(self):
        self.assertEqual(slugify("  Hello  "), "hello")
        self.assertEqual(slugify("!!Hello!!"), "hello")
        self.assertEqual(slugify("-Hello-"), "hello")
        self.assertEqual(slugify("--Hello--"), "hello")

    def test_pure_punctuation_returns_empty(self):
        self.assertEqual(slugify("!!!"), "")
        self.assertEqual(slugify("   "), "")
        self.assertEqual(slugify("-"), "")
        self.assertEqual(slugify("--- ---"), "")

    def test_only_alphanumeric_and_hyphen_survive(self):
        # letters/digits kept; everything else becomes a single separator
        self.assertEqual(slugify("a_b"), "a-b")  # underscore is not alnum
        self.assertEqual(slugify("a@b#c"), "a-b-c")
        self.assertEqual(slugify("foo/bar\\baz"), "foo-bar-baz")

    def test_digits_preserved(self):
        self.assertEqual(slugify("Python 3.14"), "python-3-14")
        self.assertEqual(slugify("v2"), "v2")


class TestSlugifyUnicode(unittest.TestCase):
    """Unicode strategy: NFKD + strip combining marks → ASCII slug.

    Café → cafe (NFKD: C a f e + combining acute; drop the mark).
    Chosen because URL-safe ASCII slugs are the common slugify convention.
    """

    def test_cafe_nfkd_ascii(self):
        self.assertEqual(slugify("Café"), "cafe")

    def test_naive_with_diaeresis(self):
        self.assertEqual(slugify("naïve"), "naive")

    def test_greek_alpha_is_not_ascii_folding_to_letter(self):
        # Greek letters are letters under NFKD but not Latin; after
        # "keep only a-z0-9" they disappear → empty separators collapse.
        # Documenting the boundary of the ASCII strategy.
        self.assertEqual(slugify("αβγ"), "")

    def test_cyrillic_dropped_like_greek(self):
        self.assertEqual(slugify("привет"), "")

    def test_mixed_unicode_word(self):
        self.assertEqual(slugify("Über-Cool Café!"), "uber-cool-cafe")

    def test_fullwidth_digits_folded(self):
        # NFKD maps fullwidth digits to ASCII digits
        self.assertEqual(slugify("１２３"), "123")


class TestSlugifyBoundaries(unittest.TestCase):
    """Extra edge cases beyond the minimal happy path."""

    def test_single_char(self):
        self.assertEqual(slugify("a"), "a")
        self.assertEqual(slugify("!"), "")

    def test_long_separator_run(self):
        self.assertEqual(slugify("a!!!###___b"), "a-b")

    def test_leading_digits_ok(self):
        self.assertEqual(slugify("42 is the answer"), "42-is-the-answer")

    def test_none_like_empty_after_strip(self):
        self.assertEqual(slugify("..."), "")


if __name__ == "__main__":
    unittest.main()
