#!/usr/bin/env python3
"""Check of the Macedonian (mk) world-layer localisation (contract of L-tasks, pool 3).
Run from the repo root:  python3 content/world/i18n/mk/check.py"""
import csv, json, re, sys
from pathlib import Path

LANG = 'mk'
HERE = Path(__file__).resolve().parent
WORLD = HERE.parent.parent
PL_KEYS = {'strings_pages': {'pl_city', 'pl_city_in', 'pl_country', 'pl_country_in', 'pl_loc', 'pl_net',
                             'pl_place', 'pl_point', 'pl_publoc'},
           'strings_shell': {'pl_loc', 'pl_cc'}}
SLUG_KEYS = ['home', 'map', 'hub', 'net', 'about', 'download', 'gnet', 'prices', 'shell_about', 'sources', 'methodology']
# FIXL (11.11.2026): section paths the engine reads, optional in addition to the 11 required keys
SECTION_KEYS = ['pay', 'routes', 'press', 'b2b', 'embed', 'map_conf', 'developers']
FULL = {'home', 'map', 'hub', 'gnet', 'prices', 'shell_about', 'sources', 'methodology'} | set(SECTION_KEYS)
errs, warns = [], []
PH = re.compile(r'\{[a-z_0-9]*\}')
TAG = re.compile(r'</?[a-z][^>]*>|&[a-z#0-9]+;')


def cats():
    try:
        from babel import Locale
        return set(Locale(LANG).plural_form.tags) | {'other'}
    except Exception as e:  # babel missing
        warns.append(f'babel not available ({e}); using CLDR mk = one, other')
        return {'one', 'other'}


def norm_ph(xs):
    # FIXL: {name_nom} may stand where EN has {name}; {city_u}/{country_u} where EN has {city}/{country}
    return sorted(x.replace('{name_nom}', '{name}').replace('_u}', '}') for x in xs)


def same_marks(en, tr, where):
    if norm_ph(PH.findall(en)) != norm_ph(PH.findall(tr)):
        errs.append(f'{where}: placeholders {PH.findall(en)} != {PH.findall(tr)}')
    if sorted(TAG.findall(en)) != sorted(TAG.findall(tr)):
        errs.append(f'{where}: tags/entities differ')
    if not tr.strip():
        errs.append(f'{where}: empty')
    if en.endswith(' | BlokVolt') != tr.endswith(' | BlokVolt'):
        errs.append(f'{where}: " | BlokVolt" tail differs')
    if re.search(r'24/7|\bнаш[аиео]?\b|\bние\b|редакција', tr, re.I):
        errs.append(f'{where}: forbidden word (24/7, first person, редакција)')
    if 'Evolako' in tr:
        errs.append(f'{where}: Evolako in the world layer')


C = cats()
n_str = 0
FILES = ['strings_map', 'strings_pages', 'strings_shell', 'strings_prices',
         'strings_pay', 'strings_press', 'strings_b2b', 'strings_embed',  # L2: all 8 files
         'strings_home']  # FIXL: home page (HOME2)
for f in FILES:
    en = json.load(open(WORLD / f'{f}.json'))
    if not (HERE / f'{f}.json').exists():
        errs.append(f'{f}: file missing'); continue
    tr = json.load(open(HERE / f'{f}.json'))
    for k in en.keys() - tr.keys():
        errs.append(f'{f}: missing key {k}')
    for k in tr.keys() - en.keys():
        errs.append(f'{f}: extra key {k}')
    for k, v in tr.items():
        if k not in en:
            continue
        e = en[k]['en']
        n_str += 1
        if k in PL_KEYS.get(f, set()) or k.startswith('pl_'):
            if not isinstance(v, dict) or set(v) != C:
                errs.append(f'{f}.{k}: plural object must have exactly {sorted(C)}')
            elif not all(isinstance(x, str) and x.strip() for x in v.values()):
                errs.append(f'{f}.{k}: empty plural form')
        else:
            if not isinstance(v, str):
                errs.append(f'{f}.{k}: must be a string')
                continue
            same_marks(e, v, f'{f}.{k}')

# texts.json — same structure as the EN parts
texts = json.load(open(HERE / 'texts.json'))


def walk(a, b, p):
    if type(a) is not type(b):
        errs.append(f'texts {p}: type differs'); return
    if isinstance(a, dict):
        if set(a) != set(b):
            errs.append(f'texts {p}: keys differ {set(a) ^ set(b)}')
        for k in a.keys() & b.keys():
            walk(a[k], b[k], f'{p}.{k}')
    elif isinstance(a, list):
        if len(a) != len(b):
            errs.append(f'texts {p}: length differs')
        for i, (x, y) in enumerate(zip(a, b)):
            walk(x, y, f'{p}[{i}]')
    elif isinstance(a, str):
        same_marks(a, b, f'texts {p}')
        if a.startswith('http') and a != b:
            errs.append(f'texts {p}: URL changed')


for part in ['about_data', 'download']:
    walk(json.load(open(WORLD / f'{part}.json'))['en'], texts.get(part), part)


# L2 / LANG0: texts.json -> pay, routes = {dotted path of a multilingual node: text}
def nodes(o, p, out):
    if isinstance(o, dict):
        if 'en' in o and 'sr' in o and all(isinstance(v, str) for v in o.values()):
            out[p] = o['en']; return
        for k, v in o.items():
            nodes(v, f'{p}.{k}' if p else k, out)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            nodes(v, f'{p}[{i}]', out)


