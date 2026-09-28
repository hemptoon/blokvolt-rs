---
key: stats
slug: statistika/
order: 9
nav: Statistika
icon: chart
priority: 0.7
title: Električni automobili u Hrvatskoj u brojkama 2026. — broj vozila, prodaja, punionice | BlokVolt
description: Broj električnih automobila u Hrvatskoj od 2021. (Eurostat), nove registracije 2026. (ACEA), najprodavaniji modeli, županije, javne punionice po operaterima. Podaci za preuzimanje (CSV).
h1: Električni automobili u Hrvatskoj u brojkama
lead: Koliko električnih automobila vozi Hrvatskom, koliko se novih prodaje, koji su modeli najprodavaniji i koliko je javnih punionica — iz službenih izvora, s datumom.
card: Broj vozila od 2021., nove registracije 2026., modeli, županije i punionice po operaterima; CSV za preuzimanje.
schema: Dataset
related: map, subsidies, prices
---
{{ w.stats([(num(C.fleet.series[-1][1]), pl(C.fleet.series[-1][1], 'električni osobni automobil', 'električna osobna automobila', 'električnih osobnih automobila') ~ ' krajem 2025. (Eurostat)'),
            (num(C.new_bev.jan_aug_2026), pl(C.new_bev.jan_aug_2026, 'novi', 'nova', 'novih') ~ ' od siječnja do kolovoza 2026. (ACEA), 4,2 % svih novih'),
            ('~' ~ num(C.charging_stats.hpc_2026.connectors), pl(C.charging_stats.hpc_2026.connectors, 'ultrabrzi priključak', 'ultrabrza priključka', 'ultrabrzih priključaka') ~ ' od 150 kW naviše (ožujak 2026.)')]) }}

## Koliko ih vozi

{{ w.bars(C.fleet.series, title='Električni osobni automobili (BEV) krajem godine. Izvor: Eurostat, road_eqs_carpda, ažurirano ' ~ C.fleet.src_date) }}

Krajem 2025. Hrvatska je imala **{{ num(C.fleet.series[-1][1]) }}** {{ pl(C.fleet.series[-1][1], 'električni osobni automobil', 'električna osobna automobila', 'električnih osobnih automobila') }}, {{ C.fleet.growth_2025 }} % više nego godinu prije i četiri puta više nego 2021. Od toga je {{ num(C.fleet.phys_2025) }} u vlasništvu fizičkih, a {{ num(C.fleet.legal_2025) }} pravnih osoba — više od polovice registrirano je na tvrtke. Izvor: [{{ C.fleet.src_label }}]({{ C.fleet.src }}).

## Koliko ih se prodaje

| Razdoblje | Novi električni automobili | Promjena | Udio u novim automobilima |
|---|---|---|---|
| 2024. | {{ num(C.new_bev.y2024) }} | | |
| 2025. | {{ num(C.new_bev.y2025) }} | −29,4 % | 1,8 % |
| siječanj–lipanj 2026. | {{ num(C.new_bev.h1_2026) }} | +349,7 % | 4,0 % |
| siječanj–kolovoz 2026. | {{ num(C.new_bev.jan_aug_2026) }} | +329,3 % | 4,2 % |

Po mjesecima 2026.: lipanj 344 (lani 77), srpanj 358 (lani 69), kolovoz 158 (lani 70). ACEA za srpanj nije objavila zasebno izvješće, pa je srpanj izračunat kao razlika zbrojeva. Izvor: [{{ C.new_bev.src_label }}]({{ C.new_bev.src }}), [lipanj 2026.]({{ C.new_bev.src_h1 }}), [prosinac 2025.]({{ C.new_bev.src_y2025 }}).

Centar za vozila Hrvatske (CVH) za prvih šest mjeseci 2026. navodi {{ num(C.new_bev.cvh_h1_2026) }} {{ pl(C.new_bev.cvh_h1_2026, 'novoregistrirani električni automobil', 'novoregistrirana električna automobila', 'novoregistriranih električnih automobila') }} (lani {{ num(C.new_bev.cvh_h1_2025) }}). Brojka se razlikuje od ACEA-ine, a izvor ne navodi broji li CVH i rabljena uvezena vozila ([HRT, {{ C.new_bev.cvh_date }}]({{ C.new_bev.cvh_src }})).

## Najprodavaniji modeli

{{ w.pairs(C.top_models.y2026, 'Model, ' ~ C.top_models.y2026_label, 'Prodano') }}

Od siječnja do kolovoza 2026. broj prodanih električnih automobila bio je {{ num(C.top_models.y2026_total) }}; BYD ih je prodao 723, Tesla 352. Izvor: Promocija plus prema [Autonetu, {{ C.top_models.y2026_date }}]({{ C.top_models.y2026_src }}). U cijeloj 2025. prvi je bio Tesla Model Y (239), zatim Model 3 (113) i BYD Dolphin Surf (89) ([Autonet, {{ C.top_models.y2025_date }}]({{ C.top_models.y2025_src }})).

## Po županijama

{{ w.pairs(C.counties_2024.rows, 'Županija, 2024.', 'Električnih automobila') }}

Ukupno {{ num(C.counties_2024.total) }} {{ pl(C.counties_2024.total, 'električni automobil', 'električna automobila', 'električnih automobila') }} 2024. prema CVH-u; gotovo dvije petine u Gradu Zagrebu. Izvor: [{{ C.counties_2024.src_label }}]({{ C.counties_2024.src }}), {{ C.counties_2024.src_date }}

## Javne punionice

- **Na našoj karti:** {{ num(M.n) }} {{ pl(M.n, 'punionica', 'punionice', 'punionica') }} iz OpenStreetMapa i Open Charge Mapa, od toga {{ num(M.dc50) }} s DC punjenjem od 50 kW naviše ([karta]({{ PAGES.map.path }})).
- **Državni Registar punionica** (CRO IDRO) ima {{ C.registry.rows }} zapisa; jedan zapis je jedna registrirana punionica, bez snage i broja priključaka. {{ C.registry.missing }}.
- **Krajem 2023.** javnih mjesta za punjenje bilo je 1.074: 675 AC i 399 DC ([ACEA]({{ C.charging_stats.acea_2023.src }})).
- **Ultrabrze punionice:** oko 300 priključaka od 150 kW naviše; Tesla ima {{ C.charging_stats.tesla.list }} {{ pl(C.charging_stats.tesla.list, 'lokaciju', 'lokacije', 'lokacija') }} na svom popisu i, prema Autonetu, {{ C.charging_stats.tesla.spots }} {{ pl(C.charging_stats.tesla.spots, 'mjesto', 'mjesta', 'mjesta') }} za punjenje ([energetika-net.com, {{ C.charging_stats.hpc_2026.date }}]({{ C.charging_stats.hpc_2026.src }}); [Autonet, {{ C.charging_stats.tesla.date }}]({{ C.charging_stats.tesla.src }})).

Zapisi u Registru punionica po vlasniku ({{ C.checked }}):

{{ w.pairs(C.registry.owners, 'Vlasnik', 'Zapisa') }}

## Podaci za preuzimanje

[{{ C.csv.file }}](/hr/{{ C.csv.file }}) — broj električnih automobila (Eurostat) i nove registracije (ACEA) po godinama, CSV sa separatorom „;”. Licenca CC BY 4.0: slobodno koristite uz navođenje izvora „BlokVolt (blokvolt.com), prema Eurostatu i ACEA-i”.
