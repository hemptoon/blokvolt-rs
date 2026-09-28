---
id: B9
title: Cene javnog punjenja: odakle su i zašto se razlikuju
h1: Odakle su cene i zašto se razlikuju
description: Cene na mapi BlokVolt su iz aplikacija mreža i sa računa, uz datum. Zašto se plaća po minutu, šta znači „~“ uz cenu i zašto je isti punjač skuplji u romingu.
lead: Cene su iz aplikacija mreža i sa računa, uz datum. Mreže naplaćuju po minutu, pa cena po kWh zavisi od snage kojom vaš auto puni.
kicker: Pomoć
section: mapa-i-podaci
order: 5
path: /pomoc/cene-javnog-punjenja/
updated: 28.09.2026
related: /pomoc/kalkulator-troskova/, /pomoc/konektori-i-filteri/, /pomoc/odakle-su-podaci/
shots: mapa-cena-kartica, mapa-cene-pored-tacaka, svg-cena-po-minutu
published: 2026-09-28
modified: 2026-09-28
---
## Odakle su cene

Mreže ne objavljuju cenovnike na svojim sajtovima, pa se cena vidi tek u aplikaciji. Cene se jednom mesečno čitaju iz aplikacija mreža, uz snimak ekrana sa datumom, i sa računa za plaćena punjenja.

Kad cena nije zabeležena baš na tom punjaču, kartica prikazuje cenu iste mreže za istu snagu. Sve zabeležene cene, sa mestom i datumom, su na stranici [Javno punjenje](/javno-punjenje/).

## Zašto se plaća po minutu

Po čl. 210v Zakona o energetici punjenje je usluga, a ne prodaja struje. Uredba o merenju još nije doneta, pa mreže naplaćuju vreme.

Zato kWh košta više kad auto puni sporije. Auto koji na brzom punjaču prima 50 kW plaća po kWh duplo više od auta koji prima 100 kW.

<div class="flow calc-ex" markdown="0">
<p class="fl-h">Ista cena po minutu, dva auta</p>
<p class="fl-f">cena po kWh = cena po minutu × 60 ÷ snaga u kW</p>
<div class="fl-row">
<div class="fl-b"><b>Auto prima 50 kW</b><span>100 RSD/min × 60 ÷ 50 = <strong>120 RSD po kWh</strong></span></div>
<div class="fl-b ok"><b>Auto prima 100 kW</b><span>100 RSD/min × 60 ÷ 100 = <strong>60 RSD po kWh</strong></span></div>
</div>
<p class="fl-note">Primer sa okruglom cenom od 100 RSD po minutu. Snaga je ono što auto zaista prima, a ne najveća snaga punjača.</p>
</div>

## Kako da čitate cenu na mapi

Kad uvećate mapu do nivoa grada, pored tačke piše:

- „0 RSD“: punjenje je besplatno;
- „56-60 RSD/kWh“: po računima sa tog punjača, ne starijim od 90 dana;
- „~68 RSD/kWh“: procena iz cene po minutu, za snagu koju auto realno dobija;
- „?“: cena nije poznata.

Sivi natpis znači da je cena nepoznata ili starija od godinu dana. Na kartici je cena sa izvorom i datumom i procena, na primer „≈ 68 RSD po kWh ako auto puni sa 90 kW“. Starija cena ima upozorenje „Cena je starija od godinu dana. Proverite u aplikaciji mreže.“

[[shot:mapa-cena-kartica | Deo „Cena“ na kartici DC punjača: cena po minutu, procena po kWh za snagu koju auto realno dobija, izvor i datum, zauzeće posle punjenja]]

[[shot:mapa-cene-pored-tacaka | Mapa uvećana na grad, sa natpisima pored tačaka: „0 RSD“, „~68 RSD/kWh“, „56-60 RSD/kWh“ i „?“]]

<details markdown="1">
<summary>Detalji: sa kojom snagom se računa procena</summary>

Procena deli cenu po minutu snagom koju auto realno dobija na toj vrsti punjača, a ne snagom sa natpisa: DC 30 kW → 30 kW, 50 → 45, 60 → 50, 110–120 → 90, 150–180 → 100, 240 → 130 kW; između tih vrednosti snaga se računa srazmerno. Za AC punjač računa se 11 kW. Formula: cena po minutu × 60 ÷ snaga.

</details>

## Zašto se ista stanica razlikuje

- **Roming.** Isti punjač u tuđoj aplikaciji može biti skuplji. Na punjaču Super Vero Novi Sad (DC 150 kW), 22.09.2026: 197 RSD/min i 140 RSD za priključenje u aplikaciji Orion eMobility, a 114,17 RSD/min u aplikaciji Charge&GO.
- **Priključenje.** Orion eMobility na svojim punjačima naplaćuje i 50 RSD po punjenju.
- **Zauzeće posle punjenja.** Charge&GO i Orion eMobility naplaćuju 5 RSD po minutu posle 15 minuta.
- **Jedinica.** Emobility Spectra naplaćuje po „jedinici“, koja nije kWh.

Tačnu cenu pre punjenja pokazuje aplikacija mreže.

## Šta da pošaljete

Za noviju cenu pošaljite snimak ekrana iz aplikacije na hello@blokvolt.com; forma za ispravke prima samo tekst i link. Na snimku treba da se vide:

- naziv stanice i snaga punjača;
- cena po minutu, po kWh ili ukupan iznos računa;
- datum i mesto.

Ime, e-adresu i broj kartice na snimku možete prekriti; za cenu nisu potrebni.
