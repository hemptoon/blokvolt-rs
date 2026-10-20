---
title: Zašto auto puni sporo na brzom punjaču: hladnoća, deljenje, napon
h1: Zašto auto puni sporo na brzom punjaču
description: Hladna baterija, drugi auto na istom stubu, napon auta i softver usporavaju DC punjenje. Šta proveriti pre punjenja i tokom njega.
lead: Na stubu piše najveća snaga punjača, a koliko ćete dobiti određuju baterija, auto i drugi priključak.
kicker: Vodič
updated: 20.10.2026
next_check: 19.11.2026
path: /javno-punjenje/zasto-auto-puni-sporo-na-brzom-punjacu/
published: 2026-10-20
modified: 2026-10-20
priority: 0.7
image: dc-punjenje-zimi-inje
image_alt: Električni auto sa injem na krovu puni na DC punjaču pored autoputa zimi
sources: ADAC, 07.08.2025 — saveti za brzo punjenje: temperatura baterije 20–40 °C, leto, deljenje snage, provera ekrana :: https://www.adac.de/rund-ums-fahrzeug/elektromobilitaet/laden/elektroauto-tipps-zum-schnellladen/ | ADAC — deljenje snage na pola, predgrevanje pre dolaska, temperatura baterije se ne prikazuje :: https://www.presseportal.de/pm/7849/6092045 | ADAC, 18.03.2026 — krive brzog punjenja, test na −7 °C :: https://www.adac.de/rund-ums-fahrzeug/elektromobilitaet/laden/schnellladen-langstrecke-ladekurven-2026/ | ADAC — 400 ili 800 V, CCS 500 A trajno i 600 A kratko :: https://www.adac.de/rund-ums-fahrzeug/elektromobilitaet/elektroauto/elektroauto-400-oder-800-volt/ | Edison, 17.11.2025 — auto od 800 V na punjaču od 400 V :: https://edison.media/verkehr/mit-800-volt-sind-wir-nahe-an-dem-was-moeglich-ist/25263208/ | Fastned — brzinu određuje auto, temperatura, vožnja i baterija :: https://support.fastnedcharging.com/kb/guide/nl/alles-over-je-laadsnelheid-hINR9JWXDH/Steps/4458462 | Energetski portal, 02.01.2023 — Charge&GO Unity 180, 2 × 90 kW :: https://energetskiportal.rs/chargego-siri-mrezu-elektropunjaca/ | Energetski portal, 19.04.2023 — Charge&GO OMV Kruševac, 2 × 65 kW :: https://energetskiportal.rs/brzo-i-lako-do-najblizeg-punjaca-u-mrezi/ | Hyundai — IONIQ 5, punjenje na 50 i 350 kW, 400 i 800 V :: https://www.hyundai.com/eu/en/models/ioniq5/performance.html | electrive, 21.10.2022 — Kia EV6, predgrevanje ažuriranjem :: https://www.electrive.net/2022/10/21/kia-bringt-batterie-vorkonditionierung-in-aeltere-ev6/
---
<div class="sum" markdown="1">
- Na stubu piše **najveća** moguća snaga, a ne snaga koju ćete sigurno dobiti. Brzinu određuje auto.
- Baterija puni najbrže na oko **20–40 °C**. Kad je hladnija ili toplija, prima manju snagu.
- Na **−7 °C**, bez predgrevanja, brzo punjenje je u ADAC testu trajalo **40–70 %** duže.
- Kad dva auta pune na istom stubu, snaga se obično deli **na pola**, na primer **2 × 90 kW** umesto 180 kW.
- Auto od **400 V** preko CCS kabla prima najviše oko **200–240 kW**, ma koliko jak bio punjač.
</div>

## Hladna ili vruća baterija

Najbrže punjenje moguće je samo u određenom opsegu temperature baterije, obično od 20 do 40 °C, a kod nekih modela i više. Van tog opsega auto sam smanjuje snagu.

Zimi, sa baterijom ohlađenom preko noći, ne računajte ni približno na najveću snagu. U ADAC testu VW ID.3 je na −7 °C počeo punjenje sa manje od 50 kW. Na 23 °C povremeno prima 125 kW.

Rešenje je predgrevanje baterije. Uključuje se preko navigacije do punjača ili ručno, nekoliko minuta pre dolaska.

<details markdown="1">
<summary>Detalji: zimski test i leto</summary>

