"""Tests for slugify — RED first, then GREEN after fix.

Unicode strategy (documented): NFKD decomposition + strip combining marks,
so accented Latin letters become ASCII (Café → cafe).
"""
import pytest

from slugify import slugify


class TestBasic:
    def test_hello_world(self):
        assert slugify("Hello, World!") == "hello-world"

    def test_already_slug(self):
        assert slugify("hello-world") == "hello-world"

    def test_lowercases(self):
        assert slugify("Hello") == "hello"
        assert slugify("ABC Def") == "abc-def"


class TestCollapseAndStrip:
    def test_collapse_whitespace(self):
        assert slugify("a   b") == "a-b"
        assert slugify("a\t\nb") == "a-b"

    def test_collapse_punctuation_run(self):
        assert slugify("a!!!b") == "a-b"
        assert slugify("a,.;:b") == "a-b"
        assert slugify("a ,.;: b") == "a-b"

    def test_mixed_separators(self):
        assert slugify("a -- b") == "a-b"
        assert slugify("foo___bar") == "foo-bar"

    def test_strip_leading_trailing(self):
        assert slugify("--hello--") == "hello"
        assert slugify("!!!hello!!!") == "hello"
        assert slugify("  hello  ") == "hello"
        assert slugify("---") == ""
        assert slugify("!!!") == ""


class TestEdgeCases:
    def test_empty_string(self):
        assert slugify("") == ""

    def test_pure_punctuation(self):
        assert slugify("...") == ""
        assert slugify("?!@#$%^&*()") == ""
        assert slugify(" \t\n ") == ""

    def test_leading_trailing_symbols(self):
        assert slugify("***lead and trail***") == "lead-and-trail"
        assert slugify("!!!") == ""
        assert slugify("_-_-hello-_-_") == "hello"

    def test_multiple_separators_between_words(self):
        assert slugify("one,, two -- three!! four") == "one-two-three-four"
        assert slugify("a---b---c") == "a-b-c"

    def test_digits_kept(self):
        assert slugify("Item 42") == "item-42"
        assert slugify("v1.2.3") == "v1-2-3"


class TestUnicodeNfkd:
    """NFKD strategy: accents stripped to ASCII base letters."""

    def test_cafe(self):
        assert slugify("Café") == "cafe"

    def test_nacl(self):
        assert slugify("naïve") == "naive"

    def test_german_ish(self):
        # ü → u under NFKD (not ss); document strategy choice
        assert slugify("Über") == "uber"

    def test_mixed_unicode_sentence(self):
        assert slugify("Crème Brûlée") == "creme-brulee"

    def test_non_latin_stripped(self):
        # CJK / symbols are non-ASCII-alnum → separators / empty
        assert slugify("你好") == ""
        assert slugify("日本語") == ""
        assert slugify("hello 你好 world") == "hello-world"
