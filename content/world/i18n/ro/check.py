#!/usr/bin/env python3
"""L-RO check: python3 content/world/i18n/ro/check.py  (from repo root or anywhere). Exit 1 on errors."""
import csv, json, re, sys
from pathlib import Path
from babel import Locale

LANG = 'ro'
HERE = Path(__file__).resolve().parent
WORLD = HERE.parent.parent
err, warn = [], []
PH = re.compile(r'\{[^{}]*\}')
TAG = re.compile(r'</?[a-zA-Z][^>]*>')
ENT = re.compile(r'&[a-zA-Z#0-9]+;')
CAT = set(Locale(LANG).plural_form.tags) | {'other'}

def sig(s):
    return (sorted(PH.findall(s)), sorted(TAG.findall(s)), sorted(ENT.findall(s)))

def bad_chars(where, s):
    if re.search('[şţŞŢ]', s): err.append(f'{where}: cedilla ş/ţ instead of comma-below ș/ț')

# 1. strings
for f in ['strings_map', 'strings_pages', 'strings_shell', 'strings_prices']:
    en = {k: v['en'] for k, v in json.load(open(WORLD / f'{f}.json', encoding='utf-8')).items()}
    tr = json.load(open(HERE / f'{f}.json', encoding='utf-8'))
    for k in en.keys() - tr.keys(): err.append(f'{f}: missing key {k}')
    for k in tr.keys() - en.keys(): err.append(f'{f}: extra key {k}')
    for k in en.keys() & tr.keys():
        v = tr[k]
        if k.startswith('pl_'):
            if not isinstance(v, dict): err.append(f'{f}.{k}: plural must be object'); continue
            if set(v) != CAT: err.append(f'{f}.{k}: categories {sorted(v)} != CLDR {sorted(CAT)}')
            for c, s in v.items():
                if not s.strip(): err.append(f'{f}.{k}.{c}: empty')
                bad_chars(f'{f}.{k}.{c}', s)
            continue
        if not isinstance(v, str) or not v.strip(): err.append(f'{f}.{k}: empty or not a string'); continue
        if sig(en[k]) != sig(v): err.append(f'{f}.{k}: placeholders/tags differ EN={sig(en[k])} RO={sig(v)}')
        if en[k].endswith(' | BlokVolt') and not v.endswith(' | BlokVolt'): err.append(f'{f}.{k}: lost " | BlokVolt"')
        bad_chars(f'{f}.{k}', v)
        for w in ['24/7', 'Evolako', 'noi ', 'redacți']:
            if w.lower() in v.lower(): warn.append(f'{f}.{k}: contains "{w}"')

# 2. texts.json
def walk(e, t, path):
    if isinstance(e, dict):
        if not isinstance(t, dict) or set(e) != set(t): err.append(f'texts{path}: keys differ'); return
        for k in e: walk(e[k], t[k], f'{path}.{k}')
    elif isinstance(e, list):
        if not isinstance(t, list) or len(e) != len(t): err.append(f'texts{path}: list length differs'); return
        for i, (a, b) in enumerate(zip(e, t)): walk(a, b, f'{path}[{i}]')
    elif isinstance(e, str):
        if not isinstance(t, str) or (e.strip() and not t.strip()): err.append(f'texts{path}: empty'); return
        if sig(e) != sig(t): err.append(f'texts{path}: placeholders/tags differ')
        bad_chars(f'texts{path}', t)
    elif e != t: err.append(f'texts{path}: non-text value changed')
T = json.load(open(HERE / 'texts.json', encoding='utf-8'))
for name in ['about_data', 'download']:
    walk(json.load(open(WORLD / f'{name}.json', encoding='utf-8'))['en'], T.get(name), f'.{name}')

# 3. slugs
S = json.load(open(HERE / 'slugs.json', encoding='utf-8'))
KEYS = ['home', 'map', 'hub', 'net', 'about', 'download', 'gnet', 'prices', 'shell_about', 'sources', 'methodology']
if set(S) != set(KEYS): err.append(f'slugs: keys {sorted(S)} != {KEYS}')
for k, v in S.items():
    if k in ('net', 'about', 'download'):
        if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', v): err.append(f'slugs.{k}: bad segment {v!r}')
    elif not re.fullmatch(rf'/{LANG}/([a-z0-9]+(-[a-z0-9]+)*/)?', v): err.append(f'slugs.{k}: bad path {v!r}')
paths = [v for k, v in S.items() if k not in ('net', 'about', 'download')]
if len(set(paths)) != len(paths): err.append('slugs: duplicate paths')

# 4. CSV
cc_src = {r['cc'] for r in csv.DictReader(open(WORLD / 'names/countries.csv', encoding='utf-8'))}
cs = list(csv.DictReader(open(HERE / 'countries.csv', encoding='utf-8')))
if {r['cc'] for r in cs} != cc_src: err.append('countries.csv: cc set differs from names/countries.csv')
if len({r['slug'] for r in cs}) != len(cs): err.append('countries.csv: duplicate slugs')
for r in cs:
    if not (r['name'] and r['in_phrase']): err.append(f'countries {r["cc"]}: empty')
    if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', r['slug']): err.append(f'countries {r["cc"]}: bad slug')
    bad_chars(f'countries {r["cc"]}', r['name'] + r['in_phrase'])
gid_src = {r['geonameid'] for r in csv.DictReader(open(WORLD / 'names/cities.csv', encoding='utf-8'))}
ct = list(csv.DictReader(open(HERE / 'cities.csv', encoding='utf-8')))
gids = [r['geonameid'] for r in ct]
if len(set(gids)) != len(gids): err.append('cities.csv: duplicate geonameid')
if set(gids) - gid_src: err.append(f'cities.csv: unknown geonameid {len(set(gids) - gid_src)}')
for r in ct:
    if not (r['name'] and r['in_phrase']) or r['decl_ok'] not in ('0', '1'): err.append(f'cities {r["geonameid"]}: bad row')
    bad_chars(f'cities {r["geonameid"]}', r['name'])
print(f'cities: {len(ct)}/{len(gid_src)} covered')

for w in warn: print('WARN', w)
for e in err: print('ERR ', e)
print(f'{LANG}: {len(err)} errors, {len(warn)} warnings')
sys.exit(1 if err else 0)
