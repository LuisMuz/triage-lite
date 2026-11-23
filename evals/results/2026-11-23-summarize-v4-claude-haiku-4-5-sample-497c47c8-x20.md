# Summarize eval: summarize/v4 on sample-497c47c8

Model `global.anthropic.claude-haiku-4-5-20251001-v1:0`, 20 repeats per language, 63 calls, $0.385. Created 2026-11-23T18:35:17+00:00.

| lang | template fallbacks | passed on first draft | passed on re-ask |
|---|---|---|---|
| es | 0/20 (0%) | 14/20 (70%) | 6/20 (30%) |
| en | 5/20 (25%) | 4/20 (20%) | 11/20 (55%) |

## Problems in rejected drafts

- number word: 42

Most frequent:

- number word 'three': 24
- number word 'four': 9
- number word 'tres': 6
- number word 'five': 2
- number word 'cuatro': 1

## Sentences that broke a rule

- en, repeat 1, 'three': Three components account for the most incidents:
- en, repeat 2, 'three': Three components account for the most incidents: checkout with {{component.checkout.count}} incidents, notifications with {{component.notifications.count}}, and search with {{component.search.count}}.
- en, repeat 2, 'four': Four critical incidents require immediate attention: inc-0003 (checkout crash on order confirmation), inc-0005 (double payment charge), inc-0010 (API leaking user addresses), and inc-0016 (password exposed in admin logs).
- en, repeat 3, 'three': Three components account for the highest incident density:
- en, repeat 3, 'three': Three bugs were reported multiple times: inc-0003 ({{reports.inc_0003}} reports), inc-0006 ({{reports.inc_0006}} reports), and inc-0009 ({{reports.inc_0009}} reports).
- en, repeat 3, 'four': Four critical incidents require immediate attention:
- en, repeat 4, 'four': Four critical incidents need immediate attention:
- en, repeat 4, 'three': Three components account for the majority of incidents: checkout with {{component.checkout.count}} incidents including {{component.checkout.severity.critical.count}} critical and {{component.checkout.severity.high.count}} high; notifications with {{component.notifications.count}} incidents including {{component.notifications.severity.medium.count}} medium and {{component.notifications.severity.low.count}} low; search with {{component.search.count}} incidents including {{component.search.severity.high.count}} high and {{component.search.severity.medium.count}} medium.
- en, repeat 5, 'three': Three components account for the majority of incidents:
- en, repeat 5, 'four': Four critical incidents pose immediate risks and should be prioritized:
- en, repeat 5, 'five': After these, address the five high-severity incidents: inc-0001 (Google login broken), inc-0002 (discount codes ignored in cart), inc-0006 (search quality degraded by accent handling), inc-0012 (order history crashes app), and inc-0019 (free shipping incorrectly applied to international orders).
- es, repeat 6, 'tres': Tres bugs fueron reportados múltiples veces:
- en, repeat 7, 'three': Three components account for the highest incident load:
- en, repeat 7, 'three': Three bugs were reported multiple times:
- en, repeat 8, 'three': Three bugs were reported more than once: inc-0003 ({{reports.inc_0003}} reports), inc-0006 ({{reports.inc_0006}} reports), and inc-0009 ({{reports.inc_0009}} reports).
- en, repeat 9, 'four': Four critical incidents require immediate attention:
- en, repeat 9, 'three': Three components dominate the incidents:
- es, repeat 10, 'tres': Tres componentes concentran la mayoría de los incidentes:
- es, repeat 10, 'tres': Tres defectos fueron reportados múltiples veces:
- en, repeat 11, 'three': Three components concentrate the most incidents:
- … and 22 more in the JSON result

## Reports to review

Read these for claims the facts don't support; the grounding check only covers numbers and incident IDs.

### es, repeat 1

````markdown
# Informe de triage QA

Lote `sample-497c47c8` · redactado por el modelo global.anthropic.claude-haiku-4-5-20251001-v1:0 con el prompt summarize/v4

## Resumen general

Se procesaron 20 incidentes, con 20 clasificados automáticamente y 0 requieren triaje manual. La clasificación identificó 17 bugs distintos tras agrupar reportes duplicados: 3 bugs fueron reportados múltiples veces, generando 3 reportes redundantes.

## Severidad

