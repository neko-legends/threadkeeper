"""score_output(): gate -> facts -> threads -> invention for one summary."""
from __future__ import annotations

import json
import os

from gen.render import corpus_text, load_session, render_transcript
from . import envscrub, facts as facts_mod, gate, invention, threads as threads_mod, weights as weights_mod


class Corpus:
    def __init__(self, directory):
        self.dir = directory
        self.messages = load_session(os.path.join(directory, "session.jsonl"))
        self.gt = json.load(open(os.path.join(directory, "ground_truth.json"), encoding="utf-8"))
        self.text = corpus_text(self.messages)
        self._index = None

    @property
    def index(self):
        if self._index is None:
            self._index = invention.corpus_index(self.text)
        return self._index


def score_output(text: str, corpus: Corpus, meta: dict | None = None, judge=None, weights: dict | None = None) -> dict:
    g = gate.classify(text, corpus.messages, meta)
    res = {"gate": g}
    if g["label"] != "summary":
        res.update(status="FAILED", failed_as=g["label"], composite=None, composite_v1=None)
        return res
    f = facts_mod.score_facts(text, corpus.gt)
    mech_threads = threads_mod.mechanical(text, corpus.gt)
    thr = {"mechanical": mech_threads, "mechanical_score": threads_mod.points(mech_threads), "judge": None}
    final_threads, thr_source = mech_threads, "mechanical"
    # environment strings (cwd, run date) are not invention: the checks and the judge see the scrubbed summary
    seen, stripped = envscrub.scrub(text, corpus.text, envscrub.run_dates(meta))
    res["environment_stripped"] = stripped
    inv_mech = invention.check(seen, corpus.index)
    inv = {"mechanical": inv_mech, "judge": None}
    if judge is not None:
        jt = judge.threads(seen, corpus.gt)
        thr["judge"] = {k: v for k, v in jt.items() if k != "raw"}
        thr["judge"]["raw"] = jt["raw"][:4000]
        if jt["parsed"]:
            final_threads, thr_source = jt["verdicts"], "judge"
        ji = judge.invention(seen, render_transcript(corpus.messages))
        inv["judge"] = {k: v for k, v in ji.items() if k != "raw"}
        inv["judge"]["raw"] = ji["raw"][:4000]
    tscore = threads_mod.points(final_threads)
    thr.update(final=final_threads, final_source=thr_source, score=tscore,
               counts={k: list(final_threads.values()).count(k) for k in ("PRESERVED", "PARTIAL", "LOST")})
    comp = weights_mod.composites(f["net"], tscore, inv_mech["count"], weights)
    res.update(status="SCORED", facts=f, threads=thr, invention=inv, **comp)
    return res
