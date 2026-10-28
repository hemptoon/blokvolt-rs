---
key: electricity
slug: cijena-struje/
order: 5
nav: Cijena struje
icon: bolt
priority: 0.85
title: Cijena struje u Crnoj Gori 2026. – kWh kod EPCG-a | BlokVolt
description: Kilovat-sat kod EPCG-a s mrežom, naknadom za obnovljive izvore i PDV-om: 0,073 € noću i 0,140 € danju (osnovni model). Sati niže tarife i punjenje auta.
kicker: Struja za domaćinstva
h1: Cijena struje u Crnoj Gori 2026. za domaćinstva
lead: Koliko kilovat-sat struje plaća domaćinstvo kod EPCG-a — noću i danju, po modelima, s mrežnim naknadama i PDV-om — i od koliko sati je struja jeftinija.
card: Kilovat-sat kod EPCG-a noću i danju, po modelima, sati niže tarife i punjenje auta.
checked: 28.10.2026.
checked_iso: 2026-10-28
related: home, prices, map
---
{% set E = C.electricity %}
{% set o = E.rows|selectattr('id', 'equalto', 'osnovni')|first %}
{% set p1 = E.rows|selectattr('id', 'equalto', 'plavi150')|first %}
{% set p2 = E.rows|selectattr('id', 'equalto', 'plavi_plus')|first %}
<div class="sum" markdown="1">
- **{{ money(o.nt, 3) }}** kWh noću (osnovni model), s mrežnim naknadama, naknadom za obnovljive izvore i PDV-om
- **{{ money(o.vt, 3) }}** danju, skoro dva puta više
- Niža tarifa traje **od 23 do 7 h**, na novim brojilima i nedjeljom cijeli dan
- **{{ money(o.nt * 18.7) }}** struja za 100 km noću
</div>

## Cijena kilovat-sata po modelima

| Model EPCG-a | Noću | Danju |
|---|---|---|
{% for r in E.rows %}
| {{ r.name }} | **{{ num(r.nt, 3) }}** | {{ num(r.vt, 3) }} |
{% endfor %}

Cijene su u eurima po kWh, s mrežnim naknadama, naknadom za obnovljive izvore i PDV-om 21 %, prema cjenovniku EPCG-a od 01.01.2026. Cijene noću i danju važe uz dvotarifno brojilo. S jednotarifnim brojilom kWh cijeli dan košta {{ money(E.rows[0].jt, 3) }} u osnovnom modelu, {{ money(E.rows[1].jt, 3) }} u plavom modelu do 300 kWh mjesečno i {{ money(E.rows[2].jt, 3) }} preko toga, a {{ money(E.rows[3].jt, 3) }} u zelenom modelu.

- **Osnovni model:** jedna cijena noću i jedna danju, bez obzira na mjesečnu potrošnju.
- **Plavi model:** prvih 150 kWh mjesečno u svakoj tarifi (uz jednotarifno brojilo prvih 300 kWh) jeftinije je, a potrošnja preko toga skuplja.
- **Zeleni model** je osnovni model uz 0,2 c€ po kWh za struju iz obnovljivih izvora.
- **Crveni model** ima jednu cijenu energije u svako doba, {{ num(E.energy.crveni, 4) }} c€ po kWh bez mreže i PDV-a. Noću je to skuplje od osnovnog modela ({{ num(E.energy.osnovni_nt, 4) }} c€), pa se za punjenje auta noću ne isplati.

Uz potrošnju se plaća i fiksna mjesečna naknada za priključnu snagu: s PDV-om {{ money(E.fixed[0][1] * 1.21) }} do {{ E.fixed[0][0] }} kW, {{ money(E.fixed[1][1] * 1.21) }} od 8 do 16 kW i {{ money(E.fixed[2][1] * 1.21) }} od 16 do 34,5 kW. Ako se zbog kućnog punjača poveća odobrena snaga preko 8 kW, ta naknada raste za {{ money((E.fixed[1][1] - E.fixed[0][1]) * 1.21) }} mjesečno.

## Od koliko sati je jeftinija struja

| Brojilo | Niža tarifa |
|---|---|
{% for s, t in E.hours %}
| {{ s }} | {{ t }} |
{% endfor %}

Viša tarifa traje ostatak dana. Starija brojila imaju uklopni sat podešen po srednjoevropskom vremenu, pa se po ljetnjem računanju vremena niža tarifa pomjera za sat. Punjenje auta podesite tajmerom u autu ili na punjaču da počne u nižoj tarifi.

## Koliko košta 100 kWh

