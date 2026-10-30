# classify/v3 · global.anthropic.claude-haiku-4-5-20251001-v1:0 · seed-v1/tuning

Run 2026-10-30T05:02:16+00:00 · repeat 3 · 5 incidents per call · 60 items · 40 calls (40 fresh, 0 cached chunks)

| prompt | model | split | severity macro-F1 [95% CI] | sev acc | comp acc | cat acc | conf≥0.7 acc (share) | valid first try | needs_manual | $/100 | p50 / p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| classify/v3 | global.anthropic.claude-haiku-4-5-20251001-v1:0 | tuning | **0.726** [0.628-0.805] | 70.6% | 91.1% | 88.9% | 72.6% (97.2%) | 91.9% | 2.8% | $0.105 | 2778 / 3192 |

Language detection accuracy: 100.0%.

## Severity per class

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| critical | 0.78 | 0.97 | 0.86 | 33 |
| high | 0.61 | 0.77 | 0.68 | 48 |
| medium | 0.69 | 0.44 | 0.54 | 54 |
| low | 0.89 | 0.76 | 0.82 | 45 |

## Confusion (rows = gold, columns = predicted)

| gold \ pred | critical | high | medium | low | needs_manual |
|---|---|---|---|---|---|
| critical | 32 | 0 | 0 | 0 | 1 |
| high | 9 | 37 | 2 | 0 | 0 |
| medium | 0 | 24 | 24 | 4 | 2 |
| low | 0 | 0 | 9 | 34 | 2 |

## Calibration (severity correct, by stated confidence)

| confidence | count | mean confidence | accuracy |
|---|---|---|---|
| 0.0-0.2 | 0 | n/a | n/a |
| 0.2-0.4 | 0 | n/a | n/a |
| 0.4-0.6 | 0 | n/a | n/a |
| 0.6-0.8 | 0 | n/a | n/a |
| 0.8-1.0 | 175 | 0.90 | 72.6% |

## Errors (any label wrong, or needs_manual)

- **cand-021** (en, r0) App crashes opening order history — severity high→critical · conf 0.95
  - The app crashes immediately when opening the order history with more than 100 orders, making this core profile feature completely inaccessible for affected users with no workaround.
- **cand-022** (en, r0) Crash: IndexOutOfBoundsException in OrderAdapter — severity high→critical · conf 0.98
  - IndexOutOfBoundsException in OrderAdapter is causing app crashes on the order history screen with 2,310 events in 24 hours, indicating a widespread crash affecting many users.
- **cand-023** (en, r0) order history closes the app — severity high→critical · conf 0.95
  - Order history crashes the entire app for users with many orders, blocking access to a core feature; web version works fine confirming it's an app-specific issue.
- **cand-028** (es, r0) Imagen de producto pixelada en iPad — severity low→medium · conf 0.85
  - Product images appear blurry on iPad, loading thumbnails instead of high-resolution versions; this is a display quality issue affecting the catalog experience on tablet devices.
- **cand-029** (es, r0) fotos borrosas en tablet — severity low→medium · conf 0.80
  - Product images display with poor quality on tablets while appearing fine on phones, indicating a responsive design or image scaling issue in the catalog component.
- **cand-035** (en, r0) Password reset email not arriving for Hotmail users — severity medium→high; component notifications→auth · conf 0.80
  - Password reset emails are not being delivered to Hotmail and Outlook users, blocking account recovery for a subset of users; a workaround may exist (contacting support).
- **cand-036** (en, r0) No reset email (outlook) — severity medium→high; component notifications→auth · conf 0.80
  - User cannot receive password reset emails on Outlook account despite multiple attempts and checking spam, indicating a delivery issue affecting account recovery.
- **cand-041** (es, r0) Direcciones guardadas se duplican al editar — severity medium→high · conf 0.90
  - Edited addresses are duplicated instead of updated, creating multiple copies of the same address. This is a data integrity issue in the profile/addresses system.
- **cand-042** (es, r0) Se repiten mis direcciones — severity medium→high · conf 0.90
  - User reports duplicate addresses appearing in their profile after attempting to edit an address. This is the same data duplication issue as inc-0021, affecting multiple users.
- **cand-044** (en, r0) Partner reports missing webhooks — severity high→critical · conf 0.85
  - Partner reports missing webhook deliveries for new-order events for 2 days, forcing them to poll instead. This breaks the partner integration and impacts order processing.
