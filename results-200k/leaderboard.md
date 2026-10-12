# threadkeeper leaderboard

**composite** (v2): `composite = 100*(0.45*facts_score + 0.30*threads_score + 0.25*invention_score); facts_score=facts.net; threads_score=threads.score (judge, else mechanical); invention_score=1/(1+mechanical_inventions/3)`

**composite_v1** (kept for old comparisons): `100*(0.55*facts_net + 0.35*threads + 0.10*(1-min(1,mechanical_inventions/10)))`

**Model versions** (an alias is not a version: re-resolve on every run): `deepseek-v4-1-flash` via HTTP, resolved 2026-10-11; `kimi-k3` via HTTP, resolved 2026-10-11; `openai/gpt-6-astra` via pi CLI 0.99.1, resolved 2026-10-11; `z-ai-glm-5-3-flash` via HTTP, resolved 2026-10-11; `opus` = `claude-opus-5-5` via claude CLI 2.1.289 (Claude Code), resolved 2026-10-11

Corpus session.jsonl sha256: 200k=`edb66f4e19b4aab06f9f8c082f887a6c3fbf61031d16db14741a17872a50c546`

Never read a composite alone: every row carries its breakdown, the judge that graded it and the transport. FAILED = the output was not a summary (continuation / chat-reply / empty / tool-call); it is not ranked. `invention mech` is the mechanical cross-check (raw count favours terse summaries: compare `mech per 100 checked`);  `invention judge` is a ranking signal, never ground truth.

| # | model | effort | corpus | status | composite | composite_v1 | facts found/total | facts net % | stale | decoy hits | threads judge P/PA/L | threads mech P/PA/L | invention mech | mech checked (quotes+nums) | mech per 100 checked | invention judge | latency s | prompt tok | completion tok | reasoning tok | judge | transport | resolved model id | tool version | effort flag |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | deepseek-v4-1-flash | default | 200k | SCORED | 99.2 | 99.0 | 49/50 | 98.3 | 0 | 0 | 8/0/0 | 7/1/0 | 0 | 125 | 0.0 | 3 | 31.514 | 219813 | 16221 | 12097 | z-ai-glm-5-3-flash | openai | deepseek-v4-1-flash | n/a (HTTP) | (none: flag omitted, provider default) |
| 2 | kimi-k3 | default | 200k | SCORED | 96.2 | 95.4 | 48/50 | 95.7 | 0 | 1 | 7/1/0 | 8/0/0 | 0 | 43 | 0.0 | 1 | 35.367 | 235791 | 3616 | 2049 | z-ai-glm-5-3-flash | openai | kimi-k3 | n/a (HTTP) | (none: flag omitted, provider default) |
| 3 | openai/gpt-6-astra | default | 200k | SCORED | 93.0 | 91.5 | 46/50 | 84.5 | 3 | 2 | 8/0/0 | 8/0/0 | 0 | 135 | 0.0 | 1 | 108.081 | n/a | n/a | n/a | opus | pi | openai/gpt-6-astra | 0.99.1 | (none: flag omitted, provider default) |
| 4 | deepseek-v4-1-flash | low | 200k | SCORED | 90.3 | 94.7 | 47/50 | 92.2 | 1 | 1 | 8/0/0 | 8/0/0 | 1 | 39 | 2.56 | 1 | 13.282 | 219813 | 4647 | 2511 | z-ai-glm-5-3-flash | openai | deepseek-v4-1-flash | n/a (HTTP) | reasoning_effort=low |
| 5 | z-ai-glm-5-3-flash | default | 200k | SCORED | 85.4 | 92.5 | 47/50 | 94.0 | 0 | 1 | 7/1/0 | 8/0/0 | 2 | 65 | 3.08 | 2 | 22.951 | 201112 | 3024 | 11 | kimi-k3 | openai | z-ai-glm-5-3-flash | n/a (HTTP) | (none: flag omitted, provider default) |
| 6 | opus | max | 200k | SCORED | 78.3 | 87.8 | 49/50 | 94.8 | 2 | 1 | 6/2/0 | 7/1/0 | 5 | 203 | 2.46 | 0 | 413.45 | 311078 | 49363 | 41630 | openai/gpt-6-astra | claude | claude-opus-5-5 | 2.1.289 (Claude Code) | --effort max |
