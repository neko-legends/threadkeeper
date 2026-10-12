# threadkeeper leaderboard

**composite** (v2): `composite = 100*(0.45*facts_score + 0.30*threads_score + 0.25*invention_score); facts_score=facts.net; threads_score=threads.score (judge, else mechanical); invention_score=1/(1+mechanical_inventions/3)`

**composite_v1** (kept for old comparisons): `100*(0.55*facts_net + 0.35*threads + 0.10*(1-min(1,mechanical_inventions/10)))`

**Model versions** (an alias is not a version: re-resolve on every run): `kimi-k3` via HTTP, resolved 2026-10-11; `deepseek-v4-1-flash` via HTTP, resolved 2026-10-11; `DeepSeek-V4.1-Flash-TF` via HTTP, resolved 2026-10-11; `opus` = `claude-opus-5-5` via claude CLI 2.1.289 (Claude Code), resolved 2026-10-11; `z-ai-glm-5-3-flash` via HTTP, resolved 2026-10-11; `venice/qwen-3-8-flash` via pi CLI 0.99.1, resolved 2026-10-11; `sonnet` = `claude-sonnet-5-5` via claude CLI 2.1.289 (Claude Code), resolved 2026-10-11; `openai/gpt-6-astra` via pi CLI 0.99.1, resolved 2026-10-11; `venice/grok-4-7` via pi CLI 0.99.1, resolved 2026-10-11

Corpus session.jsonl sha256: 128k=`115686d990527833d9df9ea08407e087340103865bb244516a52599a8d75728e`; 200k=`edb66f4e19b4aab06f9f8c082f887a6c3fbf61031d16db14741a17872a50c546`; 32k=`86b9627afc4823cb8c7ec3cd7a4a435d09b3314dee25cc66ecea1c7443db218f`

Never read a composite alone: every row carries its breakdown, the judge that graded it and the transport. FAILED = the output was not a summary (continuation / chat-reply / empty / tool-call / prompt-echo); it fails the gate, is not ranked, is not sent to a judge, and carries its gate reason in the status cell. Rank `#` restarts per corpus. `invention mech` is the mechanical cross-check (raw count favours terse summaries: compare `mech per 100 checked`);  `invention judge` is a ranking signal, never ground truth.

