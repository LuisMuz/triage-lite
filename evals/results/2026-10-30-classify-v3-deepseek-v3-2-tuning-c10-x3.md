# classify/v3 · deepseek.v3.2 · seed-v1/tuning

Run 2026-10-30T19:23:28+00:00 · repeat 3 · 10 incidents per call · 60 items · 19 calls (12 fresh, 6 cached chunks)

| prompt | model | split | severity macro-F1 [95% CI] | sev acc | comp acc | cat acc | conf≥0.7 acc (share) | valid first try | needs_manual | $/100 | p50 / p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| classify/v3 | deepseek.v3.2 | tuning | **0.635** [0.539-0.730] | 62.8% | 90.0% | 86.1% | 62.8% (100.0%) | 94.4% | 0.0% | $0.029 | 20887 / 31942 |

Language detection accuracy: 100.0%.

## Severity per class

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| critical | 0.79 | 0.70 | 0.74 | 33 |
| high | 0.49 | 0.44 | 0.46 | 48 |
| medium | 0.53 | 0.50 | 0.51 | 54 |
| low | 0.74 | 0.93 | 0.82 | 45 |

## Confusion (rows = gold, columns = predicted)

| gold \ pred | critical | high | medium | low | needs_manual |
|---|---|---|---|---|---|
| critical | 23 | 10 | 0 | 0 | 0 |
| high | 6 | 21 | 21 | 0 | 0 |
| medium | 0 | 12 | 27 | 15 | 0 |
| low | 0 | 0 | 3 | 42 | 0 |

## Calibration (severity correct, by stated confidence)

| confidence | count | mean confidence | accuracy |
|---|---|---|---|
| 0.0-0.2 | 0 | n/a | n/a |
| 0.2-0.4 | 0 | n/a | n/a |
| 0.4-0.6 | 0 | n/a | n/a |
| 0.6-0.8 | 2 | 0.70 | 0.0% |
| 0.8-1.0 | 178 | 0.90 | 63.5% |

## Errors (any label wrong, or needs_manual)

- **cand-001** (es, r0) Error 500 al pagar el pedido — component checkout→payments · conf 1.00
  - Payment flow completely broken with 500 error affecting all users on web and app, no workaround for core e-commerce functionality.
- **cand-002** (en, r0) checkout broken!!! — component checkout→payments · conf 1.00
  - Checkout broken with 500 error on order creation affecting all users since last deployment, preventing any orders from being placed.
- **cand-003** (en, r0) Order confirmation returns HTTP 500 — component checkout→payments · conf 1.00
  - Order confirmation returns HTTP 500 error preventing order creation across all platforms with no workaround found.
- **cand-006** (es, r0) Cobro duplicado con tarjeta — severity critical→high · conf 0.95
  - Multiple customers experiencing duplicate charges for single orders, causing financial harm and requiring manual refunds.
- **cand-007** (en, r0) Customers charged twice for one order — severity critical→high · conf 0.95
  - Payment gateway timeout retry logic causing duplicate charges for customers, requiring manual intervention and financial impact.
- **cand-008** (es, r0) me cobraron 2 veces!! — severity critical→high · conf 0.95
  - Customer charged twice for single order displayed once in system, causing financial loss and customer dissatisfaction.
- **cand-014** (es, r0) Notificación push duplicada — severity medium→low; category functional→ui · conf 0.90
  - Duplicate push notifications for order shipments are annoying but don't block any functionality or cause data issues.
- **cand-015** (en, r0) Duplicate 'order shipped' push — severity medium→low; category functional→ui · conf 0.90
  - Users receive duplicate push notifications for shipped orders, which is a minor annoyance without functional impact.
- **cand-021** (en, r0) App crashes opening order history — severity high→critical · conf 0.90
  - App crashes when accessing order history for users with many orders, blocking access to a core feature without workaround in the app.
- **cand-022** (en, r0) Crash: IndexOutOfBoundsException in OrderAdapter — severity high→critical · conf 1.00
  - IndexOutOfBoundsException crash in OrderAdapter affecting order history screen with 2,310 events, indicating a crash bug that terminates the app.
