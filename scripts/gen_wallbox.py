# -*- coding: utf-8 -*-
"""Generates content/podaci/wallbox-modeli.md from content/data/wallbox-modeli.json.

The JSON is the model-level view of the same prices that sit in the firm register
(content/firme/*.json) — re-derive it during the quarterly firm revision.
Run: python3 scripts/gen_wallbox.py"""
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = json.load(open(ROOT / 'content' / 'data' / 'wallbox-modeli.json', encoding='utf-8'))
FIRMS = {}
for f in sorted((ROOT / 'content' / 'firme').glob('*.json')):
    d = json.load(open(f, encoding='utf-8'))
    FIRMS[d['slug']] = d
OUT = ROOT / 'content' / 'podaci' / 'wallbox-modeli.md'
CHECKED = DATA['checked']
MODIFIED = '-'.join(reversed(CHECKED.split('.')))
ROWS = DATA['rows']


def sr(x, d=0):
    s = f'{x:,.{d}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    return s


def price(v):
    return sr(v, 2) if abs(v - round(v)) > 0.005 else sr(v, 0)


CLASSES = [('Jednofazni: 7–7,4 kW', lambda r: r['kw'] < 11 and not r.get('commercial')),
           ('Trofazni: 11 kW', lambda r: 11 <= r['kw'] < 22 and not r.get('commercial')),
           ('Trofazni: 22 kW', lambda r: r['kw'] >= 22 and not r.get('commercial')),
           ('Za zgrade i firme', lambda r: bool(r.get('commercial')))]

def seller_cell(row):
    f = FIRMS.get(row['seller'])
    name = f['name'] if f else row['seller']
    return f'<a href="/firme/{row["seller"]}/">{name}</a>'


def note_cell(row):
    bits = []
    if row.get('note'):
        bits.append(row['note'])
    if row.get('stock'):
        bits.append(row['stock'])
    return '; '.join(bits)


def vat_note(row):
    vat = row['vat']
    if vat.startswith('sa PDV'):
        return ''
    return 'PDV nije naznačen' if vat == 'nije naznačen' else vat


def table(rows):
    out = ['| Model | Snaga | Cena | Prodavac |', '|---|---|---|---|']
    for r in sorted(rows, key=lambda x: x['price_rsd']):
        kw = sr(r['kw'], 1).rstrip('0').rstrip(',') + ' kW'
        note = note_cell(r)
        vat = vat_note(r)
        model = f"**{r['brand']} {r['model']}**" + (f"<small>{note}</small>" if note else '')
        cena = f"{price(r['price_rsd'])} RSD" + (f"<small>{vat}</small>" if vat else '')
        out.append(f"| {model} | {kw} | {cena} | {seller_cell(r)} |")
    return '\n'.join(out)


def cena_plural(n):
    last, last2 = n % 10, n % 100
    if last == 1 and last2 != 11:
        return f'{n} objavljena cena'
    if last in (2, 3, 4) and last2 not in (12, 13, 14):
        return f'{n} objavljene cene'
    return f'{n} objavljenih cena'


def pl(n, one, few, many):
    """Serbian noun form for a count (without the number): 1/21 model, 2-4 modela, 5+ modela."""
    last, last2 = n % 10, n % 100
    if last == 1 and last2 != 11:
        return one
    if last in (2, 3, 4) and last2 not in (12, 13, 14):
        return few
    return many


blocks = []
for title, pred in CLASSES:
    rows = [r for r in ROWS if pred(r)]
    if not rows:
        continue
    lo, hi = min(r['price_rsd'] for r in rows), max(r['price_rsd'] for r in rows)
    span = f'Od {price(lo)} do {price(hi)} RSD ({cena_plural(len(rows))}).' if len(rows) > 1 else f'{price(lo)} RSD.'
    blocks.append(f"## {title}\n\n{span}\n\n{table(rows)}")

# same model at more than one seller
same = defaultdict(list)
for r in ROWS:
    same[(r['brand'], r['model'].split(' (')[0])].append(r)
dupes = []
for (brand, model), rs in sorted(same.items()):
    if len({r['seller'] for r in rs}) < 2:
        continue
    rs = sorted(rs, key=lambda x: x['price_rsd'])
    parts = ', '.join(f"{price(r['price_rsd'])} RSD ({FIRMS[r['seller']]['name']})" for r in rs)
    d = rs[-1]['price_rsd'] - rs[0]['price_rsd']
    dupes.append(f"- **{brand} {model}**: {parts} — razlika {price(d)} RSD.")
