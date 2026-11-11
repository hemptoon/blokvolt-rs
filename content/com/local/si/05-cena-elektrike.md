---
key: electricity
slug: cena-elektrike/
order: 5
nav: Cena elektrike
icon: bolt
priority: 0.7
title: Cena elektrike v Sloveniji 2026 za polnjenje avta | BlokVolt
description: Koliko stane kilovatna ura doma v Sloveniji: cene energije GEN-I (VT, MT, ET), razpon pri dobaviteljih, konec regulacije, omrežnina po blokih in DDV 22 %.
h1: Cena elektrike za polnjenje doma
lead: Cene energije pri dobaviteljih, kako se sestavi račun in zakaj skupne cene kWh ni mogoče natančno navesti za vse.
card: Cene energije GEN-I in drugih dobaviteljev, omrežnina, prispevki in DDV.
related: home, prices, subsidies
---
{% set E = C.electricity %}{% set G = E.geni %}
Regulirane cene elektrike za gospodinjstva v Sloveniji ni več: zadnja uredba je veljala {{ E.regulated.period }} (VT {{ E.regulated.vt }}, MT {{ E.regulated.mt }}, ET {{ E.regulated.et }} €/kWh brez DDV). Za leto 2026 regulirane cene ni bilo mogoče najti; vlada pa je 9. 4. 2026 z uredbo določila, da morajo dobavitelji pred zvišanjem cen elektrike za gospodinjstva pridobiti njeno predhodno soglasje (časovno omejen ukrep). Ceno energije zdaj določa dobavitelj; omrežnina je za vse dobavitelje enaka.

## Energija pri GEN-I

Redni cenik GEN-I za gospodinjske odjemalce velja od {{ G.valid }}; GEN-I je 31. 8. 2026 napovedal, da teh cen do {{ G.until }} ne bo zvišal (za obstoječe odjemalce in tiste, ki se pridružijo do 31. 12. 2026).

| Tarifa | Brez DDV | Z DDV 22 % | 100 km (samo energija) |
|---|---|---|---|
| Višja tarifa (VT) | {{ num(G.vt, 5) }} € | {{ num(G.vt_v, 5) }} € | {{ money(G.vt_v * 18.7) }} |
| Manjša tarifa (MT) | {{ num(G.mt, 5) }} € | {{ num(G.mt_v, 5) }} € | {{ money(G.mt_v * 18.7) }} |
| Enotna tarifa (ET) | {{ num(G.et, 5) }} € | {{ num(G.et_v, 5) }} € | {{ money(G.et_v * 18.7) }} |

Mesečno nadomestilo {{ money(G.fee) }} ({{ money(G.fee_v) }} z DDV) ali {{ money(G.fee_e) }} z e-računom. 100 km = 17 kWh × 1,1 (izgube pri polnjenju). Vir: [{{ G.src_label }}]({{ G.src }}).

## Razpon pri dobaviteljih

Po primerjalni strani Tarifnik (september 2026, samo energija, brez DDV): VT {{ E.range.vt }} € (povprečje {{ E.range.vt_avg }}), MT {{ E.range.mt }} € (povprečje {{ E.range.mt_avg }}), ET {{ E.range.et }} € (povprečje {{ E.range.et_avg }}). Zanesljivost je nizka — preverite na ceniku svojega dobavitelja.

## Kaj je še na računu

- **Omrežnina.** Od 1. 10. 2024 se obračunava tudi po dogovorjeni moči v časovnih blokih. V višji sezoni 2025/26 se je za moč v bloku 1 obračunalo 50 % ciljne tarifne postavke, v sezoni 2026/27 (november–februar) 70 %, v naslednji sezoni 90 %. Od 1. 1. 2027 veljajo nove meje časovnih blokov; višja sezona ostaja od novembra do februarja.
- **Primer.** Moč v bloku 1 je novembra in decembra 2025 stala 1,71 € na kW na mesec (polovica od 3,42 €), novembra in decembra 2026 pa 2,68 € na kW (70 % tarife za leto 2026); v nižji sezoni (marec–oktober) blok 1 ne velja. Povprečno gospodinjstvo (4.000 kWh na leto) plača v letu 2026 okoli 182 € omrežnine, leta 2025 okoli 171 €; po stari metodologiji bi plačalo 222,5 € (STA po Agenciji za energijo, 8. 10. 2026).
- **Prispevek OVE+SPTE:** 0,77562 € na kW obračunske moči na mesec (0,94626 € z DDV), po ZPS se znova zaračunava od računov za avgust 2025.
- **DDV:** 22 %.

Avto je najceneje polniti v času manjše tarife in brez dviga dogovorjene moči — polnilnica z dinamičnim upravljanjem obremenitve (pogoj za Borzenovo subvencijo) pri tem pomaga.

{{ w.sources(E.sources) }}
