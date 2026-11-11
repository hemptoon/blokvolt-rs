#!/usr/bin/env python3
"""Checks the Slovenian (sl) world-layer localisation against the EN sources.

Run from the repo root:  python3 content/world/i18n/sl/check.py
Exit code 0 = no errors. Warnings are informational.
"""
import csv, json, os, re, sys

LANG = 'sl'
HERE = os.path.dirname(os.path.abspath(__file__))
WORLD = os.path.normpath(os.path.join(HERE, '..', '..'))
STRINGS = ['strings_map', 'strings_pages', 'strings_shell', 'strings_prices',
           'strings_pay', 'strings_press', 'strings_b2b', 'strings_embed', 'strings_home']   # FIXL: + home (HOME2)
SLUG_KEYS = ['home', 'map', 'hub', 'net', 'about', 'download', 'gnet', 'prices', 'shell_about', 'sources', 'methodology']
SECTION_KEYS = ['pay', 'routes', 'press', 'b2b', 'embed', 'map_conf', 'developers']   # FIXL F5: optional section paths
FULL_PATH = {'home', 'map', 'hub', 'gnet', 'prices', 'shell_about', 'sources', 'methodology'} | set(SECTION_KEYS)
PH = re.compile(r'\{[a-zA-Z0-9_]*\}')
TAG = re.compile(r'</?[a-zA-Z][^>]*>')
ENT = re.compile(r'&[a-zA-Z#0-9]+;')
FORBIDDEN = [r'24/7', r'\btakoj\b', r'Evolako', r'!', r'\bmi\b', r'\bnaš[aeiou]?\b', r'uredništv', r'\bekipa\b']

errors, warns = [], []
def err(m): errors.append(m)
def warn(m): warns.append(m)

def cldr_tags():
    try:
        from babel import Locale
        return set(Locale(LANG).plural_form.tags) | {'other'}
    except Exception as e:  # babel missing: fixed CLDR set for sl
        warn(f'babel not available ({e}); using built-in CLDR set')
        return {'one', 'two', 'few', 'other'}

def tags(s): return sorted(TAG.findall(s))
def phs(s): return sorted(x.replace('{name_nom}', '{name}') for x in PH.findall(s))   # FIXL D14: {name_nom} may stand for {name}

def check_text(where, en, tr, alt_ph=None):
    if not isinstance(tr, str) or not tr.strip():
        err(f'{where}: empty or not a string'); return
    if tags(en) != tags(tr): err(f'{where}: HTML tags differ: {tags(en)} vs {tags(tr)}')
    if sorted(ENT.findall(en)) != sorted(ENT.findall(tr)): err(f'{where}: HTML entities differ')
    pe, pt = phs(en), phs(tr)
    if pe != pt:
        # allowed only if SR or RU of the same key uses the same placeholder set (e.g. {city_u})
        if alt_ph and sorted(pt) in alt_ph: warn(f'{where}: placeholders {pt} differ from EN {pe} (same as SR/RU — OK)')
        else: err(f'{where}: placeholders differ: EN {pe} vs {pt}')
    if en.endswith(' | BlokVolt') and not tr.endswith(' | BlokVolt'): err(f'{where}: lost " | BlokVolt" tail')
    for f in FORBIDDEN:
        if re.search(f, tr, re.I) and not re.search(f, en, re.I): err(f'{where}: forbidden pattern {f!r}')

tags_cldr = cldr_tags()
for name in STRINGS:
    src = json.load(open(os.path.join(WORLD, name + '.json'), encoding='utf-8'))
    p = os.path.join(HERE, name + '.json')
    if not os.path.exists(p): err(f'{name}: file missing'); continue
    tr = json.load(open(p, encoding='utf-8'))
    for k in src:
        if k not in tr: err(f'{name}.{k}: missing'); continue
        v = tr[k]; en = src[k]['en']
        if k.startswith('pl_'):
            if not isinstance(v, dict): err(f'{name}.{k}: plural must be an object'); continue
            if set(v) != tags_cldr: err(f'{name}.{k}: plural categories {sorted(v)} != CLDR {sorted(tags_cldr)}')
            for c, s in v.items():
                if not isinstance(s, str) or not s.strip(): err(f'{name}.{k}.{c}: empty')
        else:
            alt = [sorted(phs(src[k][x])) for x in ('sr', 'ru') if x in src[k]]
            check_text(f'{name}.{k}', en, v, alt)
    for k in tr:
        if k not in src: err(f'{name}.{k}: extra key not in EN')

# texts.json — same structure as the "en" part of about_data.json / download.json
def walk(where, en, tr):
    if isinstance(en, dict):
        if not isinstance(tr, dict): err(f'{where}: expected object'); return
        for k in en:
            if k not in tr: err(f'{where}.{k}: missing')
            else: walk(f'{where}.{k}', en[k], tr[k])
        for k in tr:
            if k not in en: err(f'{where}.{k}: extra key')
    elif isinstance(en, list):
        if not isinstance(tr, list) or len(tr) != len(en): err(f'{where}: list length differs'); return
        for i, (a, b) in enumerate(zip(en, tr)): walk(f'{where}[{i}]', a, b)
    elif isinstance(en, str):
        check_text(where, en, tr)
    elif en != tr:
        err(f'{where}: non-text value changed')