- **cand-023** (en, r0) order history closes the app — severity high→critical · conf 0.90
  - Order history closes the entire app when opened by user with many orders, representing a crash that blocks access to past orders.
- **cand-032** (es, r0) Búsqueda muy lenta en la app — severity high→medium · conf 0.90
  - Search takes 6-8 seconds to show results on mobile app compared to instant web performance, impacting user experience but search still works.
- **cand-033** (es, r0) buscar tarda muchisimo — severity high→medium · conf 0.85
  - Search operations take excessive time causing user frustration and abandonment, but search functionality still works eventually.
- **cand-034** (es, r0) Latencia alta en /search desde móvil — severity high→medium · conf 1.00
  - Search endpoint used by mobile app has high latency (7.8s p95) compared to web, indicating performance issue affecting core search feature.
- **cand-035** (en, r0) Password reset email not arriving for Hotmail users — severity medium→high; component notifications→auth · conf 0.90
  - Password reset emails not delivered to Hotmail/Outlook users, blocking password recovery for a specific email provider segment.
- **cand-036** (en, r0) No reset email (outlook) — severity medium→high; component notifications→auth · conf 0.90
  - Password reset email not received for Outlook email address, preventing password recovery and blocking account access.
- **cand-060** (es, r0) Pantalla en blanco en el paso de envío — category crash→functional · conf 1.00
  - Checkout shipping step shows blank page with JavaScript error, preventing all purchases across all platforms. This is a critical functional failure blocking the core checkout flow.
- **cand-062** (es, r0) Historial de pedidos vacío después de la migración — severity critical→high · conf 0.95
  - Order history empty for thousands of users after database migration, affecting ability to view past orders. This is a major data loss/display issue affecting the profile component.
- **cand-069** (es, r0) No llega el código de verificación por SMS — severity high→medium; component notifications→auth · conf 0.85
  - Two-factor authentication SMS verification codes are not being delivered, though email alternative works. This is a functional failure in the auth component's notification delivery.
- **cand-071** (es, r0) No acepta tarjetas American Express — severity high→medium · conf 0.90
  - American Express card rejection across all platforms while Visa/Mastercard work. This is a functional payment processing issue affecting a specific card type.
- **cand-073** (es, r0) El carrito se vacía al cerrar sesión — severity high→medium; category data→functional · conf 0.85
  - Cart contents lost when logging out and back in, affecting all users across platforms. This is a functional issue with cart persistence functionality.
- **cand-083** (es, r0) Reporte de ventas no incluye pedidos con cupón — severity medium→high · conf 0.90
  - The admin sales report excludes orders with coupons, causing financial discrepancies and inaccurate reporting.
- **cand-088** (es, r0) El cupón de primera compra se puede usar varias veces — severity medium→high · conf 0.95
  - The welcome coupon meant for first purchases only can be used repeatedly, breaking the intended promotional logic.
- **cand-108** (en, r0) Search shows products that can't ship to the user's region — severity high→medium; category data→functional · conf 0.85
  - Search results display products unavailable for the user's region, leading to checkout failures and poor user experience.
- **cand-116** (en, r0) Admin order list shows times in UTC — severity medium→low; category data→ui · conf 0.85
  - Order times displayed in UTC instead of local Mexico City time causes confusion for staff but doesn't break functionality.
- **cand-127** (en, r0) Push shows price in USD instead of MXN — severity medium→low; category data→ui · conf 0.85
  - Push notifications show USD currency label for MXN amounts, causing confusion but not preventing functionality.
- **hand-010** (en, r0) Unread notification badge does not clear immediately — category ui→functional · conf 0.85
  - Unread notification badge doesn't update immediately after reading notifications, requiring page refresh to clear visual indicator.
- **cand-001** (es, r1) Error 500 al pagar el pedido — component checkout→payments · conf 0.95
  - Error 500 prevents any orders from being created after clicking 'Pagar ahora', affecting all users on web and mobile with no workaround. This is a complete outage of the core checkout/payment flow.
