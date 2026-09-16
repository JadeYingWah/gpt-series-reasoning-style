"""slugify — Unicode-aware slug generator.

Strategy (NFKD):
1. NFKD-normalize (decompose accents: é → e + combining acute).
2. Drop combining marks (category Mn).
3. Lowercase.
4. Replace runs of non-[a-z0-9] with a single '-'.
5. Strip leading/trailing '-'.

Examples: Café → cafe, über → uber, 你好 → "" (CJK has no ASCII fold).
"""
import re
import unicodedata


def slugify(text: str) -> str:
    if not text:
        return ""
    # 1. decompose accents / compatibility chars
    s = unicodedata.normalize("NFKD", text)
    # 2. strip combining marks (Mn = Nonspacing_Mark)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    # 3. lowercase
    s = s.lower()
    # 4. collapse non-alnum runs to single hyphen
    s = re.sub(r"[^a-z0-9]+", "-", s)
    # 5. strip leading/trailing hyphens
    return s.strip("-")
