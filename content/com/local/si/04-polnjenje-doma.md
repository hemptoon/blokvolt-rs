---
key: home
slug: polnjenje-doma/
order: 4
nav: Doma
icon: calc
priority: 0.8
title: Koliko stane polnjenje električnega avta doma | BlokVolt
description: Kalkulator polnjenja doma z ocenjeno ceno elektrike in cenami energije GEN-I, primerjava z bencinom in dizlom, cene domačih polnilnic in pravila za polnilnico v bloku.
h1: Polnjenje doma ali na javni polnilnici
lead: Koliko na mesec stane elektrika za električni avto doma in koliko je to v primerjavi z bencinom ali dizlom — s cenami energije, cenami goriv in pravili za večstanovanjske stavbe.
card: Kalkulator s cenami elektrike, cene domačih polnilnic in polnilnica v bloku.
schema: WebPage
related: electricity, prices, subsidies
---
{{ w.calc() }}

## Kilovatna ura doma

{{ C.power.note }}

{{ w.tariffs() }}

Cene energije pri več dobaviteljih in kako se sestavi račun, so na strani [Cena elektrike]({{ PAGES.electricity.path }}).

- **Groba ocena 0,17 €/kWh** je s primerjalne strani brez datuma; v kalkulatorju jo lahko zamenjate s ceno s svojega računa (»Svoja cena«).
- **Samo energija** pri GEN-I: manjša tarifa (MT) je cenejša od višje (VT); omrežnina, prispevki in trošarina se obračunajo posebej.
- **Omrežnina** se od 1. 10. 2024 obračunava tudi po dogovorjeni moči v časovnih blokih. Večja dogovorjena moč za hitrejše polnjenje lahko poveča mesečni račun.

## Domača polnilnica: cene

{{ w.pairs(C.home_prices, 'Kaj', 'Razpon cen') }}

Vir: ceniki podjetij, preverjeno 23. 9. 2026 (npr. [Elektro Požun]({{ C.home_prices_src }})). Pri več prodajalcih je cena polnilnice z osnovno vgradnjo navedena z znižano stopnjo DDV 9,5 %. Za domačo polnilnico obstaja [Borzenova subvencija]({{ PAGES.subsidies.path }}) (55 %, do 1.000 €), vendar zaprošeni zneski že presegajo sredstva za leto 2026.

## Polnilnica v bloku

{{ w.facts_list(C.buildings) }}

<details markdown="1"><summary>Kako se računa</summary>

- **Doma:** strošek = kilometri × poraba ÷ 100 × (1 + izgube) × cena kWh. Privzeta je groba ocena skupne cene; izberete lahko tudi samo energijo pri GEN-I ali vpišete svojo ceno.
- **Javne polnilnice:** kWh, ki jih prejme avto × cena kWh; pristojbine za polnjenje in časovni dodatki niso všteti.
- **Gorivo:** kilometri × litri na 100 km ÷ 100 × cena litra. Privzete so najvišje dovoljene cene zunaj avtocest od {{ C.fuel.date }}: bencin 95 {{ money(C.fuel.petrol, 3) }}, dizel {{ money(C.fuel.diesel, 3) }} ([Vlada RS]({{ C.fuel.src }})). Vlada jih spreminja vsak teden; ob avtocestah so cene proste.
</details>

{{ w.sources(C.power.sources) }}