- **cand-002** (en, r1) checkout broken!!! — component checkout→payments · conf 0.95
  - POST /api/orders returns HTTP 500 error, preventing order creation for all users since last deploy. This is a complete outage of the core checkout flow with no workaround.
- **cand-003** (en, r1) Order confirmation returns HTTP 500 — component checkout→payments · conf 0.95
  - Clicking 'Place order' returns HTTP 500 and no order is created, affecting all platforms in production with no workaround. This is a full outage of the core checkout flow.
- **cand-006** (es, r1) Cobro duplicado con tarjeta — category data→functional · conf 0.90
  - Multiple customers are being charged twice for single orders with Mastercard, requiring manual refunds. This is a serious payment processing defect affecting financial transactions.
- **cand-007** (en, r1) Customers charged twice for one order — category data→functional · conf 0.90
  - 14+ customers charged twice for single orders due to payment confirm retries after gateway timeouts. This is a serious payment processing issue causing financial harm to customers.
- **cand-008** (es, r1) me cobraron 2 veces!! — category data→functional · conf 0.90
  - Customer charged twice for a single 899 peso order, experiencing financial impact. This is part of the wider duplicate payments issue affecting multiple customers.
- **cand-014** (es, r1) Notificación push duplicada — severity medium→low · conf 0.80
  - Users receive duplicate 'order shipped' push notifications for every shipment. This is a duplicate notification issue that doesn't block core functionality.
- **cand-015** (en, r1) Duplicate 'order shipped' push — severity medium→low · conf 0.80
  - Duplicate 'order shipped' push notifications are sent for every shipment, but this doesn't affect core functionality or cause data loss.
- **cand-028** (es, r1) Imagen de producto pixelada en iPad — severity low→medium · conf 0.85
  - Product images appear blurry/pixelated on iPad Pro, suggesting the thumbnail is being loaded instead of the high-resolution image. This is a UI/display issue affecting image quality.
- **cand-029** (es, r1) fotos borrosas en tablet — severity low→medium · conf 0.80
  - Product images have very poor quality on tablets while looking fine on phones. This is a display/rendering issue specific to tablet devices.
- **cand-032** (es, r1) Búsqueda muy lenta en la app — severity high→medium · conf 0.90
  - Search takes 6-8 seconds to show results in the mobile app over 4G, while being instant on the web. This is a performance issue affecting search responsiveness.
- **cand-033** (es, r1) buscar tarda muchisimo — severity high→medium · conf 0.85
  - Search takes a long time to load in the app, causing user frustration and abandonment, while the web version is fast. This is a performance problem with search.
- **cand-034** (es, r1) Latencia alta en /search desde móvil — severity high→medium · conf 0.95
  - The search endpoint used by the mobile app has high latency (7.8s p95) compared to the web endpoint (300ms), indicating the app isn't using the new index. This is a performance issue.
- **cand-035** (en, r1) Password reset email not arriving for Hotmail users — severity medium→high; component notifications→auth · conf 0.90
  - Password reset emails are not being delivered to Hotmail and Outlook users while working for Gmail users. This is a functional issue preventing password resets for specific email domains.
- **cand-036** (en, r1) No reset email (outlook) — severity medium→high; component notifications→auth · conf 0.85
  - Password reset emails are not received by Outlook users despite multiple attempts, and the emails aren't in spam. This prevents password reset functionality for these users.
- **cand-042** (es, r1) Se repiten mis direcciones — severity medium→low · conf 0.80
  - Address appears duplicated multiple times after editing, causing data inconsistency in the profile.
- **cand-068** (es, r1) Precio en la app distinto al de la web — severity high→medium; category data→functional · conf 0.85
  - App shows lower outdated prices than web, but charges higher web prices at payment, causing functional inconsistency and customer complaints.
- **cand-069** (es, r1) No llega el código de verificación por SMS — severity high→medium; component notifications→auth · conf 0.80
  - Two-factor verification SMS codes are not being delivered, though email alternative still works as a workaround.
