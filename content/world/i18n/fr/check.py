#!/usr/bin/env python3
"""Check content/world/i18n/<lang>/ against the EN sources (L-task contract, pool 3).

Usage: python3 content/world/i18n/fr/check.py   (from repo root or anywhere)
Exit code 0 = clean.
"""
import csv, json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LANG = HERE.name
WORLD = HERE.parents[1]
NAMES = WORLD / 'names'
errors, warns = [], []

PH = re.compile(r'\{[^{}]*\}')
TAG = re.compile(r'</?([a-zA-Z][a-zA-Z0-9]*)')
ENT = re.compile(r'&[a-zA-Z]+;|&#\d+;')
FORBID = re.compile(r'\b(nous|notre|nos)\b|24\s*h\s*/\s*24|24/7|evolako|la rédaction', re.I)
SLUG = re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*$')


def cldr_cats(lang):
    try:
        from babel import Locale
        return set(Locale(lang).plural_form.tags) | {'other'}
    except Exception as e:  # babel missing
        warns.append(f'babel unavailable ({e}); plural categories not checked against CLDR')
        return None


def is_plural_en(v):
    return isinstance(v, str) and '|' in v and ' | ' not in v


def sig(s):
    # pool 4 (10.11.2026): {city_u}/{country_u} may replace {city}/{country} in any language
    ph = [p.replace('{city_u}', '{city}').replace('{country_u}', '{country}') for p in PH.findall(s)]
    return (sorted(ph), sorted(TAG.findall(s)), sorted(ENT.findall(s)))


def cmp_text(where, en, tr):
    if not isinstance(tr, str) or not tr.strip():
        errors.append(f'{where}: empty or not a string'); return
    if sig(en) != sig(tr):
        errors.append(f'{where}: placeholders/tags/entities differ: EN {sig(en)} vs {sig(tr)}')
    if FORBID.search(tr):
        errors.append(f'{where}: forbidden word: {FORBID.search(tr).group(0)!r}')


cats = cldr_cats(LANG)

# 1. strings_*.json
# LANG pool L2 (11.11.2026): all 8 string files
for name in ('strings_map', 'strings_pages', 'strings_shell', 'strings_prices',
             'strings_pay', 'strings_press', 'strings_b2b', 'strings_embed'):
    src = json.loads((WORLD / f'{name}.json').read_text())
    p = HERE / f'{name}.json'
    if not p.exists():
        errors.append(f'{name}.json missing'); continue
    tr = json.loads(p.read_text())
    en = {k: v['en'] for k, v in src.items()}
    miss, extra = set(en) - set(tr), set(tr) - set(en)
    if miss: errors.append(f'{name}: missing keys {sorted(miss)}')
    if extra: errors.append(f'{name}: extra keys {sorted(extra)}')
    for k in en.keys() & tr.keys():
        w = f'{name}.{k}'
        if is_plural_en(en[k]):
            if not isinstance(tr[k], dict):
                errors.append(f'{w}: plural key must be an object'); continue
            if cats is not None and set(tr[k]) != cats:
                errors.append(f'{w}: plural categories {sorted(tr[k])} != CLDR {sorted(cats)}')
            for c, v in tr[k].items():
                cmp_text(f'{w}.{c}', en[k].split('|')[0], v)
        else:
            cmp_text(w, en[k], tr[k])
        if isinstance(en[k], str) and en[k].endswith(' | BlokVolt') and isinstance(tr[k], str) \
                and not tr[k].endswith(' | BlokVolt'):
            errors.append(f'{w}: lost " | BlokVolt" suffix')

# 2. texts.json — same structure as the EN parts
def walk(where, en, tr):
    if isinstance(en, dict):
        if not isinstance(tr, dict) or set(en) != set(tr):
            errors.append(f'{where}: keys differ'); return
        for k in en: walk(f'{where}.{k}', en[k], tr[k])
    elif isinstance(en, list):
        if not isinstance(tr, list) or len(en) != len(tr):
            errors.append(f'{where}: list length differs'); return
        for i, (a, b) in enumerate(zip(en, tr)): walk(f'{where}[{i}]', a, b)
    elif isinstance(en, str):
        if en.startswith('http') or not en.strip():
            if tr != en: warns.append(f'{where}: URL/empty value changed')
            return
        cmp_text(where, en, tr)
    elif en != tr:
        errors.append(f'{where}: non-text value changed')

