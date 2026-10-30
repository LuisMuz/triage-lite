# classify/v3 · global.anthropic.claude-haiku-4-5-20251001-v1:0 · seed-v1/tuning

Run 2026-10-30T04:58:26+00:00 · repeat 3 · 10 incidents per call · 60 items · 18 calls (18 fresh, 0 cached chunks)

| prompt | model | split | severity macro-F1 [95% CI] | sev acc | comp acc | cat acc | conf≥0.7 acc (share) | valid first try | needs_manual | $/100 | p50 / p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| classify/v3 | global.anthropic.claude-haiku-4-5-20251001-v1:0 | tuning | **0.746** [0.651-0.828] | 73.9% | 93.9% | 91.7% | 73.9% (100.0%) | 100.0% | 0.0% | $0.073 | 4614 / 5230 |

Language detection accuracy: 100.0%.

## Severity per class

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| critical | 0.94 | 1.00 | 0.97 | 33 |
| high | 0.69 | 0.92 | 0.79 | 48 |
| medium | 0.65 | 0.37 | 0.47 | 54 |
| low | 0.72 | 0.80 | 0.76 | 45 |

## Confusion (rows = gold, columns = predicted)

| gold \ pred | critical | high | medium | low | needs_manual |
|---|---|---|---|---|---|
| critical | 33 | 0 | 0 | 0 | 0 |
| high | 2 | 44 | 2 | 0 | 0 |
| medium | 0 | 20 | 20 | 14 | 0 |
| low | 0 | 0 | 9 | 36 | 0 |

## Calibration (severity correct, by stated confidence)

| confidence | count | mean confidence | accuracy |
|---|---|---|---|
| 0.0-0.2 | 0 | n/a | n/a |
| 0.2-0.4 | 0 | n/a | n/a |
| 0.4-0.6 | 0 | n/a | n/a |
| 0.6-0.8 | 2 | 0.75 | 0.0% |
| 0.8-1.0 | 178 | 0.90 | 74.7% |

## Errors (any label wrong, or needs_manual)

- **cand-014** (es, r0) Notificación push duplicada — severity medium→low · conf 0.85
  - Push notification is sent twice for every shipment update. Non-critical feature malfunction that does not block user flows.
- **cand-015** (en, r0) Duplicate 'order shipped' push — severity medium→low · conf 0.85
  - Users receive duplicate shipment notification a few seconds apart across both platforms. Non-critical annoyance that does not impact core functionality.
- **cand-028** (es, r0) Imagen de producto pixelada en iPad — severity low→medium · conf 0.85
  - Product images appear pixelated on iPad, displaying low-resolution thumbnails instead of full-quality images, a UI/display issue.
- **cand-029** (es, r0) fotos borrosas en tablet — severity low→medium · conf 0.80
  - Product images display at poor quality on tablets but render properly on phones, indicating a responsive display or resolution handling issue.
- **cand-035** (en, r0) Password reset email not arriving for Hotmail users — severity medium→high; component notifications→auth · conf 0.92
  - Password reset emails fail to arrive for Hotmail and Outlook users, blocking authentication for a subset of users with a workaround of contacting support.
- **cand-036** (en, r0) No reset email (outlook) — severity medium→high; component notifications→auth · conf 0.90
  - Password reset email not received by an Outlook user despite multiple attempts, preventing password recovery for core authentication flow.
- **cand-044** (en, r0) Partner reports missing webhooks — severity high→critical · conf 0.90
  - Partner reports no new-order webhooks received for 2 days, breaking their integration. This is a critical API functionality failure affecting partner systems.
- **cand-045** (en, r0) Webhook delivery queue empty for order events — severity high→critical · conf 0.95
  - Webhook dispatcher shows zero order.created deliveries since deploy 4.2.0, while other event types work. This confirms a functional defect in the API webhook system.
- **cand-073** (es, r0) El carrito se vacía al cerrar sesión — category data→functional · conf 0.90
  - Cart contents are lost when users logout and login, affecting all users and requiring re-adding items. This is a functional defect in cart persistence that impacts the core shopping flow.
- **cand-083** (es, r0) Reporte de ventas no incluye pedidos con cupón — severity medium→high · conf 0.90
  - The sales report excludes orders using coupons, causing incorrect totals that don't match finance records. This is a data integrity issue in critical reporting.
- **cand-085** (es, r0) Buscar clientes en el admin tarda 15 segundos — severity medium→low · conf 0.80
  - Customer search in admin takes 15 seconds, which is slow but the function works. This is a performance issue in a non-critical admin feature.
- **cand-088** (es, r0) El cupón de primera compra se puede usar varias veces — severity medium→high · conf 0.90
  - A first-purchase-only coupon can be reused multiple times, breaking the intended business logic. This is a functional defect that causes revenue loss.
- **cand-108** (en, r0) Search shows products that can't ship to the user's region — category data→functional · conf 0.85
  - Search returns unavailable products causing checkout failures for affected users; the search logic does not filter by regional availability as it should.
- **cand-116** (en, r0) Admin order list shows times in UTC — severity medium→low; category data→ui · conf 0.80
  - Admin staff see order times in UTC instead of their local time zone, causing confusion but not blocking order management functionality.
