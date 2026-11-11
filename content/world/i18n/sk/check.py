#!/usr/bin/env python3
"""L-SK check: Slovak strings of the world layer against EN (contract of pool 3, L-tasks).

Run from anywhere:  python3 content/world/i18n/sk/check.py
Exit code 0 = no errors. Warnings do not fail.
"""
import csv, json, re, sys
from pathlib import Path

LANG = 'sk'
HERE = Path(__file__).resolve().parent
WORLD = HERE.parent.parent
NAMES = WORLD / 'names'
FILES = ('strings_map', 'strings_pages', 'strings_shell', 'strings_prices',
         'strings_pay', 'strings_press', 'strings_b2b', 'strings_embed', 'strings_home')  # L2: all 8; FIXL: + home
SLUG_KEYS = ('home', 'map', 'hub', 'net', 'about', 'download', 'gnet', 'prices', 'shell_about', 'sources', 'methodology')
SLUG_EXTRA = ('pay', 'routes', 'press', 'b2b', 'embed', 'map_conf', 'developers')  # FIXL F5: allowed in addition
SLUG_SEGMENT = ('net', 'about', 'download')
FORBIDDEN = [r'24\s*/\s*7', r'\bokamžite\b', r'\bhneď\b', r'\bEvolako\b', r'\bredakci', r'\bnáš\b', r'\bnaš[aeiou]',
             r'\bmy\s', r'najlepš\w*\s+(nabíjac\w*\s+)?sie']

err, warn = [], []
PH = re.compile(r'\{[^{}]*\}')
TAG = re.compile(r'</?[a-zA-Z][^>]*>')
ENT = re.compile(r'&[a-zA-Z#0-9]+;')


def _norm_ph(x):
    # pool 4 (10.11.2026): {city_u}/{country_u} may replace {city}/{country}; FIXL (D14): {name_nom} may replace {name}
    return {'{city_u}': '{city}', '{country_u}': '{country}', '{name_nom}': '{name}'}.get(x, x)


def sig(s):
    return sorted(_norm_ph(x) for x in PH.findall(s)), sorted(TAG.findall(s)), sorted(ENT.findall(s))


def plural_tags():
    try:
        from babel import Locale
        return set(Locale(LANG).plural_form.tags) | {'other'}
    except ImportError:
        warn.append('babel not installed — CLDR categories taken as one/few/many/other')
        return {'one', 'few', 'many', 'other'}


CATS = plural_tags()


def check_text(where, en, tr):
    if not isinstance(tr, str) or not tr.strip():
        err.append(f'{where}: empty or not a string')
        return
    a, b = sig(en), sig(tr)
    for name, x, y in zip(('placeholders', 'tags', 'entities'), a, b):
        if x != y:
            err.append(f'{where}: {name} differ EN={x} {LANG}={y}')
    if en.endswith(' | BlokVolt') and not tr.endswith(' | BlokVolt'):
        err.append(f'{where}: lost " | BlokVolt" tail')
    for p in FORBIDDEN:
        if re.search(p, tr, re.I):
            err.append(f'{where}: forbidden pattern {p!r}: {tr[:80]}')


n_keys = 0
for f in FILES:
    en = {k: v['en'] for k, v in json.load(open(WORLD / f'{f}.json', encoding='utf-8')).items()}
    p = HERE / f'{f}.json'
    if not p.exists():
        err.append(f'{f}.json missing')
        continue
    tr = json.load(open(p, encoding='utf-8'))
    for k in en.keys() - tr.keys():
        err.append(f'{f}: missing key {k}')
    for k in tr.keys() - en.keys():
        err.append(f'{f}: extra key {k}')
    for k in en.keys() & tr.keys():
        n_keys += 1
        v = tr[k]
        if k.startswith('pl_'):
            if not isinstance(v, dict):
                err.append(f'{f}.{k}: plural must be an object {sorted(CATS)}')
                continue
            if set(v) != CATS:
                err.append(f'{f}.{k}: categories {sorted(v)} != CLDR {sorted(CATS)}')
            for c, t in v.items():
                if not isinstance(t, str) or not t.strip():
                    err.append(f'{f}.{k}.{c}: empty')
        else:
            check_text(f'{f}.{k}', en[k], v)


