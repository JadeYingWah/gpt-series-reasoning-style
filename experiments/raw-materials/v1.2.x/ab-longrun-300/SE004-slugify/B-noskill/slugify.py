"""slugify — NFKD + drop combining marks + lower."""
import re
import unicodedata


def _is_alnum_letter_or_digit(ch: str) -> bool:
    cat = unicodedata.category(ch)
    return cat.startswith("L") or cat.startswith("N")


def slugify(text: str) -> str:
    if not text:
        return ""
    # NFKD: é → e + combining acute
    s = unicodedata.normalize("NFKD", text)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.lower()
    # collapse any run of non-letter/non-digit into a single "-"
    out = []
    for ch in s:
        if _is_alnum_letter_or_digit(ch):
            out.append(ch)
        else:
            out.append("-")
    s = re.sub(r"-+", "-", "".join(out))
    return s.strip("-")
