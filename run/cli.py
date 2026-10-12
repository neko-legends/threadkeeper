"""Local-CLI transports (subscription models): `pi -p` and `claude -p`.

The prompt is written to a temp file and fed to the CLI on stdin (a 128k-token prompt exceeds the 128 KiB argv
limit). Tools, sessions, extensions and skills are switched off so the CLI behaves like a bare chat model.
Never raises; returns {status, text, cmd, exit_code, stderr, latency_s, usage, cost_usd, error}.
"""
from __future__ import annotations

import json
import os
import shlex
import subprocess
import tempfile
import time

SYSTEM = "You are a helpful assistant."


def build_cmd(transport: str, model: str, effort: str = "default") -> list:
    if transport == "pi":
        cmd = ["pi", "-p", "--model", model, "--no-tools", "--no-session", "--no-extensions", "--no-skills",
               "--no-prompt-templates", "--system-prompt", SYSTEM]
        if effort != "default":
            cmd += ["--thinking", effort]
        return cmd
    if transport == "claude":
        # `--model opus` resolves to claude-opus-5-5 (verified via modelUsage in the json output)
        cmd = ["claude", "-p", "--model", model, "--tools", "", "--no-session-persistence", "--disable-slash-commands",
               "--system-prompt", SYSTEM, "--output-format", "json"]
        if effort != "default":
            cmd += ["--effort", effort]
        return cmd
    raise ValueError("unknown CLI transport %r" % transport)


def call_cli(transport: str, model: str, prompt: str, effort: str = "default", timeout: float = 3600) -> dict:
    cmd = build_cmd(transport, model, effort)
    out = {"transport": transport, "cmd": " ".join(shlex.quote(c) for c in cmd) + " < <prompt-tempfile>", "text": "",
           "exit_code": None, "stderr": "", "usage": None, "cost_usd": None, "finish_reason": None, "error": None, "status": "error"}
    t0 = time.time()
    with tempfile.NamedTemporaryFile("w", suffix=".txt", encoding="utf-8", delete=False) as tf:
        tf.write(prompt)
        path = tf.name
    try:
        with open(path, "rb") as fh:
            p = subprocess.run(cmd, stdin=fh, capture_output=True, timeout=timeout)
        out["exit_code"] = p.returncode
        out["stderr"] = p.stderr.decode("utf-8", "replace")[:4000]
        raw = p.stdout.decode("utf-8", "replace")
        if transport == "claude":
            try:
                j = json.loads(raw)
                out["text"] = j.get("result") or ""
                out["usage"] = {"usage": j.get("usage"), "modelUsage": j.get("modelUsage"), "is_error": j.get("is_error"),
                                "terminal_reason": j.get("terminal_reason")}
                out["cost_usd"] = j.get("total_cost_usd")  # list-price equivalent; subscription, not billed
                out["finish_reason"] = j.get("stop_reason")
                if j.get("is_error"):
                    out["error"] = "claude reported is_error: %s" % str(j.get("result"))[:500]
            except Exception as e:
                out["error"] = "unparseable claude json: %s" % e
                out["text"] = raw
        else:
            out["text"] = raw
        if p.returncode != 0:
            out["error"] = out["error"] or "non-zero exit %s" % p.returncode
        elif not out["text"].strip():
            out["error"] = out["error"] or "empty output"
        out["status"] = "ok" if not out["error"] else "error"
    except subprocess.TimeoutExpired:
        out["error"] = "timeout after %ss" % timeout
    except Exception as e:
        out["error"] = "%s: %s" % (type(e).__name__, e)
    finally:
        os.unlink(path)
    out["latency_s"] = round(time.time() - t0, 3)
    return out
