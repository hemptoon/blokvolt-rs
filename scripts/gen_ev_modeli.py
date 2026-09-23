# -*- coding: utf-8 -*-
"""Generates content/podaci/cene-elektricnih-automobila.md from content/data/ev-modeli.json.
Prices are copied from importers' Serbian sites / price lists (check date in the JSON). Run: python3 scripts/gen_ev_modeli.py"""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = json.load(open(ROOT / 'content' / 'data' / 'ev-modeli.json', encoding='utf-8'))
FOTO = json.load(open(ROOT / 'content' / 'data' / 'ev-foto.json', encoding='utf-8'))
FOTO_ITEMS = FOTO['items']


def thumb(brand, model, name):
    """Illustrative photo from Wikimedia Commons, if we have one for this model."""
    f = FOTO_ITEMS.get(f'{brand}||{model}')
    if not f:
        # same footprint as a photo, so every name in the column starts at the same place
        return '<span class="evm-i evm-none" aria-hidden="true"></span>'
    return (f'<img class="evm-i" src="/assets/auto/{f["slug"]}.png?v={f["v"]}" alt="" width="{FOTO["w"]}" '
            f'height="{FOTO["h"]}" loading="lazy" decoding="async">')

OUT = ROOT / 'content' / 'podaci' / 'cene-elektricnih-automobila.md'
SUB = DATA.get('subsidy_eur', 5000)
CHECKED = DATA.get('checked', '22.09.2026')
NEXT_CHECK = DATA.get('next_check', '15.11.2026')
MODIFIED = '-'.join(reversed(CHECKED.split('.')))


def plural(n, one, few, many):
    """Serbian count agreement: 1 slika / 2-4 slike / 5+ slika."""
    last, last2 = n % 10, n % 100
    if last == 1 and last2 != 11:
        return f'{n} {one}'
    if last in (2, 3, 4) and last2 not in (12, 13, 14):
        return f'{n} {few}'
    return f'{n} {many}'


def eur(x):
    return f"{int(round(x)):,}".replace(',', '.') + ' €'

