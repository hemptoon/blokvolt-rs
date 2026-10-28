# -*- coding: utf-8 -*-
"""Rows of the new-EV price table, from content/data/ev-modeli.json — the rules live here once and are used by
scripts/gen_ev_modeli.py (the page /podaci/cene-elektricnih-automobila/) and build.py (the brand pages under
/elektricni-automobili/, docs/RUNBOOK.md 3.32). Prices are copied from the importers' Serbian sites and price lists."""
import json, re, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = json.load(open(ROOT / 'content' / 'data' / 'ev-modeli.json', encoding='utf-8'))
FOTO = json.load(open(ROOT / 'content' / 'data' / 'ev-foto.json', encoding='utf-8'))
FOTO_ITEMS = FOTO['items']
SUB = DATA.get('subsidy_eur', 5000)
CHECKED = DATA.get('checked', '22.09.2026')
NEXT_CHECK = DATA.get('next_check', '15.11.2026')
# the brand pages' slugs (content/data/automobili.json, field `ev` = the brand name in ev-modeli.json): a priced model has
# its own page at /elektricni-automobili/<brand slug>/<model slug>/ (docs/RUNBOOK.md 3.32, model pages since 29.10.2026)
_AUTO = json.load(open(ROOT / 'content' / 'data' / 'automobili.json', encoding='utf-8'))
BRAND_SLUG = {b['ev']: b['slug'] for b in _AUTO['brands'] if b.get('ev')}
# a model slug is made from the JSON model name; these are written by hand (the name is long or not the one people use)
SLUG = {('Mercedes-Benz', 'Električna G-Klasa (G 580 sa EQ tehnologijom)'): 'g-580',
        ('MINI', 'Countryman (električni)'): 'countryman-e'}


def model_slug(brand, model):
    """'Grande Panda (električni)' → grande-panda, 'Twingo E-Tech electric' → twingo-e-tech, 'C-HR+' → c-hr-plus, 'ë-C3' → e-c3.
    The slug is part of a public address: once published, change it only with a redirect in _redirects."""
    if (brand, model) in SLUG:
        return SLUG[(brand, model)]
    m = re.sub(r'\s*\([^()]*\)\s*$', '', model)
    m = re.sub(r'\s+electric$', '', m, flags=re.I)
    m = unicodedata.normalize('NFKD', m.replace('+', ' plus ')).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', m).strip('-')


def model_page(brand, model):
    return f'/elektricni-automobili/{BRAND_SLUG[brand]}/{model_slug(brand, model)}/' if brand in BRAND_SLUG else None


