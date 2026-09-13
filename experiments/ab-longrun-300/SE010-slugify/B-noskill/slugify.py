"""Slugify text to a URL-safe slug.

Unicode strategy: NFKD-normalize and strip combining marks so accented
Latin letters fold to ASCII (Café → cafe). Remaining non-alphanumeric
characters become a single hyphen; result is lowercased and stripped.
"""
import re
import unicodedata


def slugify(text: str) -> str:
    if not text:
        return ""
    # NFKD: decompose accents (é → e + combining acute), then drop marks
    normalized = unicodedata.normalize("NFKD", text)
    without_marks = "".join(c for c in normalized if not unicodedata.combining(c))
    # Collapse non-alphanumeric runs to a single hyphen
    s = re.sub(r"[^a-z0-9]+", "-", without_marks.lower())
    # Strip leading/trailing hyphens
    return s.strip("-")