- **cand-071** (es, r1) No acepta tarjetas American Express — severity high→medium · conf 0.90
  - American Express cards are rejected as invalid while Visa/Mastercard work, blocking payment method for affected customers.
- **cand-073** (es, r1) El carrito se vacía al cerrar sesión — severity high→medium; category data→functional · conf 0.85
  - Shopping cart empties when logging out and logging back in, affecting all users and forcing them to re-add items.
- **cand-083** (es, r1) Reporte de ventas no incluye pedidos con cupón — severity medium→high · conf 0.85
  - Sales report excludes orders with coupons, causing financial discrepancies - this is a data issue affecting reporting accuracy.
- **cand-088** (es, r1) El cupón de primera compra se puede usar varias veces — severity medium→high · conf 0.80
  - Welcome coupon intended for first purchase only can be used multiple times, violating business rules for discounts.
- **cand-108** (en, r1) Search shows products that can't ship to the user's region — severity high→medium; category data→functional · conf 0.85
  - Search showing products that cannot be shipped to user's region wastes user time and leads to checkout failures, affecting core search functionality.
- **cand-116** (en, r1) Admin order list shows times in UTC — severity medium→low; category data→ui · conf 0.80
  - Time display shows UTC instead of local time zone, causing confusion for staff but not blocking functionality.
- **cand-124** (en, r1) Autocomplete lags on older iPhones — severity medium→low · conf 0.80
  - Search autocomplete lag on older devices affects usability but doesn't break functionality.
- **cand-127** (en, r1) Push shows price in USD instead of MXN — severity medium→low; category data→ui · conf 0.85
  - Push notifications showing incorrect currency labels but correct amounts represents a display/translation issue.
- **cand-001** (es, r2) Error 500 al pagar el pedido — component checkout→payments · conf 1.00
  - Payment flow returns 500 error preventing all users from placing orders since deployment, with no workaround available. This is a complete outage of the payment/checkout core flow.
- **cand-002** (en, r2) checkout broken!!! — component checkout→payments · conf 1.00
  - Payment flow broken with 500 error for all users since last deploy, preventing order creation. This is a complete outage of the checkout/payment core flow.
- **cand-003** (en, r2) Order confirmation returns HTTP 500 — component checkout→payments · conf 1.00
  - Order placement returns HTTP 500 error preventing order creation across all platforms with no workaround. This is a complete outage of the payment/checkout core flow.
- **cand-006** (es, r2) Cobro duplicado con tarjeta — severity critical→high; category data→functional · conf 0.90
  - Customers are being charged twice for single orders when using Mastercard, requiring manual refunds. This is a payment processing defect causing financial harm to users.
- **cand-007** (en, r2) Customers charged twice for one order — severity critical→high; category data→functional · conf 0.90
  - Multiple customers charged twice for single orders due to payment confirm retries after gateway timeouts. This is a payment processing defect causing financial impact.
- **cand-008** (es, r2) me cobraron 2 veces!! — severity critical→high; category data→functional · conf 0.80
  - Customer was charged twice for a single order, causing financial impact. This is a payment processing defect affecting user funds.
- **cand-014** (es, r2) Notificación push duplicada — severity medium→low; category functional→ui · conf 0.70
  - Users receive duplicate push notifications for order shipments. This is a notification delivery issue but doesn't prevent core functionality.
- **cand-015** (en, r2) Duplicate 'order shipped' push — severity medium→low; category functional→ui · conf 0.70
  - Duplicate push notifications are sent for shipments, causing minor user annoyance but not blocking functionality.
- **cand-021** (en, r2) App crashes opening order history — severity high→critical · conf 0.90
  - The app crashes when opening order history for users with many orders, preventing access to a core feature without workaround.
- **cand-022** (en, r2) Crash: IndexOutOfBoundsException in OrderAdapter — severity high→critical · conf 0.95
  - IndexOutOfBoundsException causes app crashes specifically on order history screen, affecting users with many orders.
