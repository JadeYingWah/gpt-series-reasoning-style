"""slugify — NFKD + strip marks + lower + collapse separators."""
import re
import unicodedata


def slugify(text: str) -> str:
    # NFKD so Café -> Cafe; drop Mn combining marks so Cafe -> cafe.
    normalized = unicodedata.normalize("NFKD", text)
    stripped = "".join(c for c in normalized if not unicodedata.combining(c))
    lowered = stripped.lower()
    # Only ASCII alnum survive; runs of anything else become a single '-'.
    dashed = re.sub(r"[^a-z0-9]+", "-", lowered)
    return dashed.strip("-")
