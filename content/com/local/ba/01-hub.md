---
key: hub
slug:
template: hub
order: 1
priority: 0.9
title: Punjači za električne automobile u BiH — mapa, cijene, poticaji | BlokVolt
description: Mapa javnih punjača u Bosni i Hercegovini, cijene punjenja, koliko košta punjenje kod kuće po tarifama EPBiH, ERS i EP HZ HB, poticaji FBiH i punjači na koridoru Vc — s izvorima.
kicker: Nezavisni vodič · Bosna i Hercegovina
h1: Punjenje električnih automobila u Bosni i Hercegovini
lead: Gdje napuniti auto, koliko košta punjenje na javnim punjačima i kod kuće u oba entiteta, koji poticaji postoje i gdje se puni na putu — na jednom mjestu, s izvorom i datumom provjere.
card: Mapa punjača, cijene, kalkulator s tarifama EPBiH, ERS i EP HZ HB, poticaji FBiH i koridor Vc.
---
{{ w.stats([(num(C.fleet.series[-1][1]), pl(C.fleet.series[-1][1], 'električni putnički automobil', 'električna putnička automobila', 'električnih putničkih automobila') ~ ' krajem 2025. — 38 % više nego godinu prije (Eurostat)'),
            (num(M.n), pl(M.n, 'javni punjač', 'javna punjača', 'javnih punjača') ~ ' na našoj mapi, od toga ' ~ num(M.dc50) ~ ' s brzim DC punjenjem od 50 kW naviše'),
            ('0 %', 'carina na nova električna vozila do 31.12.2026.')]) }}

## Koliko košta 100 km

Električni automobil troši oko 17 kWh na 100 km. Uz cijene objavljene do 28.09.2026.:

| Gdje punite | Cijena kWh | 100 km |
|---|---|---|
| Kod kuće noću, EPBiH (plavi blok) | {{ money(C.power.tariffs[0].allin, 3) }} | oko {{ money(C.power.tariffs[0].allin * 17 * 1.1) }} |
| Kod kuće noću, Elektroprivreda RS (bijela zona) | {{ money(C.power.tariffs[3].allin, 3) }} | oko {{ money(C.power.tariffs[3].allin * 17 * 1.1) }} |
| Kod kuće, EPBiH jednotarifno | {{ money(C.power.tariffs[2].allin, 3) }} | oko {{ money(C.power.tariffs[2].allin * 17 * 1.1) }} |
| Javni DC punjač, MOON 150 kW (2024.) | 0,80 KM | 13,60 KM |
| Benzin BMB 95, 6,5 l po {{ money(C.fuel.petrol) }} | — | {{ money(6.5 * C.fuel.petrol) }} |

Kod kuće noću 100 km košta oko 2 KM — otprilike deset puta manje nego benzinom. Na javnim punjačima cijene su vrlo različite: od besplatnih u promotivnoj fazi do 0,90 KM po kWh. Svoj izračun napravite u [kalkulatoru]({{ PAGES.home.path }}).

## Šta ovdje nalazite

{{ w.tiles(['map', 'prices', 'home', 'subsidies', 'road', 'stats']) }}

## Ukratko, septembar 2026.

- **Poticaj FBiH.** Fond za zaštitu okoliša FBiH otvorio je 16.09.2026. poziv JP EV 2026 (do 12.000 KM po električnom vozilu), a 18.09. ga privremeno zatvorio jer su sredstva rezervisana. [Poticaji]({{ PAGES.subsidies.path }})
- **Carina.** Nova električna vozila do kraja 2026. uvoze se bez carine.
- **Koridor Vc.** Na A1 su brzi punjači EPBiH na odmorištu Lepenica (samo prema Sarajevu) i MOON kod Počitelja. [Na putu]({{ PAGES.road.path }})
- **Cijene.** Elektroprivreda BiH i MOON nemaju javne cjenovnike; na mnogim punjačima punjenje je još besplatno. [Cijene]({{ PAGES.prices.path }})

<p class="note disc">BlokVolt je nezavisni vodič. Vodi ga tim srpske firme Evolako, koja ugrađuje kućne punjače samo u Srbiji. U Bosni i Hercegovini ne prodajemo ništa i niko ne plaća za mjesto na ovim stranicama. <a href="{{ PAGES.method.path }}">Kako radimo</a></p>
