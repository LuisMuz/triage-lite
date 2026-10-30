# classify/v3 · openai.gpt-oss-120b-1:0 · seed-v1/tuning

Run 2026-10-30T19:16:25+00:00 · repeat 3 · 10 incidents per call · 60 items · 36 calls (24 fresh, 6 cached chunks)

| prompt | model | split | severity macro-F1 [95% CI] | sev acc | comp acc | cat acc | conf≥0.7 acc (share) | valid first try | needs_manual | $/100 | p50 / p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| classify/v3 | openai.gpt-oss-120b-1:0 | tuning | **0.630** [0.505-0.737] | 62.8% | 92.2% | 80.6% | 62.8% (100.0%) | 0.0% | 0.0% | $0.023 | 8036 / 10788 |

Language detection accuracy: 100.0%.

## Severity per class

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| critical | 1.00 | 0.55 | 0.71 | 33 |
| high | 0.53 | 0.60 | 0.56 | 48 |
| medium | 0.53 | 0.39 | 0.45 | 54 |
| low | 0.67 | 1.00 | 0.80 | 45 |

## Confusion (rows = gold, columns = predicted)

| gold \ pred | critical | high | medium | low | needs_manual |
|---|---|---|---|---|---|
| critical | 18 | 14 | 1 | 0 | 0 |
| high | 0 | 29 | 18 | 1 | 0 |
| medium | 0 | 12 | 21 | 21 | 0 |
| low | 0 | 0 | 0 | 45 | 0 |

## Calibration (severity correct, by stated confidence)

| confidence | count | mean confidence | accuracy |
|---|---|---|---|
| 0.0-0.2 | 0 | n/a | n/a |
| 0.2-0.4 | 0 | n/a | n/a |
| 0.4-0.6 | 0 | n/a | n/a |
| 0.6-0.8 | 1 | 0.75 | 100.0% |
| 0.8-1.0 | 179 | 0.91 | 62.6% |

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
- **cand-001** (es, r1) Error 500 al pagar el pedido — category crash→functional; component checkout→payments · conf 0.97
  - All users cannot complete payment and receive a 500 error, preventing order creation with no workaround.
- **cand-002** (en, r1) checkout broken!!! — category crash→functional; component checkout→payments · conf 0.96
  - Universal 500 error on order placement blocks the core checkout flow for every user, no workaround available.
- **cand-003** (en, r1) Order confirmation returns HTTP 500 — category crash→functional; component checkout→payments · conf 0.96
  - Placing an order fails with HTTP 500 across all platforms, stopping the core purchase flow entirely.
- **cand-006** (es, r1) Cobro duplicado con tarjeta — severity critical→high · conf 0.94
  - Customers are charged twice for a single order; finance can refund manually, so a workaround exists but the core payment flow misbehaves.
- **cand-007** (en, r1) Customers charged twice for one order — severity critical→high · conf 0.94
  - Duplicate captures due to retry logic cause double charges; staff can refund, indicating a workaround but a critical payment issue.
- **cand-008** (es, r1) me cobraron 2 veces!! — severity critical→high · conf 0.93
  - User reports double charge for a single purchase; issue is similar to other duplicate‑charge reports with manual refunds as a workaround.
- **cand-014** (es, r1) Notificación push duplicada — severity medium→low; category functional→ui · conf 0.98
  - Push notification is sent twice; it’s a minor annoyance with no impact on core functionality.
- **cand-015** (en, r1) Duplicate 'order shipped' push — severity medium→low; category functional→ui · conf 0.98
  - Duplicate 'order shipped' push is a cosmetic issue, not affecting core flows.
- **cand-021** (en, r1) App crashes opening order history — severity high→medium · conf 0.85
  - The app crashes when opening order history for users with many orders, preventing access to a core user profile feature for a sizable segment.
- **cand-023** (en, r1) order history closes the app — severity high→medium · conf 0.80
  - Order list crashes the whole app for users with many orders, blocking access to their purchase history.
- **cand-032** (es, r1) Búsqueda muy lenta en la app — severity high→medium · conf 0.85
  - Search results take 6‑8 seconds on 4G, noticeably slower than the web, degrading user experience in a core flow.
- **cand-033** (es, r1) buscar tarda muchisimo — severity high→medium · conf 0.85
  - Search hangs for a long time on the app while the web version is fast, impacting the core search functionality.
- **cand-034** (es, r1) Latencia alta en /search desde móvil — component search→api · conf 0.80
  - The mobile /search API has p95 latency of 7.8 s versus 300 ms on web, causing severe slowdown for the search feature.
- **cand-035** (en, r1) Password reset email not arriving for Hotmail users — severity medium→high · conf 0.85
  - Password‑reset emails are not delivered to Hotmail/Outlook users, blocking a critical authentication flow for those users.
