# classify/v2 · global.anthropic.claude-haiku-4-5-20251001-v1:0 · seed-v1/tuning

Run 2026-10-30T04:56:23+00:00 · repeat 3 · 10 incidents per call · 60 items · 18 calls (18 fresh, 0 cached chunks)

| prompt | model | split | severity macro-F1 [95% CI] | sev acc | comp acc | cat acc | conf≥0.7 acc (share) | valid first try | needs_manual | $/100 | p50 / p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| classify/v2 | global.anthropic.claude-haiku-4-5-20251001-v1:0 | tuning | **0.752** [0.673-0.822] | 73.9% | 92.8% | 91.7% | 73.9% (100.0%) | 100.0% | 0.0% | $0.076 | 4964 / 5702 |

Language detection accuracy: 100.0%.

## Severity per class

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| critical | 0.97 | 1.00 | 0.99 | 33 |
| high | 0.67 | 0.81 | 0.74 | 48 |
| medium | 0.62 | 0.39 | 0.48 | 54 |
| low | 0.74 | 0.89 | 0.81 | 45 |

## Confusion (rows = gold, columns = predicted)

| gold \ pred | critical | high | medium | low | needs_manual |
|---|---|---|---|---|---|
| critical | 33 | 0 | 0 | 0 | 0 |
| high | 1 | 39 | 8 | 0 | 0 |
| medium | 0 | 19 | 21 | 14 | 0 |
| low | 0 | 0 | 5 | 40 | 0 |

## Calibration (severity correct, by stated confidence)

| confidence | count | mean confidence | accuracy |
|---|---|---|---|
| 0.0-0.2 | 0 | n/a | n/a |
| 0.2-0.4 | 0 | n/a | n/a |
| 0.4-0.6 | 0 | n/a | n/a |
| 0.6-0.8 | 3 | 0.75 | 66.7% |
| 0.8-1.0 | 177 | 0.90 | 74.0% |

## Errors (any label wrong, or needs_manual)

- **cand-001** (es, r0) Error 500 al pagar el pedido — component checkout→payments · conf 0.95
  - A core flow (checkout/payments) is completely broken for all users across web and app after the latest deployment, with no workaround available, preventing any orders from being created.
- **cand-014** (es, r0) Notificación push duplicada — severity medium→low · conf 0.85
  - Users receive duplicate push notifications for order shipments, which is a non-core feature displaying wrong behavior but does not block any functionality.
- **cand-015** (en, r0) Duplicate 'order shipped' push — severity medium→low · conf 0.85
  - Users receive duplicate push notifications for shipments, which is a non-core feature showing incorrect behavior but does not block functionality.
- **cand-028** (es, r0) Imagen de producto pixelada en iPad — severity low→medium · conf 0.85
  - Product images display at low quality on iPad, appearing as thumbnails instead of full resolution, a display issue affecting catalog browsing.
- **cand-029** (es, r0) fotos borrosas en tablet — severity low→medium · conf 0.88
  - Product images show poor quality on tablets while working correctly on phones, a display issue affecting catalog on specific devices.
- **cand-035** (en, r0) Password reset email not arriving for Hotmail users — severity medium→high; component notifications→auth · conf 0.93
  - Password reset emails are not arriving for Hotmail and Outlook users, blocking a core auth flow for affected users with no workaround.
- **cand-036** (en, r0) No reset email (outlook) — severity medium→high; component notifications→auth · conf 0.90
  - Outlook user unable to receive password reset email after multiple attempts, blocking password recovery with no workaround.
- **cand-045** (en, r0) Webhook delivery queue empty for order events — severity high→critical; category functional→crash · conf 0.90
  - Webhook dispatcher shows zero deliveries for order events since 4.2.0 deploy; partners cannot receive order notifications. Critical API functionality is down.
- **cand-069** (es, r0) No llega el código de verificación por SMS — component notifications→auth · conf 0.85
  - SMS verification codes not delivered in two-step authentication, but email alternative exists as workaround. Core auth flow is partially broken with a workaround available.
