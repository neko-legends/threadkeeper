"""Environment-derived strings are not invention.

Some transports leak their runtime environment into the model's context (`pi` puts its scratch cwd `/tmp/tk-cwd-XXXX`
and today's date in the system prompt; a summarizer then dutifully records both). Those strings are real for the model
and absent from the session, so the judge and the mechanical check would count them as fabrications.

Rule: before the invention checks (mechanical + judge) and the threads judge, the summary is scrubbed:
  * `/tmp/tk-cwd-*` scratch dirs and `/home/<user>/...` / `/Users/<user>/...` paths that the session does not contain -> `<cwd>`
  * ISO dates equal to the day the arm ran (from meta) that the session does not contain -> `<date>`
Facts/gate scoring still read the original text. What was stripped is recorded in score.json as `environment_stripped`.
"""
from __future__ import annotations

import datetime as dt
import re

CWD = re.compile(r"/tmp/tk-cwd-[\w]+|/(?:home|Users)/[\w.-]+(?:/[\w.@+~-]+)*")
ISO = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
PLACE_CWD, PLACE_DATE = "<cwd>", "<date>"


def run_dates(meta: dict | None) -> set:
    """The day the arm ran: UTC and this machine's local date at start, plus the day versions were resolved."""
    meta = meta or {}
    days = set()
    t = meta.get("started_at_unix")
    if isinstance(t, (int, float)):
        days |= {dt.datetime.fromtimestamp(t, dt.timezone.utc).date().isoformat(), dt.datetime.fromtimestamp(t).date().isoformat()}
    on = (meta.get("versions") or {}).get("resolved_on")
    if on:
        days.add(str(on)[:10])
    return days


def scrub(text: str, corpus_text: str, dates: set) -> tuple[str, list]:
    """Return (scrubbed text, sorted list of distinct stripped strings)."""
    gone = set()

    def cwd(m):
        if m.group(0) in corpus_text:
            return m.group(0)
        gone.add(m.group(0))
        return PLACE_CWD

    def day(m):
        if m.group(0) not in dates or m.group(0) in corpus_text:
            return m.group(0)
        gone.add(m.group(0))
        return PLACE_DATE

    out = ISO.sub(day, CWD.sub(cwd, text))
    return out, sorted(gone)


def drop_env_items(items: list, stripped: list) -> tuple[list, list]:
    """Split judge invention items into (kept, excluded): excluded = the flagged quote names a stripped environment string."""
    kept, excl = [], []
    for it in items:
        q = it.get("summary_quote", "")
        (excl if any(s in q for s in stripped) or CWD.search(q) else kept).append(it)
    return kept, excl
