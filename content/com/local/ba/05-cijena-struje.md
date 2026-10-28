---
key: electricity
slug: cijena-struje/
order: 5
nav: Cijena struje
icon: bolt
priority: 0.85
title: Cijena struje u BiH 2026. – kWh kod EPBiH, ERS i EP HZ HB | BlokVolt
description: Kilovat-sat s PDV-om noću od 0,094 KM (Elektroprivreda RS) i 0,12 KM (EPBiH), danju oko dva puta više. Sati jeftinije struje, blokovi, zone i punjenje auta.
kicker: Struja za domaćinstva
h1: Cijena struje u BiH 2026. za domaćinstva
lead: Koliko kilovat-sat struje plaća domaćinstvo kod EPBiH, Elektroprivrede RS, EP HZ HB i u Brčko distriktu — noću i danju, s naknadama i PDV-om — i od koliko sati je struja jeftinija.
card: Kilovat-sat noću i danju kod EPBiH, ERS-a, EP HZ HB i u Brčkom, sati jeftinije struje i punjenje auta.
checked: 29.10.2026.
checked_iso: 2026-10-29
related: home, prices, map
---
{% set E = C.electricity %}
{% set ep = E.rows|selectattr('id', 'equalto', 'epbih_plavi')|first %}
{% set ez = E.rows|selectattr('id', 'equalto', 'epbih_zeleni')|first %}
{% set ers = E.rows|selectattr('id', 'equalto', 'ers_bijela')|first %}
{% set erp = E.rows|selectattr('id', 'equalto', 'ers_plava')|first %}
{% set hz = E.rows|selectattr('id', 'equalto', 'hz_visa')|first %}
{% set br = E.rows|selectattr('id', 'equalto', 'brcko')|first %}
<div class="sum" markdown="1">
- **{{ money(ep.nt, 3) }}** kWh noću kod EPBiH (plavi blok), s naknadom za obnovljive izvore i PDV-om
- **{{ money(ers.nt, 3) }}** noću kod Elektroprivrede RS (bijela zona, prvih 500 kWh mjesečno)
- Danju je kilovat-sat oko **dva puta skuplji** nego noću
- **{{ money(ep.nt * 18.7) }}** struja za 100 km noću (EPBiH, plavi blok)
</div>

## Cijena kilovat-sata po snabdjevaču

| Snabdjevač | Noću | Danju |
|---|---|---|
{% for r in E.rows %}
| {{ r.name }}{% if r.range %} ({{ r.range }}){% endif %} | **{{ num(r.nt, 3) }}** | {{ num(r.vt, 3) }} |
{% endfor %}

Cijene su u KM po kWh, s PDV-om 17 %, a kod EPBiH i EP HZ HB i s naknadom za obnovljive izvore ({{ num(C.power.oie, 6) }} KM/kWh u 2026.). Cijene noću i danju važe uz dvotarifno brojilo.

- **Blokovi kod EPBiH.** Prvih 350 kWh mjesečno plaća se po zelenom bloku, od 351 do 1.000 kWh po plavom, a svaki kWh preko 1.000 po crvenom. Cijene važe od 01.09.2025.
- **Zone kod Elektroprivrede RS.** Prvih 500 kWh mjesečno ide u bijelu zonu, sljedećih 1.000 kWh u plavu, a ostatak u crvenu. Cijene važe od 01.02.2026.
- **EP HZ HB** ima višu i nižu sezonu, s cijenama od 01.01.2020. Koji mjeseci pripadaju kojoj sezoni, cjenovnik ne navodi (nije potvrđeno).
- **Brčko distrikt** ima vlastite cijene, bez blokova i zona, od 01.02.2026.

## Cijena za jednotarifno brojilo

| Snabdjevač | Cijena |
|---|---|
{% for r in E.rows %}
| {{ r.name }}{% if r.range %} ({{ r.range }}){% endif %} | {{ num(r.jt, 3) }} |
{% endfor %}

Jednotarifno brojilo ima istu cijenu cijeli dan; blokovi EPBiH i zone Elektroprivrede RS važe i za njega.

## Od koliko sati je jeftinija struja

| Snabdjevač | Niža tarifa |
|---|---|
{% for s, t in E.hours %}
| {{ s }} | {{ t }} |
{% endfor %}

Zimi znači po zimskom računanju vremena, od posljednje nedjelje u oktobru do posljednje nedjelje u martu. Nižu tarifu ima samo dvotarifno brojilo. Punjenje auta podesite tajmerom u autu ili na punjaču da počne kad počne niža tarifa.

## Koliko košta 100 kWh

| Snabdjevač | Noću | Danju |
|---|---|---|
| EPBiH, plavi blok | {{ money(ep.nt * 100) }} | {{ money(ep.vt * 100) }} |
| Elektroprivreda RS, bijela zona | {{ money(ers.nt * 100) }} | {{ money(ers.vt * 100) }} |
| EP HZ HB, viša sezona | {{ money(hz.nt * 100) }} | {{ money(hz.vt * 100) }} |
| Brčko distrikt | {{ money(br.nt * 100) }} | {{ money(br.vt * 100) }} |

S jednotarifnim brojilom 100 kWh kod EPBiH (plavi blok) košta {{ money(ep.jt * 100) }}.

## Punjenje električnog auta noću

