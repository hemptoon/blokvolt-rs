---
key: map
slug: harta/
template: map
order: 2
nav: Harta
icon: map
priority: 0.9
title: Harta e karikuesve për makina elektrike në Shqipëri | BlokVolt
description: Karikuesit publikë në Shqipëri në një hartë, me priza, fuqi dhe rrjet, nga OpenStreetMap dhe Open Charge Map, me filtra për karikimin e shpejtë.
h1: Harta e karikuesve
lead: Karikuesit publikë në Shqipëri nga OpenStreetMap dhe Open Charge Map, me priza dhe fuqi.
card: Karikuesit publikë nga bazat e hapura në një hartë, me filtra për karikuesit e shpejtë.
dataset: Karikues publikë për makina elektrike në Shqipëri
search_label: Kërkoni karikues
search_ph: Qyteti, adresa ose rrjeti
chip_all: Të gjithë
chip_fav: Të preferuarit
chip_fast: Të shpejtë (DC ≥ 50 kW)
near_me: Pranë meje
noscript: Harta kërkon JavaScript. Çmimet janë te faqja Çmimet.
attr_map: Harta
attr_data: Të dhënat
related: prices, road, home
---
## Nga vijnë të dhënat

Karikuesit vijnë nga dy baza të hapura të dhënash: **OpenStreetMap** (licenca ODbL) dhe **Open Charge Map** (CC BY 4.0). Kopja është e datës {{ M.retrieved }}: OpenStreetMap në gjendjen e {{ M.osm_base }} dhe Open Charge Map sipas eksportit të {{ M.ocm_export }}. I njëjti vend nga të dyja bazat shfaqet një herë. Harta tregon {{ num(M.n) }} {{ pl(M.n, 'karikues', 'karikues', 'karikues') }}, nga të cilët {{ num(M.dc50) }} me karikim DC nga 50 kW e lart.

**Karikuesit nuk janë kontrolluar një nga një.** Bazat e hapura i plotësojnë shoferë dhe vullnetarë, prandaj ndonjë karikues mund të mos punojë më ose të jetë vetëm për klientët e hotelit. Regjistër zyrtar i karikuesve publikë nuk ka; OSHEE numëronte më shumë se {{ C.oshee_2025.points }} pika karikimi në funksion ({{ C.oshee_2025.date }}). Para udhëtimit kontrolloni te operatori.

Në bazat e hapura karikuesit e VEGA CHARGING dhe PlugoAL nuk shënohen me emrin e rrjetit; vendndodhjet e tyre sipas operatorëve janë te faqja [Udhëtimi]({{ PAGES.road.path }}). Asnjë rrjet nuk publikon çmim për kWh; në kartën e karikuesit shfaqet shënimi i rrjetit, kur ka. Gjithçka për çmimet: [Çmimet]({{ PAGES.prices.path }}).

## Si përdoret harta

- **Filtrat** mbi listë: të gjithë, karikuesit e shpejtë DC nga 50 kW, vetëm AC, CHAdeMO dhe rrjetet. Kërkimi gjen karikues sipas emrit, adresës, qytetit dhe rrjetit.
- **Pranë meje** e kërkon vendndodhjen tuaj vetëm kur shtypni butonin; vendndodhja mbetet në shfletuesin tuaj.
- **Të preferuarit** (ylli në kartën e karikuesit) ruhen vetëm në këtë shfletues.
- **Navigimi** hap Google Maps, Apple Maps ose Waze.

Nëse mungon një karikues ose një e dhënë është e gabuar, shkruani te [hello@blokvolt.com](mailto:hello@blokvolt.com?subject=Korrigjim%20harte%20AL) ose bëjeni vetë ndryshimin në [OpenStreetMap](https://www.openstreetmap.org): ai shfaqet në hartë pas përditësimit të ardhshëm mujor.

Të dhëna të hapura: [stanice.json](/assets/region/al/stanice.json) (ODbL 1.0, © OpenStreetMap dhe Open Charge Map).
