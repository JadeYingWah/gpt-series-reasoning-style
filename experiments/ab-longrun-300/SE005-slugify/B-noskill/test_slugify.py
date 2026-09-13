"""Tests for slugify — written first against the broken seed (RED)."""
import unittest

from slugify import slugify


class TestSlugify(unittest.TestCase):
    # Spec examples
    def test_hello_world(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    # Collapse consecutive whitespace / punctuation into a single '-'
    def test_collapse_whitespace_and_punct(self):
        self.assertEqual(slugify("Hello   World"), "hello-world")
        self.assertEqual(slugify("Hello---World"), "hello-world")
        self.assertEqual(slugify("Hello , . World"), "hello-world")
        self.assertEqual(slugify("a  \t\n  b"), "a-b")

    # Strip leading / trailing '-'
    def test_strip_leading_trailing_hyphens(self):
        self.assertEqual(slugify("--Hello World--"), "hello-world")
        self.assertEqual(slugify("  !Hello World!  "), "hello-world")
        self.assertEqual(slugify("-a-"), "a")

    # Non alphanumeric (except '-') stripped; empty input -> ""
    def test_empty_string(self):
        self.assertEqual(slugify(""), "")

    def test_pure_punctuation(self):
        self.assertEqual(slugify("!!!"), "")
        self.assertEqual(slugify(" ,.; "), "")

    def test_only_symbols_to_empty_or_hyphens_stripped(self):
        self.assertEqual(slugify("***---***"), "")

    def test_alphanumeric_kept(self):
        self.assertEqual(slugify("abc123"), "abc123")
        self.assertEqual(slugify("a-b"), "a-b")

    # Lowercasing
    def test_lowercases_ascii(self):
        self.assertEqual(slugify("HELLO"), "hello")
        self.assertEqual(slugify("HelloWorld"), "helloworld")

    # Unicode strategy: NFKD + strip combining marks, then lower.
    # Café -> cafe ; Éclair -> eclair. Documented in response.md notes.
    def test_unicode_nfd_ascii_fold(self):
        self.assertEqual(slugify("Café"), "cafe")
        self.assertEqual(slugify("Éclair"), "eclair")
        self.assertEqual(slugify("naïve"), "naive")
        self.assertEqual(slugify("Ünïcödé"), "unicode")

    def test_unicode_mixed_sentence(self):
        self.assertEqual(slugify("Café au Lait!"), "cafe-au-lait")

    # Multiple separators / edge adjacency
    def test_multiple_separator_patterns(self):
        self.assertEqual(slugify("a--b--c"), "a-b-c")
        self.assertEqual(slugify("a - b - c"), "a-b-c")
        self.assertEqual(slugify("_Hello_World_"), "hello-world")

    def test_digits_and_letters_together(self):
        self.assertEqual(slugify("Version 2.0"), "version-2-0")


if __name__ == "__main__":
    unittest.main()
