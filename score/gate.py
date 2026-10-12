"""The summary gate: classify an output BEFORE scoring.

Classes: summary | continuation | chat-reply | empty | tool-call | prompt-echo.
Everything except `summary` is reported as FAILED, never as a low score.

The gate is deliberately structural/heuristic (no model involved) so it is reproducible. It looks at
  * tool-call syntax (or a tool_calls field recorded by the runner),
  * length and markdown structure,
  * conversational / in-character openers ("Sure!", "Let me ...", "I'll now ..."),
  * coverage: how many parts of the session the output touches via entity-like tokens whose first
    appearance is in that part. A summary spans the whole session; an in-character continuation
    only talks about the last few turns.
"""
from __future__ import annotations

import os
import re

from gen.render import render_transcript

TOOL_PATTERNS = [
    r"<tool_call>", r"<function_calls?>", r"<invoke\b", r"\[TOOL_CALLS?\]", r"<\|tool", r"to=functions\.",
    r'"tool_calls"\s*:', r'^\s*\{\s*"name"\s*:\s*"[\w.-]+"\s*,\s*"(arguments|parameters)"', r"<tool_use>", r"<\|python_tag\|>",
]
CHAT_OPEN = re.compile(r"^\s*(sure|okay|ok|got it|great|alright|absolutely|of course|certainly|understood|thanks|thank you|hi|hello|no problem|will do|sorry|i('| a)m sorry|i can('|no)t|i cannot)\b", re.I)
ROLEPLAY_PARA = re.compile(r"^\s*(let me|let's|i'll|i will|i'm going to|i am going to|now i|next,? i|now,? let|running|first,? i|alright,? i|okay,? i)\b", re.I | re.M)
SUMMARY_WORDS = re.compile(r"\b(summary|overview|state of (the )?work|open (items|threads)|decisions?|context|goal|status)\b", re.I)
COMPACT_PROMPT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "prompts", "compact.md")
ENTITY = re.compile(r"[A-Za-z0-9_./~#$@:-]{4,}")


def echoes_prompt(text: str, prompt_path: str = COMPACT_PROMPT, min_lines: int = 4, share: float = 0.6) -> bool:
    """True if most of the output's non-empty lines are lines of the compaction prompt (the model repeated the request)."""
    try:
        want = {l.strip() for l in open(prompt_path, encoding="utf-8").read().splitlines() if len(l.strip()) >= 12}
    except OSError:
        return False
    got = [l.strip() for l in text.splitlines() if len(l.strip()) >= 12]
    return len(got) >= min_lines and sum(1 for l in got if l in want) >= share * len(got)


def _entity_tokens(s: str):
    out = set()
    for t in ENTITY.findall(s):
        t = t.strip(".,:;()[]'\"`").lower()
        if len(t) >= 4 and (re.search(r"\d", t) or re.search(r"[_./~#$@-]", t)):
            out.add(t)
    return out


def coverage_map(messages, parts=10):
    """For each of `parts` equal slices of the session, the entity tokens whose FIRST occurrence is there."""
    n = len(messages)
    seen, per = set(), [set() for _ in range(parts)]
    for i, m in enumerate(messages):
        txt = render_transcript([m])
        p = min(parts - 1, i * parts // max(1, n))
        for t in _entity_tokens(txt):
            if t not in seen:
                seen.add(t)
                per[p].add(t)
    return per


def coverage(text: str, messages, parts=10, need=2) -> int:
    toks = _entity_tokens(text)
    return sum(1 for s in coverage_map(messages, parts) if len(s & toks) >= need)


def classify(text: str, messages, meta: dict | None = None) -> dict:
    """Return {"label": ..., "reasons": [...], "signals": {...}}. Honours TK_DISABLE_GATE=1 (mutant test)."""
    meta = meta or {}
    t = text or ""
    s = t.strip()
    sig = {"chars": len(s)}
    reasons = []
    if os.environ.get("TK_DISABLE_GATE") == "1":      # mutant: gate switched off, everything scores
        return {"label": "summary", "reasons": ["gate disabled"], "signals": sig}
    if meta.get("tool_calls"):
        return {"label": "tool-call", "reasons": ["response carried a tool_calls field"], "signals": sig}
    if len(re.sub(r"\s", "", s)) < 20:
        return {"label": "empty", "reasons": ["no usable text"], "signals": sig}
    for p in TOOL_PATTERNS:
        if re.search(p, s, re.M):
            return {"label": "tool-call", "reasons": ["tool-call syntax matches %r" % p], "signals": sig}
    if echoes_prompt(s):
        return {"label": "prompt-echo", "reasons": ["output is the compaction prompt echoed back, not a summary"], "signals": sig}
    lines = s.splitlines()
    structure = sum(1 for l in lines if re.match(r"\s*(#{1,4}\s|[-*+]\s|\d+[.)]\s|\*\*[^*]+\*\*\s*:?)", l))
    roleplay = len(ROLEPLAY_PARA.findall(s))
    chat_open = bool(CHAT_OPEN.match(s))
    cov = coverage(s, messages)
    sig.update(structure_lines=structure, roleplay_paragraphs=roleplay, chat_opener=chat_open, coverage_parts=cov,
               ends_with_question=s.rstrip().endswith("?"), summary_words=len(SUMMARY_WORDS.findall(s)))
    if len(s) < 400:
        reasons.append("too short (%d chars) to be a summary of a long session" % len(s))
        return {"label": "chat-reply" if (chat_open or sig["ends_with_question"] or roleplay == 0) else "continuation", "reasons": reasons, "signals": sig}
    if cov < 3:
        reasons.append("touches only %d/10 parts of the session (a summary spans it)" % cov)
        label = "continuation" if (roleplay or structure < 5) else "chat-reply" if chat_open else "continuation"
        if chat_open and not roleplay:
            label = "chat-reply"
        return {"label": label, "reasons": reasons, "signals": sig}
    if roleplay >= 3 and roleplay * 3 > structure:
        reasons.append("%d in-character 'let me/I'll' paragraphs: reads as the agent's next turn" % roleplay)
        return {"label": "continuation", "reasons": reasons, "signals": sig}
    if structure < 3 and (chat_open or roleplay):
        reasons.append("no structure and conversational opener")
        return {"label": "chat-reply" if chat_open else "continuation", "reasons": reasons, "signals": sig}
    return {"label": "summary", "reasons": ["structure=%d coverage=%d/10" % (structure, cov)], "signals": sig}
