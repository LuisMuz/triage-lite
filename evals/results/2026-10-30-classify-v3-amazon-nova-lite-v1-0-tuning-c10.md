# classify/v3 · amazon.nova-lite-v1:0 · seed-v1/tuning

Run 2026-10-30T19:09:14+00:00 · repeat 1 · 10 incidents per call · 60 items · 6 calls (6 fresh, 0 cached chunks)

| prompt | model | split | severity macro-F1 [95% CI] | sev acc | comp acc | cat acc | conf≥0.7 acc (share) | valid first try | needs_manual | $/100 | p50 / p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| classify/v3 | amazon.nova-lite-v1:0 | tuning | **0.601** [0.465-0.712] | 60.0% | 93.3% | 90.0% | 60.0% (100.0%) | 100.0% | 0.0% | $0.003 | 5214 / 6404 |

Language detection accuracy: 100.0%.

## Severity per class

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| critical | 0.58 | 1.00 | 0.73 | 11 |
| high | 0.60 | 0.56 | 0.58 | 16 |
| medium | 0.50 | 0.33 | 0.40 | 18 |
| low | 0.71 | 0.67 | 0.69 | 15 |

## Confusion (rows = gold, columns = predicted)

| gold \ pred | critical | high | medium | low | needs_manual |
|---|---|---|---|---|---|
| critical | 11 | 0 | 0 | 0 | 0 |
| high | 6 | 9 | 1 | 0 | 0 |
| medium | 2 | 6 | 6 | 4 | 0 |
| low | 0 | 0 | 5 | 10 | 0 |

## Calibration (severity correct, by stated confidence)

| confidence | count | mean confidence | accuracy |
|---|---|---|---|
| 0.0-0.2 | 0 | n/a | n/a |
| 0.2-0.4 | 0 | n/a | n/a |
| 0.4-0.6 | 0 | n/a | n/a |
| 0.6-0.8 | 1 | 0.75 | 0.0% |
| 0.8-1.0 | 59 | 0.91 | 61.0% |

## Errors (any label wrong, or needs_manual)

- **cand-001** (es, r0) Error 500 al pagar el pedido — component checkout→payments · conf 0.95
  - A critical error during payment prevents users from completing purchases, impacting a core flow.
- **cand-014** (es, r0) Notificación push duplicada — severity medium→low; category functional→ui · conf 0.90
  - Users receive duplicate push notifications for every shipment, which is a cosmetic issue.
- **cand-015** (en, r0) Duplicate 'order shipped' push — severity medium→low; category functional→ui · conf 0.90
  - Users receive duplicate push notifications for every shipment, which is a cosmetic issue.
- **cand-021** (en, r0) App crashes opening order history — severity high→critical · conf 0.95
  - The app crashes when a user with more than 100 orders tries to open their order history, indicating a critical issue that prevents access to a core feature.
- **cand-022** (en, r0) Crash: IndexOutOfBoundsException in OrderAdapter — severity high→critical · conf 0.95
  - An IndexOutOfBoundsException causing a crash on the order history screen is a critical issue that affects a core flow for many users.
- **cand-023** (en, r0) order history closes the app — severity high→critical · conf 0.95
  - The app closing when trying to access the order history is a critical issue affecting a core flow for users with a large number of orders.
- **cand-028** (es, r0) Imagen de producto pixelada en iPad — severity low→medium · conf 0.90
  - Pixelated product images on iPad indicate a UI issue that affects the shopping experience for tablet users.
- **cand-029** (es, r0) fotos borrosas en tablet — severity low→medium · conf 0.90
  - Poor quality images on a tablet compared to a phone suggest a UI issue that impacts the visual shopping experience.
- **cand-035** (en, r0) Password reset email not arriving for Hotmail users — severity medium→critical; component notifications→auth · conf 0.95
  - Failure to deliver password reset emails to specific email providers is a critical issue affecting account recovery for users.
- **cand-036** (en, r0) No reset email (outlook) — severity medium→critical; component notifications→auth · conf 0.95
  - Failure to deliver password reset emails to a specific email provider is a critical issue affecting account recovery for users.
- **cand-041** (es, r0) Direcciones guardadas se duplican al editar — severity medium→high; category data→functional · conf 0.95
  - Saved addresses are duplicating instead of updating, affecting the profile component.
- **cand-042** (es, r0) Se repiten mis direcciones — severity medium→high; category data→functional · conf 0.95
  - Saved addresses are repeating in the profile, which is a functional issue in the profile component.
- **cand-044** (en, r0) Partner reports missing webhooks — severity high→critical · conf 0.95
  - Missing webhooks are causing a critical issue with our partner's order processing.
- **cand-045** (en, r0) Webhook delivery queue empty for order events — severity high→critical · conf 0.95
  - Webhook delivery queue is empty for order events, affecting order processing.
- **cand-069** (es, r0) No llega el código de verificación por SMS — component notifications→auth · conf 0.95
  - Users with 2FA are not receiving SMS verification codes, impacting authentication.
- **cand-073** (es, r0) El carrito se vacía al cerrar sesión — category data→functional · conf 0.95
  - The shopping cart is cleared upon logout, impacting the shopping experience for all users.
- **cand-083** (es, r0) Reporte de ventas no incluye pedidos con cupón — severity medium→high · conf 0.95
  - Sales report is inaccurate as it doesn't include orders with coupons, affecting financial reporting.
- **cand-088** (es, r0) El cupón de primera compra se puede usar varias veces — severity medium→high · conf 0.90
  - A first-time purchase coupon can be used multiple times, affecting coupon policy.
- **cand-092** (es, r0) Mensaje de error del login en inglés — severity low→medium · conf 0.90
  - Login error message is in English despite the app being in Spanish, affecting user experience.
- **cand-098** (es, r0) Montos alineados a la izquierda en tablas del admin — severity low→medium · conf 0.90
  - Amounts are left-aligned in admin tables, making them hard to compare.
- **cand-108** (en, r0) Search shows products that can't ship to the user's region — severity high→medium · conf 0.85
  - Search results incorrectly include products not available in the user's region.
- **cand-110** (en, r0) iOS app crashes on payment step with saved card — severity high→critical · conf 0.90
  - iOS app crashes when selecting a saved card during payment.
- **cand-116** (en, r0) Admin order list shows times in UTC — severity medium→low · conf 0.80
  - Admin order list displays times in UTC instead of local time, causing confusion.
- **cand-118** (en, r0) Order cancellation email not sent — severity medium→high · conf 0.90
  - Customers do not receive an order cancellation email after support cancels an order.
- **cand-122** (en, r0) API returns 200 with empty body for unknown product — category functional→data · conf 0.80
  - API returns a 200 status code with an empty body for an unknown product, breaking partner error handling.
- **cand-124** (en, r0) Autocomplete lags on older iPhones — severity medium→low · conf 0.75
  - Autocomplete in the search box lags significantly on older iPhone models.
- **cand-138** (en, r0) API docs example uses an old field name — severity low→medium · conf 0.85
  - The API documentation is incorrect, potentially leading to confusion for developers, but it does not directly affect the end-user experience.
- **hand-006** (en, r0) Category page takes over ten seconds to load — severity medium→high · conf 0.90
  - A performance issue that affects the user experience by delaying the loading of a category page.
