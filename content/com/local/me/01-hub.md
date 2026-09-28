---
key: hub
slug:
template: hub
order: 1
priority: 0.9
title: Punjači za električne automobile u Crnoj Gori — mapa, cijene, subvencije | BlokVolt
description: Mapa javnih punjača u Crnoj Gori, šta operateri objavljuju o cijenama, koliko košta punjenje kod kuće po tarifama EPCG, subvencije Eko-fonda i punjači na primorju i autoputu — s izvorima.
kicker: Nezavisni vodič · Crna Gora
h1: Punjenje električnih automobila u Crnoj Gori
lead: Gdje napuniti auto, šta se zna o cijenama javnog punjenja, koliko košta punjenje kod kuće, koje subvencije postoje i gdje se puni na primorju — na jednom mjestu, s izvorom i datumom provjere.
card: Mapa punjača, cijene, kalkulator s tarifama EPCG, subvencije Eko-fonda i primorje.
---
{{ w.stats([(num(C.fleet.series[-1][1]), pl(C.fleet.series[-1][1], 'električni putnički automobil', 'električna putnička automobila', 'električnih putničkih automobila') ~ ' krajem 2025. — 30 % više nego godinu prije (Eurostat)'),
            (num(C.points.n), pl(C.points.n, 'javno mjesto', 'javna mjesta', 'javnih mjesta') ~ ' za punjenje prema nacrtu nacionalnog okvira (jun 2026.); nijedno iznad 150 kW'),
            (num(M.n), pl(M.n, 'punjač', 'punjača', 'punjača') ~ ' na našoj mapi, od toga ' ~ num(M.dc50) ~ ' s DC punjenjem od 50 kW naviše')]) }}

## Ukratko

- **Mreža je mala.** Javnih mjesta za punjenje u Crnoj Gori je {{ C.points.n }} (nacrt nacionalnog okvira, jun 2026.), uglavnom manje snage i u gradovima. Najveća mreža brzih punjača su EKO stanice (Jugopetrol) sa 7 punjača od 50 kW. [Mapa]({{ PAGES.map.path }})
- **Cijene nisu objavljene.** Nijedan operater koji smo provjerili ne objavljuje cjenovnik javnog punjenja. [Cijene]({{ PAGES.prices.path }})
- **Kod kuće je jeftino.** Noću kWh sa mrežnim naknadama i PDV-om košta oko 0,07 € (indikativno), pa 100 km košta oko 1,30 €, a benzinom oko 11 €. [Kalkulator]({{ PAGES.home.path }})
- **Subvencije.** Eko-fond je u dva konkursa, u saradnji sa Slovenijom, subvencionisao 53 električna vozila; otvorenog konkursa trenutno nema. [Subvencije]({{ PAGES.subsidies.path }})
- **Autoput.** Na dionici Smokovac – Mateševo na odmorištu Pelev Brijeg izgrađena je stanica 4 × 50 kW, a na Gornjim Mrkama u ugradnji je 4 × 60 kW. [Na putu]({{ PAGES.road.path }})

## Šta ovdje nalazite

{{ w.tiles(['map', 'prices', 'home', 'subsidies', 'road', 'stats']) }}

<p class="note disc">BlokVolt je nezavisni vodič. Vodi ga tim srpske firme Evolako, koja ugrađuje kućne punjače samo u Srbiji. U Crnoj Gori ne prodajemo ništa i niko ne plaća za mjesto na ovim stranicama. <a href="{{ PAGES.method.path }}">Kako radimo</a></p>
