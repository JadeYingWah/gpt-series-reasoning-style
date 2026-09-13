"""Slugify: turn text into a URL-safe ASCII slug.

Unicode policy
--------------
NFKD decomposition + strip combining marks + ASCII fold.
  Cafe with acute (Café) -> cafe
  U-with-diaeresis etc.  -> ASCII base letters
CJK and other non-foldable scripts are dropped after fold
(so pure CJK collapses to the empty string).
"""
from __future__ import annotations

import re
import unicodedata

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def slugify(text: str) -> str:
    if not text:
        return ""
    # NFKD: Café -> Cafe + combining acute
    decomposed = unicodedata.normalize("NFKD", text)
    # Drop combining marks / non-spacing marks
    ascii_text = "".join(c for c in decomposed if not unicodedata.combining(c))
    # Keep only ASCII letters/digits; lower first so case is stable
    lowered = ascii_text.lower()
    # Collapse runs of non-alnum into a single hyphen
    slug = _NON_ALNUM.sub("-", lowered)
    # Strip leading/trailing hyphens
    return slug.strip("-")