# The charging data of a model page come from content/data/ev-specs.json (the map's „Moj auto“) only where the entry is the
# version whose price is shown — the same battery and on-board charger (checked by hand, 29.10.2026). Rows without an entry
# here show the importer's figures only. A field listed in the entry's "est" is an estimate: never shown as a fact
# (consumption is always an estimate and is shown as one, for the cost of 100 km). SPEC_HIDE: what the entry has but the
# priced version may not (optional equipment).
SPEC = {
    ('JMEV', 'EV3'): ('JMEV', 'EV3 (30.24 kWh LFP)'),
    ('Leapmotor', 'T03'): ('Leapmotor', 'T03'),
    ('Renault', 'Twingo E-Tech electric'): ('Renault', 'Twingo E-Tech electric 27.5 kWh (Evolution 82 KS)'),
    ('Dongfeng', 'Box'): ('Dongfeng', 'Box 42.3 kWh LFP'),
    ('Fiat', 'Grande Panda (električni)'): ('Fiat', 'Grande Panda Electric 44 kWh LFP (built in Kragujevac)'),
    ('JAC', 'E30X'): ('JAC', 'E30X Luxury (41 kWh)'),
    ('Volkswagen', 'ID. Polo'): ('Volkswagen', 'ID. Polo 37 kWh LFP'),
    ('Citroën', 'ë-C3'): ('Citroën', 'ë-C3 44 kWh'),
    ('Citroën', 'ë-C3 Aircross'): ('Citroën', 'ë-C3 Aircross 44 kWh'),
    ('Renault', 'Renault 5 E-Tech electric'): ('Renault', '5 E-Tech 40 kWh'),
    ('Renault', 'Renault 4 E-Tech electric'): ('Renault', '4 E-Tech electric 40 kWh (Evolution 120 KS)'),
    ('Lynk & Co', '02'): ('Lynk & Co', '02 66 kWh LFP'),
    ('BYD', 'Atto 2'): ('BYD', 'Atto 2 Comfort 64.8 kWh'),
    ('Changan', 'Deepal S05'): ('Changan', 'Deepal S05 RWD Pro (68.8 kWh LFP)'),
    ('Jeep', 'Avenger Electric'): ('Jeep', 'Avenger Electric 54 kWh'),
    ('Ford', 'Puma Gen-E'): ('Ford', 'Puma Gen-E (43 kWh)'),
    ('Volvo', 'EX30'): ('Volvo', 'EX30 Extended Range / Twin Performance (64 kWh)'),
    ('Volvo', 'EX30 Cross Country'): ('Volvo', 'EX30 Extended Range / Twin Performance (64 kWh)'),
    ('Kia', 'Niro EV'): ('Kia', 'Niro EV 64.8 kWh (2nd gen)'),
    ('BYD', 'Atto 3 Evo'): ('BYD', 'Atto 3 EVO (74.8 kWh)'),
    ('Fiat', '600e'): ('Fiat', '600e 54 kWh (RED)'),
    ('MINI', 'Cooper E (električni)'): ('Mini', 'Cooper E 40.7 kWh (J01)'),
    ('Peugeot', 'E-208'): ('Peugeot', 'e-208 50 kWh (136 hp)'),
    ('Toyota', 'C-HR+'): ('Toyota', 'C-HR+ 57.7 kWh FWD'),
    ('MINI', 'Aceman'): ('Mini', 'Aceman 42.5 kWh (E, 184 hp)'),
    ('BYD', 'Seal'): ('BYD', 'Seal 82.5 kWh (RWD Design / AWD Excellence)'),
    ('Toyota', 'bZ4X'): ('Toyota', 'bZ4X 57.7 kWh FWD'),
    ('Škoda', 'Elroq'): ('Skoda', 'Elroq 60'),
    ('Kia', 'EV3'): ('Kia', 'EV3 Standard 58.3 kWh'),
    ('Toyota', 'Proace City Verso Electric (putnički kombi, M1)'): ('Toyota', 'Proace City Verso Electric 50 kWh'),
    ('Ford', 'Explorer EV'): ('Ford', 'Explorer EV Standard Range RWD (58 kWh LFP)'),
    ('BYD', 'Sealion 7'): ('BYD', 'Sealion 7 82.5 kWh (Design RWD)'),
    ('Ford', 'Capri'): ('Ford', 'Capri Standard Range RWD (58 kWh LFP)'),
    ('Jeep', 'Compass Electric'): ('Jeep', 'Compass Electric 73 kWh (FWD)'),
    ('MINI', 'Countryman (električni)'): ('Mini', 'Countryman E 66.5 kWh (204 hp)'),
    ('Mercedes-Benz', 'EQB'): ('Mercedes-Benz', 'EQB 250+ 70.5 kWh'),
    ('Peugeot', 'E-3008'): ('Peugeot', 'E-3008 73 kWh (Allure 210 KS)'),
    ('BMW', 'iX1'): ('BMW', 'iX1 eDrive20 / xDrive30'),
    ('Peugeot', 'E-5008'): ('Peugeot', 'E-5008 73 kWh (Allure 210 KS)'),
    ('BMW', 'iX2'): ('BMW', 'iX2 eDrive20 64.8 kWh'),
    ('Volvo', 'EX60'): ('Volvo', 'EX60 P6 RWD 83 kWh'),
    ('Lexus', 'RZ'): ('Lexus', 'RZ 350e 77 kWh (MY26)'),
    ('Volvo', 'ES90'): ('Volvo', 'ES90 Single Motor 88 kWh'),
    ('Lexus', 'ES (električni)'): ('Lexus', 'ES 350e 77 kWh'),
    ('Mercedes-Benz', 'EQE limuzina'): ('Mercedes-Benz', 'EQE 300 / 350+ 89 kWh'),
    ('BMW', 'i5'): ('BMW', 'i5 eDrive40 81.2 kWh'),
    ('BMW', 'i5 Touring'): ('BMW', 'i5 eDrive40 Touring 81.2 kWh'),
    ('Hyundai', 'IONIQ 9'): ('Hyundai', 'IONIQ 9 110.3 kWh AWD'),
    ('BMW', 'iX'): ('BMW', 'iX xDrive45 94.8 kWh'),
    ('Mercedes-Benz', 'EQS limuzina'): ('Mercedes-Benz', 'EQS 450+ 118 kWh'),
    ('Mercedes-Benz', 'EQS SUV'): ('Mercedes-Benz', 'EQS SUV 450 4MATIC (118 kWh)'),
    ('BMW', 'i7'): ('BMW', 'i7 eDrive50 101.7 kWh'),
    ('Mercedes-Benz', 'Električna G-Klasa (G 580 sa EQ tehnologijom)'): ('Mercedes-Benz', 'G 580 with EQ Technology (116 kWh)'),
    ('Mercedes-Benz', 'Mercedes-Maybach EQS SUV'): ('Mercedes-Benz', 'Mercedes-Maybach EQS 680 SUV (118 kWh)'),
}
# Twingo: 50 kW DC (and 11 kW AC) only with the optional Advanced Charge Pack (ev-specs.json note)
SPEC_HIDE = {('Renault', 'Twingo E-Tech electric'): {'dc'}}


