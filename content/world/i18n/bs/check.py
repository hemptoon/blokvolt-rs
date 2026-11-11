#!/usr/bin/env python3
"""L-BS / L2-bs check (8 string files + texts pay/routes): python3 content/world/i18n/bs/check.py  (exit 1 on errors)"""
import csv, json, re, sys
from pathlib import Path
from babel import Locale
LANG = 'bs'
HERE = Path(__file__).resolve().parent
WORLD = HERE.parent.parent
CATS = set(Locale(LANG).plural_form.tags) | {'other'}
PH = re.compile(r'\{[A-Za-z_0-9]+\}')
TAG = re.compile(r'</?[a-zA-Z][^>]*>|&[a-z#0-9]+;')
BAD = re.compile(r'24/7|\bodmah\b|Evolako|redakcij|\bmi smo\b|\bnaš[aeiu]?\b|[Ѐ-ӿ]', re.I)
EKAV = re.compile(r'\b(cena|cene|cenu|mesto|mesta|gde|vreme|proveri\w*|provere\w*|nedelj\w*|posle|deo|sveta|svetu|reka|tjedan\w*|tisuć\w*|točk\w*|cjenik\w*)\b', re.I)
err, warn = [], []

def strs(v):
    if isinstance(v, str): yield v
    elif isinstance(v, dict):
        for x in v.values(): yield from strs(x)
    elif isinstance(v, list):
        for x in v: yield from strs(x)

FILES = ('strings_map', 'strings_pages', 'strings_shell', 'strings_prices', 'strings_pay', 'strings_press', 'strings_b2b', 'strings_embed')   # L2: all 8
for f in FILES:
    en = {k: v['en'] for k, v in json.load(open(WORLD / f'{f}.json', encoding='utf-8')).items()}
    tr = json.load(open(HERE / f'{f}.json', encoding='utf-8'))
    if set(en) != set(tr): err.append(f'{f}: keys differ: missing {sorted(set(en)-set(tr))} extra {sorted(set(tr)-set(en))}')
    for k, e in en.items():
        t = tr.get(k)
        if t is None: continue
        if k.startswith('pl_'):
            if not isinstance(t, dict) or set(t) != CATS: err.append(f'{f}.{k}: plural categories {t if not isinstance(t,dict) else sorted(t)} != {sorted(CATS)}')
            elif not all(isinstance(x, str) and x.strip() for x in t.values()): err.append(f'{f}.{k}: empty plural form')
            continue
        if not isinstance(t, str) or not t.strip(): err.append(f'{f}.{k}: empty'); continue
        nph = lambda x: sorted(re.sub(r'\{(city|country)_u\}', r'{\1}', y) for y in PH.findall(x))   # R-BS: {city_u}/{country_u} allowed for {city}/{country} (pool 4, 00:12)
        if nph(e) != nph(t): err.append(f'{f}.{k}: placeholders {PH.findall(e)} vs {PH.findall(t)}')
        if len(e) <= 25 and '{' not in e and len(t) > max(len(e) * 1.4, len(e) + 4): warn.append(f'{f}.{k}: short UI string longer than EN x1.4: {t!r} vs {e!r}')
        if sorted(TAG.findall(e)) != sorted(TAG.findall(t)): err.append(f'{f}.{k}: html/entities differ')
        if e.endswith(' | BlokVolt') and not t.endswith(' | BlokVolt'): err.append(f'{f}.{k}: title tail')
        if BAD.search(t): err.append(f'{f}.{k}: forbidden word/script: {BAD.search(t).group(0)}')
        if EKAV.search(t): warn.append(f'{f}.{k}: ekavian/HR lexis? {EKAV.search(t).group(0)}')

def same_shape(a, b, path):
    if type(a) is not type(b): err.append(f'texts {path}: type'); return
    if isinstance(a, dict):
        if list(a) != list(b): err.append(f'texts {path}: keys differ')
        for k in a:
            if k in b: same_shape(a[k], b[k], f'{path}.{k}')
    elif isinstance(a, list):
        if len(a) != len(b): err.append(f'texts {path}: list length')
        for i, (x, y) in enumerate(zip(a, b)): same_shape(x, y, f'{path}[{i}]')
    elif isinstance(a, str):
        if a.strip() and not b.strip(): err.append(f'texts {path}: empty')
        if sorted(PH.findall(a)) != sorted(PH.findall(b)): err.append(f'texts {path}: placeholders')
        if BAD.search(b): err.append(f'texts {path}: forbidden {BAD.search(b).group(0)}')
        if EKAV.search(b): warn.append(f'texts {path}: ekavian? {EKAV.search(b).group(0)}')

