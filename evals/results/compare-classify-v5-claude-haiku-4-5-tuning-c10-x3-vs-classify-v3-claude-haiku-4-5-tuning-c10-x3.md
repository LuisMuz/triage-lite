# classify-v5-claude-haiku-4-5-tuning-c10-x3 vs classify-v3-claude-haiku-4-5-tuning-c10-x3

seed-v1/tuning · 60 items · paired bootstrap over items (repeats stay together), 95% CI of candidate minus base.

**Verdict (severity macro-F1, TL-08): no significant difference.**

| metric | base | candidate | Δ [95% CI] |
|---|---|---|---|
| severity macro-F1 | 0.746 | 0.720 | **-0.026** [-0.088, +0.035] |
| severity accuracy | 0.739 | 0.722 | **-0.017** [-0.078, +0.039] |
| component accuracy | 0.939 | 0.956 | **+0.017** [-0.017, +0.050] |
| category accuracy | 0.917 | 0.894 | **-0.022** [-0.056, +0.000] |

| run-level | base | candidate |
|---|---|---|
| $ per 100 incidents | $0.073 | $0.070 |
| p95 latency ms | 5230 | 4010 |
| schema-valid first try | 100.0% | 94.4% |
| confidence ≥ 0.7 share | 100.0% | 100.0% |

## Fixed (3)

- **cand-085** severity (gold medium): 33% → 67% of repeats right · Buscar clientes en el admin tarda 15 segundos
- **cand-124** severity (gold medium): 33% → 100% of repeats right · Autocomplete lags on older iPhones
- **cand-138** severity (gold low): 0% → 67% of repeats right · API docs example uses an old field name

## Broken (6)

- **cand-041** severity (gold medium): 100% → 33% of repeats right · Direcciones guardadas se duplican al editar
- **cand-042** severity (gold medium): 100% → 33% of repeats right · Se repiten mis direcciones
- **cand-113** severity (gold medium): 100% → 33% of repeats right · Can't change account email
- **cand-088** component (gold checkout): 100% → 33% of repeats right · El cupón de primera compra se puede usar varias veces
- **cand-138** category (gold functional): 67% → 0% of repeats right · API docs example uses an old field name
- **hand-010** category (gold ui): 67% → 0% of repeats right · Unread notification badge does not clear immediately
