# threadkeeper 🌸

*A benchmark for the unglamorous part of long conversations: remembering what mattered.*

> Every summary is a promise that nothing important was lost.
> `threadkeeper` is how you find out whether the promise was kept — and, more usefully, whether the model even **tried**.

Long agent sessions eventually get compacted: the history is replaced by a summary, and everything after that depends on the summary being faithful. `threadkeeper` hands a model a long synthetic session, asks it to write the summary that would replace it, and grades the result on what survived, what got corrupted, and what got invented.

Everything in the corpus is invented — a solo founder and a coding agent shipping a small web app over several days, complete with dead ends, a bug hunt, a vendor email thread, a reversed decision and a teammate disagreement. It is generated deterministically from a seed, with no LLM and no network. Generating, running and scoring are **pure Python 3 standard library**; `tiktoken` and `matplotlib` are optional extras.

---

## The failure this was built around

Most compaction evaluations measure *how much* of the session a summary kept. That misses the failure that actually bites in production:

**At some reasoning-effort settings, a model stops summarizing and starts continuing the conversation.** It replies in character. It emits fake tool calls. It returns a chat stub. Every one of those outputs is *fluent*, and a naive fact-scorer gives them a low score — one out of fifty facts — which reads as **"mediocre"** rather than **"broken"**.

So `threadkeeper` classifies before it scores. Its first stage is a **summary gate**: is this output a summary at all? If it is a continuation, a chat reply, a tool call or empty, the arm is marked `FAILED`, and no score is attached. A run that never summarized should never appear as a low number on a leaderboard.

---

## Quick start

```bash
# 1. score a model you can reach over HTTP
python3 -m run --model z-ai-glm-5-3-flash --effort medium --corpus 128k \
  --base-url https://api.venice.ai/api/v1 --api-key-env VENICE_API_KEY

# 2. grade the summary it produced (judge = a model that is NOT the one being graded)
python3 -m score --judge-base-url https://api.venice.ai/api/v1 \
  --judge-model z-ai-glm-5-3-flash

# 3. see the board
cat results/leaderboard.md
```

Optional: `pip install tiktoken matplotlib` for exact token counts and the chart.

---

## What it measures

| stage | question | how |
|---|---|---|
| **Summary gate** | Is this even a summary? | structural classifier → `SCORED` or `FAILED:<reason>` |
| **Facts** | Did the concrete facts survive? | 50 planted facts (names, ports, paths, prices, hashes, vendor details), normalised boundary-aware alias matching |
| **Corrections** | Did it keep the *current* value? | 7 facts are stated, then corrected later. Only the latest earns credit; asserting a stale value as current is penalised. Cueing it honestly ("was", "moved from") is not |
| **Decoys** | Did it swallow the near-miss? | near-duplicate vendor name, near-duplicate ticket number, an unrelated commit hash |
| **Threads** | Did the *open loops* survive? | 8 open items graded `PRESERVED` / `PARTIAL` / `LOST` by a rubric judge, with a mechanical keyword fallback reported alongside |
| **Invention** | Did it make things up? | two independent measures — a **mechanical cross-check** (every number, hash and quoted span must appear in the session) and a **blind judge** whose own quoted evidence must be an exact substring or the item is discarded |

That last row is why invention is reported twice. Our own judge was caught **fabricating quotes** — inventing evidence for a claim it wanted to make. A judge-only invention count is a ranking signal, never ground truth.

---

## The shipped corpora

| corpus | tokens (o200k) | messages | seed |
|---|---|---|---|
| `32k` | ~31,000 | 277 | 3201 |
| `128k` | ~127,000 | 886 | 12801 |
| `200k` | ~200,000 | 1226 | 20001 |

Each ships with `session.jsonl`, `ground_truth.json` (facts + aliases + which values are stale, thread criteria, decoys) and a `reference_summary.md`. SHA256s live in `corpora/MANIFEST.json`.

**A reference point from our smoke run:** a cheap flash model scored **97.6** on `32k`. That is not a compliment to the model so much as a warning about the corpus — **32k is too easy to separate strong models.** Use `128k` when you want a spread.

---

## Make your own — and please do

```bash
python3 -m gen --size 128k --seed 12345 --out /tmp/mine
```

**This is the part that matters.** A published benchmark becomes a training target: publish it, wait a version or two, and models will have learned its facts, its decoys and its phrasing. The leaderboard stops measuring compaction and starts measuring familiarity. That is not a flaw you can fix by hiding the numbers — it is what happens to every fixed public test.

