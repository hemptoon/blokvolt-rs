---
id: B1
title: Kako radi mapa punjača: boje, filteri i pretraga
h1: Kako radi mapa: boje, filteri i pretraga
description: Šta znače boje tačaka na mapi punjača BlokVolt i kako rade filteri Brzi, AC, CHAdeMO, Besplatni i Potvrđeni, pretraga, „Blizu mene“ i kartica punjača.
lead: Boja tačke pokazuje vrstu punjača, filteri iznad liste sužavaju izbor, a pretraga traži po gradu, adresi ili mreži. Dodir na tačku ili red u listi otvara karticu punjača.
kicker: Pomoć
section: mapa-i-podaci
order: 1
path: /pomoc/kako-radi-mapa/
updated: 28.09.2026
related: /pomoc/sta-znaci-potvrdjeno/, /pomoc/konektori-i-filteri/, /pomoc/cene-javnog-punjenja/
shots: mapa-pregled, mapa-legenda, mapa-filteri-mobilni, mapa-kartica-mobilni
published: 2026-09-28
modified: 2026-09-28
---
## Boje i oznake

[[shot:mapa-pregled | Mapa na računaru: levo pretraga, filteri i lista punjača, desno mapa sa legendom i dugmetom „Blizu mene“]]

Legenda je u gornjem levom uglu mape.

| Oznaka | Kako izgleda i šta znači |
|---|---|
| DC | tamna tačka sa žutozelenim obodom: punjač jednosmerne struje |
| AC | bela tačka sa tamnim obodom: punjač naizmenične struje |
| Besplatno | žutozelena tačka |
| Ne radi | svetlosiva tačka: državni punjač koji po spisku JP „Putevi Srbije“ ne radi ili punjač sa prijavljenim kvarom |
| Samo Tesla | siva tačka sa slovom „T“ |
| Nije potvrđeno | bleda tačka, uz snagu stoji „?“ |

Kad je mapa umanjena, punjači su grupisani u tamne krugove sa brojem. Dodir na krug uvećava taj deo mape. Kad mapu uvećate do nivoa grada, u tački piše snaga u kW, a pored nje cena.

Zeleni prsten oko tačke označava punjač koji ste sačuvali u omiljene.

[[shot:mapa-legenda | Legenda mape (DC, AC, Besplatno, Ne radi, Samo Tesla, Nije potvrđeno) i primer tačaka sa snagom i cenom pored njih]]

## Filteri

Iznad liste su dugmad: Svi, Omiljeni, Brzi (DC ≥ 50 kW), AC, CHAdeMO, Besplatni i mreže sa brojem punjača. Od njih je uključeno jedno.

„Potvrđeni“ i „Imam Teslu“ su prekidači i rade uz bilo koji filter, na primer Brzi i Potvrđeni zajedno. Izbor „Imam Teslu“ pregledač pamti i za sledeću posetu.

Iznad liste piše koliko punjača odgovara izboru, na primer „Prikazano 45 od 240“. Ako piše „Nema punjača za ovaj izbor.“, izaberite „Svi“ ili isključite „Potvrđeni“.

[[shot:mapa-filteri-mobilni | Vrh mape na telefonu: pretraga i čipovi iznad liste, uključen „Brzi (DC ≥ 50 kW)“]]

## Pretraga i „Blizu mene“

Polje „Grad, adresa ili mreža“ traži po nazivu, adresi, mestu i mreži. Kvačice nisu potrebne: „cacak“ nalazi „Čačak“. Kad upišete više reči, prikazuju se punjači koji sadrže sve.

„Blizu mene“ traži vašu lokaciju tek kad ga pritisnete. Lista se tada ređa od najbližeg punjača, sa udaljenošću u km. Lokacija se ne šalje sajtu.

Kad uvećate deo mape, lista prikazuje samo punjače na tom delu („U ovom delu mape“). Dugme „Cela Srbija“ vraća celu listu.

## Korak po korak: od mape do punjača

1. Otvorite [mapu](/mapa/) i izaberite filter ili upišite grad.
2. Dodirnite tačku ili red u listi. Otvara se kartica: provera, cena, priključci i „Gde tačno“.
3. Pogledajte oznaku provere i deo „Iskustva vozača“ sa poslednjom prijavom ([šta znači „Potvrđeno“](/pomoc/sta-znaci-potvrdjeno/)).
4. Pritisnite „Navigacija“. Na Apple uređajima otvara se Apple Maps, na ostalim Google Maps. Ispod dugmeta je link za Waze, a na Apple uređajima i za Google Maps.
5. Zvezdica u vrhu kartice čuva punjač u omiljene. Spisak je samo u ovom pregledaču, a otvara ga filter „Omiljeni“.

Na telefonu je mapa gore, a lista ispod nje. Kartica se otvara od dna ekrana, a „Podeli“ šalje ili kopira link na nju.

[[shot:mapa-kartica-mobilni | Otvorena kartica punjača na telefonu: naziv, „Potvrđeno“, cena, priključci, dugmad „Navigacija“, „Prijavi grešku“, „Podeli“ i zvezdica]]

<details markdown="1">
<summary>Detalji: „Gde tačno“ i linkovi sa gotovim izborom</summary>

„Gde tačno“ prikazuje adresu, opis kako da nađete punjač (gde je proveren), koordinate sa dugmetom „Kopiraj“, zapis u stepenima za navigaciju u autu i Plus Code. Ispod piše odakle je tačka: sa spiska mreže, iz OpenStreetMap-a, iz Open Charge Map-a ili je to približna tačka parkinga ili objekta.

Mapa se otvara sa gotovim izborom preko linka:

- `/mapa/?grad=novi-sad` — mapa na tom gradu, lista od najbližeg (beograd, novi-sad, nis, subotica, cacak, kragujevac);
- `/mapa/?mreza=chargego` — samo jedna mreža;
- `/mapa/?f=fast` — filter Brzi; isto i `ac`, `chademo`, `free`, `fav`;
- `/mapa/?ok=1` — samo potvrđeni; `/mapa/?tesla=1` — „Imam Teslu“ samo za taj pregled;
- `/mapa/#cg-80` — odmah otvara karticu tog punjača; takav link daje dugme „Podeli“.

</details>