- **cand-036** (en, r1) No reset email (outlook) — severity medium→high · conf 0.85
  - Outlook users never receive password‑reset emails, preventing them from resetting credentials; a core auth function fails.
- **cand-062** (es, r1) Historial de pedidos vacío después de la migración — severity critical→high · conf 0.90
  - After a DB migration, many users and staff see an empty order history, indicating a major data loss issue.
- **cand-069** (es, r1) No llega el código de verificación por SMS — component notifications→auth · conf 0.90
  - Two‑step verification SMS codes are not delivered, blocking login for users who rely on SMS (email fallback exists).
- **cand-071** (es, r1) No acepta tarjetas American Express — severity high→medium · conf 0.85
  - American Express cards are rejected while other cards work, affecting a subset of payment methods.
- **cand-073** (es, r1) El carrito se vacía al cerrar sesión — category data→functional · conf 0.90
  - The cart is cleared on logout for all users, breaking the shopping flow and requiring re‑adding items.
- **cand-077** (es, r1) No se ve la tabla de tallas en móvil — severity medium→low · conf 0.95
  - The size chart is missing only on mobile devices, which is a visual/layout issue that does not block buying.
- **cand-083** (es, r1) Reporte de ventas no incluye pedidos con cupón — severity medium→high · conf 0.85
  - Sales reports omit orders that used coupons, leading to inaccurate financial data for staff.
- **cand-088** (es, r1) El cupón de primera compra se puede usar varias veces — severity medium→high · conf 0.90
  - The welcome coupon can be reused, breaking the intended one‑time discount rule and affecting revenue.
- **cand-101** (en, r1) User sees another customer's cart — severity critical→high; category security→functional · conf 0.90
  - Customers see each other's cart items, breaking the core cart flow for many users; a workaround would be to clear the CDN cache.
- **cand-108** (en, r1) Search shows products that can't ship to the user's region — severity high→medium; category data→functional · conf 0.85
  - Search returns products unavailable in the user's region, leading to checkout failures for a specific user group.
- **cand-116** (en, r1) Admin order list shows times in UTC — severity medium→low; category data→ui · conf 0.90
  - Admin order list displays times in UTC instead of local time, a cosmetic display issue for staff.
- **cand-124** (en, r1) Autocomplete lags on older iPhones — severity medium→low · conf 0.85
  - Autocomplete input lags on older iPhones, a performance degradation affecting a subset of devices.
- **cand-127** (en, r1) Push shows price in USD instead of MXN — severity medium→low; category data→ui · conf 0.90
  - Push notifications show MXN amounts with a USD label, a minor UI/translation issue.
- **cand-138** (en, r1) API docs example uses an old field name — category functional→ui · conf 0.90
  - Documentation shows an outdated field name, which may confuse developers but does not affect the live API.
- **cand-001** (es, r2) Error 500 al pagar el pedido — category crash→functional; component checkout→payments · conf 0.97
  - All users cannot complete purchase due to a 500 error at payment, a core flow is completely broken with no workaround.
- **cand-002** (en, r2) checkout broken!!! — category crash→functional; component checkout→payments · conf 0.96
  - Order placement fails for everyone with a 500 error, blocking the checkout core flow entirely.
- **cand-003** (en, r2) Order confirmation returns HTTP 500 — category crash→functional; component checkout→payments · conf 0.96
  - Placing an order returns HTTP 500 across all platforms, preventing order creation for all users, no workaround.
- **cand-006** (es, r2) Cobro duplicado con tarjeta — severity critical→high; category data→functional · conf 0.94
  - Customers are charged twice for the same order, affecting core payment flow; refunds are possible but manual.
- **cand-007** (en, r2) Customers charged twice for one order — severity critical→high; category data→functional · conf 0.94
  - Multiple tickets show duplicate card charges; core payment flow malfunction, workaround is manual refund.
- **cand-008** (es, r2) me cobraron 2 veces!! — severity critical→medium; category data→functional · conf 0.92
  - An individual user sees a double charge; core payment flow errors but limited impact, no automated fix yet.
- **cand-014** (es, r2) Notificación push duplicada — severity medium→low · conf 0.95
  - Push notification is sent twice, causing annoyance but no functional blockage.
- **cand-015** (en, r2) Duplicate 'order shipped' push — severity medium→low · conf 0.95
  - Duplicate 'order shipped' push is a minor usability issue without impact on core functionality.
- **cand-021** (en, r2) App crashes opening order history — severity high→medium · conf 0.80
  - The app crashes when opening order history for users with many orders, affecting a segment of users but not the entire core flow.
