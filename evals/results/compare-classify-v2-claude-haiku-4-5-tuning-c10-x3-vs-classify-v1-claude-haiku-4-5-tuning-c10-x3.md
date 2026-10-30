# classify-v2-claude-haiku-4-5-tuning-c10-x3 vs classify-v1-claude-haiku-4-5-tuning-c10-x3

seed-v1/tuning · 60 items · paired bootstrap over items (repeats stay together), 95% CI of candidate minus base.

**Verdict (severity macro-F1, TL-08): no significant difference.**

| metric | base | candidate | Δ [95% CI] |
|---|---|---|---|
| severity macro-F1 | 0.752 | 0.752 | **-0.001** [-0.078, +0.072] |
| severity accuracy | 0.744 | 0.739 | **-0.006** [-0.083, +0.067] |
| component accuracy | 0.917 | 0.928 | **+0.011** [-0.017, +0.044] |
| category accuracy | 0.906 | 0.917 | **+0.011** [-0.022, +0.056] |

| run-level | base | candidate |
|---|---|---|
| $ per 100 incidents | $0.071 | $0.076 |
| p95 latency ms | 5767 | 5702 |
| schema-valid first try | 100.0% | 100.0% |
| confidence ≥ 0.7 share | 100.0% | 100.0% |

## Fixed (9)

- **cand-028** severity (gold low): 0% → 67% of repeats right · Imagen de producto pixelada en iPad
- **cand-029** severity (gold low): 0% → 67% of repeats right · fotos borrosas en tablet
- **cand-041** severity (gold medium): 33% → 100% of repeats right · Direcciones guardadas se duplican al editar
- **cand-042** severity (gold medium): 33% → 100% of repeats right · Se repiten mis direcciones
- **cand-045** severity (gold high): 0% → 67% of repeats right · Webhook delivery queue empty for order events
- **cand-113** severity (gold medium): 33% → 100% of repeats right · Can't change account email
- **cand-002** component (gold checkout): 33% → 100% of repeats right · checkout broken!!!
- **cand-003** component (gold checkout): 33% → 67% of repeats right · Order confirmation returns HTTP 500
- **cand-108** category (gold data): 0% → 100% of repeats right · Search shows products that can't ship to the user's region

## Broken (5)

- **cand-014** severity (gold medium): 67% → 0% of repeats right · Notificación push duplicada
- **cand-015** severity (gold medium): 67% → 0% of repeats right · Duplicate 'order shipped' push
- **cand-069** severity (gold high): 100% → 33% of repeats right · No llega el código de verificación por SMS
- **cand-077** severity (gold medium): 67% → 33% of repeats right · No se ve la tabla de tallas en móvil
- **cand-108** severity (gold high): 100% → 33% of repeats right · Search shows products that can't ship to the user's region
