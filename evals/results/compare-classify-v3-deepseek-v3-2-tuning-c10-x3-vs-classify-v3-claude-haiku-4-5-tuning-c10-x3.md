# classify-v3-deepseek-v3-2-tuning-c10-x3 vs classify-v3-claude-haiku-4-5-tuning-c10-x3

seed-v1/tuning · 60 items · paired bootstrap over items (repeats stay together), 95% CI of candidate minus base.

**Verdict (severity macro-F1, TL-08): regression.**

| metric | base | candidate | Δ [95% CI] |
|---|---|---|---|
| severity macro-F1 | 0.746 | 0.635 | **-0.111** [-0.216, -0.001] |
| severity accuracy | 0.739 | 0.628 | **-0.111** [-0.222, +0.017] |
| component accuracy | 0.939 | 0.900 | **-0.039** [-0.078, -0.006] |
| category accuracy | 0.917 | 0.861 | **-0.056** [-0.117, +0.000] |

| run-level | base | candidate |
|---|---|---|
| $ per 100 incidents | $0.073 | $0.029 |
| p95 latency ms | 5230 | 31942 |
| schema-valid first try | 100.0% | 94.4% |
| confidence ≥ 0.7 share | 100.0% | 100.0% |

## Fixed (7)

- **cand-028** severity (gold low): 0% → 67% of repeats right · Imagen de producto pixelada en iPad
- **cand-029** severity (gold low): 0% → 67% of repeats right · fotos borrosas en tablet
- **cand-085** severity (gold medium): 33% → 100% of repeats right · Buscar clientes en el admin tarda 15 segundos
- **cand-118** severity (gold medium): 33% → 100% of repeats right · Order cancellation email not sent
- **cand-122** severity (gold medium): 0% → 100% of repeats right · API returns 200 with empty body for unknown product
- **cand-138** severity (gold low): 0% → 67% of repeats right · API docs example uses an old field name
- **hand-006** severity (gold medium): 0% → 100% of repeats right · Category page takes over ten seconds to load

## Broken (23)

- **cand-006** severity (gold critical): 100% → 33% of repeats right · Cobro duplicado con tarjeta
- **cand-007** severity (gold critical): 100% → 33% of repeats right · Customers charged twice for one order
- **cand-008** severity (gold critical): 100% → 33% of repeats right · me cobraron 2 veces!!
- **cand-021** severity (gold high): 100% → 33% of repeats right · App crashes opening order history
- **cand-022** severity (gold high): 100% → 33% of repeats right · Crash: IndexOutOfBoundsException in OrderAdapter
- **cand-023** severity (gold high): 100% → 33% of repeats right · order history closes the app
- **cand-032** severity (gold high): 100% → 0% of repeats right · Búsqueda muy lenta en la app
- **cand-033** severity (gold high): 100% → 0% of repeats right · buscar tarda muchisimo
- **cand-034** severity (gold high): 100% → 0% of repeats right · Latencia alta en /search desde móvil
- **cand-062** severity (gold critical): 100% → 33% of repeats right · Historial de pedidos vacío después de la migración
- **cand-069** severity (gold high): 67% → 0% of repeats right · No llega el código de verificación por SMS
- **cand-071** severity (gold high): 100% → 0% of repeats right · No acepta tarjetas American Express
- **cand-073** severity (gold high): 100% → 33% of repeats right · El carrito se vacía al cerrar sesión
- **cand-108** severity (gold high): 67% → 0% of repeats right · Search shows products that can't ship to the user's region
- **cand-002** component (gold checkout): 67% → 0% of repeats right · checkout broken!!!
- **cand-003** component (gold checkout): 67% → 0% of repeats right · Order confirmation returns HTTP 500
- **cand-069** component (gold notifications): 67% → 0% of repeats right · No llega el código de verificación por SMS
- **cand-006** category (gold data): 100% → 33% of repeats right · Cobro duplicado con tarjeta
- **cand-007** category (gold data): 100% → 33% of repeats right · Customers charged twice for one order
- **cand-008** category (gold data): 100% → 33% of repeats right · me cobraron 2 veces!!
- **cand-014** category (gold functional): 100% → 33% of repeats right · Notificación push duplicada
- **cand-015** category (gold functional): 100% → 33% of repeats right · Duplicate 'order shipped' push
- **hand-010** category (gold ui): 67% → 33% of repeats right · Unread notification badge does not clear immediately
