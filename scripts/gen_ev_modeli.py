# -*- coding: utf-8 -*-
"""Generates content/podaci/cene-elektricnih-automobila.md from content/data/ev-modeli.json.
Prices are copied from importers' Serbian sites / price lists (check date in the JSON). Run: python3 scripts/gen_ev_modeli.py"""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = json.load(open(ROOT / 'content' / 'data' / 'ev-modeli.json', encoding='utf-8'))
OUT = ROOT / 'content' / 'podaci' / 'cene-elektricnih-automobila.md'
SUB = 5000
CHECKED = DATA.get('checked', '22.09.2026')

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
            price_cell = f'{eur(base)}<small class="chk">računica: uvoznik objavljuje {eur(after)} sa uračunatom subvencijom</small>'
            after_cell = f'{eur(after)}<small class="chk">cena uvoznika</small>'
        elif brand == 'Ford' and promo and reg and reg - promo == SUB:
            base = reg
            price_cell = f'{eur(reg)}<small class="chk">u cenovniku i „akcijska cena“ {eur(promo)}</small>'
            after_cell = f'{eur(reg - SUB)}<small class="chk">= akcijska cena; cenovnik ne kaže da li je to subvencija</small>'
        elif promo and reg and brand == 'Toyota':
            base = reg
            price_cell = f'{eur(reg)}<small class="chk">u cenovniku i {eur(promo)} — proverite uslove</small>'
            after_cell = eur(reg - SUB)
        elif promo and reg:
            base = promo
            price_cell = f'{eur(promo)}<small class="chk">akcija; redovna {eur(reg)}</small>'
            after_cell = eur(promo - SUB)
        else:
            base = reg or promo
            price_cell = eur(base)
            after_cell = eur(base - SUB)
        if brand == 'Toyota' and model == 'bZ4X':
            price_cell += '<small class="chk">na naslovnoj toyota.rs: 39.990 €</small>'
        vat = m.get('vat') or ''
        kind = 'cenovnik' if m.get('source_type') == 'pricelist_pdf' else 'sajt uvoznika'
        date = DATES.get((brand, model), f'provereno {CHECKED}')
        src = f'[{kind}]({m["url"]})<small class="chk">{date}' + ('; PDV nije naveden' if vat == 'nije navedeno' else '') + '</small>'
        model_cell = name + (f'<small class="chk">{ver}</small>' if ver else '')
        rows.append((base, model_cell, price_cell, after_cell, src, brand, name))

rows.sort(key=lambda r: (r[0], r[6]))
n_models = len(rows)
brands_priced = sorted({r[5] for r in rows})
under30 = sum(1 for r in rows if r[0] < 30000)
cheapest = rows[0]

table = ['| Model | Cena od | Posle subvencije 5.000 € | Izvor |', '|---|---|---|---|']
for base, model_cell, price_cell, after_cell, src, brand, name in rows:
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
]

