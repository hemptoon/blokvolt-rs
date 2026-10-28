---
key: home
slug: punjenje-kod-kuce/
order: 4
nav: Kod kuće
icon: calc
priority: 0.8
title: Koliko košta punjenje električnog auta kod kuće (EPCG) | BlokVolt
description: Kalkulator punjenja kod kuće s cijenama EPCG-a od 01.01.2026. za višu i nižu tarifu, s mrežnim naknadama i PDV-om, i poređenje s benzinom.
h1: Punjenje kod kuće ili na javnom punjaču
lead: Koliko mjesečno košta struja za električni auto kod kuće i koliko je to u odnosu na benzin ili dizel — s cijenama struje EPCG-a i maksimalnim cijenama goriva.
card: Kalkulator s tarifama EPCG i poređenjem s gorivom.
schema: WebPage
related: electricity, prices, subsidies
---
{{ w.calc() }}

## Kilovat-sat kod kuće

{{ C.power.note }}

{{ w.tariffs() }}

Cijene po modelima EPCG-a (osnovni, plavi, zeleni, crveni) i sati niže tarife nalaze se na stranici [Cijena struje]({{ PAGES.electricity.path }}).

- **Niža tarifa.** {{ C.power.nt_hours }} Noćno punjenje je upola jeftinije od dnevnog.
- **Fiksni dio** mrežne naknade (0,84 € mjesečno s PDV-om za odobrenu snagu do 8 kW) plaćate i bez auta, pa ga kalkulator ne računa.
- **Popusti.** EPCG redovnim platišama daje popuste na račun; uslove za 2026. nije bilo moguće provjeriti, pa nisu uračunati.

<details markdown="1"><summary>Kako se računa</summary>

- **Kod kuće:** (aktivna energija + angažovanje mrežnog kapaciteta + gubici u mreži + naknada za obnovljive izvore) × 1,21 (PDV), po cjenovniku EPCG-a od 01.01.2026. Struja sa zida = kilometri × potrošnja ÷ 100 × (1 + gubici).
- **Javni punjači:** kWh koje auto primi × cijena po kWh; operateri cijene ne objavljuju, pa upišite svoju.
- **Gorivo:** kilometri × litara na 100 km ÷ 100 × cijena litra. Zadate su maksimalne cijene od {{ C.fuel.date }}: Eurosuper 95 {{ money(C.fuel.petrol) }}, Eurodizel {{ money(C.fuel.diesel) }} ([Nafta.hr]({{ C.fuel.src }})). Ministarstvo ih mijenja svake sedmice.
</details>

{{ w.sources(C.power.sources) }}
