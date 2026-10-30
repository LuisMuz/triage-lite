# classify/v3 · openai.gpt-oss-120b-1:0 · seed-v1/tuning

Run 2026-10-30T19:12:27+00:00 · repeat 1 · 10 incidents per call · 60 items · 12 calls (12 fresh, 0 cached chunks)

| prompt | model | split | severity macro-F1 [95% CI] | sev acc | comp acc | cat acc | conf≥0.7 acc (share) | valid first try | needs_manual | $/100 | p50 / p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| classify/v3 | openai.gpt-oss-120b-1:0 | tuning | **0.647** [0.509-0.767] | 65.0% | 96.7% | 81.7% | 65.0% (100.0%) | 0.0% | 0.0% | $0.023 | 8032 / 12803 |

Language detection accuracy: 100.0%.

## Severity per class

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| critical | 1.00 | 0.55 | 0.71 | 11 |
| high | 0.58 | 0.69 | 0.63 | 16 |
| medium | 0.64 | 0.39 | 0.48 | 18 |
| low | 0.62 | 1.00 | 0.77 | 15 |

## Confusion (rows = gold, columns = predicted)

| gold \ pred | critical | high | medium | low | needs_manual |
|---|---|---|---|---|---|
| critical | 6 | 5 | 0 | 0 | 0 |
| high | 0 | 11 | 4 | 1 | 0 |
| medium | 0 | 3 | 7 | 8 | 0 |
| low | 0 | 0 | 0 | 15 | 0 |

## Calibration (severity correct, by stated confidence)

| confidence | count | mean confidence | accuracy |
|---|---|---|---|
| 0.0-0.2 | 0 | n/a | n/a |
| 0.2-0.4 | 0 | n/a | n/a |
| 0.4-0.6 | 0 | n/a | n/a |
| 0.6-0.8 | 0 | n/a | n/a |
| 0.8-1.0 | 60 | 0.93 | 65.0% |

## Errors (any label wrong, or needs_manual)

- **cand-001** (es, r0) Error 500 al pagar el pedido — category crash→functional · conf 0.97
  - All attempts to place an order fail with HTTP 500, blocking the core checkout flow for every user with no workaround.
- **cand-002** (en, r0) checkout broken!!! — category crash→functional · conf 0.96
  - Every order placement returns a server error, stopping the core checkout process for all users and no workaround exists.
- **cand-003** (en, r0) Order confirmation returns HTTP 500 — category crash→functional · conf 0.97
  - Placing an order consistently results in HTTP 500 across all platforms, fully breaking the checkout flow with no alternative path.
- **cand-006** (es, r0) Cobro duplicado con tarjeta — severity critical→high; category data→functional · conf 0.94
  - Customers are being charged twice for the same order, causing financial loss; refunds are possible but the payment flow is incorrect.
- **cand-007** (en, r0) Customers charged twice for one order — severity critical→high; category data→functional · conf 0.94
  - Multiple tickets report double charges for a single order due to duplicated capture calls, impacting core payment functionality.
- **cand-008** (es, r0) me cobraron 2 veces!! — severity critical→high; category data→functional · conf 0.93
  - User sees two identical bank charges for one purchase, indicating a duplicate payment processing error.
- **cand-014** (es, r0) Notificación push duplicada — severity medium→low · conf 0.96
  - Each order triggers two identical push notifications, which is a nuisance but does not prevent any primary user action.
- **cand-015** (en, r0) Duplicate 'order shipped' push — severity medium→low · conf 0.96
  - Users receive duplicate 'order shipped' push alerts; the issue is minor and only affects notification experience.
- **cand-021** (en, r0) App crashes opening order history — severity high→medium · conf 0.90
  - The app crashes when opening the order history screen for users with many orders, affecting a subset of users.
- **cand-023** (en, r0) order history closes the app — severity high→medium · conf 0.85
  - Opening the order list crashes the app for users with many orders, similar to other order‑history crashes.
- **cand-032** (es, r0) Búsqueda muy lenta en la app — severity high→medium · conf 0.90
  - Search results take 6–8 seconds on the app over 4G, much slower than the web version.
- **cand-034** (es, r0) Latencia alta en /search desde móvil — component search→api · conf 0.90
  - The mobile /search endpoint has a p95 latency of 7.8 s versus 300 ms on web, degrading the core search flow.
- **cand-035** (en, r0) Password reset email not arriving for Hotmail users — severity medium→high · conf 0.90
  - Password‑reset emails are not delivered to Hotmail/Outlook users, blocking a critical login flow.
- **cand-036** (en, r0) No reset email (outlook) — severity medium→high · conf 0.90
  - Outlook users do not receive password‑reset emails despite multiple attempts, preventing account recovery.
- **cand-041** (es, r0) Direcciones guardadas se duplican al editar — severity medium→low · conf 0.94
  - Editing a saved address creates duplicate entries, causing minor annoyance but does not block any core flow.
- **cand-042** (es, r0) Se repiten mis direcciones — severity medium→low · conf 0.94
  - Duplicate addresses appear in the Android app, similar to inc-0021, affecting usability only.
- **cand-062** (es, r0) Historial de pedidos vacío después de la migración — severity critical→high · conf 0.95
  - Order history is empty for thousands of users after migration, losing access to past orders; core user history feature is broken.
- **cand-068** (es, r0) Precio en la app distinto al de la web — severity high→low · conf 0.93
  - App shows stale lower prices, but users are charged the correct web price, causing confusion but not financial error.
- **cand-069** (es, r0) No llega el código de verificación por SMS — component notifications→auth · conf 0.95
  - Two‑factor SMS codes are not delivered, blocking login for users relying on SMS, though email fallback exists.
- **cand-073** (es, r0) El carrito se vacía al cerrar sesión — category data→functional · conf 0.97
  - Cart contents disappear after logout for all users, breaking the shopping flow and requiring re‑adding items.
- **cand-077** (es, r0) No se ve la tabla de tallas en móvil — severity medium→low · conf 0.95
  - Size table missing only on mobile devices, a cosmetic UI issue that does not prevent purchase.
- **cand-088** (es, r0) El cupón de primera compra se puede usar varias veces — severity medium→high · conf 0.90
  - Welcome coupon can be reused, leading to revenue loss in the checkout flow; no proper restriction exists.
- **cand-101** (en, r0) User sees another customer's cart — severity critical→high; category security→functional · conf 0.94
  - Users on the same network see each other's cart items and addresses, breaking the core cart flow.
- **cand-108** (en, r0) Search shows products that can't ship to the user's region — severity high→medium · conf 0.90
  - Search returns products unavailable in the user’s region, causing checkout failures for affected users.
- **cand-116** (en, r0) Admin order list shows times in UTC — severity medium→low; category data→ui · conf 0.95
  - Order times are displayed in UTC instead of local time, a visual inconvenience for staff.
- **cand-124** (en, r0) Autocomplete lags on older iPhones — severity medium→low · conf 0.88
  - Autocomplete in the search box lags on older iPhone models, slowing the UI but still functional.
- **cand-127** (en, r0) Push shows price in USD instead of MXN — severity medium→low; category data→ui · conf 0.90
  - Push notifications show prices with a USD label for Mexican users, causing minor confusion.
- **cand-138** (en, r0) API docs example uses an old field name — category functional→ui · conf 0.90
  - Docs showing an outdated field name can mislead developers but does not break the live system.
