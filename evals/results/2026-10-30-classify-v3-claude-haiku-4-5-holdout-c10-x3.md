# classify/v3 · global.anthropic.claude-haiku-4-5-20251001-v1:0 · seed-v1/holdout

Run 2026-10-30T20:18:00+00:00 · repeat 3 · 10 incidents per call · 60 items · 18 calls (18 fresh, 0 cached chunks)

| prompt | model | split | severity macro-F1 [95% CI] | sev acc | comp acc | cat acc | conf≥0.7 acc (share) | valid first try | needs_manual | $/100 | p50 / p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| classify/v3 | global.anthropic.claude-haiku-4-5-20251001-v1:0 | holdout | **0.768** [0.673-0.849] | 76.1% | 91.7% | 87.8% | 76.1% (100.0%) | 100.0% | 0.0% | $0.074 | 4830 / 5607 |

Language detection accuracy: 100.0%.

## Severity per class

| class | precision | recall | F1 | support |
|---|---|---|---|---|
| critical | 0.86 | 0.94 | 0.90 | 33 |
| high | 0.72 | 0.89 | 0.79 | 54 |
| medium | 0.71 | 0.56 | 0.63 | 54 |
| low | 0.80 | 0.72 | 0.76 | 39 |

## Confusion (rows = gold, columns = predicted)

| gold \ pred | critical | high | medium | low | needs_manual |
|---|---|---|---|---|---|
| critical | 31 | 2 | 0 | 0 | 0 |
| high | 5 | 48 | 1 | 0 | 0 |
| medium | 0 | 17 | 30 | 7 | 0 |
| low | 0 | 0 | 11 | 28 | 0 |

## Calibration (severity correct, by stated confidence)

| confidence | count | mean confidence | accuracy |
|---|---|---|---|
| 0.0-0.2 | 0 | n/a | n/a |
| 0.2-0.4 | 0 | n/a | n/a |
| 0.4-0.6 | 0 | n/a | n/a |
| 0.6-0.8 | 1 | 0.75 | 100.0% |
| 0.8-1.0 | 179 | 0.89 | 76.0% |

## Errors (any label wrong, or needs_manual)

- **cand-025** (es, r0) timeout al exportar en admin — severity medium→high · conf 0.85
  - Monthly order export times out with a 504 error; staff must work around it by exporting weekly. This is a performance issue in the back-office that impacts business operations.
- **cand-026** (en, r0) Product page says in stock but cart says sold out — severity medium→high · conf 0.90
  - Product catalog shows stock status inconsistently: page says in stock but cart correctly reflects zero stock. This is a data consistency problem where the catalog display is wrong.
- **cand-027** (en, r0) Stock badge wrong for electronics — severity medium→high · conf 0.88
  - Availability badge displays stale stock data due to cache not refreshing after updates. This is a data consistency issue where displayed stock is incorrect.
- **cand-046** (es, r0) Link de darse de baja del newsletter da 404 — severity low→medium · conf 0.88
  - Newsletter unsubscribe link returns 404 error, preventing users from managing their subscription preferences. This is a functional issue affecting the notifications component.
- **cand-047** (es, r0) no me puedo desuscribir — severity low→medium · conf 0.88
  - Newsletter unsubscribe link is broken and returns 404. Same issue as inc-0018 preventing users from managing newsletter preferences.
- **cand-048** (en, r0) Orders created with $0 total — component checkout→payments · conf 0.95
  - Orders are being created with $0.00 totals when combining coupon and gift card, allowing items to ship for free. This is a critical data and pricing issue affecting revenue.
- **cand-049** (en, r0) Zero-value orders in finance report — severity critical→high; component checkout→payments · conf 0.85
  - Orders with zero total due to coupon and gift card interaction represent stored data that is wrong and inconsistent with the transaction amount. This is a data integrity issue affecting financial records.
