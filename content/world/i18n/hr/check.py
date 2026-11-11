#!/usr/bin/env python3
"""Check content/world/i18n/hr/ against the EN sources (L-HR contract, pool 3 README §3 L)."""
import csv, json, re, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
WORLD = HERE.parent.parent
LANG = HERE.name
err = []
PH = re.compile(r'\{[^{}]*\}')
TAG = re.compile(r'<[^>]+>|&[a-z#0-9]+;')

def cats():
    try:
        from babel import Locale
        return set(Locale(LANG).plural_form.tags) | {'other'}
    except Exception:
        return {'one', 'few', 'other'}   # CLDR hr
CATS = cats()

def same(a, b, where):
    for rx, what in ((PH, 'placeholders'), (TAG, 'tags/entities')):
        # pool 4: {city_u}/{country_u} may replace {city}/{country}; FIXL D14: {name_nom} may replace {name}
        norm = (lambda xs: sorted(x.replace('_u}', '}').replace('{name_nom}', '{name}') for x in xs)) if rx is PH else sorted
        if norm(rx.findall(a)) != norm(rx.findall(b)):
            err.append(f'{where}: {what} differ: EN {sorted(rx.findall(a))} vs {sorted(rx.findall(b))}')

STRINGS = ('strings_map', 'strings_pages', 'strings_shell', 'strings_prices',
           'strings_pay', 'strings_press', 'strings_b2b', 'strings_embed', 'strings_home')   # L2: all 8 files; FIXL: + home
for f in STRINGS:
    en = {k: v['en'] for k, v in json.load(open(WORLD / f'{f}.json')).items()}
    tr = json.load(open(HERE / f'{f}.json'))
    for k in en.keys() - tr.keys(): err.append(f'{f}: missing key {k}')
    for k in tr.keys() - en.keys(): err.append(f'{f}: extra key {k}')
    for k, e in en.items():
        t = tr.get(k)
        if t is None: continue
        if k.startswith('pl_'):
            if not isinstance(t, dict) or set(t) != CATS: err.append(f'{f}.{k}: plural categories {t if not isinstance(t, dict) else sorted(t)} != {sorted(CATS)}')
            elif any(not str(v).strip() for v in t.values()): err.append(f'{f}.{k}: empty plural form')
            continue
        if not isinstance(t, str) or not t.strip(): err.append(f'{f}.{k}: empty or not a string'); continue
        same(e, t, f'{f}.{k}')
        if e.endswith(' | BlokVolt') and not t.endswith(' | BlokVolt'): err.append(f'{f}.{k}: lost " | BlokVolt"')

def walk(a, b, where):
    if isinstance(a, dict):
        if not isinstance(b, dict) or set(a) != set(b): err.append(f'{where}: keys differ'); return
        for k in a: walk(a[k], b[k], f'{where}.{k}')
    elif isinstance(a, list):
        if not isinstance(b, list) or len(a) != len(b): err.append(f'{where}: list length differs'); return
        for i, (x, y) in enumerate(zip(a, b)): walk(x, y, f'{where}[{i}]')
    elif isinstance(a, str):
        if not isinstance(b, str) or (a.strip() and not b.strip()): err.append(f'{where}: empty/not a string'); return
        same(a, b, where)
texts = json.load(open(HERE / 'texts.json'))
for f in ('about_data', 'download'):
    walk(json.load(open(WORLD / f'{f}.json'))['en'], texts.get(f), f'texts.{f}')

# L2 / LANG0: texts.json "pay" and "routes" = {path of a multilingual node in pay.json / routes.json: text}
def nodes(o, p, out):
    if isinstance(o, dict):
        if isinstance(o.get('en'), str) and ('sr' in o or 'ru' in o):
            out[p] = o['en']; return
        for k, v in o.items(): nodes(v, (p + '.' if p else '') + k, out)
    elif isinstance(o, list):
        for i, v in enumerate(o): nodes(v, f'{p}[{i}]', out)