Primjer: u bateriju ulazi 40 kWh, što je oko 235 km uz potrošnju od 17 kWh na 100 km. Zbog gubitaka pri punjenju (oko 10 %) sa brojila se potroši 44 kWh. Noću to košta:

- EPBiH, plavi blok: **{{ money(ep.nt * 44) }}** (danju {{ money(ep.vt * 44) }})
- Elektroprivreda RS, bijela zona: **{{ money(ers.nt * 44) }}**
- EP HZ HB, viša sezona: **{{ money(hz.nt * 44) }}**
- Brčko distrikt: **{{ money(br.nt * 44) }}**

Za 1.200 km mjesečno auto troši oko 224 kWh sa brojila: noću je to {{ money(ep.nt * 224.4) }} kod EPBiH i {{ money(ers.nt * 224.4) }} kod Elektroprivrede RS.

Tih 224 kWh dodaje se potrošnji domaćinstva i može ga prebaciti u skuplji blok ili zonu. Kod EPBiH je razlika mala: noću {{ num(ez.nt, 3) }} KM u zelenom i {{ num(ep.nt, 3) }} KM u plavom bloku. Kod Elektroprivrede RS kWh u plavoj zoni noću je oko {{ ((erp.nt / ers.nt - 1) * 100)|round|int }} % skuplji nego u bijeloj, pa se isplati paziti na granicu od 500 kWh. Računica za vaš auto: [kalkulator punjenja kod kuće]({{ PAGES.home.path }}).

<details markdown="1"><summary>Kako je računato</summary>

- **EPBiH:** cijena snabdijevanja i mrežarina iz kalkulatora EPBiH (cjenovnik od 01.09.2025.) + naknada za obnovljive izvore {{ num(C.power.oie, 6) }} KM/kWh, sve × 1,17 (PDV). Plavi blok noću: (0,0586 + 0,0426 + {{ num(C.power.oie, 6) }}) × 1,17 = {{ num(ep.nt, 4) }} KM.
- **Elektroprivreda RS:** energija + mrežarina iz odluke RERS-a (primjena od 01.02.2026.) × 1,17. Bijela zona noću: (0,0406 + 0,0397) × 1,17 = {{ num(ers.nt, 4) }} KM. Naknada za obnovljive izvore u Republici Srpskoj nije uračunata, jer iznos za 2026. nije potvrđen.
- **EP HZ HB:** tarifa iz cjenovnika (od 01.01.2020.) + naknada za obnovljive izvore, × 1,17.
- **Brčko distrikt:** snabdijevanje + distribucija iz odluka DERK-a (od 01.02.2026.) × 1,17; naknada za obnovljive izvore nije uračunata (nije potvrđeno da li se plaća).
- **Fiksne mjesečne stavke** (mjerno mjesto, obračunska snaga kod ERS-a, EP HZ HB i u Brčkom) plaćaju se i bez auta, pa nisu u cijeni kWh.
- **Auto:** 17 kWh na 100 km i 10 % gubitaka pri punjenju.

</details>

## Česta pitanja

<details markdown="1">
<summary>Koliko košta kilovat struje u BiH 2026.?</summary>

S PDV-om: kod EPBiH (plavi blok) {{ money(ep.nt, 3) }} noću i {{ money(ep.vt, 3) }} danju, kod Elektroprivrede RS (bijela zona) {{ money(ers.nt, 3) }} i {{ money(ers.vt, 3) }}, kod EP HZ HB (viša sezona) {{ money(hz.nt, 3) }} i {{ money(hz.vt, 3) }}, a u Brčko distriktu {{ money(br.nt, 3) }} i {{ money(br.vt, 3) }}.

</details>

<details markdown="1">
<summary>Od koliko sati je jeftinija struja?</summary>

Kod EPBiH zimi od 22 do 7 h i od 13 do 16 h, ljeti od 23 do 8 h i od 14 do 17 h, a nedjeljom cijeli dan. Kod Elektroprivrede RS zimi od 22 do 6 h, ljeti od 23 do 7 h, i vikendom od petka navečer do ponedjeljka ujutro. Niža tarifa važi samo uz dvotarifno brojilo.

</details>

<details markdown="1">
<summary>Šta su blokovi i zone na računu za struju?</summary>

To su stepenice mjesečne potrošnje. Kod EPBiH prvih 350 kWh plaća se po zelenom bloku, do 1.000 kWh po plavom, a sve preko toga po crvenom. Kod Elektroprivrede RS prvih 500 kWh je u bijeloj zoni, sljedećih 1.000 kWh u plavoj, a ostatak u crvenoj.

</details>

<details markdown="1">
<summary>Koliko košta punjenje električnog auta kod kuće?</summary>

Za 100 km treba oko 18,7 kWh sa brojila. Noću je to {{ money(ep.nt * 18.7) }} kod EPBiH (plavi blok) i {{ money(ers.nt * 18.7) }} kod Elektroprivrede RS (bijela zona). Punjenje 40 kWh u bateriju noću košta oko {{ money(ep.nt * 44) }} kod EPBiH.

</details>

## Izvori i provjera

Cijene su provjerene {{ E.checked }} na stranicama snabdjevača i regulatora. Sljedeća provjera: {{ E.next_check }}

{{ w.sources(E.sources) }}
