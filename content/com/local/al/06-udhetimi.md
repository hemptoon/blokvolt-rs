---
key: road
slug: udhetimi/
order: 6
nav: Udhëtimi
icon: road
priority: 0.7
title: Me makinë elektrike nëpër Shqipëri — karikuesit, kufiri, tragetet | BlokVolt
description: Karikuesit në rrugët Tiranë–Durrës–Fier–Vlorë, në jug dhe në veri sipas operatorëve, pagesa në Rrugën e Kombit, pikat kufitare dhe tragetet për në Itali.
h1: Me makinë elektrike nëpër Shqipëri
lead: Karikuesit në rrugët kryesore sipas listave të operatorëve, pagesa në Rrugën e Kombit, pikat kufitare dhe tragetet.
card: Karikuesit në rrugët kryesore, Rruga e Kombit, kufiri dhe tragetet.
related: map, prices, home
---
Listat e vendndodhjeve i publikojnë dy rrjete: VEGA CHARGING dhe PlugoAL (ky i fundit vetëm qytetet). Në Rrugën e Kombit dhe në Kukës nuk u konfirmua asnjë karikues i shpejtë. Pikat e tjera janë në [hartë]({{ PAGES.map.path }}).

{{ w.pairs(C.road, 'Rruga', 'Karikuesit sipas operatorëve') }}

## Rruga e Kombit (A1)

{{ C.toll.text }}

Në Kosovë rruga vazhdon si autostrada R7 për në Prishtinë. Sipas burimit më të fundit që u gjet, autostradat atje janë pa pagesë (Radio Evropa e Lirë, 16.05.2021).

## Pikat kufitare

{{ w.pairs(C.borders, 'Pika kufitare', 'Ku të karikoni para kufirit') }}

{% set L = LOCALS_ALL|map(attribute='key')|list %}
{% set nb = [] %}
{% if 'xk' in L %}{% set _ = nb.append('[Kosova](/xk/harta/)') %}{% endif %}
{% if 'me' in L %}{% set _ = nb.append('[Mali i Zi](/me/mapa/)') %}{% endif %}
{% if 'mk' in L %}{% set _ = nb.append('[Maqedonia e Veriut](/mk/mapa/)') %}{% endif %}
Emrat e pikave me Greqinë janë nga njoftimi i Policisë së Shtetit (26.07.2026); të tjerat nuk u verifikuan në një listë zyrtare. {{ ('Karikuesit në anën tjetër të kufirit: ' ~ nb|join(', ') ~ '.') if nb else '' }}

## Tragetet

{{ w.pairs(C.ferries, 'Linja', 'Çfarë dihet') }}

Për rregullat e kompanisë së tragetit për makinat elektrike pyesni kur blini biletën.

## Këshilla

- **Rruga e Kombit.** Në vetë rrugën A1 karikues i shpejtë nuk u konfirmua: për Kukësin dhe për Kosovën nisuni nga Tirana me bateri të mbushur.
- **Bregdeti jugor.** Në jug të Vlorës, sipas listës së VEGA CHARGING, ka karikues në Lukovë dhe së shpejti në Sarandë. Karikoni në Vlorë ose në Fier para rrugës bregdetare.
- **Prizat.** Karikuesit DC të VEGA CHARGING kanë dy priza, GB/T dhe CCS2; PlugoAL ka CCS2.
- **Pagesa.** PlugoAL paguhet në aplikacionin web, iCharge.app në aplikacion dhe VEGA CHARGING me kartën e vet. Mbani gati edhe kartën bankare. [Si paguhet]({{ PAGES.prices.path }})
- **Çmimi.** Rrjetet nuk publikojnë çmime: kontrollojeni në aplikacion ose në stacion para karikimit.

{{ w.sources(C.road_srcs) }}
