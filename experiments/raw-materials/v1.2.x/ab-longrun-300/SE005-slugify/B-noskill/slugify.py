"""Slugify: text -> URL-safe ASCII slug.

Strategy (Unicode): NFKD decompose, drop combining marks, then lower.
So "Café" -> "cafe", "Éclair" -> "eclair". Non-ASCII letters that do not
fold to ASCII (e.g. CJK) are treated as separators and stripped.
"""
import re
import unicodedata


def slugify(text: str) -> str:
    if not text:
        return ""
    s = unicodedata.normalize("NFKD", text)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    return s
