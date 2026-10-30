# classify-v4-claude-haiku-4-5-tuning-c10-x3 vs classify-v3-claude-haiku-4-5-tuning-c10-x3

seed-v1/tuning · 60 items · paired bootstrap over items (repeats stay together), 95% CI of candidate minus base.

**Verdict (severity macro-F1, TL-08): no significant difference.**

| metric | base | candidate | Δ [95% CI] |
|---|---|---|---|
| severity macro-F1 | 0.746 | 0.752 | **+0.005** [-0.067, +0.081] |
| severity accuracy | 0.739 | 0.750 | **+0.011** [-0.056, +0.083] |
| component accuracy | 0.939 | 0.906 | **-0.033** [-0.072, -0.006] |
| category accuracy | 0.917 | 0.894 | **-0.022** [-0.061, +0.011] |

| run-level | base | candidate |
|---|---|---|
| $ per 100 incidents | $0.073 | $0.075 |
| p95 latency ms | 5230 | 5349 |
| schema-valid first try | 100.0% | 100.0% |
| confidence ≥ 0.7 share | 100.0% | 99.4% |

## Fixed (5)

- **cand-118** severity (gold medium): 33% → 67% of repeats right · Order cancellation email not sent
- **cand-124** severity (gold medium): 33% → 67% of repeats right · Autocomplete lags on older iPhones
- **cand-127** severity (gold medium): 0% → 67% of repeats right · Push shows price in USD instead of MXN
- **cand-138** severity (gold low): 0% → 67% of repeats right · API docs example uses an old field name
- **hand-006** severity (gold medium): 0% → 67% of repeats right · Category page takes over ten seconds to load

## Broken (7)

- **cand-041** severity (gold medium): 100% → 33% of repeats right · Direcciones guardadas se duplican al editar
- **cand-042** severity (gold medium): 100% → 33% of repeats right · Se repiten mis direcciones
- **cand-002** component (gold checkout): 67% → 0% of repeats right · checkout broken!!!
- **cand-003** component (gold checkout): 67% → 0% of repeats right · Order confirmation returns HTTP 500
- **cand-069** component (gold notifications): 67% → 33% of repeats right · No llega el código de verificación por SMS
- **cand-138** category (gold functional): 67% → 0% of repeats right · API docs example uses an old field name
- **hand-010** category (gold ui): 67% → 33% of repeats right · Unread notification badge does not clear immediately
