---
key: map
slug: mapa/
template: map
order: 2
nav: Mapa
icon: map
priority: 0.9
title: Mapa punjača za električne automobile u Bosni i Hercegovini | BlokVolt
description: Svi javni punjači u BiH na jednoj mapi: Elektroprivreda BiH, MOON, hoteli i tržni centri, s priključcima, snagom i cijenom gdje je objavljena.
h1: Mapa punjača
lead: Javni punjači u Bosni i Hercegovini iz OpenStreetMapa i Open Charge Mapa, s priključcima i snagom.
card: Svi javni punjači na jednoj mapi, s filterima za brze punjače i mreže.
dataset: Javni punjači za električna vozila u Bosni i Hercegovini
search_label: Pretraga punjača
search_ph: Grad, adresa ili mreža
chip_all: Svi
chip_fav: Omiljeni
chip_fast: Brzi (DC ≥ 50 kW)
near_me: Blizu mene
noscript: Mapi treba JavaScript. Cijene su na stranici Cijene.
attr_map: Mapa
attr_data: Podaci
related: prices, road, home
---
## Odakle su podaci

Punjači su iz dvije otvorene baze: **OpenStreetMap** (licenca ODbL) i **Open Charge Map** (CC BY 4.0). Snimak je od {{ M.retrieved }}; stanje OpenStreetMapa {{ M.osm_base }}, izvoz Open Charge Mapa {{ M.ocm_export }}. Isto mjesto iz obje baze prikazano je jednom. Mapa prikazuje {{ num(M.n) }} {{ pl(M.n, 'punjač', 'punjača', 'punjača') }}, od toga {{ num(M.dc50) }} s DC punjenjem od 50 kW naviše.

**Punjače nismo pojedinačno provjerili.** Otvorene baze uređuju vozači i volonteri, pa neki punjač možda više ne radi ili je samo za goste hotela. Službenog spiska javnih punjača u BiH nema: procjene se kreću od 131 (2022.) do oko 350 instaliranih punjača (2024.), od kojih nisu svi javni. Prije puta provjerite kod operatera.

Elektroprivreda BiH i MOON cijene ne objavljuju u cjenovniku; gdje je cijena poznata, vidi se u kartici punjača. Sve o cijenama: [Cijene]({{ PAGES.prices.path }}).

## Kako koristiti mapu

- **Filteri** iznad spiska: svi, brzi DC punjači od 50 kW, samo AC, CHAdeMO i mreže. Pretraga traži po nazivu, adresi, gradu i mreži.
- **Blizu mene** traži lokaciju samo kad pritisnete dugme; lokacija ostaje u vašem pregledniku.
- **Omiljeni** (zvjezdica u kartici punjača) čuvaju se samo u ovom pregledniku.
- **Navigacija** otvara Google Maps, Apple Maps ili Waze.

Punjač nedostaje ili je podatak pogrešan? Pišite na [hello@blokvolt.com](mailto:hello@blokvolt.com?subject=Ispravka%20mape%20BA) — ili ga unesite u [OpenStreetMap](https://www.openstreetmap.org), pa će se pojaviti na mapi nakon sljedećeg mjesečnog osvježavanja.

Otvoreni podaci: [stanice.json](/assets/region/ba/stanice.json) (ODbL 1.0, © OpenStreetMap i Open Charge Map).
