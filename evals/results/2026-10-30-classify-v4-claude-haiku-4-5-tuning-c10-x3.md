# classify/v4 · global.anthropic.claude-haiku-4-5-20251001-v1:0 · seed-v1/tuning

Run 2026-10-30T05:00:12+00:00 · repeat 3 · 10 incidents per call · 60 items · 18 calls (18 fresh, 0 cached chunks)

| prompt | model | split | severity macro-F1 [95% CI] | sev acc | comp acc | cat acc | conf≥0.7 acc (share) | valid first try | needs_manual | $/100 | p50 / p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| classify/v4 | global.anthropic.claude-haiku-4-5-20251001-v1:0 | tuning | **0.752** [0.668-0.823] | 75.0% | 90.6% | 89.4% | 75.4% (99.4%) | 100.0% | 0.0% | $0.075 | 4874 / 5349 |

Language detection accuracy: 100.0%.

## Severity per class

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| critical | 0.92 | 1.00 | 0.96 | 33 |
| high | 0.68 | 0.92 | 0.78 | 48 |
| medium | 0.73 | 0.35 | 0.48 | 54 |
| low | 0.74 | 0.87 | 0.80 | 45 |

## Confusion (rows = gold, columns = predicted)

| gold \ pred | critical | high | medium | low | needs_manual |
|---|---|---|---|---|---|
| critical | 33 | 0 | 0 | 0 | 0 |
| high | 3 | 44 | 1 | 0 | 0 |
| medium | 0 | 21 | 19 | 14 | 0 |
| low | 0 | 0 | 6 | 39 | 0 |

## Calibration (severity correct, by stated confidence)

| confidence | count | mean confidence | accuracy |
|---|---|---|---|
| 0.0-0.2 | 0 | n/a | n/a |
| 0.2-0.4 | 0 | n/a | n/a |
| 0.4-0.6 | 1 | 0.50 | 0.0% |
| 0.6-0.8 | 31 | 0.70 | 71.0% |
| 0.8-1.0 | 148 | 0.86 | 76.4% |

## Errors (any label wrong, or needs_manual)

- **cand-001** (es, r0) Error 500 al pagar el pedido — component checkout→payments · conf 0.90
  - Payment checkout is completely broken across all platforms since deployment, returning 500 errors and preventing order creation for all users. This is a full outage of a core flow with no workaround.
- **cand-002** (en, r0) checkout broken!!! — component checkout→payments · conf 0.90
  - Checkout is broken for all users since last night's deploy, returning 500 errors on the order creation API endpoint. This is a complete failure of a core flow with no workaround.
- **cand-003** (en, r0) Order confirmation returns HTTP 500 — component checkout→payments · conf 0.90
  - Order placement fails with HTTP 500 across all platforms after release 4.2.0 with no workaround found. This is a full outage of the checkout/payment core flow.
- **cand-014** (es, r0) Notificación push duplicada — severity medium→low · conf 0.80
  - Users receive duplicate push notifications for every shipment, which is a minor functional issue with notifications. The behavior is incorrect but does not prevent core functionality.
- **cand-015** (en, r0) Duplicate 'order shipped' push — severity medium→low · conf 0.80
  - Users receive duplicate 'order shipped' push notifications every time, which is a functional defect in notification logic. This affects many users but is not blocking any core flow.
- **cand-028** (es, r0) Imagen de producto pixelada en iPad — severity low→medium · conf 0.80
  - Product images appear pixelated/blurry on iPad because thumbnails are loaded instead of full-size images. This is a UI/display issue specific to one device type.
- **cand-029** (es, r0) fotos borrosas en tablet — severity low→medium · conf 0.80
  - Product images display with poor quality on tablets but work fine on phones. This is a UI display/scaling issue affecting tablet users.
- **cand-032** (es, r0) Búsqueda muy lenta en la app — severity high→medium · conf 0.70
  - Search takes 6-8 seconds on app (4G) versus instant on web, making it slow but functional. This is a performance issue on the search feature.
- **cand-035** (en, r0) Password reset email not arriving for Hotmail users — severity medium→high; component notifications→auth · conf 0.80
  - Password reset emails fail to arrive for Hotmail/Outlook users but work for Gmail users. This blocks authentication for a subset of users with a workaround (contact support).
- **cand-036** (en, r0) No reset email (outlook) — severity medium→high; component notifications→auth · conf 0.75
  - User with Outlook account does not receive password reset email after multiple attempts. This is the same issue as inc-0019, blocking password reset auth flow.
