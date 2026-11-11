#!/usr/bin/env python3
"""L-PT validator: python3 content/world/i18n/pt/check.py  (exit 1 on errors)."""
import csv, json, re, sys
from pathlib import Path
from babel import Locale

LANG, LOCALE = 'pt', 'pt_PT'
HERE = Path(__file__).resolve().parent
WORLD = HERE.parents[1]
ERR, WARN = [], []
PH = re.compile(r'\{[^{}]*\}')
TAG = re.compile(r'</?[a-zA-Z][^>]*>|&[a-z#0-9]+;')
CATS = set(Locale.parse(LOCALE).plural_form.tags) | {'other'}

def ph(s): return sorted(PH.findall(s))
def tags(s): return sorted(re.sub(r'\s+[^>]*', '', t) if t.startswith('<') else t for t in TAG.findall(s))

def cmp_text(where, en, alts, pt):
    if not isinstance(pt, str) or not pt.strip():
        ERR.append(f'{where}: empty'); return
    # FIXL D14: {name_nom} (countries.csv name_nom) may stand where EN has {name}
    if ph(pt.replace('{name_nom}', '{name}') if '{name}' in en else pt) not in [ph(en)] + [ph(a) for a in alts if isinstance(a, str)]:
        ERR.append(f'{where}: placeholders {ph(pt)} != EN {ph(en)}')
    if tags(pt) != tags(en):
        ERR.append(f'{where}: tags {tags(pt)} != EN {tags(en)}')

for f in ['strings_home', 'strings_map', 'strings_pages', 'strings_shell', 'strings_prices',
          'strings_pay', 'strings_press', 'strings_b2b', 'strings_embed']:
    src = json.load(open(WORLD / f'{f}.json', encoding='utf-8'))
    p = HERE / f'{f}.json'
    if not p.exists():
        ERR.append(f'{f}: missing'); continue
    tr = json.load(open(p, encoding='utf-8'))
    for k in set(tr) - set(src): ERR.append(f'{f}.{k}: extra key')
    for k, v in src.items():
        if k not in tr: ERR.append(f'{f}.{k}: missing key'); continue
        en, alts = v['en'], [v.get('sr'), v.get('ru')]
        if k.startswith('pl_') and en.count('|') == 2:
            if not isinstance(tr[k], dict) or set(tr[k]) != CATS:
                ERR.append(f'{f}.{k}: plural categories {sorted(tr[k]) if isinstance(tr[k], dict) else type(tr[k]).__name__} != CLDR {sorted(CATS)}')
                continue
            for c, s in tr[k].items(): cmp_text(f'{f}.{k}.{c}', en.split('|')[0], [], s)
        else:
            cmp_text(f'{f}.{k}', en, alts, tr[k])

def walk(where, en, pt):
    if isinstance(en, dict):
        if not isinstance(pt, dict) or set(en) != set(pt):
            ERR.append(f'{where}: keys differ'); return
        for k in en: walk(f'{where}.{k}', en[k], pt[k])
    elif isinstance(en, list):
        if not isinstance(pt, list) or len(en) != len(pt):
            ERR.append(f'{where}: list length differs'); return
        for i, (a, b) in enumerate(zip(en, pt)): walk(f'{where}[{i}]', a, b)
    elif isinstance(en, str):
        cmp_text(where, en, [], pt)
    elif en != pt:
        ERR.append(f'{where}: non-text value changed')

tx = json.load(open(HERE / 'texts.json', encoding='utf-8'))
if set(tx) != {'about_data', 'download', 'sources_pages', 'pay', 'routes'}: ERR.append('texts.json: top-level keys')
walk('texts.about_data', json.load(open(WORLD / 'about_data.json', encoding='utf-8'))['en'], tx.get('about_data'))
walk('texts.download', json.load(open(WORLD / 'download.json', encoding='utf-8'))['en'], tx.get('download'))
sp = json.load(open(WORLD / 'sources_pages.json', encoding='utf-8'))
walk('texts.sources_pages', sp, tx.get('sources_pages'))

# texts.json → pay / routes (LANG0 format: dotted path of a multilingual node → text)
def ml_nodes(x, p, out):
    if isinstance(x, dict):
        if isinstance(x.get('en'), str) and {'en', 'sr', 'ru'} <= set(x):
            out[p] = x['en']; return
        for k, v in x.items(): ml_nodes(v, f'{p}.{k}' if p else k, out)
    elif isinstance(x, list):
        for i, v in enumerate(x): ml_nodes(v, f'{p}[{i}]', out)
