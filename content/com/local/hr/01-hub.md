---
key: hub
slug:
template: hub
order: 1
priority: 0.9
title: Punionice i punjenje električnih automobila u Hrvatskoj — karta, cijene, poticaji | BlokVolt
description: Karta javnih punionica u Hrvatskoj, cijene svih mreža po kWh, koliko košta punjenje kod kuće, poticaji 2026., autoceste, trajekti i otoci — s izvorima i datumom provjere.
kicker: Neovisni vodič · Hrvatska
h1: Punjenje električnih automobila u Hrvatskoj
lead: Gdje napuniti auto, koliko košta kilovatsat na svakoj mreži i kod kuće, koji poticaji vrijede i što kaže zakon za zgrade — na jednom mjestu, s izvorom i datumom provjere uz svaki podatak.
card: Karta punionica, cijene svih mreža, kalkulator s HEP-ovim tarifama, poticaji i savjeti za put na more.
---
{{ w.stats([(num(C.fleet.series[-1][1]), pl(C.fleet.series[-1][1], 'električni osobni automobil', 'električna osobna automobila', 'električnih osobnih automobila') ~ ' krajem 2025. — 26 % više nego godinu prije (Eurostat)'),
            (num(C.new_bev.jan_aug_2026), pl(C.new_bev.jan_aug_2026, 'novi električni automobil', 'nova električna automobila', 'novih električnih automobila') ~ ' od siječnja do kolovoza 2026. — 4,2 % tržišta i 4,3 puta više nego u istom razdoblju lani (ACEA)'),
            (num(M.n), pl(M.n, 'javna punionica', 'javne punionice', 'javnih punionica') ~ ' na našoj karti, od toga ' ~ num(M.dc50) ~ ' s brzim DC punjenjem od 50 kW naviše')]) }}

## Koliko košta 100 km

Električni automobil troši oko 17 kWh na 100 km. Uz cijene objavljene 28. 9. 2026. to izgleda ovako:

| Gdje punite | Cijena kWh | 100 km |
|---|---|---|
| Kod kuće noću, HEP tarifni model Bijeli | {{ money(C.power.tariffs[0].allin, 3) }} | oko {{ money(C.power.tariffs[0].allin * 17 * 1.1) }} |
| Kod kuće, jedinstvena tarifa (Plavi) | {{ money(C.power.tariffs[1].allin, 3) }} | oko {{ money(C.power.tariffs[1].allin * 17 * 1.1) }} |
| Javna AC punionica (ELEN, izvan autocesta) | 0,35 € | 5,95 € |
| Brza DC punionica do 50 kW (Petrol, registrirani) | 0,47 € | 7,99 € |
| Ultrabrza punionica (IONITY bez pretplate) | 0,74 € | 12,58 € |
| Benzin, 6,5 l na 100 km po {{ money(C.fuel.petrol) }} | — | {{ money(6.5 * C.fuel.petrol) }} |

Kod kuće noću 100 km stoji otprilike šest puta manje nego benzinom, a na ultrabrzoj punionici bez pretplate nešto više nego benzinom. Kod kuće smo uračunali 10 % gubitaka pri punjenju. Svoj izračun napravite u [kalkulatoru]({{ PAGES.home.path }}).

## Što ovdje nalazite

{{ w.tiles(['map', 'prices', 'apps', 'home', 'subsidies', 'road', 'buildings', 'stats']) }}

## Ukratko, rujan 2026.

- **Poticaji za građane.** FZOEU je najavio poziv od 20 milijuna eura „na jesen”; prvi put sufinancira i kupnju i ugradnju kućnih punionica, a plug-in hibride više ne. Na dan 28. 9. 2026. poziv još nije objavljen. Poziv za tvrtke EnU-4/26 je zatvoren. [Svi poticaji]({{ PAGES.subsidies.path }})
- **Zgrade.** Od 1. 1. 2025. o postavljanju mjesta za punjenje u zgradi odlučuje natpolovična većina suvlasnika — ne jednoglasno i ne 80 %. [Što kaže zakon]({{ PAGES.buildings.path }})
- **Autoceste.** Na A1 punionicu ima 15 odmorišta, ali južno od Raščana gornjih nijedno. Na A5, A10 i A11 nema nijedne. [Put na more]({{ PAGES.road.path }})
- **Trajekti.** Električni automobil smije na Jadrolinijin trajekt, ali pri kupnji karte morate navesti da je vozilo električno.
- **Struja kod kuće.** Od 1. 10. 2026. do 31. 3. 2027. cijene energije za kućanstva određuje nova uredba; iznad 3.000 kWh u šest mjeseci energija je 35 % skuplja.

<p class="note disc">BlokVolt je neovisni vodič. Vodi ga tim srpske tvrtke Evolako, koja ugrađuje kućne punionice samo u Srbiji. U Hrvatskoj ne prodajemo ništa i nitko ne plaća za mjesto na ovim stranicama: sve mreže prikazujemo po istim pravilima. <a href="{{ PAGES.method.path }}">Kako radimo</a></p>
