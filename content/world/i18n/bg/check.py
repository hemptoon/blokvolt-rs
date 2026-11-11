#!/usr/bin/env python3
"""Checks the BG localisation of the world layer (L-BG, pool 3).

L2-BG (11.11.2026): all 8 strings_*.json files and the texts.json sections
pay / routes (LANG0 format: dotted path of a multilingual node -> text).

Run from the repo root:  python3 content/world/i18n/bg/check.py
Exit code 0 = no errors. Warnings do not fail.
"""
import csv
import json
import re
import sys
from pathlib import Path

LANG = 'bg'
HERE = Path(__file__).resolve().parent
WORLD = HERE.parent.parent
NAMES = WORLD / 'names'
PH = re.compile(r'\{[^{}]*\}')
TAG = re.compile(r'</?([a-zA-Z0-9]+)[^>]*>')
ENT = re.compile(r'&[a-zA-Z#0-9]+;')
SLUG_SEG = re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*$')
FORBIDDEN = [r'24/7', r'\bведнага\b', r'\bние\b', r'\bнаш[аиe]?\b', r'\bредакци', r'Evolako']

STRING_FILES = ('strings_map', 'strings_pages', 'strings_shell', 'strings_prices',
                'strings_pay', 'strings_press', 'strings_b2b', 'strings_embed')
NODE_LANGS = {'en', 'sr', 'ru'}

errors, warns = [], []


def err(m):
    errors.append(m)


def warn(m):
    warns.append(m)


def plural_cats():
    try:
        from babel import Locale
        tags = set(Locale(LANG).plural_form.tags)
    except Exception as e:  # babel missing — fall back to known CLDR set
        warn(f'babel unavailable ({e}); using CLDR bg = one/other')
        tags = {'one'}
    return tags | {'other'}


def _norm_ph(x):
    # {city_u}/{country_u} are allowed in every language (pool 4, 00:12): engine puts the language's in_phrase there
    return re.sub(r'\{(city|country)_u\}', r'{\1}', x)


def sig(s):
    return (sorted(_norm_ph(x) for x in PH.findall(s)), sorted(t.lower() for t in TAG.findall(s)), sorted(ENT.findall(s)))


def check_text(where, en, bg):
    if not isinstance(bg, str) or not bg.strip():
        err(f'{where}: empty or not a string')
        return
    if sig(en) != sig(bg):
        err(f'{where}: placeholders/tags differ EN {sig(en)} vs BG {sig(bg)}')
    if en.endswith(' | BlokVolt') and not bg.endswith(' | BlokVolt'):
        err(f'{where}: lost " | BlokVolt" tail')
    for f in FORBIDDEN:
        if re.search(f, bg, re.I):
            err(f'{where}: forbidden word /{f}/')
    if re.search(r'[A-Za-z]{4,}', PH.sub('', TAG.sub('', bg))) and en == bg:
        warn(f'{where}: identical to EN')


def check_strings(cats):
    for name in STRING_FILES:
        en = {k: v['en'] for k, v in json.load(open(WORLD / f'{name}.json', encoding='utf-8')).items()}
        p = HERE / f'{name}.json'
        if not p.exists():
            err(f'{name}.json missing')
            continue
        bg = json.load(open(p, encoding='utf-8'))
        for k in en.keys() - bg.keys():
            err(f'{name}.{k}: missing')
        for k in bg.keys() - en.keys():
            err(f'{name}.{k}: extra key')
        for k in en.keys() & bg.keys():
            if k.startswith('pl_'):
                v = bg[k]
                if not isinstance(v, dict):
                    err(f'{name}.{k}: plural must be an object')
                    continue
                if set(v) != cats:
                    err(f'{name}.{k}: categories {sorted(v)} != CLDR {sorted(cats)}')
                for c, s in v.items():
                    if not isinstance(s, str) or not s.strip():
                        err(f'{name}.{k}.{c}: empty')
            else:
                if isinstance(bg[k], dict):
                    err(f'{name}.{k}: only pl_* keys may be objects')
                    continue
                check_text(f'{name}.{k}', en[k], bg[k])


def walk(where, en, bg):
    if isinstance(en, dict):
        if not isinstance(bg, dict) or set(en) != set(bg):
            err(f'{where}: keys differ')
            return
        for k in en:
            walk(f'{where}.{k}', en[k], bg[k])
    elif isinstance(en, list):
        if not isinstance(bg, list) or len(en) != len(bg):
            err(f'{where}: list length differs')
            return
        for i, (a, b) in enumerate(zip(en, bg)):
            walk(f'{where}[{i}]', a, b)
    elif isinstance(en, str):
        if not isinstance(bg, str):
            err(f'{where}: type differs')
        elif en.startswith('http') or en.startswith('/'):
            if en != bg:
                err(f'{where}: URL/path changed')
        elif en.strip():
            check_text(where, en, bg)
    elif en != bg:
        err(f'{where}: non-text value changed')


def ml_nodes(x, path='', out=None):
    """Multilingual nodes of pay.json / routes.json: dicts with 'en' plus 'sr'/'ru'."""
    out = {} if out is None else out
    if isinstance(x, dict):
        if isinstance(x.get('en'), str) and (NODE_LANGS - {'en'}) & set(x):
            out[path] = x['en']
            return out
        for k, v in x.items():
            ml_nodes(v, f'{path}.{k}' if path else k, out)
    elif isinstance(x, list):
        for i, v in enumerate(x):
            ml_nodes(v, f'{path}[{i}]', out)
    return out


