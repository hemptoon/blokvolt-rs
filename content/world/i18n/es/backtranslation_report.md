# Back-translation QA — Spanish UI strings (60)

Method: blind back-translation of bt_es.json → bt_back.json, then compared against bt_en.json by id.

**Summary: ok 53 · minor 5 · mismatch 2**

Mismatch ids: prices:pay_sub, prices:plan_sub

## Mismatch

**prices:pay_sub**
- EN: Plans: {list}.
- ES: Suscripciones: {list}.
- back_en: Subscriptions: {list}.
- Issue: wrong term. "Plans" (tariff plans, which may include pay-as-you-go/membership plans) became "subscriptions".
- Fix: `Planes: {list}.`

**prices:plan_sub**
- EN: Plan
- ES: Suscripción
- back_en: Subscription
- Issue: same wrong term as pay_sub (column/label for a tariff plan).
- Fix: `Plan`

## Minor

**pages:nav_hub**
- EN: Charging stations
- ES: Puntos de carga
- back_en: Charging points
- Issue: different term; now identical to map:c_pts ("Charging points"), so two different EN labels collapse into one.
- Fix: `Estaciones de carga`

**prices:cars_note**
- EN: …in winter about 20–30 % more…
- ES: …en invierno, entre un 20 y un 30 % más…
- back_en: …in winter 20–30% more…
- Issue: hedge "about" dropped; estimate reads as exact.
- Fix: `…en invierno, aproximadamente entre un 20 y un 30 % más…`

**map:ch_ft_checked**
- EN: checked
- ES: verificado
- back_en: verified
- Issue: "verified" is a stronger claim than "checked".
- Fix: `comprobado`

**pages:balkan_note**
- EN: These countries have their own BlokVolt pages with checked data.
- ES: Estos países tienen sus propias páginas de BlokVolt con datos verificados.
- back_en: These countries have their own BlokVolt pages with verified data.
- Issue: same "checked" → "verified" strengthening.
- Fix: `Estos países tienen sus propias páginas de BlokVolt con datos comprobados.`

**shell:about_more**
- EN: How the data is collected and checked
- ES: Cómo se recopilan y verifican los datos
- back_en: How the data is collected and verified
- Issue: same "checked" → "verified"; keep the term consistent with the two items above.
- Fix: `Cómo se recopilan y comprueban los datos`

## Notes
- Every other string keeps its meaning; differences are only word order or synonyms (e.g. "registries/registers", "news reports/news items", "Power unknown/Unknown power", "Last confirmed/Last confirmation").
- Placeholders ({n}, {m}, {c}, {list}, {net}, {country_u}, {n_countries}, {shown}, {total}, {x}) and the HTML links in map:ch_ft_data match the EN source.
