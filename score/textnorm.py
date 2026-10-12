"""Text normalisation + boundary-aware matching shared by the mechanical scorers."""
from __future__ import annotations

import re

_TRANS = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"', "–": "-", "—": "-", " ": " ", "‑": "-"})


def norm(s: str) -> str:
    s = s.translate(_TRANS).lower()
    s = s.replace("**", "").replace("`", "").replace("__", "")
    s = re.sub(r"(?<=\d),(?=\d{3}\b)", "", s)      # 20,000 -> 20000
    s = re.sub(r"\s+", " ", s)
    return s


def find(haystack_norm: str, needle: str):
    """Yield (start, end) of boundary-respecting matches of needle in an already-normalised haystack."""
    n = norm(needle)
    if not n:
        return
    pat = r"(?<![a-z0-9])" + re.escape(n) + r"(?![a-z0-9]|[.,]\d)"
    for m in re.finditer(pat, haystack_norm):
        yield m.start(), m.end()


def has(haystack_norm: str, needle: str) -> bool:
    return next(find(haystack_norm, needle), None) is not None
