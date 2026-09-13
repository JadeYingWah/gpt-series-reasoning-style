"""slugify — turn text into a URL-safe slug.

Unicode strategy: NFKD-normalize, then keep only ASCII [a-z0-9]
(so Café -> cafe). Non-decomposable non-ASCII (e.g. CJK) is dropped.
"""
import re
import unicodedata


def slugify(text: str) -> str:
    # NFKD so accented Latin decomposes (Café -> Cafe + combining acute)
    s = unicodedata.normalize("NFKD", text)
    s = s.lower()
    # Drop combining marks / non-ASCII leftovers from NFKD
    s = s.encode("ascii", "ignore").decode("ascii")
    # Collapse runs of non-alphanumeric into a single dash
    s = re.sub(r"[^a-z0-9]+", "-", s)
    # Strip leading/trailing dashes; pure-separator input becomes ""
    s = s.strip("-")
    return s
