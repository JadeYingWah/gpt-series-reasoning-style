"""Tests for slugify — Unicode strategy: NFKD decomposition then ASCII keep."""
import unittest

from slugify import slugify


class TestSlugifyBasic(unittest.TestCase):
    def test_hello_world(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_simple_word(self):
        self.assertEqual(slugify("Hello"), "hello")

    def test_already_slug(self):
        self.assertEqual(slugify("already-a-slug"), "already-a-slug")

    def test_empty_string(self):
        self.assertEqual(slugify(""), "")

    def test_none_like_empty(self):
        # empty / whitespace-only
        self.assertEqual(slugify("   "), "")
        self.assertEqual(slugify("\t\n"), "")


class TestSlugifyCollapse(unittest.TestCase):
    def test_consecutive_whitespace_collapses(self):
        self.assertEqual(slugify("a   b"), "a-b")

    def test_consecutive_punctuation_collapses(self):
        self.assertEqual(slugify("a!!!b"), "a-b")

    def test_mixed_whitespace_punctuation_collapses(self):
        self.assertEqual(slugify("a ,. b"), "a-b")

    def test_multiple_separators(self):
        self.assertEqual(slugify("foo---bar...baz"), "foo-bar-baz")

    def test_word_with_spaces_and_commas(self):
        self.assertEqual(slugify("Hello ,  World"), "hello-world")


class TestSlugifyStripEdges(unittest.TestCase):
    def test_leading_symbols(self):
        self.assertEqual(slugify("!!!Hello"), "hello")

    def test_trailing_symbols(self):
        self.assertEqual(slugify("Hello!!!"), "hello")

    def test_both_edges(self):
        self.assertEqual(slugify("--Hello--"), "hello")

    def test_leading_trailing_whitespace(self):
        self.assertEqual(slugify("  Hello  "), "hello")

    def test_pure_punctuation(self):
        self.assertEqual(slugify("!!!"), "")

    def test_pure_symbols_and_spaces(self):
        self.assertEqual(slugify(" - - - "), "")


class TestSlugifyUnicode(unittest.TestCase):
    """Strategy: NFKD decompose then keep only ASCII alnum → Café → cafe."""

    def test_cafe_nfd_decomposes(self):
        self.assertEqual(slugify("Café"), "cafe")

    def test_naive_with_diaeresis(self):
        self.assertEqual(slugify("naïve"), "naive")

    def test_cyrillic_stripped(self):
        # NFKD leaves Cyrillic as non-ASCII → stripped
        self.assertEqual(slugify("Привет"), "")

    def test_mixed_unicode_and_ascii(self):
        self.assertEqual(slugify("Café au Lait"), "cafe-au-lait")

    def test_ligature_nfd(self):
        # ﬁ (U+FB01) NFKD → fi
        self.assertEqual(slugify("ﬁle"), "file")


class TestSlugifyDigits(unittest.TestCase):
    def test_digits_kept(self):
        self.assertEqual(slugify("Chapter 12"), "chapter-12")

    def test_alphanumeric_mix(self):
        self.assertEqual(slugify("abc123"), "abc123")

    def test_underscores_become_sep(self):
        self.assertEqual(slugify("foo_bar"), "foo-bar")


if __name__ == "__main__":
    unittest.main()
