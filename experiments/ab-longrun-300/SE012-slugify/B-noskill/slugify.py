"""slugify — convert text to a URL-safe slug.

Unicode policy: NFKD. Decompose characters (e.g. é -> e + combining mark)
then drop combining marks, so Café -> cafe.
"""
import re
import unicodedata


def slugify(text: str) -> str:
    if not text:
        return ""
    # NFKD: decompose accents, then strip combining marks
    s = unicodedata.normalize("NFKD", text)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    # Collapse runs of non-alphanumeric into a single hyphen
    s = re.sub(r"[^a-z0-9]+", "-", s)
    # Strip leading/trailing hyphens
    s = s.strip("-")
    return s
