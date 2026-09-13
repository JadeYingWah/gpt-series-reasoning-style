"""Tests for slugify — Unicode strategy: NFKD + drop combining marks.

Café → cafe (deaccented ASCII fold), not café.
"""
import unittest

from slugify import slugify


class TestSlugify(unittest.TestCase):
    def test_hello_world(self):
        self.assertEqual(slugify("Hello, World!"), "hello-world")

    def test_empty_string(self):
        self.assertEqual(slugify(""), "")

    def test_pure_punctuation(self):
        self.assertEqual(slugify("!!!"), "")
        self.assertEqual(slugify("...---..."), "")

    def test_collapse_whitespace_and_punct(self):
        self.assertEqual(slugify("a   b"), "a-b")
        self.assertEqual(slugify("a,,,b"), "a-b")
        self.assertEqual(slugify("a - b"), "a-b")
        self.assertEqual(slugify("a!!b??c"), "a-b-c")
        self.assertEqual(slugify("  lots   of\t--separators  "), "lots-of-separators")

    def test_strip_leading_trailing_separators(self):
        self.assertEqual(slugify("--Hello--"), "hello")
        self.assertEqual(slugify("!!!Hello!!!"), "hello")
        self.assertEqual(slugify("  Hello  "), "hello")
        self.assertEqual(slugify("-.-.-"), "")

    def test_non_alnum_stripped(self):
        self.assertEqual(slugify("foo@bar#baz"), "foo-bar-baz")
        self.assertEqual(slugify("path/to/file"), "path-to-file")

    def test_unicode_nfkd_fold(self):
        # NFKD strategy: accents stripped → ASCII
        self.assertEqual(slugify("Café"), "cafe")
        self.assertEqual(slugify("naïve"), "naive")
        self.assertEqual(slugify("Über"), "uber")
        self.assertEqual(slugify("Ångström"), "angstrom")
        self.assertEqual(slugify("résumé"), "resume")

    def test_mixed_case_and_digits(self):
        self.assertEqual(slugify("Python3.12"), "python3-12")
        self.assertEqual(slugify("ABC_xyz"), "abc-xyz")

    def test_only_unicode_letters(self):
        self.assertEqual(slugify("Ñoño"), "nono")
        self.assertEqual(slugify("Été"), "ete")


if __name__ == "__main__":
    unittest.main()
