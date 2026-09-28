---
key: road
slug: udhetimi/
order: 6
nav: Udhëtimi
icon: road
priority: 0.7
title: Me veturë elektrike nëpër Kosovë — autostradat dhe pikat kufitare | BlokVolt
description: Autostradat R6 dhe R7 pa pagesë, ku ka karikues të shpejtë në qytetet përgjatë rrugëve kryesore, pikat kufitare dhe rruga drejt bregdetit shqiptar.
h1: Me veturë elektrike nëpër Kosovë
lead: Autostradat R6 dhe R7, karikuesit e shpejtë në qytete, pikat kufitare dhe rruga drejt detit.
card: Autostradat pa pagesë, karikuesit DC në qytete dhe pikat kufitare.
related: map, prices, home
---
{% set built = LOCALS_ALL|map(attribute='key')|list %}
Asnjë burim nuk tregon karikues në vetë autostradat R6 dhe R7. Mbushja e shpejtë bëhet në qytete dhe në pika karburanti pranë rrugëve kryesore, prandaj udhëtimi duhet planifikuar.

Sipas burimit më të fundit të gjetur ([{{ C.tolls.src_label }}]({{ C.tolls.src }})), {{ C.tolls.text }}

{{ w.pairs(C.road, 'Ku', 'Çfarë dihet') }}

Në [hartë]({{ PAGES.map.path }}), më {{ M.retrieved }}, janë {{ num(M.dc50) }} karikues DC nga 50 kW e lart: në Prishtinë, Fushë Kosovë, Lipjan, Drenas, Podujevë, Pejë, Gjilan, Suharekë dhe Prizren (OpenStreetMap dhe Open Charge Map, të pakontrolluar).

## Pikat kufitare

Policia e Kosovës numëron 16 pika kufitare. Në autostrada janë **Vërmica** (R7, drejt Shqipërisë; në anën shqiptare Morinë) dhe **Hani i Elezit** (R6, drejt Shkupit). Lista e Policisë sipas drejtorive rajonale:

{{ w.pairs(C.borders, 'Drejtoria rajonale', 'Pikat kufitare') }}

Asnjë burim nuk tregon karikues të shpejtë pranë pikave kufitare. Shikoni [hartën]({{ PAGES.map.path }}) dhe karikuesit në anën tjetër: {% if 'al' in built %}[Shqipëria](/al/harta/){% else %}[Shqipëria](/albania/){% endif %}, {% if 'mk' in built %}[Maqedonia e Veriut](/mk/mapa/){% else %}[Maqedonia e Veriut](/north-macedonia/){% endif %}, [Mali i Zi](/me/mapa/) dhe [Serbia](https://www.blokvolt.rs/mapa/).

## Drejt bregdetit shqiptar

Nga Vërmica R7 vazhdon në Shqipëri si autostrada A1 „Rruga e Kombit” drejt Tiranës dhe Durrësit. Në A1 kalimi paguhet: {{ C.a1.text }} ([{{ C.a1.src_label }}]({{ C.a1.src }})). Asnjë burim nuk tregon karikues të shpejtë në vetë A1. ECHARGE shkruan se ka pika edhe në Shqipëri, pa emra vendesh, dhe nuk thuhet nëse çmimet e saj vlejnë edhe atje. Karikuesit në Shqipëri: {% if 'al' in built %}[harta](/al/harta/){% else %}[faqja për Shqipërinë](/albania/), në anglisht{% endif %}.

## Këshilla

- **Karikoni para autostradës.** Para R7 drejt Shqipërisë karikoni në Prishtinë, Suharekë ose Prizren; para R6 drejt Shkupit, në Prishtinë ose Ferizaj.
- **Pyetni për çmimin.** Vetëm ECHARGE publikon çmime; te operatorët e tjerë pyetni para karikimit.
- **Aplikacionet.** ECHARGE dhe RapidCharge përmendin aplikacionet e tyre: instalojini dhe shtoni kartelën para udhëtimit.
- **Lidhësi GB/T.** ECHARGE ka GB/T vetëm „në disa stacione”. Nëse vetura juaj ka prizë GB/T, kontrolloni stacionin para nisjes.

{{ w.sources(C.road_srcs) }}