- **cand-041** (es, r0) Direcciones guardadas se duplican al editar — severity medium→high · conf 0.70
  - Editing a saved address creates a duplicate instead of updating it, causing data duplication. This is a data handling defect in the profile address management.
- **cand-042** (es, r0) Se repiten mis direcciones — severity medium→high · conf 0.70
  - User's profile shows the same address duplicated 4 times after a minor edit. This is the same data duplication issue as inc-0021, affecting stored user data.
- **cand-073** (es, r0) El carrito se vacía al cerrar sesión — category data→functional · conf 0.80
  - Cart empties for all users when they log out and back in, forcing them to re-add items. This is a functional defect in cart persistence affecting the entire user base.
- **cand-083** (es, r0) Reporte de ventas no incluye pedidos con cupón — severity medium→high · conf 0.90
  - Sales reports exclude coupon-discounted orders, causing financial data discrepancies that directly impact business reporting accuracy and reconciliation.
- **cand-085** (es, r0) Buscar clientes en el admin tarda 15 segundos — severity medium→low · conf 0.70
  - Customer search in admin takes 15 seconds, which is a performance issue affecting staff productivity but not blocking critical operations.
- **cand-088** (es, r0) El cupón de primera compra se puede usar varias veces — severity medium→high · conf 0.90
  - The first-purchase welcome coupon can be used multiple times instead of once, allowing users to bypass intended business rules and abuse discounts.
- **cand-108** (en, r0) Search shows products that can't ship to the user's region — category data→functional · conf 0.80
  - Search returns products that cannot be purchased by users in certain regions, causing failures at checkout. This breaks the search flow for a specific region and forces users to try products they cannot buy.
- **cand-116** (en, r0) Admin order list shows times in UTC — severity medium→low; category data→ui · conf 0.80
  - Admin staff see order times in UTC instead of their local timezone, causing confusion about when orders were placed. This is a UI/display issue that doesn't block operations.
- **cand-127** (en, r0) Push shows price in USD instead of MXN — severity medium→low; category data→ui · conf 0.85
  - Push notifications display incorrect currency labels (USD instead of MXN) for Mexican users, though the amounts are in the correct currency. This is a UI/display issue in notifications.
- **cand-138** (en, r0) API docs example uses an old field name — category functional→ui · conf 0.90
  - The API documentation example shows an outdated field name, misleading developers but not affecting actual API functionality or production systems.
- **hand-006** (en, r0) Category page takes over ten seconds to load — severity medium→high · conf 0.90
  - Category pages with many products take 11–14 seconds on first load, which is a significant performance degradation that affects the core search/catalog flow.
- **hand-010** (en, r0) Unread notification badge does not clear immediately — category ui→functional · conf 0.70
  - The notification badge does not update immediately after reading notifications and requires a page refresh to clear, which is a functional bug in the notifications UI.
- **cand-001** (es, r1) Error 500 al pagar el pedido — component checkout→payments · conf 0.90
  - Checkout and payment process returns HTTP 500 error preventing order creation across all platforms and users since last night's deployment. This is a full outage of a core checkout/payment flow with no workaround.
- **cand-002** (en, r1) checkout broken!!! — component checkout→payments · conf 0.90
  - POST /api/orders endpoint returns HTTP 500 preventing any orders from being placed since last night's deployment. All users affected with no workaround.
- **cand-003** (en, r1) Order confirmation returns HTTP 500 — component checkout→payments · conf 0.90
  - Place order button returns HTTP 500 and blocks order creation across all platforms (web, iOS, Android) after release 4.2.0. This is a full outage of a critical flow with no workaround.
- **cand-014** (es, r1) Notificación push duplicada — severity medium→low · conf 0.90
  - Users receive the same shipment notification twice in quick succession on both iOS and Android. This is a functional defect in the notification system but does not block any core flows.
- **cand-015** (en, r1) Duplicate 'order shipped' push — severity medium→low · conf 0.90
  - Shipment notification is sent twice to all users within seconds of each other on both platforms. This is a functional defect but does not impact core functionality.
- **cand-028** (es, r1) Imagen de producto pixelada en iPad — severity low→medium · conf 0.80
  - Product images display at low quality (thumbnail instead of full resolution) on iPad, a non-core feature with wrong display behavior.
- **cand-029** (es, r1) fotos borrosas en tablet — severity low→medium · conf 0.80
  - Product images show poor quality on tablets but work fine on phones, indicating a device-specific UI/rendering issue in the catalog.
- **cand-035** (en, r1) Password reset email not arriving for Hotmail users — severity medium→high; component notifications→auth · conf 0.80
  - Password reset emails don't arrive for Hotmail/Outlook users but do for Gmail, breaking auth for a segment of users with no workaround.
