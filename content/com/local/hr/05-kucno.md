---
key: home
slug: punjenje-kod-kuce/
order: 5
nav: Kod kuće
icon: calc
priority: 0.9
title: Punjenje električnog auta kod kuće ili na punionici: koliko košta (kalkulator, HEP 2026.) | BlokVolt
description: Kalkulator troškova punjenja s HEP-ovim cijenama od 1. 10. 2026.: tarifni modeli Plavi i Bijeli, niža tarifa noću, javne punionice i usporedba s benzinom i dizelom.
h1: Punjenje kod kuće ili na javnoj punionici
lead: Koliko mjesečno stoji struja za električni auto kod kuće i na javnim punionicama i koliko je to u odnosu na benzin ili dizel — s HEP-ovim cijenama od 1. listopada 2026.
card: Kalkulator s HEP-ovim tarifama od 1. 10. 2026., javnim punionicama i usporedbom s gorivom.
schema: WebPage
related: prices, subsidies, buildings
---
{{ w.calc() }}

## Kilovatsat kod kuće

Cijene energije za kućanstva od **{{ C.power.period }}** određuje {{ C.power.regulation }}. Mrežne naknade vrijede od 1. 1. 2026., a naknada za obnovljive izvore je {{ num(C.power.oie, 6) }} € po kWh. Na sve se dodaje PDV od {{ C.power.vat }} %.

{{ w.tariffs() }}

- **Niža tarifa.** {{ C.power.nt_hours }} Noćno punjenje na tarifnom modelu Bijeli gotovo je dvostruko jeftinije od jedinstvene tarife.
- **Prag od 3.000 kWh.** {{ C.power.threshold }} Kućanstvo koje već troši više od 300 kWh mjesečno s punjenjem auta lako prijeđe prag — tada vrijedi desni stupac.
- **Fiksne naknade** (mjerno mjesto i opskrba, oko {{ money(C.power.fixed_month) }} mjesečno s PDV-om) plaćate i bez auta, pa ih kalkulator ne računa.

**Primjer.** Auto koji prijeđe oko 1.100 km mjesečno treba oko 200 kWh sa zida. Noću na tarifnom modelu Bijeli to je {{ money(C.power.example.night) }} mjesečno, a iznad praga {{ money(C.power.example.night_hi) }}. Ista struja po jedinstvenoj tarifi stoji {{ money(C.power.example.plavi) }}, a danju na Bijelom {{ money(C.power.example.vt) }}.

<details markdown="1"><summary>Kako se računa</summary>

- **Kod kuće:** (energija + mrežna naknada + naknada za obnovljive izvore) × 1,13 (PDV). Struja sa zida = kilometri × potrošnja ÷ 100 × (1 + gubici).
- **Javne punionice:** kWh koje auto primi × cijena po kWh. Gumbi iznad polja upisuju objavljene cijene mreža.
- **Gorivo:** kilometri × litara na 100 km ÷ 100 × cijena litre. Zadane su najviše maloprodajne cijene koje Vlada određuje: od {{ C.fuel.date }} Eurosuper 95 {{ money(C.fuel.petrol) }}, Eurodizel {{ money(C.fuel.diesel) }} po litri. Bez mjera Vlade bile bi {{ money(C.fuel.without_measures[0]) }} i {{ money(C.fuel.without_measures[1]) }}.
</details>

<details markdown="1"><summary>Što nije uračunato</summary>

Cijena automobila i [poticaji]({{ PAGES.subsidies.path }}), osiguranje, održavanje, cestarina, godišnja naknada za ceste (za električni osobni automobil 38,40 €), fiksne stavke računa za struju i sama kućna punionica s ugradnjom.
</details>

## Kućna punionica

Za redovito punjenje kod kuće najsigurnija je zidna punionica (wallbox) na zasebnom strujnom krugu, koju ugrađuje ovlašteni električar. Obična utičnica na produžnom kabelu nije za svakodnevno punjenje: satima radi na granici opterećenja. U stambenoj zgradi o postavljanju mjesta za punjenje odlučuju suvlasnici — [što kaže zakon]({{ PAGES.buildings.path }}). FZOEU je najavio da će poziv za građane prvi put sufinancirati i kupnju i ugradnju kućnih punionica.

{{ w.sources(C.power.sources + [{'label': C.fuel.src_label, 'url': C.fuel.src, 'date': '28. 9. 2026.'}]) }}
