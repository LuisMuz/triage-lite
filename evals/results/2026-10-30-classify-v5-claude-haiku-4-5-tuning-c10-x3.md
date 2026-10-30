# classify/v5 · global.anthropic.claude-haiku-4-5-20251001-v1:0 · seed-v1/tuning

Run 2026-10-30T05:03:42+00:00 · repeat 3 · 10 incidents per call · 60 items · 19 calls (19 fresh, 0 cached chunks)

| prompt | model | split | severity macro-F1 [95% CI] | sev acc | comp acc | cat acc | conf≥0.7 acc (share) | valid first try | needs_manual | $/100 | p50 / p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| classify/v5 | global.anthropic.claude-haiku-4-5-20251001-v1:0 | tuning | **0.720** [0.627-0.795] | 72.2% | 95.6% | 89.4% | 72.2% (100.0%) | 94.4% | 0.0% | $0.070 | 3682 / 4010 |

Language detection accuracy: 100.0%.

## Severity per class

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| critical | 0.87 | 1.00 | 0.93 | 33 |
| high | 0.65 | 0.90 | 0.75 | 48 |
| medium | 0.64 | 0.30 | 0.41 | 54 |
| low | 0.75 | 0.84 | 0.79 | 45 |

## Confusion (rows = gold, columns = predicted)

| gold \ pred | critical | high | medium | low | needs_manual |
|---|---|---|---|---|---|
| critical | 33 | 0 | 0 | 0 | 0 |
| high | 3 | 43 | 2 | 0 | 0 |
| medium | 2 | 23 | 16 | 13 | 0 |
| low | 0 | 0 | 7 | 38 | 0 |

## Calibration (severity correct, by stated confidence)

| confidence | count | mean confidence | accuracy |
|---|---|---|---|
| 0.0-0.2 | 0 | n/a | n/a |
| 0.2-0.4 | 0 | n/a | n/a |
| 0.4-0.6 | 0 | n/a | n/a |
| 0.6-0.8 | 2 | 0.77 | 50.0% |
| 0.8-1.0 | 178 | 0.91 | 72.5% |

## Errors (any label wrong, or needs_manual)

- **cand-001** (es, r0) Error 500 al pagar el pedido — component checkout→payments · conf 0.95
  - Payment flow broken with HTTP 500 for all users, preventing orders; no workaround exists.
- **cand-014** (es, r0) Notificación push duplicada — severity medium→low · conf 0.85
  - Push notification sent twice per shipment event, minor user confusion but functionally correct.
- **cand-015** (en, r0) Duplicate 'order shipped' push — severity medium→low · conf 0.85
  - Duplicate push notifications sent seconds apart for order shipments on both platforms.
- **cand-028** (es, r0) Imagen de producto pixelada en iPad — severity low→medium · conf 0.85
  - Product images load as blurry thumbnails instead of full quality on iPad.
- **cand-029** (es, r0) fotos borrosas en tablet — severity low→medium · conf 0.80
  - Product images display poor quality on tablets but work fine on phones.
- **cand-035** (en, r0) Password reset email not arriving for Hotmail users — severity medium→high; component notifications→auth · conf 0.92
  - Password reset emails fail to reach Hotmail/Outlook users; auth flow broken.
- **cand-036** (en, r0) No reset email (outlook) — severity medium→high; component notifications→auth · conf 0.90
  - Password reset email not received by Outlook user; auth flow broken.
- **cand-068** (es, r0) Precio en la app distinto al de la web — severity high→medium · conf 0.80
  - App displays outdated lower price but charges web price, customer confusion and complaint.
- **cand-073** (es, r0) El carrito se vacía al cerrar sesión — category data→functional · conf 0.85
  - Cart empties on logout affecting all users, workaround is to add items again.
- **cand-083** (es, r0) Reporte de ventas no incluye pedidos con cupón — severity medium→high · conf 0.90
  - Sales report excludes coupon orders; totals mismatch with finance records.
- **cand-088** (es, r0) El cupón de primera compra se puede usar varias veces — severity medium→high · conf 0.93
  - Welcome coupon reusable multiple times instead of once per customer.
- **cand-108** (en, r0) Search shows products that can't ship to the user's region — category data→functional · conf 0.85
  - Search results contain region-restricted products that fail at checkout, breaking purchase flow for affected users.
- **cand-116** (en, r0) Admin order list shows times in UTC — severity medium→low; category data→ui · conf 0.90
  - Admin order times display in wrong timezone, causing staff confusion but data is correct.