- **cand-045** (en, r0) Webhook delivery queue empty for order events — severity high→critical · conf 0.90
  - Webhook dispatcher shows zero deliveries for order.created events since deploy 4.2.0, while other event types work. This is a critical defect in webhook delivery affecting order notifications.
- **cand-069** (es, r0) No llega el código de verificación por SMS — severity high→medium; component notifications→auth · conf 0.85
  - SMS verification codes fail to deliver, but users have an alternative workaround by receiving the code via email instead. This is a non-core authentication method with a fallback available.
- **cand-073** (es, r0) El carrito se vacía al cerrar sesión — category data→functional · conf 0.88
  - Cart contents are lost when users log out and back in, affecting all users. This breaks a core checkout flow and requires manual workaround (re-adding items).
- **cand-083** (es, r0) Reporte de ventas no incluye pedidos con cupón — severity medium→high · conf 0.95
  - Monthly sales reports exclude orders with coupons, causing financial discrepancies. This is a data accuracy issue in the admin reporting system.
- **cand-088** (es, r0) El cupón de primera compra se puede usar varias veces — severity medium→high · conf 0.85
  - The first-purchase coupon BIENVENIDA can be reused on multiple orders, violating its intended single-use policy. This is a functional defect in the checkout/payments coupon validation logic.
- **cand-113** (en, r0) Can't change account email — category functional→data · conf 0.88
  - Email change in the profile appears to save but the old email persists, indicating a functional defect in the update logic. This is a data consistency issue affecting a non-core feature.
- **cand-116** (en, r0) Admin order list shows times in UTC — category data→ui · conf 0.85
  - Admin staff cannot correctly identify order dates because times are displayed in UTC instead of the expected Mexico City timezone, causing confusion about order timing.
- **cand-118** (en, r0) Order cancellation email not sent — severity medium→high · conf 0.90
  - Cancellation notifications fail to reach customers when orders are cancelled, breaking a critical communication flow for order lifecycle management.
- **cand-122** (en, r0) API returns 200 with empty body for unknown product — severity medium→high · conf 0.92
  - API returns incorrect HTTP status code (200 instead of 404) for nonexistent products, violating REST conventions and causing partners' error handling to fail.
- **cand-138** (en, r0) API docs example uses an old field name — severity low→medium; category functional→ui · conf 0.85
  - API documentation example shows incorrect field name ('qty' vs 'quantity'), which misleads developers and may cause integration failures.
- **cand-001** (es, r1) Error 500 al pagar el pedido — component checkout→payments · conf 0.95
  - Checkout payment flow completely broken across web and app since last deploy; users get error 500 when attempting to place orders with no workaround available.
- **cand-002** (en, r1) checkout broken!!! — component checkout→payments · conf 0.95
  - POST /api/orders endpoint returns 500 error preventing any orders from being placed across all users since last deploy; core checkout flow is completely broken.
- **cand-003** (en, r1) Order confirmation returns HTTP 500 — component checkout→payments · conf 0.95
  - Place order button returns HTTP 500 and no orders are created across all platforms after release 4.2.0; full outage of checkout payment with no workaround.
- **cand-008** (es, r1) me cobraron 2 veces!! — severity critical→none; category data→none; component payments→none · conf n/a
  - model output failed validation twice (schema)
- **cand-014** (es, r1) Notificación push duplicada — severity medium→none; category functional→none; component notifications→none · conf n/a
  - model output failed validation twice (schema)
- **cand-015** (en, r1) Duplicate 'order shipped' push — severity medium→none; category functional→none; component notifications→none · conf n/a
  - model output failed validation twice (schema)
- **cand-019** (es, r1) Botón Guardar aparece en inglés — severity low→none; category ui→none; component profile→none · conf n/a
  - model output failed validation twice (schema)
- **cand-020** (en, r1) Untranslated 'Save' button on Spanish profile page — severity low→none; category ui→none; component profile→none · conf n/a
  - model output failed validation twice (schema)
- **cand-028** (es, r1) Imagen de producto pixelada en iPad — severity low→medium · conf 0.85
  - Product images appear pixelated/blurry on iPad, suggesting the wrong resolution is being loaded. This is a UI/display issue in the catalog affecting tablet users.
- **cand-029** (es, r1) fotos borrosas en tablet — severity low→medium · conf 0.88
  - Product images show poor quality on tablets but display correctly on mobile phones. This is a UI/display issue specific to tablet screen sizes affecting the catalog.