Los incidentes clasificados se distribuyen así:
- 5 críticos (25,0 %)
- 5 altos (25,0 %)
- 7 medios (35,0 %)
- 3 bajos (15,0 %)

## Componentes más afectados

Los 3 componentes con más incidentes son checkout, notifications y search. El checkout concentra 2 críticos y 1 altos. Notifications tiene 2 medios y 1 bajos. Search presenta 1 altos y 2 medios.

## Incidentes duplicados

Los siguientes bugs fueron reportados múltiples veces:
- Error 500 al confirmar el pedido (inc-0003): 2 reportes
- Search ignores accents (inc-0006): 2 reportes
- Notificación push duplicada (inc-0009): 2 reportes

## Qué reparar primero

Priorizar estos incidentes críticos por su impacto en usuarios y funcionalidad:
- inc-0003: Error 500 al confirmar el pedido (checkout)
- inc-0005: Pago con tarjeta se cobra dos veces (payments)
- inc-0010: API returns other user's addresses (api)
- inc-0016: Contraseña visible en logs del admin (admin)

Luego abordar los altos en checkout e integración de pagos para evitar pérdidas de usuarios durante la compra.
````

### es, repeat 2

````markdown
# Informe de triage QA

Lote `sample-497c47c8` · redactado por el modelo global.anthropic.claude-haiku-4-5-20251001-v1:0 con el prompt summarize/v4

## Resumen de la evaluación

Se han triado 15 incidentes en este lote. El modelo clasificó automáticamente 20 incidentes, mientras que 0 requieren revisión manual. Se identificaron 17 bugs distintos tras agrupar reportes duplicados: 3 bugs fueron reportados más de una vez, sumando 3 reportes adicionales.

## Severidad

Se encontraron 5 incidentes críticos (25,0 % de los clasificados). Los incidentes de alta severidad suman 5 (25,0 %), mientras que 7 se clasificaron como medios (35,0 %) y 3 como bajos (15,0 %).

## Componentes más afectados

Los 3 componentes con más incidentes son:
- Checkout: 3 incidentes, con 2 críticos y 1 de alta severidad
- Notifications: 3 incidentes, siendo 2 medios y 1 bajos
- Search: 3 incidentes, con 1 de alta severidad y 2 medios

## Reportes duplicados

Los bugs más reportados son:
- Error al confirmar pedido (inc-0003): 2 reportes
- Búsqueda ignora acentos (inc-0006): 2 reportes
- Notificación push duplicada (inc-0009): 2 reportes

## Qué arreglar primero

Priorizar estos incidentes críticos y de alto impacto:
- inc-0003: Error 500 al confirmar el pedido
- inc-0005: Pago con tarjeta se cobra dos veces
- inc-0010: API returns other user's addresses
- inc-0016: Contraseña visible en logs del admin
- inc-0006: Search ignores accents
- inc-0001: No puedo iniciar sesión con Google
- inc-0002: Cart total ignores discount code
- inc-0012: App crashes when opening order history
- inc-0019: El cupón de envío gratis se aplica a pedidos internacionales
````

### es, repeat 3

````markdown
# Informe de triage QA

Lote `sample-497c47c8` · redactado por el modelo global.anthropic.claude-haiku-4-5-20251001-v1:0 con el prompt summarize/v4

## Resumen del lote

Se procesaron 20 incidentes, 20 fueron clasificados automáticamente y 0 requieren clasificación manual. 17 bugs distintos fueron identificados después de fusionar reportes duplicados.

## Severidad

Los incidentes clasificados se distribuyen así:
- 5 críticos (25,0 %)
- 5 altos (25,0 %)
- 7 medios (35,0 %)
- 3 bajos (15,0 %)

## Componentes más afectados

Los componentes con más incidentes son:
- Checkout: 3 incidentes (2 críticos, 1 altos)
- Notificaciones: 3 incidentes (2 medios, 1 bajos)
- Búsqueda: 3 incidentes (1 altos, 2 medios)

## Reportes duplicados

Se encontraron 3 reportes duplicados en 3 bugs distintos:
- inc-0003 (error 500 al confirmar pedido): 2 reportes
- inc-0006 (búsqueda ignora acentos): 2 reportes
- inc-0009 (notificación duplicada): 2 reportes

## Qué arreglar primero