- **cand-050** (en, r0) coupon + giftcard = free stuff — severity critical→high; category data→functional; component checkout→payments · conf 0.90
  - Users exploiting a coupon and gift card combination to receive free items is a functional bug in the pricing logic that allows unauthorized transactions. The fact it's already public on deal forums makes this high priority.
- **cand-051** (en, r0) Gift card and coupon stacking zeroes the order total — category data→functional; component checkout→payments · conf 0.95
  - The gift card calculation logic incorrectly handles the interaction with coupons, causing orders to total zero instead of the correct amount. This is a core checkout flow defect affecting payment accuracy.
- **cand-052** (es, r0) El contador del carrito no baja al quitar productos — category functional→ui · conf 0.85
  - The cart badge counter fails to update visually when items are removed, but the actual cart data is correct. This is a UI display issue without functional impact.
- **cand-054** (es, r0) Badge del carrito desactualizado — category functional→ui · conf 0.85
  - Cart badge does not update to show the current item count after deletion, though the cart itself functions correctly. This is a visual consistency issue.
- **cand-055** (es, r0) Ícono de carrito con cantidad incorrecta — category functional→ui · conf 0.85
  - Cart icon badge displays stale item count after deletion, but actual cart contents are correct when accessed. This is a UI update issue.
- **cand-074** (es, r0) El botón Pagar queda escondido detrás del teclado — component checkout→payments · conf 0.90
  - The payment button is hidden behind the keyboard on iOS Safari with no way to scroll, making it impossible to complete payment without closing the keyboard first. This blocks a core flow.
- **cand-082** (es, r0) Los filtros de precio se pierden al regresar — severity medium→low · conf 0.80
  - Price filters are lost when navigating away from search results and returning. This is a functional issue affecting the search experience.
- **cand-084** (es, r0) 'Recordarme' no funciona — severity medium→high · conf 0.90
  - The 'Remember me' option does not persist the session, forcing users to log in every time. This is a core authentication feature that is broken.
- **cand-087** (es, r0) No llegan notificaciones push en Huawei — severity medium→high · conf 0.85
  - Huawei users without Google services cannot receive push notifications at all. This affects a significant user segment with a critical communication channel blocked.
- **cand-089** (es, r0) Error 500 al subir CSV de productos con acentos — category crash→functional · conf 0.85
  - Admin product CSV import crashes with a 500 error when product names contain accents, while it works without them. This is a functional defect in the admin tool that can be worked around.
- **cand-106** (en, r0) Login endpoint has no rate limit — severity high→critical · conf 0.98
  - The login endpoint lacks rate limiting, exposing all user accounts to brute-force attacks. This is a security vulnerability requiring immediate remediation.
- **cand-112** (en, r0) Checkout takes 15s to load on mobile — severity high→medium · conf 0.85
  - Checkout page is slow to load on mobile devices (15s), degrading the user experience. The core flow still works, just slowly.
- **cand-115** (en, r0) Admin dashboard charts take 40s to load — severity medium→low · conf 0.80
  - Admin dashboard charts load slowly (40s), affecting back-office usability but not customer-facing functionality.
- **cand-119** (en, r0) Sorting reviews by most recent does nothing — severity medium→low · conf 0.80
  - Review sorting by most recent does not work, leaving reviews in their default order. This is a non-core feature malfunction.
- **cand-132** (en, r0) Search box clears when switching tabs — severity low→medium · conf 0.85
  - The search query is lost when navigating between tabs, causing the user to re-enter their search. This is a functional issue with state management in the search component.
- **hand-008** (es, r0) El botón de iniciar sesión queda oculto con el teclado abierto — severity medium→high · conf 0.85
  - The login button is hidden behind the keyboard on small screens and the page cannot be scrolled to reveal it. This is a UI/layout issue that blocks login functionality on affected devices.
- **hand-009** (en, r0) Discount is applied twice after changing shipping method — category data→functional · conf 0.88
  - A promo discount is applied twice in the order total when changing the shipping method after applying a coupon. This is a functional calculation error in the checkout process.
