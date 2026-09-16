"""slugify — fixed implementation.

Unicode strategy: NFKD decomposition + strip Mn (combining marks),
so Latin accents map to ASCII base letters (Café → cafe, naïve → naive).
Non-Latin scripts (e.g. CJK) become separators and are removed.
"""
import re
import unicodedata


def slugify(text: str) -> str:
    if not text:
        return ""
    # NFKD so accents split off as combining marks
    text = unicodedata.normalize("NFKD", text)
    # Drop combining marks; keep remaining characters
    text = "".join(c for c in text if not unicodedata.combining(c))
    # Lowercase
    text = text.lower()
    # Non-alphanumeric runs → single hyphen
    text = re.sub(r"[^a-z0-9]+", "-", text)
    # Strip leading/trailing hyphens
    return text.strip("-")