# display names where the JSON model name is awkward
NAME = {
    ('Mercedes-Benz', 'Električna G-Klasa (G 580 sa EQ tehnologijom)'): 'Mercedes-Benz G 580 sa EQ tehnologijom',
    ('Mercedes-Benz', 'Mercedes-Maybach EQS SUV'): 'Mercedes-Maybach EQS SUV',
    ('Toyota', 'Proace City Verso Electric (putnički kombi, M1)'): 'Toyota Proace City Verso Electric',
    ('Fiat', 'Grande Panda (električni)'): 'Fiat Grande Panda',
    ('MINI', 'Cooper E (električni)'): 'MINI Cooper E',
    ('MINI', 'Countryman (električni)'): 'MINI Countryman E',
    ('BMW', 'iX3 (Neue Klasse)'): 'BMW iX3',
}
# cleaned version labels (cheapest published version)
VERSION = {
    'Dolphin Surf': 'Boost / Comfort, 43,2 kWh', 'Atto 2': 'Comfort', 'Atto 3 Evo': 'Design RWD', 'Seal': 'Design RWD',
    'Sealion 7': 'Design', 'ID. Polo': 'Trend', 'ID.3 Neo': '', 'ID.4': 'Pure', 'ID.5': '', 'ID.7': '',
    'IONIQ 5': 'najniža cena u cenovniku', 'bZ4X': '', 'bZ4X Touring': '', 'ë-C3': 'YOU, 44 kWh', 'ë-C3 Aircross': '44 kWh',
    'ë-C4': '50 kWh', 'ë-C4 X': '50 kWh', 'EQE limuzina': '', 'EQE SUV': '', 'EQS limuzina': '', 'EQS SUV': '',
    'Električna G-Klasa (G 580 sa EQ tehnologijom)': '', 'Mercedes-Maybach EQS SUV': '', 'e-JS4': '', 'EV3': '', 'Elight': '', 'EWind': '',
    'Spring': 'Electric 65', 'Proace City Verso Electric (putnički kombi, M1)': 'Compact Shuttle, 50 kWh (putnički kombi)',
    'Niro EV': 'EX Limited Edition, 64,8 kWh', 'Grande Panda (električni)': 'POP, 44 kWh',
}
VERSION_BM = {('Kia', 'EV3'): '58,3 kWh STAR', ('JMEV', 'EV3'): ''}
# price list dates we could read (otherwise: page checked on CHECKED)
DATES = {
    ('Dacia', 'Spring'): 'cenovnik 01.09.2026', ('Renault', 'Twingo E-Tech electric'): 'cenovnik 01.09.2026',
    ('Renault', 'Renault 5 E-Tech electric'): 'cenovnik 01.09.2026', ('Renault', 'Renault 4 E-Tech electric'): 'cenovnik 01.07.2026',
    ('Hyundai', 'INSTER'): 'cenovnik 06.05.2026', ('Hyundai', 'IONIQ 5'): 'cenovnik 11.09.2025 (stariji)', ('Hyundai', 'IONIQ 6'): 'cenovnik 11.09.2025 (stariji)',
    ('Hyundai', 'IONIQ 6 N'): 'cenovnik 12.08.2026', ('Hyundai', 'IONIQ 9'): 'cenovnik 06.05.2026',
    ('Toyota', 'C-HR+'): 'cenovnik 14.09.2026', ('Toyota', 'Proace City Verso Electric (putnički kombi, M1)'): 'cenovnik 02.04.2026',
    ('Fiat', 'Grande Panda (električni)'): 'cenovnik 01.08.2026', ('Fiat', '500e'): 'cenovnik 01.08.2026', ('Fiat', '600e'): 'cenovnik 12.02.2025 (stariji)',
    ('Peugeot', 'E-208'): 'cenovnik 01.11.2025', ('Peugeot', 'E-2008'): 'cenovnik 11.2025', ('Peugeot', 'E-3008'): 'cenovnik, datum nejasan', ('Peugeot', 'E-5008'): 'cenovnik, datum nejasan',
    ('Škoda', 'Elroq'): 'cenovnik MY2027, bez datuma', ('Škoda', 'Enyaq'): 'cenovnik MY2027, bez datuma', ('Škoda', 'Enyaq Coupé'): 'cenovnik MY2027, bez datuma',
    ('Ford', 'Puma Gen-E'): 'cenovnik 07.2026', ('Ford', 'Explorer EV'): 'cenovnik 06.2026', ('Ford', 'Capri'): 'cenovnik 04.2026',
}
for m in ('iX1', 'iX2', 'i4', 'iX3 (Neue Klasse)', 'i5', 'i5 Touring', 'iX', 'i7'):
    DATES[('BMW', m)] = 'cenovnik 01.07.2026'
for m in ('Cooper E (električni)', 'Aceman', 'Countryman (električni)'):
    DATES[('MINI', m)] = 'cenovnik 01.06.2026'