def walk(a, b, path, n):
    if isinstance(a, dict):
        if not isinstance(b, dict) or list(a) != list(b):
            err.append(f'texts {path}: keys/order differ')
            return n
        for k in a:
            n = walk(a[k], b[k], f'{path}.{k}', n)
    elif isinstance(a, list):
        if not isinstance(b, list) or len(a) != len(b):
            err.append(f'texts {path}: list length differs')
            return n
        for i, (x, y) in enumerate(zip(a, b)):
            n = walk(x, y, f'{path}[{i}]', n)
    elif isinstance(a, str):
        check_text(f'texts {path}', a, b)
        n += 1
    elif a != b:
        err.append(f'texts {path}: non-string value changed')
    return n


n_txt = 0
try:
    T = json.load(open(HERE / 'texts.json', encoding='utf-8'))
    for part in ('about_data', 'download'):
        n_txt = walk(json.load(open(WORLD / f'{part}.json', encoding='utf-8'))['en'], T.get(part), part, n_txt)
except FileNotFoundError:
    err.append('texts.json missing')
    T = {}


def ml_nodes(node, path, out):
    # LANG0 contract: multilingual node {en, sr, ru} -> dotted path, list index [i]
    if isinstance(node, dict):
        if isinstance(node.get('en'), str) and ('sr' in node or 'ru' in node):
            out[path] = node['en']
            return out
        for k, v in node.items():
            ml_nodes(v, f'{path}.{k}' if path else k, out)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            ml_nodes(v, f'{path}[{i}]', out)
    return out


for part in ('pay', 'routes'):  # L2 (11.11.2026)
    src = ml_nodes(json.load(open(WORLD / f'{part}.json', encoding='utf-8')), '', {})
    got = T.get(part)
    if not isinstance(got, dict):
        err.append(f'texts.json: section {part!r} missing')
        continue
    for k in src.keys() - got.keys():
        err.append(f'texts {part}: missing node {k}')
    for k in got.keys() - src.keys():
        err.append(f'texts {part}: extra node {k}')
    for k in src.keys() & got.keys():
        check_text(f'texts {part} {k}', src[k], got[k])
        n_txt += 1

S = json.load(open(HERE / 'slugs.json', encoding='utf-8'))
if set(SLUG_KEYS) - set(S):
    err.append(f'slugs.json: missing keys {sorted(set(SLUG_KEYS) - set(S))}')
if set(S) - set(SLUG_KEYS) - set(SLUG_EXTRA):
    err.append(f'slugs.json: unknown keys {sorted(set(S) - set(SLUG_KEYS) - set(SLUG_EXTRA))}')
for k, v in S.items():
    if k in SLUG_SEGMENT:
        ok = re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', v)
    else:
        ok = re.fullmatch(rf'/{LANG}/([a-z0-9]+(-[a-z0-9]+)*/)*', v)
    if not ok:
        err.append(f'slugs.json {k}={v!r}: not ASCII lowercase-hyphen / wrong prefix')
if len(set(S.values())) != len(S):
    err.append('slugs.json: duplicate values')


def read_csv(name, header, alt=None):  # FIXL D4: alt = optional header with name_nom
    p = HERE / name
    try:
        rows = list(csv.DictReader(open(p, encoding='utf-8', newline='')))
    except FileNotFoundError:
        err.append(f'{name} missing')
        return []
    if rows and list(rows[0].keys()) not in (header, alt):
        err.append(f'{name}: header {list(rows[0].keys())} != {header}')
    return rows


C = read_csv('countries.csv', ['cc', 'name', 'slug', 'in_phrase', 'note'], alt=['cc', 'name', 'slug', 'in_phrase', 'note', 'name_nom'])
src_cc = {r['cc'] for r in csv.DictReader(open(NAMES / 'countries.csv', encoding='utf-8'))}
if {r['cc'] for r in C} != src_cc:
    err.append(f'countries.csv: cc set differs from names/countries.csv ({len(C)} vs {len(src_cc)})')
