"""Minimal OpenAI-compatible chat-completions client (stdlib only)."""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request


def post_chat(base_url: str, api_key: str, body: dict, timeout: float = 1800, retries: int = 3) -> dict:
    """POST {base_url}/chat/completions. Never raises; returns
    {status, body, error, latency_s, attempts, headers}. 4xx (except 429) is not retried."""
    url = base_url.rstrip("/") + "/chat/completions"
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    last = {"status": None, "body": None, "error": "not attempted", "headers": {}}
    t_all = time.time()
    for attempt in range(1, retries + 1):
        req = urllib.request.Request(url, data=data, method="POST", headers={
            "Content-Type": "application/json", "Authorization": "Bearer " + api_key, "User-Agent": "threadkeeper/1"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read().decode("utf-8", "replace")
                last = {"status": r.status, "body": json.loads(raw), "error": None, "headers": dict(r.headers)}
                break
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", "replace")
            try:
                parsed = json.loads(raw)
            except Exception:
                parsed = None
            last = {"status": e.code, "body": parsed, "error": raw[:2000], "headers": dict(e.headers)}
            if e.code != 429 and e.code < 500:
                break
        except Exception as e:  # timeout, connection reset, bad json
            last = {"status": None, "body": None, "error": "%s: %s" % (type(e).__name__, e), "headers": {}}
        if attempt < retries:
            time.sleep(min(60, 4 * attempt * attempt))
    last["latency_s"] = round(time.time() - t_all, 3)
    last["attempts"] = attempt
    return last


def message_of(resp: dict) -> dict:
    try:
        return resp["body"]["choices"][0]["message"] or {}
    except Exception:
        return {}


def text_of(resp: dict) -> str:
    return message_of(resp).get("content") or ""