- **cand-073** (es, r0) El carrito se vacía al cerrar sesión — category data→functional · conf 0.90
  - Cart contents are lost after logout and login for all users, requiring re-adding items. Core checkout flow is affected for every user with no workaround.
- **cand-077** (es, r0) No se ve la tabla de tallas en móvil — severity medium→high · conf 0.80
  - Size table is not visible on mobile product pages, preventing users from accessing important product information needed for purchase decisions.
- **cand-083** (es, r0) Reporte de ventas no incluye pedidos con cupón — severity medium→high · conf 0.90
  - Sales report excludes orders with coupons, resulting in wrong totals that don't match financial records, causing data inconsistency.
- **cand-088** (es, r0) El cupón de primera compra se puede usar varias veces — severity medium→high · conf 0.85
  - First-purchase coupon can be used multiple times instead of being limited to first purchase only, allowing customers to exploit the discount policy.
- **cand-108** (en, r0) Search shows products that can't ship to the user's region — severity high→medium · conf 0.85
  - Search results include unavailable products, causing checkout failures for affected users. This breaks a core flow (search/checkout) for a small group in a specific region, not all users.
- **cand-113** (en, r0) Can't change account email — category functional→data · conf 0.80
  - Email change in profile shows success but does not persist; the old email remains. This is a data consistency issue in a non-core feature, affecting a small group.
- **cand-116** (en, r0) Admin order list shows times in UTC — severity medium→low; category data→ui · conf 0.85
  - Admin order list displays times in the wrong timezone, causing staff confusion but not blocking operations or losing data. This is a UI/display issue in the back-office.
- **cand-122** (en, r0) API returns 200 with empty body for unknown product — severity medium→high · conf 0.85
  - The API returns 200 with an empty body instead of 404, breaking partner error handling. This is a functional defect in the API contract affecting external integrations.
- **cand-127** (en, r0) Push shows price in USD instead of MXN — severity medium→low; category data→ui · conf 0.90
  - Push notifications display the wrong currency label while amounts are correct. This is a UI/display issue in notifications; nothing is blocked and the transaction values are right.
- **cand-138** (en, r0) API docs example uses an old field name — category functional→ui · conf 0.85
  - The API documentation example uses an outdated field name, which misleads developers but the actual API works correctly.
- **hand-006** (en, r0) Category page takes over ten seconds to load — severity medium→high · conf 0.88
  - Category pages take 11-14 seconds to load on first visit, which blocks the user from viewing products in a core flow (search/catalog browsing).
- **cand-001** (es, r1) Error 500 al pagar el pedido — component checkout→payments · conf 0.95
  - Checkout payment fails with HTTP 500 for all users across web and app since release 4.2.0, blocking all orders with no workaround.
- **cand-003** (en, r1) Order confirmation returns HTTP 500 — component checkout→payments · conf 0.95
  - Place order returns HTTP 500 across all platforms after release 4.2.0, preventing any order creation with no workaround.
- **cand-014** (es, r1) Notificación push duplicada — severity medium→low · conf 0.90
  - Push notification sent twice for order shipment events; annoying but users are not blocked and notification content is correct.
- **cand-015** (en, r1) Duplicate 'order shipped' push — severity medium→low · conf 0.90
  - Duplicate push notifications for shipment on both platforms; cosmetic issue that does not block functionality or show wrong data.
- **cand-032** (es, r1) Búsqueda muy lenta en la app — severity high→medium · conf 0.90
  - Search takes 6-8 seconds on the app but is instant on the web, causing a significant delay in a core flow. Users can still search but experience poor performance.
- **cand-033** (es, r1) buscar tarda muchisimo — severity high→medium · conf 0.85
  - Search hangs for a long time on the app causing user frustration and abandonment, while web search is fast. This performance issue affects the core search flow.
- **cand-034** (es, r1) Latencia alta en /search desde móvil — severity high→medium · conf 0.92
  - The /search API endpoint responds in 7.8s (p95) on mobile compared to 300ms on web because the app uses an outdated search index. This is a performance issue in a core flow with a known root cause.
