---
key: electricity
slug: cijena-struje/
order: 6
nav: Cijena struje
icon: bolt
priority: 0.85
title: Cijena struje u Hrvatskoj 2026. – kWh kod HEP-a, Bijeli i Plavi | BlokVolt
description: Kilovatsat s mrežarinom, OIE i PDV-om noću od 0,101 € (tarifni model Bijeli), danju 0,199 €, jednotarifno 0,177 €. Prag od 3.000 kWh, sati niže tarife i punjenje auta.
kicker: Struja za kućanstva
h1: Cijena struje u Hrvatskoj 2026. za kućanstva
lead: Koliko kilovatsat struje stoji kućanstvo u univerzalnoj usluzi HEP Elektre od 1. 10. 2026. do 31. 3. 2027. — noću i danju, s mrežnim naknadama, naknadom za obnovljive izvore i PDV-om — kada počinje niža tarifa i što znači prag od 3.000 kWh.
card: Kilovatsat noću i danju na tarifnim modelima Bijeli i Plavi, prag od 3.000 kWh, sati niže tarife i punjenje auta.
checked: 9. 11. 2026.
checked_iso: 2026-11-09
related: home, prices, map
---
{% set E = C.electricity %}
{% set bi = E.rows|selectattr('id', 'equalto', 'bijeli')|first %}
{% set bh = E.rows|selectattr('id', 'equalto', 'bijeli_hi')|first %}
{% set pl_ = E.rows|selectattr('id', 'equalto', 'plavi')|first %}
{% set ph = E.rows|selectattr('id', 'equalto', 'plavi_hi')|first %}
<div class="sum" markdown="1">
- **{{ money(bi.nt, 3) }}** kWh noću na tarifnom modelu Bijeli, sa svim naknadama i PDV-om
- **{{ money(bi.vt, 3) }}** danju na Bijelom, **{{ money(pl_.jt, 3) }}** po jedinstvenoj tarifi (Plavi)
- Iznad **3.000 kWh u šest mjeseci** energija je 35 % skuplja
- **{{ money(bi.nt * 18.7) }}** struja za 100 km noću (Bijeli, ispod praga)
</div>

## Cijena kilovatsata po tarifnom modelu

| Tarifni model | Noću (NT) | Danju (VT) | Jedinstvena (JT) |
|---|---|---|---|
{% for r in E.rows %}
| {{ r.name }}, {{ r.range }} | {% if r.nt %}**{{ num(r.nt, 3) }}**{% else %}—{% endif %} | {% if r.vt %}{{ num(r.vt, 3) }}{% else %}—{% endif %} | {% if r.jt %}**{{ num(r.jt, 3) }}**{% else %}—{% endif %} |
{% endfor %}

Cijene su u eurima po kWh, s PDV-om od {{ C.power.vat }} %. U svakoj su četiri dijela: radna energija koju određuje Vlada, naknade za distribuciju i prijenos koje određuje HERA i naknada za obnovljive izvore ({{ num(C.power.oie, 6) }} € po kWh bez PDV-a).

- **Bijeli** je tarifni model s dvotarifnim brojilom: noću je kilovatsat otprilike upola jeftiniji nego danju.
- **Plavi** je jedinstvena tarifa — ista cijena cijeli dan.
- **Razdoblje.** Cijene energije vrijede u razdoblju {{ E.period }} (Uredba, NN 101/2026). Mrežne naknade vrijede od 1. 1. 2026.
- Postoje i tarifni modeli Crveni (s mjerenjem snage) i Crni (akumulacijsko grijanje); ova stranica ih ne prikazuje.

## Prag od 3.000 kWh

Cijene označene s „do 3.000 kWh” vrijede dok kućanstvo u šest mjeseci (od 1. 10. 2026. do 31. 3. 2027.) ne potroši više od 3.000 kWh, što je u prosjeku 500 kWh mjesečno. Za potrošnju iznad praga radna energija je 35 % skuplja; mrežne naknade i naknada za obnovljive izvore ostaju iste. Skuplja je samo razlika iznad 3.000 kWh, ne cijela potrošnja.

Auto koji prijeđe 1.200 km mjesečno doda oko 224 kWh mjesečno, odnosno oko 1.350 kWh u šest mjeseci. Ako kućanstvo i bez auta troši blizu 500 kWh mjesečno, dio punjenja prelazi prag: noću na Bijelom tada se plaća {{ money(bh.nt, 3) }} umjesto {{ money(bi.nt, 3) }} po kWh.

## Od koliko sati je jeftinija struja

| Razdoblje | Niža tarifa |
|---|---|
{% for s, t in E.hours %}
| {{ s }} | {{ t }} |
{% endfor %}

Zimsko računanje vremena traje od posljednje nedjelje u listopadu do posljednje nedjelje u ožujku. Nižu tarifu ima samo dvotarifno brojilo (tarifni model Bijeli). Punjenje auta podesite tajmerom u autu ili na punionici da počne u 21 h zimi, odnosno u 22 h ljeti.

