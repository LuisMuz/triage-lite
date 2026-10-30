# Dedupe · dedupe_judge/v3 · global.anthropic.claude-haiku-4-5-20251001-v1:0 · seed-v1/holdout

Run 2026-10-30T20:19:00+00:00 · 60 incidents · amazon.titan-embed-text-v2:0 (1024 dims) · threshold 0.3 · top-k 5 · 81 candidate pairs (0 dropped by the cap of 400) · 9 judge calls (9 fresh, 100% valid first try) · judge $0.0632 · total $0.105 per 100 incidents

## Ablation (cluster-implied pairs vs. gold groups, 95% CI)

| arm | precision | recall | predicted pairs | true pairs | gold pairs | clusters | largest |
|---|---|---|---|---|---|---|---|
| Threshold + top-k only | **26.9%** [13.3%-50.0%] | **100.0%** [100.0%-100.0%] | 78 | 21 | 21 | 14 | 7 |
| Threshold + top-k + judge | **91.3%** [73.9%-100.0%] | **100.0%** [100.0%-100.0%] | 23 | 21 | 21 | 14 | 4 |

## Judge on candidate pairs

Precision 91.3% · recall 100.0% · 81 judged · 0 unjudged

| gold kind | candidates | judged duplicate | unjudged |
|---|---|---|---|
| duplicate_same_language | 15 | 15 | 0 |
| duplicate_cross_language | 6 | 6 | 0 |
| near_miss | 1 | 0 | 0 |
| unrelated | 59 | 2 | 0 |

## Judge calibration (answer correct, by stated confidence)

| confidence | count | mean confidence | accuracy |
|---|---|---|---|
| 0.0-0.2 | 0 | n/a | n/a |
| 0.2-0.4 | 0 | n/a | n/a |
| 0.4-0.6 | 0 | n/a | n/a |
| 0.6-0.8 | 1 | 0.75 | 100.0% |
| 0.8-1.0 | 80 | 0.94 | 97.5% |

## Judge false positives (merged, but not the same bug)

- `cand-074` 'El botón Pagar queda escondido detrás del teclado' ~ `hand-008` 'El botón de iniciar sesión queda oculto con el teclado abierto' (unrelated, similarity 0.398): said True, confidence 0.85. A: Pay button hidden behind keyboard on iPhone during CVV entry. B: Login button hidden behind keyboard on small Android screen. Same defect: button obscured by keyboard, unable to scroll.
- `cand-089` 'Error 500 al subir CSV de productos con acentos' ~ `cand-126` 'Admin crashes exporting customers with emoji names' (unrelated, similarity 0.451): said True, confidence 0.85. A: CSV import error 500 with accented characters. B: export error 500 with emoji in names. Same root cause (encoding issue) but different features (import vs export). Likely same underlying bug.

## Judge false negatives (same bug, not merged)

None.

## Gold pairs never proposed by the embedding stage

None.

## Clusters with the judge

- `cand-004` "GET /v1/orders/{id} returns other customers' orders" · `cand-005` 'API devuelve pedidos de otros usuarios'
- `cand-009` 'Login con Google regresa a la pantalla inicial' · `cand-010` 'Sign in with Google loops back to login'
- `cand-011` 'Promo code shows badge but total unchanged' · `cand-012` 'El cupón no descuenta del total' · `cand-013` 'discount not applied'
- `cand-016` 'Search is accent sensitive' · `cand-018` 'buscador no sirve'
- `cand-024` 'Exportar pedidos del mes se queda colgado' · `cand-025` 'timeout al exportar en admin'
- `cand-026` 'Product page says in stock but cart says sold out' · `cand-027` 'Stock badge wrong for electronics'
- `cand-037` 'La app se cierra al pagar con Apple Pay' · `cand-038` 'Crashea con apple pay'
- `cand-039` 'Shipping address form misaligned on small screens' · `cand-040` 'Address fields overlap labels on iPhone SE'
- `cand-046` 'Link de darse de baja del newsletter da 404' · `cand-047` 'no me puedo desuscribir'
- `cand-048` 'Orders created with $0 total' · `cand-049` 'Zero-value orders in finance report' · `cand-050` 'coupon + giftcard = free stuff' · `cand-051` 'Gift card and coupon stacking zeroes the order total'
- `cand-052` 'El contador del carrito no baja al quitar productos' · `cand-054` 'Badge del carrito desactualizado' · `cand-055` 'Ícono de carrito con cantidad incorrecta'
- `cand-074` 'El botón Pagar queda escondido detrás del teclado' · `hand-008` 'El botón de iniciar sesión queda oculto con el teclado abierto'
- `cand-082` 'Los filtros de precio se pierden al regresar' · `hand-001` 'Search filters reset after opening a product'
- `cand-089` 'Error 500 al subir CSV de productos con acentos' · `cand-126` 'Admin crashes exporting customers with emoji names'
