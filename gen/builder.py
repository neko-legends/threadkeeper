"""Message builder + fact/thread registry for the synthetic session generator.

Everything here is deterministic given the `random.Random` it is constructed with.
"""
from __future__ import annotations

import datetime as dt
import json
import re


class Builder:
    def __init__(self, rng, start: dt.datetime):
        self.rng = rng
        self.msgs: list[dict] = []
        self.chars = 0
        self.clock = start
        self.facts: dict[str, dict] = {}
        self.threads: list[dict] = []
        self.closed: list[dict] = []
        self.decoys: list[dict] = []
        self._call_n = 0

    # -- clock -----------------------------------------------------------
    def tick(self, minutes: int = 0, seconds: int = 0):
        self.clock += dt.timedelta(minutes=minutes, seconds=seconds)
        return self.clock

    def ts(self, fmt="%Y-%m-%d %H:%M:%S") -> str:
        return self.clock.strftime(fmt)

    # -- messages --------------------------------------------------------
    def _add(self, m: dict, plants=(), corrects=()):
        self.msgs.append(m)
        idx = len(self.msgs) - 1
        self.chars += len(m.get("content") or "")
        for tc in m.get("tool_calls", []):
            self.chars += len(tc["function"]["arguments"])
        for fid in plants:
            self.facts[fid]["planted_at"].append(idx)
        for fid in corrects:
            self.facts[fid]["corrected_at"].append(idx)
        return idx

    def system(self, text):
        return self._add({"role": "system", "content": text})

    def user(self, text, plants=(), corrects=()):
        self.tick(minutes=self.rng.randint(1, 9))
        return self._add({"role": "user", "content": text.strip("\n")}, plants, corrects)

    def assistant(self, text, plants=(), corrects=()):
        self.tick(seconds=self.rng.randint(5, 50))
        return self._add({"role": "assistant", "content": text.strip("\n")}, plants, corrects)

    def tool(self, name, args: dict, output: str, say: str | None = None, plants=(), corrects=()):
        """assistant tool call + the tool result message."""
        self._call_n += 1
        cid = "call_%s" % "".join(self.rng.choice("0123456789abcdef") for _ in range(10))
        self.tick(seconds=self.rng.randint(2, 40))
        self._add({
            "role": "assistant",
            "content": say.strip("\n") if say else None,
            "tool_calls": [{"id": cid, "type": "function",
                            "function": {"name": name, "arguments": json.dumps(args, ensure_ascii=False)}}],
        })
        return self._add({"role": "tool", "tool_call_id": cid, "content": output.strip("\n")}, plants, corrects)

    def bash(self, cmd, output, say=None, **kw):
        return self.tool("bash", {"command": cmd}, output, say, **kw)

    # -- ground truth registry ------------------------------------------
    def fact(self, fid, category, description, value, aliases, line, weight=1,
             stale=None, stale_aliases=None, regex=None):
        """Register a fact. `line` is a reference-summary sentence containing {v} (latest value)
        and, for superseded facts, {s} (stale value) inside a cued phrase."""
        self.facts[fid] = {
            "id": fid, "category": category, "description": description, "value": value,
            "aliases": sorted(set([value] + list(aliases))), "regex": regex, "weight": weight,
            "superseded": stale is not None,
            "stale": [{"value": stale, "aliases": sorted(set([stale] + list(stale_aliases or [])))}] if stale else [],
            "line": line, "planted_at": [], "corrected_at": [], "stale_at": [],
        }

    def stale_here(self, fid):
        self.facts[fid]["stale_at"].append(len(self.msgs) - 1)

    def thread(self, tid, kind, title, criteria, keywords, line):
        self.threads.append({"id": tid, "kind": kind, "title": title, "state": "open",
                             "criteria": criteria, "keywords": keywords, "line": line, "evidence_at": []})

    def thread_at(self, tid):
        for t in self.threads:
            if t["id"] == tid:
                t["evidence_at"].append(len(self.msgs) - 1)

    def closed_thread(self, title, resolution):
        self.closed.append({"title": title, "resolution": resolution})

    def decoy(self, did, value, aliases, why):
        self.decoys.append({"id": did, "value": value, "aliases": sorted(set([value] + list(aliases))), "why": why})


def render_line(f: dict, stale=False) -> str:
    fmt = {"v": f["value"], "s": f["stale"][0]["value"] if f["stale"] else ""}
    if stale and f["stale"]:
        fmt["v"] = fmt["s"]
        return f["stale_line"].format(**fmt) if f.get("stale_line") else re.sub(r"\s*\(.*?\)", "", f["line"]).format(**fmt)
    return f["line"].format(**fmt)
