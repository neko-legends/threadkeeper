"""Mechanical invention check: every quoted span, number and hash in the summary must occur in the session."""
from __future__ import annotations

import re

from .textnorm import norm

NUM = re.compile(r"(?<![\w.])\d+(?:[.:]\d+)*")
HEX = re.compile(r"\b(?=[0-9a-f]*\d)(?=[0-9a-f]*[a-f])[0-9a-f]{7,40}\b")
QUOTES = [re.compile(r'"([^"\n]{4,160})"'), re.compile(r"`([^`\n]{4,160})`"), re.compile(r"“([^”\n]{4,160})”"),
          re.compile(r"(?<![\w])'([^'\n]{4,160})'(?![\w])")]


MIN_QUOTE = 12  # shorter spans are scare-quotes / single words ("fixes", "all good"); not checkable as verbatim, reported as skipped
PLACEHOLDER = re.compile(r"<[^<>\n]{1,40}>|…|\.{3}")  # summarisers template identifiers (<name>) and elide ids (inv_…)
EDGE = " \t.,;:!?-–—/\\|"


def quote_fragments(q: str):
    """A quoted span is checked as the verbatim fragments around placeholders/ellipses, with edge punctuation stripped
    (the punctuation belongs to the summary's sentence, not the session's text). Fragments < 4 chars are uncheckable."""
    return [f for f in (x.strip(EDGE) for x in PLACEHOLDER.split(q)) if len(f) >= 4]


def corpus_index(corpus_text: str):
    c = norm(corpus_text)
    toks = set()
    for t in NUM.findall(c):
        toks.add(t)
        parts = re.split(r"[.:]", t)
        toks.update(parts)
        for k in range(2, len(parts)):
            toks.add(".".join(parts[:k]))
    return c, toks, set(HEX.findall(c))


def with_rate(mech: dict) -> dict:
    """Add checked_total and per_100 (unsupported items per 100 checked quotes+numbers). Raw counts reward terse summaries; compare this rate."""
    c = mech.get("checked") or {}
    total = c.get("quotes", 0) + c.get("numbers", 0)
    mech["checked_total"] = total
    mech["per_100"] = round(100 * mech["count"] / total, 2) if total else None
    return mech


def check(summary: str, index) -> dict:
    c, toks, hexes = index
    s = norm(summary)
    bad_q, nq, skipped, seen = [], 0, [], set()
    for rx in QUOTES:
        for m in rx.finditer(s):
            q = m.group(1).strip()
            if len(q) < 4 or q in seen:
                continue
            seen.add(q)
            frags = quote_fragments(q)
            if len(q) < MIN_QUOTE or not frags:
                skipped.append(q)
                continue
            nq += 1
            if not all(f in c for f in frags):
                bad_q.append(q)
    bad_n, nn = [], 0
    for t in NUM.findall(s):
        if len(re.sub(r"\D", "", t)) < 2:
            continue
        nn += 1
        if t not in toks and t not in bad_n:
            bad_n.append(t)
    bad_h = [h for h in set(HEX.findall(s)) if h not in hexes and h not in c]
    return with_rate({"unsupported_quotes": bad_q, "unsupported_numbers": bad_n, "unsupported_hashes": sorted(bad_h),
            "checked": {"quotes": nq, "numbers": nn}, "skipped_short_quotes": skipped,
            "count": len(bad_q) + len(bad_n) + len(bad_h)})
