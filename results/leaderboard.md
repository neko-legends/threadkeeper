# threadkeeper leaderboard

FAILED = the output was not a summary (continuation / chat-reply / empty / tool-call); it is not ranked. `invention judge` is a ranking signal, not ground truth.

| # | model | effort | corpus | status | score | facts | stale/decoy | threads P/PA/L | invention mech/judge | latency s | tok p/c/r | cost $ | judge | transport |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | kimi-k3 | default | 128k | SCORED | 99.0 | 49/50 (98.3%) | 0/0 | 8/0/0 | 0/0 | 36.673 | 152586/3995/2171 | n/a | z-ai-glm-5-3-flash | openai |
| 2 | deepseek-v4-1-flash | default | 128k | SCORED | 97.1 | 49/50 (96.5%) | 1/0 | 8/0/0 | 1/1 | 16.269 | 141393/7246/3766 | n/a | z-ai-glm-5-3-flash | openai |
| 3 | deepseek-v4-1-flash | low | 128k | SCORED | 97.1 | 48/50 (96.5%) | 0/0 | 8/0/0 | 1/2 | 14.428 | 141393/5299/2482 | n/a | z-ai-glm-5-3-flash | openai |
| 4 | kimi-k3 | low | 128k | SCORED | 95.9 | 48/50 (96.5%) | 0/0 | 7/1/0 | 0/1 | 19.089 | 152587/1331/5 | n/a | z-ai-glm-5-3-flash | openai |
| 5 | z-ai-glm-5-3-flash | default | 128k | SCORED | 95.2 | 48/50 (93.1%) | 1/2 | 8/0/0 | 1/2 | 20.23 | 127512/2172/11 | n/a | kimi-k3 | openai |
| 6 | openai/gpt-6-astra | high | 128k | SCORED | 93.2 | 49/50 (93.1%) | 3/1 | 8/0/0 | 3/1 | 100.101 | None/None/None | n/a | opus | pi |
| 7 | opus | default | 128k | SCORED | 92.5 | 48/50 (94.0%) | 1/1 | 7/1/0 | 2/1 | 60.459 | 199578/6946/2070 | n/a | openai/gpt-6-astra | claude |
| 8 | openai/gpt-6-astra | default | 128k | SCORED | 90.4 | 46/50 (86.2%) | 2/2 | 8/0/0 | 2/1 | 111.701 | None/None/None | n/a | opus | pi |
| 9 | z-ai-glm-5-3-flash | low | 128k | SCORED | 90.4 | 45/50 (86.2%) | 1/2 | 8/0/0 | 2/1 | 12.969 | 127512/1994/11 | n/a | kimi-k3 | openai |
| 10 | opus | max | 128k | SCORED | 88.8 | 49/50 (94.8%) | 2/1 | 6/2/0 | 4/7 | 404.639 | 199578/48807/42025 | n/a | openai/gpt-6-astra | claude |
