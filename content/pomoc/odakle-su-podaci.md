---
id: B3
title: Odakle su podaci na mapi punjača i koliko su sveži
h1: Odakle su podaci i koliko su sveži
description: Lokacije na BlokVoltu su iz OpenStreetMap-a i Open Charge Map-a, proverene na spiskovima mreža; cene iz aplikacija i sa računa. Svaki podatak ima datum.
lead: Lokacije su iz otvorenih baza, proverene na spiskovima mreža, a cene iz aplikacija mreža i sa računa. Uz svaki podatak stoji datum, a prijave vozača vide se odmah.
kicker: Pomoć
section: mapa-i-podaci
order: 3
path: /pomoc/odakle-su-podaci/
updated: 28.09.2026
related: /pomoc/sta-znaci-potvrdjeno/, /pomoc/cene-javnog-punjenja/, /pomoc/dodajte-punjac/
shots: svg-izvori-podataka, mapa-atribucija, mapa-kartica-izvori
published: 2026-09-28
modified: 2026-09-28
---
## Izvori

1. **Otvorene baze.** Lokacije su iz OpenStreetMap-a (licenca ODbL) i Open Charge Map-a (CC BY 4.0). Isto mesto iz obe baze prikazano je jednom.
2. **Spiskovi mreža.** Svaki punjač je proveren na spiskovima koje objavljuju Charge&GO (i njena roming mapa sa punjačima Orion eMobility), Tesla i JP „Putevi Srbije“. Punjači sa tih spiskova kojih nije bilo u bazama dodati su na mapu.
3. **Google mape, samo za proveru.** Punjač sa ocenom vozača iz poslednjih godinu dana računa se kao potvrđen. Sa Google mapa se ne preuzimaju tekst, ocene ni fotografije.
4. **Ručno provereni podaci** za pojedine punjače: tačna tačka, adresa sa kućnim brojem, radno vreme, pristup i ko puni besplatno. Uz svaki stoji izvor, a podatak od vozača nosi oznaku „po vozačima“ i godinu. Nekoliko punjača potvrđeno je na sajtu vlasnika lokacije.
5. **Cene** su iz aplikacija mreža, beležene snimkom ekrana sa datumom, i sa računa za plaćena punjenja.
6. **Prijave vozača**: stanje, ocene i fotografije koje vozači šalju sa kartice punjača.

Stanje državnih punjača na autoputevima je po spisku JP „Putevi Srbije“.

<div class="flow" markdown="0">
<p class="fl-h">Put jednog punjača do mape</p>
<div class="fl-row">
<div class="fl-b"><b>OpenStreetMap</b><span>licenca ODbL</span></div>
<div class="fl-b"><b>Open Charge Map</b><span>licenca CC BY 4.0</span></div>
</div>
<div class="fl-down" aria-hidden="true"></div>
<div class="fl-row"><div class="fl-b"><b>Spajanje</b><span>isto mesto iz obe baze prikazuje se jednom</span></div></div>
<div class="fl-down" aria-hidden="true"></div>
<div class="fl-row"><div class="fl-b"><b>Provera</b><span>spiskovi mreža, Google mape, sajt vlasnika lokacije</span></div></div>
<div class="fl-down" aria-hidden="true"></div>
<div class="fl-row"><div class="fl-b ok"><b>Mapa</b><span>sa oznakom „Potvrđeno“ ili „Nije potvrđeno“ i datumom</span></div></div>
<p class="fl-note"><b>Posebno se dodaju:</b> cene iz aplikacija mreža i sa računa, sa datumom, i prijave vozača, odmah posle slanja.</p>
</div>

## Koliko su sveži

Datum stoji uz svaki podatak, pa se svežina vidi na samoj mapi:

- lokacije: datum snimka otvorenih baza stoji u dnu mape, uz izvore;
- provera na spiskovima mreža: datum je na kartici, uz „Potvrđeno“ ili „Provereno“;
- cene: datum je uz svaku cenu na kartici, a cena starija od godinu dana dobija upozorenje;
- državni punjači: uz „Stanje punjača“ stoji datum spiska JP „Putevi Srbije“;
- prijave vozača: vide se odmah posle slanja, sa vremenom prijave.

Cene javnog punjenja proveravaju se jednom mesečno.

[[shot:mapa-atribucija | Red u dnu mape: „Mapa: OpenFreeMap © OpenMapTiles · Podaci: © OpenStreetMap, Open Charge Map, JP Putevi Srbije, mreže · 23.09.2026“]]

## Gde se vidi izvor na kartici

Na dnu kartice je red „Podaci:“ sa linkovima na izvore tog punjača. U delu „Gde tačno“ piše odakle je tačka: sa spiska mreže, iz OpenStreetMap-a ili iz Open Charge Map-a. Tačka iz Open Charge Map-a može odstupati nekoliko desetina metara, a neke tačke pokazuju samo parking ili objekat.

Kad cena nije zabeležena baš na tom punjaču, kartica prikazuje cenu iste mreže za istu snagu i to piše uz cenu.

[[shot:mapa-kartica-izvori | Deo „Gde tačno“ na kartici: adresa, opis mesta, koordinate za kopiranje i napomena odakle je tačka]]

## Otvoreni podaci

Spisak punjača je otvoren skup podataka: [punjaci.json](/assets/map/punjaci.json), pod licencom ODbL. Lokacije i priključci sa spiskova mreža su u posebnom fajlu i nisu deo otvorenog skupa.

Tabele sa sajta, na primer firme i cene javnog punjenja, su na stranici [Podaci za preuzimanje](/preuzimanje/), pod licencom CC BY 4.0.

Netačan podatak ili punjač koji nedostaje prijavite kroz [formu za ispravke](/ispravka/).
