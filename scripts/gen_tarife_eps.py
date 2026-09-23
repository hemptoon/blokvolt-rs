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
    rows.append('| {name} | {range} | **{nta}** | {vta} |'.format(name=z['name'].replace(' zona', ''), range=z['range'].replace(' mesečno', ''),
                                                            nta=sr(all_in(z['nt'])), vta=sr(all_in(z['vt']))))
table = '\n'.join(rows)
raw = '\n'.join('| {name} | {nt} | {vt} | {j} |'.format(name=z['name'].replace(' zona', ''), nt=sr(z['nt'], 4), vt=sr(z['vt'], 4),
                                                     j=sr(E['jednotarifno'][z['id']], 2) if E['jednotarifno'].get(z['id']) else '—') for z in E['zones'])
nt_rows = '\n'.join(f"| {h['region']} | {h['window']} |" for h in E['nt_hours'])
sources = ' | '.join(f"{s['label']} :: {s['url']}" for s in E['sources'])
diff = (all_in(Z['plava']['vt']) - all_in(Z['plava']['nt'])) * home

md = f"""---
title: Cena struje za domaćinstva u Srbiji 2026: zone, tarife, niža tarifa
h1: Cena struje kod kuće
description: Kilovat-sat kod kuće sa svim dažbinama: od {sr(all_in(Z['zelena']['nt']))} do {sr(all_in(Z['crvena']['vt']))} RSD, zavisno od zone i tarife. Niža tarifa traje 8 sati, a počinje različito po regionu.
kicker: Cene struje
lead: Kilovat-sat kod kuće košta od {sr(all_in(Z['zelena']['nt']))} do {sr(all_in(Z['crvena']['vt']))} RSD sa svim dažbinama, a noću je više od tri puta jeftiniji nego danju.
updated: {CHECKED}
next_check: {NEXT}
published: 2026-09-23
modified: {MODIFIED}
priority: 0.85
sources: {sources}
---
<div class="sum" markdown="1">
- **{sr(all_in(Z['plava']['nt']))} RSD** kWh noću u plavoj zoni, sa naknadama, akcizom i PDV-om
- Niža tarifa traje **8 sati**: Beograd od 24.00, Vojvodina od 23.00, centralna Srbija od 22.00
- **{sr(per100['plava'], 0)} RSD** struja za 100 km noću (plava zona)
- Cene važe od **{E['valid_from']}**
</div>

## Cena po zonama

| Zona | Potrošnja mesečno | Noć | Dan |
|---|---|---|---|
{table}

Cene su u RSD po kWh, sa svim naknadama, akcizom i PDV-om. Zona se računa po ukupnoj mesečnoj potrošnji domaćinstva.

<details markdown="1">
<summary>Detalji: kako se računa cena</summary>

Na cenu iz cenovnika EPS-a dodaju se naknada za obnovljive izvore ({sr(E['oie'], 3)} RSD/kWh) i naknada za energetsku efikasnost ({sr(E['ee'], 3)} RSD/kWh), pa akciza {sr(E['akciza'] * 100, 1)} % i PDV {int(E['pdv'] * 100)} %.

Zone su stepenice: prvih 350 kWh ide po zelenoj ceni, do 1.200 kWh po plavoj, preko toga po crvenoj. {E['zone_change']}

| Zona | Noć, cenovnik | Dan, cenovnik | Jednotarifno |
|---|---|---|---|
{raw}

Cene iz cenovnika su bez akcize i PDV-a. Jednotarifne cene su iz sekundarnog izvora.

</details>

## Kada počinje niža tarifa

| Region | Niža tarifa |
|---|---|
{nt_rows}

Niža tarifa važi svakog dana, i vikendom, samo uz dvotarifno brojilo. Punjenje podesite da počne tada, tajmerom u autu ili punjaču. U plavoj zoni to je oko {sr(diff, 0)} RSD mesečno manje nego danju.

## Šta auto menja na računu

Za {sr(DEF['km'], 0)} km mesečno auto troši oko **{sr(home, 0)} kWh** sa brojila ({DEF['kwh100']} kWh na 100 km i {DEF['loss']} % gubitaka). Noću je to {sr(home * all_in(Z['zelena']['nt']), 0)} RSD u zelenoj, **{sr(home * all_in(Z['plava']['nt']), 0)} RSD** u plavoj i {sr(home * all_in(Z['crvena']['nt']), 0)} RSD u crvenoj zoni.

Tih {sr(home, 0)} kWh često prebaci domaćinstvo iz zelene u plavu zonu. Računica za vaš auto: [kalkulator troškova](/alati/kalkulator-troskova/).

<details markdown="1">
<summary>Detalji: obračunska snaga i provera računa</summary>

Na računu je i obračunska snaga: {sr(E['snaga_rsd_kw'], 4)} RSD po kW odobrene snage mesečno, sa dažbinama {sr(snaga)} RSD. Za 17,25 kW (3×25 A) to je oko {sr(snaga * 17.25, 0)} RSD mesečno. Punjač ne menja ovu stavku dok se ne poveća odobrena snaga.

Na računu EPS-a piše da li je brojilo dvotarifno i koliko je kWh u kojoj zoni. Račune vidite na portal.eps.rs. Zamenu jednotarifnog brojila tražite od Elektrodistribucije Srbije.

</details>
"""

OUT.write_text(md, encoding='utf-8')
print(f'written {OUT.name}: {len(md)} chars, {len(E["sources"])} sources')
