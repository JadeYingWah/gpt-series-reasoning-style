"""Slugify text into URL-friendly slugs.

Unicode strategy (documented, see response.md):
- NFKD-normalize, then strip combining marks (category Mn).
  Latin accents fold to ASCII (Café → cafe); compatibility
  ligatures expand (ﬁ → fi). Non-Latin letters (CJK, Cyrillic,
  …) survive and are kept as-is.
- Result is lowercased; sequences of non-alphanumeric
  characters collapse to a single '-'; leading/trailing '-'
  are stripped. Empty / punctuation-only input yields "".
"""
import re
import unicodedata


def slugify(text: str) -> str:
    if not text:
        return ""
    # NFKD: Café → Cafe + U+0301; ﬁ → fi
    text = unicodedata.normalize("NFKD", text)
    # Drop combining marks (nonspacing Mn) so Café → Cafe
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    # Keep Unicode letters/digits; collapse everything else to '-'
    # \w with re.UNICODE matches letters+digits+underscore across scripts
    text = re.sub(r"[^\w]+", "-", text, flags=re.UNICODE)
    # Underscore is not a word separator we want in slugs → treat as separator
    text = text.replace("_", "-")
    # Collapse any accidental -- and strip edges
    text = re.sub(r"-{2,}", "-", text)
    return text.strip("-")
