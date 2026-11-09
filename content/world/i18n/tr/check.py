#!/usr/bin/env python3
"""L-TR: check content/world/i18n/tr against the EN sources. Run from repo root or anywhere."""
import json, csv, re, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
W = HERE.parent.parent
LANG = HERE.name
err = []
PH = re.compile(r'\{[^{}]*\}'); TAG = re.compile(r'<[^>]+>'); ENT = re.compile(r'&#?\w+;')
try:
    from babel import Locale
    CATS = sorted(Locale(LANG).plural_form.tags | {'other'})
except Exception as e:
    CATS = ['one', 'other']; print('babel missing, assuming', CATS)
PL = {'strings_pages': {'pl_city','pl_city_in','pl_country','pl_country_in','pl_loc','pl_net','pl_place','pl_point','pl_publoc'},
      'strings_shell': {'pl_loc','pl_cc'}}
def same(a, b, where):
    for name, rx in (('placeholders', PH), ('tags', TAG), ('entities', ENT)):
        if sorted(rx.findall(a)) != sorted(rx.findall(b)):
            err.append(f'{where}: {name} differ EN={sorted(rx.findall(a))} TR={sorted(rx.findall(b))}')
for f in ('strings_map', 'strings_pages', 'strings_shell', 'strings_prices'):
    en = json.load(open(W / f'{f}.json')); tr = json.load(open(HERE / f'{f}.json'))
    for k in set(en) - set(tr): err.append(f'{f}: missing {k}')
    for k in set(tr) - set(en): err.append(f'{f}: extra {k}')
    for k, v in tr.items():
        if k not in en: continue
        e = en[k]['en']
        if k in PL.get(f, ()):
            if not isinstance(v, dict) or sorted(v) != CATS or not all(x.strip() for x in v.values()):
                err.append(f'{f}.{k}: plural must be object with {CATS}')
            continue
        if not isinstance(v, str) or not v.strip(): err.append(f'{f}.{k}: empty/not string'); continue
        same(e, v, f'{f}.{k}')
        if e.endswith(' | BlokVolt') and not v.endswith(' | BlokVolt'): err.append(f'{f}.{k}: lost " | BlokVolt"')
        if re.search(r'\b(biz|bizim)\b|7/24|24/7|Evolako', v, re.I): err.append(f'{f}.{k}: forbidden word')
# texts.json
def walk(a, b, p):
    if type(a) != type(b): err.append(f'texts{p}: type differs'); return
    if isinstance(a, dict):
        if list(a) != list(b): err.append(f'texts{p}: keys differ')
        for k in a:
            if k in b: walk(a[k], b[k], f'{p}.{k}')
    elif isinstance(a, list):
        if len(a) != len(b): err.append(f'texts{p}: list length differs')
        for i, (x, y) in enumerate(zip(a, b)): walk(x, y, f'{p}[{i}]')
    elif isinstance(a, str):
        if a.strip() and not b.strip(): err.append(f'texts{p}: empty')
        same(a, b, f'texts{p}')
t = json.load(open(HERE / 'texts.json'))
walk({'about_data': json.load(open(W / 'about_data.json'))['en'], 'download': json.load(open(W / 'download.json'))['en']}, t, '')
# slugs
KEYS = ['home','map','hub','net','about','download','gnet','prices','shell_about','sources','methodology']
s = json.load(open(HERE / 'slugs.json'))
if sorted(s) != sorted(KEYS): err.append('slugs: keys differ')
for k, v in s.items():
    if k in ('net','about','download'):
        if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', v): err.append(f'slugs.{k}: bad segment {v}')
    elif not re.fullmatch(rf'/{LANG}/([a-z0-9]+(-[a-z0-9]+)*/)?', v): err.append(f'slugs.{k}: bad path {v}')
if len(set(s.values())) != len(s): err.append('slugs: duplicates')
# countries
en_c = {r['cc'] for r in csv.DictReader(open(W / 'names' / 'countries.csv'))}
rows = list(csv.DictReader(open(HERE / 'countries.csv')))
if [*rows[0]] != ['cc','name','slug','in_phrase','note']: err.append('countries: header')
if {r['cc'] for r in rows} != en_c: err.append('countries: cc set differs')
sl = [r['slug'] for r in rows]
if len(set(sl)) != len(sl): err.append('countries: duplicate slugs')
for r in rows:
    if not (r['name'] and r['in_phrase']): err.append(f"countries {r['cc']}: empty")
    if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', r['slug']): err.append(f"countries {r['cc']}: bad slug")
# cities
ids = {r['geonameid'] for r in csv.DictReader(open(W / 'names' / 'cities.csv'))}
rows = list(csv.DictReader(open(HERE / 'cities.csv')))
if [*rows[0]] != ['geonameid','name','in_phrase','decl_ok','note']: err.append('cities: header')
seen = set()
for r in rows:
    g = r['geonameid']
    if g not in ids: err.append(f'cities {g}: unknown geonameid')
    if g in seen: err.append(f'cities {g}: duplicate')
    seen.add(g)
    if not (r['name'] and r['in_phrase']) or r['decl_ok'] not in ('0','1'): err.append(f'cities {g}: bad row')
print(f'cities: {len(rows)}/{len(ids)} covered, decl_ok=1: {sum(r["decl_ok"]=="1" for r in rows)}')
print('\n'.join(err) if err else 'OK: 0 errors')
sys.exit(1 if err else 0)
