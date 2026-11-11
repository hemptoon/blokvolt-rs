#!/usr/bin/env python3
"""L-ET / L2-et: checks content/world/i18n/et against the EN sources (8 strings files, texts.json incl. pay/routes). Run from repo root: python3 content/world/i18n/et/check.py"""
import csv, json, re, sys
from pathlib import Path
LANG = 'et'
ROOT = Path(__file__).resolve().parents[4]
W = ROOT / 'content' / 'world'
D = W / 'i18n' / LANG
errs = []
def err(m): errs.append(m)
PH = re.compile(r'\{[^{}]*\}')
TAG = re.compile(r'<[^>]+>|&[a-z#0-9]+;')
def sig(s): return sorted(PH.findall(s)), sorted(TAG.findall(s))
def sig_t(t, e):
    # pool-4 rule: {city_u}/{country_u} (case form from cities.csv/countries.csv) may stand for {city}/{country}/{country_name}
    t = t.replace('{city_u}', '{city}')
    if '{name_nom}' in t and '{name}' in e: t = t.replace('{name_nom}', '{name}')   # FIXL D14
    if '{country_u}' in t and '{country_u}' not in e:
        t = t.replace('{country_u}', '{country}' if '{country}' in e else '{country_name}')
    return sig(t)
FILES = ('strings_map', 'strings_pages', 'strings_shell', 'strings_prices', 'strings_pay', 'strings_press', 'strings_b2b', 'strings_embed', 'strings_home')
try:
    from babel import Locale
    cats = set(Locale(LANG).plural_form.tags) | {'other'}
except Exception as e:
    cats = {'one', 'other'}; print('babel missing, using', cats)
for f in FILES:
    if not (D / f'{f}.json').exists(): err(f'{f}.json missing'); continue
    en = {k: v['en'] for k, v in json.load(open(W / f'{f}.json', encoding='utf-8')).items()}
    tr = json.load(open(D / f'{f}.json', encoding='utf-8'))
    for k in en.keys() - tr.keys(): err(f'{f}: missing key {k}')
    for k in tr.keys() - en.keys(): err(f'{f}: extra key {k}')
    for k in en.keys() & tr.keys():
        e, t = en[k], tr[k]
        if isinstance(t, dict):
            if '|' not in e: err(f'{f}.{k}: plural object but EN is not a plural form')
            if set(t) != cats: err(f'{f}.{k}: plural categories {sorted(t)} != CLDR {sorted(cats)}')
            for c, v in t.items():
                if not str(v).strip(): err(f'{f}.{k}.{c}: empty')
                if sig(v) != sig(e.split('|')[0]): err(f'{f}.{k}.{c}: placeholders/tags differ')
            continue
        if '|' in e and k.startswith('pl_'): err(f'{f}.{k}: EN is a plural form, ET must be an object')
        if not str(t).strip() and str(e).strip(): err(f'{f}.{k}: empty')
        if sig_t(t, e) != sig(e): err(f'{f}.{k}: placeholders/tags differ: {sig(e)} vs {sig(t)}')
# texts.json
def walk(a, b, p):
    if type(a) != type(b): return err(f'texts{p}: type {type(a).__name__} vs {type(b).__name__}')
    if isinstance(a, dict):
        if a.keys() != b.keys(): err(f'texts{p}: keys differ {set(a) ^ set(b)}')
        for k in a.keys() & b.keys(): walk(a[k], b[k], f'{p}.{k}')
    elif isinstance(a, list):
        if len(a) != len(b): return err(f'texts{p}: list length {len(a)} vs {len(b)}')
        for i, (x, y) in enumerate(zip(a, b)): walk(x, y, f'{p}[{i}]')
    elif isinstance(a, str):
        if a.strip() and not b.strip(): err(f'texts{p}: empty')
        if sig(a) != sig(b): err(f'texts{p}: placeholders/tags differ')
t = json.load(open(D / 'texts.json', encoding='utf-8'))
src = {'about_data': json.load(open(W / 'about_data.json'))['en'], 'download': json.load(open(W / 'download.json'))['en']}  # sources_pages.json is not translated (README 23:55)
if set(t) != set(src) | {'pay', 'routes'}: err(f'texts.json top keys {sorted(t)}')
for k in src: walk(src[k], t.get(k), '.' + k)
# texts.json pay / routes (LANG0 format: dotted path of a multilingual node -> text)
def ml_nodes(o, p, out):
    if isinstance(o, dict):
        if isinstance(o.get('en'), str) and 'ru' in o: out[p] = o['en']; return
        for k, v in o.items(): ml_nodes(v, f'{p}.{k}' if p else k, out)
    elif isinstance(o, list):
        for i, v in enumerate(o): ml_nodes(v, f'{p}[{i}]', out)
    return out
