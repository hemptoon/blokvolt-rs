# -*- coding: utf-8 -*-
"""Generates content/podaci/tarife-eps.md from content/data/kalkulator.json.

All EPS numbers live in that one file (the calculator reads the same block), so the page and the
calculator can never drift apart. Run: python3 scripts/gen_tarife_eps.py"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import valuta  # noqa: E402

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


def fx_kwh(x):
    return str(valuta.fx_num(x, rate=True, text=sr(x), stack=True))


Z = {z['id']: z for z in E['zones']}
snaga = E['snaga_rsd_kw'] * (1 + E['akciza']) * (1 + E['pdv'])
# an electric car at the site's default assumptions
need = DEF['km'] * DEF['kwh100'] / 100
home = need * (1 + DEF['loss'] / 100)
per100 = {zid: all_in(z['nt']) * DEF['kwh100'] * (1 + DEF['loss'] / 100) for zid, z in Z.items()}

rows = []
for z in E['zones']:
    # each price marked for the display currency (scripts/valuta.py, docs/RUNBOOK.md 3.29): RSD per kWh, converted on the page
    # only for a reader who chose EUR or USD
    rows.append('| {name} | {range} | **{nta}** | {vta} |'.format(name=z['name'].replace(' zona', ''), range=z['range'].replace(' mesečno', ''),
                                                            nta=fx_kwh(all_in(z['nt'])), vta=fx_kwh(all_in(z['vt']))))
table = '\n'.join(rows)
raw = '\n'.join('| {name} | {nt} | {vt} | {j} |'.format(name=z['name'].replace(' zona', ''), nt=sr(z['nt'], 4), vt=sr(z['vt'], 4),
                                                     j=sr(E['jednotarifno'][z['id']], 2) if E['jednotarifno'].get(z['id']) else '—') for z in E['zones'])
nt_rows = '\n'.join(f"| {h['region']} | {h['window']} |" for h in E['nt_hours'])
sources = ' | '.join(f"{s['label']} :: {s['url']}" for s in E['sources'])
diff = (all_in(Z['plava']['vt']) - all_in(Z['plava']['nt'])) * home
J = {zid: all_in(v) for zid, v in E['jednotarifno'].items() if zid in Z and isinstance(v, (int, float))}
# two-tariff meter pays off once this share of the month's kWh is used at night (same in every zone within a point)
breakeven = {zid: (all_in(Z[zid]['vt']) - J[zid]) / (all_in(Z[zid]['vt']) - all_in(Z[zid]['nt'])) for zid in J}
be_pct = round(max(breakeven.values()) * 100)
j_rows = '\n'.join('| {name} | {range} | {j} |'.format(name=z['name'].replace(' zona', ''), range=z['range'].replace(' mesečno', ''),
                                                       j=fx_kwh(J[z['id']])) for z in E['zones'] if z['id'] in J)
nt_list = ', '.join(f"{h['region']} {h['window']}" for h in E['nt_hours'])

md = f"""---
thumb: stambeni-blokovi-sunce
title: Cena struje u Srbiji 2026: kilovat za domaćinstva po zonama
h1: Cena struje za domaćinstva u Srbiji 2026
description: Kilovat struje sa svim dažbinama: od {sr(all_in(Z['zelena']['nt']))} RSD noću u zelenoj do {sr(all_in(Z['crvena']['vt']))} RSD danju u crvenoj zoni. Jednotarifno brojilo i od koliko sati je jeftinija struja.
kicker: Cene struje
lead: Kilovat struje za domaćinstva košta od {sr(all_in(Z['zelena']['nt']))} do {sr(all_in(Z['crvena']['vt']))} RSD sa svim dažbinama, zavisno od zone i tarife. Noću je više od tri puta jeftiniji nego danju.
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

## Cena kilovata struje po zonama

| Zona | Potrošnja mesečno | Noć | Dan |
|---|---|---|---|
{table}

Cene su u RSD po kWh, sa svim naknadama, akcizom i PDV-om. Zona se računa po ukupnoj mesečnoj potrošnji domaćinstva: zelena do 350 kWh, plava od 351 do 1.200 kWh, crvena preko 1.200 kWh.

<details markdown="1">
<summary>Detalji: kako se računa cena</summary>

Na cenu iz cenovnika EPS-a dodaju se naknada za obnovljive izvore ({sr(E['oie'], 3)} RSD/kWh) i naknada za energetsku efikasnost ({sr(E['ee'], 3)} RSD/kWh), pa akciza {sr(E['akciza'] * 100, 1)} % i PDV {int(E['pdv'] * 100)} %.

Zone su stepenice: prvih 350 kWh ide po zelenoj ceni, do 1.200 kWh po plavoj, preko toga po crvenoj. {E['zone_change']}

