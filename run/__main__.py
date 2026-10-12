"""python -m run --base-url URL --api-key-env ENV --model M --effort low,high --corpus 32k [--max-tokens 32768]"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import json
import os
import re
import sys
import time

from gen.render import load_session, render_transcript
from .client import message_of, post_chat
from .cli import call_cli
from . import versions

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
    ap.add_argument("--transport", choices=["openai", "pi", "claude"], default="openai",
                    help="openai: OpenAI-compatible HTTP; pi: `pi -p --model M`; claude: `claude -p --model M` (subscription CLIs, text mode, stdin)")
    ap.add_argument("--base-url")
    ap.add_argument("--api-key-env")
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
    ap.add_argument("--parallel", type=int, default=1,
                    help="run N arms at once; arms are independent (default 1, sequential)")
    ap.add_argument("--force", action="store_true", help="re-run an arm whose meta.json already exists (default: skip, never re-run)")
    a = ap.parse_args(argv)
    key = None
    if a.transport == "openai":
        if not (a.base_url and a.api_key_env):
            sys.exit("--transport openai needs --base-url and --api-key-env")
        key = os.environ.get(a.api_key_env)
        if not key:
            sys.exit("env var %s is not set" % a.api_key_env)
    else:
        a.mode = "text"  # CLIs take one text prompt on stdin; no structured chat turns
    session = load_session(os.path.join(a.corpora, a.corpus, "session.jsonl"))
    prompt = open(a.prompt, encoding="utf-8").read()
    messages = build_messages(session, prompt, a.mode)
    prompt_hash = hashlib.sha256(json.dumps(messages, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    efforts = ALL_EFFORTS if a.effort == "all" else a.effort
    effs = [e.strip() for e in efforts.split(",") if e.strip()]

    def run_arm(eff):
            body = {"model": a.model, "messages": messages, "temperature": 0, "max_tokens": a.max_tokens}
            if eff != "default":
                body["reasoning_effort"] = eff
            arm = os.path.join(a.results, "%s__%s__%s" % (slug(a.model), eff, a.corpus))
            os.makedirs(arm, exist_ok=True)
            if os.path.exists(os.path.join(arm, "meta.json")) and not a.force:
                print("%s: already ran, skipping" % os.path.basename(arm))
                return
            t0 = time.time()
            if a.transport != "openai":
                text_prompt = messages[-1]["content"] if len(messages) == 1 else "\n\n".join(m["content"] for m in messages)
                r = call_cli(a.transport, a.model, text_prompt, eff, a.timeout)
                text = r["text"]
                failed_as = None
                if r["status"] != "ok":
                    failed_as = "context" if re.search(r"context|too long|too large|maximum|prompt is too", r["error"] or r["stderr"], re.I) else "cli-error"
                meta = {
                    "status": "ok" if not failed_as else "failed", "failed_as": failed_as,
                    "transport": a.transport, "command": r["cmd"], "exit_code": r["exit_code"], "stderr": r["stderr"],
                    "model": a.model, "effort": eff, "corpus": a.corpus, "mode": a.mode, "message_count": len(messages),
                    "prompt_sha256": prompt_hash, "prompt_chars": len(text_prompt),
                    "compact_prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                    "latency_s": r["latency_s"], "finish_reason": r.get("finish_reason"), "usage": r["usage"],
                    "cost_usd": None, "list_price_equiv_usd": r["cost_usd"], "error": r["error"], "started_at_unix": int(t0), "finished_at_unix": int(time.time()),
                    "judge_model": None, "versions": versions.for_cli_result(a.transport, a.model, eff, r["usage"]),
                }
                with open(os.path.join(arm, "output.md"), "w", encoding="utf-8") as fh:
                    fh.write(text)
                json.dump(meta, open(os.path.join(arm, "meta.json"), "w"), indent=1, ensure_ascii=False)
                print("%s: %s exit=%s %.1fs chars=%d err=%s" % (os.path.basename(arm), meta["status"], r["exit_code"], r["latency_s"], len(text), r["error"]))
                return
            r = post_chat(a.base_url, key, body, a.timeout)
            msg = message_of(r)
            choice = ((r.get("body") or {}).get("choices") or [{}])[0]
            ok = r["status"] == 200 and bool(choice)
            params = {k: v for k, v in body.items() if k != "messages"}
            status = "ok" if ok else ("rejected" if r["status"] and 400 <= r["status"] < 500 else "error")
            failed_as = None
            if not ok and re.search(r"context.{0,20}(length|window)|too long|maximum context|exceeds", str(r.get("error")), re.I):
                status, failed_as = "failed", "context"
            meta = {
                "status": status, "failed_as": failed_as, "transport": "openai",
                "command": "POST %s/chat/completions model=%s reasoning_effort=%s" % (a.base_url.rstrip("/"), a.model, eff),
                "model": a.model, "effort": eff, "corpus": a.corpus, "mode": a.mode, "base_url": a.base_url,
                "request_params": params, "message_count": len(messages), "prompt_sha256": prompt_hash,
                "compact_prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                "http_status": r["status"], "attempts": r.get("attempts"), "latency_s": r["latency_s"],
                "finish_reason": choice.get("finish_reason"), "usage": (r.get("body") or {}).get("usage"),
                "cost_usd": cost_of(r), "tool_calls": msg.get("tool_calls"), "has_reasoning_content": bool(msg.get("reasoning_content") or msg.get("reasoning")),
                "error": None if ok else r.get("error"), "started_at_unix": int(t0), "finished_at_unix": int(time.time()),
                "versions": versions.for_http_result(a.model, eff, r.get("body")),
            }
            with open(os.path.join(arm, "output.md"), "w", encoding="utf-8") as fh:
                fh.write(msg.get("content") or "")
            json.dump(meta, open(os.path.join(arm, "meta.json"), "w"), indent=1, ensure_ascii=False)
            print("%s: %s http=%s finish=%s %.1fs usage=%s" % (os.path.basename(arm), meta["status"], r["status"], meta["finish_reason"], r["latency_s"], meta["usage"]))

    if a.parallel > 1:
        # arms are independent; run N at once (Jun's rule: never one arm at a time)
        with cf.ThreadPoolExecutor(max_workers=a.parallel) as ex:
            list(ex.map(run_arm, effs))
    else:
        for eff in effs:
            run_arm(eff)

if __name__ == "__main__":
    main()