- **cand-118** (en, r0) Order cancellation email not sent — severity medium→high · conf 0.88
  - Order cancellation emails not sent to customers, missing critical communication.
- **cand-122** (en, r0) API returns 200 with empty body for unknown product — severity medium→high · conf 0.90
  - API returns 200 for invalid request instead of 404, breaking partner error handling logic.
- **cand-127** (en, r0) Push shows price in USD instead of MXN — severity medium→low; category data→ui · conf 0.88
  - Push notification displays wrong currency label while amounts are correct, causing user confusion.
- **cand-138** (en, r0) API docs example uses an old field name — severity low→medium; category functional→ui · conf 0.85
  - API documentation example uses outdated field name; misleads developers.
- **hand-006** (en, r0) Category page takes over ten seconds to load — severity medium→high · conf 0.90
  - Category page takes 11-14 seconds to load on first visit; core search flow is slow.
- **hand-010** (en, r0) Unread notification badge does not clear immediately — category ui→functional · conf 0.85
  - Notification unread badge does not update without refresh; UI state not syncing.
- **cand-001** (es, r1) Error 500 al pagar el pedido — component checkout→payments · conf 0.95
  - Payment processing broken for all users after deploy, orders not created, error 500.
- **cand-014** (es, r1) Notificación push duplicada — severity medium→low · conf 0.85
  - Users receive duplicate push notifications for order shipment across platforms.
- **cand-015** (en, r1) Duplicate 'order shipped' push — severity medium→low · conf 0.85
  - Users receive duplicate push notifications for order shipment, several seconds apart.
- **cand-028** (es, r1) Imagen de producto pixelada en iPad — severity low→medium · conf 0.85
  - Product images load at low resolution on iPad instead of full resolution.
- **cand-029** (es, r1) fotos borrosas en tablet — severity low→medium · conf 0.80
  - Product images display with poor quality on tablet but work fine on mobile.
- **cand-035** (en, r1) Password reset email not arriving for Hotmail users — severity medium→high · conf 0.92
  - Password reset emails not delivered to Hotmail/Outlook users, blocking account recovery.
- **cand-036** (en, r1) No reset email (outlook) — severity medium→high · conf 0.88
  - Password reset email not received via Outlook after multiple attempts, blocking recovery.
- **cand-041** (es, r1) Direcciones guardadas se duplican al editar — severity medium→high · conf 0.95
  - Saved addresses duplicate on edit instead of updating, causing data multiplication.
- **cand-042** (es, r1) Se repiten mis direcciones — severity medium→high · conf 0.95
  - Duplicate addresses appear in profile after minor edit, same underlying data issue.
- **cand-044** (en, r1) Partner reports missing webhooks — severity high→critical · conf 0.95
  - Critical partner integration broken; no webhooks delivered for 2 days, forcing workaround.
- **cand-045** (en, r1) Webhook delivery queue empty for order events — severity high→critical · conf 0.95
  - Order webhooks completely failing post-deploy; no deliveries since 4.2.0.
- **cand-071** (es, r1) No acepta tarjetas American Express — severity high→critical · conf 0.95
  - All American Express cards rejected; core payment method blocked for Amex users.
- **cand-073** (es, r1) El carrito se vacía al cerrar sesión — category data→functional · conf 0.90
  - Cart clears on logout for all users; sessions not persisting cart data.
- **cand-083** (es, r1) Reporte de ventas no incluye pedidos con cupón — severity medium→high · conf 0.90
  - Sales report excludes coupon orders, causing data mismatch with finance.
- **cand-085** (es, r1) Buscar clientes en el admin tarda 15 segundos — severity medium→low · conf 0.80
  - Customer search in admin takes 15 seconds; slow response affects workflow.
- **cand-088** (es, r1) El cupón de primera compra se puede usar varias veces — severity medium→high; component checkout→payments · conf 0.95
  - First purchase coupon reusable multiple times instead of once; wrong behavior.
- **cand-108** (en, r1) Search shows products that can't ship to the user's region — severity high→medium; category data→functional · conf 0.85
  - Search results mislead users by showing unavailable products, causing checkout failure.
- **cand-113** (en, r1) Can't change account email — severity medium→high; category functional→data · conf 0.90
  - Email update fails silently, old email persists after save confirmation.
- **cand-116** (en, r1) Admin order list shows times in UTC — severity medium→low; category data→ui · conf 0.90
  - Admin sees incorrect timezone, causing confusion about order timing.
