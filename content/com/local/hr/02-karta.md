---
key: map
slug: karta/
template: map
order: 2
nav: Karta
icon: map
priority: 0.9
title: Karta punionica za električne automobile u Hrvatskoj s cijenama | BlokVolt
description: Sve javne punionice u Hrvatskoj na jednoj karti: ELEN, Petrol, Tesla, IONITY, Lidl, Kaufland i druge, s priključcima, snagom i cijenom mreže po kWh.
h1: Karta punionica
lead: Javne punionice u Hrvatskoj iz OpenStreetMapa i Open Charge Mapa, s priključcima, snagom i cjenikom mreže.
card: Sve javne punionice na jednoj karti, s filtrima za brze punionice i mreže te cijenom mreže u kartici punionice.
dataset: Javne punionice za električna vozila u Hrvatskoj
search_label: Pretraga punionica
search_ph: Grad, adresa ili mreža
chip_all: Sve
chip_fav: Omiljene
chip_fast: Brze (DC ≥ 50 kW)
near_me: Blizu mene
noscript: Karti treba JavaScript. Cijene po mrežama su na stranici Cijene.
attr_map: Karta
attr_data: Podaci
related: prices, apps, road
---
## Odakle su podaci

Punionice su iz dviju otvorenih baza: **OpenStreetMap** (licenca ODbL) i **Open Charge Map** (CC BY 4.0). Snimak je od {{ M.retrieved }}; stanje OpenStreetMapa {{ M.osm_base }}, izvoz Open Charge Mapa {{ M.ocm_export }}. Isto mjesto iz obje baze prikazano je jednom. Karta prikazuje {{ num(M.n) }} {{ pl(M.n, 'punionicu', 'punionice', 'punionica') }}: {{ num(M.dc50) }} s DC punjenjem od 50 kW naviše, od toga {{ num(M.hpc) }} s 150 kW ili više.

**Punionice nisu pojedinačno provjerene.** Otvorene baze uređuju vozači i volonteri, pa neka punionica možda više ne radi ili je samo za goste hotela. Prije puta provjerite u aplikaciji mreže. Državni [Registar punionica](https://pametnamobilnost.hr/hr/registar-punionica/44) ima 715 zapisa, ali bez koordinata i snage, pa ga ne možemo izravno usporediti s kartom.

Cijena u kartici punionice je **cjenik mreže** za tu vrstu punjenja — AC, DC do 50 kW ili ultrabrzo — s datumom od kojeg vrijedi. Gdje mreža ima više cijena (s registracijom i bez nje, na autocesti i izvan nje), vidite raspon i sve stavke. Cijene svih mreža na jednom mjestu: [Cijene punjenja]({{ PAGES.prices.path }}).

## Kako koristiti kartu

- **Filtri** iznad popisa: sve, brze DC punionice od 50 kW, samo AC, CHAdeMO i najveće mreže. Pretraga traži po nazivu, adresi, gradu i mreži.
- **Blizu mene** traži lokaciju samo kad pritisnete gumb; lokacija ostaje u vašem pregledniku i nigdje se ne šalje.
- **Omiljene** (zvjezdica u kartici punionice) spremaju se samo u ovom pregledniku.
- **Navigacija** otvara Google Maps, Apple Maps ili Waze; **Podijeli** kopira poveznicu na punionicu.
- **Gdje točno**: adresa, koordinate za kopiranje i Plus Code za navigaciju.

Punionica nedostaje ili je podatak pogrešan? Pošaljite ispravku na [hello@blokvolt.com](mailto:hello@blokvolt.com?subject=Ispravka%20karte%20HR) — ili je sami unesite u [OpenStreetMap](https://www.openstreetmap.org), pa će se pojaviti na karti nakon sljedećeg mjesečnog osvježavanja.

Otvoreni skup podataka: [stanice.json](/assets/region/hr/stanice.json) (ODbL 1.0, © OpenStreetMap i Open Charge Map).
