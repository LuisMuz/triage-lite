# classify/v3 · moonshotai.kimi-k2.5 · seed-v1/tuning

Run 2026-10-30T19:08:15+00:00 · repeat 3 · 10 incidents per call · 60 items · 19 calls (13 fresh, 6 cached chunks)

| prompt | model | split | severity macro-F1 [95% CI] | sev acc | comp acc | cat acc | conf≥0.7 acc (share) | valid first try | needs_manual | $/100 | p50 / p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| classify/v3 | moonshotai.kimi-k2.5 | tuning | **0.748** [0.657-0.825] | 74.4% | 95.6% | 86.1% | 74.4% (100.0%) | 100.0% | 0.0% | $0.032 | 5988 / 10085 |

Language detection accuracy: 100.0%.

## Severity per class

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| critical | 0.92 | 0.67 | 0.77 | 33 |
| high | 0.63 | 0.79 | 0.70 | 48 |
| medium | 0.74 | 0.59 | 0.66 | 54 |
| low | 0.79 | 0.93 | 0.86 | 45 |

## Confusion (rows = gold, columns = predicted)

| gold \ pred | critical | high | medium | low | needs_manual |
|---|---|---|---|---|---|
| critical | 22 | 11 | 0 | 0 | 0 |
| high | 2 | 38 | 8 | 0 | 0 |
| medium | 0 | 11 | 32 | 11 | 0 |
| low | 0 | 0 | 3 | 42 | 0 |

## Calibration (severity correct, by stated confidence)

| confidence | count | mean confidence | accuracy |
|---|---|---|---|
| 0.0-0.2 | 0 | n/a | n/a |
| 0.2-0.4 | 0 | n/a | n/a |
| 0.4-0.6 | 0 | n/a | n/a |
| 0.6-0.8 | 0 | n/a | n/a |
| 0.8-1.0 | 180 | 0.91 | 74.4% |

## Errors (any label wrong, or needs_manual)

- **cand-001** (es, r0) Error 500 al pagar el pedido — component checkout→payments · conf 0.95
  - A 500 error occurs at the moment of payment in production, preventing all users from completing orders. This is a full outage of the core checkout/payment flow with no workaround.
- **cand-002** (en, r0) checkout broken!!! — component checkout→payments · conf 0.95
  - Production shows a 500 error when placing orders affecting all users since the last deploy. The payment/checkout flow is completely blocked with no workaround.
- **cand-003** (en, r0) Order confirmation returns HTTP 500 — component checkout→payments · conf 0.95
  - Returns HTTP 500 when placing orders in production on all platforms. This is a full outage of the core payment flow with no workaround.
- **cand-006** (es, r0) Cobro duplicado con tarjeta — severity critical→high; category data→functional · conf 0.90
  - Customers are being charged twice for the same order due to a retry mechanism issue during gateway timeouts. This is incorrect payment behavior affecting multiple customers.
- **cand-007** (en, r0) Customers charged twice for one order — severity critical→high; category data→functional · conf 0.90
  - Duplicate captures on card payments due to retry logic after gateway timeouts. The system creates only one order but captures the payment twice. This is incorrect payment behavior with financial impact.
- **cand-008** (es, r0) me cobraron 2 veces!! — severity critical→high; category data→functional · conf 0.90
  - Customer reports being charged twice for a single order. This is a duplicate payment issue affecting customers financially, part of the same root cause as similar reports.
- **cand-068** (es, r0) Precio en la app distinto al de la web — severity high→medium · conf 0.85
  - Product prices displayed in the app differ from the web, showing old/stale prices. The catalog pricing system is not syncing correctly between platforms, leading to customer confusion even though checkout uses the correct price.
- **cand-069** (es, r0) No llega el código de verificación por SMS — severity high→medium · conf 0.85
  - Two-factor authentication SMS codes are not being delivered, but users have a workaround via email. This is a partial outage in the notification system affecting a subset of users (those with MFA enabled).
- **cand-073** (es, r0) El carrito se vacía al cerrar sesión — category data→functional · conf 0.85
  - The cart clears when logging out and back in for all users. This suggests cart data is tied to session rather than persisting to the user account, or session persistence is broken in the cart component.
