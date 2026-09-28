---
key: stats
slug: statistika/
order: 7
nav: Statistika
icon: chart
priority: 0.6
title: Električni automobili u BiH u brojkama — broj vozila, prodaja, punjači | BlokVolt
description: Broj električnih automobila u Bosni i Hercegovini od 2021. (Eurostat), udio u novim registracijama (BHAS), broj javnih punjača po izvorima. Podaci za preuzimanje (CSV).
h1: Električni automobili u BiH u brojkama
lead: Koliko električnih automobila vozi Bosnom i Hercegovinom, koliki je njihov udio u novim registracijama i koliko je javnih punjača — iz službenih izvora, s datumom.
card: Broj vozila od 2021., udio u novim registracijama i procjene broja punjača; CSV.
schema: Dataset
related: map, subsidies, prices
---
{{ w.stats([(num(C.fleet.series[-1][1]), pl(C.fleet.series[-1][1], 'električni putnički automobil', 'električna putnička automobila', 'električnih putničkih automobila') ~ ' krajem 2025. (Eurostat)'),
            ('1,1 %', 'udio električnih u novim putničkim automobilima u decembru 2025. (BHAS)'),
            (num(M.n), pl(M.n, 'javni punjač', 'javna punjača', 'javnih punjača') ~ ' na mapi')]) }}

## Koliko ih vozi

{{ w.bars(C.fleet.series, title='Električni putnički automobili (BEV) krajem godine. Izvor: Eurostat, road_eqs_carpda, ažurirano ' ~ C.fleet.src_date) }}

Krajem 2025. BiH je imala **{{ num(C.fleet.series[-1][1]) }}** {{ pl(C.fleet.series[-1][1], 'električni putnički automobil', 'električna putnička automobila', 'električnih putničkih automobila') }}, {{ C.fleet.growth_2025 }} % više nego godinu prije i devet puta više nego 2021. Od toga je {{ num(C.fleet.phys_2025) }} u vlasništvu fizičkih, a {{ num(C.fleet.legal_2025) }} pravnih lica. Izvor: [{{ C.fleet.src_label }}]({{ C.fleet.src }}).

## Udio u novim registracijama

Agencija za statistiku BiH (BHAS) objavljuje udio električnih vozila u novim putničkim automobilima po mjesecima:

{{ w.pairs(C.bhas, 'Mjesec', 'Električni automobili među novim putničkim') }}

U 2025. prvi put registrovanih novih vozila bilo je {{ num(C.bhas_2025_new) }}, 8,5 % više nego 2024. Godišnji udio električnih BHAS ne objavljuje ([BHAS]({{ C.bhas_2025_src }})).

## Javni punjači

Službenog broja javnih punjača u BiH nema. Brojke iz različitih izvora:

{% set rows = [] %}{% for a, b, u in C.charger_counts %}{% set _ = rows.append((a, b)) %}{% endfor %}{{ w.pairs(rows, 'Izvor', 'Broj') }}

Naša [mapa]({{ PAGES.map.path }}) prikazuje {{ num(M.n) }} {{ pl(M.n, 'punjač', 'punjača', 'punjača') }} iz OpenStreetMapa i Open Charge Mapa, od toga {{ num(M.dc50) }} s DC punjenjem od 50 kW naviše.

## Podaci za preuzimanje

[{{ C.csv.file }}](/ba/{{ C.csv.file }}) — broj električnih putničkih automobila po godinama (Eurostat), CSV sa separatorom „;”. Licenca CC BY 4.0: slobodno koristite uz navođenje izvora „BlokVolt (blokvolt.com), prema Eurostatu”.
