"""slugify — NFKD + strip combining marks + ASCII alnum separators."""
import re
import unicodedata


def slugify(text: str) -> str:
    # Unicode strategy: NFKD normalize, drop combining marks (diacritics),
    # then keep only ASCII [a-z0-9] with '-' as separator.
    # Café → café → cafe (not "café" or "Caf-").
    if not text:
        return ""
    normalized = unicodedata.normalize("NFKD", text)
    stripped = "".join(
        ch for ch in normalized if not unicodedata.combining(ch)
    )
    lowered = stripped.lower()
    hyphenated = re.sub(r"[^a-z0-9]+", "-", lowered)
    return hyphenated.strip("-")