- **cand-122** (en, r1) API returns 200 with empty body for unknown product — severity medium→high · conf 0.90
  - API returns 200 instead of 404 for missing product, breaking partner error handling.
- **cand-127** (en, r1) Push shows price in USD instead of MXN — severity medium→low; category data→ui · conf 0.85
  - Push notification shows wrong currency label, confusing Mexican users.
- **cand-138** (en, r1) API docs example uses an old field name — category functional→ui · conf 0.85
  - API documentation example uses deprecated field name causing developer confusion.
- **hand-006** (en, r1) Category page takes over ten seconds to load — severity medium→high · conf 0.92
  - Category page takes 11-14 seconds on first load; significant performance degradation for users.
- **hand-010** (en, r1) Unread notification badge does not clear immediately — category ui→functional · conf 0.85
  - Notification badge does not update immediately after reading; state not synced until page refresh.
- **cand-014** (es, r2) Notificación push duplicada — severity medium→low · conf 0.85
  - Push notification sent twice for every shipment, minor user experience issue.
- **cand-015** (en, r2) Duplicate 'order shipped' push — severity medium→low · conf 0.85
  - Push notification sent twice for every shipment, minor user experience issue.
- **cand-028** (es, r2) Imagen de producto pixelada en iPad — severity low→medium · conf 0.85
  - Product images display pixelated on iPad Pro, loading thumbnails instead of full resolution.
- **cand-029** (es, r2) fotos borrosas en tablet — severity low→medium · conf 0.80
  - Product images show poor quality on Galaxy Tab but work fine on mobile.
- **cand-035** (en, r2) Password reset email not arriving for Hotmail users — severity medium→critical; component notifications→auth · conf 0.90
  - Password reset emails not delivered to Hotmail/Outlook users, breaking auth flow.
- **cand-036** (en, r2) No reset email (outlook) — severity medium→critical; component notifications→auth · conf 0.88
  - Password reset email fails for Outlook user, blocking authentication.
- **cand-041** (es, r2) Direcciones guardadas se duplican al editar — severity medium→high · conf 0.95
  - Saved addresses are duplicated instead of updated when edited, causing data proliferation.
- **cand-042** (es, r2) Se repiten mis direcciones — severity medium→high · conf 0.95
  - User profile shows same address repeated four times after minor edit, indicating data duplication.
- **cand-073** (es, r2) El carrito se vacía al cerrar sesión — category data→functional · conf 0.93
  - Cart empties on logout and login across all users, forcing items to be re-added.
- **cand-083** (es, r2) Reporte de ventas no incluye pedidos con cupón — severity medium→high · conf 0.90
  - Sales report excludes coupon orders; data discrepancy breaks financial reconciliation.
- **cand-088** (es, r2) El cupón de primera compra se puede usar varias veces — severity medium→high; component checkout→cart · conf 0.95
  - Welcome coupon usable multiple times instead of once; allows fraudulent reuse of promotion.
- **cand-108** (en, r2) Search shows products that can't ship to the user's region — category data→functional · conf 0.85
  - Search results include unavailable products, causing customer frustration at checkout but users can still purchase available items.
- **cand-113** (en, r2) Can't change account email — severity medium→high · conf 0.88
  - Email update shows success but fails silently, leaving old email unchanged and breaking authentication recovery.
- **cand-116** (en, r2) Admin order list shows times in UTC — severity medium→low; category data→ui · conf 0.80
  - Admin sees UTC times instead of local timezone, causing confusion but orders are tracked correctly.
- **cand-118** (en, r2) Order cancellation email not sent — severity medium→high · conf 0.85
  - Cancellation email fails to send, leaving customers unaware their order was cancelled.
- **cand-122** (en, r2) API returns 200 with empty body for unknown product — severity medium→high · conf 0.88
  - API returns 200 instead of 404 for missing product, breaking partner error handling and contract.
- **cand-127** (en, r2) Push shows price in USD instead of MXN — severity medium→low; category data→ui · conf 0.78
  - Push notifications show incorrect currency label, confusing customers about actual price in their region.
- **cand-138** (en, r2) API docs example uses an old field name — category functional→ui · conf 0.85
  - API documentation example contains outdated field name reference.
- **hand-010** (en, r2) Unread notification badge does not clear immediately — category ui→functional · conf 0.85
  - Notification badge does not update immediately after reading all notifications.
