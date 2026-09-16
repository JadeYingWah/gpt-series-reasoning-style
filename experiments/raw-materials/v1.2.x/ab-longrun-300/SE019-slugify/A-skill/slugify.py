"""Slugify: turn text into a URL-safe slug.

Unicode strategy: NFKD-decompose, drop combining marks, lowercase.
  "Café" -> "cafe"; CJK (no combining marks) kept: "中文" -> "中文".
"""
from __future__ import annotations

import re
import unicodedata


def slugify(text: str) -> str:
    if not text:
        return ""
    # NFKD: split base + combining marks (é -> e + U+0301)
    decomposed = unicodedata.normalize("NFKD", text)
    # drop combining marks so accents fold to ASCII bases
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    lowered = stripped.lower()
    # keep unicode letters/digits; collapse everything else to '-'
    slug = re.sub(r"[^\w]+", "-", lowered, flags=re.UNICODE)
    # \w includes '_' — treat as separator
    slug = slug.replace("_", "-")
    # collapse any run of '-' produced by the above
    slug = re.sub(r"-{2,}", "-", slug)
    return slug.strip("-")
