"""Tests for slugify — Unicode strategy: NFKD + strip combining marks."""
import unittest

from slugify import slugify


class TestSlugify(unittest.TestCase):
    def test_basic_hello_world(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_empty_string(self):
        self.assertEqual(slugify(""), "")

    def test_only_punctuation(self):
        self.assertEqual(slugify("!!!"), "")
        self.assertEqual(slugify("..."), "")
        self.assertEqual(slugify(" -- "), "")

    def test_leading_trailing_symbols(self):
        self.assertEqual(slugify("--Hello--"), "hello")
        self.assertEqual(slugify("  Hello  "), "hello")
        self.assertEqual(slugify("!!!Hello!!!"), "hello")
        self.assertEqual(slugify("-_-Hello-_-"), "hello")

    def test_collapse_multiple_separators(self):
        self.assertEqual(slugify("a   b"), "a-b")
        self.assertEqual(slugify("a,,,b"), "a-b")
        self.assertEqual(slugify("a - b"), "a-b")
        self.assertEqual(slugify("a!!!b???c"), "a-b-c")
        self.assertEqual(slugify("  a  ,,  b  "), "a-b")

    def test_preserves_hyphen_between_words(self):
        self.assertEqual(slugify("already-a-slug"), "already-a-slug")

    def test_numbers_kept(self):
        self.assertEqual(slugify("Item 42"), "item-42")
        self.assertEqual(slugify("v1.2.3"), "v1-2-3")

    def test_unicode_nfkd_strategy(self):
        # NFKD: accents decomposed, combining marks stripped → ASCII
        self.assertEqual(slugify("Café"), "cafe")
        self.assertEqual(slugify("Café au Lait"), "cafe-au-lait")
        self.assertEqual(slugify("naïve"), "naive")
        self.assertEqual(slugify("Über"), "uber")
        self.assertEqual(slugify("señor"), "senor")

    def test_non_letter_non_digit_stripped(self):
        self.assertEqual(slugify("a@b#c"), "a-b-c")
        self.assertEqual(slugify("50% off!"), "50-off")

    def test_underscore_treated_as_separator(self):
        self.assertEqual(slugify("hello_world"), "hello-world")

    def test_already_slug_unchanged(self):
        self.assertEqual(slugify("hello-world"), "hello-world")

    def test_mixed_case_collapses(self):
        self.assertEqual(slugify("HeLLo WoRLD"), "hello-world")

    def test_single_character(self):
        self.assertEqual(slugify("A"), "a")
        self.assertEqual(slugify("!"), "")


if __name__ == "__main__":
    unittest.main()
