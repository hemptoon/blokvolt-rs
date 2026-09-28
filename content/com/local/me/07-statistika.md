---
key: stats
slug: statistika/
order: 7
nav: Statistika
icon: chart
priority: 0.6
title: Električni automobili u Crnoj Gori u brojkama | BlokVolt
description: Broj električnih automobila u Crnoj Gori (Eurostat), nove registracije 2025., broj javnih punjača i snaga po nacrtu nacionalnog okvira. Podaci za preuzimanje (CSV).
h1: Električni automobili u Crnoj Gori u brojkama
lead: Koliko električnih automobila vozi Crnom Gorom, koliko ih je novih i koliko je javnih punjača — iz službenih izvora, s datumom.
card: Broj vozila, nove registracije i punjači; CSV.
schema: Dataset
related: map, subsidies, prices
---
{{ w.stats([(num(C.fleet.series[-1][1]), pl(C.fleet.series[-1][1], 'električni putnički automobil', 'električna putnička automobila', 'električnih putničkih automobila') ~ ' krajem 2025. (Eurostat)'),
            (num(C.new_bev.y2025), pl(C.new_bev.y2025, 'novi električni automobil', 'nova električna automobila', 'novih električnih automobila') ~ ' u 2025. — ' ~ C.new_bev.share ~ ' od ' ~ num(C.new_bev.y2025_total) ~ ' novih'),
            (num(C.points.n), pl(C.points.n, 'javno mjesto', 'javna mjesta', 'javnih mjesta') ~ ' za punjenje (nacrt nacionalnog okvira, jun 2026.)')]) }}

## Koliko ih vozi

{{ w.bars(C.fleet.series, title='Električni putnički automobili (BEV) krajem godine. Izvor: Eurostat, road_eqs_carpda, ažurirano ' ~ C.fleet.src_date) }}

Krajem 2025. Crna Gora je imala **{{ num(C.fleet.series[-1][1]) }}** {{ pl(C.fleet.series[-1][1], 'električni putnički automobil', 'električna putnička automobila', 'električnih putničkih automobila') }} od ukupno {{ num(C.fleet.cars_2025) }} putničkih — 0,28 %. Od toga je {{ num(C.fleet.legal_2025) }} u vlasništvu pravnih, a {{ num(C.fleet.phys_2025) }} fizičkih lica. Eurostat za Crnu Goru objavljuje podatke od 2024. Izvor: [{{ C.fleet.src_label }}]({{ C.fleet.src }}).

## Nove registracije

U 2025. od {{ num(C.new_bev.y2025_total) }} novih putničkih automobila električnih je bilo {{ num(C.new_bev.y2025) }} — {{ C.new_bev.share }} ([{{ C.new_bev.src_label }}]({{ C.new_bev.src }})).

## Javni punjači

Prema nacrtu nacionalnog okvira za infrastrukturu alternativnih goriva, Crna Gora ima {{ C.points.n }} {{ pl(C.points.n, 'javno mjesto', 'javna mjesta', 'javnih mjesta') }} za punjenje, ukupne snage {{ num(C.points.kw) }} kW; {{ C.points.normal_share }} % su punjači normalne snage, a nijedan nije iznad 150 kW ([{{ C.points.src_label }}]({{ C.points.src }})). Ecoportal navodi „oko 90 javno dostupnih punjača” ([{{ C.points.eco_label }}]({{ C.points.eco }})). Na našoj [mapi]({{ PAGES.map.path }}) je {{ num(M.n) }} punjača iz OpenStreetMapa i Open Charge Mapa.

## Podaci za preuzimanje

[{{ C.csv.file }}](/me/{{ C.csv.file }}) — broj električnih putničkih automobila (Eurostat) i novih po godinama, CSV sa separatorom „;”. Licenca CC BY 4.0: slobodno koristite uz navođenje izvora „BlokVolt (blokvolt.com), prema Eurostatu”.
