"""slugify — convert text into a URL-safe slug.

Unicode strategy: NFKD-normalize, drop combining marks, lowercase.
Accented Latin letters fold to ASCII base form (Café → cafe).
"""
import re
import unicodedata


def slugify(text: str) -> str:
    if not text:
        return ""
    # Decompose accents: é → e + combining acute
    s = unicodedata.normalize("NFKD", text)
    # Discard combining marks; keep base letters/digits
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    # Fold case
    s = s.lower()
    # Collapse runs of non-alphanumerics into a single hyphen
    s = re.sub(r"[^a-z0-9]+", "-", s)
    # Strip leading/trailing hyphens
    return s.strip("-")
