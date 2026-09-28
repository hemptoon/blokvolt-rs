---
key: stats
slug: statistika/
order: 7
nav: Statistika
icon: chart
priority: 0.6
title: Makinat elektrike në Shqipëri në shifra — numri dhe regjistrimet | BlokVolt
description: Numri i makinave elektrike në Shqipëri nga 2021 (Eurostat), regjistrimet e reja, të dhënat e DPSHTRR për 2026 dhe karikuesit publikë. CSV për shkarkim.
h1: Makinat elektrike në Shqipëri në shifra
lead: Sa makina elektrike qarkullojnë në Shqipëri, sa regjistrohen çdo vit dhe sa karikues publikë ka — nga burime zyrtare, me datë.
card: Numri i makinave nga 2021, regjistrimet e reja dhe karikuesit; CSV.
schema: Dataset
related: map, subsidies, prices
---
{{ w.stats([(num(C.fleet.series[-1][1]), pl(C.fleet.series[-1][1], 'makinë elektrike', 'makina elektrike', 'makina elektrike') ~ ' në fund të vitit 2025 (Eurostat)'),
            (num(C.new_reg.series[-1][1]), pl(C.new_reg.series[-1][1], 'regjistrim i ri', 'regjistrime të reja', 'regjistrime të reja') ~ ' të makinave elektrike në vitin 2025 (Eurostat)'),
            (num(M.n), pl(M.n, 'karikues publik', 'karikues publikë', 'karikues publikë') ~ ' në hartë')]) }}

## Sa qarkullojnë

{{ w.bars(C.fleet.series, title='Makinat elektrike (autovetura vetëm me bateri) në fund të vitit. Burimi: Eurostat, road_eqs_carpda, përditësuar më ' ~ C.fleet.src_date) }}

Në fund të vitit 2025 Shqipëria kishte **{{ num(C.fleet.series[-1][1]) }}** {{ pl(C.fleet.series[-1][1], 'makinë elektrike', 'makina elektrike', 'makina elektrike') }}, {{ C.fleet.growth_2025 }} % më shumë se një vit më parë. Eurostat numëron autoveturat vetëm me bateri. Burimi: [{{ C.fleet.src_label }}]({{ C.fleet.src }}).

INSTAT raporton të njëjtën rritje, {{ C.instat.ev_growth }} %, për autoveturat elektrike në vitin 2025, por nuk jep numrin e tyre. Sipas INSTAT, në vitin 2025 ishin regjistruar {{ num(C.instat.vehicles) }} mjete rrugore, {{ C.instat.vehicles_change }} % më shumë se në vitin 2024; {{ C.instat.cars_share }} % prej tyre ishin autovetura dhe {{ C.instat.diesel_share }} % e autoveturave ishin me naftë. Burimi: [{{ C.instat.src_label }}]({{ C.instat.src }}), {{ C.instat.date }} (PDF në anglisht).

## Regjistrimet e reja

{% set rows = [] %}{% for y, n in C.new_reg.series %}{% set _ = rows.append((y, num(n))) %}{% endfor %}{{ w.pairs(rows, 'Viti', 'Makina elektrike të reja') }}

Burimi: [{{ C.new_reg.src_label }}]({{ C.new_reg.src }}), përditësuar më {{ C.new_reg.src_date }}.

Për vitin 2026 ka vetëm të dhëna të DPSHTRR të raportuara nga media:

{% for r in C.first_reg_2026 %}
- **{{ r.period|capitalize }}.** {{ num(r.n) }} mjete elektrike të regjistruara për herë të parë, {{ r.change }} % më shumë se një vit më parë; {{ r.share }} ([{{ r.src_label }}]({{ r.src }})).
{% endfor %}

Asnjë burim nuk tregon sa prej tyre ishin autovetura dhe sa ishin makina të përdorura.

[OSHEE]({{ C.oshee_2025.src }}) shkroi më {{ C.oshee_2025.date }} për rreth {{ num(C.oshee_2025.evs) }} mjete elektrike të regjistruara, nga të cilat {{ num(C.oshee_2025.added) }} ishin shtuar në dhjetë muajt e parë të vitit 2025. Shifra ndryshon nga ajo e Eurostat-it dhe OSHEE nuk e sqaron se çfarë numëron.

## Karikuesit publikë

Numër zyrtar i karikuesve publikë nuk ka. Shifrat nga burime të ndryshme:

{% set rows = [] %}{% for a, b, u in C.charger_counts %}{% set _ = rows.append((a, b)) %}{% endfor %}{{ w.pairs(rows, 'Burimi', 'Numri') }}

[Harta]({{ PAGES.map.path }}) tregon {{ num(M.n) }} {{ pl(M.n, 'karikues', 'karikues', 'karikues') }} nga OpenStreetMap dhe Open Charge Map, nga të cilët {{ num(M.dc50) }} me karikim DC nga 50 kW e lart.

## Të dhëna për shkarkim

[{{ C.csv.file }}](/al/{{ C.csv.file }}) — numri i makinave elektrike në qarkullim dhe regjistrimet e reja sipas viteve (Eurostat), CSV me ndarës „;“. Licenca CC BY 4.0: përdoreni lirisht, duke përmendur burimin „BlokVolt (blokvolt.com), sipas Eurostat-it“.
