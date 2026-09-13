"""slugify — NFKD deaccent, collapse non-alnum to '-', strip edges."""
import re
import unicodedata


def slugify(text: str) -> str:
    if not text:
        return ""
    # NFKD so Café → Cafe (+ combining acute), then drop marks
    s = unicodedata.normalize("NFKD", text)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    # Keep Unicode letters/digits only; everything else becomes a separator
    s = "".join(c if c.isalnum() else "-" for c in s)
    # Collapse runs and strip edge separators
    s = re.sub(r"-{2,}", "-", s)
    return s.strip("-")
