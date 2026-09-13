"""slugify — turn text into a URL-safe slug.

Unicode strategy: NFKD normalization + strip combining marks (ASCII fold),
then lowercase. Accented Latin letters become their ASCII base (Café -> cafe).
Non-decomposable non-ASCII characters (e.g. ß, CJK) become separators.
"""
import re
import unicodedata


def slugify(text: str) -> str:
    if not text:
        return ""
    # 1. Unicode fold: decompose, drop combining marks
    s = unicodedata.normalize("NFKD", text)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    # 2. Lowercase
    s = s.lower()
    # 3. Non [a-z0-9] become hyphens (existing hyphens kept as separators too)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    # 4. Collapse already done by +; strip edge hyphens
    s = s.strip("-")
    return s