for f in ('pay', 'routes'):
    en = {}; nodes(json.load(open(WORLD / f'{f}.json')), '', en)
    tr = texts.get(f)
    if not isinstance(tr, dict): err.append(f'texts.{f}: missing section'); continue
    for k in en.keys() - tr.keys(): err.append(f'texts.{f}: missing node {k}')
    for k in tr.keys() - en.keys(): err.append(f'texts.{f}: extra node {k}')
    for k, e in en.items():
        t = tr.get(k)
        if t is None: continue
        if not isinstance(t, str) or not t.strip(): err.append(f'texts.{f}.{k}: empty or not a string'); continue
        same(e, t, f'texts.{f}.{k}')

SLUG = re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*$')
s = json.load(open(HERE / 'slugs.json'))
need = {'home', 'map', 'hub', 'net', 'about', 'download', 'gnet', 'prices', 'shell_about', 'sources', 'methodology'}
extra = {'pay', 'routes', 'press', 'b2b', 'embed', 'map_conf', 'developers'}   # FIXL F5: optional section paths
if not need <= set(s) <= need | extra: err.append(f'slugs: keys {sorted(set(s) ^ need)}')
for k, v in s.items():
    if k in ('net', 'about', 'download'):
        if not SLUG.match(v): err.append(f'slugs.{k}: not one ASCII segment: {v}')
    else:
        segs = v.strip('/').split('/')
        if not (v.startswith(f'/{LANG}/') and v.endswith('/') and segs[0] == LANG and all(SLUG.match(x) for x in segs)):
            err.append(f'slugs.{k}: bad path {v}')
paths = [v for k, v in s.items() if k not in ('net', 'about', 'download')]
if len(paths) != len(set(paths)): err.append('slugs: duplicate paths')

src_cc = [r['cc'] for r in csv.DictReader(open(WORLD / 'names' / 'countries.csv'))]
cc = list(csv.DictReader(open(HERE / 'countries.csv')))
if cc and list(cc[0].keys()) not in (['cc', 'name', 'slug', 'in_phrase', 'note'], ['cc', 'name', 'slug', 'in_phrase', 'note', 'name_nom']):
    err.append(f'countries.csv: columns {list(cc[0].keys())}')   # FIXL D4: an extra last column name_nom is allowed
if [r['cc'] for r in cc] != src_cc: err.append('countries.csv: cc list/order differs from names/countries.csv')
for r in cc:
    if not all(r[c].strip() for c in ('name', 'slug', 'in_phrase')): err.append(f'countries {r["cc"]}: empty field')
    if not SLUG.match(r['slug']): err.append(f'countries {r["cc"]}: bad slug {r["slug"]}')
    if not r['in_phrase'].startswith(('u ', 'na ')): err.append(f'countries {r["cc"]}: in_phrase {r["in_phrase"]}')
if len({r['slug'] for r in cc}) != len(cc): err.append('countries: duplicate slugs')

src_g = {r['geonameid'] for r in csv.DictReader(open(WORLD / 'names' / 'cities.csv'))}
ci = list(csv.DictReader(open(HERE / 'cities.csv')))
g = [r['geonameid'] for r in ci]
if len(g) != len(set(g)): err.append('cities.csv: duplicate geonameid')
_ex = WORLD / 'names' / 'cities_extra.csv'   # FIXL2: geonameids may also come from names/cities_extra.csv
ext_g = {r['geonameid'] for r in csv.DictReader(open(_ex, encoding='utf-8'))} if _ex.exists() else set()
if set(g) - src_g - ext_g: err.append(f'cities.csv: {len(set(g) - src_g - ext_g)} unknown geonameid')
# FIXL: every city page of pages_state must have a row
_ps = WORLD / 'state' / 'pages_state.json'
if _ps.exists():
    _pages = {str(v.get('key', '')).split(':')[-1] for v in json.load(open(_ps)).values()
              if v.get('type') == 'city' and str(v.get('key', '')).startswith('t:')}
    for x in sorted(_pages - set(g)): err.append(f'cities.csv: city with a page missing: {x}')
for r in ci:
    if not r['name'].strip() or not r['in_phrase'].strip() or r['decl_ok'] not in ('0', '1'): err.append(f'cities {r["geonameid"]}: bad row')

print(f'{LANG}: strings, texts, slugs, {len(cc)} countries, {len(ci)}/{len(src_g | ext_g)} cities checked')
for e in err: print('ERR', e)
print('OK' if not err else f'{len(err)} errors')
sys.exit(1 if err else 0)
