"""Slugify: ASCII-safe URL slug with NFKD Unicode strategy."""
import re
import unicodedata


def slugify(text: str) -> str:
    """Lowercase, NFKD-normalize, collapse non-alnum to '-', strip edges.

    Unicode strategy: NFKD + drop combining marks.
    e.g. "Café" -> "cafe", "ÅNGSTRÖM" -> "angstrom".
    """
    if not text:
        return ""
    s = unicodedata.normalize("NFKD", text)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")
