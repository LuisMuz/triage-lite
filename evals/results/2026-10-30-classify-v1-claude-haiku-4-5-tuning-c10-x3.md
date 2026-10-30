# classify/v1 · global.anthropic.claude-haiku-4-5-20251001-v1:0 · seed-v1/tuning

Run 2026-10-30T04:54:32+00:00 · repeat 3 · 10 incidents per call · 60 items · 18 calls (12 fresh, 6 cached chunks)

| prompt | model | split | severity macro-F1 [95% CI] | sev acc | comp acc | cat acc | conf≥0.7 acc (share) | valid first try | needs_manual | $/100 | p50 / p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| classify/v1 | global.anthropic.claude-haiku-4-5-20251001-v1:0 | tuning | **0.752** [0.658-0.827] | 74.4% | 91.7% | 90.6% | 74.4% (100.0%) | 100.0% | 0.0% | $0.071 | 4569 / 5767 |

Language detection accuracy: 100.0%.

## Severity per class

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| critical | 0.92 | 1.00 | 0.96 | 33 |
| high | 0.64 | 0.94 | 0.76 | 48 |
| medium | 0.68 | 0.39 | 0.49 | 54 |
| low | 0.81 | 0.78 | 0.80 | 45 |

## Confusion (rows = gold, columns = predicted)

| gold \ pred | critical | high | medium | low | needs_manual |
|---|---|---|---|---|---|
| critical | 33 | 0 | 0 | 0 | 0 |
| high | 3 | 45 | 0 | 0 | 0 |
| medium | 0 | 25 | 21 | 8 | 0 |
| low | 0 | 0 | 10 | 35 | 0 |

## Calibration (severity correct, by stated confidence)

| confidence | count | mean confidence | accuracy |
|---|---|---|---|
| 0.0-0.2 | 0 | n/a | n/a |
| 0.2-0.4 | 0 | n/a | n/a |
| 0.4-0.6 | 0 | n/a | n/a |
| 0.6-0.8 | 3 | 0.75 | 100.0% |
| 0.8-1.0 | 177 | 0.90 | 74.0% |

## Errors (any label wrong, or needs_manual)

- **cand-001** (es, r0) Error 500 al pagar el pedido — component checkout→payments · conf 0.95
  - Payment processing fails with HTTP 500 across all platforms since last night's deploy, blocking all users from completing purchases with no workaround.
- **cand-002** (en, r0) checkout broken!!! — component checkout→payments · conf 0.95
  - Order placement returns HTTP 500 for all users since last deploy, preventing any orders from being created with no workaround available.
- **cand-003** (en, r0) Order confirmation returns HTTP 500 — component checkout→payments · conf 0.95
  - Place order returns HTTP 500 on all platforms after 4.2.0 release, preventing order creation with no workaround.
- **cand-028** (es, r0) Imagen de producto pixelada en iPad — severity low→medium · conf 0.85
  - Product images appear pixelated on iPad because the app loads thumbnails instead of full-resolution images, a UI rendering issue.
- **cand-029** (es, r0) fotos borrosas en tablet — severity low→medium · conf 0.80
  - Product images display with poor quality on tablets but work fine on phones, indicating a device-specific UI/rendering issue.
- **cand-035** (en, r0) Password reset email not arriving for Hotmail users — severity medium→high; component notifications→auth · conf 0.90
  - Password reset emails fail to deliver for Hotmail/Outlook users but work for Gmail, blocking authentication for a user segment.
- **cand-036** (en, r0) No reset email (outlook) — severity medium→high; component notifications→auth · conf 0.88
  - Password reset email not received by Outlook user after multiple attempts, blocking access to account recovery.
- **cand-041** (es, r0) Direcciones guardadas se duplican al editar — severity medium→high · conf 0.95
  - Saved addresses are duplicated instead of updated when edited, causing data corruption in the user profile. This is a data integrity issue affecting stored user information.
- **cand-042** (es, r0) Se repiten mis direcciones — severity medium→high · conf 0.95
  - User reports duplicate addresses in their profile after editing. This is the same data duplication issue as inc-0021, affecting the Android app platform.
