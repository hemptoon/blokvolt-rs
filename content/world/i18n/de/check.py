#!/usr/bin/env python3
"""Check of the DE localisation of the world layer (content/world/i18n/de/).

Run from anywhere:  python3 content/world/i18n/de/check.py
Exit code 0 = clean. Babel is optional (falls back to the known CLDR set for DE).
"""
import csv, json, re, sys
from collections import Counter
from pathlib import Path

LANG = 'de'
HERE = Path(__file__).resolve().parent
WORLD = HERE.parent.parent
errs, warns = [], []

PH = re.compile(r'\{[a-zA-Z0-9_]+\}')
TAG = re.compile(r'</?[a-zA-Z][^>]*>')
ENT = re.compile(r'&[a-zA-Z#0-9]+;')
BANNED = re.compile(r'\b(wir|uns|unser\w*|Redaktion|du|dich|dir|dein\w*|rund um die Uhr|sofort|umgehend|Evolako)\b|24/7', re.I)

try:
    from babel import Locale
    CATS = sorted(Locale(LANG).plural_form.tags | {'other'})
except Exception:
    CATS = ['one', 'other']


def strings_of(v):
    if isinstance(v, str):
        yield v
    elif isinstance(v, dict):
        for x in v.values():
            yield from strings_of(x)
    elif isinstance(v, list):
        for x in v:
            yield from strings_of(x)


def ph_ok(en, de):
    """FIXL D14: {name_nom} may stand where EN has {name}; {city_u}/{country_u} where EN has {city}/{country}."""
    a, b = set(PH.findall(en)), set(PH.findall(de))
    alt = {'{name_nom}': '{name}', '{city_u}': '{city}', '{country_u}': '{country}'}
    return a == {alt.get(x, x) for x in b} and not ({x for x in b if x in alt} & a)


def same_text_marks(where, en, de):
    if set(PH.findall(en)) != set(PH.findall(de)) and not ph_ok(en, de):
        errs.append(f'{where}: placeholders {sorted(set(PH.findall(en)))} != {sorted(set(PH.findall(de)))}')
    if Counter(TAG.findall(en)) != Counter(TAG.findall(de)):
        errs.append(f'{where}: HTML tags differ')
    if Counter(ENT.findall(en)) != Counter(ENT.findall(de)):
        errs.append(f'{where}: entities differ')


def banned(where, s):
    m = BANNED.search(s)
    if m and not where.startswith('texts.sources_pages'):  # attributions keep original wording (e.g. French "du")
        errs.append(f'{where}: banned word "{m.group(0)}"')


# 1. strings_*.json
for name in ['strings_map', 'strings_pages', 'strings_shell', 'strings_prices',
             'strings_pay', 'strings_press', 'strings_b2b', 'strings_embed', 'strings_home']:
    src = json.load(open(WORLD / f'{name}.json', encoding='utf-8'))
    try:
        de = json.load(open(HERE / f'{name}.json', encoding='utf-8'))
    except Exception as e:
        errs.append(f'{name}: cannot read ({e})'); continue
    miss = [k for k in src if k not in de]
    extra = [k for k in de if k not in src]
    if miss: errs.append(f'{name}: missing keys {miss[:10]} ({len(miss)})')
    if extra: errs.append(f'{name}: extra keys {extra[:10]}')
    for k, v in src.items():
        if k not in de: continue
        en, d = v['en'], de[k]
        is_pl = k.startswith('pl_') and '|' in en
        if is_pl:
            if not isinstance(d, dict) or sorted(d) != CATS or not all(isinstance(x, str) and x.strip() for x in d.values()):
                errs.append(f'{name}.{k}: plural must be object with categories {CATS}')
            continue
        if not isinstance(d, str) or not d.strip():
            errs.append(f'{name}.{k}: empty or not a string'); continue
        same_text_marks(f'{name}.{k}', en, d)
        banned(f'{name}.{k}', d)
        if en.endswith(' | BlokVolt') and not d.endswith(' | BlokVolt'):
            errs.append(f'{name}.{k}: lost " | BlokVolt"')

