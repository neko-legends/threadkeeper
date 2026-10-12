# 🌸 threadkeeper

> [!WARNING]
> **Correction 1: Opus was not the worst inventor. A biased judge made it look that way.**
> Earlier versions of this benchmark reported 7 invented facts for `claude-opus-5-5` (max effort). Those flags came from `openai/gpt-6-astra`, a competitor on the same board that was also grading it. Re-graded by a neutral judge (`venice/gemini-3-8-flash`, a family nowhere else on the board), Opus at max has **0** flagged inventions and sits mid-table. Do not use pre-v4 judge counts. Full write-up and screenshot proof: [docs/CORRECTIONS.md](docs/CORRECTIONS.md).


*Does your AI remember what mattered when it summarizes a long chat?*

Long agent sessions get "squeezed": the whole chat is replaced by a summary, and the agent keeps working from that summary alone (people call this *compaction*). If the summary drops or changes something, the agent never knows.

threadkeeper gives a model a long fake chat, asks for the summary, and grades it: what survived, what got corrupted, what got made up.

The chat is invented (a founder and a coding agent shipping a small web app) and generated from a seed. No LLM, no network. Pure Python 3 standard library; `tiktoken` and `matplotlib` are optional.

## 🚨 The problem it was built for

At some settings a model stops summarizing and starts *continuing the chat*: it replies in character, fakes tool calls, or sends a stub. The text is fluent, so a plain fact-counter gives it a low score. That reads as "mediocre" when it is really "broken".

So first we check the output is actually a summary. If not, the run is marked `FAILED` and gets no score.

## 🚀 Quick start

```bash
# 1. run a model you can reach over HTTP
python3 -m run --model z-ai-glm-5-3-flash --effort medium --corpus 128k \
  --base-url https://api.venice.ai/api/v1 --api-key-env VENICE_API_KEY

# 2. grade its summary (the grader must be a different model)
python3 -m score --judge-base-url https://api.venice.ai/api/v1 \
  --judge-model z-ai-glm-5-3-flash

# 3. read the board
cat results/leaderboard.md
```

## 📊 Results

![threadkeeper 128k leaderboard](docs/threadkeeper-128k.png)

*128k corpus (seed 12801, `session.jsonl` sha256 `115686d9…5728e`), composite v2. One panel per score, same row order: overall score, facts, open threads, made-up claims, speed. Each row says which transport ran the model and which other AI graded it. Caveat: the `claude` and `pi` CLI arms got the chat pasted into one message with tools off; the `openai` arms got it as real chat turns, so those groups are not a like-for-like comparison. Full breakdown: [`results/leaderboard.md`](results/leaderboard.md).*

## 🧪 What it measures

| check | question | how |
|---|---|---|
| Is it a summary? | Did the model summarize at all? | structural check → `SCORED` or `FAILED:<reason>` |
| Facts | Did the details survive? | 50 planted facts (names, ports, paths, prices, hashes) matched automatically |
| Corrections | Did it keep the *latest* value? | 7 facts change mid-chat; only the newest earns credit, stale ones cost points |
| Decoys | Did it fall for near-misses? | look-alike vendor, ticket number, commit hash |
| Threads | Did the 8 unfinished tasks survive? | another AI grades each `PRESERVED` / `PARTIAL` / `LOST` |
| Made-up claims | Did it invent things? | two ways, below |

Overall score:

```
composite = 100 * (0.45*facts + 0.30*threads + 0.25*invention_score)
invention_score = 1 / (1 + auto_checked_inventions/3)
```

Strong models all find 45-49 of 50 facts, so made-up claims and dropped threads decide the ranking. Inventing is worse than forgetting: the summary *replaces* the history. Weights: `score/weights.py`. `python3 -m score --rescore` recomputes without calling a model.

## 🕵️ Made-up claims

Lower is better. Counted two ways, because neither is reliable alone:

- **Checked automatically:** every number, hash and quoted phrase in the summary must appear in the chat. Count the ones that don't.
- **Another AI grades it:** it flags unsupported claims and must quote the summary exactly, or the flag is dropped. It once invented its own quotes, so treat its count as a hint, not truth. Counts are not comparable across graders.

