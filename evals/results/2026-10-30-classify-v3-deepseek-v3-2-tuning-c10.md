# classify/v3 · deepseek.v3.2 · seed-v1/tuning

Run 2026-10-30T19:19:18+00:00 · repeat 1 · 10 incidents per call · 60 items · 7 calls (7 fresh, 0 cached chunks)

| prompt | model | split | severity macro-F1 [95% CI] | sev acc | comp acc | cat acc | conf≥0.7 acc (share) | valid first try | needs_manual | $/100 | p50 / p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| classify/v3 | deepseek.v3.2 | tuning | **0.630** [0.512-0.742] | 63.3% | 90.0% | 86.7% | 63.3% (100.0%) | 83.3% | 0.0% | $0.033 | 25004 / 32205 |

Language detection accuracy: 100.0%.

## Severity per class

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| critical | 0.70 | 0.64 | 0.67 | 11 |
| high | 0.43 | 0.38 | 0.40 | 16 |
| medium | 0.59 | 0.56 | 0.57 | 18 |
| low | 0.79 | 1.00 | 0.88 | 15 |

## Confusion (rows = gold, columns = predicted)

| gold \ pred | critical | high | medium | low | needs_manual |
|---|---|---|---|---|---|
| critical | 7 | 4 | 0 | 0 | 0 |
| high | 3 | 6 | 7 | 0 | 0 |
| medium | 0 | 4 | 10 | 4 | 0 |
| low | 0 | 0 | 0 | 15 | 0 |

## Calibration (severity correct, by stated confidence)

| confidence | count | mean confidence | accuracy |
|---|---|---|---|
| 0.0-0.2 | 0 | n/a | n/a |
| 0.2-0.4 | 0 | n/a | n/a |
| 0.4-0.6 | 0 | n/a | n/a |
| 0.6-0.8 | 0 | n/a | n/a |
| 0.8-1.0 | 60 | 0.90 | 63.3% |

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
