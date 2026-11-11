#!/usr/bin/env python3
"""L-TR / L2-TR: check content/world/i18n/tr against the EN sources. Run from repo root or anywhere."""
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
      'strings_shell': {'pl_loc','pl_cc'}, 'strings_home': {'pl_places','pl_countries','pl_public'}}
# FIXL: {name_nom} may stand where EN has {name}; {city_u}/{country_u} where EN has {city}/{country}
EQUIV = {'{name_nom}': '{name}', '{city_u}': '{city}', '{country_u}': '{country}'}
def same(a, b, where):
    for name, rx in (('placeholders', PH), ('tags', TAG), ('entities', ENT)):
        got = [EQUIV.get(x, x) if name == 'placeholders' and EQUIV.get(x) in rx.findall(a) else x for x in rx.findall(b)]
        if sorted(rx.findall(a)) != sorted(got):
            err.append(f'{where}: {name} differ EN={sorted(rx.findall(a))} TR={sorted(rx.findall(b))}')
FILES = ('strings_map', 'strings_pages', 'strings_shell', 'strings_prices', 'strings_pay', 'strings_press', 'strings_b2b', 'strings_embed', 'strings_home')
for f in FILES:
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
if sorted(t) != ['about_data', 'download', 'pay', 'routes']: err.append(f'texts: sections {sorted(t)}')
walk({'about_data': json.load(open(W / 'about_data.json'))['en'], 'download': json.load(open(W / 'download.json'))['en']},
     {k: t.get(k) for k in ('about_data', 'download')}, '')
# texts.json pay/routes (LANG0 format): dotted path of each multilingual node -> text
def ml_nodes(o, p, out):
    if isinstance(o, dict):
        if isinstance(o.get('en'), str) and ('sr' in o or 'ru' in o): out[p] = o['en']; return
        for k, v in o.items(): ml_nodes(v, f'{p}.{k}' if p else k, out)
    elif isinstance(o, list):
        for i, v in enumerate(o): ml_nodes(v, f'{p}[{i}]', out)
for sec, fn in (('pay', 'pay.json'), ('routes', 'routes.json')):
    want = {}; ml_nodes(json.load(open(W / fn)), '', want); got = t.get(sec, {})
    for k in set(want) - set(got): err.append(f'texts.{sec}: missing {k}')
    for k in set(got) - set(want): err.append(f'texts.{sec}: extra {k}')
    for k, v in got.items():
        if k not in want: continue
        if not isinstance(v, str) or not v.strip(): err.append(f'texts.{sec}.{k}: empty'); continue
        same(want[k], v, f'texts.{sec}.{k}')
# slugs
KEYS = ['home','map','hub','net','about','download','gnet','prices','shell_about','sources','methodology']
SECTION = ['pay','routes','press','b2b','embed','map_conf','developers']   # FIXL F5: optional, full paths (embed has two segments)
s = json.load(open(HERE / 'slugs.json'))
if not set(KEYS) <= set(s) <= set(KEYS) | set(SECTION): err.append('slugs: keys differ')
for k, v in s.items():
    if k in SECTION:
        if not re.fullmatch(rf'/{LANG}/([a-z0-9]+(-[a-z0-9]+)*/)+', v): err.append(f'slugs.{k}: bad path {v}')
    elif k in ('net','about','download'):
        if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', v): err.append(f'slugs.{k}: bad segment {v}')
    elif not re.fullmatch(rf'/{LANG}/([a-z0-9]+(-[a-z0-9]+)*/)?', v): err.append(f'slugs.{k}: bad path {v}')
if len(set(s.values())) != len(s): err.append('slugs: duplicates')
# countries
en_c = {r['cc'] for r in csv.DictReader(open(W / 'names' / 'countries.csv'))}
rows = list(csv.DictReader(open(HERE / 'countries.csv')))
if [*rows[0]] not in (['cc','name','slug','in_phrase','note'], ['cc','name','slug','in_phrase','note','name_nom']): err.append('countries: header')
if {r['cc'] for r in rows} != en_c: err.append('countries: cc set differs')
sl = [r['slug'] for r in rows]
if len(set(sl)) != len(sl): err.append('countries: duplicate slugs')
for r in rows:
    if not (r['name'] and r['in_phrase']): err.append(f"countries {r['cc']}: empty")
    if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', r['slug']): err.append(f"countries {r['cc']}: bad slug")
# cities
ids = {r['geonameid'] for f in ('cities.csv', 'cities_extra.csv') for r in csv.DictReader(open(W / 'names' / f))}  # FIXL2: + cities_extra.csv
# FIXL F2: every geonameid must exist in names/cities.csv; every city page needs a row
_ps = json.load(open(W / 'state' / 'pages_state.json'))
page_ids = {v['key'].split(':')[2] for v in _ps.values() if v.get('type') == 'city' and str(v.get('key', '')).startswith('t:')}
for g in sorted(page_ids - {r['geonameid'] for r in csv.DictReader(open(HERE / 'cities.csv'))}): err.append(f'cities {g}: page city missing')
rows = list(csv.DictReader(open(HERE / 'cities.csv')))
if [*rows[0]] != ['geonameid','name','in_phrase','decl_ok','note']: err.append('cities: header')
seen = set()
for r in rows:
    g = r['geonameid']
    if g not in ids: err.append(f'cities {g}: unknown geonameid')
    if g in seen: err.append(f'cities {g}: duplicate')
    seen.add(g)
    if not (r['name'] and r['in_phrase']) or r['decl_ok'] not in ('0','1'): err.append(f'cities {g}: bad row')
print(f'cities: {len(rows)}/{len(ids)} covered (names/cities.csv + cities_extra.csv), decl_ok=1: {sum(r["decl_ok"]=="1" for r in rows)}')
print('\n'.join(err) if err else 'OK: 0 errors')
sys.exit(1 if err else 0)