- **cand-118** (en, r0) Order cancellation email not sent — severity medium→high · conf 0.85
  - Cancellation emails fail to send when support cancels orders, leaving customers uninformed of order status changes.
- **cand-122** (en, r0) API returns 200 with empty body for unknown product — severity medium→high · conf 0.90
  - The API returns a 200 success status with an empty body for non-existent products instead of the proper 404 error, breaking partner error handling logic.
- **cand-127** (en, r0) Push shows price in USD instead of MXN — severity medium→low; category data→ui · conf 0.85
  - Push notifications display incorrect currency labels (USD instead of MXN) for Mexican users, confusing prices though the amounts are correct.
- **cand-138** (en, r0) API docs example uses an old field name — severity low→medium · conf 0.85
  - API documentation example uses an outdated field name ('qty') that doesn't match the current API specification ('quantity'). This is a functional issue where the documentation is incorrect.
- **hand-006** (en, r0) Category page takes over ten seconds to load — severity medium→high · conf 0.85
  - Category pages with many products take 11-14 seconds to load on first visit, which is excessive. This is a performance issue affecting the core catalog browsing flow.
- **hand-010** (en, r0) Unread notification badge does not clear immediately — category ui→functional · conf 0.80
  - The unread notification badge count does not update immediately after reading notifications, requiring a page refresh to clear. This is a functional issue with the notification status display.
- **cand-001** (es, r1) Error 500 al pagar el pedido — component checkout→payments · conf 0.95
  - Error 500 on payment submission across all platforms and user accounts prevents any orders from being created. This is a complete outage of the payment/checkout flow with no workaround.
- **cand-014** (es, r1) Notificación push duplicada — severity medium→low · conf 0.85
  - Users receive 'order shipped' push notification twice. This is a non-critical notification delivery duplication that doesn't block any functionality.
- **cand-015** (en, r1) Duplicate 'order shipped' push — severity medium→low · conf 0.85
  - Users receive 'order shipped' push notification twice. This is a non-critical notification delivery duplication that doesn't block any functionality.
- **cand-028** (es, r1) Imagen de producto pixelada en iPad — severity low→medium · conf 0.88
  - Product images appear pixelated/blurry on iPad Pro, with thumbnail being loaded instead of full-resolution image. This is a UI/display issue with images on tablet devices.
- **cand-029** (es, r1) fotos borrosas en tablet — severity low→medium · conf 0.85
  - Product images show poor quality on Galaxy Tab but display correctly on phones, indicating a responsive design or image scaling issue specific to tablets.
- **cand-035** (en, r1) Password reset email not arriving for Hotmail users — severity medium→high; component notifications→auth · conf 0.88
  - Password reset emails fail to arrive for Hotmail/Outlook users while Gmail works, blocking authentication for a subset of users. A workaround (web may work or using different email) likely exists.
- **cand-036** (en, r1) No reset email (outlook) — severity medium→high; component notifications→auth · conf 0.85
  - Password reset email not received by Outlook user after multiple attempts, indicating a blocking issue with the password reset flow for certain email providers.
- **cand-073** (es, r1) El carrito se vacía al cerrar sesión — category data→functional · conf 0.90
  - Cart contents are lost when users log out and back in, affecting all users. This is a functional issue where cart state is not persisted correctly.
- **cand-083** (es, r1) Reporte de ventas no incluye pedidos con cupón — severity medium→high · conf 0.90
  - The monthly sales report excludes orders with coupons, causing financial totals to be incorrect. This is a data accuracy issue in admin reporting.
- **cand-088** (es, r1) El cupón de primera compra se puede usar varias veces — severity medium→high · conf 0.85
  - The BIENVENIDA first-purchase coupon can be used multiple times when it should only be valid once. This is a functional bug that breaks coupon logic and affects revenue.
- **cand-108** (en, r1) Search shows products that can't ship to the user's region — category data→functional · conf 0.90
  - Search returns products unavailable to users in their region, causing checkout failures and a broken shopping flow for affected users.
- **cand-113** (en, r1) Can't change account email — category functional→data · conf 0.88
  - Email change appears successful but does not persist, leaving the account in an inconsistent state with the wrong contact email.
- **cand-116** (en, r1) Admin order list shows times in UTC — severity medium→low; category data→ui · conf 0.85
  - Admin displays order times in UTC instead of the local timezone, causing confusion but not blocking any functionality; staff can work around by mental conversion.
- **cand-122** (en, r1) API returns 200 with empty body for unknown product — severity medium→high · conf 0.91
  - API returns 200 with empty body instead of 404 for missing resources, breaking error handling logic in partner integrations.
- **cand-124** (en, r1) Autocomplete lags on older iPhones — severity medium→low · conf 0.82
  - Search autocomplete is slow on older iOS devices, degrading usability but not blocking search functionality.
- **cand-127** (en, r1) Push shows price in USD instead of MXN — severity medium→low; category data→ui · conf 0.80
  - Push notifications display USD currency labels for prices in MXN, confusing Mexican users about actual cost.
