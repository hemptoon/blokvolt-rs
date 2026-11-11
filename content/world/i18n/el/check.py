#!/usr/bin/env python3
"""L-EL self-check: python3 content/world/i18n/el/check.py  (exit 0 = OK)."""
import csv, json, re, sys
from pathlib import Path
from babel import Locale

HERE = Path(__file__).resolve().parent
WORLD = HERE.parent.parent
LANG = HERE.name
CATS = set(Locale(LANG).plural_form.tags) | {'other'}
PH = re.compile(r'\{[^{}]*\}')
U = {'{city_u}': '{city}', '{country_u}': '{country}'}
TAG = re.compile(r'</?[a-zA-Z][^>]*>|&[a-zA-Z#0-9]+;')
SLUG = re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*$')
err = []


def tags(s):  # tag names + entities, attribute order ignored
    return sorted(re.sub(r'\s.*', '', t.rstrip('>')) for t in TAG.findall(s))


for part in ('map', 'pages', 'shell', 'prices', 'pay', 'press', 'b2b', 'embed'):  # L2: all 8 files
    en = json.load(open(WORLD / f'strings_{part}.json'))
    tr = json.load(open(HERE / f'strings_{part}.json'))
    for k in en.keys() - tr.keys():
        err.append(f'{part}: missing key {k}')
    for k in tr.keys() - en.keys():
        err.append(f'{part}: extra key {k}')
    for k, v in en.items():
        if k not in tr:
            continue
        e, t = v['en'], tr[k]
        if k.startswith('pl_'):
            if not isinstance(t, dict) or set(t) != CATS:
                err.append(f'{part}.{k}: plural categories {sorted(t) if isinstance(t, dict) else type(t).__name__} != {sorted(CATS)}')
            elif not all(isinstance(x, str) and x.strip() for x in t.values()):
                err.append(f'{part}.{k}: empty plural form')
            continue
        if not isinstance(t, str) or not t.strip():
            err.append(f'{part}.{k}: empty or not a string')
            continue
        # pool 4 (10.11): {city_u}/{country_u} may replace {city}/{country} — the engine fills in_phrase
        if sorted(U.get(x, x) for x in PH.findall(e)) != sorted(U.get(x, x) for x in PH.findall(t)):
            err.append(f'{part}.{k}: placeholders {sorted(PH.findall(e))} vs {sorted(PH.findall(t))}')
        if tags(e) != tags(t):
            err.append(f'{part}.{k}: tags/entities differ')
        if e.endswith(' | BlokVolt') and not t.endswith(' | BlokVolt'):
            err.append(f'{part}.{k}: lost " | BlokVolt"')

# texts.json — same structure as the EN parts
def walk(a, b, path):
    if type(a) is not type(b):
        err.append(f'texts{path}: type {type(a).__name__} vs {type(b).__name__}'); return
    if isinstance(a, dict):
        if list(a) != list(b):
            err.append(f'texts{path}: keys differ')
        for k in a:
            if k in b:
                walk(a[k], b[k], f'{path}.{k}')
    elif isinstance(a, list):
        if len(a) != len(b):
            err.append(f'texts{path}: list length {len(a)} vs {len(b)}')
        for i, (x, y) in enumerate(zip(a, b)):
            walk(x, y, f'{path}[{i}]')
    elif isinstance(a, str):
        if a.strip() and not b.strip():
            err.append(f'texts{path}: empty')
        if sorted(PH.findall(a)) != sorted(PH.findall(b)):
            err.append(f'texts{path}: placeholders differ')
        if tags(a) != tags(b):
            err.append(f'texts{path}: tags differ')

texts = json.load(open(HERE / 'texts.json'))
for name, src in (('about_data', 'about_data.json'), ('download', 'download.json')):
    if name not in texts:
        err.append(f'texts: missing {name}')
    else:
        walk(json.load(open(WORLD / src))['en'], texts[name], '.' + name)

# texts.json → pay / routes (LANG0 format): dotted path of each multilingual node → text
def ml_nodes(o, p, out):
    if isinstance(o, dict):
        if 'en' in o and 'sr' in o and isinstance(o['en'], str):
            out[p] = o['en']; return out
        for k, v in o.items():
            ml_nodes(v, (p + '.' if p else '') + k, out)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            ml_nodes(v, f'{p}[{i}]', out)
    return out