| Zona | Noć, cenovnik | Dan, cenovnik | Jednotarifno |
|---|---|---|---|
{raw}

Cene iz cenovnika su bez akcize i PDV-a. Jednotarifne cene su iz sekundarnog izvora.

</details>

## Od koliko sati je jeftinija struja

| Region | Niža tarifa |
|---|---|
{nt_rows}

Niža tarifa važi svakog dana, i vikendom, samo uz dvotarifno brojilo. Punjenje podesite da počne tada, tajmerom u autu ili punjaču. U plavoj zoni to je oko {sr(diff, 0)} RSD mesečno manje nego danju.

## Cena struje za jednotarifno brojilo

| Zona | Potrošnja mesečno | Cena kWh |
|---|---|---|
{j_rows}

Sa jednotarifnim brojilom kilovat košta isto danju i noću. Po ovim cenama dvotarifno brojilo je jeftinije čim se noću potroši više od oko {be_pct} % mesečne struje, na primer kad se auto puni noću.

<details markdown="1">
<summary>Detalji: odakle su cene za jednotarifno brojilo</summary>

EPS u cenovniku za domaćinstva objavljuje cene za dvotarifno merenje. Cene za jednotarifno brojilo su iz sekundarnog izvora (vidi izvore), preračunate sa istim naknadama, akcizom i PDV-om kao gore. Zamenu brojila tražite od Elektrodistribucije Srbije.

</details>

## Šta auto menja na računu

Za {sr(DEF['km'], 0)} km mesečno auto troši oko **{sr(home, 0)} kWh** sa brojila ({DEF['kwh100']} kWh na 100 km i {DEF['loss']} % gubitaka). Noću je to {sr(home * all_in(Z['zelena']['nt']), 0)} RSD u zelenoj, **{sr(home * all_in(Z['plava']['nt']), 0)} RSD** u plavoj i {sr(home * all_in(Z['crvena']['nt']), 0)} RSD u crvenoj zoni.

Tih {sr(home, 0)} kWh često prebaci domaćinstvo iz zelene u plavu zonu. Računica za vaš auto: [kalkulator troškova](/alati/kalkulator-troskova/).

Koliko je to u odnosu na benzin i dizel, po cenama goriva ove nedelje: [cena goriva i struje](/podaci/cena-goriva-i-struje/).

<details markdown="1">
<summary>Detalji: obračunska snaga i provera računa</summary>

Na računu je i obračunska snaga: {sr(E['snaga_rsd_kw'], 4)} RSD po kW odobrene snage mesečno, sa dažbinama {sr(snaga)} RSD. Za 17,25 kW (3×25 A) to je oko {sr(snaga * 17.25, 0)} RSD mesečno. Punjač ne menja ovu stavku dok se ne poveća odobrena snaga.

Na računu EPS-a piše da li je brojilo dvotarifno i koliko je kWh u kojoj zoni. Račune vidite na portal.eps.rs. Zamenu jednotarifnog brojila tražite od Elektrodistribucije Srbije.

</details>

## Česta pitanja

<details markdown="1">
<summary>Koliko košta kilovat struje u Srbiji 2026?</summary>

Sa svim dažbinama: u zelenoj zoni {sr(all_in(Z['zelena']['nt']))} RSD noću i {sr(all_in(Z['zelena']['vt']))} RSD danju, u plavoj {sr(all_in(Z['plava']['nt']))} i {sr(all_in(Z['plava']['vt']))} RSD, u crvenoj {sr(all_in(Z['crvena']['nt']))} i {sr(all_in(Z['crvena']['vt']))} RSD. Cenovnik se primenjuje od {E['valid_from']}.

</details>

<details markdown="1">
<summary>Od koliko sati je jeftinija struja?</summary>

Niža tarifa traje osam sati: {nt_list}. Važi svakog dana, i vikendom i praznikom, samo uz dvotarifno brojilo.

</details>

<details markdown="1">
<summary>Šta su zelena, plava i crvena zona?</summary>

To su stepenice mesečne potrošnje domaćinstva: prvih 350 kWh plaća se po zelenoj ceni, sledećih do 1.200 kWh po plavoj, a sve preko toga po crvenoj.

</details>

<details markdown="1">
<summary>Koliko struje mesečno troši električni auto?</summary>

Za {sr(DEF['km'], 0)} km mesečno oko {sr(home, 0)} kWh sa brojila, sa gubicima pri punjenju. Noću u plavoj zoni to je oko {sr(home * all_in(Z['plava']['nt']), 0)} RSD. Računica za vaš auto: [kalkulator troškova](/alati/kalkulator-troskova/).

</details>
"""

OUT.write_text(md, encoding='utf-8')
print(f'written {OUT.name}: {len(md)} chars, {len(E["sources"])} sources')
