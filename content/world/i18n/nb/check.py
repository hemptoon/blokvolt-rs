#!/usr/bin/env python3
"""Check content/world/i18n/nb/ against the EN sources (L-task contract, pool 3).

Run from the repo root:  python3 content/world/i18n/nb/check.py
Exit code 0 = OK, 1 = errors.
"""
import csv
import json
import re
import sys
import unicodedata
from pathlib import Path

LANG = 'nb'
MARKET = {'NO'}  # market_countries, LANG_pool §0.3
HERE = Path(__file__).resolve().parent
WORLD = HERE.parent.parent
ERR = []

PH = re.compile(r'\{[^{}]*\}')
TAG = re.compile(r'</?[a-zA-Z][^>]*>')
ENT = re.compile(r'&[a-zA-Z#0-9]+;')
SLUG = re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*$')
PATH = re.compile(r'^/[a-z]{2,3}/([a-z0-9]+(-[a-z0-9]+)*/)?$')
FORBIDDEN = re.compile(r'\b(vi|vår|vårt|våre|redaksjonen|24/7|umiddelbart|Evolako)\b', re.I)


def plural_tags():
    try:
        from babel import Locale
        r = Locale(LANG).plural_form
        return set(r.tags) | {'other'}
    except Exception as e:  # noqa
        print('warning: babel not available, assuming {one, other}:', e)
        return {'one', 'other'}


def tokens(s):
    return sorted(PH.findall(s)), sorted(TAG.findall(s)), sorted(ENT.findall(s))


def cmp_text(where, en, tr):
    if not isinstance(tr, str) or not tr.strip():
        ERR.append(f'{where}: empty or not a string')
        return
    a, b = tokens(en), tokens(tr)
    for name, x, y in zip(('placeholders', 'tags', 'entities'), a, b):
        if x != y:
            ERR.append(f'{where}: {name} differ: EN {x} vs {LANG} {y}')
    m = FORBIDDEN.search(tr)
    if m:
        ERR.append(f'{where}: forbidden word "{m.group(0)}"')


def check_strings(tags):
    for f in ('strings_map', 'strings_pages', 'strings_shell', 'strings_prices',
              'strings_pay', 'strings_press', 'strings_b2b', 'strings_embed'):
        en = json.load(open(WORLD / f'{f}.json', encoding='utf-8'))
        p = HERE / f'{f}.json'
        if not p.exists():
            ERR.append(f'{f}: file missing')
            continue
        tr = json.load(open(p, encoding='utf-8'))
        miss = [k for k in en if k not in tr]
        extra = [k for k in tr if k not in en]
        if miss:
            ERR.append(f'{f}: {len(miss)} keys missing, e.g. {miss[:5]}')
        if extra:
            ERR.append(f'{f}: {len(extra)} extra keys, e.g. {extra[:5]}')
        for k, v in en.items():
            if k not in tr:
                continue
            e = v['en']
            t = tr[k]
            if '|' in e and k.startswith('pl_'):
                if not isinstance(t, dict):
                    ERR.append(f'{f}.{k}: plural must be an object {sorted(tags)}')
                    continue
                if set(t) != tags:
                    ERR.append(f'{f}.{k}: plural categories {sorted(t)} != CLDR {sorted(tags)}')
                for c, s in t.items():
                    if not isinstance(s, str) or not s.strip():
                        ERR.append(f'{f}.{k}.{c}: empty')
            else:
                cmp_text(f'{f}.{k}', e, t)
        print(f'{f}: {len(tr)} keys')


def walk(where, en, tr):
    if isinstance(en, dict):
        if not isinstance(tr, dict) or list(en) != list(tr):
            ERR.append(f'{where}: keys differ')
            return
        for k in en:
            walk(f'{where}.{k}', en[k], tr[k])
    elif isinstance(en, list):
        if not isinstance(tr, list) or len(en) != len(tr):
            ERR.append(f'{where}: list length differs')
            return
        for i, (a, b) in enumerate(zip(en, tr)):
            walk(f'{where}[{i}]', a, b)
    elif isinstance(en, str):
        if not isinstance(tr, str) or (en.strip() and not tr.strip()):
            ERR.append(f'{where}: empty or not a string')
        elif tokens(en) != tokens(tr):
            ERR.append(f'{where}: placeholders/tags/entities differ')
    elif type(en) is not type(tr) or en != tr:
        ERR.append(f'{where}: non-text value changed')


def ml_nodes(x, path, out):
    """Multilingual node = dict with a string 'en' and at least one of 'sr'/'ru'."""
    if isinstance(x, dict):
        if isinstance(x.get('en'), str) and ('sr' in x or 'ru' in x):
            out[path] = x['en']
            return
        for k, v in x.items():
            ml_nodes(v, f'{path}.{k}' if path else k, out)
    elif isinstance(x, list):
        for i, v in enumerate(x):
            ml_nodes(v, f'{path}[{i}]', out)