# official sources of a price: the importer's site, its price list, or the site of an authorised dealer when the importer
# publishes no price (Volvo Car centar Beograd, AK Kompresor for Leapmotor)
OFFICIAL = ('official', 'pricelist_pdf', 'official_retailer')
KIND = {'pricelist_pdf': 'cenovnik', 'official_retailer': 'sajt prodavca'}


def thumb(brand, model, name):
    """Studio illustration made from a Wikimedia Commons photo (credited), if we have one for this model."""
    f = FOTO_ITEMS.get(f'{brand}||{model}')
    if not f:
        # same footprint as a photo, so every name in the column starts at the same place
        return '<span class="evm-i evm-none" aria-hidden="true"></span>'
    return (f'<img class="evm-i" src="/assets/auto/{f["slug"]}.{FOTO.get("ext", "png")}?v={f["v"]}" alt="" width="{FOTO["w"]}" '
            f'height="{FOTO["h"]}" loading="lazy" decoding="async">')


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
    ('Changan', 'Deepal S05'): 'Deepal S05', ('Changan', 'Deepal S07'): 'Deepal S07',
    ('Dongfeng', 'Forthing S7 EV'): 'Forthing S7 EV', ('Dongfeng', 'Forthing Friday'): 'Forthing Friday',
    ('Dongfeng', 'M-Hero 917'): 'M-Hero 917',
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
# price list dates we could read (otherwise: the day the row was seen, 'seen' in the JSON)
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
    ('Toyota', 'bZ4X'): 'cenovnik 01.10.2026', ('Jeep', 'Avenger Electric'): 'cenovnik 01.08.2026',
    ('Jeep', 'Compass Electric'): 'cenovnik 01.10.2026', ('Lexus', 'RZ'): 'cenovnik 01.09.2026',
    ('Lexus', 'ES (električni)'): 'cenovnik 01.09.2026', ('Changan', 'Deepal S05'): 'cenovnik 01.10.2026',
}
for _m in ('iX1', 'iX2', 'i4', 'iX3 (Neue Klasse)', 'i5', 'i5 Touring', 'iX', 'i7'):
    DATES[('BMW', _m)] = 'cenovnik 01.07.2026'
