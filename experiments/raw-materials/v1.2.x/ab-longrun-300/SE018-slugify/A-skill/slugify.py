"""slugify — NFKD + lower + collapse + strip."""
import re
import unicodedata


def slugify(text: str) -> str:
    # NFKD: decompose accents (Café → Cafe), drop combining marks
    s = unicodedata.normalize("NFKD", text)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")