- **cand-022** (en, r2) Crash: IndexOutOfBoundsException in OrderAdapter — severity high→medium · conf 0.85
  - Crash logs show an IndexOutOfBoundsException on the order history screen, causing app termination for affected users.
- **cand-023** (en, r2) order history closes the app — severity high→medium · conf 0.80
  - User reports the whole app closing when opening the order list, indicating a crash in the profile/orders flow.
- **cand-032** (es, r2) Búsqueda muy lenta en la app — severity high→medium · conf 0.80
  - Search results take 6‑8 seconds on mobile networks, slowing a core flow for many users.
- **cand-033** (es, r2) buscar tarda muchisimo — severity high→medium · conf 0.80
  - Search is significantly delayed in the app compared to the web, impacting user experience.
- **cand-034** (es, r2) Latencia alta en /search desde móvil — component search→api · conf 0.75
  - The mobile /search endpoint has p95 latency of 7.8 s, a major slowdown of a core search API affecting many users.
- **cand-035** (en, r2) Password reset email not arriving for Hotmail users — severity medium→high; component notifications→auth · conf 0.80
  - Password reset emails are not delivered to Hotmail/Outlook users, breaking a core authentication flow for that provider.
- **cand-036** (en, r2) No reset email (outlook) — severity medium→high; component notifications→auth · conf 0.80
  - Outlook users do not receive password reset emails after multiple attempts, preventing account recovery.
- **cand-041** (es, r2) Direcciones guardadas se duplican al editar — category data→functional · conf 0.90
  - Editing a saved address creates a duplicate instead of updating it, leading to data duplication in user profiles.
- **cand-042** (es, r2) Se repiten mis direcciones — category data→functional · conf 0.90
  - The Android app shows the same address multiple times after editing, indicating a duplication bug in the profile address management.
- **cand-062** (es, r2) Historial de pedidos vacío después de la migración — severity critical→high · conf 0.85
  - After the database migration, many users and staff see an empty order history, losing access to essential order records.
- **cand-068** (es, r2) Precio en la app distinto al de la web — severity high→medium · conf 0.80
  - The app displays outdated lower prices while the payment is processed at the correct (higher) web price, causing confusion but not payment failure.
- **cand-069** (es, r2) No llega el código de verificación por SMS — component notifications→auth · conf 0.85
  - Two‑step verification SMS codes are not delivered, blocking login for affected users though email fallback exists.
- **cand-073** (es, r2) El carrito se vacía al cerrar sesión — severity high→medium; category data→functional · conf 0.85
  - The cart is cleared after logout, requiring users to re‑add items, which degrades the shopping experience but does not block checkout.
- **cand-077** (es, r2) No se ve la tabla de tallas en móvil — severity medium→low · conf 0.95
  - Size table missing only on mobile devices; the product can still be purchased, it's a cosmetic layout issue.
- **cand-083** (es, r2) Reporte de ventas no incluye pedidos con cupón — severity medium→high · conf 0.85
  - Sales reports omit orders that used coupons, leading to inaccurate financial data with no easy workaround.
- **cand-088** (es, r2) El cupón de primera compra se puede usar varias veces — severity medium→high · conf 0.90
  - Welcome coupon can be reused infinitely, breaking the intended discount logic and potentially causing revenue loss; no proper restriction exists.
- **cand-101** (en, r2) User sees another customer's cart — severity critical→high; category security→data · conf 0.90
  - Users on the same network see each other's cart items and addresses, leaking personal data and breaking the cart core flow.
- **cand-108** (en, r2) Search shows products that can't ship to the user's region — severity high→medium; category data→functional · conf 0.85
  - Search returns products unavailable in the user's region, causing checkout failures for a specific user segment.
- **cand-113** (en, r2) Can't change account email — severity medium→low · conf 0.90
  - User cannot update email address; the operation reports success but makes no change, a minor profile issue.
- **cand-116** (en, r2) Admin order list shows times in UTC — severity medium→low; category data→ui · conf 0.90
  - Admin order list displays times in UTC instead of local time, a cosmetic/display problem for staff.
- **cand-124** (en, r2) Autocomplete lags on older iPhones — severity medium→low · conf 0.85
  - Autocomplete in the iOS app lags noticeably on older iPhones, affecting usability but not core functionality.
- **cand-127** (en, r2) Push shows price in USD instead of MXN — severity medium→low · conf 0.90
  - Push notifications show prices with a USD label for Mexican users, displaying incorrect currency data.
- **cand-138** (en, r2) API docs example uses an old field name — category functional→ui · conf 0.90
  - Documentation shows an outdated field name, which is a textual UI error and does not affect the live API.
- **hand-006** (en, r2) Category page takes over ten seconds to load — severity medium→high · conf 0.85
  - First‑load of a category takes over ten seconds, severely degrading a core browsing flow for many users.