n_data = 0
for part in ['pay', 'routes']:
    want = {}
    nodes(json.load(open(WORLD / f'{part}.json')), '', want)
    got_t = texts.get(part)
    if not isinstance(got_t, dict):
        errs.append(f'texts.{part}: section missing'); continue
    for k in want.keys() - got_t.keys():
        errs.append(f'texts.{part}: missing node {k}')
    for k in got_t.keys() - want.keys():
        errs.append(f'texts.{part}: unknown node {k}')
    for k in want.keys() & got_t.keys():
        n_data += 1
        if not isinstance(got_t[k], str):
            errs.append(f'texts.{part}.{k}: must be a string'); continue
        same_marks(want[k], got_t[k], f'texts.{part}.{k}')
        if part == 'routes' and re.search(r'[A-Za-z]', got_t[k]):
            warns.append(f'texts.routes.{k}: Latin letters {got_t[k]}')

# slugs.json
sl = json.load(open(HERE / 'slugs.json'))
if not set(SLUG_KEYS) <= set(sl) <= set(SLUG_KEYS) | set(SECTION_KEYS):
    errs.append(f'slugs: keys must be {SLUG_KEYS}, optionally plus {SECTION_KEYS}')
for k, v in sl.items():
    if k in FULL:
        if not re.fullmatch(r'/mk/([a-z0-9]+(-[a-z0-9]+)*/)*', v):
            errs.append(f'slugs.{k}: full ASCII path with /mk/ prefix expected, got {v}')
    elif not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', v):
        errs.append(f'slugs.{k}: one ASCII segment expected, got {v}')
full = [v for k, v in sl.items() if k in FULL]
if len(full) != len(set(full)):
    errs.append('slugs: duplicate paths')
# paths of the existing local section /mk/ (content/com/local/mk) must not be reused
local = {'/mk/'} | {'/mk/' + m.group(1) for p in (WORLD.parent / 'com/local/mk').glob('*.md')
                    for m in [re.search(r'^slug:\s*(\S+)', p.read_text(), re.M)] if m}
for k, v in sl.items():
    if k in FULL and v in local:
        errs.append(f'slugs.{k}: {v} collides with the local section /mk/')

# countries.csv
src_c = {r['cc'] for r in csv.DictReader(open(WORLD / 'names/countries.csv'))}
rows = list(csv.DictReader(open(HERE / 'countries.csv')))
if [*rows[0].keys()] not in (['cc', 'name', 'slug', 'in_phrase', 'note'], ['cc', 'name', 'slug', 'in_phrase', 'note', 'name_nom']):
    errs.append('countries.csv: header must be cc,name,slug,in_phrase,note[,name_nom]')
got = {r['cc'] for r in rows}
if got != src_c:
    errs.append(f'countries.csv: cc differ {sorted(got ^ src_c)}')
slugs = [r['slug'] for r in rows]
if len(slugs) != len(set(slugs)):
    errs.append('countries.csv: duplicate slugs')
for r in rows:
    if not r['name'].strip() or not r['in_phrase'].strip():
        errs.append(f"countries.csv {r['cc']}: empty name or in_phrase")
    if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', r['slug']):
        errs.append(f"countries.csv {r['cc']}: slug not ASCII: {r['slug']}")
    # mk: plural/compound names take the definite article after a preposition
    # (во Обединетите Арапски Емирати) — accept when every word's stem is present
    if r['name'] not in r['in_phrase'] and not all(w[:-2] in r['in_phrase'] for w in r['name'].split()):
        warns.append(f"countries.csv {r['cc']}: name not inside in_phrase")

# cities.csv
src = {r['geonameid'] for r in csv.DictReader(open(WORLD / 'names/cities.csv'))}
# FIXL2: cities from names/cities_extra.csv are allowed too
if (WORLD / 'names/cities_extra.csv').exists():
    src |= {r['geonameid'] for r in csv.DictReader(open(WORLD / 'names/cities_extra.csv'))}
rows = list(csv.DictReader(open(HERE / 'cities.csv')))
if [*rows[0].keys()] != ['geonameid', 'name', 'in_phrase', 'decl_ok', 'note']:
    errs.append('cities.csv: header must be geonameid,name,in_phrase,decl_ok,note')
ids = [r['geonameid'] for r in rows]
if len(ids) != len(set(ids)):
    errs.append('cities.csv: duplicate geonameid')
if set(ids) - src:
    errs.append(f'cities.csv: unknown geonameid {sorted(set(ids) - src)[:5]}')
# FIXL: every city page of state/pages_state.json must have a row
st = WORLD / 'state/pages_state.json'
if st.exists():
    page_ids = {v['key'].split(':')[-1] for v in json.load(open(st)).values() if v.get('type') == 'city'}
    lost = page_ids - set(ids)
    if lost:
        errs.append(f'cities.csv: city pages without a row {sorted(lost)[:10]} ({len(lost)})')
for r in rows:
    if not r['name'].strip() or not r['in_phrase'].strip() or r['decl_ok'] not in ('0', '1'):
        errs.append(f"cities.csv {r['geonameid']}: empty name/in_phrase or bad decl_ok")
    if re.search(r'[A-Za-z]', r['name']) and 'latin' not in r['note']:
        warns.append(f"cities.csv {r['geonameid']}: Latin letters in name {r['name']}")

print(f'mk: {n_str} strings, {len(texts)} texts ({n_data} data nodes), {len(sl)} slugs, {len(got)} countries, '
      f'{len(rows)} cities of {len(src)}; plural categories {sorted(C)}')
for w in warns[:30]:
    print('WARN', w)
for e in errs:
    print('ERR ', e)
print(f'{len(errs)} errors, {len(warns)} warnings')
sys.exit(1 if errs else 0)
