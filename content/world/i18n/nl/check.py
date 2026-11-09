#!/usr/bin/env python3
"""L-NL check: Dutch files in content/world/i18n/nl/ against the EN sources.

Run from anywhere: python3 content/world/i18n/nl/check.py  (exit 1 on errors).
Checks: every EN key present (and no extra keys), placeholders {..} and HTML tags/entities identical,
no empty values, plural keys = CLDR categories of nl (Babel), slugs ASCII, texts.json mirrors the EN
structure, countries.csv / cities.csv readable and complete, banned words absent.
"""
import csv, json, re, sys
from pathlib import Path

LANG = 'nl'
HERE = Path(__file__).resolve().parent
WORLD = HERE.parent.parent
NAMES = WORLD / 'names'
errors, warns = [], []


def err(m): errors.append(m)


PH = re.compile(r'\{[^{}]*\}')
TAG = re.compile(r'</?[a-zA-Z][^>]*>')
ENT = re.compile(r'&[a-zA-Z#0-9]+;')
URL = re.compile(r'https?://[^\s"\'<>)]+')
BANNED = re.compile(r'\b(we|wij|ons|onze|redactie|je|jij|jouw|jullie)\b|24/7|evolako', re.I)


def plural_cats():
    try:
        from babel import Locale
        return set(Locale(LANG).plural_form.tags) | {'other'}
    except Exception as e:  # babel missing
        warns.append(f'babel not available ({e}); assuming one/other')
        return {'one', 'other'}


CATS = plural_cats()


def sig(s):
    s = re.sub(r'(?<!\w)(?:CCS|Type|CHAdeMO)\b', '', s)
    return (sorted(PH.findall(s)), sorted(re.sub(r'\s+', ' ', t) for t in TAG.findall(s)),
            sorted(ENT.findall(s)), sorted(URL.findall(s)))


def cmp_text(where, en, nl):
    if not isinstance(nl, str) or not nl.strip():
        return err(f'{where}: empty or not a string')
    a, b = sig(en), sig(nl)
    for name, x, y in zip(('placeholders', 'tags', 'entities', 'urls'), a, b):
        if x != y:
            err(f'{where}: {name} differ: EN {x} / NL {y}')
    m = BANNED.search(TAG.sub(' ', nl))
    if m:
        err(f'{where}: banned word «{m.group(0)}»')


def check_strings(fn):
    src = json.load(open(WORLD / fn, encoding='utf-8'))
    p = HERE / fn
    if not p.exists():
        return err(f'{fn}: missing')
    nl = json.load(open(p, encoding='utf-8'))
    for k in src.keys() - nl.keys():
        err(f'{fn}: missing key {k}')
    for k in nl.keys() - src.keys():
        err(f'{fn}: extra key {k}')
    for k, v in src.items():
        if k not in nl:
            continue
        en, t = v['en'], nl[k]
        if k.startswith('pl_') and '|' in en:
            if not isinstance(t, dict):
                err(f'{fn}.{k}: plural must be an object {sorted(CATS)}')
                continue
            if set(t) != CATS:
                err(f'{fn}.{k}: plural categories {sorted(t)} != CLDR {sorted(CATS)}')
            for c, s in t.items():
                cmp_text(f'{fn}.{k}.{c}', en.split('|')[0 if c == 'one' else -1], s)
        else:
            cmp_text(f'{fn}.{k}', en, t)
    return len(src)


def walk(where, en, nl):
    if isinstance(en, dict):
        if not isinstance(nl, dict) or set(en) != set(nl):
            return err(f'{where}: keys differ')
        for k in en:
            walk(f'{where}.{k}', en[k], nl[k])
    elif isinstance(en, list):
        if not isinstance(nl, list) or len(en) != len(nl):
            return err(f'{where}: list length differs')
        for i, (a, b) in enumerate(zip(en, nl)):
            walk(f'{where}[{i}]', a, b)
    elif isinstance(en, str):
        cmp_text(where, en, nl)
    elif en != nl:
        err(f'{where}: non-text value changed')


