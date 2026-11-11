#!/usr/bin/env python3
"""L-HU / L2-HU self-check (8 string files + texts.json about_data, download, pay, routes): python3 content/world/i18n/hu/check.py  (from the repo root). Exit 1 on any error."""
import csv, json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LANG = HERE.name
WORLD = HERE.parent.parent
errs, warns = [], []
PH = re.compile(r'\{[a-z_0-9]*\}')
TAG = re.compile(r'</?[a-zA-Z][^>]*>|&[a-z#0-9]+;')
ALIASES = {'{city}': {'{city_u}'}, '{country}': {'{country_u}'}, '{name}': {'{name_nom}'}}   # same slot, other case (as sr/ru do); FIXL D14: {name_nom}
ALLOWED_EXTRA = {'t_city': {'{city_u}'}, 't_city_cc': {'{city_u}'}, 'd_city': {'{city_u}'}}

try:
    from babel import Locale
    CATS = set(Locale(LANG).plural_form.tags) | {'other'}
except Exception as e:   # babel missing
    CATS = {'one', 'other'}
    warns.append(f'babel unavailable ({e}); assuming {CATS}')

FILES = ('strings_map', 'strings_pages', 'strings_shell', 'strings_prices', 'strings_pay', 'strings_press', 'strings_b2b', 'strings_embed',
         'strings_home')  # FIXL F3
FORBID = re.compile(r'24/7|\bmink\b|\bnálunk\b|\bnekünk\b|\brólunk\b|\bminket\b|szerkesztőség|Evolako', re.I)
for f in FILES:
    if not (HERE / f'{f}.json').exists():
        errs.append(f'{f}.json missing'); continue
    en = {k: v['en'] for k, v in json.load(open(WORLD / f'{f}.json', encoding='utf-8')).items()}
    tr = json.load(open(HERE / f'{f}.json', encoding='utf-8'))
    for k in en.keys() - tr.keys():
        errs.append(f'{f}: missing key {k}')
    for k in tr.keys() - en.keys():
        errs.append(f'{f}: extra key {k}')
    for k in en.keys() & tr.keys():
        e, t = en[k], tr[k]
        if k.startswith('pl_'):
            if not isinstance(t, dict):
                errs.append(f'{f}.{k}: plural must be an object'); continue
            if set(t) != CATS:
                errs.append(f'{f}.{k}: plural categories {sorted(t)} != CLDR {sorted(CATS)}')
            if any(not str(x).strip() for x in t.values()):
                errs.append(f'{f}.{k}: empty plural form')
            continue
        if not isinstance(t, str) or not t.strip():
            errs.append(f'{f}.{k}: empty or not a string'); continue
        pe, pt = set(PH.findall(e)), set(PH.findall(t))
        missing = {p for p in pe - pt if not (ALIASES.get(p, set()) & pt)}
        extra = pt - pe - ALLOWED_EXTRA.get(k, set()) - {a for p in pe for a in ALIASES.get(p, set())}
        if missing or extra:
            errs.append(f'{f}.{k}: placeholders missing {sorted(missing)} extra {sorted(extra)}')
        if sorted(TAG.findall(e)) != sorted(TAG.findall(t)):
            errs.append(f'{f}.{k}: HTML tags/entities differ')
        if e.endswith(' | BlokVolt') and not t.endswith(' | BlokVolt'):
            errs.append(f'{f}.{k}: lost " | BlokVolt" tail')
        if FORBID.search(t):
            errs.append(f'{f}.{k}: forbidden word (24/7, first person plural, szerkesztőség, Evolako)')


def walk(a, b, path):
    if isinstance(a, dict):
        if not isinstance(b, dict) or set(a) != set(b):
            errs.append(f'texts {path}: keys differ'); return
        for k in a:
            walk(a[k], b[k], f'{path}.{k}')
    elif isinstance(a, list):
        if not isinstance(b, list) or len(a) != len(b):
            errs.append(f'texts {path}: list length differs'); return
        for i, (x, y) in enumerate(zip(a, b)):
            walk(x, y, f'{path}[{i}]')
    elif isinstance(a, str):
        if not isinstance(b, str) or (a.strip() and not b.strip()):
            errs.append(f'texts {path}: empty'); return
        if set(PH.findall(a)) != set(PH.findall(b)):
            errs.append(f'texts {path}: placeholders differ')
        if sorted(TAG.findall(a)) != sorted(TAG.findall(b)):
            errs.append(f'texts {path}: HTML differs')


texts = json.load(open(HERE / 'texts.json', encoding='utf-8'))
for name in ('about_data', 'download'):
    src = json.load(open(WORLD / f'{name}.json', encoding='utf-8'))['en']
    walk(src, texts.get(name), name)



def ml_nodes(x, p, out):
    """Multilingual nodes of pay.json / routes.json: dicts with an 'en' string plus sr/ru; key = dotted path, [i] for list items."""
    if isinstance(x, dict):
        if isinstance(x.get('en'), str) and ('sr' in x or 'ru' in x):
            out[p] = x['en']; return out
        for k, v in x.items():
            ml_nodes(v, f'{p}.{k}' if p else k, out)
    elif isinstance(x, list):
        for i, v in enumerate(x):
            ml_nodes(v, f'{p}[{i}]', out)
    return out