| # | model | effort | corpus | status | composite | composite_v1 | facts found/total | facts net % | stale | decoy hits | threads judge P/PA/L | threads mech P/PA/L | invention mech | mech checked (quotes+nums) | mech per 100 checked | invention judge | latency s | prompt tok | completion tok | reasoning tok | judge | transport | resolved model id | tool version | effort flag |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | kimi-k3 | low | 128k | SCORED | 98.5 | 98.1 | 48/50 | 96.5 | 0 | 0 | 8/0/0 | 7/1/0 | 0 | 35 | 0.0 | 0 | 19.089 | 152587 | 1331 | 5 | venice/gemini-3-8-flash | openai | kimi-k3 | n/a (HTTP) | reasoning_effort=low |
| 2 | kimi-k3 | default | 128k | SCORED | 97.3 | 96.9 | 49/50 | 98.3 | 0 | 0 | 7/1/0 | 8/0/0 | 0 | 51 | 0.0 | 0 | 36.673 | 152586 | 3995 | 2171 | venice/gemini-3-8-flash | openai | kimi-k3 | n/a (HTTP) | (none: flag omitted, provider default) |
| 3 | deepseek-v4-1-flash | default | 128k | SCORED | 96.6 | 95.9 | 49/50 | 96.5 | 1 | 0 | 7/1/0 | 8/0/0 | 0 | 99 | 0.0 | 0 | 16.269 | 141393 | 7246 | 3766 | venice/gemini-3-8-flash | openai | deepseek-v4-1-flash | n/a (HTTP) | (none: flag omitted, provider default) |
| 4 | DeepSeek-V4.1-Flash-TF | default | 128k | SCORED | 95.4 | 94.5 | 48/50 | 94.0 | 1 | 1 | 7/1/0 | 8/0/0 | 0 | 43 | 0.0 | 3 | 59.922 | 140568 | 3288 | n/a | venice/gemini-3-8-flash | openai | DeepSeek-V4.1-Flash-TF | n/a (HTTP) | (none: flag omitted, provider default) |
| 5 | opus | default | 128k | SCORED | 95.4 | 94.5 | 48/50 | 94.0 | 1 | 1 | 7/1/0 | 8/0/0 | 0 | 93 | 0.0 | 0 | 60.459 | 199578 | 6946 | 2070 | venice/gemini-3-8-flash | claude | claude-opus-5-5 | 2.1.289 (Claude Code) | (none: flag omitted, provider default) |
| 6 | z-ai-glm-5-3-flash | default | 128k | SCORED | 95.0 | 94.0 | 48/50 | 93.1 | 1 | 2 | 7/1/0 | 8/0/0 | 0 | 50 | 0.0 | 1 | 20.23 | 127512 | 2172 | 11 | venice/gemini-3-8-flash | openai | z-ai-glm-5-3-flash | n/a (HTTP) | (none: flag omitted, provider default) |
| 7 | z-ai-glm-5-3-flash | high | 128k | SCORED | 95.0 | 94.0 | 46/50 | 93.1 | 0 | 0 | 7/1/0 | 8/0/0 | 0 | 48 | 0.0 | 2 | 29.224 | 127512 | 2152 | 11 | venice/gemini-3-8-flash | openai | z-ai-glm-5-3-flash | n/a (HTTP) | reasoning_effort=high |
| 8 | deepseek-v4-1-flash | low | 128k | SCORED | 94.7 | 93.7 | 48/50 | 96.5 | 0 | 0 | 6/2/0 | 7/1/0 | 0 | 64 | 0.0 | 2 | 14.428 | 141393 | 5299 | 2482 | venice/gemini-3-8-flash | openai | deepseek-v4-1-flash | n/a (HTTP) | reasoning_effort=low |
| 9 | venice/qwen-3-8-flash | default | 128k | SCORED | 94.6 | 93.5 | 47/50 | 92.2 | 1 | 1 | 7/1/0 | 8/0/0 | 0 | 56 | 0.0 | 0 | 323.356 | n/a | n/a | n/a | venice/gemini-3-8-flash | pi | venice/qwen-3-8-flash | 0.99.1 | (none: flag omitted, provider default) |
| 10 | sonnet | default | 128k | SCORED | 93.2 | 91.8 | 46/50 | 93.1 | 0 | 0 | 6/2/0 | 8/0/0 | 0 | 35 | 0.0 | 0 | 35.34 | 199586 | 2867 | 0 | venice/gemini-3-8-flash | claude | claude-sonnet-5-5 | 2.1.289 (Claude Code) | (none: flag omitted, provider default) |
| 11 | openai/gpt-6-astra | high | 128k | SCORED | 90.6 | 95.2 | 49/50 | 93.1 | 3 | 1 | 8/0/0 | 8/0/0 | 1 | 131 | 0.76 | 0 | 100.101 | n/a | n/a | n/a | venice/gemini-3-8-flash | pi | openai/gpt-6-astra | 0.99.1 | --thinking high |
| 12 | venice/qwen-3-8-flash | high | 128k | SCORED | 89.2 | 93.5 | 48/50 | 94.0 | 1 | 1 | 7/1/0 | 8/0/0 | 1 | 114 | 0.88 | 0 | 333.665 | n/a | n/a | n/a | venice/gemini-3-8-flash | pi | venice/qwen-3-8-flash | 0.99.1 | --thinking high |
| 13 | opus | max | 128k | SCORED | 85.8 | 93.0 | 49/50 | 94.8 | 2 | 1 | 7/1/0 | 8/0/0 | 2 | 157 | 1.27 | 0 | 404.639 | 199578 | 48807 | 42025 | venice/gemini-3-8-flash | claude | claude-opus-5-5 | 2.1.289 (Claude Code) | --effort max |
| 14 | z-ai-glm-5-3-flash | low | 128k | SCORED | 85.7 | 89.2 | 45/50 | 86.2 | 1 | 2 | 7/1/0 | 8/0/0 | 1 | 51 | 1.96 | 1 | 12.969 | 127512 | 1994 | 11 | venice/gemini-3-8-flash | openai | z-ai-glm-5-3-flash | n/a (HTTP) | reasoning_effort=low |
| 15 | openai/gpt-6-astra | default | 128k | SCORED | 83.8 | 87.0 | 46/50 | 86.2 | 2 | 2 | 6/2/0 | 8/0/0 | 1 | 143 | 0.7 | 0 | 111.701 | n/a | n/a | n/a | venice/gemini-3-8-flash | pi | openai/gpt-6-astra | 0.99.1 | (none: flag omitted, provider default) |
| - | venice/grok-4-7 | default | 128k | FAILED (prompt-echo): output is the compaction prompt echoed back, not a summary | - | - | - | - | - | - | - | - | - | - | - | - | 35.467 | n/a | n/a | n/a | none (not graded: failed the summary gate) | pi | venice/grok-4-7 | 0.99.1 | (none: flag omitted, provider default) |
| 1 | deepseek-v4-1-flash | default | 200k | SCORED | 99.2 | 99.0 | 49/50 | 98.3 | 0 | 0 | 8/0/0 | 7/1/0 | 0 | 125 | 0.0 | 3 | 31.514 | 219813 | 16221 | 12097 | z-ai-glm-5-3-flash | openai | deepseek-v4-1-flash | n/a (HTTP) | (none: flag omitted, provider default) |
| 2 | kimi-k3 | default | 200k | SCORED | 96.2 | 95.4 | 48/50 | 95.7 | 0 | 1 | 7/1/0 | 8/0/0 | 0 | 43 | 0.0 | 1 | 35.367 | 235791 | 3616 | 2049 | z-ai-glm-5-3-flash | openai | kimi-k3 | n/a (HTTP) | (none: flag omitted, provider default) |
| 3 | openai/gpt-6-astra | default | 200k | SCORED | 93.0 | 91.5 | 46/50 | 84.5 | 3 | 2 | 8/0/0 | 8/0/0 | 0 | 135 | 0.0 | 0 | 108.081 | n/a | n/a | n/a | opus | pi | openai/gpt-6-astra | 0.99.1 | (none: flag omitted, provider default) |
| 4 | deepseek-v4-1-flash | low | 200k | SCORED | 90.3 | 94.7 | 47/50 | 92.2 | 1 | 1 | 8/0/0 | 8/0/0 | 1 | 39 | 2.56 | 1 | 13.282 | 219813 | 4647 | 2511 | z-ai-glm-5-3-flash | openai | deepseek-v4-1-flash | n/a (HTTP) | reasoning_effort=low |
| 5 | z-ai-glm-5-3-flash | default | 200k | SCORED | 85.4 | 92.5 | 47/50 | 94.0 | 0 | 1 | 7/1/0 | 8/0/0 | 2 | 65 | 3.08 | 2 | 22.951 | 201112 | 3024 | 11 | kimi-k3 | openai | z-ai-glm-5-3-flash | n/a (HTTP) | (none: flag omitted, provider default) |
| 6 | opus | max | 200k | SCORED | 78.3 | 87.8 | 49/50 | 94.8 | 2 | 1 | 6/2/0 | 7/1/0 | 5 | 203 | 2.46 | 0 | 413.45 | 311078 | 49363 | 41630 | openai/gpt-6-astra | claude | claude-opus-5-5 | 2.1.289 (Claude Code) | --effort max |
| 1 | z-ai-glm-5-3-flash | medium | 32k | SCORED | 92.6 | 97.6 | 49/50 | 97.4 | 0 | 1 | 8/0/0 | 8/0/0 | 1 | 61 | 1.64 | 1 | 32.468 | 31957 | 4059 | 2177 | none (mechanical only) | openai | z-ai-glm-5-3-flash | n/a (HTTP) | reasoning_effort=medium |

