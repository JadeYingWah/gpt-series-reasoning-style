"""Slugify: text → URL-safe slug.

Unicode strategy (chosen and tested):
1. NFKD-normalize so accented Latin folds to ASCII base letters (Café → Cafe).
2. Strip combining marks (Mn) that NFKD left behind.
3. Lowercase (Unicode-aware).
4. Split on runs of non-alphanumeric characters; join with a single '-'.
   ``str.isalnum()`` is used, so CJK and other Unicode letters are kept.
5. Empty / all-separator input → ''.
"""
import unicodedata


def slugify(text: str) -> str:
    if not text:
        return ""
    decomposed = unicodedata.normalize("NFKD", text)
    without_marks = "".join(
        ch for ch in decomposed if not unicodedata.combining(ch)
    )
    lowered = without_marks.lower()
    parts = []
    current = []
    for ch in lowered:
        if ch.isalnum():
            current.append(ch)
        else:
            if current:
                parts.append("".join(current))
                current = []
    if current:
        parts.append("".join(current))
    return "-".join(parts)
