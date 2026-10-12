"""python -m run --base-url URL --api-key-env ENV --model M --effort low,high --corpus 32k [--max-tokens 32768]"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time

from gen.render import load_session, render_transcript
from .client import message_of, post_chat

ALL_EFFORTS = "none,low,medium,high,xhigh,max"


def build_messages(session, prompt, mode):
    if mode == "messages":
        return session + [{"role": "user", "content": prompt}]
    sys_msgs = [m for m in session if m["role"] == "system"]
    body = [m for m in session if m["role"] != "system"]
    text = "<session>\n" + render_transcript(body) + "\n</session>\n\n" + prompt
    return sys_msgs + [{"role": "user", "content": text}]


def slug(s):
    return re.sub(r"[^A-Za-z0-9.-]+", "-", s).strip("-")


def cost_of(resp):
    u = (resp.get("body") or {}).get("usage") or {}
    for k in ("cost", "total_cost", "cost_usd"):
        if isinstance(u.get(k), (int, float)):
            return u[k]
    h = {k.lower(): v for k, v in (resp.get("headers") or {}).items()}
    for k in ("x-cost", "x-venice-cost", "x-usage-cost"):
        if k in h:
            try:
                return float(h[k])
            except ValueError:
                pass
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m run")
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--api-key-env", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--effort", default="default", help="comma list; 'default' omits the param; 'all' = " + ALL_EFFORTS)
    ap.add_argument("--corpus", default="32k")
    ap.add_argument("--corpora", default="corpora")
    ap.add_argument("--max-tokens", type=int, default=32768)
    ap.add_argument("--prompt", default="prompts/compact.md")
    ap.add_argument("--mode", choices=["messages", "text"], default="messages",
                    help="messages: session as real chat turns + compaction request (default); text: transcript inside one user message")
    ap.add_argument("--results", default="results")
    ap.add_argument("--timeout", type=float, default=1800)
    a = ap.parse_args(argv)
    key = os.environ.get(a.api_key_env)
    if not key:
        sys.exit("env var %s is not set" % a.api_key_env)
    session = load_session(os.path.join(a.corpora, a.corpus, "session.jsonl"))
    prompt = open(a.prompt, encoding="utf-8").read()
    messages = build_messages(session, prompt, a.mode)
    prompt_hash = hashlib.sha256(json.dumps(messages, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    efforts = ALL_EFFORTS if a.effort == "all" else a.effort
    for eff in [e.strip() for e in efforts.split(",") if e.strip()]:
        body = {"model": a.model, "messages": messages, "temperature": 0, "max_tokens": a.max_tokens}
        if eff != "default":
            body["reasoning_effort"] = eff
        arm = os.path.join(a.results, "%s__%s__%s" % (slug(a.model), eff, a.corpus))
        os.makedirs(arm, exist_ok=True)
        t0 = time.time()
        r = post_chat(a.base_url, key, body, a.timeout)
        msg = message_of(r)
        choice = ((r.get("body") or {}).get("choices") or [{}])[0]
        ok = r["status"] == 200 and bool(choice)
        params = {k: v for k, v in body.items() if k != "messages"}
        meta = {
            "status": "ok" if ok else ("rejected" if r["status"] and 400 <= r["status"] < 500 else "error"),
            "model": a.model, "effort": eff, "corpus": a.corpus, "mode": a.mode, "base_url": a.base_url,
            "request_params": params, "message_count": len(messages), "prompt_sha256": prompt_hash,
            "compact_prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
            "http_status": r["status"], "attempts": r.get("attempts"), "latency_s": r["latency_s"],
            "finish_reason": choice.get("finish_reason"), "usage": (r.get("body") or {}).get("usage"),
            "cost_usd": cost_of(r), "tool_calls": msg.get("tool_calls"), "has_reasoning_content": bool(msg.get("reasoning_content") or msg.get("reasoning")),
            "error": None if ok else r.get("error"), "started_at_unix": int(t0),
        }
        with open(os.path.join(arm, "output.md"), "w", encoding="utf-8") as fh:
            fh.write(msg.get("content") or "")
        json.dump(meta, open(os.path.join(arm, "meta.json"), "w"), indent=1, ensure_ascii=False)
        print("%s: %s http=%s finish=%s %.1fs usage=%s" % (os.path.basename(arm), meta["status"], r["status"], meta["finish_reason"], r["latency_s"], meta["usage"]))


if __name__ == "__main__":
    main()
