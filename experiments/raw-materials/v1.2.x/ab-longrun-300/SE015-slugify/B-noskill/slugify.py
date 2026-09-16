"""slugify — turn text into a URL-safe slug.

Unicode strategy: NFKD-normalize, then drop combining marks so
accents fold to ASCII base letters (Café → cafe).
"""
import re
import unicodedata


def slugify(text: str) -> str:
    if not text:
        return ""
    # NFKD: decompose accents (é → e + combining acute)
    s = unicodedata.normalize("NFKD", text)
    # Drop combining marks; keep the base letters/digits
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    # Lowercase
    s = s.lower()
    # Collapse any run of non-alphanumerics into a single hyphen
    s = re.sub(r"[^a-z0-9]+", "-", s)
    # Strip leading/trailing hyphens
    return s.strip("-")
