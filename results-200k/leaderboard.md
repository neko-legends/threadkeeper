# threadkeeper leaderboard

FAILED = the output was not a summary (continuation / chat-reply / empty / tool-call); it is not ranked. `invention judge` is a ranking signal, not ground truth.

| # | model | effort | corpus | status | score | facts | stale/decoy | threads P/PA/L | invention mech/judge | latency s | tok p/c/r | cost $ | judge | transport |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | deepseek-v4-1-flash | default | 200k | SCORED | 98.0 | 49/50 (98.3%) | 0/0 | 8/0/0 | 1/3 | 31.514 | 219813/16221/12097 | n/a | z-ai-glm-5-3-flash | openai |
| 2 | deepseek-v4-1-flash | low | 200k | SCORED | 94.7 | 47/50 (92.2%) | 1/1 | 8/0/0 | 1/1 | 13.282 | 219813/4647/2511 | n/a | z-ai-glm-5-3-flash | openai |
| 3 | kimi-k3 | default | 200k | SCORED | 94.4 | 48/50 (95.7%) | 0/1 | 7/1/0 | 1/1 | 35.367 | 235791/3616/2049 | n/a | z-ai-glm-5-3-flash | openai |
| 4 | z-ai-glm-5-3-flash | default | 200k | SCORED | 91.5 | 47/50 (94.0%) | 0/1 | 7/1/0 | 3/2 | 22.951 | 201112/3024/11 | n/a | kimi-k3 | openai |
| 5 | openai/gpt-6-astra | default | 200k | SCORED | 89.5 | 46/50 (84.5%) | 3/2 | 8/0/0 | 2/1 | 108.081 | None/None/None | n/a | opus | pi |