- **cand-035** (en, r1) Password reset email not arriving for Hotmail users — severity medium→high; component notifications→auth · conf 0.92
  - Password reset emails don't arrive for @hotmail.com and @outlook.com users, blocking them from recovering access to their accounts. This is a functional failure in the auth flow affecting multiple users.
- **cand-036** (en, r1) No reset email (outlook) — severity medium→high; component notifications→auth · conf 0.90
  - User with Outlook account did not receive password reset email after multiple attempts, blocking account recovery. This confirms the password reset failure for Outlook users.
- **cand-069** (es, r1) No llega el código de verificación por SMS — severity high→medium; component notifications→auth · conf 0.85
  - SMS verification codes don't arrive, but users have email as workaround. This is a broken feature with an alternative available, affecting a subset of 2FA users.
- **cand-073** (es, r1) El carrito se vacía al cerrar sesión — category data→functional · conf 0.85
  - Cart empties on logout for all users, forcing re-entry of items. This breaks the core cart flow but is a known behavior users can work around by staying logged in.
- **cand-077** (es, r1) No se ve la tabla de tallas en móvil — severity medium→high · conf 0.80
  - The size table is missing on mobile product pages, blocking users from viewing sizing information needed for purchase. This breaks the product viewing experience for mobile users.
- **cand-083** (es, r1) Reporte de ventas no incluye pedidos con cupón — severity medium→high · conf 0.88
  - Sales report excludes orders with coupons, causing incorrect financial data and reconciliation issues between admin and finance. This is a data integrity problem in a core admin report.
- **cand-088** (es, r1) El cupón de primera compra se puede usar varias veces — severity medium→high · conf 0.88
  - The first-purchase coupon can be reused multiple times when it should only work once, allowing fraudulent discounts. This is a functional defect affecting checkout that causes revenue loss.
- **cand-108** (en, r1) Search shows products that can't ship to the user's region — severity high→medium · conf 0.85
  - Search results show unavailable products that fail at checkout, creating a broken flow for users in unsupported regions. This is a core flow showing wrong values for a geographic subset of users.
- **cand-116** (en, r1) Admin order list shows times in UTC — severity medium→low; category data→ui · conf 0.80
  - Order times display in the wrong timezone for admin staff, causing confusion but not blocking operations. This is a display/cosmetic issue in a back-office tool.
- **cand-122** (en, r1) API returns 200 with empty body for unknown product — severity medium→high · conf 0.85
  - The API returns 200 with an empty body instead of the correct 404 error, breaking partner error handling logic. This is incorrect behavior in the API contract.
- **cand-124** (en, r1) Autocomplete lags on older iPhones — severity medium→low · conf 0.75
  - Search autocomplete performance lags on older devices, causing a poor user experience but search still works. This is a performance issue with a workaround (waiting or typing slower).
- **cand-127** (en, r1) Push shows price in USD instead of MXN — severity medium→low; category data→ui · conf 0.80
  - Push notifications show USD labels on MXN prices for Mexican users, creating confusion about currency. This is displayed data that is misleading but amounts are correct.
- **cand-138** (en, r1) API docs example uses an old field name — severity low→medium; category functional→ui · conf 0.85
  - The API documentation example uses an outdated field name, which could mislead developers integrating with the API. This is a documentation issue affecting the API component.
- **hand-007** (en, r1) Expired saved card is accepted until final payment — component payments→checkout · conf 0.92
  - Checkout accepts an expired saved card without validation or warning until payment is attempted, resulting in a transaction failure. This is a functional defect in a core checkout flow affecting payment processing.
- **hand-010** (en, r1) Unread notification badge does not clear immediately — category ui→functional · conf 0.85
  - The unread notification badge does not update immediately after reading notifications and requires a page refresh. This is a minor functional issue in a non-core feature.
