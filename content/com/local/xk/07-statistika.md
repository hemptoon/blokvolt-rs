---
key: stats
slug: statistika/
order: 7
nav: Statistika
icon: chart
priority: 0.6
title: Veturat elektrike në Kosovë në shifra — numri, regjistrimet, importi | BlokVolt
description: Numri i veturave elektrike në Kosovë sipas Eurostatit, regjistrimet e reja, importi në janar–gusht 2026 sipas Doganës dhe karikuesit publikë, me CSV.
h1: Veturat elektrike në Kosovë në shifra
lead: Sa vetura elektrike qarkullojnë në Kosovë, sa regjistrohen të reja, sa importohen dhe sa karikues publikë ka — nga burime zyrtare dhe media, me datë.
card: Numri i veturave që nga 2017, regjistrimet e reja, importi 2026 dhe karikuesit; CSV.
schema: Dataset
related: map, subsidies, prices
---
{{ w.stats([(num(C.fleet.series[-1][1]), pl(C.fleet.series[-1][1], 'veturë elektrike', 'vetura elektrike', 'vetura elektrike') ~ ' në fund të vitit 2025 (Eurostat)'),
            (num(C.new_bev.y2025), pl(C.new_bev.y2025, 'regjistrim i ri', 'regjistrime të reja', 'regjistrime të reja') ~ ' të veturave elektrike në vitin 2025 (Eurostat)'),
            (num(C.imports.n), pl(C.imports.n, 'veturë elektrike e importuar', 'vetura elektrike të importuara', 'vetura elektrike të importuara') ~ ' në janar–gusht 2026, ' ~ num(C.imports.china) ~ ' prej tyre nga Kina (Dogana e Kosovës)')]) }}

## Sa qarkullojnë

{{ w.bars(C.fleet.series, title='Vetura elektrike (BEV) në fund të vitit. Burimi: Eurostat, road_eqs_carpda, përditësuar më ' ~ C.fleet.src_date ~ '. Për vitet ' ~ C.fleet.missing ~ ' nuk ka vlerë.') }}

Në fund të vitit 2025 Kosova kishte **{{ num(C.fleet.series[-1][1]) }}** vetura plotësisht elektrike (BEV), {{ num(C.fleet.growth_2025, 1) }} % më shumë se një vit më parë dhe rreth {{ num(C.fleet.series[-1][1] / C.fleet.series[3][1]) }} herë më shumë se në fund të vitit {{ C.fleet.series[3][0] }} (llogaritur). Për vitet {{ C.fleet.missing }} Eurostati nuk ka vlerë për Kosovën. Burimi: [{{ C.fleet.src_label }}]({{ C.fleet.src }}).

Agjencia e Statistikave të Kosovës nuk ka në bazën ASKdata tabelë të automjeteve sipas llojit të karburantit.

## Regjistrimet e reja

Eurostati publikon për Kosovën regjistrimet e reja të veturave elektrike:

{{ w.pairs(C.new_bev.rows, 'Viti', 'Regjistrime të reja') }}

Në vitin 2025 u bënë {{ num(C.new_bev.y2025) }} regjistrime të reja të veturave elektrike, {{ num(C.new_bev.change_2025, 1) }} % më shumë se në vitin 2024 (llogaritur). Për vitet 2020 dhe 2022 Eurostati nuk ka vlerë. Burimi: [{{ C.new_bev.src_label }}]({{ C.new_bev.src }}).

## Importi

- **Janar–gusht 2026:** {{ num(C.imports.n) }} vetura elektrike, {{ num(C.imports.china) }} prej tyre nga Kina; vlera {{ C.imports.value }}, {{ C.imports.value_note }} ([{{ C.imports.src_label }}]({{ C.imports.src }})).
- **2022:** {{ C.imports.y2022 }} ([Gazeta Express]({{ C.imports.src }})).
- **Bashkë me hibridet:** {{ C.imports.hybrid }} ([{{ C.imports.hybrid_label }}]({{ C.imports.hybrid_src }})).

Burimet nuk tregojnë sa nga veturat e importuara kanë prizë karikimi GB/T. ECHARGE shkruan se ka lidhës GB/T „në disa stacione”.

## Karikuesit publikë

Numër zyrtar i karikuesve publikë në Kosovë nuk publikohet. Shifrat nga burime të ndryshme:

{% set rows = [] %}{% for a, b, u in C.charger_counts %}{% set _ = rows.append((a, b)) %}{% endfor %}{{ w.pairs(rows, 'Burimi', 'Numri') }}

[Harta]({{ PAGES.map.path }}) e këtij udhëzuesi tregon {{ num(M.n) }} karikues nga OpenStreetMap dhe Open Charge Map, prej tyre {{ num(M.dc50) }} me karikim DC nga 50 kW e lart.

## Të dhëna për shkarkim

[{{ C.csv.file }}](/xk/{{ C.csv.file }}) — numri i veturave elektrike dhe regjistrimet e reja sipas viteve (Eurostat), CSV me ndarës „;”. Licenca CC BY 4.0: përdorini lirisht, duke cituar burimin „BlokVolt (blokvolt.com), sipas Eurostatit”.

{{ w.sources(C.stats_srcs) }}