p = HERE / 'texts.json'
if p.exists():
    t = json.loads(p.read_text())
    # pool 3, 23:55: sources_pages.json is not translated; texts.json = about_data + download
    # LANG pool L2 (11.11.2026): + pay, routes (LANG0 format: node path -> text)
    if set(t) != {'about_data', 'download', 'pay', 'routes'}:
        errors.append(f'texts.json: top keys must be about_data, download, pay, routes, got {sorted(t)}')
    for n in ('about_data', 'download'):
        walk(f'texts.{n}', json.loads((WORLD / f'{n}.json').read_text())['en'], t.get(n))

    def ml_nodes(n, p, out):
        if isinstance(n, dict):
            if isinstance(n.get('en'), str) and {'sr', 'ru'} <= set(n):
                out[p] = n['en']; return
            for k, v in n.items(): ml_nodes(v, f'{p}.{k}' if p else k, out)
        elif isinstance(n, list):
            for i, v in enumerate(n): ml_nodes(v, f'{p}[{i}]', out)

    for n in ('pay', 'routes'):
        en_nodes = {}
        ml_nodes(json.loads((WORLD / f'{n}.json').read_text()), '', en_nodes)
        tr = t.get(n) or {}
        miss, extra = set(en_nodes) - set(tr), set(tr) - set(en_nodes)
        if miss: errors.append(f'texts.{n}: missing paths {sorted(miss)[:10]} ({len(miss)})')
        if extra: errors.append(f'texts.{n}: unknown paths {sorted(extra)[:10]} ({len(extra)})')
        for k in en_nodes.keys() & tr.keys():
            cmp_text(f'texts.{n}.{k}', en_nodes[k], tr[k])
    if False: walk('texts.sources_pages', json.loads((WORLD / 'sources_pages.json').read_text()), t.get('sources_pages'))
else:
    errors.append('texts.json missing')

# 3. slugs.json
KEYS = ['home', 'map', 'hub', 'net', 'about', 'download', 'gnet', 'prices', 'shell_about', 'sources', 'methodology']
s = json.loads((HERE / 'slugs.json').read_text())
if sorted(s) != sorted(KEYS): errors.append(f'slugs.json keys {sorted(s)}')
for k, v in s.items():
    if k in ('net', 'about', 'download'):
        if not SLUG.match(v): errors.append(f'slugs.{k}: not an ASCII segment: {v!r}')
    else:
        segs = v.strip('/').split('/')
        if not (v.startswith(f'/{LANG}/') and v.endswith('/') and all(SLUG.match(x) for x in segs)):
            errors.append(f'slugs.{k}: must be /{LANG}/…/ ASCII: {v!r}')
paths = [v for k, v in s.items() if k not in ('net', 'about', 'download')]
if len(set(paths)) != len(paths): errors.append('slugs.json: duplicate paths')

# 4. countries.csv
base_cc = {r['cc'] for r in csv.DictReader(open(NAMES / 'countries.csv', encoding='utf-8'))}
rows = list(csv.DictReader(open(HERE / 'countries.csv', encoding='utf-8')))
if rows and list(rows[0]) != ['cc', 'name', 'slug', 'in_phrase', 'note']:
    errors.append(f'countries.csv header {list(rows[0])}')
cc = [r['cc'] for r in rows]
if set(cc) != base_cc or len(cc) != len(base_cc): errors.append(f'countries.csv: {len(cc)} rows, cc set differs from names/countries.csv')
sl = [r['slug'] for r in rows]
if len(set(sl)) != len(sl): errors.append('countries.csv: duplicate slugs')
for r in rows:
    if not SLUG.match(r['slug']): errors.append(f"countries {r['cc']}: bad slug {r['slug']!r}")
    if not r['name'].strip() or not r['in_phrase'].strip(): errors.append(f"countries {r['cc']}: empty name/in_phrase")

# 5. cities.csv
base = {r['geonameid'] for r in csv.DictReader(open(NAMES / 'cities.csv', encoding='utf-8'))}
p = HERE / 'cities.csv'
if p.exists():
    rows = list(csv.DictReader(open(p, encoding='utf-8')))
    if rows and list(rows[0]) != ['geonameid', 'name', 'in_phrase', 'decl_ok', 'note']:
        errors.append(f'cities.csv header {list(rows[0])}')
    ids = [r['geonameid'] for r in rows]
    if len(set(ids)) != len(ids): errors.append('cities.csv: duplicate geonameid')
    unk = set(ids) - base
    if unk: errors.append(f'cities.csv: {len(unk)} geonameids not in names/cities.csv')
    for r in rows:
        if not r['name'].strip() or not r['in_phrase'].strip(): errors.append(f"cities {r['geonameid']}: empty")
        if r['decl_ok'] not in ('0', '1'): errors.append(f"cities {r['geonameid']}: decl_ok {r['decl_ok']!r}")
    print(f'cities.csv: {len(rows)} of {len(base)} cities, decl_ok=0: {sum(r["decl_ok"] == "0" for r in rows)}')
else:
    warns.append('cities.csv missing')

for w in warns: print('WARN', w)
for e in errors: print('ERROR', e)
print(f'{LANG}: {len(errors)} errors, {len(warns)} warnings')
sys.exit(1 if errors else 0)
