---
key: home
slug: punjenje-kod-kuce/
order: 4
nav: Kod kuće
icon: calc
priority: 0.8
title: Punjenje električnog auta kod kuće u Crnoj Gori: koliko košta (kalkulator, EPCG) | BlokVolt
description: Kalkulator troškova punjenja kod kuće s indikativnim cijenama EPCG-a za višu i nižu tarifu, mrežnim naknadama REGAGEN-a za 2026. i poređenjem s benzinom i dizelom.
h1: Punjenje kod kuće ili na javnom punjaču
lead: Koliko mjesečno košta struja za električni auto kod kuće i koliko je to u odnosu na benzin ili dizel — s indikativnim cijenama struje i maksimalnim cijenama goriva.
card: Kalkulator s tarifama EPCG i poređenjem s gorivom.
schema: WebPage
related: prices, subsidies, map
---
{{ w.calc() }}

## Kilovat-sat kod kuće

{{ C.power.note }}

{{ w.tariffs() }}

- **Niža tarifa.** {{ C.power.nt_hours }} Noćno punjenje je upola jeftinije od dnevnog.
- **Fiksni dio** mrežne naknade (0,84 € mjesečno s PDV-om za odobrenu snagu do 8 kW) plaćate i bez auta, pa ga kalkulator ne računa.
- **Popusti.** EPCG redovnim platišama daje popuste na račun; uslove za 2026. nije bilo moguće provjeriti, pa nisu uračunati.

<details markdown="1"><summary>Kako se računa</summary>

- **Kod kuće:** (aktivna energija + korišćenje distributivnog sistema + gubici u distribuciji i prenosu + naknada operatora tržišta) × 1,21 (PDV). Struja sa zida = kilometri × potrošnja ÷ 100 × (1 + gubici).
- **Javni punjači:** kWh koje auto primi × cijena po kWh; operateri cijene ne objavljuju, pa upišite svoju.
- **Gorivo:** kilometri × litara na 100 km ÷ 100 × cijena litra. Zadate su maksimalne cijene od {{ C.fuel.date }}: Eurosuper 95 {{ money(C.fuel.petrol) }}, Eurodizel {{ money(C.fuel.diesel) }} ([Investitor.me]({{ C.fuel.src }})). Ministarstvo ih mijenja svake sedmice.
</details>

{{ w.sources(C.power.sources) }}