- **cand-026** (en, r1) Product page says in stock but cart says sold out — severity medium→high · conf 0.85
  - Product page shows wrong stock status (In stock) while cart correctly reflects admin stock (0), causing user confusion and failed add-to-cart attempts. Data consistency issue between catalog display and inventory.
- **cand-027** (en, r1) Stock badge wrong for electronics — severity medium→high · conf 0.90
  - Stock availability badge displays stale data (shows available when stock is zero) due to cache not refreshing after inventory updates. Data inconsistency affecting multiple environments.
- **cand-046** (es, r1) Link de darse de baja del newsletter da 404 — severity low→medium · conf 0.90
  - Newsletter unsubscribe link returns 404 error, preventing users from removing themselves from mailing list. Functional issue in notification system.
- **cand-047** (es, r1) no me puedo desuscribir — severity low→medium · conf 0.90
  - Newsletter unsubscribe action fails with 404 page not found error. Duplicate of inc-0018 with same root cause.
- **cand-048** (en, r1) Orders created with $0 total — component checkout→payments · conf 0.95
  - Orders are created with $0.00 total when combining WELCOME15 coupon with gift card, resulting in loss of revenue. 37 affected orders indicates systemic pricing calculation bug.
- **cand-049** (en, r1) Zero-value orders in finance report — component checkout→payments · conf 0.95
  - Orders are recorded with zero total value due to a calculation bug when coupon and gift card are combined. This results in data inconsistency and revenue loss.
- **cand-050** (en, r1) coupon + giftcard = free stuff — category data→functional; component checkout→payments · conf 0.98
  - Users can exploit the coupon and gift card combination to obtain products for free. This is a critical functional bug causing revenue loss and is actively being shared.
- **cand-051** (en, r1) Gift card and coupon stacking zeroes the order total — category data→functional; component checkout→payments · conf 0.99
  - The gift card and coupon calculation logic is broken, causing orders to be zeroed out and fulfilled without payment. This is a critical financial and functional defect.
- **cand-052** (es, r1) El contador del carrito no baja al quitar productos — category functional→ui · conf 0.85
  - The cart badge displays stale item count after removal until page reload. This is a UI display issue; the actual cart is updated correctly.
- **cand-054** (es, r1) Badge del carrito desactualizado — category functional→ui · conf 0.90
  - The cart item count badge doesn't refresh on item deletion, though the cart data itself is correct. This is a UI synchronization issue.
- **cand-055** (es, r1) Ícono de carrito con cantidad incorrecta — category functional→ui · conf 0.85
  - The cart icon shows outdated item count after deletion, but entering the cart shows correct data. This is a display synchronization issue on mobile.
- **cand-074** (es, r1) El botón Pagar queda escondido detrás del teclado — component checkout→payments · conf 0.90
  - The pay button is hidden behind the keyboard on iPhone Safari with no scroll option, preventing users from completing checkout. The workaround of closing the keyboard exists but is poor UX.
- **cand-082** (es, r1) Los filtros de precio se pierden al regresar — severity medium→low · conf 0.80
  - Applied price filters are lost when navigating away from search results and returning, causing users to lose their filter state.
- **cand-106** (en, r1) Login endpoint has no rate limit — severity high→critical · conf 0.95
  - The login endpoint lacks rate limiting, allowing brute force attacks at scale (40k attempts recorded). This is a security vulnerability exposing accounts to unauthorized access attempts.
- **cand-117** (en, r1) App crashes opening saved cards on Android 12 — severity medium→high · conf 0.85
  - The app crashes when accessing saved cards on Android 12, but works on newer versions. This is a crash affecting a subset of users on one OS version.
- **cand-119** (en, r1) Sorting reviews by most recent does nothing — severity medium→low · conf 0.80
  - The 'Most recent' sorting option for reviews doesn't work, leaving the order unchanged. This is a functional defect in a non-core feature.
