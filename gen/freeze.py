"""Regenerate all frozen corpora + MANIFEST.json: python -m gen.freeze [--check]"""
import argparse
import json
import os
import sys

from . import build
from .render import count_tokens, load_session, render_transcript


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="regenerate in a temp dir and compare to the committed SHA256s")
    ap.add_argument("--out", default="corpora")
    a = ap.parse_args()
    out = a.out
    man = {}
    for size, cfg in build.SIZES.items():
        d = os.path.join(out, size)
        b, w = build.build(cfg["seed"], cfg["target_chars"])
        build.write(d, b, w, cfg["seed"], size)
        t = render_transcript(load_session(os.path.join(d, "session.jsonl")))
        n, tok = count_tokens(t)
        man[size] = {"seed": cfg["seed"], "target_chars": cfg["target_chars"], "messages": len(b.msgs), "rendered_chars": len(t),
                     "tokens": n, "tokenizer": tok,
                     "sha256": {f: build.sha256_file(os.path.join(d, f)) for f in ("session.jsonl", "ground_truth.json", "reference_summary.md")}}
        print(size, n, tok, man[size]["sha256"]["session.jsonl"][:16])
    p = os.path.join(out, "MANIFEST.json")
    if a.check:
        old = json.load(open("corpora/MANIFEST.json"))
        for k in man:
            assert old[k]["sha256"] == man[k]["sha256"], "corpus %s changed" % k
        print("MANIFEST sha256s match")
        return
    json.dump(man, open(p, "w"), indent=1, sort_keys=True)
    open(p, "a").write("\n")


if __name__ == "__main__":
    main()
