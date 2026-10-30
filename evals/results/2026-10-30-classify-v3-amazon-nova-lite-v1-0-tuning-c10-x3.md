# classify/v3 · amazon.nova-lite-v1:0 · seed-v1/tuning

Run 2026-10-30T19:10:33+00:00 · repeat 3 · 10 incidents per call · 60 items · 19 calls (13 fresh, 6 cached chunks)

| prompt | model | split | severity macro-F1 [95% CI] | sev acc | comp acc | cat acc | conf≥0.7 acc (share) | valid first try | needs_manual | $/100 | p50 / p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| classify/v3 | amazon.nova-lite-v1:0 | tuning | **0.598** [0.498-0.684] | 58.9% | 92.2% | 81.7% | 58.9% (100.0%) | 100.0% | 0.0% | $0.003 | 5415 / 6991 |

Language detection accuracy: 100.0%.

## Severity per class

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| critical | 0.56 | 0.85 | 0.67 | 33 |
| high | 0.62 | 0.54 | 0.58 | 48 |
| medium | 0.48 | 0.46 | 0.47 | 54 |
| low | 0.75 | 0.60 | 0.67 | 45 |

## Confusion (rows = gold, columns = predicted)

| gold \ pred | critical | high | medium | low | needs_manual |
|---|---|---|---|---|---|
| critical | 28 | 1 | 4 | 0 | 0 |
| high | 17 | 26 | 5 | 0 | 0 |
| medium | 5 | 15 | 25 | 9 | 0 |
| low | 0 | 0 | 18 | 27 | 0 |

## Calibration (severity correct, by stated confidence)

| confidence | count | mean confidence | accuracy |
|---|---|---|---|
| 0.0-0.2 | 0 | n/a | n/a |
| 0.2-0.4 | 0 | n/a | n/a |
| 0.4-0.6 | 0 | n/a | n/a |
| 0.6-0.8 | 1 | 0.75 | 0.0% |
| 0.8-1.0 | 179 | 0.91 | 59.2% |

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
- **cand-001** (es, r1) Error 500 al pagar el pedido — category crash→functional; component checkout→payments · conf 0.95
  - A critical payment issue causing complete failure to process orders for all users.
- **cand-002** (en, r1) checkout broken!!! — category crash→functional; component checkout→payments · conf 0.95
  - A critical payment issue causing complete failure to process orders for all users.
- **cand-003** (en, r1) Order confirmation returns HTTP 500 — category crash→functional; component checkout→payments · conf 0.95
  - A critical payment issue causing complete failure to process orders for all users.
- **cand-006** (es, r1) Cobro duplicado con tarjeta — severity critical→medium · conf 0.90
  - A medium issue where customers are being charged twice for a single order.
- **cand-007** (en, r1) Customers charged twice for one order — severity critical→medium · conf 0.90
  - A medium issue where customers are being charged twice for a single order.
- **cand-008** (es, r1) me cobraron 2 veces!! — severity critical→medium · conf 0.90
  - A medium issue where customers are being charged twice for a single order.
- **cand-014** (es, r1) Notificación push duplicada — severity medium→low; category functional→ui · conf 0.90
  - A low issue where users receive duplicate push notifications.
- **cand-015** (en, r1) Duplicate 'order shipped' push — severity medium→low; category functional→ui · conf 0.90
  - A low issue where users receive duplicate push notifications.
- **cand-021** (en, r1) App crashes opening order history — severity high→critical · conf 0.95
  - The app crashes when accessing the order history for users with many orders, indicating a critical crash issue.
- **cand-022** (en, r1) Crash: IndexOutOfBoundsException in OrderAdapter — severity high→critical · conf 0.95
  - The crash is caused by an out-of-bounds error in the OrderAdapter, affecting the order history screen.
- **cand-023** (en, r1) order history closes the app — severity high→critical · conf 0.95
  - The order history feature causes the app to close, affecting usability for users with many orders.
- **cand-028** (es, r1) Imagen de producto pixelada en iPad — severity low→medium · conf 0.85
  - Product images are displayed poorly on an iPad, affecting the user experience on this device.
- **cand-029** (es, r1) fotos borrosas en tablet — severity low→medium · conf 0.85
  - Product images have poor quality on a Galaxy Tab, affecting the user experience on tablets.
- **cand-035** (en, r1) Password reset email not arriving for Hotmail users — severity medium→high; component notifications→auth · conf 0.90
  - Password reset emails are not being received by users with certain email providers, preventing account recovery.
- **cand-036** (en, r1) No reset email (outlook) — severity medium→high; component notifications→auth · conf 0.90
  - Password reset emails are not being received by a user with an Outlook email address, preventing account recovery.
