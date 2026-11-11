---
key: stats
slug: statistika/
order: 8
nav: Statistika
icon: chart
priority: 0.6
title: Električni avtomobili v Sloveniji v številkah | BlokVolt
description: Nove registracije baterijskih električnih avtomobilov v Sloveniji 2024–2026 (AMZS, ACEA), delež v voznem parku in število javnih polnilnih točk. Podatki v CSV.
h1: Električni avtomobili v Sloveniji v številkah
lead: Koliko novih električnih avtomobilov je registriranih, kolikšen je njihov delež in koliko je javnih polnilnih točk — iz virov z datumom.
card: Nove registracije, delež v voznem parku in polnilne točke; CSV.
schema: Dataset
related: map, subsidies, prices
---
{{ w.stats([(num(C.new_bev.y2025), pl(C.new_bev.y2025, 'nov baterijski električni avto', 'nova baterijska električna avtomobila', 'novi baterijski električni avtomobili', 'novih baterijskih električnih avtomobilov') ~ ' v letu 2025 — ' ~ C.new_bev.share ~ ' od ' ~ num(C.new_bev.y2025_total) ~ ' novih (AMZS)'),
            (num(C.acea.y2026_9m), 'novih od januarja do septembra 2026, ' ~ C.acea.growth ~ ' % več kot leto prej (ACEA)'),
            (C.fleet.share, 'delež baterijskih električnih avtomobilov v voznem parku konec leta 2025')]) }}

## Nove registracije

{{ w.bars(C.new_bev.series, title='Novi baterijski električni osebni avtomobili po letih. Vir: AMZS, ' ~ C.new_bev.src_date) }}

V letu 2025 je bilo registriranih **{{ num(C.new_bev.y2025) }}** novih baterijskih električnih avtomobilov, {{ C.new_bev.share }} od {{ num(C.new_bev.y2025_total) }} novih osebnih avtomobilov; leta 2024 jih je bilo 3.142, prodaja se je torej podvojila ([{{ C.new_bev.src_label }}]({{ C.new_bev.src }})). {{ C.new_bev.alt }}

Od januarja do septembra 2026 jih je bilo **{{ num(C.acea.y2026_9m) }}** (leto prej {{ num(C.acea.y2025_9m) }}, +{{ C.acea.growth }} %) od {{ num(C.acea.all_9m) }} novih avtomobilov — okoli {{ C.acea.share }} (izračun). Samo septembra 2026: {{ num(C.acea.sep) }}, okoli {{ C.acea.sep_share }} trga. V istem obdobju je bilo registriranih še {{ num(C.acea.phev) }} priključnih hibridov in {{ num(C.acea.hev) }} hibridov ([{{ C.acea.src_label }}]({{ C.acea.src }}), {{ C.acea.src_date }}).

## Vozni park

Natančnega števila baterijskih električnih avtomobilov na cestah ni bilo mogoče najti. Konec leta 2025 je bil njihov delež v voznem parku (skoraj 1,3 milijona osebnih avtomobilov) okoli {{ C.fleet.share }} (okoli 2 % po [{{ C.fleet.share_label }}]({{ C.fleet.share_src }}), okoli 1,6 % in okoli 20.000 vozil po Svet24, 1. 7. 2026); Forbes Slovenija navaja okoli {{ num(C.fleet.approx) }}, brez navedbe vira ([{{ C.fleet.src_label }}]({{ C.fleet.src }})).

## Javne polnilne točke

- **Uradni register** (NAP / Prometej, zemljevid DeMS): {{ C.points.dems }} ([{{ C.points.dems_label }}]({{ C.points.dems_src }})).
- **EAFO:** {{ C.points.eafo }} ([{{ C.points.eafo_label }}]({{ C.points.eafo_src }})).
- **Največja operaterja:** {{ C.points.top2 }}
- **Zemljevid tega vodnika:** {{ num(M.n) }} {{ pl(M.n, 'polnilnica', 'polnilnici', 'polnilnice', 'polnilnic') }} iz OpenStreetMapa in Open Charge Mapa, od tega {{ num(M.dc50) }} z DC od 50 kW naprej. [Zemljevid]({{ PAGES.map.path }})

Številke se razlikujejo, ker viri štejejo različne enote (polnilne točke ali lokacije) in so z različnih datumov.

## Podatki za prenos

[{{ C.csv.file }}](/si/{{ C.csv.file }}) — novi baterijski električni avtomobili po letih (AMZS, ACEA), CSV z ločilom »;«. Licenca CC BY 4.0: prosto uporabite z navedbo vira »BlokVolt (blokvolt.com), po AMZS in ACEA«.