for r in C:
    if not r['name'] or not r['in_phrase']:
        err.append(f'countries.csv {r["cc"]}: empty name/in_phrase')
    if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', r['slug']):
        err.append(f'countries.csv {r["cc"]}: bad slug {r["slug"]!r}')
    if not re.match(r'(v|vo|na) ', r['in_phrase']):
        warn.append(f'countries.csv {r["cc"]}: in_phrase without v/vo/na: {r["in_phrase"]}')
    if re.search(r'[Ѐ-ӿ]', r['name'] + r['in_phrase']):
        err.append(f'countries.csv {r["cc"]}: Cyrillic character')
if len({r['slug'] for r in C}) != len(C):
    err.append('countries.csv: duplicate slugs')

Y = read_csv('cities.csv', ['geonameid', 'name', 'in_phrase', 'decl_ok', 'note'])
src_city = {r['geonameid']: r for r in csv.DictReader(open(NAMES / 'cities.csv', encoding='utf-8'))}
ids = [r['geonameid'] for r in Y]
if len(ids) != len(set(ids)):
    err.append('cities.csv: duplicate geonameid')
unknown = set(ids) - set(src_city)
if unknown:
    err.append(f'cities.csv: {len(unknown)} geonameid not in names/cities.csv')
for r in Y:
    if not r['name'] or not r['in_phrase']:
        err.append(f'cities.csv {r["geonameid"]}: empty name/in_phrase')
    if r['decl_ok'] not in ('0', '1'):
        err.append(f'cities.csv {r["geonameid"]}: decl_ok={r["decl_ok"]!r}')
    if r['decl_ok'] == '0' and not r['in_phrase'].startswith('v meste '):
        warn.append(f'cities.csv {r["geonameid"]}: decl_ok=0 but not the safe "v meste X" form')
cov = {}
for g in ids:
    s = src_city.get(g, {}).get('stage', '?')
    cov[s] = cov.get(s, 0) + 1
tot = {}
for r in src_city.values():
    tot[r['stage']] = tot.get(r['stage'], 0) + 1
sk_missing = [g for g, r in src_city.items() if r['cc'] == 'SK' and g not in set(ids)]
if sk_missing:
    err.append(f'cities.csv: {len(sk_missing)} SK cities missing')
# L2: every city page of the own market (market_countries sk = SK) must have a row
MARKET = ('SK',)
try:
    PS = json.load(open(WORLD / 'state' / 'pages_state.json', encoding='utf-8'))
    all_pages = {v['key'].split(':')[2] for v in PS.values() if v.get('type') == 'city'}
    miss_all = all_pages - set(ids)  # FIXL F2: every city page of pages_state must have a row
    if miss_all:
        err.append(f'cities.csv: {len(miss_all)} city pages missing: {sorted(miss_all)[:10]}')
    page_ids = {v['key'].split(':')[2] for v in PS.values()
                if v.get('type') == 'city' and v['key'].split(':')[1] in MARKET}
    miss = page_ids - set(ids)
    if miss:
        err.append(f'cities.csv: {len(miss)} city pages of {MARKET} missing: {sorted(miss)[:10]}')
    for r in Y:
        if r['geonameid'] in page_ids and r['decl_ok'] != '1':
            warn.append(f'cities.csv {r["geonameid"]}: own-market city page with decl_ok=0')
except FileNotFoundError:
    warn.append('state/pages_state.json not found — own-market city check skipped')

print(f'{LANG}: strings {n_keys} keys, texts {n_txt} strings, slugs {len(S)}, countries {len(C)}, cities {len(Y)}')
print('cities coverage by stage: ' + ', '.join(f'{s} {cov.get(s, 0)}/{tot[s]}' for s in sorted(tot)))
print(f'decl_ok=1: {sum(r["decl_ok"] == "1" for r in Y)}')
for w in warn[:20]:
    print('WARN', w)
if len(warn) > 20:
    print(f'WARN … {len(warn) - 20} more')
for e in err:
    print('ERROR', e)
print(f'{len(err)} errors, {len(warn)} warnings')
sys.exit(1 if err else 0)