- **cand-126** (en, r1) Admin crashes exporting customers with emoji names — severity medium→high · conf 0.90
  - Customer export fails with a crash (500 error) when names contain emoji characters. This breaks admin functionality with a specific data input.
- **cand-132** (en, r1) Search box clears when switching tabs — severity low→medium · conf 0.85
  - The search query is lost when switching tabs, which is incorrect state management behavior in the search component.
- **cand-137** (en, r1) 'Member since' shows 1970 for old accounts — severity low→medium · conf 0.80
  - User profile displays incorrect 'Member since' date (1970) for old accounts due to data handling issue with legacy account creation dates.
- **hand-008** (es, r1) El botón de iniciar sesión queda oculto con el teclado abierto — severity medium→high · conf 0.85
  - The login button is hidden behind the keyboard on small screens and cannot be reached by scrolling, blocking user interaction with a core auth flow.
- **hand-009** (en, r1) Discount is applied twice after changing shipping method — category data→functional · conf 0.90
  - A promo discount is applied twice in the order total when changing shipping method, resulting in incorrect pricing calculations.
- **cand-011** (en, r2) Promo code shows badge but total unchanged — category functional→data · conf 0.88
  - Promo code shows as applied in the UI but discount is not reflected in the cart total until reapplied at checkout. The cart displays incorrect totals despite showing the discount badge.
- **cand-012** (es, r2) El cupón no descuenta del total — category functional→data · conf 0.88
  - Promo code displays a discount badge but the total price remains unchanged in the cart. The discount only applies when reapplied at checkout, indicating incorrect data display or calculation in the cart.
- **cand-013** (en, r2) discount not applied — category functional→data · conf 0.85
  - Promo code is accepted and shows a discount badge but the cart total does not reflect the discount. This is a data calculation or display issue in the cart.
- **cand-025** (es, r2) timeout al exportar en admin — severity medium→high · conf 0.85
  - Monthly order export times out with a 504 gateway error, requiring staff to work around it by exporting weekly instead. This is a performance issue affecting admin functionality.
- **cand-026** (en, r2) Product page says in stock but cart says sold out — severity medium→high · conf 0.90
  - Product page incorrectly displays items as in stock when admin stock is 0, but cart correctly rejects them. This is a data consistency issue where the catalog display is wrong.
- **cand-027** (en, r2) Stock badge wrong for electronics — severity medium→high · conf 0.85
  - Stock availability badge shows incorrect status (available when stock is zero) due to stale cache. This causes users to see wrong data about product availability.
- **cand-037** (es, r2) La app se cierra al pagar con Apple Pay — severity high→critical · conf 0.95
  - The app crashes when selecting Apple Pay during checkout, completely blocking payment for users who choose this method. Card payments work as a workaround.
- **cand-038** (es, r2) Crashea con apple pay — severity high→critical · conf 0.95
  - App crashes when attempting to use Apple Pay, forcing users to switch payment methods. This is the same defect as inc-0014.
- **cand-046** (es, r2) Link de darse de baja del newsletter da 404 — severity low→medium · conf 0.85
  - Newsletter unsubscribe link returns a 404 error, preventing users from unsubscribing. This is a functional defect in the notifications system.
- **cand-047** (es, r2) no me puedo desuscribir — severity low→medium · conf 0.85
  - Unsubscribe action in newsletter email returns 404, blocking user attempts to opt out. This is the same defect as inc-0018.
- **cand-048** (en, r2) Orders created with $0 total — component checkout→payments · conf 0.95
  - Combining WELCOME15 coupon with a gift card creates orders with $0 total that process and ship. This is a critical data integrity issue affecting revenue.
- **cand-049** (en, r2) Zero-value orders in finance report — component checkout→payments · conf 0.95
  - Orders with zero total due to coupon and gift card stacking represents data integrity loss; revenue is not captured and orders are fulfilled without payment.
