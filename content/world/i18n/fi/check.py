#!/usr/bin/env python3
"""L-FI: checks content/world/i18n/fi against the EN sources. Run from repo root: python3 content/world/i18n/fi/check.py"""
import csv, json, re, sys
from pathlib import Path
LANG = 'fi'
ROOT = Path(__file__).resolve().parents[4]
W = ROOT / 'content' / 'world'
D = W / 'i18n' / LANG
errs = []
def err(m): errs.append(m)
PH = re.compile(r'\{[^{}]*\}')
TAG = re.compile(r'<[^>]+>|&[a-z#0-9]+;')
def sig(s): return sorted(PH.findall(s)), sorted(TAG.findall(s))
try:
    from babel import Locale
    cats = set(Locale(LANG).plural_form.tags) | {'other'}
except Exception as e:
    cats = {'one', 'other'}; print('babel missing, using', cats)
for f in ('strings_map', 'strings_pages', 'strings_shell', 'strings_prices'):
    en = {k: v['en'] for k, v in json.load(open(W / f'{f}.json', encoding='utf-8')).items()}
    tr = json.load(open(D / f'{f}.json', encoding='utf-8'))
    for k in en.keys() - tr.keys(): err(f'{f}: missing key {k}')
    for k in tr.keys() - en.keys(): err(f'{f}: extra key {k}')
    for k in en.keys() & tr.keys():
        e, t = en[k], tr[k]
        if isinstance(t, dict):
            if '|' not in e: err(f'{f}.{k}: plural object but EN is not a plural form')
            if set(t) != cats: err(f'{f}.{k}: plural categories {sorted(t)} != CLDR {sorted(cats)}')
            for c, v in t.items():
                if not str(v).strip(): err(f'{f}.{k}.{c}: empty')
                if sig(v) != sig(e.split('|')[0]): err(f'{f}.{k}.{c}: placeholders/tags differ')
            continue
        if '|' in e and k.startswith('pl_'): err(f'{f}.{k}: EN is a plural form, FI must be an object')
        if not str(t).strip() and str(e).strip(): err(f'{f}.{k}: empty')
        if sig(t) != sig(e): err(f'{f}.{k}: placeholders/tags differ: {sig(e)} vs {sig(t)}')
# texts.json
def walk(a, b, p):
    if type(a) != type(b): return err(f'texts{p}: type {type(a).__name__} vs {type(b).__name__}')
    if isinstance(a, dict):
        if a.keys() != b.keys(): err(f'texts{p}: keys differ {set(a) ^ set(b)}')
        for k in a.keys() & b.keys(): walk(a[k], b[k], f'{p}.{k}')
    elif isinstance(a, list):
        if len(a) != len(b): return err(f'texts{p}: list length {len(a)} vs {len(b)}')
        for i, (x, y) in enumerate(zip(a, b)): walk(x, y, f'{p}[{i}]')
    elif isinstance(a, str):
        if a.strip() and not b.strip(): err(f'texts{p}: empty')
        if sig(a) != sig(b): err(f'texts{p}: placeholders/tags differ')
t = json.load(open(D / 'texts.json', encoding='utf-8'))
src = {'about_data': json.load(open(W / 'about_data.json'))['en'], 'download': json.load(open(W / 'download.json'))['en'],
       'sources_pages': json.load(open(W / 'sources_pages.json'))}
if set(t) != set(src): err(f'texts.json top keys {sorted(t)}')
for k in src: walk(src[k], t.get(k), '.' + k)
# slugs
s = json.load(open(D / 'slugs.json'))
need = {'home', 'map', 'hub', 'net', 'about', 'download', 'gnet', 'prices', 'shell_about', 'sources', 'methodology'}
if set(s) != need: err(f'slugs keys {set(s) ^ need}')
for k, v in s.items():
    if k in ('net', 'about', 'download'):
        if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', v): err(f'slug {k}={v} not one ASCII segment')
    elif not re.fullmatch(rf'/{LANG}/([a-z0-9]+(-[a-z0-9]+)*/)?', v): err(f'slug {k}={v} not /{LANG}/…/ ASCII')
if len(set(s.values())) != len(s): err('duplicate slugs')
# countries
cc_src = [r['cc'] for r in csv.DictReader(open(W / 'names' / 'countries.csv', encoding='utf-8'))]
rows = list(csv.DictReader(open(D / 'countries.csv', encoding='utf-8')))
if [r['cc'] for r in rows] != cc_src: err('countries.csv: cc list differs from names/countries.csv')
slugs = [r['slug'] for r in rows]
if len(set(slugs)) != len(slugs): err('countries.csv: duplicate slug')
for r in rows:
    if not r['name'] or not r['in_phrase']: err(f"countries {r['cc']}: empty")
    if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', r['slug']): err(f"countries {r['cc']}: slug {r['slug']}")
    if r['slug'] in [v.strip('/').split('/')[-1] for v in s.values()]: err(f"countries {r['cc']}: slug collides with a page slug")
# cities
gid_src = {r['geonameid'] for r in csv.DictReader(open(W / 'names' / 'cities.csv', encoding='utf-8'))}
crow = list(csv.DictReader(open(D / 'cities.csv', encoding='utf-8')))
for r in crow:
    if r['geonameid'] not in gid_src: err(f"cities: unknown geonameid {r['geonameid']}")
    if not r['name'] or not r['in_phrase'] or r['decl_ok'] not in ('0', '1'): err(f"cities {r['geonameid']}: bad row")
if len({r['geonameid'] for r in crow}) != len(crow): err('cities: duplicate geonameid')
print(f'cities: {len(crow)}/{len(gid_src)} rows, decl_ok=1: {sum(r["decl_ok"] == "1" for r in crow)}')
print(f'countries: {len(rows)}; slugs: {len(s)}')
print('\n'.join(errs) if errs else 'OK: 0 errors')
sys.exit(1 if errs else 0)
