"""Slugify: convert text to URL-safe ASCII slug.

Unicode strategy: NFKD normalize, strip combining marks, then
keep [a-z0-9] and hyphen. Accented letters become their ASCII base
(Café → cafe).
"""
import re
import unicodedata


def slugify(text: str) -> str:
    # NFKD: decompose accents, then drop combining marks
    s = unicodedata.normalize("NFKD", text)
    s = "".join(c for c in s if not unicodedata.combining(c))
    # lowercase
    s = s.lower()
    # replace any run of non-alphanumeric with a single hyphen
    s = re.sub(r"[^a-z0-9]+", "-", s)
    # strip leading/trailing hyphens
    return s.strip("-")
