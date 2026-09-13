"""Slugify: convert text to a URL-safe slug.

Unicode strategy: NFKD normalization then strip non-ASCII.
  Café -> cafe (not café)
Rationale: ASCII-only slugs are maximally portable across URL systems,
CDN caches, and legacy clients.
"""
import re
import unicodedata


def slugify(text: str) -> str:
    # NFKD: decompose accents (é -> e + combining accent)
    s = unicodedata.normalize("NFKD", text)
    # Drop combining marks / non-ascii leftovers
    s = s.encode("ascii", "ignore").decode("ascii")
    # Lowercase
    s = s.lower()
    # Collapse any run of non-alphanumeric into a single hyphen
    s = re.sub(r"[^a-z0-9]+", "-", s)
    # Strip leading/trailing hyphens
    s = s.strip("-")
    return s
