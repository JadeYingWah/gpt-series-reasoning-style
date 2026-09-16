"""Slugify text to a URL-safe ASCII slug.

Unicode strategy: NFKD normalization + drop combining marks (Mn),
so accents fold to base ASCII letters. Café → cafe.
"""
import re
import unicodedata


def slugify(text: str) -> str:
    # NFKD: split base + combining marks
    s = unicodedata.normalize("NFKD", text)
    # Drop combining marks (accents); keep base letters/digits
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    # Lowercase, replace non-alnum runs with single '-'
    s = re.sub(r"[^a-z0-9]+", "-", s.lower())
    # Strip leading/trailing separators
    return s.strip("-")