So the generator is the product, and the three corpora are demonstrations. The honest use is either:

1. **Generate your own instance** (`--seed` anything), so results are reproducible *for you* without being a target anyone can train on. Report the seed and the corpus hash alongside your numbers.
2. **Test with your own real sessions** — the truest version, and the reason our own run was done privately. Real history is what you actually care about; it is also, by definition, not something anyone trained on.

Treat the shipped corpora as historical reference points. Once they are public, their scores are a museum, not a standard.

---

## Reading the results

- `SCORED` — the output was a summary, and the score is meaningful.
- `FAILED:continuation` — the model kept writing the conversation instead of summarizing it. **This is the headline result, not a low score.**
- `FAILED:chat-reply`, `FAILED:tool-call`, `FAILED:empty` — same family.
- `FAILED:context` — the corpus did not fit the model's window. Reported, never silently truncated.

Report `status` next to `score`, always. A leaderboard that hides failures is measuring something else.

---

## Tests

```
python3 -W ignore -m unittest discover -s tests -t .
```

Thirteen tests. The point of most of them is that the **scorer itself can fail**:

| test | what it guards |
|---|---|
| `test_baseline_passes` | the happy path scores |
| `test_a_perfect_summary_near_max` | a hand-written perfect summary approaches full marks |
| `test_a2_reference_summary_max` | the shipped reference summary scores ≥99 |
| `test_b_continuations_fail_gate` | in-character continuations are `FAILED`, never scored |
| `test_b2_chat_reply_and_toolcall` | a chat stub and a fake tool call are `FAILED` too |
| `test_c_empty_fails` | empty and whitespace output is `FAILED`, not zero-but-scored |
| `test_d_stale_values_penalised` | repeating corrected facts as current costs points |
| `test_d2_cued_stale_not_penalised` | mentioning the old value *as history* is not punished |
| `test_e_invented_number_flagged` | a made-up number, hash and quote are caught mechanically |
| `test_f_judge_fabricated_quotes_dropped` | when the judge invents its evidence, the item is dropped and downgraded |
| `test_every_fact_planted_and_stale_present` | the ground truth actually contains what it claims |
| `test_generator_deterministic` | same seed → byte-identical corpus |
| `test_mutant.py` | **run the suite with `TK_DISABLE_GATE=1` and the gate tests fail** |

That last one is the most important line in this repository. If disabling the summary gate does not break the tests, the gate is decoration.

---

## Warnings and honest limits

1. **Synthetic is not real.** A generated session has cleaner facts, tidier threads and more obvious corrections than a real one. It is a fair *relative* comparison between models and a poor absolute estimate of how a model will handle your history.
2. **The gate is heuristically validated.** Continuation, chat-reply, tool-call and empty were tested against hand-written fixtures and a handful of real outputs. Expect false classifications on unusual serving behaviour — and please open an issue with the raw output when you find one.
3. **Facts are alias-matched.** A correct paraphrase that avoids every alias is missed; conversely, a summary that dumps everything scores well on facts. Only the thread and invention stages push back on dumping (and any length limit you put in the prompt).
4. **Judge models carry their own biases** — self-preference above all. **Never let a model grade itself.** Use a judge from a different family and log which judge produced which row.
5. **Costs are rarely reported.** OpenAI-compatible usage blocks often omit pricing; compare tokens, and compute cost from your own rate card.
6. **Token counts depend on the tokenizer.** Counts here are `o200k_base`. A different tokenizer gives different sizes, and a model's real context limit is not the same number as its advertised one.
7. **`32k` will not separate strong models.** Use `128k` or larger for a ranking; use `32k` for a quick smoke check.
8. **Results are not comparable across corpora or seeds.** Only compare arms that saw byte-identical input, and say which hash.

### Before you publish a leaderboard widely

- judge outside the graded family, and log it;
- report `status` alongside every score;
- publish the corpus hash and the seed next to the numbers;
- keep a **held-back seed family** you never publish, for the question the public one can no longer answer;
- consider embedding a **canary token** per generated corpus, so later training on it is detectable;
- and expect the public numbers to decay into familiarity. Refresh seeds instead of defending a scoreboard.

---

## License

MIT. Take it, fork it, run it against something I have not thought of.

*Built because a model quietly stopped summarizing one night and every number we had called it "fine".* 🌸
