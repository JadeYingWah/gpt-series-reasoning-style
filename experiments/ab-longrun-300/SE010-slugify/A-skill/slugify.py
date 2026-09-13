"""Slugify text into a URL-safe ASCII slug.

Unicode strategy: NFKD-normalize, drop combining marks, then keep only
[a-z0-9-] (hyphens as the sole separator). Letters without an ASCII
compatible decomposition (e.g. CJK) are stripped.
"""
import re
import unicodedata


def slugify(text: str) -> str:
    # NFKD: Café → Cafe (+ combining acute), Ü → U (+ combining diaeresis)
    normalized = unicodedata.normalize("NFKD", text)
    # Strip combining marks so decomposed letters collapse to base ASCII
    stripped = "".join(c for c in normalized if not unicodedata.combining(c))
    # Lowercase, replace runs of non-alnum with a single hyphen
    slug = re.sub(r"[^a-z0-9]+", "-", stripped.lower())
    # Drop leading/trailing hyphens
    return slug.strip("-")