rows = []
for b in DATA['brands']:
    brand = b['brand']
    for m in b.get('models', []):
        if m.get('source_type') not in ('official', 'pricelist_pdf'):
            continue
        reg, promo = m.get('price_regular'), m.get('price_promo')
        if not reg and not promo:
            continue
        model = m['model']
        name = NAME.get((brand, model)) or (model if model.lower().startswith(brand.lower()) else f'{brand} {model}')
        ver = VERSION_BM.get((brand, model), VERSION.get(model, m.get('version') or ''))
        notes = []
        if m.get('price_includes_subsidy') is True:
            after = promo or reg
            base = after + SUB
            price_cell = f'{eur(base)}<small>računica: uvoznik objavljuje {eur(after)} sa uračunatom subvencijom</small>'
            after_cell = f'{eur(after)}<small>cena uvoznika</small>'
        elif brand == 'Ford' and promo and reg and reg - promo == SUB:
            base = reg
            price_cell = f'{eur(reg)}<small>u cenovniku i „akcijska cena“ {eur(promo)}</small>'
            after_cell = f'{eur(reg - SUB)}<small>= akcijska cena; cenovnik ne kaže da li je to subvencija</small>'
        elif promo and reg and brand == 'Toyota':
            base = reg
            price_cell = f'{eur(reg)}<small>u cenovniku i {eur(promo)} — proverite uslove</small>'
            after_cell = eur(reg - SUB)
        elif promo and reg:
            base = promo
            price_cell = f'{eur(promo)}<small>akcija; redovna {eur(reg)}</small>'
            after_cell = eur(promo - SUB)
        else:
            base = reg or promo
            price_cell = eur(base)
            after_cell = eur(base - SUB)
        if brand == 'Toyota' and model == 'bZ4X':
            price_cell += '<small>na naslovnoj toyota.rs: 39.990 €</small>'
        vat = m.get('vat') or ''
        kind = 'cenovnik' if m.get('source_type') == 'pricelist_pdf' else 'sajt uvoznika'
        date = DATES.get((brand, model), f'provereno {CHECKED}')
        src = f'[{kind}]({m["url"]})<small>{date}' + ('; PDV nije naveden' if vat == 'nije navedeno' else '') + '</small>'
        model_cell = ('<span class="evm">' + thumb(brand, model, name) + '<span class="evm-t">' + name
                      + (f'<small>{ver}</small>' if ver else '') + '</span></span>')
        rows.append((base, model_cell, price_cell, after_cell, src, brand, name, model))

rows.sort(key=lambda r: (r[0], r[6]))
n_models = len(rows)
brands_priced = sorted({r[5] for r in rows})
under30 = sum(1 for r in rows if r[0] < 30000)
cheapest = rows[0]

table = ['| Model | Cena od | Posle subvencije 5.000 € | Izvor |', '|---|---|---|---|']
for base, model_cell, price_cell, after_cell, src, brand, name, model_key in rows:
    table.append(f'| {model_cell} | {price_cell} | {after_cell} | {src} |')

IMPORTERS = [
    ('BYD', 'TDV Automotive', 'Beograd, Novi Sad, Niš'),
    ('Škoda', 'Autočačak', 'Beograd, Čačak, Niš, Veternik (Novi Sad), Šabac, Palić, Kragujevac, Zrenjanin, Valjevo, Kruševac, Novi Pazar, Paraćin'),
    ('Volkswagen, Audi', 'Porsche SCG', 'VW: Beograd, Novi Sad, Niš, Kragujevac, Čačak, Jagodina, Subotica, Šabac · Audi: Beograd, Novi Sad, Niš, Čačak'),
    ('Renault, Dacia', 'KEOS (Emil Frey grupa)', 'Beograd, Novi Sad, Niš, Subotica, Kragujevac, Čačak, Šabac, Pančevo, Zrenjanin, Jagodina, Kraljevo, Užice, Vrnjačka Banja, Veliko Gradište, Veternik'),
    ('Hyundai', 'Hyundai Srbija', 'Beograd, Novi Sad, Niš, Čačak, Kraljevo, Jagodina, Zrenjanin, Šabac, Sombor, Subotica'),
    ('Fiat', 'Crossroad Adria', 'Beograd, Novi Sad, Kragujevac, Čačak, Subotica, Šabac, Zrenjanin'),
    ('Citroën, Leapmotor', 'Avtonova KAB', 'Citroën: Beograd, Novi Sad, Niš, Čačak, Bačka Topola · Leapmotor (prema medijima): Beograd, Novi Sad'),
    ('Peugeot', 'Euroimpex Autogroup', 'Beograd (ostala mreža samo na mapi sajta)'),
    ('BMW, MINI', 'Delta Motors (Delta Auto Grupa)', 'Beograd, Novi Sad, Niš, Čačak, Novi Pazar, Vlaška'),
    ('Mercedes-Benz', 'nije naveden na sajtu marke', 'Beograd, Novi Sad, Niš, Čačak, Novi Pazar'),
    ('Ford, MG', 'Grand Motors', 'Ford: Beograd, Novi Sad, Niš, Subotica, Čačak, Šabac, Pančevo, Kragujevac · MG: lokator samo na mapi'),
    ('Geely', 'VCAG', 'Beograd (Zemun), Novi Sad, Niš, Kragujevac, Požarevac, Subotica'),
    ('Kia', 'Kia Auto (KMAG)', 'lokator na sajtu se učitava samo na mapi'),
    ('Toyota', 'Toyota Srbija', 'lokator na sajtu se učitava samo na mapi'),
    ('JAC', 'prodavac Mašinopromet', 'Beograd'),
    ('JMEV', 'CUBI', 'Novi Sad'),
]
imp = ['| Marka | Uvoznik (kako ga navodi sajt) | Gradovi sa salonom ili ovlašćenim prodavcem |', '|---|---|---|']
for a, b_, c in IMPORTERS:
    imp.append(f'| {a} | {b_} | {c} |')