for name, src in (('pay', 'pay.json'), ('routes', 'routes.json')):
    want = ml_nodes(json.load(open(WORLD / src)), '', {})
    got = texts.get(name)
    if not isinstance(got, dict):
        err.append(f'texts: missing section {name}'); continue
    for k in want.keys() - got.keys():
        err.append(f'texts.{name}: missing {k}')
    for k in got.keys() - want.keys():
        err.append(f'texts.{name}: extra {k}')
    for k, e in want.items():
        t = got.get(k)
        if k in got and (not isinstance(t, str) or not t.strip()):
            err.append(f'texts.{name}.{k}: empty')
        elif k in got and (sorted(PH.findall(e)) != sorted(PH.findall(t)) or tags(e) != tags(t)):
            err.append(f'texts.{name}.{k}: placeholders/tags differ')

# tone: impersonal (no "we"), no 24/7 — RUNBOOK §0 / CONTENT_STYLE
BAD = re.compile(r'24/7|\bεμείς\b|ευχαριστούμε|\bη σύνταξη\b', re.I)
def all_str(o):
    if isinstance(o, str): yield o
    elif isinstance(o, dict):
        for v in o.values(): yield from all_str(v)
    elif isinstance(o, list):
        for v in o: yield from all_str(v)
for f in sorted(HERE.glob('strings_*.json')) + [HERE / 'texts.json']:
    for x in all_str(json.load(open(f))):
        if BAD.search(x):
            err.append(f'{f.name}: forbidden wording: {x[:60]}')

# slugs.json
KEYS = ['home', 'map', 'hub', 'net', 'about', 'download', 'gnet', 'prices', 'shell_about', 'sources', 'methodology']
sl = json.load(open(HERE / 'slugs.json'))
if sorted(sl) != sorted(KEYS):
    err.append(f'slugs: keys {sorted(sl)}')
for k, v in sl.items():
    if k in ('net', 'about', 'download'):
        if not SLUG.match(v):
            err.append(f'slugs.{k}: bad segment {v!r}')
    else:
        segs = v.strip('/').split('/')
        if not (v.startswith(f'/{LANG}/') and v.endswith('/') and all(SLUG.match(s) for s in segs)):
            err.append(f'slugs.{k}: bad path {v!r}')
vals = [v for v in sl.values()]
if len(vals) != len(set(vals)):
    err.append('slugs: duplicate values')

# countries.csv
src_c = [r['cc'] for r in csv.DictReader(open(WORLD / 'names' / 'countries.csv'))]
rows = list(csv.DictReader(open(HERE / 'countries.csv')))
if [r['cc'] for r in rows] != src_c:
    err.append('countries: cc list differs from names/countries.csv')
seen = set()
for r in rows:
    if list(r) != ['cc', 'name', 'slug', 'in_phrase', 'note']:
        err.append('countries: header'); break
    if not r['name'].strip() or not r['in_phrase'].strip():
        err.append(f"countries {r['cc']}: empty name/in_phrase")
    if not SLUG.match(r['slug']):
        err.append(f"countries {r['cc']}: bad slug {r['slug']!r}")
    if r['slug'] in seen:
        err.append(f"countries {r['cc']}: duplicate slug")
    seen.add(r['slug'])

# cities.csv
src = [r['geonameid'] for r in csv.DictReader(open(WORLD / 'names' / 'cities.csv'))]
rows = list(csv.DictReader(open(HERE / 'cities.csv')))
if rows and list(rows[0]) != ['geonameid', 'name', 'in_phrase', 'decl_ok', 'note']:
    err.append('cities: header')
ids = [r['geonameid'] for r in rows]
if len(set(ids)) != len(ids):
    err.append('cities: duplicate geonameid')
if set(ids) - set(src):
    err.append(f'cities: unknown geonameid {len(set(ids) - set(src))}')
for r in rows:
    if not r['name'].strip() or not r['in_phrase'].strip() or r['decl_ok'] not in ('0', '1'):
        err.append(f"cities {r['geonameid']}: empty field or bad decl_ok")

print(f'L-{LANG.upper()}: cities {len(rows)}/{len(src)}, decl_ok=1 {sum(r["decl_ok"] == "1" for r in rows)}')
for e in err:
    print('ERR', e)
print('OK' if not err else f'{len(err)} errors')
sys.exit(1 if err else 0)
