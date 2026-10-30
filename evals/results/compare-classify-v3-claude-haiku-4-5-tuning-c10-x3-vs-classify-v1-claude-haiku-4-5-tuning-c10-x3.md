# classify-v3-claude-haiku-4-5-tuning-c10-x3 vs classify-v1-claude-haiku-4-5-tuning-c10-x3

seed-v1/tuning · 60 items · paired bootstrap over items (repeats stay together), 95% CI of candidate minus base.

**Verdict (severity macro-F1, TL-08): no significant difference.**

| metric | base | candidate | Δ [95% CI] |
|---|---|---|---|
| severity macro-F1 | 0.752 | 0.746 | **-0.006** [-0.076, +0.060] |
| severity accuracy | 0.744 | 0.739 | **-0.006** [-0.067, +0.056] |
| component accuracy | 0.917 | 0.939 | **+0.022** [+0.006, +0.044] |
| category accuracy | 0.906 | 0.917 | **+0.011** [-0.011, +0.033] |

| run-level | base | candidate |
|---|---|---|
| $ per 100 incidents | $0.071 | $0.073 |
| p95 latency ms | 5767 | 5230 |
| schema-valid first try | 100.0% | 100.0% |
| confidence ≥ 0.7 share | 100.0% | 100.0% |

## Fixed (8)

- **cand-041** severity (gold medium): 33% → 100% of repeats right · Direcciones guardadas se duplican al editar
- **cand-042** severity (gold medium): 33% → 100% of repeats right · Se repiten mis direcciones
- **cand-045** severity (gold high): 0% → 67% of repeats right · Webhook delivery queue empty for order events
- **cand-113** severity (gold medium): 33% → 100% of repeats right · Can't change account email
- **cand-002** component (gold checkout): 33% → 67% of repeats right · checkout broken!!!
- **cand-003** component (gold checkout): 33% → 67% of repeats right · Order confirmation returns HTTP 500
- **cand-069** component (gold notifications): 33% → 67% of repeats right · No llega el código de verificación por SMS
- **cand-138** category (gold functional): 33% → 67% of repeats right · API docs example uses an old field name

## Broken (5)

- **cand-014** severity (gold medium): 67% → 33% of repeats right · Notificación push duplicada
- **cand-015** severity (gold medium): 67% → 33% of repeats right · Duplicate 'order shipped' push
- **cand-085** severity (gold medium): 100% → 33% of repeats right · Buscar clientes en el admin tarda 15 segundos
- **cand-118** severity (gold medium): 67% → 33% of repeats right · Order cancellation email not sent
- **cand-124** severity (gold medium): 100% → 33% of repeats right · Autocomplete lags on older iPhones