for sec, fn in (('pay', 'pay.json'), ('routes', 'routes.json')):
    want = ml_nodes(json.load(open(W / fn, encoding='utf-8')), '', {})
    got = t.get(sec, {})
    for k in want.keys() - got.keys(): err(f'texts.{sec}: missing {k}')
    for k in got.keys() - want.keys(): err(f'texts.{sec}: extra {k}')
    for k in want.keys() & got.keys():
        if not str(got[k]).strip(): err(f'texts.{sec}.{k}: empty')
        if sig(got[k]) != sig(want[k]): err(f'texts.{sec}.{k}: placeholders/tags differ')
# forbidden words (README §1.7)
_all = json.dumps([json.load(open(D / f'{f}.json', encoding='utf-8')) for f in FILES + ('texts',) if (D / f'{f}.json').exists()], ensure_ascii=False)
for pat in (r'24\s*/\s*7', r'evolako', r'\bmeie\b', r'\bme\b', r'\bkohe\b', r'toimetus'):
    if re.search(pat, _all, re.I): err(f'forbidden word: {pat}')
# slugs
s = json.load(open(D / 'slugs.json'))
need = {'home', 'map', 'hub', 'net', 'about', 'download', 'gnet', 'prices', 'shell_about', 'sources', 'methodology'}
section = {'pay', 'routes', 'press', 'b2b', 'embed', 'map_conf', 'developers'}   # FIXL F5: optional, full paths
if not need <= set(s) <= need | section: err(f'slugs keys {sorted(set(s) ^ need)}: need {sorted(need)}, may add {sorted(section)}')
for k, v in s.items():
    if k in section:
        if not re.fullmatch(rf'/{LANG}/([a-z0-9]+(-[a-z0-9]+)*/)+', v): err(f'slug {k}={v} not /{LANG}/…/ ASCII')
    elif k in ('net', 'about', 'download'):
        if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', v): err(f'slug {k}={v} not one ASCII segment')
    elif not re.fullmatch(rf'/{LANG}/([a-z0-9]+(-[a-z0-9]+)*/)?', v): err(f'slug {k}={v} not /{LANG}/…/ ASCII')
if len(set(s.values())) != len(s): err('duplicate slugs')
# countries
cc_src = [r['cc'] for r in csv.DictReader(open(W / 'names' / 'countries.csv', encoding='utf-8'))]
rows = list(csv.DictReader(open(D / 'countries.csv', encoding='utf-8')))
if rows and list(rows[0]) not in (['cc', 'name', 'slug', 'in_phrase', 'note'], ['cc', 'name', 'slug', 'in_phrase', 'note', 'name_nom']):
    err(f'countries.csv header {list(rows[0])}')   # FIXL D4: name_nom may be added as the last column
if [r['cc'] for r in rows] != cc_src: err('countries.csv: cc list differs from names/countries.csv')
slugs = [r['slug'] for r in rows]
if len(set(slugs)) != len(slugs): err('countries.csv: duplicate slug')
for r in rows:
    if not r['name'] or not r['in_phrase']: err(f"countries {r['cc']}: empty")
    if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', r['slug']): err(f"countries {r['cc']}: slug {r['slug']}")
    if r['slug'] in [v.strip('/').split('/')[-1] for v in s.values()]: err(f"countries {r['cc']}: slug collides with a page slug")
# cities
gid_src = {r['geonameid'] for r in csv.DictReader(open(W / 'names' / 'cities.csv', encoding='utf-8'))}
crow = list(csv.DictReader(open(D / 'cities.csv', encoding='utf-8')))
for r in crow:
    if r['geonameid'] not in gid_src: err(f"cities: unknown geonameid {r['geonameid']}")
    if not r['name'] or not r['in_phrase'] or r['decl_ok'] not in ('0', '1'): err(f"cities {r['geonameid']}: bad row")
if len({r['geonameid'] for r in crow}) != len(crow): err('cities: duplicate geonameid')
_ps = json.load(open(W / 'state' / 'pages_state.json', encoding='utf-8'))   # FIXL F2: every city page needs a row
for g in sorted({str(v['key']).split(':')[2] for v in _ps.values() if v.get('type') == 'city' and str(v.get('key', '')).startswith('t:')} - {r['geonameid'] for r in crow}):
    err(f'cities {g}: city page without a row')
print(f'cities: {len(crow)}/{len(gid_src)} rows, decl_ok=1: {sum(r["decl_ok"] == "1" for r in crow)}')
print(f'countries: {len(rows)}; slugs: {len(s)}')
print('\n'.join(errs) if errs else 'OK: 0 errors')
sys.exit(1 if errs else 0)
