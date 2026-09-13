"""Slugify: Unicode-aware, NFKD + deaccent, collapse separators, strip edges."""
import re
import unicodedata


def slugify(text: str) -> str:
    # NFKD so accented letters split into base + combining mark
    s = unicodedata.normalize("NFKD", text)
    # Drop combining marks (Mn): Café -> Cafe, Ångström -> Angstrom
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.lower()
    # Collapse runs of non-alphanumeric (Unicode letters/digits kept) and `_`
    s = re.sub(r"[\W_]+", "-", s, flags=re.UNICODE)
    return s.strip("-")
