---
key: home
slug: karikimi-ne-shtepi/
order: 4
nav: Në shtëpi
icon: calc
priority: 0.9
title: Karikimi i makinës elektrike në shtëpi — kalkulatori, tarifat e ERE-së | BlokVolt
description: Kalkulatori me tarifat e ERE-së për 2026 (8,5 dhe 9,5 lekë plus TVSH), pragu i 700 kWh, karikimi publik, krahasimi me karburantin dhe karikuesi në pallat.
h1: Karikimi në shtëpi apo në karikues publik
lead: Sa kushton në muaj energjia për makinën elektrike në shtëpi dhe në karikuesit publikë, krahasuar me benzinën ose naftën — me tarifat e ERE-së për vitin 2026.
card: Kalkulatori me tarifat e ERE-së, pragun e 700 kWh dhe krahasimin me karburantin; karikuesi në pallat.
schema: WebPage
related: prices, subsidies, map
---
{{ w.calc() }}

## Kilovat-ora në shtëpi

{{ C.power.note }}

{{ w.tariffs() }}

- **Pragu i 700 kWh.** {{ C.power.blocks }}
- **Pa tarifë nate.** {{ C.power.nt_hours }}
- **Pa tarifë fikse.** Tabela e ERE-së për vitin 2026 nuk ka tarifë fikse mujore për familjet dhe asnjë burim tjetër nuk përmend të tillë.

**Shembull.** Makina merr nga priza {{ C.power.example.ev_kwh }} kWh në muaj, mjaftueshëm për rreth {{ num(1070) }} km me 17 kWh për 100 km dhe 10 % humbje. Shumat janë me TVSH.

- Familja mbetet deri në 700 kWh edhe me makinën: {{ C.power.example.ev_kwh }} kWh kushtojnë {{ money(C.power.example.stay, 0) }}.
- Familja konsumonte {{ C.power.example.house }} kWh dhe me makinën arrin {{ C.power.example.total }} kWh: fatura rritet nga {{ money(C.power.example.before, 0) }} në {{ money(C.power.example.after, 0) }}, pra {{ money(C.power.example.diff, 0) }} më shumë, {{ money(C.power.example.per_kwh, 1) }} për çdo kWh të makinës.
- Familja ishte tashmë mbi 700 kWh: {{ C.power.example.ev_kwh }} kWh kushtojnë {{ money(C.power.example.above, 0) }}.

<details markdown="1"><summary>Si llogaritet</summary>

- **Në shtëpi:** çmimi i ERE-së × 1,2 (TVSH 20 %). Energjia nga priza = kilometrat × konsumi ÷ 100 × (1 + humbjet).
- **Pragu i 700 kWh:** rritja e faturës ndahet me kilovat-orët e makinës. Për shembullin: (750 × 9,5 − 550 × 8,5) × 1,2 ÷ 200 = 14,7 lekë për kWh. Vlera ndryshon sipas konsumit të familjes dhe të makinës.
- **Karikuesit publikë:** kWh që merr makina × çmimi për kWh. Rrjetet nuk publikojnë çmime; si vlerë fillestare është vendosur kufiri i sipërm i vlerësimit të OSHEE-së, {{ money(C.calc.pub, 0) }} për kWh.
- **Karburanti:** kilometrat × litrat për 100 km ÷ 100 × çmimi i litrit. Janë vendosur çmimet maksimale të Bordit të Transparencës nga {{ C.fuel.date }}: benzinë {{ money(C.fuel.petrol, 0) }}, naftë {{ money(C.fuel.diesel, 0) }} për litër ([{{ C.fuel.src_label }}]({{ C.fuel.src }})). Raportimet nuk thonë nëse çmimet përfshijnë TVSH.
</details>

## Karikuesi në pallat

Administrimin e pjesëve të përbashkëta në pallate e rregullon Ligji nr. 55/2025. Ligji nuk i përmend karikuesit e makinave elektrike, as garazhet si të tilla, as të drejtën e një pronari për të vendosur karikues me shpenzimet e veta.

{{ w.facts_list(C.buildings) }}

Cila nga këto dispozita vlen për një karikues në garazhin ose në parkimin e përbashkët, ligji nuk e thotë. Nëse karikuesi prek pjesët e përbashkëta, si instalimin elektrik ose matësin e përbashkët, kini parasysh që do t’ju duhet miratimi i asamblesë së bashkëpronarëve. Kjo është një përmbledhje e ligjit, jo këshillë ligjore.

{{ w.sources(C.power.sources) }}