def check_texts():
    p = HERE / 'texts.json'
    if not p.exists():
        return err('texts.json: missing')
    t = json.load(open(p, encoding='utf-8'))
    if set(t) != {'about_data', 'download', 'sources_pages'}:
        err(f'texts.json: top keys {sorted(t)}')
    walk('about_data', json.load(open(WORLD / 'about_data.json', encoding='utf-8'))['en'], t.get('about_data'))
    walk('download', json.load(open(WORLD / 'download.json', encoding='utf-8'))['en'], t.get('download'))
    src = json.load(open(WORLD / 'sources_pages.json', encoding='utf-8'))
    walk('sources_pages', src, t.get('sources_pages'))
    for k, v in src.items():  # legally required attribution stays verbatim
        if isinstance(v, dict) and v.get('attribution') != t['sources_pages'].get(k, {}).get('attribution'):
            err(f'sources_pages.{k}.attribution changed')


SLUG = re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*$')
PATH = re.compile(r'^/' + LANG + r'/([a-z0-9]+(-[a-z0-9]+)*/)*$')
SLUG_KEYS = {'home', 'map', 'hub', 'net', 'about', 'download', 'gnet', 'prices', 'shell_about', 'sources', 'methodology'}


def check_slugs():
    s = json.load(open(HERE / 'slugs.json', encoding='utf-8'))
    if set(s) != SLUG_KEYS:
        err(f'slugs.json: keys {sorted(set(s) ^ SLUG_KEYS)}')
    for k, v in s.items():
        if k in ('net', 'about', 'download'):
            if not SLUG.match(v):
                err(f'slugs.json.{k}: not a segment: {v}')
        elif not PATH.match(v):
            err(f'slugs.json.{k}: not a /{LANG}/…/ path: {v}')
    paths = [v for k, v in s.items() if k not in ('net', 'about', 'download')]
    if len(paths) != len(set(paths)):
        err('slugs.json: duplicate paths')


def check_csv():
    src_c = {r['cc'] for r in csv.DictReader(open(NAMES / 'countries.csv', encoding='utf-8'))}
    rows = list(csv.DictReader(open(HERE / 'countries.csv', encoding='utf-8')))
    if rows and list(rows[0]) != ['cc', 'name', 'slug', 'in_phrase', 'note']:
        err(f'countries.csv: header {list(rows[0])}')
    got = {r['cc'] for r in rows}
    if got != src_c:
        err(f'countries.csv: missing {sorted(src_c - got)} extra {sorted(got - src_c)}')
    slugs = [r['slug'] for r in rows]
    if len(slugs) != len(set(slugs)):
        err('countries.csv: duplicate slugs')
    for r in rows:
        if not (r['name'] and r['in_phrase'] and SLUG.match(r['slug'])):
            err(f'countries.csv {r["cc"]}: empty field or bad slug')
        if r['name'] not in r['in_phrase']:
            err(f'countries.csv {r["cc"]}: in_phrase does not contain name')
    src = {r['geonameid'] for r in csv.DictReader(open(NAMES / 'cities.csv', encoding='utf-8'))}
    rows = list(csv.DictReader(open(HERE / 'cities.csv', encoding='utf-8')))
    if rows and list(rows[0]) != ['geonameid', 'name', 'in_phrase', 'decl_ok', 'note']:
        err(f'cities.csv: header {list(rows[0])}')
    ids = [r['geonameid'] for r in rows]
    if len(ids) != len(set(ids)):
        err('cities.csv: duplicate geonameid')
    if set(ids) - src:
        err(f'cities.csv: unknown geonameid {sorted(set(ids) - src)[:5]}')
    for r in rows:
        if not r['name'] or not r['in_phrase'] or r['decl_ok'] not in ('0', '1'):
            err(f'cities.csv {r["geonameid"]}: empty field or bad decl_ok')
    return len(rows), len(src)


if __name__ == '__main__':
    n = {f: check_strings(f) for f in ('strings_map.json', 'strings_pages.json', 'strings_shell.json', 'strings_prices.json')}
    check_texts()
    check_slugs()
    cities = check_csv()
    for w in warns:
        print('warn:', w)
    for e in errors[:200]:
        print('ERROR:', e)
    print(f'L-{LANG.upper()} check: strings {n}, cities {cities[0]}/{cities[1]}, plural cats {sorted(CATS)}, '
          f'errors {len(errors)}')
    sys.exit(1 if errors else 0)
