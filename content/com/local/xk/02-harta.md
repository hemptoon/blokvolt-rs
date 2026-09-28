---
key: map
slug: harta/
template: map
order: 2
nav: Harta
icon: map
priority: 0.9
title: Harta e karikuesve për vetura elektrike në Kosovë | BlokVolt
description: Karikuesit publikë në Kosovë në një hartë — ECHARGE, HIB Petrol, RapidCharge, Shell e të tjerë — me lidhësit dhe fuqinë, nga OpenStreetMap dhe Open Charge Map.
h1: Harta e karikuesve
lead: Karikuesit publikë në Kosovë nga OpenStreetMap dhe Open Charge Map, me lidhësit dhe fuqinë.
card: Karikuesit publikë nga bazat e hapura në një hartë, me filtra për karikuesit e shpejtë.
dataset: Karikuesit publikë për vetura elektrike në Kosovë
search_label: Kërkoni karikues
search_ph: Qyteti, adresa ose rrjeti
chip_all: Të gjithë
chip_fav: Të preferuarit
chip_fast: Të shpejtë (DC ≥ 50 kW)
near_me: Pranë meje
noscript: Harta ka nevojë për JavaScript. Çmimet janë te faqja Çmimet.
attr_map: Harta
attr_data: Të dhënat
related: prices, road, home
---
## Nga vijnë të dhënat

Karikuesit janë nga dy baza të hapura: **OpenStreetMap** (licenca ODbL) dhe **Open Charge Map** (CC BY 4.0). Të dhënat u morën më {{ M.retrieved }}: OpenStreetMap në gjendjen e {{ M.osm_base }}, Open Charge Map sipas eksportit të {{ M.ocm_export }}. I njëjti vend nga të dyja bazat shfaqet një herë. Harta tregon {{ num(M.n) }} karikues, prej tyre {{ num(M.dc50) }} me karikim DC nga 50 kW e lart.

**Karikuesit nuk janë kontrolluar një nga një.** Bazat e hapura i plotësojnë shoferët dhe vullnetarët, prandaj ndonjë karikues mund të mos punojë më ose të jetë vetëm për mysafirët e një hoteli. Numër zyrtar i karikuesve publikë në Kosovë nuk publikohet. ECHARGE shkruan në faqen e vet për „24+ stacione” në Kosovë dhe Shqipëri, RapidCharge tregon dy stacione në Prishtinë, kurse HIB Petrol nuk e jep numrin. Para udhëtimit kontrolloni te operatori.

Çmime publikon vetëm ECHARGE; në hartë ato shihen te karikuesit e saj. Të gjitha çmimet: [Çmimet]({{ PAGES.prices.path }}).

## Si përdoret harta

- **Filtrat** mbi listë: të gjithë, karikuesit e shpejtë DC nga 50 kW, vetëm AC, CHAdeMO dhe rrjetet. Kërkimi gjen sipas emrit, adresës, qytetit dhe rrjetit.
- **Pranë meje** e kërkon vendndodhjen vetëm kur e shtypni butonin; vendndodhja mbetet në shfletuesin tuaj.
- **Të preferuarit** (ylli te karikuesi) ruhen vetëm në këtë shfletues.
- **Navigimi** hap Google Maps, Apple Maps ose Waze.

Nëse mungon një karikues ose një e dhënë është e gabuar, shkruani në [hello@blokvolt.com](mailto:hello@blokvolt.com?subject=Korrigjim%20i%20hart%C3%ABs%20XK) — ose shtojeni karikuesin në [OpenStreetMap](https://www.openstreetmap.org); do të shfaqet në hartë pas freskimit të ardhshëm mujor.

Të dhëna të hapura: [stanice.json](/assets/region/xk/stanice.json) (ODbL 1.0, © OpenStreetMap dhe Open Charge Map).