- **cand-014** (es, r2) Notificación push duplicada — severity medium→low · conf 0.90
  - Duplicate 'order shipped' push notifications are being sent for every shipment across both platforms. While annoying, this does not block any functionality or cause data loss.
- **cand-015** (en, r2) Duplicate 'order shipped' push — severity medium→low · conf 0.90
  - Users receive the 'order shipped' push notification twice per shipment on both platforms. While annoying, this does not block any functionality or cause data loss.
- **cand-035** (en, r2) Password reset email not arriving for Hotmail users — severity medium→high; component notifications→auth · conf 0.93
  - Password reset emails don't reach Hotmail/Outlook users while Gmail users receive them. This blocks password recovery for a subset of users in a core authentication flow.
- **cand-036** (en, r2) No reset email (outlook) — severity medium→high; component notifications→auth · conf 0.92
  - User with Outlook address cannot receive password reset email after multiple attempts, blocking account recovery in the auth flow.
- **cand-069** (es, r2) No llega el código de verificación por SMS — severity high→medium; component notifications→auth · conf 0.80
  - SMS verification codes not arriving for two-step authentication, but email is available as workaround. Auth partially broken with fallback.
- **cand-073** (es, r2) El carrito se vacía al cerrar sesión — category data→functional · conf 0.90
  - Cart is cleared on logout/login for all users, blocking the core cart functionality with no workaround. Users must rebuild cart after each session.
- **cand-075** (es, r2) No se pueden marcar pedidos como enviados — severity high→medium · conf 0.85
  - The admin button to mark orders as shipped is broken, forcing warehouse staff to use the API as a workaround. This affects admin operations but is not a core customer flow and a workaround exists.
- **cand-079** (es, r2) Imágenes de productos tardan mucho en 3G — severity medium→low · conf 0.80
  - Product images load slowly (over 10 seconds) on 3G connections. This is a performance issue affecting the catalog but the feature eventually works.
- **cand-083** (es, r2) Reporte de ventas no incluye pedidos con cupón — severity medium→high · conf 0.90
  - Sales report in admin excludes orders with coupons, causing incorrect totals and data inconsistency with the finance department. This is a data integrity issue in admin reporting.
- **cand-085** (es, r2) Buscar clientes en el admin tarda 15 segundos — severity medium→low · conf 0.80
  - Admin customer search by email takes 15 seconds. This is a performance issue affecting admin operations but the search eventually completes.
- **cand-088** (es, r2) El cupón de primera compra se puede usar varias veces — severity medium→high · conf 0.85
  - First-purchase welcome coupon can be used multiple times instead of just once. This is a functional defect allowing unintended coupon reuse and revenue loss.
- **cand-116** (en, r2) Admin order list shows times in UTC — category data→ui · conf 0.80
  - Admin list displays times in UTC instead of the local timezone, causing confusion about order dates. This is a UI/data display issue affecting admin usability but not blocking operations.
- **cand-122** (en, r2) API returns 200 with empty body for unknown product — severity medium→high · conf 0.88
  - The API returns 200 with an empty body instead of 404 for unknown products, which is incorrect behavior that breaks client error handling logic.
- **cand-127** (en, r2) Push shows price in USD instead of MXN — severity medium→low; category data→ui · conf 0.85
  - Push notifications display the wrong currency label (USD instead of MXN) for Mexican users, though the amounts are correct in the local currency. This is a UI labeling issue.
- **cand-128** (en, r2) Long product titles truncated with no tooltip — severity low→medium · conf 0.85
  - Product titles are truncated with no way to read the full text, blocking users from viewing complete product information in the catalog grid.
- **cand-138** (en, r2) API docs example uses an old field name — severity low→medium; category functional→ui · conf 0.80
  - API documentation example uses incorrect field name, misleading developers; this is a documentation accuracy issue affecting the API component.
- **hand-006** (en, r2) Category page takes over ten seconds to load — severity medium→high · conf 0.85
  - Category pages take 11–14 seconds to load initially on a reasonable connection; this is a performance issue blocking the search/catalog core flow.