# photo credits: every rendered thumbnail, with author, license and link to the file page
used_foto = [(name, FOTO_ITEMS[f'{brand}||{model_key}'])
             for base, model_cell, price_cell, after_cell, src, brand, name, model_key in rows
             if f'{brand}||{model_key}' in FOTO_ITEMS]
credit_li = '\n'.join(
    f'<li><b>{nm}</b> — {f["au"]}, <a href="{f["licurl"]}" rel="nofollow noopener">{f["lic"]}</a>, '
    f'<a href="{f["page"]}" rel="nofollow noopener">Wikimedia Commons</a></li>'
    for nm, f in sorted(used_foto, key=lambda x: x[0].lower()))
n_foto = len(used_foto)

sources = [
    'Uredba o subvencionisanoj kupovini novih vozila isključivo na električni pogon (Sl. glasnik 12/2026 i 86/2026) :: https://www.paragraf.rs/propisi/uredba-o-uslovima-subvencionisane-kupovine-elektricnih-hibridnih-vozila.html',
    'Kia EV3 — cena sa uračunatom subvencijom :: https://www.kia.rs/ev3',
    'Dacia Spring — cenovnik od 01.09.2026 :: https://www.dacia.rs/CountriesData/Serbia/images/pdf/pricelist/spring-pricelist.pdf',
    'Renault — cenovnik Renault 5 (subvencija nije uračunata) :: https://www.renault.rs/CountriesData/Serbia/images/pdf/pricelist/renault-5-pricelist.pdf',
    'Volkswagen — svi modeli sa cenama :: https://www.volkswagen.rs/modeli-i-konfigurator/svi-modeli',
    'Škoda — cenovnici :: https://www.skoda-auto.rs/kontakti/cenovnik',
    'BMW — cenovnik :: https://www.bmw.rs/sr/topics/offers-and-services/bmw-cenovnik.html',
    'Fiat — cenovnici i brošure :: https://www.fiat.rs/ponude-i-kupovina/cenovnici-i-brosure',
    'Hyundai — cenovnici :: https://www.hyundai.rs/cenovnici',
    'Toyota — cenovnici i katalozi :: https://www.toyota.rs/new-cars/pricelists-catalogues',
    'Auto Motorevija, 26.07.2026 — prva polovina 2026: 535 novih električnih automobila (SAUVD) :: https://www.automotorevija.rs/rubrike/veliki-rast-prodaje-novih-vozila-u-srbiji',
    'BYD Srbija, 23.07.2026 — podatak uvoznika o najprodavanijim modelima :: https://byd-auto.rs/vesti/byd-u-top-10-brendova-u-srbiji-i-apsolutni-lider-ev-segmenta/',
    'Tesla — prodajni centri, Srbija (lista prazna) :: https://www.tesla.com/findus/list/stores/Serbia',
    'Fotografije modela — Wikimedia Commons, slobodne licence (autori i licence su na stranici) :: https://commons.wikimedia.org/',
]

