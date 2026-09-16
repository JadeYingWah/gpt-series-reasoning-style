"""slugify — Unicode-aware slug generator.

Policy: NFKD + strip combining marks, so Latin accents fold to ASCII
(Café → cafe). Remaining non-alphanumeric runs collapse to a single '-'.
"""
import re
import unicodedata


def slugify(text: str) -> str:
    if not text:
        return ""
    # NFKD splits accented chars into base + combining mark
    s = unicodedata.normalize("NFKD", text)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.lower()
    # Collapse any run of non-alphanumeric (except '-') into a single '-'
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")
