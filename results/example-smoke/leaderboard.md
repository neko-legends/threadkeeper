# threadkeeper leaderboard

**composite** (v2): `composite = 100*(0.45*facts_score + 0.30*threads_score + 0.25*invention_score); facts_score=facts.net; threads_score=threads.score (judge, else mechanical); invention_score=1/(1+mechanical_inventions/3)`

**composite_v1** (kept for old comparisons): `100*(0.55*facts_net + 0.35*threads + 0.10*(1-min(1,mechanical_inventions/10)))`

Corpus session.jsonl sha256: 32k=`86b9627afc4823cb8c7ec3cd7a4a435d09b3314dee25cc66ecea1c7443db218f`

Never read a composite alone: every row carries its breakdown, the judge that graded it and the transport. FAILED = the output was not a summary (continuation / chat-reply / empty / tool-call); it is not ranked. `invention mech` is the mechanical cross-check; `invention judge` is a ranking signal, never ground truth.

| # | model | effort | corpus | status | composite | composite_v1 | facts found/total | facts net % | stale | decoy hits | threads judge P/PA/L | threads mech P/PA/L | invention mech | invention judge | latency s | prompt tok | completion tok | reasoning tok | judge | transport |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | z-ai-glm-5-3-flash | medium | 32k | SCORED | 92.6 | 97.6 | 49/50 | 97.4 | 0 | 1 | 8/0/0 | 8/0/0 | 1 | 1 | 32.468 | 31957 | 4059 | 2177 | none (JUDGE CALL FAILED) | openai |