- **cand-079** (es, r0) Imágenes de productos tardan mucho en 3G — severity medium→high · conf 0.90
  - Product images are loading too slowly on 3G connections, taking over 10 seconds. This is a performance/speed issue affecting user experience.
- **cand-083** (es, r0) Reporte de ventas no incluye pedidos con cupón — severity medium→high · conf 0.95
  - The monthly sales report in admin is excluding orders that used coupons, causing financial totals to be incorrect. This is a data accuracy issue.
- **cand-088** (es, r0) El cupón de primera compra se puede usar varias veces — severity medium→high · conf 0.95
  - The first-purchase-only coupon (BIENVENIDA) can be used multiple times instead of being restricted to the first order. This is a functional error in coupon validation logic.
- **cand-101** (en, r0) User sees another customer's cart — severity critical→high · conf 0.90
  - Users seeing each other's cart items and addresses due to CDN caching is a data exposure issue. This is a security problem where sensitive data crosses user boundaries, though it only affects users behind the same corporate proxy.
- **cand-108** (en, r0) Search shows products that can't ship to the user's region — severity high→medium; category data→functional · conf 0.85
  - Search is returning products that users cannot actually purchase due to regional restrictions. This is a functional issue where search isn't respecting region filters, causing frustration at checkout for many Mexican users.
- **cand-113** (en, r0) Can't change account email — severity medium→low · conf 0.90
  - The email update appears to save but doesn't actually persist. This is a functional bug where profile updates aren't being stored, affecting a single user's ability to change their contact info.
- **cand-116** (en, r0) Admin order list shows times in UTC — severity medium→low; category data→ui · conf 0.95
  - Order times display in UTC instead of local time in the admin panel. This is a UI/timing display issue that causes confusion but doesn't block functionality.
- **cand-127** (en, r0) Push shows price in USD instead of MXN — severity medium→low; category data→ui · conf 0.90
  - Push notifications show incorrect currency labels (USD instead of MXN). This is a display/UI issue in notifications - the amounts are correct but mislabeled, causing confusion but not blocking functionality.
- **cand-138** (en, r0) API docs example uses an old field name — severity low→medium; category functional→ui · conf 0.80
  - Documentation error that could cause integration issues for developers. The API itself works correctly, but the docs are misleading.
- **hand-003** (en, r0) Read-only staff account can export customer data — severity critical→high · conf 0.95
  - Authorization failure allowing unauthorized data export. Read-only accounts should not be able to export sensitive customer data including PII.
- **hand-007** (en, r0) Expired saved card is accepted until final payment — severity high→medium; component payments→checkout · conf 0.90
  - The payment flow accepts an expired card at selection time and only fails at the final step. This is a functional validation issue in the checkout flow that causes poor UX.
- **hand-010** (en, r0) Unread notification badge does not clear immediately — category ui→functional · conf 0.85
  - UI state synchronization issue where the notification badge doesn't update until page refresh. Functional issue where the notification system doesn't behave as expected.
- **cand-001** (es, r1) Error 500 al pagar el pedido — component checkout→payments · conf 0.95
  - HTTP 500 error prevents order creation entirely, affecting all users across web and app since the release. This is a complete outage of the payment/checkout flow with no workaround.
- **cand-002** (en, r1) checkout broken!!! — component checkout→payments · conf 0.95
  - All users cannot place orders due to 500 error on POST /api/orders since last night's deploy. This is a complete outage of the checkout flow with no workaround.
- **cand-003** (en, r1) Order confirmation returns HTTP 500 — component checkout→payments · conf 0.95
  - Order creation fails with HTTP 500 across all platforms in production. The entire checkout flow is broken for all users since release 4.2.0 with no workaround available.
- **cand-006** (es, r1) Cobro duplicado con tarjeta — severity critical→high · conf 0.90
  - Multiple customers are being charged twice for a single order while only one order is created in the system. This is duplicate payment processing affecting multiple users.
- **cand-007** (en, r1) Customers charged twice for one order — severity critical→high; category data→functional · conf 0.90
  - Payment system is retrying and capturing payments twice after gateway timeouts, resulting in duplicate charges. Affects multiple customers but orders are still being created correctly.
- **cand-008** (es, r1) me cobraron 2 veces!! — severity critical→high · conf 0.85
  - Individual user report of duplicate charge on their card for a single order amount. This is a single occurrence of the duplicate payment issue others are reporting.
