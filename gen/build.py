"""Build one corpus: python -m gen --size 32k --seed 3201 --out corpora/32k"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import random

from . import filler, story
from .builder import Builder, render_line

SIZES = json.load(open(os.path.join(os.path.dirname(__file__), "sizes.json")))


def build(seed: int, target_chars: int):
    rng = random.Random(seed)
    w = story.make_world(rng)
    b = Builder(rng, dt.datetime.combine(w["base"], dt.time(8, 40)))
    b.w = w
    story.define(b, w)
    story.define_threads(b, w)
    n = len(story.SCENES)
    # measure core cost deterministically with a throwaway pass using the same seed
    probe_rng = random.Random(seed)
    pw = story.make_world(probe_rng)
    pb = Builder(probe_rng, dt.datetime.combine(pw["base"], dt.time(8, 40)))
    pb.w = pw
    story.define(pb, pw); story.define_threads(pb, pw)
    for sc in story.SCENES + [story.s_final]:
        sc(pb, pw)
    core = pb.chars
    spare = max(0, target_chars - core)
    for i, sc in enumerate(story.SCENES):
        sc(b, w)
        if i < n - 1:
            b.tick(minutes=rng.choice([30, 90, 240]))
            filler.fill(b, spare // (n - 1))
    # extra filler before the closing scene soaks up the remainder
    filler.fill(b, max(0, target_chars - core - b.chars + core))
    story.s_final(b, w)
    return b, w


def ground_truth(b, w, seed, size):
    facts = list(b.facts.values())
    for f in facts:
        f["line_latest"] = render_line(f)
        if f["superseded"]:
            f["line_stale"] = render_line(f, stale=True)
    return {"version": 1, "seed": seed, "size": size, "app": w["app"],
            "facts": facts, "threads": b.threads, "closed_threads": b.closed, "decoys": b.decoys,
            "cue_note": "A stale/decoy value is only penalised when no supersession cue appears near it."}


def reference_summary(gt):
    L = ["# Session summary", "", "## Facts and current state"]
    L += ["- " + f["line_latest"] for f in gt["facts"]]
    L += ["", "## Open threads"] + ["- " + t["line"] for t in gt["threads"]]
    L += ["", "## Closed"] + ["- %s: %s." % (c["title"], c["resolution"]) for c in gt["closed_threads"]]
    return "\n".join(L) + "\n"


def write(out, b, w, seed, size):
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "session.jsonl"), "w", encoding="utf-8", newline="\n") as fh:
        for m in b.msgs:
            fh.write(json.dumps(m, ensure_ascii=False, sort_keys=True) + "\n")
    gt = ground_truth(b, w, seed, size)
    with open(os.path.join(out, "ground_truth.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(gt, fh, ensure_ascii=False, indent=1, sort_keys=True, default=str)
        fh.write("\n")
    with open(os.path.join(out, "reference_summary.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(reference_summary(gt))


def sha256_file(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m gen")
    ap.add_argument("--size", choices=sorted(SIZES), default="32k")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--target-chars", type=int)
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    seed = a.seed if a.seed is not None else SIZES[a.size]["seed"]
    tc = a.target_chars or SIZES[a.size]["target_chars"]
    b, w = build(seed, tc)
    out = a.out or os.path.join("corpora", a.size)
    write(out, b, w, seed, a.size)
    print("%s: %d messages, %d chars, session sha256=%s" % (out, len(b.msgs), b.chars, sha256_file(os.path.join(out, "session.jsonl"))))


if __name__ == "__main__":
    main()
