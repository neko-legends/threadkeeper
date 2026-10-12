"""Record WHICH model ran, not just what it was called. An alias is not a version.

`opus` is an alias: it means claude-opus-5-5 today and something else after the next release. Every arm therefore
stores a `versions` block: the id as requested, the id the provider/CLI reported back (where obtainable), the tool
version, the exact effort flag and the date the alias was resolved.
"""
from __future__ import annotations

import datetime
import subprocess

_CACHE = {}


def tool_version(transport):
    """`claude --version` / `pi --version`; None for HTTP. Cached per process."""
    if transport not in ("claude", "pi"):
        return None
    if transport not in _CACHE:
        try:
            p = subprocess.run([transport, "--version"], capture_output=True, timeout=30)
            _CACHE[transport] = (p.stdout or p.stderr).decode("utf-8", "replace").strip() or None
        except Exception:
            _CACHE[transport] = None
    return _CACHE[transport]


def effort_flag(transport, effort):
    if effort == "default":
        return "(none: flag omitted, provider default)"
    return {"claude": "--effort %s", "pi": "--thinking %s", "openai": "reasoning_effort=%s"}[transport] % effort


def resolved_from_claude_usage(usage):
    """The id claude -p reports in modelUsage (canonicalModel when present)."""
    mu = ((usage or {}).get("modelUsage")) or {}
    ids = sorted({(v or {}).get("canonicalModel") or k for k, v in mu.items()})
    return ids[0] if len(ids) == 1 else (",".join(ids) or None)


def build(transport, model, effort, resolved=None, source=None, date=None, captured="at-run"):
    return {
        "requested_model": model,
        "resolved_model_id": resolved,
        "resolution_source": source,
        "resolved_on": date or datetime.date.today().isoformat(),
        "transport": transport,
        "tool_version": tool_version(transport),
        "effort_flag": effort_flag(transport, effort),
        "captured": captured,
    }


def for_cli_result(transport, model, effort, usage):
    if transport == "claude":
        rid = resolved_from_claude_usage(usage)
        return build(transport, model, effort, rid, "claude -p json modelUsage (canonicalModel)" if rid else "claude did not report a model id")
    return build(transport, model, effort, model, "pi model ref as requested (pi does not echo a resolved id; the provider/id is the pin)")


def for_http_result(model, effort, body):
    echoed = (body or {}).get("model")
    return build("openai", model, effort, echoed or model,
                 "endpoint-echoed `model` field" if echoed else "explicit id sent (endpoint did not echo a model id)")
