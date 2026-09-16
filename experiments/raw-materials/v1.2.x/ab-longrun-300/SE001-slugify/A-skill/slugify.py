"""slugify: text → URL-safe ASCII slug.

Unicode strategy: NFKD normalize, drop combining marks (Mn category),
lowercase, keep only [a-z0-9], collapse runs of other chars to '-',
strip leading/trailing '-'.
"""
import re
import unicodedata

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def slugify(text: str) -> str:
    if not text:
        return ""
    # NFKD: Café → Cafe + combining acute; fullwidth → ASCII
    decomposed = unicodedata.normalize("NFKD", text)
    # Drop combining marks so Café → Cafe
    no_marks = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    lowered = no_marks.lower()
    # Collapse everything that is not [a-z0-9] into a single '-'
    collapsed = _NON_ALNUM.sub("-", lowered)
    return collapsed.strip("-")
