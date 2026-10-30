# classify/v3 · moonshotai.kimi-k2.5 · seed-v1/tuning

Run 2026-10-30T19:06:32+00:00 · repeat 1 · 10 incidents per call · 60 items · 6 calls (6 fresh, 0 cached chunks)

| prompt | model | split | severity macro-F1 [95% CI] | sev acc | comp acc | cat acc | conf≥0.7 acc (share) | valid first try | needs_manual | $/100 | p50 / p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| classify/v3 | moonshotai.kimi-k2.5 | tuning | **0.733** [0.616-0.841] | 73.3% | 93.3% | 85.0% | 73.3% (100.0%) | 100.0% | 0.0% | $0.029 | 5813 / 7422 |

Language detection accuracy: 100.0%.

## Severity per class

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| critical | 1.00 | 0.55 | 0.71 | 11 |
| high | 0.60 | 0.75 | 0.67 | 16 |
| medium | 0.71 | 0.67 | 0.69 | 18 |
| low | 0.82 | 0.93 | 0.87 | 15 |

## Confusion (rows = gold, columns = predicted)

| gold \ pred | critical | high | medium | low | needs_manual |
|---|---|---|---|---|---|
| critical | 6 | 5 | 0 | 0 | 0 |
| high | 0 | 12 | 4 | 0 | 0 |
| medium | 0 | 3 | 12 | 3 | 0 |
| low | 0 | 0 | 1 | 14 | 0 |

## Calibration (severity correct, by stated confidence)

| confidence | count | mean confidence | accuracy |
|---|---|---|---|
| 0.0-0.2 | 0 | n/a | n/a |
| 0.2-0.4 | 0 | n/a | n/a |
| 0.4-0.6 | 0 | n/a | n/a |
| 0.6-0.8 | 0 | n/a | n/a |
| 0.8-1.0 | 60 | 0.91 | 73.3% |

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
