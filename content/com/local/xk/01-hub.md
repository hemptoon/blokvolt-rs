---
key: hub
slug:
template: hub
order: 1
priority: 0.9
title: Karikimi i veturave elektrike në Kosovë — harta, çmimet, tarifat | BlokVolt
description: Harta e karikuesve publikë në Kosovë, çmimet e karikimit, sa kushton karikimi në shtëpi me tarifat e ZRRE-së, taksat dhe autostradat — me burime.
kicker: Udhëzues · Kosova
h1: Karikimi i veturave elektrike në Kosovë
lead: Ku ta mbushni veturën elektrike, sa kushton karikimi në karikuesit publikë dhe në shtëpi, çfarë taksash paguhen dhe si udhëtohet — në një vend, me burim dhe datë kontrolli.
card: Harta e karikuesve, çmimet e ECHARGE, kalkulatori me tarifat e ZRRE-së, taksat dhe autostradat R6 e R7.
---
{% set TR = C.power.tariffs %}{% set EC = C.networks[0].prices %}
{{ w.stats([(num(C.fleet.series[-1][1]), pl(C.fleet.series[-1][1], 'veturë elektrike', 'vetura elektrike', 'vetura elektrike') ~ ' në fund të vitit 2025 — ' ~ num(C.fleet.growth_2025, 1) ~ ' % më shumë se një vit më parë (Eurostat, rritja e llogaritur)'),
            (num(C.imports.n), pl(C.imports.n, 'veturë elektrike e importuar', 'vetura elektrike të importuara', 'vetura elektrike të importuara') ~ ' në janar–gusht 2026, ' ~ num(C.imports.china) ~ ' prej tyre nga Kina (Dogana e Kosovës)'),
            (num(M.n), pl(M.n, 'karikues publik', 'karikues publikë', 'karikues publikë') ~ ' në hartë, prej tyre ' ~ num(M.dc50) ~ ' me karikim të shpejtë DC nga 50 kW e lart')]) }}

## Sa kushtojnë 100 km

Një veturë elektrike konsumon rreth 17 kWh në 100 km. Me çmimet e publikuara deri më {{ C.checked }}:

| Ku karikoni | Çmimi i kWh | 100 km |
|---|---|---|
| Në shtëpi natën, deri në 800 kWh në muaj | {{ money(TR[0].allin, 3) }} | rreth {{ money(TR[0].allin * 17 * 1.1) }} |
| Në shtëpi ditën, deri në 800 kWh në muaj | {{ money(TR[1].allin, 3) }} | rreth {{ money(TR[1].allin * 17 * 1.1) }} |
| Në shtëpi natën, mbi 800 kWh në muaj | {{ money(TR[2].allin, 3) }} | rreth {{ money(TR[2].allin * 17 * 1.1) }} |
| ECHARGE AC, natën dhe ditën | {{ num(EC[1].v, 2) }}–{{ money(EC[0].v) }} | {{ num(EC[1].v * 17, 2) }}–{{ money(EC[0].v * 17) }} |
| ECHARGE DC | {{ num(EC[2].v, 2) }}–{{ money(EC[3].v) }} | {{ num(EC[2].v * 17, 2) }}–{{ money(EC[3].v * 17) }} |
| Benzinë, 6,5 l në 100 km, {{ money(C.fuel.petrol) }} për litër | — | {{ money(6.5 * C.fuel.petrol) }} |

Për karikimin në shtëpi janë llogaritur TVSH 8 % dhe 10 % humbje; tarifa fikse mujore nuk është përfshirë. ECHARGE nuk shkruan nëse çmimet e saj përfshijnë TVSH-në. Çmimi i benzinës është orientues, nga Petrol Company më {{ C.fuel.date }}. Llogaritjen për veturën tuaj mund ta bëni te [kalkulatori]({{ PAGES.home.path }}).

## Çfarë gjeni këtu

{{ w.tiles(['map', 'prices', 'home', 'subsidies', 'road', 'stats']) }}

## Gjendja në shtator 2026

- **Importi rritet.** Sipas Doganës së Kosovës, në janar–gusht 2026 u importuan {{ num(C.imports.n) }} vetura elektrike, {{ num(C.imports.china) }} prej tyre nga Kina. [Statistika]({{ PAGES.stats.path }})
- **Pa lehtësi tatimore.** Veturat elektrike paguajnë doganë 10 % dhe TVSH 18 %, si veturat e tjera. Oda Ekonomike e Kosovës ka kërkuar heqjen e doganës dhe uljen e TVSH-së në 8 %. [Lehtësitë]({{ PAGES.subsidies.path }})
- **Rryma në shtëpi.** Tarifat e ZRRE-së nga {{ C.power.valid_from }} vlejnë edhe në vitin 2026. Natën, me konsum mujor deri në 800 kWh, kilovat-ora kushton {{ num(TR[0].price, 2) }} centë pa TVSH. [Karikimi në shtëpi]({{ PAGES.home.path }})
- **Çmimet publike.** Vetëm ECHARGE publikon çmime. HIB Petrol, RapidCharge dhe Shell nuk publikojnë çmim për kWh. [Çmimet]({{ PAGES.prices.path }})
- **Autostradat.** R6 dhe R7 janë pa pagesë sipas burimit më të fundit (2021). Asnjë burim nuk tregon karikues në vetë autostradat. [Udhëtimi]({{ PAGES.road.path }})

<p class="note disc">Të gjitha rrjetet paraqiten sipas të njëjtave rregulla dhe askush nuk paguan për vendin në këto faqe. Kush qëndron pas BlokVolt dhe nga vijnë të dhënat, shkruhet te <a href="{{ PAGES.method.path }}">metodologjia</a>.</p>