- **cand-036** (en, r1) No reset email (outlook) — severity medium→high; component notifications→auth · conf 0.80
  - User cannot receive password reset email on Outlook account after multiple attempts, blocking core auth functionality with no workaround.
- **cand-041** (es, r1) Direcciones guardadas se duplican al editar — severity medium→high · conf 0.90
  - Saved addresses are duplicated instead of updated, causing data inconsistency. User explicitly reports 5 copies of the same address already created.
- **cand-042** (es, r1) Se repiten mis direcciones — severity medium→high · conf 0.90
  - Same issue as inc-0021: saved addresses are duplicated instead of updated when edited, causing data inconsistency across the profile.
- **cand-045** (en, r1) Webhook delivery queue empty for order events — severity high→critical · conf 0.90
  - Webhook dispatcher shows zero deliveries for order.created since v4.2.0 deploy, while other event types work. This is a broken core integration point.
- **cand-069** (es, r1) No llega el código de verificación por SMS — component notifications→auth · conf 0.80
  - SMS verification codes are not delivered for 2FA, but users have an email workaround available. This affects a core auth flow but a workaround exists.
- **cand-073** (es, r1) El carrito se vacía al cerrar sesión — category data→functional · conf 0.80
  - Shopping cart is cleared on logout and login, affecting all users. This breaks cart persistence, a core flow behavior, though users can re-add items.
- **cand-083** (es, r1) Reporte de ventas no incluye pedidos con cupón — severity medium→high · conf 0.90
  - The sales report excludes orders with coupons, causing financial reconciliation errors and incorrect data displayed to admin users. This is a data integrity issue affecting reporting accuracy.
- **cand-085** (es, r1) Buscar clientes en el admin tarda 15 segundos — severity medium→low · conf 0.50
  - Customer search in admin takes 15 seconds, which is slow but the feature works and staff can still complete their tasks. This is a performance issue in a non-core feature.
- **cand-088** (es, r1) El cupón de primera compra se puede usar varias veces — severity medium→high · conf 0.90
  - The BIENVENIDA welcome coupon can be used multiple times instead of only once per customer, breaking the business logic and enabling coupon abuse. This is a functional defect in the coupon system.
- **cand-108** (en, r1) Search shows products that can't ship to the user's region — category data→functional · conf 0.80
  - Search returns unavailable products for a region, causing checkout failures; this breaks the search-to-checkout flow for affected users but they can still purchase available items.
- **cand-116** (en, r1) Admin order list shows times in UTC — severity medium→low; category data→ui · conf 0.90
  - Admin UI displays order times in UTC instead of local timezone, causing confusion for staff but not affecting customer-facing functionality or data accuracy.
- **cand-122** (en, r1) API returns 200 with empty body for unknown product — severity medium→high · conf 0.85
  - API returns 200 with empty body instead of 404 for missing products, violating REST conventions and breaking partner error handling.
- **cand-124** (en, r1) Autocomplete lags on older iPhones — severity medium→low · conf 0.85
  - Search autocomplete is slow on older iPhones, degrading user experience; the feature works but is sluggish on a subset of devices.
- **cand-127** (en, r1) Push shows price in USD instead of MXN — category data→ui · conf 0.80
  - Push notifications display USD currency label instead of MXN for Mexican users, a UI/data mismatch that misleads about pricing but does not block purchases.
- **cand-138** (en, r1) API docs example uses an old field name — category functional→ui · conf 0.70
  - The API documentation example shows an outdated parameter name that does not match the current API specification. This will mislead developers but can be worked around by consulting the actual spec.
- **hand-010** (en, r1) Unread notification badge does not clear immediately — category ui→functional · conf 0.70
  - The unread notification badge does not update immediately after reading notifications until the page is refreshed. This is a functional issue where the UI state does not sync with the user's actions.
- **cand-001** (es, r2) Error 500 al pagar el pedido — component checkout→payments · conf 0.90
  - Error 500 during payment prevents order creation entirely across all accounts and platforms since the latest release. This blocks the core checkout flow with no workaround.
- **cand-002** (en, r2) checkout broken!!! — component checkout→payments · conf 0.90
  - POST /api/orders returning 500 prevents all users from placing orders since last night's deploy. This is a complete outage of a core flow with no workaround.
- **cand-003** (en, r2) Order confirmation returns HTTP 500 — component checkout→payments · conf 0.90
  - HTTP 500 on order placement blocks order creation across all platforms after release 4.2.0 with no workaround found. This is a critical outage of the checkout flow.
