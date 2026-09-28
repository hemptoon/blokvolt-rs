---
key: map
slug: mapa/
template: map
order: 2
nav: Mapa
icon: map
priority: 0.9
title: Mapa punjača za električne automobile u Crnoj Gori | BlokVolt
description: Svi javni punjači u Crnoj Gori na jednoj mapi: EKO stanice, hoteli, marine i opštinski punjači, s priključcima i snagom.
h1: Mapa punjača
lead: Javni punjači u Crnoj Gori iz OpenStreetMapa i Open Charge Mapa, s priključcima i snagom.
card: Svi javni punjači na jednoj mapi, s filterima za brze punjače.
dataset: Javni punjači za električna vozila u Crnoj Gori
search_label: Pretraga punjača
search_ph: Grad, adresa ili mreža
chip_all: Svi
chip_fav: Omiljeni
chip_fast: Brzi (DC ≥ 50 kW)
near_me: Blizu mene
noscript: Mapi treba JavaScript.
attr_map: Mapa
attr_data: Podaci
related: prices, road, home
---
## Odakle su podaci

Punjači su iz dvije otvorene baze: **OpenStreetMap** (licenca ODbL) i **Open Charge Map** (CC BY 4.0). Snimak je od {{ M.retrieved }}; stanje OpenStreetMapa {{ M.osm_base }}, izvoz Open Charge Mapa {{ M.ocm_export }}. Isto mjesto iz obje baze prikazano je jednom. Mapa prikazuje {{ num(M.n) }} {{ pl(M.n, 'punjač', 'punjača', 'punjača') }}, od toga {{ num(M.dc50) }} s DC punjenjem od 50 kW naviše.

**Punjači nisu pojedinačno provjereni.** Otvorene baze uređuju vozači i volonteri, pa neki punjač možda više ne radi ili je samo za goste hotela. Prema nacrtu nacionalnog okvira Crna Gora ima {{ C.points.n }} {{ pl(C.points.n, 'javno mjesto', 'javna mjesta', 'javnih mjesta') }} za punjenje, ukupne snage {{ num(C.points.kw) }} kW; {{ C.points.normal_share }} % su punjači normalne snage ([{{ C.points.src_label }}]({{ C.points.src }})).

## Kako koristiti mapu

- **Filteri** iznad spiska: svi, brzi DC punjači od 50 kW, samo AC i CHAdeMO. Pretraga traži po nazivu, adresi i gradu.
- **Blizu mene** traži lokaciju samo kad pritisnete dugme; lokacija ostaje u vašem pregledaču.
- **Omiljeni** (zvjezdica u kartici punjača) čuvaju se samo u ovom pregledaču.

Punjač nedostaje ili je podatak pogrešan? Pišite na [hello@blokvolt.com](mailto:hello@blokvolt.com?subject=Ispravka%20mape%20ME) — ili ga unesite u [OpenStreetMap](https://www.openstreetmap.org), pa će se pojaviti na mapi nakon sljedećeg mjesečnog osvježavanja.

Otvoreni podaci: [stanice.json](/assets/region/me/stanice.json) (ODbL 1.0, © OpenStreetMap i Open Charge Map).