- **cand-041** (es, r1) Direcciones guardadas se duplican al editar — severity medium→high; category data→functional · conf 0.95
  - The saved addresses are duplicating instead of updating, which is a data consistency issue.
- **cand-042** (es, r1) Se repiten mis direcciones — severity medium→high · conf 0.90
  - Repeated addresses in the user profile is a data issue affecting multiple users.
- **cand-044** (en, r1) Partner reports missing webhooks — severity high→critical · conf 0.95
  - Missing webhooks for 2 days can lead to significant business impacts; a critical incident.
- **cand-045** (en, r1) Webhook delivery queue empty for order events — severity high→critical · conf 0.95
  - Webhook delivery queue being empty for order events is a critical functional issue.
- **cand-069** (es, r1) No llega el código de verificación por SMS — component notifications→auth · conf 0.90
  - Users not receiving SMS verification codes is a functional issue affecting user authentication.
- **cand-073** (es, r1) El carrito se vacía al cerrar sesión — category data→functional · conf 0.95
  - Cart being emptied on logout affects all users and is a significant functional issue.
- **cand-075** (es, r1) No se pueden marcar pedidos como enviados — severity high→critical · conf 0.95
  - The inability to mark orders as sent in the admin affects the order fulfillment process.
- **cand-083** (es, r1) Reporte de ventas no incluye pedidos con cupón — severity medium→high · conf 0.95
  - Incorrect sales report due to missing coupon orders affects many users.
- **cand-088** (es, r1) El cupón de primera compra se puede usar varias veces — severity medium→high · conf 0.95
  - A coupon meant for first-time use only being applicable multiple times affects many users.
- **cand-096** (es, r1) Texto 'Direccion de envio' sin acentos — severity low→medium · conf 0.90
  - Missing accents in the shipping address text affects all users.
- **cand-098** (es, r1) Montos alineados a la izquierda en tablas del admin — severity low→medium · conf 0.90
  - Misaligned currency amounts in admin tables affects all users.
- **cand-101** (en, r1) User sees another customer's cart — severity critical→high; category security→functional · conf 0.90
  - Users seeing another's cart is a major functional issue affecting multiple users in a specific environment.
- **cand-108** (en, r1) Search shows products that can't ship to the user's region — category data→functional · conf 0.85
  - Search results showing unavailable products can lead to user frustration and failed transactions.
- **cand-110** (en, r1) iOS app crashes on payment step with saved card — severity high→critical · conf 0.95
  - An app crash during a critical step like payment is a severe issue.
- **cand-113** (en, r1) Can't change account email — severity medium→critical · conf 0.95
  - An inability to change an account email is a critical functional issue.
- **cand-122** (en, r1) API returns 200 with empty body for unknown product — category functional→data · conf 0.80
  - API returning an incorrect status code and empty body for an unknown product is a medium severity issue.
- **cand-128** (en, r1) Long product titles truncated with no tooltip — severity low→medium · conf 0.90
  - Product title truncation is a UI issue that affects usability.
- **cand-133** (en, r1) Admin sidebar icon misaligned — severity low→medium · conf 0.90
  - Misaligned icon in the admin sidebar is a UI issue, potentially confusing for admin users.
- **cand-136** (en, r1) Typo 'Adress' in shipping form — severity low→medium; category ui→data · conf 0.90
  - Typo in the shipping form is a data issue, leading to potential user confusion.
- **cand-138** (en, r1) API docs example uses an old field name — severity low→medium; category functional→data · conf 0.90
  - API docs example using an old field name is a data issue, potentially causing developer confusion.
- **cand-140** (en, r1) Card brand logos have different sizes — severity low→medium · conf 0.90
  - Different sizes of card brand logos on the payment step is a UI issue, affecting visual consistency.
- **hand-006** (en, r1) Category page takes over ten seconds to load — severity medium→high · conf 0.90
  - Slow loading of a category page is a performance issue, affecting user experience.
- **hand-010** (en, r1) Unread notification badge does not clear immediately — severity low→medium · conf 0.90
  - Unread notification badge not clearing immediately is a UI issue, potentially misleading users.
- **cand-001** (es, r2) Error 500 al pagar el pedido — category crash→functional; component checkout→payments · conf 0.95
  - A payment failure that affects all users in production since the last update, preventing purchases.
- **cand-002** (en, r2) checkout broken!!! — category crash→functional · conf 0.95
  - A core checkout flow is broken for all users in production since the last deploy, with no workaround.
- **cand-003** (en, r2) Order confirmation returns HTTP 500 — category crash→functional · conf 0.95
  - Order confirmation returns HTTP 500 and no order is created, affecting all platforms in production.
- **cand-014** (es, r2) Notificación push duplicada — category functional→ui · conf 0.90
  - Users receive duplicate push notifications for every shipment in Android and iOS.
