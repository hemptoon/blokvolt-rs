---
key: hub
slug:
template: hub
order: 1
priority: 0.9
title: Polnilnice za električne avtomobile v Sloveniji | BlokVolt
description: Zemljevid javnih polnilnic v Sloveniji, cene polnjenja (Gremo na elektriko, Petrol, IONITY, Tesla), strošek polnjenja doma, subvencije Borzen in hitre polnilnice ob avtocestah.
kicker: Vodnik · Slovenija
h1: Polnjenje električnih avtomobilov v Sloveniji
lead: Kje napolniti avto, koliko stane polnjenje na javnih polnilnicah in doma, katere subvencije veljajo in kje so hitre polnilnice na poti — na enem mestu, z virom in datumom preverjanja.
card: Zemljevid polnilnic, ceniki mrež, kalkulator za polnjenje doma, subvencije Borzen in hitre polnilnice ob avtocestah.
---
{{ w.stats([(num(C.acea.y2026_9m), pl(C.acea.y2026_9m, 'nov baterijski električni avto', 'nova baterijska električna avtomobila', 'novi baterijski električni avtomobili', 'novih baterijskih električnih avtomobilov') ~ ' od januarja do septembra 2026 — ' ~ C.acea.share ~ ' vseh novih (ACEA)'),
            (num(M.n), pl(M.n, 'javna polnilnica', 'javni polnilnici', 'javne polnilnice', 'javnih polnilnic') ~ ' na zemljevidu, od tega ' ~ num(M.dc50) ~ ' s hitrim DC-polnjenjem od 50 kW naprej'),
            ('do 7.800 €', 'subvencija Borzen za nov električni avto v letu 2026 — zaprošeni zneski že presegajo sredstva')]) }}

## Koliko stane 100 km

Električni avto porabi okoli 17 kWh na 100 km. Po cenah, objavljenih do {{ C.checked }}:

| Kje polnite | Cena kWh | 100 km |
|---|---|---|
| Doma, groba ocena z omrežnino in dajatvami | {{ money(C.power.tariffs[0].allin, 2) }} | okoli {{ money(C.power.tariffs[0].allin * 17 * 1.1) }} |
| Gremo na elektriko, AC do 22 kW | 0,35 € | 5,95 € + pristojbina 0,50 € |
| Gremo na elektriko, DC | 0,45 € | 7,65 € + pristojbina 1,00 € |
| IONITY brez naročnine | 0,73 € | 12,41 € |
| Bencin 95, 6,5 l po {{ money(C.fuel.petrol, 3) }} | — | {{ money(6.5 * C.fuel.petrol) }} |

Doma stane 100 km približno trikrat manj kot z bencinom, vendar ima ocena cene elektrike doma nizko zanesljivost: račun je odvisen od dobavitelja, tarife in dogovorjene moči. Svoj izračun naredite v [kalkulatorju]({{ PAGES.home.path }}), cene energije pri dobaviteljih pa so na strani [Cena elektrike]({{ PAGES.electricity.path }}).

## Kaj najdete tukaj

{{ w.tiles(['map', 'prices', 'home', 'electricity', 'subsidies', 'road', 'stats']) }}

**[Polnilnice po krajih](/si/kraji/)**: seznam krajev s številom polnilnic in povezavo na zemljevid.

## Na kratko, oktober 2026

- **Subvencija za avto.** Borzenov poziv JP SUB-EV26 (do 7.800 €) je še na seznamu odprtih pozivov, vendar zaprošeni zneski že presegajo sredstva; ministrstvo jih ne bo povečalo. [Subvencije]({{ PAGES.subsidies.path }})
- **Subvencija za domačo polnilnico.** 55 % stroškov, do 1.000 € na polnilno mesto; tudi tu so vloge že presegle sredstva za leto 2026.
- **Prodaja.** Od januarja do septembra 2026 je bil skoraj vsak peti nov avto baterijski električni. [Statistika]({{ PAGES.stats.path }})
- **Cene.** Gremo na elektriko in IONITY objavljata cenik; Petrol, Tesla in MOONcharge cene kWh na preverjenih straneh ne prikazujejo. [Cene]({{ PAGES.prices.path }})

<p class="note disc">Vse mreže so prikazane po enakih pravilih, mesta na teh straneh nihče ne plačuje. Kdo stoji za BlokVoltom in od kod so podatki, piše v <a href="{{ PAGES.method.path }}">metodologiji</a>.</p>