dupes = '\n'.join(dupes + [''] + DATA.get('compare_notes', []) and dupes + [''] + ['- ' + n for n in DATA.get('compare_notes', [])])

n_sellers = len({r['seller'] for r in ROWS})
n_models = len({(r['brand'], r['model']) for r in ROWS})
cheap11 = min((r for r in ROWS if 11 <= r['kw'] < 22), key=lambda x: x['price_rsd'])
cheap22 = min((r for r in ROWS if r['kw'] >= 22 and not r.get('commercial')), key=lambda x: x['price_rsd'])
mid = [r for r in ROWS if 'MID' in (r['model'] + r.get('note', ''))]

sources = ' | '.join(sorted({f"{FIRMS[r['seller']]['name']} — cene sa sajta ({CHECKED}) :: {r['url']}" for r in ROWS}))

md = f"""---
title: Wallbox modeli u Srbiji 2026: cene kućnih punjača kod prodavaca
h1: Wallbox modeli i cene
description: {n_models} {pl(n_models, 'model', 'modela', 'modela')} kućnih punjača sa javnom cenom kod {n_sellers} {pl(n_sellers, 'prodavca', 'prodavca', 'prodavaca')} u Srbiji: 11 kW od {price(cheap11['price_rsd'])} RSD, 22 kW od {price(cheap22['price_rsd'])} RSD. Cena samog uređaja, bez ugradnje.
kicker: Modeli punjača
lead: Cene samih uređaja kod prodavaca u Srbiji, po snazi. Isti model kod drugog prodavca može da košta i 30 % više.
updated: {CHECKED}
next_check: {DATA['next_check']}
published: 2026-09-23
modified: {MODIFIED}
priority: 0.85
sources: {sources}
---
<div class="sum" markdown="1">
- **{len(ROWS)}** {pl(len(ROWS), 'objavljena cena', 'objavljene cene', 'objavljenih cena')} kod **{n_sellers}** {pl(n_sellers, 'prodavca', 'prodavca', 'prodavaca')}
- 11 kW od **{price(cheap11['price_rsd'])} RSD** ({cheap11['brand']} {cheap11['model']})
- 22 kW od **{price(cheap22['price_rsd'])} RSD** ({cheap22['brand']} {cheap22['model']})
- Cena je za **sam uređaj**; ugradnja, kabl do table i zaštita plaćaju se posebno
</div>

Cene su prepisane sa sajtova prodavaca. Gde cena nije sa PDV-om, to piše ispod cene. Punjač sa ugradnjom: [koliko košta kućni punjač](/cena-punjaca-za-elektricni-auto).

{chr(10).join(blocks)}

<details markdown="1">
<summary>Isti model kod više prodavaca</summary>

{dupes}

Razlika je obično u tome da li je cena preporučena, akcijska ili bez kabla.

</details>

## Šta gledati pri kupovini

- **Snaga:** većina automobila prima najviše 11 kW naizmenične struje. Punjač od 22 kW ne puni brže ako ga auto ne prima.
- **Kabl ili utičnica:** uređaj sa Type 2 utičnicom je jeftiniji, ali se kabl kupuje posebno.
- **Brojilo (MID):** za zajedničku garažu treba overeno merenje. Ugrađeno MID brojilo navodi {len(mid)} {pl(len(mid), 'model', 'modela', 'modela')}.
- **Raspodela snage (DLB):** punjač smanjuje struju kad rade šporet i bojler, pa ne iskače glavni osigurač.

<details markdown="1">
<summary>Detalji: OCPP, RFID, aplikacija</summary>

OCPP znači da punjač radi sa tuđim sistemom za naplatu i nadzor; to je bitno za zgrade i firme. RFID kartica sprečava da punjač koristi bilo ko. Aplikacija je korisna, ali punjenje mora da radi i bez interneta. Modeli sa MID brojilom: {', '.join(sorted({m['brand'] + ' ' + m['model'] for m in mid})) if mid else '—'}. Kako se meri struja u zgradi: [ko plaća struju](/ko-placa-struju-za-punjenje).

</details>
"""

OUT.write_text(md, encoding='utf-8')
print(f'written {OUT.name}: {len(ROWS)} rows, {n_models} models, {n_sellers} sellers')