- **cand-015** (en, r2) Duplicate 'order shipped' push — category functional→ui · conf 0.90
  - Users receive duplicate push notifications for every shipment in iOS and Android.
- **cand-021** (en, r2) App crashes opening order history — severity high→critical · conf 0.95
  - The app crashes when users with many orders open the order history, which is a critical flow.
- **cand-022** (en, r2) Crash: IndexOutOfBoundsException in OrderAdapter — severity high→critical · conf 0.95
  - This crash occurs in a specific adapter when binding data, affecting the order history screen.
- **cand-023** (en, r2) order history closes the app — severity high→critical · conf 0.95
  - The app crashes when opening the order history, which is a critical flow for users with many orders.
- **cand-032** (es, r2) Búsqueda muy lenta en la app — severity high→medium · conf 0.90
  - Search is slow on the app over 4G, which affects usability.
- **cand-035** (en, r2) Password reset email not arriving for Hotmail users — severity medium→critical; component notifications→auth · conf 0.95
  - Password reset emails are not reaching users with certain email providers, which is a critical flow.
- **cand-036** (en, r2) No reset email (outlook) — severity medium→critical; component notifications→auth · conf 0.95
  - Password reset emails are not reaching users with Outlook, which is a critical flow.
- **cand-041** (es, r2) Direcciones guardadas se duplican al editar — category data→functional · conf 0.90
  - Saved addresses are being duplicated instead of being updated, causing multiple copies of the same address.
- **cand-042** (es, r2) Se repiten mis direcciones — category data→functional · conf 0.90
  - Saved addresses are being duplicated in the app, causing multiple copies of the same address.
- **cand-044** (en, r2) Partner reports missing webhooks — category functional→data · conf 0.85
  - Missing webhooks for new orders have been reported, indicating a potential issue with webhook delivery.
- **cand-045** (en, r2) Webhook delivery queue empty for order events — category functional→data · conf 0.85
  - Webhook delivery queue is empty for order events, indicating a potential issue with webhook delivery.
- **cand-068** (es, r2) Precio en la app distinto al de la web — severity high→medium · conf 0.80
  - Product prices differ between the app and the web, causing confusion and complaints from customers.
- **cand-069** (es, r2) No llega el código de verificación por SMS — severity high→medium; component notifications→auth · conf 0.85
  - Users with two-step verification are not receiving SMS verification codes, forcing them to use an alternative method.
- **cand-073** (es, r2) El carrito se vacía al cerrar sesión — category data→functional · conf 0.90
  - The shopping cart is being emptied upon logging out and back in, causing inconvenience for users.
- **cand-075** (es, r2) No se pueden marcar pedidos como enviados — severity high→critical · conf 0.95
  - A critical functional issue in the admin component that prevents orders from being marked as sent.
- **cand-083** (es, r2) Reporte de ventas no incluye pedidos con cupón — severity medium→high · conf 0.90
  - A data issue in the admin component that affects the accuracy of sales reports.
- **cand-092** (es, r2) Mensaje de error del login en inglés — severity low→medium · conf 0.90
  - A UI issue in the auth component that affects the display of login error messages.
- **cand-098** (es, r2) Montos alineados a la izquierda en tablas del admin — severity low→medium · conf 0.85
  - A UI issue in the admin component that affects the readability of financial data.
- **cand-101** (en, r2) User sees another customer's cart — severity critical→medium; category security→functional · conf 0.95
  - Users seeing each other's cart items is a functional issue, but it's limited to a specific environment.
- **cand-108** (en, r2) Search shows products that can't ship to the user's region — severity high→medium · conf 0.95
  - Search results showing products unavailable in the user's region is a data issue.
- **cand-116** (en, r2) Admin order list shows times in UTC — severity medium→low; category data→ui · conf 0.95
  - Time zone discrepancy in the admin order list is a cosmetic issue.
- **cand-122** (en, r2) API returns 200 with empty body for unknown product — category functional→data · conf 0.95
  - API returning incorrect response for an unknown product is a data issue.
- **cand-124** (en, r2) Autocomplete lags on older iPhones — severity medium→low · conf 0.95
  - Autocomplete lag on older devices is a performance issue.
- **cand-127** (en, r2) Push shows price in USD instead of MXN — severity medium→low · conf 0.95
  - Incorrect currency display in push notifications is a data issue.
- **cand-136** (en, r2) Typo 'Adress' in shipping form — category ui→functional · conf 0.95
  - This is a typo in the shipping form.
- **cand-138** (en, r2) API docs example uses an old field name — severity low→medium; category functional→data · conf 0.95
  - This is a data issue with an incorrect field name in the API docs.
- **hand-006** (en, r2) Category page takes over ten seconds to load — severity medium→high · conf 0.95
  - This is a performance issue with the loading time of a category page.
