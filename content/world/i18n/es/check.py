#!/usr/bin/env python3
"""L-ES check: content/world/i18n/es vs EN sources. Run from repo root or anywhere: python3 content/world/i18n/es/check.py"""
import csv, json, re, sys
from pathlib import Path

LANG = 'es'
HERE = Path(__file__).resolve().parent
WORLD = HERE.parents[1]
NAMES = WORLD / 'names'
errs, warns = [], []
PH = re.compile(r'\{[^{}]*\}')
TAG = re.compile(r'<[^>]+>')
ENT = re.compile(r'&[a-zA-Z#0-9]+;')
BANNED = re.compile(r'24/7|\bnosotros\b|\bnuestr[oa]s?\b|\bla redacción\b|\bel equipo\b|\bEvolako\b|\binmediatamente\b|\bal instante\b', re.I)

try:
    from babel import Locale
    CATS = set(Locale(LANG).plural_form.tags) | {'other'}
except Exception as e:  # babel missing → fall back to known CLDR set
    warns.append(f'babel unavailable ({e}); using one/many/other')
    CATS = {'one', 'many', 'other'}


def same_marks(a, b, where):
    for rx, nm in ((PH, 'placeholders'), (TAG, 'html tags'), (ENT, 'entities')):
        if sorted(rx.findall(a)) != sorted(rx.findall(b)):
            errs.append(f'{where}: {nm} differ: EN {sorted(rx.findall(a))} vs ES {sorted(rx.findall(b))}')
    if a.count('BlokVolt') != b.count('BlokVolt'):
        errs.append(f'{where}: BlokVolt count differs')
    if BANNED.search(b):
        errs.append(f'{where}: banned word "{BANNED.search(b).group(0)}"')


# 1. strings
n_str = 0
for f in ('map', 'pages', 'shell', 'prices'):
    en = json.load(open(WORLD / f'strings_{f}.json', encoding='utf-8'))
    p = HERE / f'strings_{f}.json'
    if not p.exists():
        errs.append(f'missing {p.name}'); continue
    es = json.load(open(p, encoding='utf-8'))
    for k in en:
        if k not in es:
            errs.append(f'{p.name}: missing key {k}'); continue
        e, s = en[k]['en'], es[k]
        n_str += 1
        if k.startswith('pl_'):
            if not isinstance(s, dict):
                errs.append(f'{p.name}:{k}: plural must be an object'); continue
            if set(s) != CATS:
                errs.append(f'{p.name}:{k}: plural categories {sorted(s)} != CLDR {sorted(CATS)}')
            if any(not str(v).strip() for v in s.values()):
                errs.append(f'{p.name}:{k}: empty plural form')
            for c, v in s.items():
                same_marks(e.split('|')[0], v, f'{p.name}:{k}.{c}')
            continue
        if not isinstance(s, str) or not s.strip():
            errs.append(f'{p.name}:{k}: empty or not a string'); continue
        same_marks(e, s, f'{p.name}:{k}')
    for k in es:
        if k not in en:
            errs.append(f'{p.name}: extra key {k}')

# 2. texts.json — same structure as EN parts
SRC = {'about_data': 'about_data.json', 'download': 'download.json', 'sources_pages': 'sources_pages.json'}
texts = json.load(open(HERE / 'texts.json', encoding='utf-8'))


def walk(a, b, where):
    global n_str
    if type(a) is not type(b):
        errs.append(f'{where}: type {type(a).__name__} vs {type(b).__name__}'); return
    if isinstance(a, dict):
        if list(a) != list(b):
            errs.append(f'{where}: keys differ {set(a) ^ set(b)}')
        for k in a:
            if k in b:
                walk(a[k], b[k], f'{where}.{k}')
    elif isinstance(a, list):
        if len(a) != len(b):
            errs.append(f'{where}: list length {len(a)} vs {len(b)}')
        for i, (x, y) in enumerate(zip(a, b)):
            walk(x, y, f'{where}[{i}]')
    elif isinstance(a, str):
        n_str += 1
        if a.strip() and not b.strip():
            errs.append(f'{where}: empty')
        same_marks(a, b, where)


for key, fn in SRC.items():
    src = json.load(open(WORLD / fn, encoding='utf-8'))
    en = src['en'] if isinstance(src, dict) and 'en' in src else src
    if key not in texts:
        errs.append(f'texts.json: missing {key}'); continue
    walk(en, texts[key], f'texts.{key}')

# 3. slugs
SLUG_KEYS = ['home', 'map', 'hub', 'net', 'about', 'download', 'gnet', 'prices', 'shell_about', 'sources', 'methodology']
sl = json.load(open(HERE / 'slugs.json', encoding='utf-8'))
if sorted(sl) != sorted(SLUG_KEYS):
    errs.append(f'slugs.json keys {sorted(sl)}')
for k, v in sl.items():
    if k in ('net', 'about', 'download'):
        if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', v):
            errs.append(f'slug {k}={v!r} must be one ascii segment')
    elif not re.fullmatch(rf'/{LANG}/([a-z0-9]+(-[a-z0-9]+)*/)?', v):
        errs.append(f'slug {k}={v!r} must be /{LANG}/…/ ascii')
if len(set(sl.values())) != len(sl):
    errs.append('slugs.json: duplicate values')

# 4. countries.csv
src_cc = [r['cc'] for r in csv.DictReader(open(NAMES / 'countries.csv', encoding='utf-8'))]
rows = list(csv.DictReader(open(HERE / 'countries.csv', encoding='utf-8')))
if [r['cc'] for r in rows] != src_cc:
    errs.append('countries.csv: cc list differs from names/countries.csv')
seen = set()
for r in rows:
    if list(r) != ['cc', 'name', 'slug', 'in_phrase', 'note']:
        errs.append('countries.csv: bad header'); break
    if not r['name'] or not r['in_phrase'].startswith('en '):
        errs.append(f"countries.csv {r['cc']}: name/in_phrase")
    if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', r['slug']) or r['slug'] in seen:
        errs.append(f"countries.csv {r['cc']}: slug {r['slug']!r}")
    seen.add(r['slug'])

# 5. cities.csv
src_ids = {r['geonameid'] for r in csv.DictReader(open(NAMES / 'cities.csv', encoding='utf-8'))}
crow = list(csv.DictReader(open(HERE / 'cities.csv', encoding='utf-8')))
ids = [r['geonameid'] for r in crow]
if len(ids) != len(set(ids)):
    errs.append('cities.csv: duplicate geonameid')
if set(ids) - src_ids:
    errs.append(f'cities.csv: unknown geonameid {sorted(set(ids) - src_ids)[:5]}')
for r in crow:
    if not r['name'] or not r['in_phrase'] or r['decl_ok'] not in ('0', '1'):
        errs.append(f"cities.csv {r['geonameid']}: empty/bad")
cov = len(set(ids) & src_ids)

print(f'L-{LANG.upper()} check: {n_str} strings, slugs {len(sl)}, countries {len(rows)}, cities {cov}/{len(src_ids)}')
for w in warns:
    print('WARN', w)
for e in errs[:200]:
    print('ERR ', e)
print(f'{len(errs)} errors')
sys.exit(1 if errs else 0)
