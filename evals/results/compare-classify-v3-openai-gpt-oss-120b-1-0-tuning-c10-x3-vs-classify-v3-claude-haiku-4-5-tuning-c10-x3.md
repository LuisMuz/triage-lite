# classify-v3-openai-gpt-oss-120b-1-0-tuning-c10-x3 vs classify-v3-claude-haiku-4-5-tuning-c10-x3

seed-v1/tuning · 60 items · paired bootstrap over items (repeats stay together), 95% CI of candidate minus base.

**Verdict (severity macro-F1, TL-08): regression.**

| metric | base | candidate | Δ [95% CI] |
|---|---|---|---|
| severity macro-F1 | 0.746 | 0.630 | **-0.116** [-0.245, +0.011] |
| severity accuracy | 0.739 | 0.628 | **-0.111** [-0.233, +0.028] |
| component accuracy | 0.939 | 0.922 | **-0.017** [-0.067, +0.033] |
| category accuracy | 0.917 | 0.806 | **-0.111** [-0.194, -0.039] |

| run-level | base | candidate |
|---|---|---|
| $ per 100 incidents | $0.073 | $0.023 |
| p95 latency ms | 5230 | 10788 |
| schema-valid first try | 100.0% | 0.0% |
| confidence ≥ 0.7 share | 100.0% | 100.0% |

## Fixed (9)

- **cand-028** severity (gold low): 0% → 100% of repeats right · Imagen de producto pixelada en iPad
- **cand-029** severity (gold low): 0% → 100% of repeats right · fotos borrosas en tablet
- **cand-085** severity (gold medium): 33% → 100% of repeats right · Buscar clientes en el admin tarda 15 segundos
- **cand-118** severity (gold medium): 33% → 100% of repeats right · Order cancellation email not sent
- **cand-122** severity (gold medium): 0% → 100% of repeats right · API returns 200 with empty body for unknown product
- **cand-138** severity (gold low): 0% → 100% of repeats right · API docs example uses an old field name
- **hand-006** severity (gold medium): 0% → 67% of repeats right · Category page takes over ten seconds to load
- **cand-035** component (gold notifications): 0% → 67% of repeats right · Password reset email not arriving for Hotmail users
- **cand-036** component (gold notifications): 0% → 67% of repeats right · No reset email (outlook)

## Broken (24)

- **cand-006** severity (gold critical): 100% → 0% of repeats right · Cobro duplicado con tarjeta
- **cand-007** severity (gold critical): 100% → 0% of repeats right · Customers charged twice for one order
- **cand-008** severity (gold critical): 100% → 0% of repeats right · me cobraron 2 veces!!
- **cand-021** severity (gold high): 100% → 0% of repeats right · App crashes opening order history
- **cand-023** severity (gold high): 100% → 0% of repeats right · order history closes the app
- **cand-032** severity (gold high): 100% → 0% of repeats right · Búsqueda muy lenta en la app
- **cand-033** severity (gold high): 100% → 33% of repeats right · buscar tarda muchisimo
- **cand-062** severity (gold critical): 100% → 0% of repeats right · Historial de pedidos vacío después de la migración
- **cand-068** severity (gold high): 100% → 33% of repeats right · Precio en la app distinto al de la web
- **cand-077** severity (gold medium): 100% → 0% of repeats right · No se ve la tabla de tallas en móvil
- **cand-101** severity (gold critical): 100% → 0% of repeats right · User sees another customer's cart
- **cand-108** severity (gold high): 67% → 0% of repeats right · Search shows products that can't ship to the user's region
- **cand-002** component (gold checkout): 67% → 33% of repeats right · checkout broken!!!
- **cand-003** component (gold checkout): 67% → 33% of repeats right · Order confirmation returns HTTP 500
- **cand-034** component (gold search): 100% → 0% of repeats right · Latencia alta en /search desde móvil
- **cand-069** component (gold notifications): 67% → 0% of repeats right · No llega el código de verificación por SMS
- **cand-001** category (gold crash): 100% → 0% of repeats right · Error 500 al pagar el pedido
- **cand-002** category (gold crash): 100% → 0% of repeats right · checkout broken!!!
- **cand-003** category (gold crash): 100% → 0% of repeats right · Order confirmation returns HTTP 500
- **cand-006** category (gold data): 100% → 33% of repeats right · Cobro duplicado con tarjeta
- **cand-007** category (gold data): 100% → 33% of repeats right · Customers charged twice for one order
- **cand-008** category (gold data): 100% → 33% of repeats right · me cobraron 2 veces!!
- **cand-101** category (gold security): 100% → 0% of repeats right · User sees another customer's cart
- **cand-138** category (gold functional): 67% → 0% of repeats right · API docs example uses an old field name
