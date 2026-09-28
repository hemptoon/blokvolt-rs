---
key: home
slug: punjenje-kod-kuce/
order: 4
nav: Kod kuće
icon: calc
priority: 0.9
title: Punjenje električnog auta kod kuće u BiH: koliko košta (kalkulator, EPBiH, ERS, EP HZ HB) | BlokVolt
description: Kalkulator troškova punjenja s tarifama EPBiH (blok tarife od 01.09.2025.), Elektroprivrede RS (od 01.02.2026.) i EP HZ HB, niža tarifa, javni punjači i poređenje s benzinom i dizelom.
h1: Punjenje kod kuće ili na javnom punjaču
lead: Koliko mjesečno košta struja za električni auto kod kuće i na javnim punjačima i koliko je to u odnosu na benzin ili dizel — s tarifama sva tri javna snabdjevača.
card: Kalkulator s tarifama EPBiH, ERS i EP HZ HB, javnim punjačima i poređenjem s gorivom.
schema: WebPage
related: prices, subsidies, map
---
{{ w.calc() }}

## Kilovat-sat kod kuće

{{ C.power.note }}

{{ w.tariffs() }}

- **Blokovi.** {{ C.power.blocks }}
- **Niža tarifa.** {{ C.power.nt_hours }} Noćno punjenje na dvotarifnom brojilu je 35–40 % jeftinije od jednotarifnog.
- **Fiksne naknade** (mjerno mjesto, obračunska snaga kod ERS-a) plaćate i bez auta, pa ih kalkulator ne računa.

<details markdown="1"><summary>Kako se računa</summary>

- **Kod kuće:** (energija + naknada za obnovljive izvore u FBiH) × 1,17 (PDV); kod Elektroprivrede RS: (energija + mrežarina po kWh) × 1,17. Struja sa zida = kilometri × potrošnja ÷ 100 × (1 + gubici).
- **Javni punjači:** kWh koje auto primi × cijena po kWh.
- **Gorivo:** kilometri × litara na 100 km ÷ 100 × cijena litra. Zadane su prosječne cijene u FBiH od {{ C.fuel.date }}: BMB 95 {{ money(C.fuel.petrol) }}, eurodizel {{ money(C.fuel.diesel) }} ([N1]({{ C.fuel.src }})).
</details>

## Punjač u stambenoj zgradi

Pravila o zajedničkim dijelovima zgrade u BiH donose kantoni i entiteti, a punjači za električna vozila se u njima još ne spominju.

{{ w.facts_list(C.buildings) }}

Ako punjač u garaži zgrade dira zajedničku instalaciju ili zajedničko brojilo, računajte na odluku etažnih vlasnika. Ovo je sažetak propisa, ne pravni savjet.

{{ w.sources(C.power.sources) }}
