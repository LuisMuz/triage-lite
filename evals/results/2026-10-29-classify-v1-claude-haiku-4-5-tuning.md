# classify/v1 · global.anthropic.claude-haiku-4-5-20251001-v1:0 · seed-v1/tuning

Run 2026-10-29T20:54:43+00:00 · repeat 1 · 60 items · 6 calls (0 fresh, 6 cached chunks)

| prompt | model | split | severity macro-F1 [95% CI] | sev acc | comp acc | cat acc | conf≥0.7 acc (share) | valid first try | needs_manual | $/100 | p50 / p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| classify/v1 | global.anthropic.claude-haiku-4-5-20251001-v1:0 | tuning | **0.726** [0.620-0.817] | 71.7% | 91.7% | 90.0% | 71.7% (100.0%) | 100.0% | 0.0% | $0.070 | 4482 / 5561 |

Language detection accuracy: 100.0%.

## Severity per class

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| critical | 0.92 | 1.00 | 0.96 | 11 |
| high | 0.60 | 0.94 | 0.73 | 16 |
| medium | 0.60 | 0.33 | 0.43 | 18 |
| low | 0.85 | 0.73 | 0.79 | 15 |

## Confusion (rows = gold, columns = predicted)

| gold \ pred | critical | high | medium | low | needs_manual |
|---|---|---|---|---|---|
| critical | 11 | 0 | 0 | 0 | 0 |
| high | 1 | 15 | 0 | 0 | 0 |
| medium | 0 | 10 | 6 | 2 | 0 |
| low | 0 | 0 | 4 | 11 | 0 |

## Calibration (severity correct, by stated confidence)

| confidence | count | mean confidence | accuracy |
|---|---|---|---|
| 0.0-0.2 | 0 | n/a | n/a |
| 0.2-0.4 | 0 | n/a | n/a |
| 0.4-0.6 | 0 | n/a | n/a |
| 0.6-0.8 | 0 | n/a | n/a |
| 0.8-1.0 | 60 | 0.90 | 71.7% |

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
