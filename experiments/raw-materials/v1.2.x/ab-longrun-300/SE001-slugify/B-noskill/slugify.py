"""Slugify: convert text to a URL-safe slug.

Unicode strategy: NFKD normalize, then keep only ASCII letters/digits.
Accented letters decompose (é -> e + combining mark); marks are dropped.
"""
import re
import unicodedata


def slugify(text: str) -> str:
    if not text:
        return ""
    s = unicodedata.normalize("NFKD", text)
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")