- **cand-014** (es, r2) Notificación push duplicada — severity medium→low; category functional→ui · conf 0.90
  - Users receive the same push notification twice for every shipment. This is a cosmetic/usability issue with no functional impact.
- **cand-015** (en, r2) Duplicate 'order shipped' push — severity medium→low; category functional→ui · conf 0.90
  - Users receive 'order shipped' push notification twice for every shipment. This is a cosmetic/usability issue with no functional impact.
- **cand-022** (en, r2) Crash: IndexOutOfBoundsException in OrderAdapter — severity high→critical · conf 0.90
  - IndexOutOfBoundsException in OrderAdapter is causing 2,310 crashes in 24h on the order history screen, indicating a widespread crash affecting many users.
- **cand-034** (es, r2) Latencia alta en /search desde móvil — severity high→critical · conf 0.80
  - The /search endpoint responds 26x slower on app (p95 7.8s) than web (300ms) because the app uses an old index; this is a critical performance gap affecting a core flow with no workaround documented.
- **cand-035** (en, r2) Password reset email not arriving for Hotmail users — severity medium→high; component notifications→auth · conf 0.80
  - Password reset emails don't arrive for Hotmail/Outlook users, blocking account recovery for a subset of users; Gmail users can recover, suggesting a workaround-like situation.
- **cand-036** (en, r2) No reset email (outlook) — severity medium→high; component notifications→auth · conf 0.70
  - Outlook user unable to receive password reset email after multiple attempts, indicating a systematic delivery failure for that email provider domain.
- **cand-069** (es, r2) No llega el código de verificación por SMS — component notifications→auth · conf 0.70
  - SMS verification codes are not being delivered for two-factor authentication, but users have an email alternative workaround. This breaks a core auth flow for some users.
- **cand-073** (es, r2) El carrito se vacía al cerrar sesión — category data→functional · conf 0.80
  - Cart is cleared when users log out and log back in, affecting all users and forcing re-entry of items. This breaks cart persistence, a core feature.
- **cand-083** (es, r2) Reporte de ventas no incluye pedidos con cupón — severity medium→high · conf 0.80
  - The monthly sales report omits orders with coupon codes, causing incorrect totals that don't match financial records. This is a data integrity issue affecting reporting accuracy.
- **cand-085** (es, r2) Buscar clientes en el admin tarda 15 segundos — severity medium→low · conf 0.70
  - Customer search by email in admin takes 15 seconds, which is slow but the feature still works. This is a performance issue affecting an admin feature.
- **cand-088** (es, r2) El cupón de primera compra se puede usar varias veces — severity medium→high · conf 0.80
  - A first-purchase-only coupon can be used repeatedly, violating business logic and allowing unintended discounts. This is a functional defect in the coupon validation system.
- **cand-101** (en, r2) User sees another customer's cart — category security→data · conf 0.90
  - Users see other customers' cart and address data due to CDN caching, exposing sensitive personal and transactional data. This is a data privacy breach affecting the checkout core flow.
- **cand-108** (en, r2) Search shows products that can't ship to the user's region — category data→functional · conf 0.80
  - Search returns products that cannot be purchased by the user, causing checkout failures. This breaks the search experience for users in unsupported regions, but checkout still processes valid items.
- **cand-113** (en, r2) Can't change account email — severity medium→high · conf 0.85
  - Email address change in profile appears to save but does not persist, leaving the account data unchanged. This is a functional defect in account management with no workaround.
- **cand-116** (en, r2) Admin order list shows times in UTC — severity medium→low; category data→ui · conf 0.80
  - Admin order timestamps display in UTC instead of the local timezone, causing timezone confusion for staff. This is a UI/presentation issue with no impact on core order operations.
- **cand-118** (en, r2) Order cancellation email not sent — severity medium→high · conf 0.85
  - Order cancellation emails are not sent to customers when support cancels orders. This breaks the notification flow for a critical customer event with no workaround.
- **cand-122** (en, r2) API returns 200 with empty body for unknown product — severity medium→high · conf 0.80
  - API returns 200 with empty body instead of 404 for unknown products, violating REST conventions and breaking partner error handling logic.
- **cand-128** (en, r2) Long product titles truncated with no tooltip — severity low→medium · conf 0.70
  - Product titles are truncated without a way to view the full text, making it impossible for users to read complete product names in the grid view. This is a usability issue affecting the catalog experience.
- **cand-138** (en, r2) API docs example uses an old field name — severity low→medium; category functional→ui · conf 0.70
  - The API documentation example shows an incorrect field name ('qty' instead of 'quantity'), which will mislead developers trying to use the API. This is a documentation correctness issue.