- **cand-028** (es, r1) Imagen de producto pixelada en iPad — severity low→medium · conf 0.85
  - Product images appear blurry/pixelated on iPad because the app is loading thumbnails instead of full-resolution images. This is a layout/styling problem with the image display.
- **cand-029** (es, r1) fotos borrosas en tablet — severity low→medium · conf 0.85
  - Same as inc-0014 - product images display with poor quality on tablet devices. This is a UI/display issue related to image resolution selection.
- **cand-032** (es, r1) Búsqueda muy lenta en la app — severity high→medium · conf 0.90
  - Search functionality is working but takes 6-8 seconds to return results on mobile app with 4G, while the web is instant. This is a performance degradation specific to the app.
- **cand-033** (es, r1) buscar tarda muchisimo — severity high→medium · conf 0.90
  - Same performance issue as inc-0016 - search takes a long time loading in the app compared to web. The feature works but is prohibitively slow, causing user abandonment.
- **cand-068** (es, r1) Precio en la app distinto al de la web — severity high→medium · conf 0.85
  - Price displayed on the app differs from web, causing customer confusion and complaints. Payment uses the correct price, so the issue is in how prices are displayed/catalogued in the app.
- **cand-073** (es, r1) El carrito se vacía al cerrar sesión — category data→functional · conf 0.85
  - Cart contents are lost upon logout and re-login, forcing users to re-add items. This affects the cart persistence functionality.
- **cand-077** (es, r1) No se ve la tabla de tallas en móvil — severity medium→low · conf 0.90
  - The size chart is not displaying on mobile web, which is a layout/styling issue that prevents some content from showing. This is a UI problem on the product page.
- **cand-083** (es, r1) Reporte de ventas no incluye pedidos con cupón — severity medium→high · conf 0.95
  - The sales report in admin is not including orders with coupon codes, causing incorrect totals. This is a data accuracy issue in the reporting system.
- **cand-088** (es, r1) El cupón de primera compra se puede usar varias veces — severity medium→high · conf 0.90
  - The first-time purchase coupon can be used multiple times instead of only once. This is a functional bug in the checkout/cart validation logic.
- **cand-101** (en, r1) User sees another customer's cart — category security→data · conf 0.90
  - Users seeing other customers' carts and addresses is a severe data leakage issue, likely CDN misconfiguration caching personal data. This is critical data/privacy exposure in the cart component.
- **cand-108** (en, r1) Search shows products that can't ship to the user's region — category data→functional · conf 0.85
  - Search returns products that aren't available for the user's region, which is incorrect functional behavior. Users discover this at checkout, so it affects the core search flow but has a workaround.
- **cand-113** (en, r1) Can't change account email — category functional→data · conf 0.85
  - Profile email change shows success but doesn't persist the new value. This is a functional data issue that fails to save user information correctly.
- **cand-116** (en, r1) Admin order list shows times in UTC — severity medium→low; category data→ui · conf 0.90
  - Admin times display in UTC instead of local timezone, causing confusion for staff. This is purely a display/formatting issue with correct underlying data.
- **cand-127** (en, r1) Push shows price in USD instead of MXN — severity medium→low; category data→ui · conf 0.90
  - Push notification shows incorrect currency label (USD instead of MXN). The amounts are correct but the text label is wrong, making this a UI/display issue.
- **cand-138** (en, r1) API docs example uses an old field name — category functional→ui · conf 0.95
  - API documentation using an outdated field name causes confusion for developers but the actual API works as expected with the correct field name.
- **hand-006** (en, r1) Category page takes over ten seconds to load — severity medium→high · conf 0.90
  - Category page taking 10+ seconds to load on first visit is a performance issue. The page eventually loads, so it's not a crash, but the delay is significant.
- **cand-006** (es, r2) Cobro duplicado con tarjeta — severity critical→high; category data→functional · conf 0.90
  - Customers are being double-charged for single orders due to a payment processing issue. This is a functional defect in payments causing financial harm requiring manual refunds.
- **cand-007** (en, r2) Customers charged twice for one order — severity critical→high; category data→functional · conf 0.90
  - Payment confirm call retry logic is causing double charges for card payments after gateway timeouts. This is a functional defect in the payment service affecting multiple customers.