- **cand-035** (en, r1) Password reset email not arriving for Hotmail users — severity medium→high · conf 0.85
  - Password reset emails fail to deliver for Hotmail/Outlook users but work for Gmail, affecting the auth flow for a specific subset of users with no clear workaround.
- **cand-036** (en, r1) No reset email (outlook) — severity medium→high · conf 0.80
  - Outlook user unable to receive password reset email despite multiple attempts, blocking the password reset flow for that account.
- **cand-041** (es, r1) Direcciones guardadas se duplican al editar — severity medium→high · conf 0.85
  - Edited addresses are being duplicated instead of updated, causing data integrity issues. Multiple copies of the same address accumulate in the profile.
- **cand-042** (es, r1) Se repiten mis direcciones — severity medium→high · conf 0.90
  - Duplicate addresses appear in user profile after editing, consistent with inc-0021. This is a data integrity issue affecting the profile system.
- **cand-045** (en, r1) Webhook delivery queue empty for order events — severity high→critical · conf 0.95
  - Order webhooks are not being dispatched at all since deploy 4.2.0, while other event types work, indicating a broken feature for webhook-dependent integrations.
- **cand-073** (es, r1) El carrito se vacía al cerrar sesión — severity high→critical; category data→functional · conf 0.94
  - Cart contents are lost when users log out and back in, affecting all users in a core checkout flow with no workaround.
- **cand-083** (es, r1) Reporte de ventas no incluye pedidos con cupón — severity medium→high · conf 0.90
  - The monthly sales report excludes orders with coupons, causing data inconsistency with finance records. This is a data accuracy problem in the admin reporting system.
- **cand-085** (es, r1) Buscar clientes en el admin tarda 15 segundos — severity medium→low · conf 0.80
  - Customer search in the admin takes 15 seconds, which is slow but not a complete failure. The feature works but needs performance optimization.
- **cand-088** (es, r1) El cupón de primera compra se puede usar varias veces — severity medium→high · conf 0.90
  - The first-purchase coupon BIENVENIDA should be restricted to one use but can be applied multiple times, allowing users to gain unfair discounts on subsequent orders. This is a functional defect in the checkout logic.
- **cand-108** (en, r1) Search shows products that can't ship to the user's region — category data→functional · conf 0.85
  - Search returns products unavailable in user's region, leading to checkout failures. This breaks the search and checkout flows for international users but users can work around it by checking region restrictions.
- **cand-113** (en, r1) Can't change account email — severity medium→high · conf 0.88
  - Email update in profile appears to save but the old email persists, preventing users from changing their account email address.
- **cand-116** (en, r1) Admin order list shows times in UTC — category data→ui · conf 0.85
  - Admin staff cannot correctly interpret order timestamps due to timezone mismatch, making it difficult to manage orders. This is a UI/display issue affecting the admin back-office.
- **cand-118** (en, r1) Order cancellation email not sent — severity medium→high · conf 0.90
  - Order cancellation notifications are not being sent to customers, breaking the communication flow after a support-initiated cancellation. This is a notifications system failure.
- **cand-122** (en, r1) API returns 200 with empty body for unknown product — severity medium→high · conf 0.92
  - API returns incorrect HTTP status (200 instead of 404) for non-existent resources, causing partner integrations to fail error handling. This is a functional defect in the API.
- **cand-127** (en, r1) Push shows price in USD instead of MXN — category data→ui · conf 0.85
  - Push notifications display incorrect currency labels, causing user confusion about pricing. This is a UI/data display issue in the notifications.
- **cand-138** (en, r1) API docs example uses an old field name — severity low→medium; category functional→ui · conf 0.85
  - The API documentation example uses an incorrect field name ('qty' instead of 'quantity'), which will cause developers to write broken code.
- **cand-001** (es, r2) Error 500 al pagar el pedido — component checkout→payments · conf 0.95
  - HTTP 500 error prevents order creation across all users on both web and mobile after a deploy. This is a complete outage of the checkout payment flow with no workaround.
- **cand-002** (en, r2) checkout broken!!! — component checkout→payments · conf 0.95
  - POST /api/orders returns HTTP 500 preventing any orders from being placed across all users since last night deploy. This is a full outage of checkout with no workaround.
- **cand-003** (en, r2) Order confirmation returns HTTP 500 — component checkout→payments · conf 0.95
  - HTTP 500 on Place order across all platforms and users after release 4.2.0 prevents order creation with no workaround found. This is a complete outage of core checkout functionality.
- **cand-014** (es, r2) Notificación push duplicada — severity medium→low · conf 0.90
  - Push notification is being sent twice to users for the same shipment event. This is a notification delivery issue affecting user experience across both platforms.