md = f"""---
title: Cene električnih automobila u Srbiji 2026: svi modeli kod uvoznika
h1: Cene električnih automobila
description: {n_models} električnih modela {len(brands_priced)} marki sa javnom cenom kod uvoznika u Srbiji: od {eur(cheapest[0])} (Dacia Spring), {under30} ispod 30.000 €. Cena pre i posle subvencije od 5.000 €.
kicker: Modeli i cene
lead: Najniža cena svakog električnog modela kod zvaničnih uvoznika u Srbiji, pre i posle subvencije od 5.000 €.
updated: {CHECKED}
next_check: {NEXT_CHECK}
published: 2026-09-22
modified: {MODIFIED}
priority: 0.8
sources: {' | '.join(sources)}
---
<div class="sum" markdown="1">
- Najjeftiniji: **{eur(cheapest[0])}** (Dacia Spring), posle subvencije **{eur(cheapest[0] - SUB)}**
- **{n_models}** modela {len(brands_priced)} marki sa javnom cenom, **{under30}** ispod 30.000 €
- Subvencija **5.000 €** za nov automobil, prijava do **1. decembra 2026.** ([uslovi](/podaci/subvencije-2026/))
</div>

## Modeli i cene

„Cena od“ je najniža cena koju uvoznik objavljuje, po pravilu sa PDV-om. Kad uvoznik objavi cenu već umanjenu za subvenciju, u tabeli je cena pre subvencije, a objavljena cena stoji ispod.

{chr(10).join(table)}

<details markdown="1">
<summary>Modeli bez javne cene</summary>

Cenu na srpskom sajtu nije moguće pročitati za: **Audi** (Q4 e-tron, Q6 e-tron, A6 e-tron, e-tron GT), **Kia** (EV2, EV4, EV6, EV9), **Opel** (Astra, Frontera, Grandland Electric), **MG** (MG4, MG5, MGS5 EV), **Geely** (E5), **Volvo** (EX30, EX60, EX90), **Mazda** (6e, CX-6e), **Ford** Mustang Mach-E i **Leapmotor** (T03, B10, C10).

Cupra Tavascan „čeka homologaciju“, a Nissan ne prikazuje nijedan električni model. **Tesla** u Srbiji nema zvaničnog uvoznika; automobili stižu individualnim uvozom ([uvoz i carina](/podaci/uvoz-i-carina/)).

</details>

<details markdown="1">
<summary>Uvoznici i gradovi sa salonima</summary>

{chr(10).join(imp)}

</details>

## Pre kupovine

- Pitajte da li je cena za auto sa zaliha ili za naručivanje i koliko se čeka isporuka.
- Proverite da li „akcijska cena“ već sadrži subvenciju.
- Subvencija može biti i učešće u lizingu ([krediti i lizing](/podaci/krediti-i-lizing/)).

<details markdown="1">
<summary>Šta se najviše prodaje</summary>

Zvanična statistika po modelima nije objavljena. U prvoj polovini 2026. registrovano je 535 novih električnih automobila (SAUVD). BYD kao uvoznik navodi da ima polovinu tog segmenta i da je Sealion 7 najprodavaniji model. Više: [statistika](/podaci/statistika-ev-srbija/).

</details>

<details markdown="1">
<summary>Fotografije: autori i licence ({plural(n_foto, 'fotografija', 'fotografije', 'fotografija')})</summary>

Fotografije su sa Wikimedia Commonsa, pod slobodnim licencama; pozadina je uklonjena, a veličina ujednačena. Ilustrativne su: auto na slici može biti druga verzija modela.

<ul>
{credit_li}
</ul>

</details>
"""
OUT.write_text(md, encoding='utf-8')
print('written', OUT.name, n_models, 'models', len(brands_priced), 'brands; cheapest', cheapest[6], cheapest[0], 'under30', under30)