- **cand-138** (en, r1) API docs example uses an old field name — severity low→medium; category functional→ui · conf 0.85
  - API documentation example uses deprecated field name 'qty' instead of 'quantity', which could mislead developers and cause integration issues. This is documentation that needs correction.
- **hand-006** (en, r1) Category page takes over ten seconds to load — severity medium→high · conf 0.88
  - Category page with many products takes 11–14 seconds to load on initial visit, creating a poor user experience. Subsequent category switches are fast, suggesting initial load optimization is needed.
- **cand-001** (es, r2) Error 500 al pagar el pedido — component checkout→payments · conf 0.95
  - A core payment flow is completely broken with HTTP 500 errors, affecting all users across web and app platforms since a recent deploy. No orders can be created.
- **cand-002** (en, r2) checkout broken!!! — component checkout→payments · conf 0.95
  - The checkout/payment submission endpoint is returning HTTP 500 for all users since the last deployment, preventing any orders from being placed.
- **cand-003** (en, r2) Order confirmation returns HTTP 500 — component checkout→payments · conf 0.95
  - Order placement fails with HTTP 500 across all platforms after release 4.2.0, with no workaround available and preventing all purchases.
- **cand-028** (es, r2) Imagen de producto pixelada en iPad — severity low→medium · conf 0.85
  - Product images appear pixelated/blurry on iPad, loading thumbnails instead of full-resolution images, which is a display quality issue but not a functional blocker.
- **cand-029** (es, r2) fotos borrosas en tablet — severity low→medium · conf 0.85
  - Product images display at poor quality on tablets while working fine on phones, indicating a responsive image/resolution selection bug.
- **cand-035** (en, r2) Password reset email not arriving for Hotmail users — severity medium→high; component notifications→auth · conf 0.90
  - Password reset emails don't arrive for Hotmail/Outlook users but work for Gmail, blocking password recovery for a subset of users.
- **cand-036** (en, r2) No reset email (outlook) — severity medium→high; component notifications→auth · conf 0.90
  - User cannot receive password reset email on Outlook account despite multiple attempts, blocking access recovery for this user.
- **cand-069** (es, r2) No llega el código de verificación por SMS — severity high→medium; component notifications→auth · conf 0.85
  - Two-factor authentication via SMS fails to deliver codes, but users can use email as a workaround, so login is not fully blocked.
- **cand-073** (es, r2) El carrito se vacía al cerrar sesión — category data→functional · conf 0.92
  - Cart contents are lost after logout/login for all users, forcing them to rebuild their cart. This breaks the core shopping flow although users can work around it.
- **cand-083** (es, r2) Reporte de ventas no incluye pedidos con cupón — severity medium→high · conf 0.90
  - The monthly sales report excludes orders with coupons, causing financial data to be incomplete and misaligned with actual sales. This is data integrity issue affecting reporting accuracy.
- **cand-085** (es, r2) Buscar clientes en el admin tarda 15 segundos — severity medium→low · conf 0.75
  - Customer search in admin takes 15 seconds, which is slow but staff can still complete the task. This is a performance issue affecting admin usability.
- **cand-088** (es, r2) El cupón de primera compra se puede usar varias veces — severity medium→high · conf 0.90
  - The BIENVENIDA coupon should only work on first purchase but can be reused on all purchases. This allows users to abuse the promotional offer.
- **cand-108** (en, r2) Search shows products that can't ship to the user's region — severity high→medium; category data→functional · conf 0.85
  - Search results include products unavailable to users based on region, causing failures at checkout; search logic does not filter by user geography.
- **cand-116** (en, r2) Admin order list shows times in UTC — severity medium→low; category data→ui · conf 0.80
  - Admin displays order timestamps in UTC instead of the staff's local timezone, causing confusion but not blocking functionality; staff can work around it.
- **cand-118** (en, r2) Order cancellation email not sent — severity medium→high · conf 0.85
  - Order cancellation notifications fail to send to customers when support cancels orders, breaking the notification flow.
- **cand-122** (en, r2) API returns 200 with empty body for unknown product — severity medium→high · conf 0.88
  - API endpoint returns incorrect HTTP status (200 instead of 404) for missing resources, breaking partner error handling and violating REST conventions.
- **cand-124** (en, r2) Autocomplete lags on older iPhones — severity medium→low · conf 0.75
  - Search autocomplete causes noticeable lag on older iPhone models, degrading user experience but not blocking functionality.
- **cand-127** (en, r2) Push shows price in USD instead of MXN — severity medium→low; category data→ui · conf 0.80
  - Push notifications display incorrect currency label (USD vs MXN) despite correct amounts, causing user confusion about pricing.
- **cand-138** (en, r2) API docs example uses an old field name — severity low→medium · conf 0.85
  - The API documentation example uses an outdated field name that does not match the current API specification, potentially confusing developers. This is a documentation/functional mismatch.
- **hand-006** (en, r2) Category page takes over ten seconds to load — severity medium→high · conf 0.85
  - Category pages with many products take 11–14 seconds to load initially, which is a significant performance issue. The problem only occurs on first visit, suggesting caching or lazy-loading could help.
