"""Slugify — SE021 fixed.

Unicode strategy: NFKD normalize + strip combining marks.
'Café' -> 'cafe'. Letters that do not decompose to ASCII stay
lowercased (e.g. '中文' -> '中文', 'ЖЖЖ' -> 'жжж').
"""
import re
import unicodedata


def slugify(text: str) -> str:
    if not text:
        return ""

    # Decompose accents, drop combining marks, then lower.
    s = unicodedata.normalize("NFKD", text)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.lower()

    # Underscore is non-alnum: strip it (do not turn into separator).
    s = s.replace("_", "")

    # Non-alphanumeric (Unicode-aware \\w) collapse to a single '-'.
    s = re.sub(r"[^\w]+", "-", s, flags=re.UNICODE)
    s = re.sub(r"-{2,}", "-", s)

    return s.strip("-")
