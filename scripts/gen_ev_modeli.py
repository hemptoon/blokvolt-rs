# -*- coding: utf-8 -*-
"""Generates content/podaci/cene-elektricnih-automobila.md from content/data/ev-modeli.json.
Prices are copied from importers' Serbian sites / price lists (check date in the JSON). Run: python3 scripts/gen_ev_modeli.py"""
import json, re, unicodedata
from ev_rows import DATA, FOTO_ITEMS, SUB, CHECKED, NEXT_CHECK, ROOT, OFFICIAL, eur, rows as _rows

OUT = ROOT / 'content' / 'podaci' / 'cene-elektricnih-automobila.md'
UPDATED = DATA.get('updated', CHECKED)          # last change of any row (a full check is 'checked')
MODIFIED = '-'.join(reversed(UPDATED.split('.')))


def plural(n, one, few, many):
    """Serbian count agreement: 1 slika / 2-4 slike / 5+ slika."""
    last, last2 = n % 10, n % 100
    if last == 1 and last2 != 11:
        return f'{n} {one}'
    if last in (2, 3, 4) and last2 not in (12, 13, 14):
        return f'{n} {few}'
    return f'{n} {many}'


# the rules for every row (names, versions, dates, subsidy arithmetic) live in scripts/ev_rows.py, shared with build.py
rows = [(r['base'], r['model_cell'], r['price_cell'], r['after_cell'], r['src'], r['brand'], r['name'], r['model']) for r in _rows()]
n_models = len(rows)
brands_priced = sorted({r[5] for r in rows})
under30 = sum(1 for r in rows if r[0] < 30000)
cheapest = rows[0]
# the ten cheapest models, for the "najjeftiniji" answer on top of the page (SEO 26.10.2026): name, price, price after the subsidy
_after = lambda cell: re.match(r'[\d.]+ €', cell).group(0)
top10 = '\n'.join(f'{i + 1}. <span translate="no">{r[6]}</span> — {eur(r[0])}, posle subvencije {_after(r[3])}' for i, r in enumerate(rows[:10]))

table = ['| Model | Cena od | Posle subvencije 5.000 € | Izvor |', '|---|---|---|---|']
for base, model_cell, price_cell, after_cell, src, brand, name, model_key in rows:
    table.append(f'| {model_cell} | {price_cell} | {after_cell} | {src} |')

# importers and showroom cities: from content/data/automobili.json (the brand pages, docs/RUNBOOK.md 3.32)
AUTO = json.load(open(ROOT / 'content' / 'data' / 'automobili.json', encoding='utf-8'))
_fold = lambda t: unicodedata.normalize('NFKD', t).encode('ascii', 'ignore').decode().lower()
imp = ['| Marka | Uvoznik | Gradovi sa salonom ili ovlašćenim prodavcem |', '|---|---|---|']
for _b in sorted((x for x in AUTO['brands'] if x['status'] == 'zvanicno' and x.get('ev')), key=lambda x: _fold(x['name'])):
    imp.append(f"| [{_b['name']}](/elektricni-automobili/{_b['slug']}/) | {_b['importer_short']} | "
               f"{', '.join(_b['cities']) if _b.get('cities') else (_b.get('no_cities') or 'lokator na sajtu marke')} |")
AUTO_CHECKED = AUTO['checked']

# models the importer shows without a readable price
_unp = []
for _b in DATA['brands']:
    _names = []
    for _m in _b.get('models', []):
        if (_m.get('price_regular') or _m.get('price_promo')) and _m.get('source_type') in OFFICIAL:
            continue
        _n = re.sub(r'\s*\((?:električn[ia]|putnički kombi, M1)\)$', '', _m['model'])
        _names.append(re.sub(r'\s*\(([^()]+)\)$', r' / \1', _n))
    if _names:
        _unp.append(f"**{_b['brand']}** ({', '.join(_names)})")
UNPRICED = ', '.join(_unp)

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
    'Mercedes-Benz Srbija — cene od, sa PDV-om (24.10.2026) :: https://www.mercedes-benz.rs/',
    'Volvo Car centar Beograd — EX30, subvencija nije uključena u cenu (24.10.2026) :: https://beograd.volvocars.rs/nova_vozila/view/ex30-787',
    'Jeep — brošure i cenovnici (24.10.2026) :: https://www.jeep.rs/jeep-brosure-i-cenovnici',
    'Lexus — cenovnici (24.10.2026) :: https://www.lexus.rs/new-cars/brochures',
    'Lynk & Co Srbija — 02, cena sa uračunatom subvencijom (24.10.2026) :: https://www.lynkco-see.com/rs/vozila/02',
    'Changan Srbija — cenovnik Deepal S05 od 01.10.2026 :: https://changanbalkans.com/rs/wp-content/uploads/2026/09/Deepal-S05-BEV-CENOVNIK-radna-verzija.pdf',
    'China Motor Company — Dongfeng i Forthing, specijalne cene (24.10.2026) :: https://chinamotor.rs/',
    'CUPRA Srbija — Raval (24.10.2026) :: https://www.cupraofficial.rs/raval',
    'Auto Motorevija, 26.07.2026 — prva polovina 2026: 535 novih električnih automobila (SAUVD) :: https://www.automotorevija.rs/rubrike/veliki-rast-prodaje-novih-vozila-u-srbiji',
    'BYD Srbija, 23.07.2026 — podatak uvoznika o najprodavanijim modelima :: https://byd-auto.rs/vesti/byd-u-top-10-brendova-u-srbiji-i-apsolutni-lider-ev-segmenta/',
    'Tesla — prodajni centri, Srbija (lista prazna) :: https://www.tesla.com/findus/list/stores/Serbia',
    'Fotografije modela — Wikimedia Commons, slobodne licence (autori i licence su na stranici) :: https://commons.wikimedia.org/',
]

