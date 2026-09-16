"""Tests for slugify — behaviour as specified in task.md.

Unicode strategy under test: NFKD + strip combining marks + ASCII-only slug
(e.g. Café → cafe). A second class of tests covers letters with no
compatible decomposition so the strategy is fully pinned.
"""

import unittest

from slugify import slugify


class TestSlugifySpec(unittest.TestCase):
    def test_hello_world(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_empty_string(self):
        self.assertEqual(slugify(""), "")

    def test_consecutive_whitespace_and_punctuation_collapse(self):
        self.assertEqual(slugify("a   ,,,  b"), "a-b")
        self.assertEqual(slugify("foo  --  bar"), "foo-bar")
        self.assertEqual(slugify("hello!!!world"), "hello-world")

    def test_strip_leading_and_trailing_hyphens(self):
        self.assertEqual(slugify("---hello---"), "hello")
        self.assertEqual(slugify("!!! hello !!!"), "hello")

    def test_non_alnum_stripped_except_hyphen(self):
        self.assertEqual(slugify("a_b$c@d"), "a-b-c-d")
        self.assertEqual(slugify("user_name & email"), "user-name-email")

    def test_pure_punctuation_returns_empty(self):
        self.assertEqual(slugify("!!!"), "")
        self.assertEqual(slugify("   "), "")
        self.assertEqual(slugify("***---***"), "")

    def test_digits_preserved(self):
        self.assertEqual(slugify("Chapter 12: Part 3"), "chapter-12-part-3")

    def test_already_slug_unchanged(self):
        self.assertEqual(slugify("hello-world-2"), "hello-world-2")

    def test_single_word_lowered(self):
        self.assertEqual(slugify("Python"), "python")

    def test_unicode_nfkd_cafe(self):
        # Café uses e + combining acute → NFKD → cafe
        self.assertEqual(slugify("Café"), "cafe")
        self.assertEqual(slugify("Café au Lait!"), "cafe-au-lait")

    def test_unicode_nfkd_ueber(self):
        # Ü is a single precomposed char; NFKD decomposes to U + combining diaeresis
        self.assertEqual(slugify("Über"), "uber")

    def test_unicode_nfkd_angstrom(self):
        # Ångström: Å → A, ö → o
        self.assertEqual(slugify("Ångström"), "angstrom")

    def test_mixed_script_non_decomposable_letter_dropped(self):
        # CJK has no NFKD ASCII form → non-alnum after ASCII filter → stripped
        self.assertEqual(slugify("中文 English"), "english")


if __name__ == "__main__":
    unittest.main()