## Judge comparison: one judge for every arm vs the original per-arm judges

Single judge: `venice/gemini-3-8-flash` (a family that grades nothing else on this board). `multijudge` = the original rows, each graded by a different judge (kept as `score_multijudge.json`); those judge counts are NOT comparable across rows, the single-judge column is. Mechanical invention needs no judge and is identical in both.

| model/effort | mech inv | multijudge (judge) | inv judge (multi) | threads P/PA/L (multi) | inv judge (single) | threads P/PA/L (single) | composite multi | composite single |
|---|---|---|---|---|---|---|---|---|
| kimi-k3__low | 0 | z-ai-glm-5-3-flash | 1 | 7/1/0 | 0 | 8/0/0 | 96.6 | 98.5 |
| kimi-k3__default | 0 | z-ai-glm-5-3-flash | 0 | 8/0/0 | 0 | 7/1/0 | 99.2 | 97.3 |
| deepseek-v4-1-flash__default | 0 | z-ai-glm-5-3-flash | 1 | 8/0/0 | 0 | 7/1/0 | 98.5 | 96.6 |
| opus__default | 0 | openai/gpt-6-astra | 1 | 7/1/0 | 0 | 7/1/0 | 95.4 | 95.4 |
| z-ai-glm-5-3-flash__default | 0 | kimi-k3 | 2 | 8/0/0 | 1 | 7/1/0 | 96.9 | 95.0 |
| z-ai-glm-5-3-flash__high | 0 | kimi-k3 | 2 | 7/1/0 | 2 | 7/1/0 | 95.0 | 95.0 |
| deepseek-v4-1-flash__low | 0 | z-ai-glm-5-3-flash | 2 | 8/0/0 | 2 | 6/2/0 | 98.5 | 94.7 |
| openai-gpt-6-astra__high | 1 | opus | 1 | 8/0/0 | 0 | 8/0/0 | 90.6 | 90.6 |
| opus__max | 2 | openai/gpt-6-astra | 7 | 6/2/0 | 0 | 7/1/0 | 83.9 | 85.8 |
| z-ai-glm-5-3-flash__low | 1 | kimi-k3 | 1 | 8/0/0 | 1 | 7/1/0 | 87.5 | 85.7 |
| openai-gpt-6-astra__default | 1 | opus | 1 | 8/0/0 | 0 | 6/2/0 | 87.5 | 83.8 |