md = f"""---
thumb: salon-automobila
title: Cene električnih automobila u Srbiji 2026: od {eur(cheapest[0])}
h1: Cene električnih automobila u Srbiji 2026
description: {plural(n_models, 'električni model', 'električna modela', 'električnih modela')} {plural(len(brands_priced), 'marke', 'marke', 'marki')} sa javnom cenom kod uvoznika u Srbiji: od {eur(cheapest[0])} ({cheapest[6]}), {under30} ispod 30.000 €. Cena pre i posle subvencije od 5.000 €.
kicker: Modeli i cene
lead: Najniža cena svakog električnog modela kod zvaničnih uvoznika u Srbiji, pre i posle subvencije od 5.000 €.
updated: {UPDATED}
next_check: {NEXT_CHECK}
published: 2026-09-22
modified: {MODIFIED}
priority: 0.8
sources: {' | '.join(sources)}
---
<div class="sum" markdown="1">
- Najjeftiniji: **{eur(cheapest[0])}** ({cheapest[6]}), posle subvencije **{_after(cheapest[3])}**
- **{n_models}** modela {len(brands_priced)} marki sa javnom cenom, **{under30}** ispod 30.000 €
- Subvencija **5.000 €** za nov automobil, prijava do **1. decembra 2026.** ([uslovi](/podaci/subvencije-2026/))
</div>

## Najjeftiniji električni automobili u Srbiji

Najjeftiniji nov električni automobil kod zvaničnog uvoznika je {cheapest[6]}: {eur(cheapest[0])}, a posle državne subvencije {_after(cheapest[3])}. Deset modela sa najnižom cenom:

{top10}

Cene su najniže koje uvoznici objavljuju, ponegde akcijske. Sve verzije, izvori i datumi provere su u tabeli ispod.

## Modeli i cene

„Cena od“ je najniža cena koju uvoznik objavljuje, po pravilu sa PDV-om. Kad uvoznik objavi cenu već umanjenu za subvenciju, u tabeli je cena pre subvencije, a objavljena cena stoji ispod.

{chr(10).join(table)}

<details markdown="1">
<summary>Modeli bez javne cene</summary>

Cenu na srpskom sajtu nije moguće pročitati za: {UNPRICED}.

Marke bez električnih modela u ponudi, najavljene marke i marke bez uvoznika su na stranici [električni automobili u Srbiji](/elektricni-automobili/). **Tesla** u Srbiji nema zvaničnog uvoznika; automobili stižu uvozom ([Tesla u Srbiji](/elektricni-automobili/tesla/)).

</details>

<details markdown="1">
<summary>Uvoznici i gradovi sa salonima (provereno {AUTO_CHECKED})</summary>

{chr(10).join(imp)}

</details>

## Pre kupovine

- Pitajte da li je cena za auto sa zaliha ili za naručivanje i koliko se čeka isporuka.
- Proverite da li „akcijska cena“ već sadrži subvenciju.
- Subvencija može biti i učešće u lizingu ([krediti i lizing](/podaci/krediti-i-lizing/)).
- Uvoznik, saloni i servis za svaku marku: [električni automobili u Srbiji](/elektricni-automobili/).

<details markdown="1">
<summary>Šta se najviše prodaje</summary>

Zvanična statistika po modelima nije objavljena. Od januara do septembra 2026. registrovano je 1.166 novih električnih automobila (SAUVD). BYD kao uvoznik je u julu naveo da ima polovinu tog segmenta u prvoj polovini godine i da je Sealion 7 najprodavaniji model. Više: [statistika](/podaci/statistika-ev-srbija/).

</details>

<details markdown="1">
<summary>Slike: izvorne fotografije, autori i licence ({plural(n_foto, 'fotografija', 'fotografije', 'fotografija')})</summary>

Slike modela su studijske ilustracije, napravljene alatom veštačke inteligencije prema fotografijama sa Wikimedia Commonsa: za svaki model isti ugao i ista pozadina. Autori i licence izvornih fotografija su navedeni ispod, a ilustracije se dele pod istim licencama. Ilustrativne su: auto na slici može biti druga verzija modela, a sitni detalji mogu odstupati od pravog vozila.

<ul>
{credit_li}
</ul>

</details>
"""
OUT.write_text(md, encoding='utf-8')
print('written', OUT.name, n_models, 'models', len(brands_priced), 'brands; cheapest', cheapest[6], cheapest[0], 'under30', under30)
