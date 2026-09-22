# -*- coding: utf-8 -*-
"""Generates content/podaci/tarife-eps.md from content/data/kalkulator.json.

All EPS numbers live in that one file (the calculator reads the same block), so the page and the
calculator can never drift apart. Run: python3 scripts/gen_tarife_eps.py"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = json.load(open(ROOT / 'content' / 'data' / 'kalkulator.json', encoding='utf-8'))
OUT = ROOT / 'content' / 'podaci' / 'tarife-eps.md'
E, DEF = D['eps'], D['defaults']
CHECKED = D.get('checked', '22.09.2026')
NEXT = D.get('tarife_next_check', '15.11.2026')
MODIFIED = '-'.join(reversed(CHECKED.split('.')))


def all_in(x):
    """Regulated price -> what you actually pay: + OIE + EE, then akciza, then PDV."""
    return (x + E['oie'] + E['ee']) * (1 + E['akciza']) * (1 + E['pdv'])


def sr(x, d=2):
    s = f'{x:,.{d}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    return s


Z = {z['id']: z for z in E['zones']}
snaga = E['snaga_rsd_kw'] * (1 + E['akciza']) * (1 + E['pdv'])
# an electric car at the site's default assumptions
need = DEF['km'] * DEF['kwh100'] / 100
home = need * (1 + DEF['loss'] / 100)
per100 = {zid: all_in(z['nt']) * DEF['kwh100'] * (1 + DEF['loss'] / 100) for zid, z in Z.items()}

rows = []
for z in E['zones']:
    j = E['jednotarifno'].get(z['id'])
    rows.append('| {name} | {range} | {vt} / **{vta}** | {nt} / **{nta}** | {j} |'.format(
        name=z['name'], range=z['range'], vt=sr(z['vt'], 4), vta=sr(all_in(z['vt'])),
        nt=sr(z['nt'], 4), nta=sr(all_in(z['nt'])), j=(sr(j, 2) + ' / ' + sr(all_in(j))) if j else '—'))
table = '\n'.join(rows)

nt_rows = '\n'.join(f"| {h['region']} | {h['window']} |" for h in E['nt_hours'])
sources = ' | '.join(f"{s['label']} :: {s['url']}" for s in E['sources'])

md = f"""---
title: Cena struje za domaćinstva u Srbiji 2026 — zone, tarife i sati niže tarife
description: Koliko zaista košta kilovat-sat kod kuće: regulisane cene EPS-a po zonama i tarifama, plus naknade, akciza i PDV — od {sr(all_in(Z['zelena']['nt']))} do {sr(all_in(Z['crvena']['vt']))} RSD. Sati niže tarife razlikuju se po regionu. Stanje {CHECKED}.
kicker: Podaci · cene struje
lead: Na računu ne piše jedna cena nego šest, a na svaku idu još dve naknade, akciza i PDV. Evo kako se to slaže u cenu koju stvarno plaćate — i šta menja električni auto u garaži.
updated: {CHECKED}
next_check: {NEXT}
published: 2026-09-23
modified: {MODIFIED}
priority: 0.85
disclaimer: Cene su regulisane i menjaju se odlukom EPS-a; naknade i akciza odlukama Vlade. Ako vidite noviji cenovnik, javite nam na
sources: {sources}
---
<div class="bva-stats">
<div class="bva-stat"><b>{sr(all_in(Z['plava']['nt']))} RSD</b><span>kilovat-sat noću u plavoj zoni, sa svim naknadama, akcizom i PDV-om — cena po kojoj se najčešće puni auto kod kuće</span></div>
<div class="bva-stat"><b>8 sati</b><span>traje niža tarifa svakog dana, ali ne počinje svuda u isto vreme: Beograd 24.00, Vojvodina 23.00, centralna Srbija 22.00</span></div>
<div class="bva-stat"><b>{sr(per100['plava'], 0)} RSD</b><span>struja za 100 km električnim autom po noćnoj tarifi u plavoj zoni ({DEF['kwh100']} kWh/100 km + {DEF['loss']} % gubitaka pri punjenju)</span></div>
</div>

## Kratko

Regulisana cena važi od **{E['valid_from']}** i ima tri zone i dve tarife. Na regulisanu cenu se dodaju naknada za podsticaj povlašćenih proizvođača ({sr(E['oie'], 3)} RSD/kWh), naknada za energetsku efikasnost ({sr(E['ee'], 3)} RSD/kWh), zatim akciza {sr(E['akciza'] * 100, 1)} % i na kraju PDV {int(E['pdv'] * 100)} %. Zato je cena koju plaćate oko 40 % viša od one iz cenovnika.

Za punjenje automobila kod kuće bitne su dve stvari: **tarifa** (noću je struja tri do četiri puta jeftinija) i **zona** (potrošnja preko granice ide po skupljoj ceni). Kalkulator sa vašim kilometrima i tarifom je na stranici [kalkulator troškova](/alati/kalkulator-troskova/).