texts = json.load(open(os.path.join(HERE, 'texts.json'), encoding='utf-8'))
for name in ('about_data', 'download'):
    src = json.load(open(os.path.join(WORLD, name + '.json'), encoding='utf-8'))['en']
    if name not in texts: err(f'texts.{name}: missing')
    else: walk(f'texts.{name}', src, texts[name])

# texts.json → pay / routes (LANG0 format: dotted path of a multilingual node -> text)
def ml_nodes(n, p, acc):
    if isinstance(n, dict):
        if isinstance(n.get('en'), str) and isinstance(n.get('sr'), str):
            acc[p] = n['en']; return
        for k, v in n.items(): ml_nodes(v, f'{p}.{k}' if p else k, acc)
    elif isinstance(n, list):
        for i, v in enumerate(n): ml_nodes(v, f'{p}[{i}]', acc)

for name in ('pay', 'routes'):
    src = {}
    ml_nodes(json.load(open(os.path.join(WORLD, name + '.json'), encoding='utf-8')), '', src)
    tr = texts.get(name)
    if not isinstance(tr, dict): err(f'texts.{name}: missing'); continue
    for k, en in src.items():
        if k not in tr: err(f'texts.{name}.{k}: missing')
        else: check_text(f'texts.{name}.{k}', en, tr[k])
    for k in tr:
        if k not in src: err(f'texts.{name}.{k}: extra key (no such node)')

# slugs.json
slugs = json.load(open(os.path.join(HERE, 'slugs.json'), encoding='utf-8'))
if not set(SLUG_KEYS) <= set(slugs) <= set(SLUG_KEYS) | set(SECTION_KEYS):
    err(f'slugs: keys {sorted(slugs)}: need {sorted(SLUG_KEYS)}, may add {sorted(SECTION_KEYS)}')
for k, v in slugs.items():
    if k in FULL_PATH:
        if not re.fullmatch(rf'/{LANG}/([a-z0-9]+(-[a-z0-9]+)*/)*', v): err(f'slugs.{k}: bad path {v!r}')
    elif not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', v): err(f'slugs.{k}: bad segment {v!r}')
paths = [v for k, v in slugs.items() if k in FULL_PATH]
if len(paths) != len(set(paths)): err('slugs: duplicate paths')

# countries.csv
src_cc = [r['cc'] for r in csv.DictReader(open(os.path.join(WORLD, 'names', 'countries.csv'), encoding='utf-8'))]
rows = list(csv.DictReader(open(os.path.join(HERE, 'countries.csv'), encoding='utf-8')))
if rows and list(rows[0].keys()) not in (['cc', 'name', 'slug', 'in_phrase', 'note'], ['cc', 'name', 'slug', 'in_phrase', 'note', 'name_nom']):
    err('countries.csv: wrong columns')   # FIXL D4: an extra last column name_nom is allowed
if sorted(r['cc'] for r in rows) != sorted(src_cc): err('countries.csv: country set differs from names/countries.csv')
for r in rows:
    if not r['name'] or not r['in_phrase']: err(f"countries.csv {r['cc']}: empty name/in_phrase")
    if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', r['slug']): err(f"countries.csv {r['cc']}: bad slug")
    if not re.match(r'^(v|na) ', r['in_phrase']): warn(f"countries.csv {r['cc']}: in_phrase without v/na")
if len({r['slug'] for r in rows}) != len(rows): err('countries.csv: duplicate slugs')

# cities.csv
src_ids = {r['geonameid'] for r in csv.DictReader(open(os.path.join(WORLD, 'names', 'cities.csv'), encoding='utf-8'))}
# FIXL: every geonameid must exist in names/cities.csv; every city page of pages_state must have a row
_ps = os.path.join(WORLD, 'state', 'pages_state.json')
page_ids = set()
if os.path.exists(_ps):
    for _v in json.load(open(_ps, encoding='utf-8')).values():
        if _v.get('type') == 'city' and str(_v.get('key', '')).startswith('t:'): page_ids.add(_v['key'].split(':')[-1])
crow = list(csv.DictReader(open(os.path.join(HERE, 'cities.csv'), encoding='utf-8')))
if crow and list(crow[0].keys()) != ['geonameid', 'name', 'in_phrase', 'decl_ok', 'note']: err('cities.csv: wrong columns')
ids = [r['geonameid'] for r in crow]
if len(ids) != len(set(ids)): err('cities.csv: duplicate geonameid')
unknown = set(ids) - src_ids
for g in sorted(page_ids - set(ids)): err(f'cities.csv: city with a page missing: {g}')
if unknown: err(f'cities.csv: {len(unknown)} geonameid not in names/cities.csv')
for r in crow:
    if not r['name'] or not r['in_phrase']: err(f"cities.csv {r['geonameid']}: empty")
    if r['decl_ok'] not in ('0', '1'): err(f"cities.csv {r['geonameid']}: decl_ok must be 0/1")
    if not re.match(r'^(v|na) ', r['in_phrase']): err(f"cities.csv {r['geonameid']}: in_phrase without v/na")
cov = len(set(ids)) / len(src_ids) * 100

print(f'sl check: {len(errors)} errors, {len(warns)} warnings; cities {len(crow)}/{len(src_ids)} ({cov:.0f} %), '
      f"decl_ok=1: {sum(r['decl_ok'] == '1' for r in crow)}")
for w in warns: print('WARN', w)
for e in errors: print('ERR ', e)
sys.exit(1 if errors else 0)