for _m in ('Cooper E (električni)', 'Aceman', 'Countryman (električni)'):
    DATES[('MINI', _m)] = 'cenovnik 01.06.2026'


def display_name(brand, model):
    return NAME.get((brand, model)) or (model if model.lower().startswith(brand.lower()) else f'{brand} {model}')


def rows():
    """Every model with a public price from an official source, cheapest first. Each row is a dict:
    base (EUR before the subsidy), model_cell, price_cell, after_cell, src (Markdown link + <small> date), brand, name,
    model (the JSON key), ver, url, kind ('cenovnik' | 'sajt uvoznika'), date, foto (ev-foto.json entry or None)."""
    out = []
    for b in DATA['brands']:
        brand = b['brand']
        for m in b.get('models', []):
            if m.get('source_type') not in OFFICIAL:
                continue
            reg, promo = m.get('price_regular'), m.get('price_promo')
            if not reg and not promo:
                continue
            model = m['model']
            name = display_name(brand, model)
            ver = VERSION_BM.get((brand, model), VERSION.get(model, m.get('version') or ''))
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
            vat = m.get('vat') or ''
            kind = KIND.get(m.get('source_type'), 'sajt uvoznika')
            date = DATES.get((brand, model), f'provereno {m.get("seen") or CHECKED}')
            src = f'[{kind}]({m["url"]})<small>{date}' + ('; PDV nije naveden' if vat == 'nije navedeno' else '') + '</small>'
            page = model_page(brand, model)
            # the model's own page is linked from the whole cell (photo and name), so the cell's text stays the same
            # translation unit as before (docs/RUNBOOK.md 3.9)
            tag = f'a class="evm" href="{page}"' if page else 'span class="evm"'
            model_cell = (f'<{tag}>' + thumb(brand, model, name) + '<span class="evm-t">' + name
                          + (f'<small>{ver}</small>' if ver else '') + '</span></' + tag.split()[0] + '>')
            out.append({'base': base, 'model_cell': model_cell, 'price_cell': price_cell, 'after_cell': after_cell, 'src': src,
                        'brand': brand, 'name': name, 'model': model, 'ver': ver, 'url': m['url'], 'kind': kind, 'date': date,
                        'vat_unknown': vat == 'nije navedeno', 'vat': vat, 'foto': FOTO_ITEMS.get(f'{brand}||{model}'),
                        'page': page, 'slug': model_slug(brand, model), 'seen': m.get('seen') or CHECKED,
                        'battery_kwh': m.get('battery_kwh'), 'range_wltp_km': m.get('range_wltp_km'),
                        'computed_base': m.get('price_includes_subsidy') is True})
    out.sort(key=lambda r: (r['base'], r['name']))
    return out


def unpriced(brand):
    """Models of a brand that the importer shows without a readable price: [{name, model, ver, url, seen, note}]."""
    for b in DATA['brands']:
        if b['brand'] != brand:
            continue
        res = []
        for m in b.get('models', []):
            if m.get('price_regular') or m.get('price_promo'):
                if m.get('source_type') in OFFICIAL:
                    continue
            res.append({'name': display_name(brand, m['model']), 'model': m['model'], 'url': m.get('url') or '',
                        'seen': m.get('seen') or CHECKED, 'media': m.get('source_type') == 'media',
                        'media_price': (m.get('price_promo') or m.get('price_regular')) if m.get('source_type') == 'media' else None,
                        'foto': FOTO_ITEMS.get(f'{brand}||{m["model"]}')})
        return res
    return []
