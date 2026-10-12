"""python -m run.backfill_versions [results ...]  -- add a `versions` block to arms that ran before versions were recorded.

Backfilled blocks say so (`captured: backfill-*`): the claude resolved id comes from the modelUsage the arm itself stored
(real, observed at run time); tool versions are the ones installed NOW (not at run time); judge aliases are re-resolved NOW.
"""
from __future__ import annotations

import datetime
import glob
import json
import os
import sys

from . import versions as V

TODAY = datetime.date.today().isoformat()  # local date


def judge_block(j):
    """Versions for a judge recorded before judge calls carried them. Aliases are resolved against today's ~/.claude.json."""
    tr, model = j.get("transport", "openai"), j["model"]
    if tr == "claude":
        resolved, src = _claude_default_model() if model == "opus" else model, "alias `opus` re-resolved at backfill from ~/.claude.json (NOT at run time)"
    else:
        resolved, src = model, "explicit id as requested (no echo recorded at run time)"
    return V.build(tr, model, j.get("effort") or "default", resolved, src, TODAY, "backfill")


def _claude_default_model():
    try:
        return json.load(open(os.path.expanduser("~/.claude.json"))).get("model") or "unknown"
    except Exception:
        return "unknown"


def arm_block(meta):
    tr, model, eff = meta.get("transport", "openai"), meta["model"], meta["effort"]
    day = datetime.datetime.fromtimestamp(meta.get("started_at_unix", 0)).date().isoformat()
    if tr == "claude":
        b = V.for_cli_result(tr, model, eff, meta.get("usage"))
        b["resolved_on"] = day
    elif tr == "pi":
        b = V.for_cli_result(tr, model, eff, None)
        b["resolved_on"] = day
    else:
        b = V.build("openai", model, eff, model, "explicit id as requested (endpoint echo not recorded at run time)", day)
    b["captured"] = "backfill-from-stored-run-output"
    if b["tool_version"]:
        b["tool_version_note"] = "version installed at backfill %s, not necessarily at run time" % TODAY
    return b


def main(dirs):
    for d in dirs:
        for mp in sorted(glob.glob(os.path.join(d, "*", "meta.json"))):
            meta = json.load(open(mp))
            if "versions" not in meta or "--force" in sys.argv:
                meta["versions"] = arm_block(meta)
            if meta.get("judge", {}).get("model") and not meta["judge"].get("versions"):
                meta["judge"]["versions"] = judge_block(meta["judge"])
            json.dump(meta, open(mp, "w"), indent=1, ensure_ascii=False)
            sp = os.path.join(os.path.dirname(mp), "score.json")
            if os.path.exists(sp):
                s = json.load(open(sp))
                s["versions"] = meta["versions"]
                if (s.get("judge") or {}).get("model"):
                    s["judge"]["versions"] = meta["judge"].get("versions")
                json.dump(s, open(sp, "w"), indent=1, ensure_ascii=False)
            print("%s: %s -> %s" % (os.path.basename(os.path.dirname(mp)), meta["versions"]["requested_model"], meta["versions"]["resolved_model_id"]))


if __name__ == "__main__":
    main([x for x in sys.argv[1:] if not x.startswith("--")] or ["results", "results-200k"])
