"""Slugify text to URL-safe ASCII slugs.

Unicode strategy (chosen):
- NFKD-normalize the input, then drop combining marks so accented
  Latin letters fold to ASCII base letters (Café → cafe).
- After folding, only [A-Za-z0-9] survive as content; every other
  character (including CJK and other non-decomposable letters)
  acts as a separator.
- Consecutive separators collapse to a single '-'; leading/trailing
  '-' are stripped. Empty input (or input that yields no content)
  returns "".
"""
import re
import unicodedata


def slugify(text: str) -> str:
    if not text:
        return ""
    # Decompose accents: é -> e + COMBINING ACUTE ACCENT
    s = unicodedata.normalize("NFKD", text)
    # Drop combining marks so base ASCII letters remain
    s = "".join(c for c in s if not unicodedata.combining(c))
    # Lowercase, collapse non-alphanumeric runs to one hyphen
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s.lower())
    # Strip leading/trailing hyphens
    return s.strip("-")