md = f"""---
title: Cene električnih automobila u Srbiji 2026 — svi modeli kod uvoznika
description: Početne cene {n_models} električnih modela {len(brands_priced)} marki, prepisane sa sajtova i cenovnika zvaničnih uvoznika — od {eur(cheapest[0])} (Dacia Spring), {under30} modela ispod 30.000 €. Cena posle subvencije od 5.000 €, uvoznici i gradovi sa salonima. Stanje {CHECKED}.
kicker: Podaci · modeli i cene
lead: Koliko košta nov električni automobil u Srbiji: najniža javno objavljena cena svakog modela, računica posle državne subvencije i gde se kupuje. Samo cene koje uvoznik objavljuje, sa linkom i datumom.
updated: {CHECKED}
next_check: 15.11.2026
published: 2026-09-22
modified: 2026-09-22
priority: 0.8
disclaimer: Cene su informativne — važi ponuda prodavca na dan kupovine, a subvencija zavisi od raspoloživog budžeta. Tekst je pripremljen uz pomoć AI alata; cene je redakcija BlokVolta prepisala sa sajtova i cenovnika uvoznika {CHECKED}. Grešku ili novu cenu prijavite na
sources: {' | '.join(sources)}
---
<div class="bva-stats">
<div class="bva-stat"><b>{eur(cheapest[0])}</b><span>najniža objavljena cena novog električnog automobila (Dacia Spring, cenovnik od 01.09.2026) — {eur(cheapest[0] - SUB)} posle subvencije</span></div>
<div class="bva-stat"><b>{n_models}</b><span>modela {len(brands_priced)} marki sa javnom cenom; {under30} ispod 30.000 € pre subvencije</span></div>
<div class="bva-stat"><b>5.000 €</b><span>državna subvencija za nov električni automobil, zahtevi preko eUprave do 01.12.2026 — dok ima novca u budžetu</span></div>
</div>

## Kako čitati tabelu

„Cena od“ je najniža cena modela koju uvoznik objavljuje na svom sajtu ili u cenovniku, uglavnom sa PDV-om (gde stranica PDV ne pominje, to piše uz izvor). Ako uvoznik prikazuje cenu već umanjenu za subvenciju — kao Kia za EV3 i Niro EV i JMEV za Elight — vratili smo 5.000 € da bi cene bile uporedive, a objavljenu cenu naveli smo ispod. „Posle subvencije“ je naša računica: cena od minus 5.000 €. Subvencija važi samo za nov automobil, a budžet za 2026. je ograničen — uslovi i stanje su na stranici [subvencije 2026](/podaci/subvencije-2026/).

Tabela je poređana po ceni pre subvencije. Ne ocenjujemo modele; domet i opremu proverite u konfiguratoru uvoznika.

## Modeli i cene

{chr(10).join(table)}

## Modeli bez javne cene

Na srpskim sajtovima ovih marki električni modeli postoje, ali cenu nismo mogli da pročitamo — ili je nema, ili se učitava samo u konfiguratoru: **Audi** (Q4 e-tron, Q6 e-tron, A6 e-tron, e-tron GT), **Kia** (EV2, EV4, EV6, EV9 — cenovnici u PDF-u nisu javno dostupni), **Opel** (Astra, Frontera i Grandland Electric), **MG** (MG4, MG5, MGS5 EV), **Geely** (E5), **Volvo** (EX30, EX60, EX90), **Mazda** (6e, CX-6e), **Ford** Mustang Mach-E i **Leapmotor** (T03, B10, C10; na sajmu u martu 2026. T03 je prikazan po ceni od 17.490 € sa popustom, prema medijima — aktuelnost nismo potvrdili).

Cupra Tavascan na srpskom sajtu „čeka homologaciju“, a Nissan trenutno ne prikazuje nijedan električni model. Za Suzuki (e Vitara) i Porsche (Taycan, Macan Electric) sajtovi na dan provere nisu bili dostupni. Za Changan/Deepal, Dongfeng, Voyah, BAIC, GWM, Chery/Omoda, Xpeng, Zeekr, Polestar i Smart nismo našli zvaničan srpski sajt sa električnim modelom i cenom — neki se prodaju preko pojedinačnih prodavaca.

**Tesla** u Srbiji nema zvaničnog uvoznika ni prodajni centar; automobili stižu individualnim uvozom (vidi [uvoz i carina](/podaci/uvoz-i-carina/)), a servis rade nezavisne radionice (vidi [servisi](/podaci/servisi-za-elektricne-automobile/)).

## Uvoznici i saloni

{chr(10).join(imp)}

Gradove smo prepisali sa lokatora prodavaca na sajtovima marki; spisak ovlašćenih servisa je na stranici [servisi za električne automobile](/podaci/servisi-za-elektricne-automobile/).

## Šta se najviše prodaje

Zvanična statistika po modelima za električne automobile nije javno objavljena. Po podacima SAUVD-a, u prvoj polovini 2026. u Srbiji je prvi put registrovano 535 novih električnih automobila (Auto Motorevija, 26.07.2026) — vidi [statistiku](/podaci/statistika-ev-srbija/). BYD kao uvoznik navodi da ima polovinu tog segmenta i da je Sealion 7 najprodavaniji električni model (podatak uvoznika, 23.07.2026).

## Pre kupovine proverite

Da li je cena „sa zaliha“ ili za naručivanje (Dacia Spring po najnižoj ceni je, prema cenovniku, samo iz zaliha), da li „akcijska cena“ već sadrži subvenciju, šta je uključeno (priprema vozila, registracija, kabl za punjenje) i koliko se čeka isporuka. Subvencija se može iskoristiti i kao učešće u finansijskom lizingu — vidi [krediti i lizing](/podaci/krediti-i-lizing/). Posle kupovine: [registracija i porezi](/podaci/registracija-i-porezi/) (porez na upotrebu se ne plaća) i [osiguranje](/podaci/osiguranje-elektricnog-automobila/).

## Povezano

- [Subvencije 2026](/podaci/subvencije-2026/) — iznos, uslovi, rok 01.12.2026.
- [Punjač kod kuće](/firme/) — ko prodaje i ugrađuje kućne punjače, po istim kolonama.
- [Iznajmljivanje električnog automobila](/podaci/rent-a-car-i-car-sharing/) — ako želite da ga probate pre kupovine.
"""
OUT.write_text(md, encoding='utf-8')
print('written', OUT.name, n_models, 'models', len(brands_priced), 'brands; cheapest', cheapest[6], cheapest[0], 'under30', under30)