| Model | Noću | Danju |
|---|---|---|
| Osnovni | {{ money(o.nt * 100) }} | {{ money(o.vt * 100) }} |
| Plavi, prvih 150 kWh | {{ money(p1.nt * 100) }} | {{ money(p1.vt * 100) }} |
| Plavi, preko 150 kWh | {{ money(p2.nt * 100) }} | {{ money(p2.vt * 100) }} |

S jednotarifnim brojilom 100 kWh u osnovnom modelu košta {{ money(o.jt * 100) }}.

## Punjenje električnog auta noću

Primjer: u bateriju ulazi 40 kWh, što je oko 235 km uz potrošnju od 17 kWh na 100 km. Zbog gubitaka pri punjenju (oko 10 %) sa brojila se potroši 44 kWh. U osnovnom modelu to noću košta **{{ money(o.nt * 44) }}**, a danju {{ money(o.vt * 44) }}.

Za 1.200 km mjesečno auto troši oko 224 kWh sa brojila, što je noću oko {{ money(o.nt * 224.4) }}. U plavom modelu tih 224 kWh brzo pređe prvih 150 kWh niže tarife, pa se ostatak plaća {{ money(p2.nt, 3) }} po kWh. Računica za vaš auto: [kalkulator punjenja kod kuće]({{ PAGES.home.path }}).

<details markdown="1"><summary>Kako je računato</summary>

- **Formula:** (aktivna energija + angažovanje mrežnog kapaciteta + gubici u mreži + naknada za podsticanje obnovljivih izvora) × 1,21 (PDV). Noću u osnovnom modelu: (2,6212 + 1,9589 + 0,9565 + 0,4730) c€ × 1,21 = {{ num(o.nt * 100, 2) }} c€.
- **Izvor stavki:** cjenovnik EPCG-a za domaćinstva od 01.01.2026. Mrežne cijene u njemu iste su kao u odluci REGAGEN-a o cijenama CEDIS-a za 2026. Cjenovnik ne navodi PDV; cijene u regulatornim odlukama su bez PDV-a, pa je PDV dodat na zbir.
- **Gubici u prenosnom sistemu:** REGAGEN za 2026. utvrđuje i cijenu gubitaka u prenosnom sistemu za ostale korisnike ({{ num(E.cges.nt, 4) }} c€ noću i {{ num(E.cges.vt, 4) }} c€ danju po kWh). Cjenovnik EPCG-a za domaćinstva tu stavku ne navodi, pa nije uračunata; da li je ima na računu domaćinstva, nije potvrđeno.
- **Nije uračunato:** fiksna naknada za priključnu snagu i popusti EPCG-a za redovne platiše.
- **Auto:** 17 kWh na 100 km i 10 % gubitaka pri punjenju.

</details>

## Česta pitanja

<details markdown="1">
<summary>Koliko košta kilovat struje u Crnoj Gori 2026.?</summary>

U osnovnom modelu EPCG-a {{ money(o.nt, 3) }} noću i {{ money(o.vt, 3) }} danju, s mrežnim naknadama, naknadom za obnovljive izvore i PDV-om. S jednotarifnim brojilom {{ money(o.jt, 3) }} cijeli dan.

</details>

<details markdown="1">
<summary>Od koliko sati je jeftinija struja?</summary>

Niža tarifa traje od 23 do 7 h. Nova multifunkcionalna brojila računaju je tako svakog dana, a nedjeljom cijeli dan. Starija brojila s uklopnim satom po ljetnjem računanju vremena računaju je od 0 do 8 h.

</details>

<details markdown="1">
<summary>Koji model EPCG-a je povoljniji za punjenje auta noću?</summary>

Osnovni i plavi model imaju jeftiniju struju noću: od {{ money(p1.nt, 3) }} do {{ money(p2.nt, 3) }} po kWh u plavom i {{ money(o.nt, 3) }} u osnovnom modelu. Crveni model ima istu cijenu energije cijeli dan, pa je za noćno punjenje skuplji.

</details>

<details markdown="1">
<summary>Koliko košta punjenje električnog auta kod kuće?</summary>

Za 100 km treba oko 18,7 kWh sa brojila, što je noću u osnovnom modelu {{ money(o.nt * 18.7) }}. Punjenje 40 kWh u bateriju noću košta oko {{ money(o.nt * 44) }}.

</details>

## Izvori i provjera

Cijene su provjerene {{ E.checked }} na stranicama EPCG-a i REGAGEN-a. Sljedeća provjera: {{ E.next_check }}

{{ w.sources(E.sources) }}