def check_texts():
    p = HERE / 'texts.json'
    if not p.exists():
        ERR.append('texts.json: missing')
        return
    t = json.load(open(p, encoding='utf-8'))
    src = {
        'about_data': json.load(open(WORLD / 'about_data.json', encoding='utf-8'))['en'],
        'download': json.load(open(WORLD / 'download.json', encoding='utf-8'))['en'],
    }
    want = list(src) + ['pay', 'routes']
    if list(t) != want:
        ERR.append(f'texts.json: top keys {list(t)} != {want}')
        return
    for k in src:
        walk(f'texts.{k}', src[k], t[k])
    # LANG0 format: path of a multilingual node in pay.json / routes.json -> text
    for sec in ('pay', 'routes'):
        nodes = {}
        ml_nodes(json.load(open(WORLD / f'{sec}.json', encoding='utf-8')), '', nodes)
        got = t[sec]
        miss = [k for k in nodes if k not in got]
        extra = [k for k in got if k not in nodes]
        if miss:
            ERR.append(f'texts.{sec}: {len(miss)} nodes missing, e.g. {miss[:3]}')
        if extra:
            ERR.append(f'texts.{sec}: {len(extra)} unknown nodes, e.g. {extra[:3]}')
        for k, e in nodes.items():
            if k in got:
                cmp_text(f'texts.{sec}.{k}', e, got[k])
        print(f'texts.{sec}: {len(got)} of {len(nodes)} nodes')
    # sources_pages.json is shared by all languages (README 23:55) and is not translated
    print('texts.json: ok structure' if not any(e.startswith('texts') for e in ERR) else 'texts.json: errors')


def check_slugs():
    keys = ['home', 'map', 'hub', 'net', 'about', 'download', 'gnet', 'prices', 'shell_about', 'sources', 'methodology']
    s = json.load(open(HERE / 'slugs.json', encoding='utf-8'))
    if sorted(s) != sorted(keys):
        ERR.append(f'slugs.json: keys {sorted(s)} != {sorted(keys)}')
    for k, v in s.items():
        if k in ('net', 'about', 'download'):
            if not SLUG.match(v):
                ERR.append(f'slugs.{k}: not an ASCII segment: {v!r}')
        else:
            if not PATH.match(v) or not v.startswith(f'/{LANG}/'):
                ERR.append(f'slugs.{k}: not a /{LANG}/ path: {v!r}')
    paths = [v for k, v in s.items() if k not in ('net', 'about', 'download')]
    if len(set(paths)) != len(paths):
        ERR.append('slugs.json: duplicate paths')
    print('slugs.json:', len(s), 'keys')


def check_csv():
    cc_src = {r['cc'] for r in csv.DictReader(open(WORLD / 'names' / 'countries.csv', encoding='utf-8'))}
    rows = list(csv.DictReader(open(HERE / 'countries.csv', encoding='utf-8')))
    if rows and list(rows[0]) != ['cc', 'name', 'slug', 'in_phrase', 'note']:
        ERR.append(f'countries.csv: header {list(rows[0])}')
    got = {r['cc'] for r in rows}
    if got != cc_src:
        ERR.append(f'countries.csv: missing {sorted(cc_src - got)[:10]} extra {sorted(got - cc_src)[:10]}')
    slugs = [r['slug'] for r in rows]
    if len(set(slugs)) != len(slugs):
        ERR.append('countries.csv: duplicate slugs')
    for r in rows:
        if not r['name'] or not r['in_phrase'] or r['name'] not in r['in_phrase']:
            ERR.append(f'countries.csv {r["cc"]}: bad name/in_phrase')
        if not SLUG.match(r['slug']):
            ERR.append(f'countries.csv {r["cc"]}: bad slug {r["slug"]!r}')
    print('countries.csv:', len(rows), 'rows')

    ids_src = {r['geonameid'] for r in csv.DictReader(open(WORLD / 'names' / 'cities.csv', encoding='utf-8'))}
    # L2: cities of the language's own countries that have a page in pages_state.json
    state = json.load(open(WORLD / 'state' / 'pages_state.json', encoding='utf-8'))
    market = set()
    for v in state.values():
        if v.get('type') == 'city' and v['key'].split(':')[1] in MARKET:
            market.add(v['key'].split(':')[2])
    rows = list(csv.DictReader(open(HERE / 'cities.csv', encoding='utf-8')))
    if rows and list(rows[0]) != ['geonameid', 'name', 'in_phrase', 'decl_ok', 'note']:
        ERR.append(f'cities.csv: header {list(rows[0])}')
    ids = [r['geonameid'] for r in rows]
    if len(set(ids)) != len(ids):
        ERR.append('cities.csv: duplicate geonameid')
    lost = market - set(ids)
    if lost:
        ERR.append(f'cities.csv: {len(lost)} city pages of {sorted(MARKET)} without a name, e.g. {sorted(lost)[:5]}')
    print(f'cities.csv: {len(market)} city pages of {sorted(MARKET)} all named' if not lost else '')
    ids_src |= market
    unknown = set(ids) - ids_src
    if unknown:
        ERR.append(f'cities.csv: {len(unknown)} unknown geonameid')
    for r in rows:
        if not r['name'] or not r['in_phrase'] or r['decl_ok'] not in ('0', '1'):
            ERR.append(f'cities.csv {r["geonameid"]}: bad row')
        if any(c.isalpha() and 'LATIN' not in unicodedata.name(c, '') for c in r['name']):
            ERR.append(f'cities.csv {r["geonameid"]}: non-Latin name {r["name"]!r}')
    print(f'cities.csv: {len(rows)} of {len(ids_src)} cities')


def main():
    tags = plural_tags()
    check_strings(tags)
    check_texts()
    check_slugs()
    check_csv()
    if ERR:
        print(f'\n{len(ERR)} errors:')
        for e in ERR[:200]:
            print(' -', e)
        sys.exit(1)
    print('\nOK: 0 errors')


if __name__ == '__main__':
    main()
