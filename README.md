# threadkeeper

An open, fully synthetic, reproducible benchmark for **LLM context compaction**: give a model a long agent session, ask it to write the summary that will replace that session, then grade the summary.

Everything in the corpus is invented (a solo founder and a coding agent building and shipping a small web app). It is generated deterministically from a seed with no LLM and no network. Pure Python 3 standard library for generating, running and scoring; `tiktoken` and `matplotlib` are optional.

## What it measures

1. **Facts survive or don't.** 50 planted facts (names, ports, paths, prices, hashes, vendor details...) scored mechanically by normalised, boundary-aware alias matching.
2. **Corrections and decoys.** 7 facts are stated, then corrected later (price, launch date, deploy day, session store, send limit, Node version, beta target). Only the latest value earns credit; stating a stale value as current is penalised (stating it with a cue such as "was", "moved from", "dropped" is fine). Decoys (a near-duplicate vendor name, a near-duplicate ticket number, an unrelated commit hash) are penalised the same way.
3. **Threads.** 8 open items (a flaky test, a promised migration, an undecided pricing question, a vendor reply, an unresolved interpersonal matter, a half-done README, a pending accountant answer, a file the user owes) graded PRESERVED / PARTIAL / LOST, by a rubric-based judge model, with a mechanical keyword fallback reported alongside.
4. **Invention.** Reported two ways: a **mechanical cross-check** (every quoted span, number and hash in the summary must occur in the session) and a **blind judge** whose quoted evidence must itself be an exact substring of the summary or the item is dropped (our judge fabricated quotes). The judge count is a ranking signal, not ground truth.
5. **The summary gate.** Before any scoring, each output is classified `summary` / `continuation` / `chat-reply` / `empty` / `tool-call`. Non-summaries are **FAILED**, never a low score.

Composite (0-100) = `55 x facts_net + 35 x threads + 10 x (1 - min(1, mechanical_invention/10))`. FAILED arms get no score and are listed unranked.

## Lessons baked in (plain words)

- A fact scorer will give a model that *continued the conversation in character* 1/49 and it looks "mediocre" instead of broken. Some models at some `reasoning_effort` values simply don't summarise: they carry on as the agent, answer the user, or emit a fake tool call. So there is a gate, and failing it is its own outcome.
- Effort is model-specific. It can help one model and break another, so every `reasoning_effort` value is its own arm, and values a model rejects are recorded (`status: rejected`), not skipped silently.
- Summaries lose things at corrections: the old value and the new one both look like "the price". We plant corrections and reward only the latest.
- LLM judges invent evidence. We verify every judge quote mechanically and run a non-LLM invention check next to the judge.
- Same bytes for every arm: the request is hashed (`prompt_sha256`), temperature 0.

## Run it (3 commands)

```
export MY_KEY=...
python3 -m run --base-url https://api.example.com/v1 --api-key-env MY_KEY --model my-model --effort low,medium,high --corpus 128k
python3 -m score --judge-base-url https://api.example.com/v1 --judge-model my-judge   # judge key from THREADKEEPER_JUDGE_API_KEY; --no-judge for mechanical only
```

`score` writes `results/<arm>/score.json`, `results/leaderboard.md` and `results/leaderboard.csv`. Chart: `python -m score.chart results/leaderboard.csv`.

`--effort default` omits the parameter; `--effort all` tries `none,low,medium,high,xhigh,max`. `--mode messages` (default) sends the session as real chat turns (tool calls included) followed by `prompts/compact.md` as a final user message, which is how agent harnesses compact and what provokes the "continue in character" failure; `--mode text` embeds a rendered transcript in one user message for endpoints that reject tool-call history.

**Add a model:** just run it with a new `--model` (and `--base-url`/`--api-key-env` if the provider differs). Any OpenAI-compatible `/chat/completions` endpoint works. Output lands in `results/<model>__<effort>__<corpus>/{output.md,meta.json}`; `meta.json` has latency, usage (prompt/completion/reasoning tokens), finish_reason, cost when the provider reports it in `usage`, the exact request params and the prompt hash.

## Corpora

`corpora/{32k,128k,200k}` with SHA256s and token counts in `corpora/MANIFEST.json` (counted with tiktoken `o200k_base` over the rendered transcript from `gen/render.py`; other tokenizers differ). Each holds `session.jsonl` (OpenAI message format), `ground_truth.json` and a template-authored `reference_summary.md`. Regenerate/verify: `python -m gen.freeze --check` (needs tiktoken). Make a new one: `python -m gen --size 128k --seed 7 --out /tmp/x`.

## Tests

`python -m unittest discover -s tests -t .` runs the self-tests: a perfect summary scores near max; in-character continuations, a chat reply, a tool call and an empty string are FAILED; stale values are penalised; invented numbers/hashes/quotes are flagged; judge-fabricated quotes are dropped; the generator is byte-deterministic and matches the manifest. `tests/test_mutant.py` re-runs the self-tests with the gate disabled (`TK_DISABLE_GATE=1`) and asserts they fail.

## Limitations

- Synthetic is not real. Templated sessions are cleaner and more repetitive than real ones; filler is random but structurally regular. The seeded values differ per corpus but the story and fact list are the same shape.
- The gate is heuristic (structure, openers, session coverage). It can misclassify unusual outputs; the reasons and signals are stored in `score.json`. Check FAILED arms by eye.
- Substring/alias matching rewards exact tokens; a correct paraphrase of a fact with no alias can be missed, and a summary that dumps every value would score well on facts (thread and invention checks and length limits in your prompt are the counterweight).
- Judge bias: the judge may favour its own family. Use a judge that is not in the leaderboard, and treat judge invention counts as a ranking signal. Mechanical invention flags computed numbers (sums, percentages) as false positives.
- Thread keyword fallback marks a thread PRESERVED if the keywords appear, regardless of whether it is called open.
- At 32K a strong model scores very high (see `results/example-smoke`); the 128K/200K corpora are where differences show. Tokenizers and context limits differ by provider, so "200k" is a nominal o200k count.
- Single run at temperature 0, not repeated; some providers are not deterministic.

## License

MIT