- **cand-023** (en, r2) order history closes the app — severity high→critical · conf 0.90
  - Order history crashes the entire app for users with many orders, blocking access to order information.
- **cand-032** (es, r2) Búsqueda muy lenta en la app — severity high→medium · conf 0.90
  - Search takes 6-8 seconds on mobile app compared to instant web performance, indicating a performance issue.
- **cand-033** (es, r2) buscar tarda muchisimo — severity high→medium · conf 0.90
  - Search functionality has excessive loading times causing user frustration and abandonment.
- **cand-034** (es, r2) Latencia alta en /search desde móvil — severity high→medium · conf 0.95
  - High latency (7.8s p95) in search endpoint used by mobile app compared to web, indicating backend performance issue.
- **cand-035** (en, r2) Password reset email not arriving for Hotmail users — severity medium→high; component notifications→auth · conf 0.90
  - Password reset emails not delivered to Hotmail/Outlook users, blocking account recovery for specific email providers.
- **cand-036** (en, r2) No reset email (outlook) — severity medium→high; component notifications→auth · conf 0.90
  - Password reset email not received by Outlook user despite multiple attempts, preventing account access recovery.
- **cand-062** (es, r2) Historial de pedidos vacío después de la migración — severity critical→high · conf 0.85
  - Order history empty for thousands of users after database migration, affecting both users and support staff.
- **cand-069** (es, r2) No llega el código de verificación por SMS — severity high→medium; component notifications→auth · conf 0.80
  - SMS verification codes not delivered but email alternative works, affecting 2FA for some users.
- **cand-071** (es, r2) No acepta tarjetas American Express — severity high→medium · conf 0.85
  - American Express cards rejected across all platforms while other card types work, limiting payment options.
- **cand-073** (es, r2) El carrito se vacía al cerrar sesión — category data→functional · conf 0.90
  - Cart empties when users log out and back in, forcing them to rebuild carts across all platforms.
- **cand-083** (es, r2) Reporte de ventas no incluye pedidos con cupón — severity medium→high · conf 0.90
  - Monthly sales reports exclude orders with coupons, causing financial discrepancies - this is a data accuracy issue in admin reporting.
- **cand-088** (es, r2) El cupón de primera compra se puede usar varias veces — severity medium→high · conf 0.95
  - Welcome coupon intended for first purchase only can be reused multiple times - this is a functional defect in coupon validation logic.
- **cand-101** (en, r2) User sees another customer's cart — severity critical→high · conf 0.90
  - Customers seeing each other's cart and address data due to CDN caching is a data exposure issue affecting user privacy.
- **cand-108** (en, r2) Search shows products that can't ship to the user's region — severity high→medium; category data→functional · conf 0.85
  - Search showing products unavailable in user's region leads to checkout failures, representing incorrect product filtering.
- **cand-116** (en, r2) Admin order list shows times in UTC — severity medium→low; category data→ui · conf 0.85
  - Time display shows UTC instead of local timezone, representing incorrect data formatting but not breaking core functionality.
- **cand-124** (en, r2) Autocomplete lags on older iPhones — severity medium→low · conf 0.80
  - Search autocomplete lag on older devices represents performance degradation but search still works.
- **cand-127** (en, r2) Push shows price in USD instead of MXN — severity medium→low · conf 0.85
  - Push notifications show incorrect currency label (USD instead of MXN), representing incorrect data formatting.
- **cand-138** (en, r2) API docs example uses an old field name — severity low→medium · conf 0.90
  - API documentation has incorrect field name which could cause integration errors, affecting developers but not end users.
- **hand-003** (en, r2) Read-only staff account can export customer data — severity critical→high · conf 0.95
  - Read-only staff accounts can export sensitive customer data including emails and phone numbers, which is a security authorization failure.
- **hand-010** (en, r2) Unread notification badge does not clear immediately — category ui→functional · conf 0.85
  - Notification badge doesn't clear immediately after reading notifications, requiring page refresh, which is a data synchronization/user interface issue.
