"""Slugify: text → URL-safe slug.

Unicode strategy: NFKD decomposition + strip combining marks, keep
alphanumeric Unicode (str.isalnum), lowercase, non-alnum runs → single '-'.
Examples: "Hello, World!" → "hello-world"; "Café" → "cafe".
"""
import unicodedata


def slugify(text: str) -> str:
    if not text:
        return ""
    s = unicodedata.normalize("NFKD", text)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.lower()

    parts: list[str] = []
    prev_sep = False
    for ch in s:
        if ch.isalnum():
            parts.append(ch)
            prev_sep = False
        else:
            if not prev_sep and parts:
                parts.append("-")
                prev_sep = True

    return "".join(parts).strip("-")
