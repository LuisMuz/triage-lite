# Dedupe · dedupe_judge/v1 · global.anthropic.claude-haiku-4-5-20251001-v1:0 · seed-v1/tuning

Run 2026-10-30T01:52:43+00:00 · 60 incidents · amazon.titan-embed-text-v2:0 (1024 dims) · threshold 0.3 · top-k 5 · 112 candidate pairs (0 dropped by the cap of 400) · 15 judge calls (0 fresh, 75% valid first try) · judge $0.1094 · total $0.182 per 100 incidents

## Ablation (cluster-implied pairs vs. gold groups, 95% CI)

| arm | precision | recall | predicted pairs | true pairs | gold pairs | clusters | largest |
|---|---|---|---|---|---|---|---|
| Threshold + top-k only | **17.9%** [13.5%-25.3%] | **83.3%** [73.3%-100.0%] | 84 | 15 | 18 | 11 | 8 |
| Threshold + top-k + judge | **94.7%** [80.0%-100.0%] | **100.0%** [100.0%-100.0%] | 19 | 18 | 18 | 11 | 3 |

## Judge on candidate pairs

Precision 85.7% · recall 100.0% · 112 judged · 0 unjudged

| gold kind | candidates | judged duplicate | unjudged |
|---|---|---|---|
| duplicate_same_language | 12 | 12 | 0 |
| duplicate_cross_language | 6 | 6 | 0 |
| near_miss | 1 | 0 | 0 |
| unrelated | 93 | 3 | 0 |

## Judge calibration (answer correct, by stated confidence)

| confidence | count | mean confidence | accuracy |
|---|---|---|---|
| 0.0-0.2 | 0 | n/a | n/a |
| 0.2-0.4 | 0 | n/a | n/a |
| 0.4-0.6 | 0 | n/a | n/a |
| 0.6-0.8 | 1 | 0.75 | 0.0% |
| 0.8-1.0 | 111 | 0.96 | 98.2% |

## Judge false positives (merged, but not the same bug)

- `cand-002` 'checkout broken!!!' ~ `cand-045` 'Webhook delivery queue empty for order events' (unrelated, similarity 0.323): said True, confidence 0.85. inc-0002 reports checkout HTTP 500 preventing order creation since 4.2.0 deploy. inc-0024 reports webhook dispatcher showing 0 deliveries for order.created since 4.2.0. The checkout failure could cause no orders to be created, explaining missing webhooks. These likely describe the same root defect.
- `cand-003` 'Order confirmation returns HTTP 500' ~ `cand-045` 'Webhook delivery queue empty for order events' (unrelated, similarity 0.350): said True, confidence 0.85. inc-0003 reports HTTP 500 on Place order with no orders created; inc-0024 reports no webhook deliveries for order.created since 4.2.0 deploy. The same root cause (order creation failing) could explain both: if orders aren't created, webhooks won't fire. This is one defect with multiple symptoms.
- `cand-079` 'Imágenes de productos tardan mucho en 3G' ~ `hand-006` 'Category page takes over ten seconds to load' (unrelated, similarity 0.385): said True, confidence 0.75. inc-0033 reports product images taking 10+ seconds on 3G in the app. inc-0058 reports category page taking 11-14 seconds initially on the web at 50 Mbps. Both describe slow product catalog loading on initial load, likely the same performance issue across platforms with different network conditions.

## Judge false negatives (same bug, not merged)

None.

## Gold pairs never proposed by the embedding stage

None.

## Clusters with the judge

- `cand-001` 'Error 500 al pagar el pedido' · `cand-002` 'checkout broken!!!' · `cand-003` 'Order confirmation returns HTTP 500'
- `cand-006` 'Cobro duplicado con tarjeta' · `cand-007` 'Customers charged twice for one order' · `cand-008` 'me cobraron 2 veces!!'
- `cand-014` 'Notificación push duplicada' · `cand-015` "Duplicate 'order shipped' push"
- `cand-019` 'Botón Guardar aparece en inglés' · `cand-020` "Untranslated 'Save' button on Spanish profile page"
- `cand-021` 'App crashes opening order history' · `cand-022` 'Crash: IndexOutOfBoundsException in OrderAdapter' · `cand-023` 'order history closes the app'
- `cand-028` 'Imagen de producto pixelada en iPad' · `cand-029` 'fotos borrosas en tablet'
- `cand-032` 'Búsqueda muy lenta en la app' · `cand-033` 'buscar tarda muchisimo' · `cand-034` 'Latencia alta en /search desde móvil'
- `cand-035` 'Password reset email not arriving for Hotmail users' · `cand-036` 'No reset email (outlook)'
- `cand-041` 'Direcciones guardadas se duplican al editar' · `cand-042` 'Se repiten mis direcciones'
- `cand-044` 'Partner reports missing webhooks' · `cand-045` 'Webhook delivery queue empty for order events'
- `cand-079` 'Imágenes de productos tardan mucho en 3G' · `hand-006` 'Category page takes over ten seconds to load'
