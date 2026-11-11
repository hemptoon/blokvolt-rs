---
key: prices
slug: cene/
order: 3
nav: Cene
icon: coins
priority: 0.7
title: Cene polnjenja električnih avtomobilov v Sloveniji | BlokVolt
description: Ceniki javnih polnilnic v Sloveniji: Gremo na elektriko, Petrol, IONITY, Tesla Supercharger, MOONcharge in GEN-I Charge — cena kWh, pristojbine in načini plačila.
h1: Cene polnjenja v Sloveniji
lead: Kaj mreže objavljajo o cenah in načinih plačila, z virom in datumom preverjanja.
card: Ceniki Gremo na elektriko, Petrol in IONITY; kaj objavljata Tesla in MOONcharge.
related: map, home, road
---
Cenik s ceno kWh objavljajo Gremo na elektriko (AC 0,35 €, DC 0,45 €), Petrol (AC 0,37 €, DC do 50 kW 0,47 €, nad 50 kW 0,66 € za registrirane uporabnike) in IONITY (brez naročnine od 0,73 €, s paketom od 0,41 €). Tesla in MOONcharge cene kWh na preverjenih straneh ne prikazujeta, zato jo preverite v aplikaciji ali na polnilnici. Stanje {{ C.checked }}.

{{ w.price_table() }}

## Mreže

{{ w.net_cards() }}

## Druge polnilnice

{{ w.pairs(C.other_sites, 'Kdo', 'Kaj je znano') }}

## Pred polnjenjem

- Pri Gremo na elektriko se poleg kWh plača pristojbina za polnjenje, po 180 minutah na AC (podnevi) in po 60 minutah na DC pa še časovni dodatek.
- Na Teslinih polnilnicah se, ko je polnilnica zasedena, plača pristojbina za zasedenost (do 0,50 € na minuto), če avto po koncu polnjenja ali nad 80 % ostane priključen več kot 5 minut.
- Polnilnice v hotelih in podjetjih so pogosto samo za goste ali stranke.
- Za pot po regiji: [Hrvaška](/hr/aplikacije-i-kartice/){% if 'ba' in LOCALS_ALL|map(attribute='key')|list %}, [BiH](/ba/cijene/){% endif %}, [Srbija](https://www.blokvolt.rs/javno-punjenje/aplikacije-i-kartice/).

Imate posnetek cene s polnilnice ali računa, z datumom in lokacijo? Pošljite ga na [hello@blokvolt.com](mailto:hello@blokvolt.com?subject=Cena%20polnjenja%20SI) — cena bo objavljena z datumom.
