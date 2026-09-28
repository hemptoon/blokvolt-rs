---
id: B10
title: Kalkulator troškova: šta računa i šta pretpostavlja
h1: Kalkulator troškova: šta pretpostavlja
description: Kako kalkulator BlokVolt računa trošak struje kod kuće i na javnim punjačima i poredi ga sa benzinom: formule, početne vrednosti i šta nije uračunato.
lead: Kalkulator množi kilometre i potrošnju auta cenom kWh kod kuće i na javnim punjačima i poredi to sa gorivom. Rezultat je procena, a ne račun.
kicker: Pomoć
section: mapa-i-podaci
order: 6
path: /pomoc/kalkulator-troskova/
updated: 28.09.2026
related: /pomoc/cene-javnog-punjenja/, /pomoc/odakle-su-podaci/
shots: kalkulator-unos, kalkulator-rezultat
published: 2026-09-28
modified: 2026-09-28
---
## Korak po korak

1. Otvorite [kalkulator troškova](/alati/kalkulator-troskova/). Upišite kilometre mesečno i potrošnju auta u kWh na 100 km; potrošnja piše u računaru automobila.
2. Izaberite zonu sa računa EPS-a i tarifu, noć ili dan. Druga mogućnost je „Upisaću cenu sa računa“, pa upišite svoju cenu kWh.
3. Klizačem podesite deo punjenja na javnim punjačima i izaberite cenu: brzi DC, AC ili besplatni državni punjač. Možete upisati i svoju cenu po kWh.
4. Za poređenje izaberite benzin ili dizel, potrošnju u litrima i cenu litra.

Rezultat se menja odmah: trošak električnog auta mesečno i na 100 km, trošak goriva i razlika mesečno i godišnje.

[[shot:kalkulator-unos | Polja kalkulatora: kilometri, potrošnja, zona i tarifa, klizač za javno punjenje sa tri dugmeta cene]]

[[shot:kalkulator-rezultat | Blok rezultata: električni auto mesečno i na 100 km, benzin, razlika mesečno i godišnje, kWh kod kuće i na javnim punjačima]]

## Kako računa

- **Kod kuće:** (cena energije + 0,801 RSD za obnovljive izvore + 0,015 RSD za energetsku efikasnost) × akciza 7,5 % × PDV 20 %. Struja sa brojila = kilometri × potrošnja ÷ 100 × (1 + gubici).
- **Javni punjači:** kWh koje auto primi × cena po kWh.
- **Gorivo:** kilometri × litara na 100 km ÷ 100 × cena litra.

## Šta pretpostavlja

- Početne vrednosti: 1.250 km mesečno i 17 kWh na 100 km. Kod kuće: plava zona, noćna tarifa i 10 % gubitaka pri punjenju. Deo punjenja na javnim punjačima: 10 %. Benzin: 6,5 litara na 100 km.
- Brzi DC punjač: 60 RSD po kWh, prosek četiri računa iz aplikacije Charge&GO, avgust–septembar 2026 (43–79 RSD/kWh). AC punjač: 91 RSD po kWh, kad auto na punjaču Charge&GO od 22 kW prima 11 kW.
- Gubici se dodaju samo punjenju kod kuće: brojilo meri i struju koja ostane u punjaču i kablu.
- Sva struja za auto kod kuće računa se po ceni izabrane zone. Ispod rezultata piše koliko kWh mesečno punjenje dodaje računu; zelena zona važi do 350 kWh, plava do 1.200 kWh.
- „Povećanje snage, kW“, u delu „Gubici i snaga priključka“: svaki kW veće snage priključka dodaje 78,55 RSD mesečno.
- Cene goriva su najviše maloprodajne cene sa datumom ispod polja i menjaju se svakog petka. Za tačan rezultat upišite cenu sa pumpe.

## Šta nije uračunato

Cena auta i subvencija, osiguranje, održavanje, putarina (10 % popusta uz ENP), fiksne stavke računa za struju i kućni punjač. Porez na upotrebu vozila električni auto ne plaća.

<details markdown="1">
<summary>Detalji: cene struje kod kuće</summary>

Kalkulator koristi cene EPS-a za garantovano snabdevanje domaćinstava od 01.10.2025, sa naknadama, akcizom i PDV-om. Noćni kWh košta 4,15 RSD u zelenoj, 5,70 RSD u plavoj i 10,35 RSD u crvenoj zoni. Sati niže tarife zavise od regiona: [Tarife i zone](/podaci/tarife-eps/).

</details>

Cene javnog punjenja i zašto se razlikuju: [Odakle su cene](/pomoc/cene-javnog-punjenja/).