- **cand-015** (en, r2) Duplicate 'order shipped' push — severity medium→low · conf 0.90
  - Users receive duplicate 'order shipped' push notifications for each shipment. This is a functional defect in the notification system affecting both iOS and Android.
- **cand-028** (es, r2) Imagen de producto pixelada en iPad — severity low→medium · conf 0.85
  - Product images appear pixelated/blurry on iPad, with thumbnail loaded instead of full resolution; this is a display rendering issue affecting catalog on specific devices.
- **cand-029** (es, r2) fotos borrosas en tablet — severity low→medium · conf 0.88
  - Product images show poor quality on tablet while appearing correct on mobile, indicating responsive image handling issue in the catalog component.
- **cand-035** (en, r2) Password reset email not arriving for Hotmail users — severity medium→high; component notifications→auth · conf 0.88
  - Password reset emails fail to arrive for specific email providers (Hotmail/Outlook) but work for Gmail, indicating a provider-specific delivery or configuration issue.
- **cand-036** (en, r2) No reset email (outlook) — severity medium→high; component notifications→auth · conf 0.90
  - User unable to receive password reset email through Outlook after multiple attempts, preventing account recovery; matches the pattern in inc-0019.
- **cand-044** (en, r2) Partner reports missing webhooks — severity high→critical · conf 0.90
  - Order webhooks failed to deliver for 2 days, forcing partners to use polling instead. This is a critical API integration failure impacting partner systems.
- **cand-045** (en, r2) Webhook delivery queue empty for order events — severity high→critical · conf 0.95
  - Webhook dispatcher shows zero deliveries for order.created events since a recent deploy, indicating a complete failure of order webhook functionality.
- **cand-073** (es, r2) El carrito se vacía al cerrar sesión — category data→functional · conf 0.93
  - Shopping cart contents are lost when users log out and back in, affecting all users and forcing them to re-add items. This breaks the core cart functionality with no workaround.
- **cand-083** (es, r2) Reporte de ventas no incluye pedidos con cupón — severity medium→high · conf 0.88
  - The monthly sales report excludes orders with coupons, causing data inconsistencies and incorrect financial reconciliation. This is a data accuracy problem in the admin reporting system.
- **cand-085** (es, r2) Buscar clientes en el admin tarda 15 segundos — severity medium→low · conf 0.80
  - Customer search in admin takes 15 seconds, which is slow but does not prevent the workflow from completing; staff can use other methods to find customers.
- **cand-088** (es, r2) El cupón de primera compra se puede usar varias veces — severity medium→high · conf 0.90
  - The BIENVENIDA coupon, which should be limited to first purchase only, is being applied to multiple purchases. This is a functional defect in the checkout/promotions logic.
- **cand-101** (en, r2) User sees another customer's cart — category security→data · conf 0.95
  - Multiple users viewing each other's cart and personal data due to CDN caching is a critical data exposure and authorization bypass affecting checkout. This exposes sensitive customer information.
- **cand-108** (en, r2) Search shows products that can't ship to the user's region — severity high→medium; category data→functional · conf 0.85
  - Search results show products that fail at checkout, causing users to waste time and encounter errors. This breaks the shopping flow for affected region but they have a workaround of filtering manually or reading descriptions.
- **cand-113** (en, r2) Can't change account email — severity medium→high; category functional→data · conf 0.88
  - Email change in profile appears to save but does not actually update, resulting in incorrect stored data. The old email remains despite the success message.
- **cand-116** (en, r2) Admin order list shows times in UTC — category data→ui · conf 0.85
  - Admin staff cannot correctly interpret order times because the timezone display is wrong. This affects the admin backend workflow and causes confusion for a small group of internal users.
- **cand-118** (en, r2) Order cancellation email not sent — severity medium→high · conf 0.90
  - Order cancellation notifications are not being sent to customers, which is a failure in the notification system itself. This is a broken feature affecting customer communication after a core flow.
- **cand-122** (en, r2) API returns 200 with empty body for unknown product — severity medium→high · conf 0.92
  - The API returns incorrect HTTP status (200 instead of 404) for unknown resources, causing partner integrations to fail at error handling. This is a functional defect in the API contract.
- **cand-138** (en, r2) API docs example uses an old field name — severity low→medium; category functional→ui · conf 0.85
  - API documentation contains an outdated example using 'qty' field when the endpoint expects 'quantity', which misleads developers integrating with the cart API.
