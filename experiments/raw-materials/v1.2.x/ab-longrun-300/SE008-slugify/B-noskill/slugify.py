"""slugify — fixed implementation."""
import re
import unicodedata


def slugify(text: str) -> str:
    if not text:
        return ""
    # NFKD decompose so Café → Cafe, ñ → n
    s = unicodedata.normalize("NFKD", text)
    # Drop combining marks (accents)
    s = "".join(c for c in s if not unicodedata.combining(c))
    # Keep only ASCII letters/digits as word chars; collapse everything else
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s)
    # Lowercase
    s = s.lower()
    # Strip leading/trailing hyphens
    return s.strip("-")
