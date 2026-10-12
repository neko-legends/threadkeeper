# threadkeeper leaderboard

**composite** (v2): `composite = 100*(0.45*facts_score + 0.30*threads_score + 0.25*invention_score); facts_score=facts.net; threads_score=threads.score (judge, else mechanical); invention_score=1/(1+mechanical_inventions/3)`

**composite_v1** (kept for old comparisons): `100*(0.55*facts_net + 0.35*threads + 0.10*(1-min(1,mechanical_inventions/10)))`

Corpus session.jsonl sha256: 200k=`edb66f4e19b4aab06f9f8c082f887a6c3fbf61031d16db14741a17872a50c546`

Never read a composite alone: every row carries its breakdown, the judge that graded it and the transport. FAILED = the output was not a summary (continuation / chat-reply / empty / tool-call); it is not ranked. `invention mech` is the mechanical cross-check; `invention judge` is a ranking signal, never ground truth.

| # | model | effort | corpus | status | composite | composite_v1 | facts found/total | facts net % | stale | decoy hits | threads judge P/PA/L | threads mech P/PA/L | invention mech | invention judge | latency s | prompt tok | completion tok | reasoning tok | judge | transport |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | deepseek-v4-1-flash | default | 200k | SCORED | 93.0 | 98.0 | 49/50 | 98.3 | 0 | 0 | 8/0/0 | 7/1/0 | 1 | 3 | 31.514 | 219813 | 16221 | 12097 | z-ai-glm-5-3-flash | openai |
| 2 | deepseek-v4-1-flash | low | 200k | SCORED | 90.3 | 94.7 | 47/50 | 92.2 | 1 | 1 | 8/0/0 | 8/0/0 | 1 | 1 | 13.282 | 219813 | 4647 | 2511 | z-ai-glm-5-3-flash | openai |
| 3 | kimi-k3 | default | 200k | SCORED | 89.9 | 94.4 | 48/50 | 95.7 | 0 | 1 | 7/1/0 | 8/0/0 | 1 | 1 | 35.367 | 235791 | 3616 | 2049 | z-ai-glm-5-3-flash | openai |
| 4 | openai/gpt-6-astra | default | 200k | SCORED | 83.0 | 89.5 | 46/50 | 84.5 | 3 | 2 | 8/0/0 | 8/0/0 | 2 | 1 | 108.081 | n/a | n/a | n/a | opus | pi |
| 5 | z-ai-glm-5-3-flash | default | 200k | SCORED | 82.9 | 91.5 | 47/50 | 94.0 | 0 | 1 | 7/1/0 | 8/0/0 | 3 | 2 | 22.951 | 201112 | 3024 | 11 | kimi-k3 | openai |
| 6 | opus | max | 200k | SCORED | 75.7 | 84.8 | 49/50 | 94.8 | 2 | 1 | 6/2/0 | 7/1/0 | 8 | 0 | 413.45 | 311078 | 49363 | 41630 | openai/gpt-6-astra | claude |
