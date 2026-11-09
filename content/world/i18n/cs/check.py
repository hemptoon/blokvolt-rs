#!/usr/bin/env python3
"""L-CS: kontrola české lokalizace světové vrstvy. Spuštění z kořene repa:
   python3 content/world/i18n/cs/check.py"""
import csv, json, re, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
W = HERE.parent.parent
LANG = 'cs'
err = []
PH = re.compile(r'\{[^{}]*\}')
TAG = re.compile(r'<[^>]+>|&[a-z#0-9]+;')

def cats():
    try:
        from babel import Locale
        return set(Locale(LANG).plural_form.tags) | {'other'}
    except Exception:
        return {'one', 'few', 'many', 'other'}
CATS = cats()

def same(a, b, where):
    if sorted(PH.findall(a)) != sorted(PH.findall(b)):
        err.append(f'{where}: placeholders {PH.findall(a)} vs {PH.findall(b)}')
    if sorted(TAG.findall(a)) != sorted(TAG.findall(b)):
        err.append(f'{where}: tags/entities differ')
    if a.endswith(' | BlokVolt') != b.endswith(' | BlokVolt'):
        err.append(f'{where}: " | BlokVolt" tail')

for name in ('strings_map', 'strings_pages', 'strings_shell', 'strings_prices'):
    en = {k: v['en'] for k, v in json.load(open(W / f'{name}.json')).items()}
    cs = json.load(open(HERE / f'{name}.json'))
    for k in en.keys() - cs.keys(): err.append(f'{name}: missing {k}')
    for k in cs.keys() - en.keys(): err.append(f'{name}: extra {k}')
    for k, ev in en.items():
        v = cs.get(k)
        if v is None: continue
        if k.startswith('pl_'):
            if not isinstance(v, dict) or set(v) != CATS:
                err.append(f'{name}.{k}: plural categories {sorted(v) if isinstance(v, dict) else type(v).__name__} != {sorted(CATS)}')
            elif any(not s.strip() for s in v.values()):
                err.append(f'{name}.{k}: empty form')
        elif not isinstance(v, str) or not v.strip():
            err.append(f'{name}.{k}: empty or not a string')
        else:
            same(v, ev, f'{name}.{k}')

def walk(a, b, path):
    if isinstance(a, dict):
        if not isinstance(b, dict) or list(a) != list(b):
            err.append(f'texts{path}: keys differ'); return
        for k in a: walk(a[k], b[k], f'{path}.{k}')
    elif isinstance(a, list):
        if not isinstance(b, list) or len(a) != len(b):
            err.append(f'texts{path}: list length'); return
        for i, (x, y) in enumerate(zip(a, b)): walk(x, y, f'{path}[{i}]')
    elif isinstance(a, str):
        if not isinstance(b, str) or not b.strip(): err.append(f'texts{path}: empty')
        else: same(b, a, f'texts{path}')
    elif type(a) != type(b) or a != b:
        err.append(f'texts{path}: non-string value changed')

t = json.load(open(HERE / 'texts.json'))
for key, fn in (('about_data', 'about_data.json'), ('download', 'download.json')):
    src = json.load(open(W / fn))
    walk(src['en'] if 'en' in src else src, t.get(key), f'.{key}')

s = json.load(open(HERE / 'slugs.json'))
KEYS = ['home', 'map', 'hub', 'net', 'about', 'download', 'gnet', 'prices', 'shell_about', 'sources', 'methodology']
if sorted(s) != sorted(KEYS): err.append(f'slugs keys: {sorted(s)}')
for k, v in s.items():
    if k in ('net', 'about', 'download'):
        if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', v): err.append(f'slug {k}: {v!r}')
    elif not re.fullmatch(rf'/{LANG}/([a-z0-9]+(-[a-z0-9]+)*/)?', v): err.append(f'slug {k}: {v!r}')
paths = [v for k, v in s.items() if k not in ('net', 'about', 'download')]
if len(paths) != len(set(paths)): err.append('slugs: duplicate paths')

src_cc = {r['cc'] for r in csv.DictReader(open(W / 'names/countries.csv', encoding='utf-8'))}
rows = list(csv.DictReader(open(HERE / 'countries.csv', encoding='utf-8')))
if list(rows[0]) != ['cc', 'name', 'slug', 'in_phrase', 'note']: err.append('countries.csv header')
if {r['cc'] for r in rows} != src_cc: err.append(f'countries.csv: cc set differs ({len(rows)} rows)')
for r in rows:
    if not r['name'].strip() or not r['in_phrase'].strip(): err.append(f'countries {r["cc"]}: empty')
    if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', r['slug']): err.append(f'countries {r["cc"]}: slug {r["slug"]!r}')
sl = [r['slug'] for r in rows]
if len(sl) != len(set(sl)): err.append('countries.csv: duplicate slugs')

src_g = {r['geonameid'] for r in csv.DictReader(open(W / 'names/cities.csv', encoding='utf-8'))}
rows = list(csv.DictReader(open(HERE / 'cities.csv', encoding='utf-8')))
if list(rows[0]) != ['geonameid', 'name', 'in_phrase', 'decl_ok', 'note']: err.append('cities.csv header')
g = [r['geonameid'] for r in rows]
if len(g) != len(set(g)): err.append('cities.csv: duplicate geonameid')
if set(g) - src_g: err.append(f'cities.csv: unknown geonameid {len(set(g) - src_g)}')
for r in rows:
    if not r['name'].strip() or not r['in_phrase'].strip() or r['decl_ok'] not in ('0', '1'):
        err.append(f'cities {r["geonameid"]}: bad row')

print(f'cities: {len(rows)} of {len(src_g)}; decl_ok=1: {sum(r["decl_ok"] == "1" for r in rows)}')
print('\n'.join(err[:80]) or 'OK — 0 errors')
sys.exit(1 if err else 0)
