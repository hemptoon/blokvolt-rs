---
key: map
slug: zemljevid/
template: map
order: 2
nav: Zemljevid
icon: map
priority: 0.9
title: Zemljevid polnilnic za električne avtomobile v Sloveniji | BlokVolt
description: Vse javne polnilnice v Sloveniji na enem zemljevidu: Petrol, Gremo na elektriko, IONITY, Tesla, MOONcharge in druge, s priključki, močjo in ceno, kjer je objavljena.
h1: Zemljevid polnilnic
lead: Javne polnilnice v Sloveniji iz OpenStreetMapa in Open Charge Mapa, s priključki in močjo.
card: Vse javne polnilnice na enem zemljevidu, s filtri za hitre polnilnice in mreže.
dataset: Javne polnilnice za električna vozila v Sloveniji
search_label: Iskanje polnilnic
search_ph: Kraj, naslov ali mreža
chip_all: Vse
chip_fav: Priljubljene
chip_fast: Hitre (DC ≥ 50 kW)
near_me: V bližini
noscript: Zemljevid potrebuje JavaScript. Cene so na strani Cene.
attr_map: Zemljevid
attr_data: Podatki
related: prices, road, home
---
## Od kod so podatki

Polnilnice so iz dveh odprtih baz: **OpenStreetMap** (licenca ODbL) in **Open Charge Map** (CC BY 4.0). Posnetek je z dne {{ M.retrieved }}; stanje OpenStreetMapa {{ M.osm_base }}, izvoz Open Charge Mapa {{ M.ocm_export }}. Polnilnica, ki je v obeh bazah, je prikazana enkrat. Na zemljevidu je {{ num(M.n) }} {{ pl(M.n, 'polnilnica', 'polnilnici', 'polnilnice', 'polnilnic') }}, od tega {{ num(M.dc50) }} z DC-polnjenjem od 50 kW naprej.

**Polnilnice niso posamično preverjene.** Odprte baze urejajo vozniki in prostovoljci, zato kakšna polnilnica morda ne deluje več ali je samo za goste. Uradni register (NAP / Prometej) je večji: po zemljevidu društva DeMS ima {{ C.points.dems }} ([DeMS, 28. 8. 2026]({{ C.points.dems_src }})). Pred potjo preverite pri operaterju.

Kjer je cena znana, je v kartici polnilnice. Vse o cenah: [Cene]({{ PAGES.prices.path }}).

## Kako uporabljati zemljevid

- **Filtri** nad seznamom: vse, hitre DC-polnilnice od 50 kW, samo AC, CHAdeMO in mreže. Iščete lahko po imenu, naslovu, kraju in mreži.
- **V bližini** zahteva lokacijo šele, ko pritisnete gumb; lokacija ostane v vašem brskalniku.
- **Priljubljene** (zvezdica v kartici) se hranijo samo v tem brskalniku.
- **Navigacija** odpre Google Maps, Apple Maps ali Waze.

Polnilnica manjka ali je podatek napačen? Pišite na [hello@blokvolt.com](mailto:hello@blokvolt.com?subject=Popravek%20zemljevida%20SI) — ali jo vnesite v [OpenStreetMap](https://www.openstreetmap.org); na zemljevidu bo po naslednji mesečni osvežitvi.

Odprti podatki: [stanice.json](/assets/region/si/stanice.json) (ODbL 1.0, © OpenStreetMap in Open Charge Map).

**[Polnilnice po krajih](/si/kraji/)**: seznam krajev s številom polnilnic in povezavo na zemljevid.
