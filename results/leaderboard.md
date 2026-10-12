# threadkeeper leaderboard

**composite** (v2): `composite = 100*(0.45*facts_score + 0.30*threads_score + 0.25*invention_score); facts_score=facts.net; threads_score=threads.score (judge, else mechanical); invention_score=1/(1+mechanical_inventions/3)`

**composite_v1** (kept for old comparisons): `100*(0.55*facts_net + 0.35*threads + 0.10*(1-min(1,mechanical_inventions/10)))`

Corpus session.jsonl sha256: 128k=`115686d990527833d9df9ea08407e087340103865bb244516a52599a8d75728e`

Never read a composite alone: every row carries its breakdown, the judge that graded it and the transport. FAILED = the output was not a summary (continuation / chat-reply / empty / tool-call); it is not ranked. `invention mech` is the mechanical cross-check (raw count favours terse summaries: compare `mech per 100 checked`);  `invention judge` is a ranking signal, never ground truth.

| # | model | effort | corpus | status | composite | composite_v1 | facts found/total | facts net % | stale | decoy hits | threads judge P/PA/L | threads mech P/PA/L | invention mech | mech checked (quotes+nums) | mech per 100 checked | invention judge | latency s | prompt tok | completion tok | reasoning tok | judge | transport |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | kimi-k3 | default | 128k | SCORED | 99.2 | 99.0 | 49/50 | 98.3 | 0 | 0 | 8/0/0 | 8/0/0 | 0 | 53 | 0.0 | 0 | 36.673 | 152586 | 3995 | 2171 | z-ai-glm-5-3-flash | openai |
| 2 | kimi-k3 | low | 128k | SCORED | 96.6 | 95.9 | 48/50 | 96.5 | 0 | 0 | 7/1/0 | 7/1/0 | 0 | 37 | 0.0 | 1 | 19.089 | 152587 | 1331 | 5 | z-ai-glm-5-3-flash | openai |
| 3 | deepseek-v4-1-flash | default | 128k | SCORED | 92.2 | 97.1 | 49/50 | 96.5 | 1 | 0 | 8/0/0 | 8/0/0 | 1 | 112 | 0.89 | 1 | 16.269 | 141393 | 7246 | 3766 | z-ai-glm-5-3-flash | openai |
| 4 | deepseek-v4-1-flash | low | 128k | SCORED | 92.2 | 97.1 | 48/50 | 96.5 | 0 | 0 | 8/0/0 | 7/1/0 | 1 | 67 | 1.49 | 2 | 14.428 | 141393 | 5299 | 2482 | z-ai-glm-5-3-flash | openai |
| 5 | z-ai-glm-5-3-flash | default | 128k | SCORED | 90.6 | 95.2 | 48/50 | 93.1 | 1 | 2 | 8/0/0 | 8/0/0 | 1 | 57 | 1.75 | 2 | 20.23 | 127512 | 2172 | 11 | kimi-k3 | openai |
| 6 | z-ai-glm-5-3-flash | high | 128k | SCORED | 88.8 | 93.0 | 46/50 | 93.1 | 0 | 0 | 7/1/0 | 8/0/0 | 1 | 51 | 1.96 | 2 | 29.224 | 127512 | 2152 | 11 | kimi-k3 | openai |
| 7 | opus | default | 128k | SCORED | 85.4 | 92.5 | 48/50 | 94.0 | 1 | 1 | 7/1/0 | 8/0/0 | 2 | 103 | 1.94 | 1 | 60.459 | 199578 | 6946 | 2070 | openai/gpt-6-astra | claude |
| 8 | openai/gpt-6-astra | high | 128k | SCORED | 84.4 | 93.2 | 49/50 | 93.1 | 3 | 1 | 8/0/0 | 8/0/0 | 3 | 148 | 2.03 | 1 | 100.101 | n/a | n/a | n/a | opus | pi |
| 9 | openai/gpt-6-astra | default | 128k | SCORED | 83.8 | 90.4 | 46/50 | 86.2 | 2 | 2 | 8/0/0 | 8/0/0 | 2 | 159 | 1.26 | 1 | 111.701 | n/a | n/a | n/a | opus | pi |
| 10 | z-ai-glm-5-3-flash | low | 128k | SCORED | 83.8 | 90.4 | 45/50 | 86.2 | 1 | 2 | 8/0/0 | 8/0/0 | 2 | 55 | 3.64 | 1 | 12.969 | 127512 | 1994 | 11 | kimi-k3 | openai |
| 11 | opus | max | 128k | SCORED | 79.6 | 88.8 | 49/50 | 94.8 | 2 | 1 | 6/2/0 | 8/0/0 | 4 | 171 | 2.34 | 7 | 404.639 | 199578 | 48807 | 42025 | openai/gpt-6-astra | claude |
