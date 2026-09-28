---
key: home
slug: karikimi-ne-shtepi/
order: 4
nav: Në shtëpi
icon: calc
priority: 0.9
title: Karikimi në shtëpi në Kosovë — kalkulatori me tarifat e ZRRE-së | BlokVolt
description: Kalkulatori i kostos së karikimit me tarifat e ZRRE-së nga 01.05.2025 (deri dhe mbi 800 kWh, ditën e natën), çmimet e ECHARGE dhe krahasimi me karburantin.
h1: Karikimi në shtëpi apo në karikues publik
lead: Sa kushton në muaj karikimi i veturës elektrike në shtëpi dhe në karikuesit publikë, dhe sa kushton për të njëjtat kilometra një makinë me benzinë ose naftë.
card: Kalkulatori me tarifat e ZRRE-së, çmimet e ECHARGE dhe krahasimi me karburantin.
schema: WebPage
related: prices, subsidies, map
---
{% set TR = C.power.tariffs %}{% set X = C.power.example.kwh %}
{{ w.calc() }}

## Kilovat-ora në shtëpi

{{ C.power.note }}

{{ w.tariffs() }}

- **Blloqet.** {{ C.power.blocks }} {{ C.power.night_conflict }}
- **Pragu i 800 kWh.** Një veturë që bën rreth {{ num(1100) }} km në muaj kërkon rreth {{ X }} kWh nga priza. Nëse shtëpia pa veturën konsumon më shumë se {{ 800 - X }} kWh në muaj, një pjesë e këtyre kWh ose të gjitha bien në bllokun e dytë.
- **Tarifa e lartë dhe e ulët.** {{ C.power.nt_hours }} Në bllokun e parë karikimi natën kushton më pak se gjysma e karikimit ditën.
- **Tarifa fikse.** Sipas një burimi të vetëm ([{{ C.power.fixed.src_label }}]({{ C.power.fixed.src }})), tarifa fikse mujore është {{ money(C.power.fixed.v) }} për konsumator; u rrit nga {{ money(C.power.fixed.prev) }} me vendimin e tarifave të prillit 2025. Nuk thuhet nëse përfshin TVSH-në. E paguani edhe pa veturë, prandaj kalkulatori nuk e llogarit.

**Shembull.** Për {{ X }} kWh në muaj, me TVSH dhe pa tarifën fikse: natën {{ money(TR[0].allin * X) }}, ditën {{ money(TR[1].allin * X) }}. Nëse këto kWh bien mbi 800 kWh: natën {{ money(TR[2].allin * X) }}, ditën {{ money(TR[3].allin * X) }} — duke supozuar se blloku i dytë vlen vetëm për kWh mbi 800 (llogaritur).

<details markdown="1"><summary>Si llogaritet</summary>

- **Në shtëpi:** çmimi i energjisë sipas bllokut dhe tarifës × 1,08 (TVSH). Rryma nga priza = kilometrat × konsumi ÷ 100 × pjesa e karikimit në shtëpi × (1 + humbjet).
- **Karikuesit publikë:** kWh që merr vetura × çmimi për kWh. Butonat mbi fushë plotësojnë çmimet e publikuara të ECHARGE.
- **Karburanti:** kilometrat × litrat në 100 km ÷ 100 × çmimi i litrit. Të paracaktuara janë çmimet orientuese të Petrol Company më {{ C.fuel.date }}: benzinë {{ money(C.fuel.petrol) }} dhe naftë {{ money(C.fuel.diesel) }} për litër ({{ money(C.fuel.diesel_bulk) }} për blerje mbi 100 litra). Çmim zyrtar i karburantit nuk u gjet; Periskopi më {{ C.fuel.alt.date }} shkruante për naftë {{ money(C.fuel.alt.diesel) }} dhe benzinë {{ money(C.fuel.alt.petrol) }}. Nuk thuhet nëse çmimet përfshijnë TVSH-në.
</details>

<details markdown="1"><summary>Çfarë nuk është llogaritur</summary>

Çmimi i veturës, dogana dhe TVSH-ja në import ([lehtësitë]({{ PAGES.subsidies.path }})), sigurimi, mirëmbajtja, regjistrimi, tarifa fikse e faturës së rrymës dhe vetë karikuesi shtëpiak me instalimin.
</details>

## Karikuesi në ndërtesë banimi

Për ndërtesat me shumë banesa vlen Ligji nr. 03/L-091 për shfrytëzimin, administrimin dhe mirëmbajtjen e ndërtesës në bashkëpronësi. Ligji nuk përmend as garazhet, as parkingjet, as karikuesit për vetura elektrike.

{{ w.facts_list(C.buildings) }}

Nëse vendosja e karikuesit në garazhin e përbashkët llogaritet ndryshim në bashkëpronësinë e ndërtesës (neni 32), duhet pëlqimi i të gjithë pronarëve; nëse llogaritet punë e administrimit të rregullt, mjafton shumica e pronarëve me më shumë se 50 % të bashkëpronësisë (neni 14). Ligji nuk e thotë cila vlen. Nëse karikuesi prek instalimin ose njehsorin e përbashkët, prisni që të nevojitet vendimi i bashkësisë së pronarëve.

<p class="note">Kjo është përmbledhje e ligjit, jo këshillë juridike. Teksti i ligjit u kontrollua më {{ C.checked }}.</p>

{{ w.sources(C.power.sources + [{'label': 'Petrol Company — çmimet orientuese të karburantit', 'url': C.fuel.src, 'date': C.fuel.date}, {'label': 'Periskopi — çmimet e naftës dhe benzinës', 'url': C.fuel.alt.src, 'date': C.fuel.alt.date}, C.buildings_src]) }}