- **cand-008** (es, r2) me cobraron 2 veces!! — severity critical→high; category data→functional · conf 0.90
  - Customer was charged twice for a single order. Same underlying issue as inc-0004/inc-0005 - duplicate charges in payment processing causing financial harm.
- **cand-014** (es, r2) Notificación push duplicada — severity medium→low · conf 0.80
  - Users receive duplicate push notifications for shipment events. This is a non-critical issue where notifications work but are sent twice - cosmetic/duplication issue.
- **cand-015** (en, r2) Duplicate 'order shipped' push — severity medium→low · conf 0.80
  - Duplicate push notifications sent for every shipment is a functional issue with the notification system, but doesn't block core functionality - users are informed, just twice.
- **cand-022** (en, r2) Crash: IndexOutOfBoundsException in OrderAdapter — severity high→critical · conf 0.95
  - Multiple crash reports with IndexOutOfBoundsException in OrderAdapter, affecting many users (2,310 events in 24h). This is a technical crash in the order history view.
- **cand-034** (es, r2) Latencia alta en /search desde móvil — severity high→critical · conf 0.95
  - Technical root cause identified: mobile app search endpoint has high latency (7.8s p95 vs 300ms for web) because it's not using the new index. This is a performance issue in the search API.
- **cand-035** (en, r2) Password reset email not arriving for Hotmail users — severity medium→high · conf 0.90
  - Password reset emails not delivering to Hotmail/Outlook users, while Gmail works fine. This is a delivery failure affecting a subset of users.
- **cand-036** (en, r2) No reset email (outlook) — severity medium→high · conf 0.90
  - Same issue: Outlook user unable to receive password reset emails. Confirms the email delivery problem is affecting auth flows.
- **cand-069** (es, r2) No llega el código de verificación por SMS — component notifications→auth · conf 0.85
  - SMS 2FA codes are not being delivered, though email is available as a workaround. Affects authentication but has an alternative path.
- **cand-073** (es, r2) El carrito se vacía al cerrar sesión — category data→functional · conf 0.90
  - Cart contents are not persisted after logout/login. The cart should maintain items across sessions but currently loses them. This breaks expected cart functionality for all users.
- **cand-077** (es, r2) No se ve la tabla de tallas en móvil — severity medium→low · conf 0.95
  - The size chart is missing on mobile product pages but works on desktop. This is a display/layout issue specific to mobile.
- **cand-083** (es, r2) Reporte de ventas no incluye pedidos con cupón — severity medium→high · conf 0.90
  - The sales report in admin is displaying wrong data - it's missing coupon orders, causing totals to be incorrect. This is data integrity/accuracy issue in the reporting.
- **cand-088** (es, r2) El cupón de primera compra se puede usar varias veces — severity medium→high · conf 0.95
  - The first-purchase only coupon can be used multiple times, bypassing the business rule. This is a functional defect in the coupon validation logic.
- **cand-108** (en, r2) Search shows products that can't ship to the user's region — category data→functional · conf 0.85
  - Search results incorrectly include products that can't be purchased by the user region. This is a functional bug in the search system filtering logic, not a checkout issue.
- **cand-116** (en, r2) Admin order list shows times in UTC — severity medium→low; category data→ui · conf 0.90
  - Admin order times display in UTC instead of local timezone. This is a UI/data presentation issue with timezone formatting.
- **cand-127** (en, r2) Push shows price in USD instead of MXN — severity medium→low; category data→ui · conf 0.90
  - Push notifications display wrong currency label (USD instead of MXN). This is a UI/text issue in the notification content.
- **cand-138** (en, r2) API docs example uses an old field name — category functional→ui · conf 0.90
  - The documentation has an incorrect example that could mislead developers, but the actual API behavior is correct. This is a documentation issue, not a functional bug.
- **hand-006** (en, r2) Category page takes over ten seconds to load — severity medium→high · conf 0.90
  - The category page loads extremely slowly (10+ seconds), which is a performance issue affecting user experience. However, it's not crash-blocking since the page eventually loads.
- **hand-007** (en, r2) Expired saved card is accepted until final payment — severity high→medium · conf 0.92
  - The checkout flow allows selection of an expired card and fails late with a generic error. This is a functional issue where the system does the wrong thing by not validating the card expiration before attempting payment.