Longer summaries make more claims and so collect more flags. Compare the rate **per 100 checked items**, with the raw count beside it. The full table is in [`results/leaderboard.md`](results/leaderboard.md).

**Worked example, Opus max.** Best fact recall (49/50), ranked last. Its flagged claims:

- "Highest migration number is `0080`": the chat shows 0080 but never says it's the highest. A guess became a fact.
- "Lisbon is UTC+1 until 2026-10-25 01:00 UTC": that time is nowhere in the chat. Outside knowledge passed off as detail.
- `docs/dns.md` and `config/defaults.ts` listed as done, when the chat only planned them.

That last one, intent turned into done, is the worst failure: the next session believes work exists that doesn't.

Contrast: kimi-k3 default had 0 flags of any kind and leads. (Both astra arms quote the harness's working directory, a `pi` transport leak, not invention.)

## 📚 Shipped corpora

| corpus | tokens (o200k) | messages | seed |
|---|---|---|---|
| `32k` | ~31,000 | 277 | 3201 |
| `128k` | ~127,000 | 886 | 12801 |
| `200k` | ~200,000 | 1226 | 20001 |

Each has `session.jsonl`, `ground_truth.json`, `reference_summary.md`; hashes in `corpora/MANIFEST.json`. A cheap model scored 97.6 on `32k`: it's a smoke test only. Use `128k` for a spread.

## 🛠️ Make your own

```bash
python3 -m gen --size 128k --seed 12345 --out /tmp/mine
```

Public tests get trained on. Publish a benchmark and, a version or two later, models have learned its facts and phrasing; the board then measures familiarity, not summarizing. So the generator is the product and the shipped corpora are demos.

1. Generate your own instance with any `--seed`. Report the seed and corpus hash.
2. Better still, test with your own real sessions, which nobody trained on.

## 🔍 Reading results

- `SCORED`: it was a summary; the score means something.
- `FAILED:continuation`: it kept writing the chat instead of summarizing. This is the headline result, not a low score.
- `FAILED:chat-reply`, `FAILED:tool-call`, `FAILED:empty`: same family.
- `FAILED:context`: the corpus didn't fit the model's window. Never silently truncated.

## 📝 Reporting rules

- Never publish a bare score. Show the breakdown: facts, stale and decoy hits, threads, both made-up-claim counts, latency, tokens. `score/report.py` refuses otherwise.
- Name the grader model and transport on every row.
- Show `status` next to `score`.
- Give the formula and corpus hash.
- Report made-up claims as raw count, rate per 100 checked, and which items.
- Charts and tables go to the project channel, not the images channel.

## ✅ Tests

```
python3 -W ignore -m unittest discover -s tests -t .
```

The scorer itself must be able to fail:

- `test_baseline_passes`, `test_a_*`: good summaries score high.
- `test_b_*`, `test_c_empty_fails`: continuations, chat stubs, fake tool calls and empty output are `FAILED`, never scored.
- `test_d_*`: stale values cost points; mentioning them as history doesn't.
- `test_e_*`, `test_f_*`: made-up numbers and fake grader quotes are caught.
- `test_breakdown.py`, `test_mutant.py`: every breakdown column is present; with `TK_DISABLE_GATE=1` or `TK_STRIP_COLUMN` set, the tests must fail.

The mutant test matters most: if turning off the check doesn't break the tests, the check is decoration.

## ⚠️ Honest limits

- **Synthetic is not real.** Fair for comparing models, a poor estimate for your history.
- **The summary check is heuristic.** Open an issue with raw output if it misfires.
- **Facts are matched by alias.** A paraphrase can be missed; a dump-everything summary scores well on facts.
- **Graders are biased**, especially toward themselves. Never let a model grade itself.
- **Costs are rarely reported**, and token counts depend on the tokenizer (here `o200k_base`).
- **Not comparable across corpora or seeds.** Compare identical input and name the hash.

Before publishing widely: keep a private held-back seed family, consider a canary token per corpus, and expect public numbers to decay. Refresh seeds.

## 🏷️ Model versions

Names on the board are the ones used, at the effort shown. Exact IDs: `results/*/meta.json`.

## License

MIT. Take it, fork it, run it on something I haven't thought of.

*Built because a model quietly stopped summarizing one night and every number we had called it "fine".* 🌸
