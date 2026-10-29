# Eval results summary

One row per (prompt, model, split) run on `seed-v1`. Tuning rows guide prompt changes; the holdout row is run once (Session 2.5) and is the number quoted in the README. Full reports and per-item predictions are in the files next to this one.

## Tuning

| prompt | model | split | severity macro-F1 [95% CI] | sev acc | comp acc | cat acc | conf≥0.7 acc (share) | valid first try | needs_manual | $/100 | p50 / p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| classify/v1 | global.anthropic.claude-haiku-4-5-20251001-v1:0 | tuning | **0.726** [0.620-0.817] | 71.7% | 91.7% | 90.0% | 71.7% (100.0%) | 100.0% | 0.0% | $0.070 | 4482 / 5561 |

## Holdout

Not run yet.
