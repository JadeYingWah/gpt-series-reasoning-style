"""Slugify — turn text into a URL-safe slug.

Unicode strategy: NFKD fold to ASCII.
  1. unicodedata.normalize("NFKD", text)
  2. drop combining marks (category Mn)
  3. lowercase
  4. keep only [a-z0-9]; everything else becomes a separator
  5. collapse runs of separators to a single "-"
  6. strip leading/trailing "-"

Documented consequences of this choice:
  - Café → cafe, naïve → naive (diacritics fold away)
  - Straße → stra-e (ß has no NFKD ASCII fold; becomes a separator)
  - CJK and other non-foldable scripts are stripped
"""
from __future__ import annotations

import re
import unicodedata

_COMBINING = re.compile(r"[\u0300-\u036f]")
_NON_KEEP = re.compile(r"[^a-z0-9]+")
_STRIP_HYPHEN = re.compile(r"^-+|-+$")


def slugify(text: str) -> str:
    if not text:
        return ""
    s = unicodedata.normalize("NFKD", text)
    s = _COMBINING.sub("", s)
    s = s.lower()
    s = _NON_KEEP.sub("-", s)
    s = _STRIP_HYPHEN.sub("", s)
    return s