def check_texts():
    p = HERE / 'texts.json'
    if not p.exists():
        err('texts.json missing')
        return
    bg = json.load(open(p, encoding='utf-8'))
    want = {'about_data', 'download', 'pay', 'routes'}
    if set(bg) != want:
        err(f'texts.json: top keys {sorted(bg)} != {sorted(want)}')
    for k in ('about_data', 'download'):
        en = json.load(open(WORLD / f'{k}.json', encoding='utf-8'))['en']
        walk(f'texts.{k}', en, bg.get(k))
    for k in ('pay', 'routes'):
        nodes = ml_nodes(json.load(open(WORLD / f'{k}.json', encoding='utf-8')))
        got = bg.get(k) or {}
        if not isinstance(got, dict):
            err(f'texts.{k}: must be an object path -> text')
            continue
        for path in nodes.keys() - got.keys():
            err(f'texts.{k}.{path}: missing')
        for path in got.keys() - nodes.keys():
            err(f'texts.{k}.{path}: no such multilingual node')
        for path in nodes.keys() & got.keys():
            check_text(f'texts.{k}.{path}', nodes[path], got[path])


def check_slugs():
    want = ['home', 'map', 'hub', 'net', 'about', 'download', 'gnet', 'prices', 'shell_about', 'sources', 'methodology']
    s = json.load(open(HERE / 'slugs.json', encoding='utf-8'))
    if sorted(s) != sorted(want):
        err(f'slugs.json keys {sorted(s)}')
    for k, v in s.items():
        if k in ('net', 'about', 'download'):
            if not SLUG_SEG.match(v):
                err(f'slugs.{k}: bad segment {v!r}')
        else:
            if not v.startswith(f'/{LANG}/') or not v.endswith('/'):
                err(f'slugs.{k}: must be /{LANG}/…/ ({v!r})')
            for seg in v.strip('/').split('/'):
                if not SLUG_SEG.match(seg):
                    err(f'slugs.{k}: bad segment {seg!r}')
    full = [v for k, v in s.items() if k not in ('net', 'about', 'download', 'home')]
    if len(set(full)) != len(full):
        err('slugs: duplicate paths')


def check_csv():
    src_c = {r['cc']: r for r in csv.DictReader(open(NAMES / 'countries.csv', encoding='utf-8'))}
    rows = list(csv.DictReader(open(HERE / 'countries.csv', encoding='utf-8')))
    if rows and list(rows[0].keys()) != ['cc', 'name', 'slug', 'in_phrase', 'note']:
        err(f'countries.csv columns {list(rows[0].keys())}')
    seen = set()
    for r in rows:
        cc = r['cc']
        if cc in seen:
            err(f'countries.csv: duplicate {cc}')
        seen.add(cc)
        if not r['name'].strip() or not r['in_phrase'].strip():
            err(f'countries.csv {cc}: empty name/in_phrase')
        if not SLUG_SEG.match(r['slug']):
            err(f'countries.csv {cc}: bad slug {r["slug"]!r}')
        if not re.match(r'^(в|във|на) ', r['in_phrase']):
            err(f'countries.csv {cc}: in_phrase must start with „в“/„във“/„на“')
    if set(src_c) - seen:
        err(f'countries.csv: missing {sorted(set(src_c) - seen)}')
    slugs = [r['slug'] for r in rows]
    if len(set(slugs)) != len(slugs):
        err('countries.csv: duplicate slugs')

    src = {r['geonameid']: r for r in csv.DictReader(open(NAMES / 'cities.csv', encoding='utf-8'))}
    rows = list(csv.DictReader(open(HERE / 'cities.csv', encoding='utf-8')))
    if rows and list(rows[0].keys()) != ['geonameid', 'name', 'in_phrase', 'decl_ok', 'note']:
        err(f'cities.csv columns {list(rows[0].keys())}')
    seen = set()
    for r in rows:
        g = r['geonameid']
        if g not in src:
            err(f'cities.csv: unknown geonameid {g}')
        if g in seen:
            err(f'cities.csv: duplicate {g}')
        seen.add(g)
        if not r['name'].strip() or not r['in_phrase'].strip():
            err(f'cities.csv {g}: empty name/in_phrase')
        if r['decl_ok'] not in ('0', '1'):
            err(f'cities.csv {g}: decl_ok must be 0/1')
        if not re.match(r'^(в|във|на) ', r['in_phrase']):
            err(f'cities.csv {g}: in_phrase must start with „в“/„във“/„на“')
    must = {g for g, r in src.items() if r['cc'] == 'BG' or r['stage'] == 'month'}
    if must - seen:
        err(f'cities.csv: {len(must - seen)} BG/month cities missing')
    if len(seen) < len(src):
        warn(f'cities.csv: {len(seen)}/{len(src)} cities covered')
    return len(seen), len(src)


def main():
    cats = plural_cats()
    check_strings(cats)
    check_texts()
    check_slugs()
    try:
        cov = check_csv()
    except FileNotFoundError as e:
        err(f'csv missing: {e}')
        cov = None
    for w in warns:
        print('WARN ', w)
    for e in errors:
        print('ERROR', e)
    print(f'plural categories: {sorted(cats)}; cities: {cov}; errors {len(errors)}, warnings {len(warns)}')
    sys.exit(1 if errors else 0)


if __name__ == '__main__':
    main()
