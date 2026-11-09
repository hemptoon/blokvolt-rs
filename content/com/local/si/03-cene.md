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
card: Ceniki Gremo na elektriko in IONITY, kaj objavljajo Petrol, Tesla in MOONcharge.
related: map, home, road
---
Cenik z jasno ceno kWh objavljata Gremo na elektriko (AC 0,35 €, DC 0,45 €) in IONITY (od 0,43 do 0,73 € glede na paket). Petrol, Tesla in MOONcharge cene kWh na preverjenih straneh ne prikazujejo, zato jo preverite v aplikaciji ali na polnilnici. Stanje {{ C.checked }}.

{{ w.price_table() }}

## Mreže

{{ w.net_cards() }}

## Druge polnilnice

{{ w.pairs(C.other_sites, 'Kdo', 'Kaj je znano') }}

## Pred polnjenjem

- Pri Gremo na elektriko se poleg kWh plača pristojbina za polnjenje, po 180 minutah na AC (podnevi) in po 60 minutah na DC pa še časovni dodatek.
- Na Teslinih polnilnicah se po koncu polnjenja ob polni zasedenosti plača pristojbina za zasedenost.
- Polnilnice v hotelih in podjetjih so pogosto samo za goste ali stranke.
- Za pot po regiji: [Hrvaška](/hr/aplikacije-i-kartice/){% if 'ba' in LOCALS_ALL|map(attribute='key')|list %}, [BiH](/ba/cijene/){% endif %}, [Srbija](https://www.blokvolt.rs/javno-punjenje/aplikacije-i-kartice/).

Imate posnetek cene s polnilnice ali računa, z datumom in lokacijo? Pošljite ga na [hello@blokvolt.com](mailto:hello@blokvolt.com?subject=Cena%20polnjenja%20SI) — cena bo objavljena z datumom.
