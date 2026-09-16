"""Tests for slugify — run before and after the fix."""
import unittest

from slugify import slugify


class TestSlugify(unittest.TestCase):
    def test_basic_phrase(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_empty_string(self):
        self.assertEqual(slugify(""), "")

    def test_pure_punctuation(self):
        self.assertEqual(slugify("!!!"), "")
        self.assertEqual(slugify("...---..."), "")

    def test_leading_trailing_symbols_stripped(self):
        self.assertEqual(slugify("  --Hello--  "), "hello")
        self.assertEqual(slugify("!!!world!!!"), "world")
        self.assertEqual(slugify("---"), "")

    def test_collapse_multiple_separators(self):
        self.assertEqual(slugify("a   b"), "a-b")
        self.assertEqual(slugify("a, b  c!!d"), "a-b-c-d")
        self.assertEqual(slugify("one---two---three"), "one-two-three")

    def test_preserves_existing_hyphen_between_words(self):
        self.assertEqual(slugify("well-known"), "well-known")

    def test_digits_kept(self):
        self.assertEqual(slugify("Chapter 42"), "chapter-42")

    def test_unicode_nfkd(self):
        # NFKD strategy: Café -> cafe (decomposed, diacritic stripped)
        self.assertEqual(slugify("Café"), "cafe")
        self.assertEqual(slugify("naïve café"), "naive-cafe")
        self.assertEqual(slugify("ÅNGSTRÖM"), "angstrom")

    def test_unicode_nfkd_empty_after_decomposition(self):
        # symbols-only via combining marks edge
        self.assertEqual(slugify("  "), "")


if __name__ == "__main__":
    unittest.main()
