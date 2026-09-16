"""Slugify text into URL-safe slugs.

Strategy notes (Unicode):
  NFKD decomposition + strip combining marks, so accents fold to ASCII
  base letters. Café -> cafe, Über -> uber. Non-ASCII letters that have
  no NFKD base (e.g. CJK) are retained after lower().
"""
from __future__ import annotations

import re
import unicodedata


def slugify(text: str) -> str:
    if not text:
        return ""
    # 1. Unicode normalize + drop combining marks (ASCII-fold accents)
    s = unicodedata.normalize("NFKD", text)
    s = "".join(c for c in s if not unicodedata.combining(c))
    # 2. Lowercase
    s = s.lower()
    # 3. Replace non-alnum runs with single hyphen
    s = re.sub(r"[^a-z0-9]+", "-", s)
    # 4. Strip leading/trailing hyphens
    s = s.strip("-")
    return s
