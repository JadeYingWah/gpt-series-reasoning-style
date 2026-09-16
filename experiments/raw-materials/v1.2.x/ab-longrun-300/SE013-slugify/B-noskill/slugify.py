"""slugify: convert text to URL-safe slug.

Unicode strategy: NFKD normalization then strip combining marks,
so Café → cafe (ASCII-safe). Documented in tests via test_unicode_lower.
"""
import re
import unicodedata


def slugify(text: str) -> str:
    if not text:
        return ""
    # NFKD: decompose é → e + combining accent, Ñ → N + tilde, etc.
    text = unicodedata.normalize("NFKD", text)
    # Drop combining marks (accents)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    # Collapse any run of non-alphanumeric into a single hyphen
    text = re.sub(r"[^a-z0-9]+", "-", text)
    # Strip leading/trailing hyphens
    return text.strip("-")
