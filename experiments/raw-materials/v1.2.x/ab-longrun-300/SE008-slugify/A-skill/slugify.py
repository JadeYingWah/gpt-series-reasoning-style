"""Slugify: convert text to a URL-safe slug.

Unicode strategy: NFKD normalization + strip combining marks.
Accented Latin letters decompose to ASCII base letters
(e.g. Café → cafe). Non-ASCII letters without a base
decomposition are treated as separators.
"""
import re
import unicodedata


def slugify(text: str) -> str:
    if not text:
        return ""
    # NFKD decomposes accents: é -> e + U+0301
    text = unicodedata.normalize("NFKD", text)
    # Drop combining marks (category Mn)
    text = "".join(c for c in text if not unicodedata.combining(c))
    # Lowercase, then replace any non-alphanumeric run with a single hyphen
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")