for sec in ('pay', 'routes'):
    nodes = {}; ml_nodes(json.load(open(WORLD / f'{sec}.json', encoding='utf-8')), '', nodes)
    got = tx.get(sec) or {}
    for k in set(got) - set(nodes): ERR.append(f'texts.{sec}.{k}: no such multilingual node')
    for k, en in nodes.items():
        if k not in got: ERR.append(f'texts.{sec}.{k}: missing'); continue
        cmp_text(f'texts.{sec}.{k}', en, [], got[k])

SL = json.load(open(HERE / 'slugs.json', encoding='utf-8'))
PATHS = ['home', 'map', 'hub', 'gnet', 'prices', 'shell_about', 'sources', 'methodology']
SEGS = ['net', 'about', 'download']
EXTRA = ['pay', 'routes', 'press', 'b2b', 'embed', 'map_conf', 'developers']  # FIXL F5: allowed in addition (full paths)
if not set(PATHS + SEGS) <= set(SL) or set(SL) - set(PATHS + SEGS + EXTRA): ERR.append(f'slugs.json: keys {sorted(SL)}')
for k in EXTRA:
    if k in SL and not re.fullmatch(rf'/{LANG}/([a-z0-9]+(-[a-z0-9]+)*/)+', SL[k]): ERR.append(f'slugs.{k}: bad path {SL[k]!r}')
for k in PATHS:
    if not re.fullmatch(rf'/{LANG}/([a-z0-9]+(-[a-z0-9]+)*/)?', SL.get(k, '')): ERR.append(f'slugs.{k}: bad path {SL.get(k)!r}')
for k in SEGS:
    if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', SL.get(k, '')): ERR.append(f'slugs.{k}: bad segment {SL.get(k)!r}')
vals = [SL[k] for k in PATHS + EXTRA if k in SL]
if len(set(vals)) != len(vals): ERR.append('slugs: duplicate paths')

src_cc = {r['cc'] for r in csv.DictReader(open(WORLD / 'names/countries.csv', encoding='utf-8'))}
rows = list(csv.DictReader(open(HERE / 'countries.csv', encoding='utf-8')))
if rows and list(rows[0]) not in (['cc', 'name', 'slug', 'in_phrase', 'note'], ['cc', 'name', 'slug', 'in_phrase', 'note', 'name_nom']): ERR.append('countries.csv: columns')
if {r['cc'] for r in rows} != src_cc or len(rows) != len(src_cc): ERR.append(f'countries.csv: {len(rows)} rows, cc set differs from names/countries.csv')
seen = set()
for r in rows:
    if not r['name'] or not r['in_phrase']: ERR.append(f"countries {r['cc']}: empty")
    if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', r['slug']): ERR.append(f"countries {r['cc']}: slug {r['slug']!r}")
    if r['slug'] in seen: ERR.append(f"countries {r['cc']}: duplicate slug")
    seen.add(r['slug'])
    if r['name'] not in r['in_phrase']: WARN.append(f"countries {r['cc']}: name not in in_phrase")
    if 'name_nom' in r and (not r['name_nom'] or not r['name_nom'].endswith(r['name'])): ERR.append(f"countries {r['cc']}: name_nom {r['name_nom']!r}")  # D14

src_g = {r['geonameid'] for r in csv.DictReader(open(WORLD / 'names/cities.csv', encoding='utf-8'))}
rows = list(csv.DictReader(open(HERE / 'cities.csv', encoding='utf-8')))
if rows and list(rows[0]) != ['geonameid', 'name', 'in_phrase', 'decl_ok', 'note']: ERR.append('cities.csv: columns')
g = [r['geonameid'] for r in rows]
if len(set(g)) != len(g): ERR.append('cities.csv: duplicate geonameid')
if set(g) - src_g: ERR.append(f'cities.csv: {len(set(g) - src_g)} unknown geonameid')
for r in rows:
    if not r['name'] or not r['in_phrase'] or r['decl_ok'] not in ('0', '1'): ERR.append(f"cities {r['geonameid']}: bad row")
cov = len(set(g) & src_g)
# FIXL: every city page of state/pages_state.json must have a row
_ps = WORLD / 'state' / 'pages_state.json'
if _ps.exists():
    page_g = {v['key'].split(':')[-1] for v in json.load(open(_ps, encoding='utf-8')).values()
              if v.get('type') == 'city' and str(v.get('key', '')).startswith('t:')}
    if page_g - set(g): ERR.append(f'cities.csv: {len(page_g - set(g))} city pages without a row, e.g. {sorted(page_g - set(g))[:5]}')
else:
    WARN.append('state/pages_state.json not found: city pages not checked')

for e in ERR: print('ERROR', e)
for w in WARN: print('warn ', w)
print(f'{LANG}: {len(ERR)} errors, {len(WARN)} warnings; plural categories {sorted(CATS)}; cities {cov}/{len(src_g)}')
sys.exit(1 if ERR else 0)