- **cand-045** (en, r0) Webhook delivery queue empty for order events — severity high→critical · conf 0.92
  - Webhook dispatcher shows zero deliveries for order.created events since v4.2.0 deploy while other event types work. This is a critical API failure affecting order notifications with no workaround mentioned.
- **cand-073** (es, r0) El carrito se vacía al cerrar sesión — category data→functional · conf 0.88
  - Shopping cart empties when user logs out and back in, requiring re-adding all items. This breaks the cart persistence feature for all users but is not a complete checkout failure.
- **cand-077** (es, r0) No se ve la tabla de tallas en móvil — severity medium→high · conf 0.88
  - The size table is not visible on mobile product pages, preventing users from viewing sizing information on a key platform.
- **cand-083** (es, r0) Reporte de ventas no incluye pedidos con cupón — severity medium→high · conf 0.90
  - The sales report excludes orders with coupons, resulting in incorrect financial data that doesn't match accounting records.
- **cand-088** (es, r0) El cupón de primera compra se puede usar varias veces — severity medium→high · conf 0.89
  - The first-purchase coupon can be reused multiple times instead of once, allowing users to exploit the promotion and reducing revenue.
- **cand-101** (en, r0) User sees another customer's cart — category security→data · conf 0.90
  - Data exposure where users see each other's cart and addresses is a critical data breach affecting payment and privacy, though limited to specific network conditions.
- **cand-108** (en, r0) Search shows products that can't ship to the user's region — category data→functional · conf 0.85
  - Search results showing unavailable products lead to checkout failures for affected users, breaking the search and discovery flow for a specific region.
- **cand-113** (en, r0) Can't change account email — severity medium→high · conf 0.85
  - Email change fails silently, leaving the account with the old email; this breaks a core profile functionality.
- **cand-116** (en, r0) Admin order list shows times in UTC — severity medium→low; category data→ui · conf 0.90
  - Timezone display issue in admin list causes confusion for staff but does not block order management or data integrity.
- **cand-122** (en, r0) API returns 200 with empty body for unknown product — severity medium→high · conf 0.85
  - API returns 200 instead of 404 for missing resources, breaking partner error handling and violating REST standards.
- **cand-127** (en, r0) Push shows price in USD instead of MXN — severity medium→low; category data→ui · conf 0.85
  - Push notification shows wrong currency label (USD instead of MXN) while amounts are correct, causing user confusion.
- **cand-128** (en, r0) Long product titles truncated with no tooltip — severity low→medium · conf 0.85
  - Product titles are truncated without a tooltip or way to view the full text, preventing users from reading important product information on the grid view.
- **cand-138** (en, r0) API docs example uses an old field name — severity low→medium; category functional→ui · conf 0.80
  - API documentation example uses an outdated field name that does not match the current API specification, leading to developer confusion.
- **hand-006** (en, r0) Category page takes over ten seconds to load — severity medium→high · conf 0.85
  - Category pages take 11-14 seconds to load initially on a reasonable connection, which is a significant performance degradation for a core catalog flow.
- **cand-001** (es, r1) Error 500 al pagar el pedido — component checkout→payments · conf 0.95
  - Error 500 on payment submission prevents order creation across all users and platforms. This is a complete failure of the checkout/payment flow with no workaround.
- **cand-007** (en, r1) Customers charged twice for one order — category data→functional · conf 0.92
  - 14 support tickets report duplicate charges from retry logic in payment confirmation. Multiple customers affected with actual financial impact.
- **cand-014** (es, r1) Notificación push duplicada — severity medium→low · conf 0.85
  - Users receive duplicate push notifications on every shipment, but functionality is correct. This is a minor usability/notification issue.
- **cand-015** (en, r1) Duplicate 'order shipped' push — severity medium→low · conf 0.85
  - Push notifications sent twice for every shipment across iOS and Android. Functional behavior is working but duplicating unnecessarily.
- **cand-028** (es, r1) Imagen de producto pixelada en iPad — severity low→medium · conf 0.85
  - Product images appear pixelated on iPad Pro, displaying thumbnails instead of full resolution. This is a UI/display issue with incorrect asset loading.
