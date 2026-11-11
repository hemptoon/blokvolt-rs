---
key: road
slug: potovanje/
order: 7
nav: Na poti
icon: road
priority: 0.7
title: Z električnim avtom po Sloveniji: hitre polnilnice | BlokVolt
description: Kje so v Sloveniji polnilnice od 150 kW naprej (IONITY, Tesla, Petrol, Eleport, MOL) po podatkih zemljevida in kaj preveriti pred potjo.
h1: Z električnim avtom po Sloveniji
lead: Kje so najhitrejše polnilnice ob avtocestah in v večjih krajih, po odprtih podatkih zemljevida.
card: Polnilnice od 150 kW naprej po krajih in nasveti za pot.
related: map, prices, home
---
Na zemljevidu je {{ num(M.dc50) }} {{ pl(M.dc50, 'polnilnica', 'polnilnici', 'polnilnice', 'polnilnic') }} z DC-polnjenjem od 50 kW naprej in {{ num(M.hpc) }} od 150 kW naprej. Uradnega seznama polnilnic ob avtocestah (DARS, TEN-T) na dosegljivi strani ni bilo mogoče najti, zato je spodnji seznam iz odprtih podatkov in ni posamično preverjen.

## Polnilnice od 150 kW naprej

{{ w.pairs(C.road, 'Kraj', 'Mreža, največja moč') }}

## Nasveti

- **Cena na avtocesti.** IONITY brez naročnine stane od 0,73 €/kWh (najnižja prikazana cena), s paketom manj. Petrol nad 50 kW: 0,66 €/kWh za registrirane uporabnike oziroma 0,73 €/kWh brez registracije. Pri Tesli ceno preverite v aplikaciji.
- **Gostovanje.** Z aplikacijo MOONcharge ali kartico GEN-I Charge lahko polnite tudi pri drugih operaterjih. [Cene]({{ PAGES.prices.path }})
- **Na Hrvaško in s Hrvaškega.** Polnilnice na hrvaški strani so na [hrvaškem zemljevidu](/hr/karta/).
- **Pred potjo** preverite polnilnico pri operaterju: odprti podatki niso posamično preverjeni.

Za iskanje po poti uporabite [zemljevid]({{ PAGES.map.path }}) s filtrom »Hitre (DC ≥ 50 kW)«.

{{ w.sources(C.road_srcs) }}
