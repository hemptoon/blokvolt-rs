---
key: electricity
slug: cmimi-i-energjise/
order: 5
nav: Çmimi i energjisë
icon: bolt
priority: 0.85
title: Çmimi i energjisë elektrike në Shqipëri 2026 – kWh për familjet | BlokVolt
description: Kilovat-ora për familjet me TVSH: 10,2 lekë deri në 700 kWh në muaj dhe 11,4 lekë mbi 700 kWh për gjithë konsumin. Pragu, karikimi i makinës dhe burimet e ERE-së.
kicker: Energjia për familjet
h1: Çmimi i energjisë elektrike në Shqipëri në vitin 2026
lead: Sa paguan një familje për një kilovat-orë energji elektrike te furnizuesi universal i grupit OSHEE, sipas tarifave të ERE-së për vitin 2026 — me TVSH, me pragun e 700 kWh në muaj — dhe sa kushton karikimi i makinës elektrike në shtëpi.
card: Kilovat-ora me TVSH deri dhe mbi 700 kWh në muaj, pragu që e shtrenjton gjithë faturën dhe karikimi i makinës në shtëpi.
checked: 10.11.2026
checked_iso: 2026-11-10
related: home, prices, map
---
{% set P = C.power %}
{% set E = C.electricity %}
{% set a = P.tariffs|selectattr('id', 'equalto', 'deri700')|first %}
{% set b = P.tariffs|selectattr('id', 'equalto', 'mbi700')|first %}
{% set X = P.example %}
<div class="sum" markdown="1">
- **{{ money(a.allin) }}** për kWh me TVSH kur familja konsumon deri në 700 kWh në muaj
- **{{ money(b.allin) }}** për kWh mbi 700 kWh — për **gjithë konsumin** e muajit, jo vetëm për pjesën mbi prag
- **Një çmim gjatë gjithë ditës**: për familjet nuk ka tarifë nate
- **{{ money(a.allin * 18.7, 0) }}** energji për 100 km, nëse familja mbetet deri në 700 kWh
</div>

## Çmimi i kilovat-orës për familjet

| Konsumi në muaj | Pa TVSH | Me TVSH |
|---|---|---|
| Deri në 700 kWh | {{ num(a.base, 1) }} | **{{ num(a.allin, 1) }}** |
| Mbi 700 kWh, për gjithë konsumin | {{ num(b.base, 1) }} | **{{ num(b.allin, 1) }}** |

Çmimet janë në lekë për kWh. Furnizuesi universal i familjeve është shoqëria e grupit OSHEE, kurse çmimet i miraton Enti Rregullator i Energjisë (ERE) me Vendimin nr. 322, datë 15.12.2025, për periudhën 1 janar – 31 dhjetor 2026. ERE-ja i ka shpallur këto çmime pa TVSH; mbi to shtohet TVSH {{ P.vat }} %.

- **Pragu i 700 kWh.** {{ P.blocks }}
- **Pa tarifë nate.** {{ P.nt_hours }}
- **Pa tarifë fikse.** Tabela e ERE-së për vitin 2026 nuk ka tarifë fikse mujore për familjet.

## Si e ndikon makina pragun e 700 kWh

Te tarifat me blloqe në disa vende të rajonit, për shembull në Bosnjë dhe Hercegovinë, çmimi më i lartë vlen vetëm për kWh mbi kufi. Në Shqipëri, kur familja kalon 700 kWh, çmimi 9,5 lekë pa TVSH vlen për të gjithë muajin, që nga kilovat-ora e parë.

**Shembull.** Shtëpia konsumon {{ X.house }} kWh në muaj dhe makina merr nga priza edhe {{ X.ev_kwh }} kWh, mjaftueshëm për rreth {{ num(1070) }} km. Shumat janë me TVSH.

- Pa makinën: {{ X.house }} kWh × {{ num(a.allin, 1) }} = **{{ money(X.before, 0) }}**.
- Me makinën: {{ X.total }} kWh × {{ num(b.allin, 1) }} = **{{ money(X.after, 0) }}**.
- Fatura rritet me {{ money(X.diff, 0) }}, pra çdo kilovat-orë e makinës kushton në fakt **{{ num(X.per_kwh, 1) }} lekë**, jo {{ num(a.allin, 1) }}.
- Nëse familja mbetet deri në 700 kWh edhe me makinën, {{ X.ev_kwh }} kWh kushtojnë vetëm {{ money(X.stay, 0) }}.