## Koliko stoji 100 kWh

| Tarifni model | Ispod praga | Iznad praga |
|---|---|---|
| Bijeli, noću | {{ money(bi.nt * 100) }} | {{ money(bh.nt * 100) }} |
| Bijeli, danju | {{ money(bi.vt * 100) }} | {{ money(bh.vt * 100) }} |
| Plavi, jedinstvena tarifa | {{ money(pl_.jt * 100) }} | {{ money(ph.jt * 100) }} |

## Punjenje električnog auta noću

Primjer: u bateriju ulazi 40 kWh, što je oko 235 km uz potrošnju od 17 kWh na 100 km. Zbog gubitaka pri punjenju (oko 10 %) s brojila se potroši 44 kWh. To stoji:

- Bijeli, noću: **{{ money(bi.nt * 44) }}** (iznad praga {{ money(bh.nt * 44) }})
- Bijeli, danju: {{ money(bi.vt * 44) }}
- Plavi, jedinstvena tarifa: {{ money(pl_.jt * 44) }}

Za 1.200 km mjesečno auto troši oko 224 kWh s brojila: noću na Bijelom to je {{ money(bi.nt * 224.4) }}, a po jedinstvenoj tarifi {{ money(pl_.jt * 224.4) }}. Računica za vaš auto, s cijenama javnih punionica i goriva: [kalkulator punjenja kod kuće]({{ PAGES.home.path }}).

<details markdown="1"><summary>Kako je računato</summary>

- **Formula:** (radna energija + distribucija + prijenos + naknada za obnovljive izvore) × 1,13 (PDV).
- **Radna energija** (Uredba NN 101/2026, od 1. 10. 2026. do 31. 3. 2027.): Bijeli danju {{ num(E.energy.bijeli_vt, 6) }}, noću {{ num(E.energy.bijeli_nt, 6) }}, Plavi {{ num(E.energy.plavi, 6) }} € po kWh; iznad praga × 1,35.
- **Distribucija** (HERA, NN 150/2025, od 1. 1. 2026.): Bijeli danju {{ num(E.network.dist_vt, 6) }}, noću {{ num(E.network.dist_nt, 6) }}, Plavi {{ num(E.network.dist_jt, 6) }} €. **Prijenos** (NN 150/2025): Bijeli danju {{ num(E.network.tr_vt, 6) }}, noću {{ num(E.network.tr_nt, 6) }}, Plavi {{ num(E.network.tr_jt, 6) }} €.
- **Primjer, Bijeli noću:** ({{ num(E.energy.bijeli_nt, 6) }} + {{ num(E.network.dist_nt, 6) }} + {{ num(E.network.tr_nt, 6) }} + {{ num(C.power.oie, 6) }}) × 1,13 = {{ num(bi.nt, 4) }} €.
- **Fiksne mjesečne stavke** (mjerno mjesto i opskrba, oko {{ money(C.power.fixed_month) }} mjesečno s PDV-om) plaćaju se i bez auta, pa nisu u cijeni kWh.
- **Auto:** 17 kWh na 100 km i 10 % gubitaka pri punjenju.

</details>

## Česta pitanja

<details markdown="1">
<summary>Koliko stoji kilovatsat struje u Hrvatskoj 2026.?</summary>

Sa svim naknadama i PDV-om, od 1. 10. 2026. do 31. 3. 2027.: na tarifnom modelu Bijeli {{ money(bi.nt, 3) }} noću i {{ money(bi.vt, 3) }} danju, a po jedinstvenoj tarifi (Plavi) {{ money(pl_.jt, 3) }}. Za potrošnju iznad 3.000 kWh u šest mjeseci: {{ money(bh.nt, 3) }}, {{ money(bh.vt, 3) }} i {{ money(ph.jt, 3) }}.

</details>

<details markdown="1">
<summary>Od koliko sati je jeftinija struja?</summary>

Zimi od 21 do 7 h, ljeti od 22 do 8 h. Niža tarifa vrijedi samo uz dvotarifno brojilo (tarifni model Bijeli).

</details>

<details markdown="1">
<summary>Što je prag od 3.000 kWh?</summary>

Uredba određuje cijenu energije za kućanstva do 3.000 kWh potrošnje u šest mjeseci (od 1. 10. 2026. do 31. 3. 2027.). Za svaki kWh iznad toga radna energija je 35 % skuplja.

</details>

<details markdown="1">
<summary>Koliko stoji punjenje električnog auta kod kuće?</summary>

Za 100 km treba oko 18,7 kWh s brojila. Noću na Bijelom to je {{ money(bi.nt * 18.7) }}, a po jedinstvenoj tarifi {{ money(pl_.jt * 18.7) }}. Punjenje 40 kWh u bateriju noću stoji oko {{ money(bi.nt * 44) }}.

</details>

## Izvori i provjera

Cijene su provjerene {{ E.checked }} u Narodnim novinama i na stranicama HEP-a i HERA-e. Sljedeća provjera: {{ E.next_check }}

{{ w.sources(E.sources) }}