# 2. texts.json — same structure as the EN sources
texts = json.load(open(HERE / 'texts.json', encoding='utf-8'))
srcs = {'about_data': json.load(open(WORLD / 'about_data.json', encoding='utf-8'))['en'],
        'download': json.load(open(WORLD / 'download.json', encoding='utf-8'))['en'],
        'sources_pages': json.load(open(WORLD / 'sources_pages.json', encoding='utf-8'))}
DATA_SECTIONS = {'pay': 'pay.json', 'routes': 'routes.json'}  # LANG0 format: node path -> text
if sorted(texts) != sorted(list(srcs) + list(DATA_SECTIONS)):
    errs.append(f'texts.json: top keys {sorted(texts)}')


def ml_nodes(v, p, out):
    """Multilingual nodes ({'en': str, 'sr'/'ru': ...}) of pay.json/routes.json, path like afir.points[0]."""
    if isinstance(v, dict):
        if isinstance(v.get('en'), str) and ('sr' in v or 'ru' in v):
            out[p] = v['en']; return
        for k, x in v.items(): ml_nodes(x, (p + '.' if p else '') + k, out)
    elif isinstance(v, list):
        for i, x in enumerate(v): ml_nodes(x, f'{p}[{i}]', out)


for sec, fn in DATA_SECTIONS.items():
    want = {}
    ml_nodes(json.load(open(WORLD / fn, encoding='utf-8')), '', want)
    got = texts.get(sec, {})
    if not isinstance(got, dict):
        errs.append(f'texts.{sec}: not an object'); continue
    miss = [k for k in want if k not in got]
    extra = [k for k in got if k not in want]
    if miss: errs.append(f'texts.{sec}: missing nodes {miss[:5]} ({len(miss)})')
    if extra: errs.append(f'texts.{sec}: unknown nodes {extra[:5]}')
    for k, en in want.items():
        d = got.get(k)
        if k not in got: continue
        if not isinstance(d, str) or not d.strip():
            errs.append(f'texts.{sec}.{k}: empty or not a string'); continue
        same_text_marks(f'texts.{sec}.{k}', en, d)
        banned(f'texts.{sec}.{k}', d)


def walk(where, en, de):
    if isinstance(en, dict):
        if not isinstance(de, dict) or list(en) != list(de):
            errs.append(f'{where}: keys differ'); return
        for k in en: walk(f'{where}.{k}', en[k], de[k])
    elif isinstance(en, list):
        if not isinstance(de, list) or len(en) != len(de):
            errs.append(f'{where}: list length differs'); return
        for i, (a, b) in enumerate(zip(en, de)): walk(f'{where}[{i}]', a, b)
    elif isinstance(en, str):
        if not isinstance(de, str) or (en.strip() and not de.strip()):
            errs.append(f'{where}: empty or not a string'); return
        same_text_marks(where, en, de)
        banned(where, de)
    elif en != de:
        errs.append(f'{where}: non-text value changed ({en!r} -> {de!r})')


for k in srcs:
    if k in texts: walk(f'texts.{k}', srcs[k], texts[k])

# 3. slugs.json
SLUG_KEYS = ['home', 'map', 'hub', 'net', 'about', 'download', 'gnet', 'prices', 'shell_about', 'sources', 'methodology']
SLUG_EXTRA = ['pay', 'routes', 'press', 'b2b', 'embed', 'map_conf', 'developers']  # FIXL F5: allowed in addition
slugs = json.load(open(HERE / 'slugs.json', encoding='utf-8'))
if [k for k in SLUG_KEYS if k not in slugs] or [k for k in slugs if k not in SLUG_KEYS + SLUG_EXTRA]:
    errs.append(f'slugs.json: keys {sorted(slugs)}')
