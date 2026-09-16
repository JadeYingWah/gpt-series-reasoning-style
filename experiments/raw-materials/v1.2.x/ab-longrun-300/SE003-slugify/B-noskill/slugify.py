"""Slugify: text -> URL-safe slug.

Unicode strategy: NFKD normalize, drop combining marks, keep ASCII
(Cafe -> cafe). Lowercase, collapse non-alphanumeric runs to '-', strip edges.
"""
import re
import unicodedata


def slugify(text: str) -> str:
    if not text:
        return ""
    # NFKD: decompose accents, strip combining marks, keep ASCII
    decomposed = unicodedata.normalize("NFKD", text)
    ascii_only = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    # Collapse non-alphanumeric runs to single hyphen
    s = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_only)
    return s.strip("-").lower()
