# classify-v3-amazon-nova-lite-v1-0-tuning-c10-x3 vs classify-v3-claude-haiku-4-5-tuning-c10-x3

seed-v1/tuning · 60 items · paired bootstrap over items (repeats stay together), 95% CI of candidate minus base.

**Verdict (severity macro-F1, TL-08): regression.**

| metric | base | candidate | Δ [95% CI] |
|---|---|---|---|
| severity macro-F1 | 0.746 | 0.598 | **-0.148** [-0.244, -0.050] |
| severity accuracy | 0.739 | 0.589 | **-0.150** [-0.250, -0.050] |
| component accuracy | 0.939 | 0.922 | **-0.017** [-0.044, +0.000] |
| category accuracy | 0.917 | 0.817 | **-0.100** [-0.200, -0.011] |

| run-level | base | candidate |
|---|---|---|
| $ per 100 incidents | $0.073 | $0.003 |
| p95 latency ms | 5230 | 6991 |
| schema-valid first try | 100.0% | 100.0% |
| confidence ≥ 0.7 share | 100.0% | 100.0% |

## Fixed (7)

- **cand-085** severity (gold medium): 33% → 100% of repeats right · Buscar clientes en el admin tarda 15 segundos
- **cand-118** severity (gold medium): 33% → 67% of repeats right · Order cancellation email not sent
- **cand-122** severity (gold medium): 0% → 100% of repeats right · API returns 200 with empty body for unknown product
- **cand-127** severity (gold medium): 0% → 67% of repeats right · Push shows price in USD instead of MXN
- **cand-108** category (gold data): 0% → 67% of repeats right · Search shows products that can't ship to the user's region
- **cand-116** category (gold data): 0% → 67% of repeats right · Admin order list shows times in UTC
- **cand-127** category (gold data): 0% → 100% of repeats right · Push shows price in USD instead of MXN

## Broken (25)

- **cand-021** severity (gold high): 100% → 0% of repeats right · App crashes opening order history
- **cand-022** severity (gold high): 100% → 0% of repeats right · Crash: IndexOutOfBoundsException in OrderAdapter
- **cand-023** severity (gold high): 100% → 0% of repeats right · order history closes the app
- **cand-041** severity (gold medium): 100% → 33% of repeats right · Direcciones guardadas se duplican al editar
- **cand-042** severity (gold medium): 100% → 33% of repeats right · Se repiten mis direcciones
- **cand-044** severity (gold high): 67% → 33% of repeats right · Partner reports missing webhooks
- **cand-045** severity (gold high): 67% → 33% of repeats right · Webhook delivery queue empty for order events
- **cand-075** severity (gold high): 100% → 33% of repeats right · No se pueden marcar pedidos como enviados
- **cand-092** severity (gold low): 100% → 33% of repeats right · Mensaje de error del login en inglés
- **cand-098** severity (gold low): 100% → 0% of repeats right · Montos alineados a la izquierda en tablas del admin
- **cand-101** severity (gold critical): 100% → 33% of repeats right · User sees another customer's cart
- **cand-108** severity (gold high): 67% → 33% of repeats right · Search shows products that can't ship to the user's region
- **cand-110** severity (gold high): 100% → 33% of repeats right · iOS app crashes on payment step with saved card
- **cand-069** component (gold notifications): 67% → 0% of repeats right · No llega el código de verificación por SMS
- **cand-001** category (gold crash): 100% → 33% of repeats right · Error 500 al pagar el pedido
- **cand-002** category (gold crash): 100% → 33% of repeats right · checkout broken!!!
- **cand-003** category (gold crash): 100% → 33% of repeats right · Order confirmation returns HTTP 500
- **cand-014** category (gold functional): 100% → 0% of repeats right · Notificación push duplicada
- **cand-015** category (gold functional): 100% → 0% of repeats right · Duplicate 'order shipped' push
- **cand-041** category (gold data): 100% → 0% of repeats right · Direcciones guardadas se duplican al editar
- **cand-042** category (gold data): 100% → 33% of repeats right · Se repiten mis direcciones
- **cand-101** category (gold security): 100% → 33% of repeats right · User sees another customer's cart
- **cand-122** category (gold functional): 100% → 0% of repeats right · API returns 200 with empty body for unknown product
- **cand-136** category (gold ui): 100% → 33% of repeats right · Typo 'Adress' in shipping form
- **cand-138** category (gold functional): 67% → 33% of repeats right · API docs example uses an old field name
