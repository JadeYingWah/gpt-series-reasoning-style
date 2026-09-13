"""Tests for slugify — written before the fix (TDD RED)."""
import unittest

from slugify import slugify


class TestSlugifySpec(unittest.TestCase):
    """Spec cases from task.md."""

    def test_hello_world(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_collapse_whitespace_and_punctuation_to_single_hyphen(self):
        self.assertEqual(slugify("a  b   c"), "a-b-c")
        self.assertEqual(slugify("a, b; c!"), "a-b-c")
        self.assertEqual(slugify("a--b---c"), "a-b-c")
        self.assertEqual(slugify("foo ... bar"), "foo-bar")

    def test_strip_leading_and_trailing_hyphens(self):
        self.assertEqual(slugify("--Hello--"), "hello")
        self.assertEqual(slugify("!!!Hello!!!"), "hello")
        self.assertEqual(slugify("  spaced  "), "spaced")

    def test_non_alphanumeric_stripped(self):
        self.assertEqual(slugify("a@b#c"), "a-b-c")
        self.assertEqual(slugify("price$99"), "price-99")

    def test_empty_string(self):
        self.assertEqual(slugify(""), "")


class TestSlugifyBoundaries(unittest.TestCase):
    """Edge cases required by acceptance checklist."""

    def test_only_whitespace(self):
        self.assertEqual(slugify("   \t\n  "), "")

    def test_only_punctuation(self):
        self.assertEqual(slugify("!!!"), "")
        self.assertEqual(slugify("---"), "")
        self.assertEqual(slugify("..."), "")
        self.assertEqual(slugify("@#$%^&*()"), "")

    def test_only_symbols_with_spaces(self):
        self.assertEqual(slugify(" ! ? . "), "")

    def test_already_slug(self):
        self.assertEqual(slugify("hello-world"), "hello-world")
        self.assertEqual(slugify("abc-123"), "abc-123")

    def test_digits_preserved(self):
        self.assertEqual(slugify("abc123"), "abc123")
        self.assertEqual(slugify("2024-01-01"), "2024-01-01")
        self.assertEqual(slugify("v1.2.3"), "v1-2-3")

    def test_multiple_mixed_separators(self):
        self.assertEqual(slugify("Hello,   World!!  Again"), "hello-world-again")
        self.assertEqual(slugify("---a---b---"), "a-b")

    def test_internal_hyphen_preserved_after_collapse(self):
        self.assertEqual(slugify("well-known fact"), "well-known-fact")


class TestSlugifyUnicode(unittest.TestCase):
    """Unicode strategy: NFKD normalize, strip combining marks, ASCII fold.

    Chosen policy (documented in response.md):
    - Café → cafe (NFKD decomposition, not bare lower)
    - Non-decomposable non-ASCII letters (e.g. CJK) are treated as
      non-alphanumeric and become separators / are stripped.
    """

    def test_accented_latin_nfkd_to_ascii(self):
        self.assertEqual(slugify("Café"), "cafe")
        self.assertEqual(slugify("café"), "cafe")
        self.assertEqual(slugify("naïve"), "naive")
        self.assertEqual(slugify("Über"), "uber")
        self.assertEqual(slugify("résumé"), "resume")
        self.assertEqual(slugify("Ñoño"), "nono")

    def test_unicode_mixed_with_ascii(self):
        self.assertEqual(slugify("Café au Lait!"), "cafe-au-lait")
        self.assertEqual(slugify("Crème Brûlée"), "creme-brulee")

    def test_cjk_becomes_separator(self):
        # After NFKD these remain non-ASCII → separator, then stripped at edges.
        self.assertEqual(slugify("中文"), "")
        self.assertEqual(slugify("hello中文world"), "hello-world")


if __name__ == "__main__":
    unittest.main()