Prandaj ia vlen të shikohet konsumi i zakonshëm i shtëpisë në faturat e OSHEE-së para se të vendoset sa karikohet makina në shtëpi.

## Sa kushtojnë 100 kWh

| Konsumi në muaj | 100 kWh me TVSH |
|---|---|
| Deri në 700 kWh | {{ money(a.allin * 100, 0) }} |
| Mbi 700 kWh | {{ money(b.allin * 100, 0) }} |

## Karikimi i makinës elektrike në shtëpi

Shembull: në bateri hyjnë 40 kWh, rreth 235 km me konsum prej 17 kWh për 100 km. Për shkak të humbjeve gjatë karikimit (rreth 10 %), nga matësi merren 44 kWh. Kjo kushton:

- deri në 700 kWh në muaj: **{{ money(a.allin * 44, 0) }}**;
- mbi 700 kWh në muaj: **{{ money(b.allin * 44, 0) }}**, plus shtrenjtimi i pjesës tjetër të faturës (shih shembullin më lart).

Për {{ num(1200) }} km në muaj makina merr nga matësi rreth 224 kWh: {{ money(a.allin * 224.4, 0) }} me çmimin deri në 700 kWh dhe {{ money(b.allin * 224.4, 0) }} me çmimin mbi 700 kWh. Llogaritja për makinën tuaj: [kalkulatori i karikimit në shtëpi]({{ PAGES.home.path }}).

## Tarifa për karikuesit publikë

{{ C.station_tariff.text }} Çmimet që paguajnë shoferët në karikuesit publikë janë te [çmimet e karikimit]({{ PAGES.prices.path }}).

<details markdown="1"><summary>Si është llogaritur</summary>

- **Çmimi me TVSH:** çmimi i ERE-së × 1,20. Deri në 700 kWh: 8,5 × 1,20 = {{ num(a.allin, 1) }} lekë; mbi 700 kWh: 9,5 × 1,20 = {{ num(b.allin, 1) }} lekë.
- **Pragu:** sipas ERE-së, çmimi 9,5 lekë vlen për gjithë sasinë e konsumuar në muaj, duke filluar nga kWh e parë.
- **Makina:** 17 kWh për 100 km dhe 10 % humbje gjatë karikimit, pra 18,7 kWh nga matësi për 100 km.
- **Nuk përfshihen:** detyrime të tjera në faturë që nuk lidhen me kWh, nëse ka.

</details>

## Pyetje të shpeshta

<details markdown="1">
<summary>Sa kushton një kilovat-orë energji elektrike në Shqipëri në vitin 2026?</summary>

Për familjet: {{ money(a.allin) }} me TVSH ({{ num(a.base, 1) }} lekë pa TVSH) kur konsumi i muajit është deri në 700 kWh, dhe {{ money(b.allin) }} me TVSH ({{ num(b.base, 1) }} lekë pa TVSH) për gjithë konsumin kur kalon 700 kWh.

</details>

<details markdown="1">
<summary>A ka tarifë nate për familjet?</summary>

Jo. Në tabelën e ERE-së për vitin 2026 familjet kanë një çmim të vetëm gjatë gjithë ditës; orari pik vlen vetëm për klientët jofamiljarë dhe për pikat e karikimit mbi 11 kW.

</details>

<details markdown="1">
<summary>Çfarë ndodh kur konsumi kalon 700 kWh në muaj?</summary>

Çmimi 9,5 lekë pa TVSH ({{ num(b.allin, 1) }} me TVSH) vlen për gjithë konsumin e muajit, jo vetëm për kilovat-orët mbi 700. Me {{ X.house }} kWh të shtëpisë dhe {{ X.ev_kwh }} kWh të makinës, fatura rritet nga {{ money(X.before, 0) }} në {{ money(X.after, 0) }}.

</details>

<details markdown="1">
<summary>Sa kushton karikimi i makinës elektrike në shtëpi?</summary>

Për 100 km duhen rreth 18,7 kWh nga matësi: {{ money(a.allin * 18.7, 0) }} nëse familja mbetet deri në 700 kWh dhe {{ money(b.allin * 18.7, 0) }} me çmimin mbi 700 kWh — por atëherë shtrenjtohet edhe pjesa tjetër e faturës.

</details>

## Burimet dhe kontrolli

Çmimet u kontrolluan më {{ E.checked }} në faqet e ERE-së dhe të OSHEE-së. Kontrolli i radhës: {{ E.next_check }}.

{{ w.sources(E.sources) }}
