---
key: prices
slug: cmimet/
order: 3
nav: Çmimet
icon: coins
priority: 0.8
title: Çmimet e karikimit në Kosovë 2026 — ECHARGE dhe operatorët e tjerë | BlokVolt
description: Sa kushton karikimi në karikuesit publikë në Kosovë — ECHARGE DC 0,39–0,49 € dhe AC 0,19–0,21 € për kWh — si paguhet dhe cilët operatorë nuk publikojnë çmime.
h1: Çmimet e karikimit në Kosovë
lead: Çfarë publikojnë operatorët për çmimet dhe pagesën, dhe çfarë nuk publikohet — me burim dhe datë kontrolli.
card: Çmimet e ECHARGE, operatorët pa çmime të publikuara dhe si paguhet.
related: map, home, road
---
{% set EC = C.networks[0] %}{% set P = EC.packages %}
Në Kosovë vetëm **ECHARGE** publikon çmime për kWh: {{ num(EC.prices[2].v, 2) }}–{{ money(EC.prices[3].v) }} për karikim DC, {{ money(EC.prices[0].v) }} ditën dhe {{ money(EC.prices[1].v) }} natën për AC. **HIB Petrol**, **RapidCharge** dhe **Shell** nuk publikojnë çmim. ECHARGE nuk shkruan nëse çmimet përfshijnë TVSH-në, cili stacion ka cilin çmim DC dhe cilat janë orët e ditës dhe të natës. Rrjetet janë renditur sipas alfabetit. Tabela u kontrollua më {{ C.checked }}.

{{ w.price_table() }}

## Rrjetet

{{ w.net_cards() }}

## Abonimet mujore të ECHARGE

ECHARGE ofron edhe abonime mujore: {{ P[0][0] }} për {{ money(P[0][1]) }} me „{{ P[0][2] }} kW të përfshira”, {{ P[1][0] }} për {{ money(P[1][1]) }} me „{{ P[1][2] }} kW” dhe {{ P[2][0] }} për {{ money(P[2][1]) }} me „{{ P[2][2] }} kW”. Operatori shkruan „kW”; nëse njësia është kWh, kilovat-ora në pako del rreth {{ money(P[0][1] / P[0][2]) }} te {{ P[0][0] }} dhe {{ P[1][0] }} dhe {{ money(P[2][1] / P[2][2]) }} te {{ P[2][0] }} (llogaritur: çmimi i pakos ÷ sasia e përfshirë). Çmimi për kWh përtej pakos nuk publikohet. Për karikimin pa abonim operatori shkruan: „Paguan vetëm për kWh që merr realisht, pa abonim të detyrueshëm.”

## Karikim falas

{{ C.market.text }} Burimi: [{{ C.market.src_label }}]({{ C.market.src }}).

## Karikues të tjerë

{{ w.pairs(C.other_sites, 'Kush', 'Çfarë dihet') }}

## Sa kushtojnë 100 km

Me 17 kWh në 100 km: te ECHARGE me AC {{ num(EC.prices[1].v * 17, 2) }}–{{ money(EC.prices[0].v * 17) }}, me DC {{ num(EC.prices[2].v * 17, 2) }}–{{ money(EC.prices[3].v * 17) }}. Në shtëpi natën, me konsum deri në 800 kWh në muaj, rreth {{ money(C.power.tariffs[0].allin * 17 * 1.1) }}, me TVSH dhe 10 % humbje. Për veturën dhe kilometrat tuaja: [kalkulatori]({{ PAGES.home.path }}).

## Si paguhet

- **ECHARGE:** faqja e operatorit përmend aplikacionin ECHARGE; pagesa pa aplikacion (me kartelë në terminal, me kod QR ose në ueb) nuk përmendet.
- **RapidCharge:** në aplikacionin Rapid Charge, me kartelë krediti ose debiti ose me pagesë digjitale.
- **HIB Petrol dhe Shell:** mënyra e pagesës nuk publikohet; pyetni në pikën e karburantit.
- **Lidhësit:** ECHARGE shkruan se ka CCS2, Type 2 dhe „në disa stacione GB/T”. Nëse vetura juaj ka prizë GB/T, kontrolloni stacionin para nisjes.

Nëse keni një foto të çmimit nga aplikacioni ose nga fatura, me datë dhe vend, dërgojeni në [hello@blokvolt.com](mailto:hello@blokvolt.com?subject=%C3%87mimi%20i%20karikimit%20XK) — publikohet me datën.