- **ADAC, −7 °C, baterija nije predgrejana:** Tesla Model Y je oko 18 minuta grejala bateriju pre nego što je počela da puni. Na punjaču je stajala 56 minuta umesto 33, odnosno 70 % duže. VW ID.3 je punio 50 % duže, a Renault Zoe i VW e-Up po 40 % duže.
- **Vožnja i temperatura:** po Fastnedu, vožnja ne greje bateriju kao što greje motor sa unutrašnjim sagorevanjem. Baterija je obično blizu spoljne temperature.
- **Temperatura se ne vidi:** auto obično ne prikazuje temperaturu baterije.
- **Leto:** na vrućini se toplota nastala pri brzom punjenju ne odvodi dovoljno brzo, pa sistem upravljanja baterijom smanjuje snagu.

</details>

## Dva auta na jednom stubu

Kad su na stub priključena dva auta, snaga se deli između njih. Najčešće se prepolovi, ali sve više stanica snagu raspoređuje prema potrebi.

[[fig:dva-auta-isti-dc-stub|Dva električna auta pune na istom DC stubu, a susedni stub je slobodan]]

Primeri Charge&GO punjača u Srbiji, oba sa dva CCS priključka:

| Punjač | Jedan auto | Dva auta |
|---|---|---|
| OMV Martinci 1, autoput (Kostad Siemens Unity 180) | 180 kW | 2 × 90 kW |
| OMV Kruševac (Kostad Siemens) | 130 kW | 2 × 65 kW |

Ako na stubu već puni drugi auto, birajte potpuno slobodan stub kad god možete.

<details markdown="1">
<summary>Detalji: kada deljenje manje smeta</summary>

- Ako vaš auto prima najviše 50 kW, polovina od 180 kW (90 kW) i dalje je više od toga, pa deljenje ne usporava punjenje.
- Snage punjača i to da li su slobodni vide se u aplikaciji mreže i na [mapi punjača](/mapa/).

</details>

## Napon i softver

Snaga je napon pomnožen strujom. CCS utikač je predviđen za 500 A trajno i 600 A kratko. Zato auto od 400 V ima prirodnu granicu od oko 200 do 240 kW.

Auto od 800 V može da puni na stubu od 400 V, ali sa upola manjom snagom, osim ako nema dodatno rešenje.

Softver auta određuje kada i kako se baterija greje. Proizvođači ga menjaju ažuriranjem.

<details markdown="1">
<summary>Detalji: primeri za napon i softver</summary>

- **Napon raste tokom punjenja:** na 500 A, pri naponu baterije od 350 V auto prima 175 kW, a pri 400 V — 200 kW.
- **Auto od 800 V:** Hyundai navodi da IONIQ 5 puni i na punjačima od 400 V i na onima od 800 V, bez adaptera. Verzija od 84 kWh od 10 do 80 % puni za 18 minuta na 350 kW, a za 1 h 16 min na 50 kW.
- **Kia EV6, model 2022:** predgrevanje je dodato ažuriranjem softvera kod ovlašćenog servisa. Radi samo kad je baterija hladnija od 21 °C i napunjena bar 24 %. Uključuje se kad je DC punjač zadat u navigaciji, ručno ne može. U idealnim uslovima EV6 od 10 do 80 % puni za 18 minuta, a na 5 °C, bez predgrevanja, za oko 35 minuta.

</details>

## Šta proveriti

- **Koliko prima vaš auto.** Najveća DC snaga piše u specifikaciji auta.
- **Napunjenost baterije.** Što je baterija praznija, snaga je veća. Najbolje se puni od 10 do 80 %. Više: [kako platiti manje na javnom punjaču](/javno-punjenje/kako-jeftinije-puniti/).
- **Predgrevanje zimi**, preko navigacije do punjača.
- **Slobodan stub**, na kome ne puni drugi auto.
- **Ekran posle početka.** Pre nego što odete od auta, proverite da punjenje teče i da snaga odgovara očekivanoj.
- **Softver auta.** Proverite da li su instalirana najnovija ažuriranja.

Ako punjenje uopšte ne počne: [punjač ne radi](/pomoc/punjac-ne-radi/).

<details markdown="1">
<summary>Detalji: zašto 350 kW na stubu ne znači 350 kW</summary>

- Na stubu i u aplikaciji uvek piše samo najveća moguća snaga.
- Najveću snagu iz podataka proizvođača auta obično dobijate samo kad je baterija skoro prazna i kad je napolju toplo. Fastned najbolje rezultate beleži kad je spolja toplije od 20 °C.
- Punjač jači od vašeg auta možete bezbedno koristiti, jer snagu određuje auto.
- Ako auto prima malu snagu, a u blizini je slabiji slobodan stub, ADAC savetuje da brzi stub ostavite autima koja mogu da iskoriste njegovu snagu.

</details>
