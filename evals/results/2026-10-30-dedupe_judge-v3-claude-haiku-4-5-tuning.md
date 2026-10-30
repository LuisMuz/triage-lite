# Dedupe · dedupe_judge/v3 · global.anthropic.claude-haiku-4-5-20251001-v1:0 · seed-v1/tuning

Run 2026-10-30T05:07:09+00:00 · 60 incidents · amazon.titan-embed-text-v2:0 (1024 dims) · threshold 0.3 · top-k 5 · 112 candidate pairs (0 dropped by the cap of 400) · 12 judge calls (12 fresh, 100% valid first try) · judge $0.0847 · total $0.141 per 100 incidents

## Ablation (cluster-implied pairs vs. gold groups, 95% CI)

| arm | precision | recall | predicted pairs | true pairs | gold pairs | clusters | largest |
|---|---|---|---|---|---|---|---|
| Threshold + top-k only | **17.9%** [13.5%-25.3%] | **83.3%** [73.3%-100.0%] | 84 | 15 | 18 | 11 | 8 |
| Threshold + top-k + judge | **90.0%** [71.4%-100.0%] | **100.0%** [100.0%-100.0%] | 20 | 18 | 18 | 12 | 3 |

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
| 0.6-0.8 | 2 | 0.75 | 0.0% |
| 0.8-1.0 | 110 | 0.95 | 99.1% |

## Judge false positives (merged, but not the same bug)

- `cand-003` 'Order confirmation returns HTTP 500' ~ `cand-045` 'Webhook delivery queue empty for order events' (unrelated, similarity 0.350): said True, confidence 0.92. A: Order creation fails with HTTP 500 at checkout in 4.2.0. B: Webhook dispatcher shows 0 deliveries for order.created since 4.2.0. Same root cause: broken order creation.
- `cand-079` 'Imágenes de productos tardan mucho en 3G' ~ `hand-006` 'Category page takes over ten seconds to load' (unrelated, similarity 0.385): said True, confidence 0.75. A: product images slow on 3G. B: category page takes 11-14s on 50Mbps. Same defect: initial page/category load slow, different connection types.
- `cand-096` "Texto 'Direccion de envio' sin acentos" ~ `cand-136` "Typo 'Adress' in shipping form" (unrelated, similarity 0.362): said True, confidence 0.75. A: missing accents 'Dirección de envío'. B: typo 'Adress' in shipping form. Both text/spelling issues in checkout shipping, likely same defect.

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
- `cand-096` "Texto 'Direccion de envio' sin acentos" · `cand-136` "Typo 'Adress' in shipping form"
