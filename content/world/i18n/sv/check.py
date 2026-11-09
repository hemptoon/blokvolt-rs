#!/usr/bin/env python3
"""L-SV check: content/world/i18n/sv vs EN sources. Run from repo root or anywhere: python3 content/world/i18n/sv/check.py"""
import csv, json, re, sys
from pathlib import Path
from babel import Locale

HERE = Path(__file__).resolve().parent
WORLD = HERE.parent.parent
LANG = HERE.name
CATS = set(Locale.parse(LANG).plural_form.tags) | {'other'}
PH = re.compile(r'\{[^{}]*\}')
TAG = re.compile(r'</?[a-zA-Z][^>]*>|&[a-z]+;|&#\d+;')
err = []

def sig(s):
    return sorted(PH.findall(s)), sorted(TAG.findall(s))

for name in ['strings_map', 'strings_pages', 'strings_shell', 'strings_prices']:
    en = json.load(open(WORLD / f'{name}.json', encoding='utf-8'))
    tr = json.load(open(HERE / f'{name}.json', encoding='utf-8'))
    for k in en:
        if k not in tr:
            err.append(f'{name}: missing {k}'); continue
        e, t = en[k]['en'], tr[k]
        if k.startswith('pl_'):  # plural forms "one|few|many" in EN
            if not isinstance(t, dict):
                err.append(f'{name}.{k}: plural must be an object'); continue
            if set(t) != CATS:
                err.append(f'{name}.{k}: plural categories {sorted(t)} != CLDR {sorted(CATS)}')
            if any(not str(v).strip() for v in t.values()):
                err.append(f'{name}.{k}: empty plural form')
            continue
        if not isinstance(t, str) or not t.strip():
            err.append(f'{name}.{k}: empty'); continue
        if sig(e) != sig(t):
            err.append(f'{name}.{k}: placeholders/tags differ {sig(e)} vs {sig(t)}')
    for k in tr:
        if k not in en:
            err.append(f'{name}: extra key {k}')

# texts.json
tx = json.load(open(HERE / 'texts.json', encoding='utf-8'))
src = {'about_data': json.load(open(WORLD / 'about_data.json', encoding='utf-8'))['en'],
       'download': json.load(open(WORLD / 'download.json', encoding='utf-8'))['en']}
# sources_pages.json is shared by all languages and not translated (pool 3 clarification 23:55)

def walk(a, b, p):
    if isinstance(a, dict):
        if not isinstance(b, dict) or set(a) != set(b):
            err.append(f'texts {p}: keys differ'); return
        for k in a: walk(a[k], b[k], f'{p}.{k}')
    elif isinstance(a, list):
        if not isinstance(b, list) or len(a) != len(b):
            err.append(f'texts {p}: list length differs'); return
        for i, (x, y) in enumerate(zip(a, b)): walk(x, y, f'{p}[{i}]')
    elif isinstance(a, str):
        if not isinstance(b, str) or not b.strip():
            err.append(f'texts {p}: empty')
        elif sig(a) != sig(b):
            err.append(f'texts {p}: placeholders differ')
    elif a != b:
        err.append(f'texts {p}: non-text value changed')

if set(tx) != set(src):
    err.append(f'texts.json keys {sorted(tx)}')
for k in src:
    if k in tx: walk(src[k], tx[k], k)

# slugs
SK = ['home', 'map', 'hub', 'net', 'about', 'download', 'gnet', 'prices', 'shell_about', 'sources', 'methodology']
sl = json.load(open(HERE / 'slugs.json', encoding='utf-8'))
if list(sl) != SK and set(sl) != set(SK):
    err.append(f'slugs.json keys {sorted(sl)}')
for k, v in sl.items():
    if k in ('net', 'about', 'download'):
        if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', v): err.append(f'slug {k}={v!r} not a single ASCII segment')
    else:
        if not re.fullmatch(rf'/{LANG}/([a-z0-9]+(-[a-z0-9]+)*/)*', v): err.append(f'slug {k}={v!r} not a /{LANG}/ path')
paths = [v for k, v in sl.items() if k not in ('net', 'about', 'download')]
if len(set(paths)) != len(paths): err.append('slugs: duplicate paths')

# countries
cn = {r['cc']: r for r in csv.DictReader(open(WORLD / 'names' / 'countries.csv', encoding='utf-8'))}
cs = list(csv.DictReader(open(HERE / 'countries.csv', encoding='utf-8')))
if [*cs[0].keys()] != ['cc', 'name', 'slug', 'in_phrase', 'note']: err.append('countries.csv header')
if {r['cc'] for r in cs} != set(cn) or len(cs) != len(cn): err.append(f'countries.csv: {len(cs)} rows vs {len(cn)}')
slugs = [r['slug'] for r in cs]
if len(set(slugs)) != len(slugs): err.append('countries.csv: duplicate slugs')
for r in cs:
    if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', r['slug']): err.append(f"country slug {r['slug']!r}")
    if not r['name'].strip() or not r['in_phrase'].strip(): err.append(f"country {r['cc']}: empty")
    if r['name'] not in r['in_phrase']: err.append(f"country {r['cc']}: in_phrase without name")

# cities
ci = {r['geonameid'] for r in csv.DictReader(open(WORLD / 'names' / 'cities.csv', encoding='utf-8'))}
cc = list(csv.DictReader(open(HERE / 'cities.csv', encoding='utf-8')))
if [*cc[0].keys()] != ['geonameid', 'name', 'in_phrase', 'decl_ok', 'note']: err.append('cities.csv header')
ids = [r['geonameid'] for r in cc]
if len(set(ids)) != len(ids): err.append('cities.csv: duplicate geonameid')
if set(ids) - ci: err.append(f'cities.csv: unknown geonameid {sorted(set(ids) - ci)[:5]}')
for r in cc:
    if not r['name'].strip() or not r['in_phrase'].strip() or r['decl_ok'] not in ('0', '1'):
        err.append(f"city {r['geonameid']}: bad row")

print(f'{LANG}: plural categories {sorted(CATS)}; countries {len(cs)}; cities {len(cc)}/{len(ci)}')
if err:
    print(f'{len(err)} errors'); print('\n'.join(err[:80])); sys.exit(1)
print('OK — 0 errors')