- **cand-029** (es, r1) fotos borrosas en tablet — severity low→medium · conf 0.80
  - Product images show poor quality on tablet but work fine on mobile, indicating a responsive image loading issue specific to tablet form factors.
- **cand-035** (en, r1) Password reset email not arriving for Hotmail users — severity medium→high; component notifications→auth · conf 0.90
  - Password reset emails fail to arrive for Hotmail/Outlook users while Gmail works, blocking login recovery for a subset of users. No workaround documented.
- **cand-036** (en, r1) No reset email (outlook) — severity medium→high; component notifications→auth · conf 0.88
  - User unable to receive password reset email on Outlook after multiple attempts, including not in spam folder. This is a functional failure of core auth flow.
- **cand-041** (es, r1) Direcciones guardadas se duplican al editar — severity medium→high · conf 0.95
  - Edited addresses are duplicated instead of updated, causing data corruption in the profile. This is a data issue affecting the profile component.
- **cand-042** (es, r1) Se repiten mis direcciones — severity medium→high · conf 0.95
  - User has duplicate address entries in their profile, similar to inc-0021. This is a data integrity issue in the profile component.
- **cand-045** (en, r1) Webhook delivery queue empty for order events — severity high→critical · conf 0.95
  - Webhook dispatcher shows zero order.created deliveries since deploy 4.2.0, breaking the API integration for partners and internal systems. This is a core API functionality failure.
- **cand-069** (es, r1) No llega el código de verificación por SMS — component notifications→auth · conf 0.88
  - Two-factor authentication SMS delivery is broken, but users have a workaround using email codes. This breaks a security feature for many users but a workaround exists.
- **cand-073** (es, r1) El carrito se vacía al cerrar sesión — category data→functional · conf 0.93
  - Cart contents are lost after logout and login for all users, requiring them to re-add items. This breaks the cart persistence feature across the core cart flow.
- **cand-083** (es, r1) Reporte de ventas no incluye pedidos con cupón — severity medium→high · conf 0.90
  - Sales report is missing orders with coupons, causing financial discrepancies. This is data integrity issue affecting reporting accuracy.
- **cand-088** (es, r1) El cupón de primera compra se puede usar varias veces — severity medium→high · conf 0.90
  - First-purchase coupon BIENVENIDA can be used multiple times instead of only once. This is a functional defect affecting business logic and revenue.
- **cand-108** (en, r1) Search shows products that can't ship to the user's region — category data→functional · conf 0.85
  - Search results include unavailable products that fail at checkout, forcing users to retry. This is a functional defect in search filtering for non-US regions, affecting core search experience but users can workaround by manual selection.
- **cand-113** (en, r1) Can't change account email — severity medium→high · conf 0.88
  - Email address change shows a success message but does not persist the new email. This is a functional defect in profile management where the update silently fails.
- **cand-116** (en, r1) Admin order list shows times in UTC — severity medium→low; category data→ui · conf 0.82
  - Admin displays order times in UTC instead of local timezone, causing confusion but not blocking operations. This is a UI/presentation issue affecting staff usability in the back-office.
- **cand-122** (en, r1) API returns 200 with empty body for unknown product — severity medium→high · conf 0.86
  - The API returns 200 with empty body for unknown products instead of proper 404 error, breaking partner error handling logic. This is a functional defect in API response behavior.
- **cand-127** (en, r1) Push shows price in USD instead of MXN — severity medium→low; category data→ui · conf 0.80
  - Push notifications display currency label in USD when amounts are actually MXN, confusing Mexican users about the actual price. This is a UI/data presentation issue in notifications.
- **cand-138** (en, r1) API docs example uses an old field name — severity low→medium; category functional→ui · conf 0.85
  - API documentation example uses deprecated field name that would cause developers to fail requests, creating confusion for API consumers.
- **hand-006** (en, r1) Category page takes over ten seconds to load — severity medium→high · conf 0.90
  - Category page with many products takes 11-14 seconds on initial load, significantly impacting user experience on a core catalog flow.
- **hand-010** (en, r1) Unread notification badge does not clear immediately — category ui→functional · conf 0.85
  - Notification badge does not update immediately after reading all items, requiring a page refresh to reflect the correct state.
