# classify-v3-moonshotai-kimi-k2-5-tuning-c10-x3 vs classify-v3-claude-haiku-4-5-tuning-c10-x3

seed-v1/tuning · 60 items · paired bootstrap over items (repeats stay together), 95% CI of candidate minus base.

**Verdict (severity macro-F1, TL-08): no significant difference.**

| metric | base | candidate | Δ [95% CI] |
|---|---|---|---|
| severity macro-F1 | 0.746 | 0.748 | **+0.002** [-0.102, +0.103] |
| severity accuracy | 0.739 | 0.744 | **+0.006** [-0.094, +0.122] |
| component accuracy | 0.939 | 0.956 | **+0.017** [-0.028, +0.072] |
| category accuracy | 0.917 | 0.861 | **-0.056** [-0.106, -0.011] |

| run-level | base | candidate |
|---|---|---|
| $ per 100 incidents | $0.073 | $0.032 |
| p95 latency ms | 5230 | 10085 |
| schema-valid first try | 100.0% | 100.0% |
| confidence ≥ 0.7 share | 100.0% | 100.0% |

## Fixed (13)

- **cand-014** severity (gold medium): 33% → 67% of repeats right · Notificación push duplicada
- **cand-015** severity (gold medium): 33% → 67% of repeats right · Duplicate 'order shipped' push
- **cand-028** severity (gold low): 0% → 67% of repeats right · Imagen de producto pixelada en iPad
- **cand-029** severity (gold low): 0% → 67% of repeats right · fotos borrosas en tablet
- **cand-035** severity (gold medium): 0% → 67% of repeats right · Password reset email not arriving for Hotmail users
- **cand-036** severity (gold medium): 0% → 67% of repeats right · No reset email (outlook)
- **cand-085** severity (gold medium): 33% → 100% of repeats right · Buscar clientes en el admin tarda 15 segundos
- **cand-118** severity (gold medium): 33% → 100% of repeats right · Order cancellation email not sent
- **cand-122** severity (gold medium): 0% → 100% of repeats right · API returns 200 with empty body for unknown product
- **cand-124** severity (gold medium): 33% → 100% of repeats right · Autocomplete lags on older iPhones
- **cand-138** severity (gold low): 0% → 67% of repeats right · API docs example uses an old field name
- **cand-035** component (gold notifications): 0% → 100% of repeats right · Password reset email not arriving for Hotmail users
- **cand-036** component (gold notifications): 0% → 100% of repeats right · No reset email (outlook)

## Broken (12)

- **cand-006** severity (gold critical): 100% → 0% of repeats right · Cobro duplicado con tarjeta
- **cand-007** severity (gold critical): 100% → 0% of repeats right · Customers charged twice for one order
- **cand-008** severity (gold critical): 100% → 0% of repeats right · me cobraron 2 veces!!
- **cand-068** severity (gold high): 100% → 33% of repeats right · Precio en la app distinto al de la web
- **cand-077** severity (gold medium): 100% → 33% of repeats right · No se ve la tabla de tallas en móvil
- **hand-007** severity (gold high): 100% → 33% of repeats right · Expired saved card is accepted until final payment
- **cand-002** component (gold checkout): 67% → 33% of repeats right · checkout broken!!!
- **cand-003** component (gold checkout): 67% → 33% of repeats right · Order confirmation returns HTTP 500
- **cand-006** category (gold data): 100% → 33% of repeats right · Cobro duplicado con tarjeta
- **cand-007** category (gold data): 100% → 0% of repeats right · Customers charged twice for one order
- **cand-008** category (gold data): 100% → 33% of repeats right · me cobraron 2 veces!!
- **cand-138** category (gold functional): 67% → 0% of repeats right · API docs example uses an old field name
