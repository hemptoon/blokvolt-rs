#!/usr/bin/env python3
"""Check of the L-task i18n package (content/world/i18n/<code>/).
Usage: python3 content/world/i18n/it/check.py [code]  (default: the folder name)"""
import csv, json, re, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
LANG = sys.argv[1] if len(sys.argv) > 1 else HERE.name
WORLD = HERE.parent.parent
errs, warns = [], []
PH = re.compile(r'\{[^{}]*\}'); TAG = re.compile(r'</?[a-zA-Z][^>]*>|&[a-zA-Z#0-9]+;')
# pool 4 (10.11.2026): {city_u}/{country_u} may replace {city}/{country}/{country_name} where a preposition+case is needed
# FIXL (11.11.2026, D14): {name_nom} (country name with article, countries.csv:name_nom) may stand where EN has {name}
_U = {'{city_u}': '{city}', '{country_u}': '{country}', '{name_nom}': '{name}'}
def toks(s, rx): return sorted(_U.get(t, t) for t in rx.findall(s))
def toks_en(s, rx): return sorted({'{country_name}': '{country}'}.get(t, t) for t in toks(s, rx))
try:
    from babel import Locale
    CATS = set(Locale(LANG).plural_form.tags) | {'other'}
except Exception as e:
    CATS = None; warns.append(f'babel unavailable: {e}')
PLURAL_KEYS = lambda en: en.count('|') == 2 and '{' not in en and ' | ' not in en

# L2 (11.11.2026): all 8 string files
FORBID = [r'\bnoi\b', r'\bnostr[aoie]\b', r'\bredazion', r'24/7', r'\bsubito\b', r'evolako', r'\bmi\s', r'\bscont[oi]\b']
def forbid(where, v):
    for pat in FORBID:
        if re.search(pat, v, re.I): errs.append(f'{where}: forbidden word ({pat})')
for name in ('map', 'pages', 'shell', 'prices', 'pay', 'press', 'b2b', 'embed', 'home'):   # FIXL: + strings_home
    src = json.load(open(WORLD / f'strings_{name}.json', encoding='utf-8'))
    p = HERE / f'strings_{name}.json'
    if not p.exists(): errs.append(f'{p.name}: missing'); continue
    tr = json.load(open(p, encoding='utf-8'))
    for k in src:
        if k not in tr: errs.append(f'{p.name}: key {k} missing'); continue
    for k in tr:
        if k not in src: errs.append(f'{p.name}: extra key {k}')
    for k, v in tr.items():
        if k not in src: continue
        en = src[k]['en']
        if PLURAL_KEYS(en):
            if not isinstance(v, dict): errs.append(f'{p.name}:{k}: plural must be an object'); continue
            if CATS is not None and set(v) != CATS: errs.append(f'{p.name}:{k}: categories {sorted(v)} != CLDR {sorted(CATS)}')
            if any(not str(x).strip() for x in v.values()): errs.append(f'{p.name}:{k}: empty plural form')
            continue
        if not isinstance(v, str) or not v.strip(): errs.append(f'{p.name}:{k}: empty or not a string'); continue
        forbid(f'{p.name}:{k}', v)
        if toks_en(v, PH) != toks_en(en, PH): errs.append(f'{p.name}:{k}: placeholders {toks(v,PH)} != {toks(en,PH)}')
        if toks(v, TAG) != toks(en, TAG): errs.append(f'{p.name}:{k}: tags/entities differ')
        if v.strip() == en.strip() and len(en) > 12: warns.append(f'{p.name}:{k}: identical to EN')

# texts.json vs EN parts of the long-text files
def en_part(x):
    if isinstance(x, dict):
        if 'en' in x and set(x) <= {'en', 'sr', 'ru'}: return x['en']
        return {k: en_part(v) for k, v in x.items()}
    return x
src = {n: en_part(json.load(open(WORLD / f'{n}.json', encoding='utf-8'))) for n in ('about_data', 'download', 'sources_pages')}
tp = HERE / 'texts.json'
if not tp.exists(): errs.append('texts.json: missing')
else:
    tr = json.load(open(tp, encoding='utf-8'))
    def walk(a, b, path):
        if type(a) is not type(b): errs.append(f'texts.json:{path}: type differs'); return
        if isinstance(a, dict):
            if list(a) != list(b): errs.append(f'texts.json:{path}: keys differ')
            for k in a:
                if k in b: walk(a[k], b[k], f'{path}.{k}')
        elif isinstance(a, list):
            if len(a) != len(b): errs.append(f'texts.json:{path}: list length differs')
            for i, (x, y) in enumerate(zip(a, b)): walk(x, y, f'{path}[{i}]')
        elif isinstance(a, str):
            if not b.strip() and a.strip(): errs.append(f'texts.json:{path}: empty')
            if toks(a, PH) != toks(b, PH): errs.append(f'texts.json:{path}: placeholders differ')
            if toks(a, TAG) != toks(b, TAG): errs.append(f'texts.json:{path}: tags differ')
        elif a != b: errs.append(f'texts.json:{path}: non-string value changed')
    walk(src, {k: tr.get(k) for k in src}, '')
    # L2: sections pay / routes = {dot.path[i]: text} for every multilingual node of pay.json / routes.json (LANG0 format)
    def nodes(o, path=''):
        if isinstance(o, dict):
            if isinstance(o.get('en'), str): yield path, o['en']; return
            for k, v in o.items(): yield from nodes(v, f'{path}.{k}' if path else k)
        elif isinstance(o, list):
            for i, v in enumerate(o): yield from nodes(v, f'{path}[{i}]')
    for sec in ('pay', 'routes'):
        want = dict(nodes(json.load(open(WORLD / f'{sec}.json', encoding='utf-8'))))
        got = tr.get(sec)
        if not isinstance(got, dict): errs.append(f'texts.json: section {sec} missing'); continue
        for k in want:
            if k not in got: errs.append(f'texts.json:{sec}.{k}: missing')
        for k, v in got.items():
            if k not in want: errs.append(f'texts.json:{sec}.{k}: extra (no such node)'); continue
            if not isinstance(v, str) or not v.strip(): errs.append(f'texts.json:{sec}.{k}: empty'); continue
            if toks(v, PH) != toks(want[k], PH): errs.append(f'texts.json:{sec}.{k}: placeholders differ')
            forbid(f'texts.json:{sec}.{k}', v)
    extra = set(tr) - set(src) - {'pay', 'routes'}
    if extra: errs.append(f'texts.json: unknown sections {sorted(extra)}')

