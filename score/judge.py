"""Blind LLM judge for threads and invention, with quote verification.

The judge is NOT trusted: every piece of evidence it cites must be an exact (normalised) substring of the
summary, otherwise the item is dropped / the verdict capped and the event counted as `judge_fabricated_quotes`.
`chat` is injectable so tests can run offline.
"""
from __future__ import annotations

import json
import re

from run.client import post_chat, text_of
from .textnorm import norm

THREADS_PROMPT = """You are grading a SUMMARY of a long working session between a user and an AI agent.
You have not seen the session. For each THREAD below, decide whether the summary preserves it as an OPEN item:
- PRESERVED: the summary clearly says the item is still open/pending and captures the essentials in the criteria.
- PARTIAL: it is mentioned but vague, missing who owes what, or missing an essential part, or is wrongly presented as finished.
- LOST: not present.
For PRESERVED and PARTIAL you MUST give `quote`: an EXACT contiguous span copied from the SUMMARY that supports your verdict. Do not paraphrase the quote.

THREADS:
{threads}

SUMMARY:
<<<
{summary}
>>>

Answer with JSON only: {{"T1": {{"verdict": "PRESERVED|PARTIAL|LOST", "quote": "..."}}, ...}}"""

INVENTION_PROMPT = """You are fact-checking a SUMMARY of the SESSION below. List every claim in the summary that is NOT supported by the session
(invented facts, wrong values, details the session never contained). Do not list omissions. Do not list claims that are merely vague.
For each, `summary_quote` MUST be an EXACT contiguous span copied from the SUMMARY. If every claim is supported, answer [].

SESSION:
<<<
{session}
>>>

SUMMARY:
<<<
{summary}
>>>

Answer with JSON only: [{{"summary_quote": "...", "why": "..."}}, ...]"""


def extract_json(txt: str):
    txt = re.sub(r"<think>.*?</think>", "", txt or "", flags=re.S)
    txt = re.sub(r"```(?:json)?", "", txt)
    starts = [x for x in (txt.find("{"), txt.find("[")) if x >= 0]
    if not starts:
        return None
    i = min(starts)
    close = "}" if txt[i] == "{" else "]"
    j = txt.rfind(close)
    try:
        return json.loads(txt[i:j + 1])
    except Exception:
        return None


class Judge:
    def __init__(self, base_url, api_key, model, effort=None, chat=None):
        self.base_url, self.api_key, self.model, self.effort = base_url, api_key, model, effort
        self._chat = chat or self._http
        self.calls = []

    def _http(self, prompt):
        body = {"model": self.model, "temperature": 0, "max_tokens": 16384, "messages": [{"role": "user", "content": prompt}]}
        if self.effort:
            body["reasoning_effort"] = self.effort
        r = post_chat(self.base_url, self.api_key, body)
        self.calls.append({"status": r["status"], "usage": (r.get("body") or {}).get("usage"), "latency_s": r["latency_s"]})
        return text_of(r)

    def threads(self, summary: str, gt: dict) -> dict:
        listing = "\n".join("%s. %s -- criteria: %s" % (t["id"], t["title"], t["criteria"]) for t in gt["threads"])
        raw = self._chat(THREADS_PROMPT.format(threads=listing, summary=summary))
        data = extract_json(raw)
        sn = norm(summary)
        verdicts, notes, fabricated = {}, {}, 0
        for t in gt["threads"]:
            d = (data or {}).get(t["id"]) if isinstance(data, dict) else None
            v = str((d or {}).get("verdict", "")).upper().strip()
            if v not in ("PRESERVED", "PARTIAL", "LOST"):
                verdicts[t["id"]], notes[t["id"]] = "LOST", "judge gave no valid verdict"
                continue
            q = norm(str((d or {}).get("quote", ""))).strip()
            if v != "LOST" and (len(q) < 6 or q not in sn):
                fabricated += 1
                notes[t["id"]] = "judge quote not found in summary; verdict capped"
                v = "PARTIAL" if v == "PRESERVED" else "LOST"
            verdicts[t["id"]] = v
        return {"verdicts": verdicts, "notes": notes, "judge_fabricated_quotes": fabricated, "parsed": data is not None, "raw": raw}

    def invention(self, summary: str, session_text: str) -> dict:
        raw = self._chat(INVENTION_PROMPT.format(session=session_text, summary=summary))
        data = extract_json(raw)
        sn = norm(summary)
        valid, dropped = [], 0
        for it in (data if isinstance(data, list) else []):
            q = norm(str(it.get("summary_quote", ""))).strip() if isinstance(it, dict) else ""
            if len(q) >= 4 and q in sn:
                valid.append({"summary_quote": it["summary_quote"], "why": str(it.get("why", ""))[:300]})
            else:
                dropped += 1
        return {"items": valid, "count": len(valid), "dropped_unverified": dropped, "parsed": data is not None, "raw": raw}
