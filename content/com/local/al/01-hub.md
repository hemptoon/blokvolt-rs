---
key: hub
slug:
template: hub
order: 1
priority: 0.9
title: Karikimi i makinave elektrike në Shqipëri — harta, çmimet, tarifat | BlokVolt
description: Harta e karikuesve publikë në Shqipëri, çfarë dihet për çmimet, kostoja e karikimit në shtëpi me tarifat e ERE-së, lehtësitë tatimore dhe udhëtimi.
kicker: Udhëzues · Shqipëria
h1: Karikimi i makinave elektrike në Shqipëri
lead: Ku të karikoni makinën, çfarë dihet për çmimet e karikimit publik, sa kushton karikimi në shtëpi, cilat lehtësi ka makina elektrike dhe ku ka karikues gjatë udhëtimit — në një vend, me burimin dhe datën e kontrollit.
card: Harta, çmimet, kalkulatori me tarifat e ERE-së, lehtësitë tatimore dhe udhëtimi.
---
{{ w.stats([(num(C.fleet.series[-1][1]), pl(C.fleet.series[-1][1], 'makinë elektrike', 'makina elektrike', 'makina elektrike') ~ ' në fund të vitit 2025, ' ~ C.fleet.growth_2025 ~ ' % më shumë se një vit më parë (Eurostat)'),
            (num(M.n), pl(M.n, 'karikues publik', 'karikues publikë', 'karikues publikë') ~ ' në hartë, nga të cilët ' ~ num(M.dc50) ~ ' me karikim DC nga 50 kW e lart'),
            (money(C.power.tariffs[0].allin, 1), 'për kWh në shtëpi me TVSH, kur familja konsumon deri në 700 kWh në muaj (ERE)')]) }}

## Sa kushton 100 km

Makina elektrike konsumon rreth 17 kWh për 100 km. Me çmimet e publikuara deri më 28.09.2026:

| Ku karikoni | Çmimi për kWh | 100 km |
|---|---|---|
| Në shtëpi, deri në 700 kWh në muaj | {{ money(C.power.tariffs[0].allin, 1) }} | rreth {{ money(C.power.tariffs[0].allin * 17 * 1.1, 0) }} |
| Në shtëpi, mbi 700 kWh në muaj | {{ money(C.power.tariffs[1].allin, 1) }} | rreth {{ money(C.power.tariffs[1].allin * 17 * 1.1, 0) }} |
| Në shtëpi, kur makina e çon konsumin mbi 700 kWh (shembull i llogaritur) | {{ money(C.power.tariffs[2].allin, 1) }} | rreth {{ money(C.power.tariffs[2].allin * 17 * 1.1, 0) }} |
| Karikues publik, vlerësimi i OSHEE-së | {{ num(C.market.lo) }}–{{ money(C.market.hi, 0) }} | {{ num(C.market.lo * 17) }}–{{ money(C.market.hi * 17, 0) }} |
| Benzinë, 6,5 l me {{ money(C.fuel.petrol, 0) }} litri | — | rreth {{ money(6.5 * C.fuel.petrol, 0) }} |
| Naftë, 5,5 l me {{ money(C.fuel.diesel, 0) }} litri | — | rreth {{ money(5.5 * C.fuel.diesel, 0) }} |

Për karikimin në shtëpi janë llogaritur edhe 10 % humbje. Në shtëpi karikimi kushton pak, por ka rëndësi pragu i 700 kWh në muaj: kur makina e çon konsumin e familjes mbi të, i gjithë konsumi i muajit faturohet me {{ money(C.power.tariffs[1].base, 1) }} për kWh pa TVSH. Për llogaritjen tuaj përdorni [kalkulatorin]({{ PAGES.home.path }}).

## Çfarë gjeni këtu

{{ w.tiles(['map', 'prices', 'home', 'subsidies', 'road', 'stats']) }}

## Përmbledhje, shtator 2026

- **Flota.** Në vitin 2025 u regjistruan {{ num(C.new_reg.series[-1][1]) }} makina elektrike të reja dhe flota pothuajse u dyfishua (Eurostat). [Statistika]({{ PAGES.stats.path }})
- **Çmimet.** Asnjë rrjet nuk publikon çmim për kWh. OSHEE vlerëson se në stacionet e karikimit energjia shitet {{ num(C.market.lo) }}–{{ money(C.market.hi, 0) }} për kWh. PlugoAL e tregon çmimin në aplikacion dhe faturon 500 lekë kur makina mbetet e lidhur më shumë se 20 minuta pas karikimit. [Çmimet]({{ PAGES.prices.path }})
- **Në shtëpi.** Deri në 700 kWh në muaj kilovat-ora kushton {{ money(C.power.tariffs[0].base, 1) }} pa TVSH, {{ money(C.power.tariffs[0].allin, 1) }} me TVSH. Mbi 700 kWh, i gjithë konsumi i muajit faturohet me {{ money(C.power.tariffs[1].base, 1) }} pa TVSH. [Kalkulatori]({{ PAGES.home.path }})
- **OSHEE Charge.** OSHEE njoftoi në nëntor 2025 një rrjet kombëtar karikimi që do të ngrihet brenda vitit 2026. Më 28.09.2026 nuk u gjet asnjë stacion në funksion.
- **Taksat.** Sipas burimit më të ri, makinat elektrike të reja nuk paguajnë TVSH, por burimet nuk përputhen plotësisht. Mjetet elektrike përjashtohen nga taksa vjetore. [Lehtësitë]({{ PAGES.subsidies.path }})
- **Rruga e Kombit.** Tarifa zyrtare për autoveturë është {{ C.toll.eur }} € me TVSH; për pagesën në lekë burimet japin {{ money(C.toll.lek, 0) }}. Në vetë rrugën A1 karikues i shpejtë nuk u konfirmua. [Udhëtimi]({{ PAGES.road.path }})

<p class="note disc">Të gjitha rrjetet paraqiten me të njëjtat rregulla dhe askush nuk paguan për t’u shfaqur në këto faqe. Kush qëndron pas BlokVolt dhe nga vijnë të dhënat, shpjegohet te <a href="{{ PAGES.method.path }}">metodologjia</a>.</p>
