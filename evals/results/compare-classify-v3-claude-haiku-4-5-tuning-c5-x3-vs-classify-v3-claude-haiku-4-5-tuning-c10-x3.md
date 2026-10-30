# classify-v3-claude-haiku-4-5-tuning-c5-x3 vs classify-v3-claude-haiku-4-5-tuning-c10-x3

seed-v1/tuning · 60 items · paired bootstrap over items (repeats stay together), 95% CI of candidate minus base.

**Verdict (severity macro-F1, TL-08): no significant difference.** **Cost gate failed (> +15%).**

| metric | base | candidate | Δ [95% CI] |
|---|---|---|---|
| severity macro-F1 | 0.746 | 0.726 | **-0.021** [-0.100, +0.075] |
| severity accuracy | 0.739 | 0.706 | **-0.033** [-0.106, +0.056] |
| component accuracy | 0.939 | 0.911 | **-0.028** [-0.061, +0.000] |
| category accuracy | 0.917 | 0.889 | **-0.028** [-0.072, +0.017] |

| run-level | base | candidate |
|---|---|---|
| $ per 100 incidents | $0.073 | $0.105 |
| p95 latency ms | 5230 | 3192 |
| schema-valid first try | 100.0% | 91.9% |
| confidence ≥ 0.7 share | 100.0% | 97.2% |

## Fixed (5)

- **cand-116** severity (gold medium): 0% → 100% of repeats right · Admin order list shows times in UTC
- **cand-124** severity (gold medium): 33% → 100% of repeats right · Autocomplete lags on older iPhones
- **cand-127** severity (gold medium): 0% → 100% of repeats right · Push shows price in USD instead of MXN
- **hand-006** severity (gold medium): 0% → 100% of repeats right · Category page takes over ten seconds to load
- **cand-127** category (gold data): 0% → 67% of repeats right · Push shows price in USD instead of MXN

## Broken (9)

- **cand-041** severity (gold medium): 100% → 33% of repeats right · Direcciones guardadas se duplican al editar
- **cand-042** severity (gold medium): 100% → 33% of repeats right · Se repiten mis direcciones
- **cand-044** severity (gold high): 67% → 33% of repeats right · Partner reports missing webhooks
- **cand-045** severity (gold high): 67% → 0% of repeats right · Webhook delivery queue empty for order events
- **cand-113** severity (gold medium): 100% → 33% of repeats right · Can't change account email
- **cand-002** component (gold checkout): 67% → 33% of repeats right · checkout broken!!!
- **cand-003** component (gold checkout): 67% → 33% of repeats right · Order confirmation returns HTTP 500
- **cand-113** category (gold functional): 67% → 33% of repeats right · Can't change account email
- **cand-138** category (gold functional): 67% → 0% of repeats right · API docs example uses an old field name
