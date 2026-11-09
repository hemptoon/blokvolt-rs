#!/usr/bin/env python3
"""L-DA check: python3 content/world/i18n/da/check.py  (exit 1 on errors)."""
import csv, json, re, sys
from pathlib import Path
from babel import Locale

HERE = Path(__file__).resolve().parent
WORLD = HERE.parent.parent
LANG = HERE.name
CATS = sorted(set(Locale(LANG).plural_form.tags) | {'other'})
PH = re.compile(r'\{[^{}]*\}')
TAG = re.compile(r'</?[a-zA-Z][^>]*>|&[a-z#0-9]+;')
SLUG_KEYS = ['home', 'map', 'hub', 'net', 'about', 'download', 'gnet', 'prices', 'shell_about', 'sources', 'methodology']
ONE_SEG = {'net', 'about', 'download'}
err = []


def sig(s):
    return sorted(PH.findall(s)), sorted(re.sub(r'\s+', ' ', t) for t in TAG.findall(s))


for f in ['map', 'pages', 'shell', 'prices']:
    en = json.load(open(WORLD / f'strings_{f}.json'))
    tr = json.load(open(HERE / f'strings_{f}.json'))
    for k in set(en) - set(tr): err.append(f'{f}: missing {k}')
    for k in set(tr) - set(en): err.append(f'{f}: extra {k}')
    for k, v in en.items():
        if k not in tr: continue
        e, t = v['en'], tr[k]
        if k.startswith('pl_'):
            if not isinstance(t, dict) or sorted(t) != CATS: err.append(f'{f}.{k}: plural cats {t!r} != {CATS}')
            elif not all(str(x).strip() for x in t.values()): err.append(f'{f}.{k}: empty plural form')
            continue
        if not isinstance(t, str) or not t.strip(): err.append(f'{f}.{k}: empty/not string'); continue
        if sig(e) != sig(t): err.append(f'{f}.{k}: placeholders/tags differ {sig(e)} vs {sig(t)}')
        if e.endswith(' | BlokVolt') and not t.endswith(' | BlokVolt'): err.append(f'{f}.{k}: lost " | BlokVolt"')


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
    elif type(e) is not type(t) or e != t:
        err.append(f'texts{path}: non-string value changed')


texts = json.load(open(HERE / 'texts.json'))
if set(texts) != {'about_data', 'download'}: err.append('texts.json: top keys')
for k in ('about_data', 'download'):
    walk(json.load(open(WORLD / f'{k}.json'))['en'], texts.get(k), f'.{k}')

sl = json.load(open(HERE / 'slugs.json'))
if list(sl) != SLUG_KEYS: err.append(f'slugs.json: keys {list(sl)}')
for k, v in sl.items():
    if k in ONE_SEG:
        if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', v): err.append(f'slug {k}={v}')
    elif not re.fullmatch(rf'/{LANG}/([a-z0-9]+(-[a-z0-9]+)*/)?', v): err.append(f'slug {k}={v}')
if len(set(sl.values())) != len(sl): err.append('slugs.json: duplicate values')

src_cc = {r['cc'] for r in csv.DictReader(open(WORLD / 'names' / 'countries.csv'))}
cc = list(csv.DictReader(open(HERE / 'countries.csv')))
if [*cc[0]] != ['cc', 'name', 'slug', 'in_phrase', 'note']: err.append('countries.csv header')
if {r['cc'] for r in cc} != src_cc: err.append(f'countries.csv: cc set differs ({len(cc)} vs {len(src_cc)})')
slugs = [r['slug'] for r in cc]
if len(set(slugs)) != len(slugs): err.append('countries.csv: duplicate slugs')
for r in cc:
    if not r['name'] or not r['in_phrase'] or r['name'].lower() not in r['in_phrase'].lower(): err.append(f"country {r['cc']}: name/in_phrase")
    if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', r['slug']): err.append(f"country {r['cc']}: slug {r['slug']}")

src_g = {r['geonameid'] for r in csv.DictReader(open(WORLD / 'names' / 'cities.csv'))}
ci = list(csv.DictReader(open(HERE / 'cities.csv')))
if [*ci[0]] != ['geonameid', 'name', 'in_phrase', 'decl_ok', 'note']: err.append('cities.csv header')
g = [r['geonameid'] for r in ci]
if len(set(g)) != len(g): err.append('cities.csv: duplicate geonameid')
if set(g) - src_g: err.append(f'cities.csv: unknown geonameid {sorted(set(g) - src_g)[:5]}')
for r in ci:
    if not r['name'].strip() or not r['in_phrase'].strip() or r['decl_ok'] not in ('0', '1'): err.append(f"city {r['geonameid']}: bad row")

print(f'{LANG}: plural cats {CATS}; strings ok for {sum(len(json.load(open(HERE / f"strings_{f}.json"))) for f in ["map","pages","shell","prices"])} keys; '
      f'countries {len(cc)}/{len(src_cc)}; cities {len(ci)}/{len(src_g)}; errors {len(err)}')
for e in err[:80]: print(' -', e)
sys.exit(1 if err else 0)