- **cand-001** (es, r2) Error 500 al pagar el pedido — component checkout→payments · conf 0.95
  - HTTP 500 error blocks payment creation completely across multiple accounts and platforms since last night's deployment. Core checkout flow is non-functional with no workaround.
- **cand-002** (en, r2) checkout broken!!! — component checkout→payments · conf 0.95
  - POST /api/orders returns 500 error preventing all users from placing orders since deployment. Core checkout functionality is completely broken.
- **cand-003** (en, r2) Order confirmation returns HTTP 500 — component checkout→payments · conf 0.95
  - HTTP 500 on Place order prevents order creation across all platforms in production. Core payment/checkout flow is completely blocked with no workaround.
- **cand-028** (es, r2) Imagen de producto pixelada en iPad — severity low→medium · conf 0.85
  - Product images appear pixelated/blurry on iPad Pro, loading thumbnail instead of full resolution; this is a display quality issue that doesn't block functionality.
- **cand-029** (es, r2) fotos borrosas en tablet — severity low→medium · conf 0.82
  - Product images display with poor quality on tablet but work fine on mobile, affecting user experience in the catalog without blocking functionality.
- **cand-035** (en, r2) Password reset email not arriving for Hotmail users — severity medium→high; component notifications→auth · conf 0.90
  - Password reset emails not arriving for Hotmail/Outlook users blocks login recovery for a subset of users; web workaround likely unavailable.
- **cand-036** (en, r2) No reset email (outlook) — severity medium→high; component notifications→auth · conf 0.88
  - Password reset email not received for Outlook user after multiple attempts, preventing account recovery with no workaround on mobile.
- **cand-045** (en, r2) Webhook delivery queue empty for order events — severity high→critical · conf 0.95
  - Webhook dispatcher shows zero deliveries for order.created events since deployment, while other event types work. This is a core API functionality broken after 4.2.0.
- **cand-069** (es, r2) No llega el código de verificación por SMS — component notifications→auth · conf 0.80
  - Two-factor authentication SMS delivery fails, but email verification is available as a workaround. This impacts auth security for affected users.
- **cand-073** (es, r2) El carrito se vacía al cerrar sesión — category data→functional · conf 0.90
  - Cart contents are lost when users log out and back in, affecting all users. This is a functional defect in cart session management.
- **cand-083** (es, r2) Reporte de ventas no incluye pedidos con cupón — severity medium→high · conf 0.90
  - The sales report excludes orders with coupons, causing data inconsistencies with finance records. This is incorrect data in admin reporting.
- **cand-088** (es, r2) El cupón de primera compra se puede usar varias veces — severity medium→high · conf 0.90
  - The first purchase welcome coupon can be used multiple times instead of only once, violating business logic. This is a functional defect in the checkout coupon validation.
- **cand-108** (en, r2) Search shows products that can't ship to the user's region — category data→functional · conf 0.85
  - Search results include unavailable products for the user's region, causing checkout failures. This breaks the search and checkout flow for affected users but has a workaround (manually filtering).
- **cand-116** (en, r2) Admin order list shows times in UTC — severity medium→low; category data→ui · conf 0.82
  - Admin displays order timestamps in UTC instead of local timezone, causing confusion but not blocking operations. Staff can still complete tasks with manual adjustments.
- **cand-118** (en, r2) Order cancellation email not sent — severity medium→high · conf 0.87
  - Cancellation notification email is not sent to customers when support cancels orders. This breaks the notifications workflow.
- **cand-122** (en, r2) API returns 200 with empty body for unknown product — severity medium→high · conf 0.89
  - API returns 200 with empty body for unknown resources instead of proper 404 error, breaking partner error handling and API contract.
- **cand-127** (en, r2) Push shows price in USD instead of MXN — severity medium→low; category data→ui · conf 0.80
  - Push notifications display wrong currency label (USD instead of MXN), confusing users about prices but showing correct amounts.
- **cand-138** (en, r2) API docs example uses an old field name — severity low→medium · conf 0.90
  - API documentation example uses an outdated field name, misleading developers and causing integration issues. This is functional but affects a limited audience.