for k, v in slugs.items():
    if k in ('net', 'about', 'download'):
        if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', v): errs.append(f'slugs.{k}: bad segment {v!r}')
    elif not re.fullmatch(rf'/{LANG}/([a-z0-9]+(-[a-z0-9]+)*/)*', v):
        errs.append(f'slugs.{k}: bad path {v!r}')
paths = [v for k, v in slugs.items() if k not in ('net', 'about', 'download')]
if len(set(paths)) != len(paths): errs.append('slugs.json: duplicate paths')

# 4. countries.csv
src_cc = [r['cc'] for r in csv.DictReader(open(WORLD / 'names/countries.csv', encoding='utf-8'))]
rows = list(csv.DictReader(open(HERE / 'countries.csv', encoding='utf-8')))
if rows and list(rows[0]) not in (['cc', 'name', 'slug', 'in_phrase', 'note'], ['cc', 'name', 'slug', 'in_phrase', 'note', 'name_nom']):
    errs.append('countries.csv: header')
if sorted(r['cc'] for r in rows) != sorted(src_cc): errs.append('countries.csv: country set differs from names/countries.csv')
for r in rows:
    if not (r['name'] and r['in_phrase']) or ('name_nom' in r and not r['name_nom']): errs.append(f'countries {r["cc"]}: empty')
    if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', r['slug']): errs.append(f'countries {r["cc"]}: slug {r["slug"]!r}')
    if not re.match(r'(in|im|auf) ', r['in_phrase']): errs.append(f'countries {r["cc"]}: in_phrase {r["in_phrase"]!r}')
if len({r['slug'] for r in rows}) != len(rows): errs.append('countries.csv: duplicate slugs')

# 5. cities.csv
src_g = {r['geonameid'] for r in csv.DictReader(open(WORLD / 'names/cities.csv', encoding='utf-8'))}
# FIXL: every geonameid must exist in names/cities.csv; every city page must have a row
try:
    _ps = json.load(open(WORLD / 'state/pages_state.json', encoding='utf-8'))
    page_g = {v['key'].split(':')[2] for v in _ps.values() if v.get('type') == 'city'}
except Exception:
    page_g = set()
    warns.append('pages_state.json not readable: city pages not checked')
cr = list(csv.DictReader(open(HERE / 'cities.csv', encoding='utf-8')))
if cr and list(cr[0]) != ['geonameid', 'name', 'in_phrase', 'decl_ok', 'note']: errs.append('cities.csv: header')
unk = [r['geonameid'] for r in cr if r['geonameid'] not in src_g]
nopage = sorted(page_g - {r['geonameid'] for r in cr})
if nopage: errs.append(f'cities.csv: city pages without a German name {nopage[:5]} ({len(nopage)})')
if unk: errs.append(f'cities.csv: unknown geonameid {unk[:5]}')
dup = [g for g, n in Counter(r['geonameid'] for r in cr).items() if n > 1]
if dup: errs.append(f'cities.csv: duplicate geonameid {dup[:5]}')
for r in cr:
    if not r['name'] or not r['in_phrase'] or r['decl_ok'] not in ('0', '1'):
        errs.append(f'cities {r["geonameid"]}: incomplete row')
    if re.search(r'[Ͱ-ϿЀ-ӿ֐-ۿ　-鿿가-힯Ⴀ-ჿ]', r['name']):
        errs.append(f'cities {r["geonameid"]}: non-Latin name {r["name"]}')
if len(src_g - {r['geonameid'] for r in cr}): warns.append(f'cities.csv: {len(src_g - {r["geonameid"] for r in cr})} of {len(src_g)} names/cities.csv rows missing')

print(f'DE check: {len(errs)} errors, {len(warns)} warnings; plural categories {CATS}; cities {len(cr)}/{len(src_g)}; countries {len(rows)}')
for e in errs[:60]: print('ERR ', e)
for w in warns: print('WARN', w)
sys.exit(1 if errs else 0)
