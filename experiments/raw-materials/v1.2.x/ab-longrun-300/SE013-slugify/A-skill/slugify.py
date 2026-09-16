"""Slugify.

Unicode strategy: NFKD-decompose, drop non-ASCII, lowercase, collapse
non-alnum runs to a single hyphen, strip edge hyphens.
Example: Café → cafe, naïve → naive, ﬁle → file.
"""
import re
import unicodedata


def slugify(text: str) -> str:
    if not text:
        return ""
    s = unicodedata.normalize("NFKD", text)
    s = s.encode("ascii", "ignore").decode("ascii")
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")
