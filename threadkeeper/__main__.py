"""python -m threadkeeper bench --model X --base-url URL --api-key-env VAR [--judge-model Y]

One command: run the model on the corpus, score the summary, rebuild the board, draw the charts.
Without --judge-model nothing is sent to a judge: threads are matched mechanically and the row says so.
The judge defaults to the same endpoint and key as the model; override with --judge-base-url / --judge-api-key-env.
"""
from __future__ import annotations

import argparse
import os
import sys

from run import __main__ as run_cli
from score import __main__ as score_cli


def bench(a):
    results = a.results
    run_argv = ["--model", a.model, "--effort", a.effort, "--corpus", a.corpus, "--results", results, "--corpora", a.corpora,
                "--transport", a.transport, "--max-tokens", str(a.max_tokens)]
    if a.transport == "openai":
        if not (a.base_url and a.api_key_env):
            sys.exit("error: --base-url and --api-key-env are required for the openai transport")
        run_argv += ["--base-url", a.base_url, "--api-key-env", a.api_key_env]
    run_cli.main(run_argv)
    score_argv = ["--results", results, "--corpora", a.corpora, "--only", "%s__" % run_cli.slug(a.model)] + a.include_args()
    if a.judge_model:
        jurl, jkey = a.judge_base_url or a.base_url, a.judge_api_key_env or a.api_key_env
        if not (jurl and jkey):
            sys.exit("error: --judge-model needs --judge-base-url and --judge-api-key-env (or --base-url/--api-key-env to reuse)")
        os.environ["THREADKEEPER_BENCH_JUDGE_KEY"] = os.environ.get(jkey, "")
        score_argv += ["--judge-base-url", jurl, "--judge-model", a.judge_model, "--judge-api-key-env", "THREADKEEPER_BENCH_JUDGE_KEY"]
    else:
        score_argv += ["--no-judge"]
    score_cli.main(score_argv)
    score_cli.main(["--results", results, "--corpora", a.corpora, "--board-only"] + a.include_args())
    csv_path = os.path.join(results, "leaderboard.csv")
    try:
        from score import charts
        charts.draw_all(csv_path, a.charts_dir, a.corpus)
    except ImportError:
        print("note: matplotlib not installed; board written, charts skipped (pip install matplotlib)")
    print("board: %s\ncharts: %s" % (os.path.join(results, "leaderboard.md"), a.charts_dir))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m threadkeeper")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("bench", help="run + score + board + charts for one model")
    b.add_argument("--model", required=True)
    b.add_argument("--base-url")
    b.add_argument("--api-key-env")
    b.add_argument("--judge-model", help="a model from a DIFFERENT family than --model; omit for mechanical-only scoring")
    b.add_argument("--judge-base-url")
    b.add_argument("--judge-api-key-env")
    b.add_argument("--transport", choices=["openai", "pi", "claude"], default="openai")
    b.add_argument("--effort", default="default")
    b.add_argument("--corpus", default="128k")
    b.add_argument("--corpora", default="corpora")
    b.add_argument("--results", default="results")
    b.add_argument("--charts-dir", default="docs")
    b.add_argument("--max-tokens", type=int, default=32768)
    a = ap.parse_args(argv)
    a.include_args = lambda: []
    bench(a)


if __name__ == "__main__":
    main()