Priorizar estos incidentes críticos y de alto impacto:
- inc-0003: Error 500 impide completar compras
- inc-0005: Cargo doble en pagos
- inc-0010: Exposición de datos de dirección de otros usuarios
- inc-0016: Contraseña visible en logs
- inc-0006: Búsqueda ignora acentos (2 reportes)
- inc-0001: Fallo en inicio de sesión con Google
- inc-0002: Código de descuento ignorado en carrito
- inc-0019: Cupón de envío gratis se aplica incorrectamente
````

### en, repeat 1

````markdown
# QA triage report

Batch `sample-497c47c8` · written by model global.anthropic.claude-haiku-4-5-20251001-v1:0 with prompt summarize/v4

## Overview

The batch contains 20 incidents, of which 20 were automatically classified and 0 require manual review. After deduplication, 17 distinct bugs remain. Duplicate reports account for 3 of the total incidents, covering 3 bugs that were reported more than once.

## Severity distribution

5 incidents are critical (25.0% of classified), 5 are high (25.0%), 7 are medium (35.0%), and 3 are low (15.0%).

## Most affected components

The components with the most incidents are:
- Checkout: 3 incidents, including 2 critical and 1 high
- Notifications: 3 incidents, including 2 medium and 1 low
- Search: 3 incidents, including 1 high and 2 medium

## Duplicate reports

Several incidents were reported multiple times:
- inc-0003: 2 reports
- inc-0006: 2 reports
- inc-0009: 2 reports

## What to fix first

Address the critical incidents immediately:
- inc-0003 (checkout crash on order confirmation)
- inc-0005 (payment charged twice)
- inc-0010 (API exposes other users' addresses)
- inc-0016 (admin password visible in logs)

Then prioritize high-severity issues affecting checkout and authentication:
- inc-0019 (free shipping voucher applied incorrectly to international orders)
- inc-0001 (Google login failure)
- inc-0002 (cart total ignores discount code)
````

### en, repeat 2

````markdown
# QA triage report

Batch `sample-497c47c8` · written by model global.anthropic.claude-haiku-4-5-20251001-v1:0 with prompt summarize/v4

## Overview

A total of 20 incidents were submitted for triage, with 20 automatically classified and 0 awaiting manual review. After merging duplicate reports, 17 distinct bugs remain, with 3 bugs reported multiple times across 3 duplicate submissions.

## Severity distribution

Critical incidents dominate the batch at 5 (25.0%), followed by high severity at 5 (25.0%). Medium severity incidents account for 7 (35.0%), and 3 (15.0%) are classified as low severity.

## Most affected components

The components with the most incidents are checkout (3 incidents), notifications (3 incidents), and search (3 incidents). Checkout is especially critical with 2 critical issues. Notifications has 2 medium and 1 low severity incidents, while search shows 1 high and 2 medium severity problems.

## Duplicate reports

Several incidents were reported multiple times. Bugs reported more than once: inc-0003 (2 reports), inc-0006 (2 reports), and inc-0009 (2 reports).

## What to fix first

The 4 critical incidents require immediate attention: inc-0003 (500 error on order confirmation in checkout), inc-0005 (double charge on card payments), inc-0010 (API exposing other users' addresses), and inc-0016 (admin logs showing passwords).
````

### en, repeat 3

````markdown
# QA triage report

Batch `sample-497c47c8` · written by model global.anthropic.claude-haiku-4-5-20251001-v1:0 with prompt summarize/v4

## Overview

20 incidents were submitted for triage, of which 20 were automatically classified and 0 require manual review. 17 distinct bugs were identified after merging duplicate reports.

## Severity distribution

Critical incidents dominate the batch: 5 are classified as critical (25.0%), 5 as high (25.0%), 7 as medium (35.0%), and 3 as low (15.0%).

## Most affected components

The checkout, notifications, and search components account for the most incidents. Checkout has 2 critical incidents and 1 high-severity ones. Notifications combines 2 medium and 1 low-severity issues. Search shows 1 high and 2 medium incidents.

## Duplicates

3 bugs were reported multiple times. Notably, inc-0003 has 2 reports, inc-0006 has 2 reports, and inc-0009 has 2 reports, indicating these issues affect multiple users.

## What to fix first

Prioritize these critical incidents: inc-0003 (checkout crash on order confirmation), inc-0005 (double charge on card payments), inc-0010 (API exposing other users' addresses), and inc-0016 (admin password visible in logs). These pose immediate risk to revenue, data integrity, and security.
````
