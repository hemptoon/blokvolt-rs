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
        bits.append(f"<strong>{row['stock']}</strong>")
    vat = row['vat']
    bits.append('cena ' + ('sa PDV-om' if vat.startswith('sa PDV') else 'bez naznake PDV-a' if vat == 'nije naznačen' else vat))
    return '; '.join(bits)


def table(rows):
    out = ['| Model | Snaga | Cena | Prodavac | Napomena |', '|---|---|---|---|---|']
    for r in sorted(rows, key=lambda x: x['price_rsd']):
        kw = sr(r['kw'], 1).rstrip('0').rstrip(',') + ' kW'
        out.append(f"| **{r['brand']} {r['model']}** | {kw} | {price(r['price_rsd'])} RSD | {seller_cell(r)} | {note_cell(r)} |")
    return '\n'.join(out)


def cena_plural(n):
    last, last2 = n % 10, n % 100
    if last == 1 and last2 != 11:
        return f'{n} objavljena cena'
    if last in (2, 3, 4) and last2 not in (12, 13, 14):
        return f'{n} objavljene cene'
    return f'{n} objavljenih cena'


blocks = []
for title, pred in CLASSES:
    rows = [r for r in ROWS if pred(r)]
    if not rows:
        continue
    lo, hi = min(r['price_rsd'] for r in rows), max(r['price_rsd'] for r in rows)
    span = f'{cena_plural(len(rows))}, od {price(lo)} do {price(hi)} RSD.' if len(rows) > 1 else f'{cena_plural(len(rows))}: {price(lo)} RSD.'
    blocks.append(f"### {title}\n\n{span}\n\n{table(rows)}")

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
title: Wallbox modeli u Srbiji 2026 — ko šta prodaje i po kojoj ceni
description: {n_models} modela kućnih punjača sa javno objavljenom cenom kod {n_sellers} prodavaca u Srbiji: od {price(cheap11['price_rsd'])} RSD za 11 kW do preko 150.000 za iste snage. Cene za sam uređaj, sa izvorom i datumom provere ({CHECKED}).
kicker: Podaci · modeli punjača
lead: Isti punjač u Srbiji ume da košta i 30 % više kod drugog prodavca, a „11 kW“ na dve etikete ne znači isti uređaj. Ovde su svi modeli sa javnom cenom, poređani po snazi, sa linkom na prodavca.
updated: {CHECKED}
next_check: {DATA['next_check']}
published: 2026-09-23
modified: {MODIFIED}
priority: 0.85
disclaimer: Cene se menjaju i akcije traju kratko — pre kupovine proverite kod prodavca. Grešku ili noviju cenu prijavite na
sources: {sources}
---
<div class="bva-stats">
<div class="bva-stat"><b>{len(ROWS)}</b><span>javno objavljenih cena uređaja kod {n_sellers} prodavaca u registru</span></div>
<div class="bva-stat"><b>{price(cheap11['price_rsd'])} RSD</b><span>najniža objavljena cena za 11 kW ({cheap11['brand']} {cheap11['model']}) — najskuplji 11 kW je četiri puta skuplji</span></div>
<div class="bva-stat"><b>{price(cheap22['price_rsd'])} RSD</b><span>najniža objavljena cena za 22 kW ({cheap22['brand']} {cheap22['model']})</span></div>
</div>

## Šta je u tabeli

Cena je za **sam uređaj**, bez ugradnje, onako kako je objavljena na sajtu prodavca {CHECKED}. Gde je cena bila bez PDV-a ili u evrima, u napomeni stoji originalna cena, a u koloni je naš preračun (PDV 20 %, 117,2 RSD/€). Kod nekih prodavaca PDV-status uopšte nije označen — i to piše u napomeni, jer je razlika 20 %.

Cene „ključ u ruke“ (uređaj + ugradnja) nisu ovde nego u [uporednoj tabeli cena](/cena-punjaca-za-elektricni-auto), gde su i firme koje uređaj ne prodaju nego samo ugrađuju.

{chr(10).join(blocks)}

## Isti model, različita cena

{dupes}

Razlike nisu greška: neki prodavci daju preporučenu maloprodajnu cenu proizvođača, neki akcijsku, a neki cenu bez kabla. Zato uz svaku cenu proveravamo šta tačno ulazi u nju.

## Šta gledati u specifikaciji

**Kabl ili utičnica.** Uređaj sa Type 2 utičnicom je jeftiniji, ali kabl košta zasebno — kod Oriona je, na primer, kabl od 7 m 42.600 RSD, skoro pola cene punjača. Circontrol eHome 5 se takođe isporučuje bez kabla.

**Brojilo u uređaju (MID).** Ako punjač stoji u zajedničkoj garaži i struja se preračunava stanarima, potreban je overen (MID) obračun. Od svih modela sa javnom cenom, ugrađeno MID brojilo javno navodi {len(mid)} — {', '.join(sorted({m['brand'] + ' ' + m['model'] for m in mid})) if mid else '—'}. Kod ostalih se brojilo ugrađuje zasebno; kako to izgleda u zgradi, piše u vodiču [ko plaća struju](/ko-placa-struju-za-punjenje).

**OCPP, RFID, aplikacija.** OCPP znači da punjač može da radi sa tuđim sistemom za naplatu i nadzor — bitno za zgrade i firme, nepotrebno za kuću. RFID kartica služi da punjač ne koristi bilo ko. Aplikacija je udobnost, ali proverite da li radi bez interneta (punjenje mora da radi i kad padne WiFi).

**Dinamičko ograničenje snage (DLB).** Punjač sam smanjuje struju kad se u stanu uključe šporet i bojler, pa ne iskače glavni osigurač. Kod starijih instalacija to je često jeftinije rešenje nego povećavanje odobrene snage — o tome i o tome zašto 22 kW u praksi retko ima smisla piše u vodiču [koliko košta punjač](/cena-punjaca-za-elektricni-auto).

**11 ili 22 kW.** Skoro svi automobili u Srbiji primaju najviše 11 kW naizmenične struje, a tipična kućna instalacija ionako ima odobrenih 17,25 kW (3×25 A). Punjač od 22 kW ne puni brže ako auto to ne prima.

## Cena uređaja nije cena punjenja

Uz uređaj idu zaštita (FID tip A + automatski osigurač), kabl do table, ugradnja i izveštaj o ispitivanju. Zato kod dve firme koje objavljuju cenu zajedno sa ugradnjom (Evolako i STASANET) 11 kW „ključ u ruke“ košta {price(95000)}–{price(130000)} RSD, dok sam uređaj počinje od {price(cheap11['price_rsd'])} RSD. Ko i pod kojim uslovima ugrađuje — u [registru firmi](/firme/); koliko struja košta posle toga — u [kalkulatoru](/alati/kalkulator-troskova/).
"""

OUT.write_text(md, encoding='utf-8')
print(f'written {OUT.name}: {len(ROWS)} rows, {n_models} models, {n_sellers} sellers')