for name in ('pay', 'routes'):
    src = ml_nodes(json.load(open(WORLD / f'{name}.json', encoding='utf-8')), '', {})
    got = texts.get(name)
    if not isinstance(got, dict):
        errs.append(f'texts.{name}: section missing'); continue
    for k in src.keys() - got.keys():
        errs.append(f'texts.{name}: missing {k}')
    for k in got.keys() - src.keys():
        errs.append(f'texts.{name}: extra {k}')
    for k in src.keys() & got.keys():
        a, b = src[k], got[k]
        if not isinstance(b, str) or not b.strip():
            errs.append(f'texts.{name}.{k}: empty'); continue
        if set(PH.findall(a)) != set(PH.findall(b)):
            errs.append(f'texts.{name}.{k}: placeholders differ')
        if sorted(TAG.findall(a)) != sorted(TAG.findall(b)):
            errs.append(f'texts.{name}.{k}: HTML differs')
        if FORBID.search(b):
            errs.append(f'texts.{name}.{k}: forbidden word')

SLUG_KEYS = ['home', 'map', 'hub', 'net', 'about', 'download', 'gnet', 'prices', 'shell_about', 'sources', 'methodology']
SLUG_EXTRA = ['pay', 'routes', 'press', 'b2b', 'embed', 'map_conf', 'developers']  # FIXL F5: allowed in addition
sl = json.load(open(HERE / 'slugs.json', encoding='utf-8'))
if set(SLUG_KEYS) - set(sl) or set(sl) - set(SLUG_KEYS) - set(SLUG_EXTRA):
    errs.append(f'slugs.json keys {sorted(sl)}')
for k, v in sl.items():
    if k in ('net', 'about', 'download'):
        if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', v):
            errs.append(f'slug {k}={v!r} must be one ASCII segment')
    elif not re.fullmatch(rf'/{LANG}/([a-z0-9]+(-[a-z0-9]+)*/)' + ('*' if k in SLUG_EXTRA else '?'), v):
        errs.append(f'slug {k}={v!r} must be /{LANG}/…/ ASCII')
if len(set(sl.values())) != len(sl):
    errs.append('slugs: duplicate values')

def rows(p, cols, alt=None):
    with open(p, encoding='utf-8', newline='') as fh:
        r = list(csv.DictReader(fh))
    if not r or list(r[0].keys()) not in (cols, alt):
        errs.append(f'{p.name}: columns != {cols}')
    return r

c = rows(HERE / 'countries.csv', ['cc', 'name', 'slug', 'in_phrase', 'note'], alt=['cc', 'name', 'slug', 'in_phrase', 'note', 'name_nom'])  # FIXL D4
base = {r['cc'] for r in csv.DictReader(open(WORLD / 'names' / 'countries.csv', encoding='utf-8'))}
if {r['cc'] for r in c} != base:
    errs.append(f'countries.csv: cc set differs from names/countries.csv ({len(c)} vs {len(base)})')
seen = set()
for r in c:
    if not all(r[k].strip() for k in ('name', 'slug', 'in_phrase')):
        errs.append(f'countries {r["cc"]}: empty field')
    if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', r['slug']):
        errs.append(f'countries {r["cc"]}: slug not ASCII')
    if r['slug'] in seen:
        errs.append(f'countries {r["cc"]}: duplicate slug')
    seen.add(r['slug'])

ci = rows(HERE / 'cities.csv', ['geonameid', 'name', 'in_phrase', 'decl_ok', 'note'])
gids = {r['geonameid'] for r in csv.DictReader(open(WORLD / 'names' / 'cities.csv', encoding='utf-8'))}
bad = [r['geonameid'] for r in ci if r['geonameid'] not in gids]
if bad:
    errs.append(f'cities.csv: {len(bad)} geonameids not in names/cities.csv')
if len({r['geonameid'] for r in ci}) != len(ci):
    errs.append('cities.csv: duplicate geonameid')
for r in ci:
    if not r['name'].strip() or not r['in_phrase'].strip() or r['decl_ok'] not in ('0', '1'):
        errs.append(f'cities {r["geonameid"]}: bad row')
ok1 = sum(r['decl_ok'] == '1' for r in ci)
# FIXL F2: every city page of pages_state must have a row
PS = json.load(open(WORLD / 'state' / 'pages_state.json', encoding='utf-8'))
miss = {v['key'].split(':')[2] for v in PS.values() if v.get('type') == 'city'} - {r['geonameid'] for r in ci}
if miss:
    errs.append(f'cities.csv: {len(miss)} city pages missing: {sorted(miss)[:10]}')

print(f'{LANG}: strings ok ({len(FILES)} files), texts: ' + ', '.join(k for k in texts) if not [e for e in errs if not e.startswith(("texts", "slug", "countries", "cities"))] else '')
print(f'countries {len(c)}, cities {len(ci)} of {len(gids)} (decl_ok=1: {ok1}), plural categories {sorted(CATS)}')
for w in warns:
    print('WARN', w)
for e in errs:
    print('ERR ', e)
print('OK' if not errs else f'{len(errs)} errors')
sys.exit(1 if errs else 0)