## Tri zone: kako se računa cena

{E['zone_note']} {E['zone_change']}

Zone nisu „popust za štedljive“ nego stepenice: prvih 350 kWh uvek ide po najnižoj ceni, sledećih do 1.200 kWh po plavoj, a tek ono iznad po crvenoj. Domaćinstvo koje mesečno potroši 500 kWh ne plaća sve po plavoj ceni — plaća 350 kWh po zelenoj i 150 kWh po plavoj.

| Zona | Potrošnja | Viša tarifa (VT): cenovnik / sa dažbinama | Niža tarifa (NT): cenovnik / sa dažbinama | Jednotarifno |
|---|---|---|---|---|
{table}

Cene iz cenovnika su bez akcize i PDV-a i sadrže i pristup mreži; podebljane su cene sa svim naknadama, akcizom i PDV-om — to je ono što plaćate po kilovat-satu. Cene za **jednotarifno** merenje EPS ne objavljuje na stranici sa cenama (odluka je skenirana), pa su preuzete iz sekundarnog izvora i označene kao takve.

## Šta još stoji na računu

Pored kilovat-sati, tu je i **obračunska snaga**: {sr(E['snaga_rsd_kw'], 4)} RSD po kilovatu odobrene snage mesečno, odnosno **{sr(snaga)} RSD/kW sa akcizom i PDV-om**. Domaćinstvo sa uobičajenom odobrenom snagom od 17,25 kW (3×25 A) na toj stavci plaća oko {sr(snaga * 17.25, 0)} RSD mesečno, bez obzira na to koliko je struje potrošilo. Kućni punjač od 11 kW sam po sebi ne menja tu stavku dok se ne menja odobrena snaga.

## Kada je niža tarifa — zavisi od regiona

{E['nt_note']}

| Region | Niža tarifa |
|---|---|
{nt_rows}

Za auto to znači jednu jednostavnu stvar: punjenje treba da počne kad krene niža tarifa u vašem regionu, a ne „kad se vratite kući“. Svaki punjač i svaki automobil imaju tajmer; razlika između VT i NT u plavoj zoni je {sr(all_in(Z['plava']['vt']) - all_in(Z['plava']['nt']))} RSD po kilovat-satu, odnosno oko {sr((all_in(Z['plava']['vt']) - all_in(Z['plava']['nt'])) * home, 0)} RSD mesečno za {sr(home, 0)} kWh.

## Šta električni auto znači za račun

Za {sr(DEF['km'], 0)} km mesečno i potrošnju od {DEF['kwh100']} kWh/100 km automobilu treba oko {sr(need, 0)} kWh, a sa gubicima pri punjenju (oko {DEF['loss']} %) iz zida izlazi oko **{sr(home, 0)} kWh mesečno**. Po noćnoj tarifi to je {sr(home * all_in(Z['zelena']['nt']), 0)} RSD u zelenoj, **{sr(home * all_in(Z['plava']['nt']), 0)} RSD u plavoj** i {sr(home * all_in(Z['crvena']['nt']), 0)} RSD u crvenoj zoni. Po višoj tarifi iste te kilovat-sate platili biste {sr(home * all_in(Z['plava']['vt']), 0)} RSD (plava zona).

Ono što se obično previdi: tih {sr(home, 0)} kWh **pomera celo domaćinstvo u sledeću zonu**. Domaćinstvo koje je inače u zelenoj zoni (do 350 kWh) sa autom prelazi u plavu, pa se skuplje plaća i struja za sve ostalo iznad granice. Ako u zgradi punjenje ide preko zajedničkog brojila, isto se dešava zgradi — zato se u [vodiču o tome ko plaća struju](/ko-placa-struju-za-punjenje) predlaže zasebno brojilo i obračun po stvarnoj potrošnji.

Za poređenje: 100 km na struju po noćnoj tarifi košta oko {sr(per100['plava'], 0)} RSD (plava zona), dok isto rastojanje na benzinu, po {sr(D['fuel']['benzin'], 0)} RSD/l i potrošnji {sr(DEF['l100_benzin'], 1)} l/100 km, košta oko {sr(DEF['l100_benzin'] / 100 * D['fuel']['benzin'] * 100, 0)} RSD.

## Kako da proverite svoju tarifu i zonu

Na računu EPS-a piše da li je brojilo jedno- ili dvotarifno i koliko je kilovat-sati palo u koju zonu. Uvid u račune je na portalu EPS-a (portal.eps.rs), a informativni obračun na kalkulator.eps.rs. Ako imate jednotarifno brojilo a planirate punjenje kod kuće, zamena za dvotarifno se traži od Elektrodistribucije Srbije i obično se isplati u prvim mesecima.
"""

OUT.write_text(md, encoding='utf-8')
print(f'written {OUT.name}: {len(md)} chars, {len(E["sources"])} sources')