- **cand-050** (en, r2) coupon + giftcard = free stuff — component checkout→payments · conf 0.95
  - Same issue as inc-0021: coupon and gift card combination results in zero-cost orders, allowing free fulfillment and financial loss.
- **cand-051** (en, r2) Gift card and coupon stacking zeroes the order total — category data→functional; component checkout→payments · conf 0.98
  - Gift card application logic incorrectly applies to pre-discount amount and clamps negative remainder to zero, allowing orders to be placed without payment.
- **cand-052** (es, r2) El contador del carrito no baja al quitar productos — category functional→ui · conf 0.90
  - Cart badge counter fails to update after item removal until page reload; the actual cart state is correct but the UI display is stale.
- **cand-054** (es, r2) Badge del carrito desactualizado — category functional→ui · conf 0.90
  - Cart badge quantity display is outdated after item deletion; actual cart content is correct so this is a display-only issue.
- **cand-055** (es, r2) Ícono de carrito con cantidad incorrecta — category functional→ui · conf 0.90
  - Cart icon badge shows stale count after deletion but cart contents display correctly; this is a UI synchronization issue.
- **cand-074** (es, r2) El botón Pagar queda escondido detrás del teclado — component checkout→payments · conf 0.85
  - The payment button becomes inaccessible behind the keyboard on iOS Safari, preventing users from completing checkout. This blocks the payment flow but has a workaround (close keyboard first).
- **cand-084** (es, r2) 'Recordarme' no funciona — severity medium→high · conf 0.85
  - The 'Remember me' feature does not persist the session, forcing users to log in repeatedly. This breaks the login flow for a subset of users on iOS.
- **cand-089** (es, r2) Error 500 al subir CSV de productos con acentos — category crash→functional · conf 0.80
  - The admin product import endpoint crashes with a 500 error when CSV contains accented characters, though a workaround exists (remove accents). This blocks admin functionality.
- **cand-106** (en, r2) Login endpoint has no rate limit — severity high→critical · conf 0.95
  - The login endpoint lacks rate limiting, allowing brute-force attacks with 40k attempts overnight against user accounts. This is a critical security vulnerability enabling account compromise.
- **cand-117** (en, r2) App crashes opening saved cards on Android 12 — severity medium→high · conf 0.90
  - The app crashes when opening saved cards on Android 12, blocking users from viewing payment methods. This is a crash affecting a profile feature on a specific OS version.
- **cand-119** (en, r2) Sorting reviews by most recent does nothing — severity medium→low · conf 0.85
  - Sorting reviews by 'Most recent' does not change the order, failing to implement the requested functionality. This is a non-core feature that doesn't block any primary flow.
- **cand-123** (en, r2) Shipping options unreadable in dark mode — severity medium→low · conf 0.90
  - Shipping option text is dark grey on black background in dark mode, making it unreadable. This is a UI accessibility and contrast issue that does not block functionality.
- **cand-132** (en, r2) Search box clears when switching tabs — severity low→medium · conf 0.85
  - The search box clears when navigating between tabs, causing the user's input to be lost. This is a functional defect in the search component that disrupts the user experience.
- **cand-137** (en, r2) 'Member since' shows 1970 for old accounts — severity low→medium · conf 0.80
  - The 'Member since' date displays incorrectly as 1970 for old accounts, indicating a data display or parsing error. This is a data integrity issue affecting user profile information.
- **hand-008** (es, r2) El botón de iniciar sesión queda oculto con el teclado abierto — severity medium→high · conf 0.88
  - The login button is hidden behind the keyboard on small screens with no scroll capability, making it impossible to submit the form. This is a UI/layout issue in the auth flow that blocks login for affected users.
- **hand-009** (en, r2) Discount is applied twice after changing shipping method — category data→functional · conf 0.92
  - A promo discount is subtracted twice in the order total when changing shipping methods, resulting in an incorrect (lower) total. This is a functional defect in the checkout calculation logic.
