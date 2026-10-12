"""Canonical text rendering of a session (used for token counts, text-mode prompts, judge context)."""
from __future__ import annotations

import json


def load_session(path):
    with open(path, encoding="utf-8") as fh:
        return [json.loads(l) for l in fh if l.strip()]


def render_transcript(messages) -> str:
    out = []
    for m in messages:
        r = m["role"]
        if r == "tool":
            out.append("[tool result %s]\n%s" % (m.get("tool_call_id", ""), m.get("content") or ""))
            continue
        head = {"system": "[system]", "user": "[user]", "assistant": "[assistant]"}.get(r, "[%s]" % r)
        body = m.get("content") or ""
        for tc in m.get("tool_calls", []) or []:
            body += ("\n" if body else "") + "[tool call] %s %s" % (tc["function"]["name"], tc["function"]["arguments"])
        out.append("%s\n%s" % (head, body))
    return "\n\n".join(out)


def corpus_text(messages) -> str:
    """Everything a summary could legitimately quote from: all message contents + tool args."""
    return render_transcript(messages)


def count_tokens(text: str):
    """(tokens, tokenizer). o200k_base via tiktoken if installed, else chars/3.7 estimate (labelled)."""
    try:
        import tiktoken
        return len(tiktoken.get_encoding("o200k_base").encode(text)), "tiktoken:o200k_base"
    except Exception:
        return round(len(text) / 3.7), "estimate:chars/3.7"