texts = json.load(open(HERE / 'texts.json', encoding='utf-8'))
if set(texts) != {'about_data', 'download', 'pay', 'routes'}: err.append(f'texts.json: top keys {sorted(texts)}')
for k in ('about_data', 'download'):
    same_shape(json.load(open(WORLD / f'{k}.json', encoding='utf-8'))['en'], texts.get(k), k)

# L2 / LANG0: texts.pay and texts.routes — dotted path of each multilingual node of pay.json / routes.json -> text
def ml_nodes(v, p, out):
    if isinstance(v, dict):
        if isinstance(v.get('en'), str) and ('sr' in v or 'ru' in v): out[p] = v['en']; return
        for k, x in v.items(): ml_nodes(x, f'{p}.{k}' if p else k, out)
    elif isinstance(v, list):
        for i, x in enumerate(v): ml_nodes(x, f'{p}[{i}]', out)
for sec in ('pay', 'routes'):
    nodes = {}; ml_nodes(json.load(open(WORLD / f'{sec}.json', encoding='utf-8')), '', nodes)
    got = texts.get(sec) or {}
    if set(nodes) != set(got): err.append(f'texts.{sec}: paths differ: missing {sorted(set(nodes)-set(got))[:5]} extra {sorted(set(got)-set(nodes))[:5]}')
    for path, e in nodes.items():
        t = got.get(path)
        if t is None: continue
        if not isinstance(t, str) or not t.strip(): err.append(f'texts.{sec} {path}: empty'); continue
        if sorted(PH.findall(e)) != sorted(PH.findall(t)): err.append(f'texts.{sec} {path}: placeholders')
        if BAD.search(t): err.append(f'texts.{sec} {path}: forbidden {BAD.search(t).group(0)}')
        if EKAV.search(t): warn.append(f'texts.{sec} {path}: ekavian? {EKAV.search(t).group(0)}')

KEYS = ['home', 'map', 'hub', 'net', 'about', 'download', 'gnet', 'prices', 'shell_about', 'sources', 'methodology']
sl = json.load(open(HERE / 'slugs.json', encoding='utf-8'))
if list(sl) != KEYS and set(sl) != set(KEYS): err.append(f'slugs: keys {list(sl)}')
for k, v in sl.items():
    if k in ('net', 'about', 'download'):
        if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', v): err.append(f'slugs.{k}: {v}')
    elif not re.fullmatch(r'/' + LANG + r'/([a-z0-9]+(-[a-z0-9]+)*/)*', v): err.append(f'slugs.{k}: {v}')
if len(set(sl.values())) != len(sl): err.append('slugs: duplicates')

src_c = {r['cc'] for r in csv.DictReader(open(WORLD / 'names/countries.csv', encoding='utf-8'))}
cs = list(csv.DictReader(open(HERE / 'countries.csv', encoding='utf-8')))
if cs and list(cs[0]) != ['cc', 'name', 'slug', 'in_phrase', 'note']: err.append('countries.csv: columns')
if {r['cc'] for r in cs} != src_c: err.append('countries.csv: cc set differs')
for r in cs:
    if not (r['name'] and r['in_phrase']): err.append(f"countries {r['cc']}: empty")
    if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', r['slug']): err.append(f"countries {r['cc']}: slug {r['slug']}")
    if not re.match(r'(u|na) ', r['in_phrase']): warn.append(f"countries {r['cc']}: in_phrase {r['in_phrase']}")
if len({r['slug'] for r in cs}) != len(cs): err.append('countries: duplicate slugs')

src_g = {r['geonameid'] for r in csv.DictReader(open(WORLD / 'names/cities.csv', encoding='utf-8'))}
ci = list(csv.DictReader(open(HERE / 'cities.csv', encoding='utf-8')))
if ci and list(ci[0]) != ['geonameid', 'name', 'in_phrase', 'decl_ok', 'note']: err.append('cities.csv: columns')
if not {r['geonameid'] for r in ci} <= src_g: err.append('cities.csv: unknown geonameid')
for r in ci:
    if not (r['name'] and r['in_phrase']) or r['decl_ok'] not in ('0', '1'): err.append(f"cities {r['geonameid']}: bad row")
    if r['in_phrase'].startswith('u gradu') and r['decl_ok'] != '0': err.append(f"cities {r['geonameid']}: safe phrase must be decl_ok=0")

print(f'cities {len(ci)}/{len(src_g)}, decl_ok=1: {sum(r["decl_ok"]=="1" for r in ci)}; countries {len(cs)}')
for w in warn: print('WARN', w)
for e in err: print('ERR ', e)
print('OK' if not err else f'{len(err)} errors')
sys.exit(1 if err else 0)