# slugs.json
SLUG_KEYS = ['home', 'map', 'hub', 'net', 'about', 'download', 'gnet', 'prices', 'shell_about', 'sources', 'methodology']
SLUG_OPT = ['pay', 'routes', 'press', 'b2b', 'embed', 'map_conf', 'developers']   # FIXL F5: section paths, optional
sl = json.load(open(HERE / 'slugs.json', encoding='utf-8'))
if set(SLUG_KEYS) - set(sl) or set(sl) - set(SLUG_KEYS) - set(SLUG_OPT): errs.append(f'slugs.json: keys {sorted(sl)}')
for k, v in sl.items():
    if k in ('net', 'about', 'download'):
        if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', v): errs.append(f'slugs.json:{k}: bad segment {v!r}')
    elif not re.fullmatch(rf'/{LANG}/([a-z0-9]+(-[a-z0-9]+)*/)*', v): errs.append(f'slugs.json:{k}: bad path {v!r}')
paths = [v for k, v in sl.items() if k not in ('net', 'about', 'download')]
if len(set(paths)) != len(paths): errs.append('slugs.json: duplicate paths')

# countries.csv
names = list(csv.DictReader(open(WORLD / 'names/countries.csv', encoding='utf-8')))
cc_all = {r['cc'] for r in names}
rows = list(csv.DictReader(open(HERE / 'countries.csv', encoding='utf-8')))
# FIXL D14: optional last column name_nom (country as sentence subject, with article)
if rows and list(rows[0]) not in (['cc', 'name', 'slug', 'in_phrase', 'note'], ['cc', 'name', 'slug', 'in_phrase', 'note', 'name_nom']): errs.append('countries.csv: columns')
if {r['cc'] for r in rows} != cc_all: errs.append(f'countries.csv: cc set differs ({len(rows)} rows)')
for r in rows:
    if not r['name'] or not r['in_phrase']: errs.append(f'countries.csv:{r["cc"]}: empty')
    if 'name_nom' in r and not (r['name_nom'] or '').endswith(r['name']) and r['cc'] != 'MC': errs.append(f'countries.csv:{r["cc"]}: name_nom {r["name_nom"]!r} does not end with name')
    if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', r['slug']): errs.append(f'countries.csv:{r["cc"]}: slug {r["slug"]!r}')
if len({r['slug'] for r in rows}) != len(rows): errs.append('countries.csv: duplicate slugs')

# cities.csv
cg = {r['geonameid'] for r in csv.DictReader(open(WORLD / 'names/cities.csv', encoding='utf-8'))}
# FIXL2 (11.11.2026): rows may also come from names/cities_extra.csv
if (WORLD / 'names/cities_extra.csv').exists(): cg |= {r['geonameid'] for r in csv.DictReader(open(WORLD / 'names/cities_extra.csv', encoding='utf-8'))}
rows = list(csv.DictReader(open(HERE / 'cities.csv', encoding='utf-8')))
if rows and list(rows[0]) != ['geonameid', 'name', 'in_phrase', 'decl_ok', 'note']: errs.append('cities.csv: columns')
ids = [r['geonameid'] for r in rows]
if len(set(ids)) != len(ids): errs.append('cities.csv: duplicate geonameid')
if set(ids) - cg: errs.append(f'cities.csv: {len(set(ids)-cg)} unknown geonameid')
# FIXL F2: every city page of pages_state must have an Italian row
try:
    _ps = json.load(open(WORLD / 'state/pages_state.json', encoding='utf-8'))
    page_g = {v['key'].split(':')[2] for v in _ps.values() if v.get('type') == 'city'}
    nopage = sorted(page_g - set(ids))
    if nopage: errs.append(f'cities.csv: city pages without a row {nopage[:5]} ({len(nopage)})')
except Exception as e:
    warns.append(f'pages_state.json not readable ({e}): city pages not checked')
for r in rows:
    if not r['name'] or not r['in_phrase'] or r['decl_ok'] not in ('0', '1'): errs.append(f'cities.csv:{r["geonameid"]}: bad row')
print(f'L-{LANG.upper()} check: cities {len(rows)}/{len(cg)}; errors {len(errs)}, warnings {len(warns)}')
for e in errs[:50]: print('ERROR', e)
for w in warns[:50]: print('warn ', w)
sys.exit(1 if errs else 0)
