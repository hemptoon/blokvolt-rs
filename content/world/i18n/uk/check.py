#!/usr/bin/env python3
"""Check content/world/i18n/uk against the EN sources (L-UK, pool 3; L2-uk: 8 string files, texts pay/routes/sources_pages).

Run from the repo root:  python3 content/world/i18n/uk/check.py
Exit code 0 = no errors. Warnings do not fail.
"""
import csv, json, os, re, sys

LANG = 'uk'
HERE = os.path.dirname(os.path.abspath(__file__))
WORLD = os.path.normpath(os.path.join(HERE, '..', '..'))
NAMES = os.path.join(WORLD, 'names')
SLUG_KEYS = ['home', 'map', 'hub', 'net', 'about', 'download', 'gnet', 'prices',
             'shell_about', 'sources', 'methodology']
SEGMENT_KEYS = {'net', 'about', 'download'}

PH = re.compile(r'\{[^{}]*\}')
TAG = re.compile(r'</?[a-zA-Z][^>]*>')
ENT = re.compile(r'&[a-zA-Z#0-9]+;')
URL = re.compile(r'https?://[^\s"<>)]+')
SLUG = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
BANNED = [r'\b24/7\b', r'\bодразу\b', r'\bмиттєво\b', r'\bми\b', r'\bнаш[аеіуо]?\b', r'\bредакці']

errors, warnings = [], []
err = errors.append
warn = warnings.append


def plural_cats():
    try:
        from babel import Locale
        return set(Locale(LANG).plural_form.tags) | {'other'}
    except Exception as e:  # babel missing
        warn(f'babel unavailable ({e}); using fixed CLDR set for uk')
        return {'one', 'few', 'many', 'other'}


CATS = plural_cats()


def same(label, a, b, what):
    if sorted(a) != sorted(b):
        err(f'{label}: {what} differ: en={sorted(a)} {LANG}={sorted(b)}')


def cmp_string(label, en, tr):
    if not isinstance(tr, str) or not tr.strip():
        err(f'{label}: empty or not a string')
        return
    # pool 4 (10.11.2026): {city_u}/{country_u} may stand for {city}/{country}; the engine fills in_phrase
    norm = lambda xs: [x.replace('_u}', '}') for x in xs]
    same(label, norm(PH.findall(en)), norm(PH.findall(tr)), 'placeholders')
    same(label, TAG.findall(en), TAG.findall(tr), 'HTML tags')
    same(label, ENT.findall(en), ENT.findall(tr), 'entities')
    same(label, URL.findall(en), URL.findall(tr), 'URLs')
    if en.endswith(' | BlokVolt') and not tr.endswith(' | BlokVolt'):
        err(f'{label}: lost " | BlokVolt" tail')
    for b in BANNED:
        if re.search(b, tr, re.I):
            warn(f'{label}: banned/suspicious word /{b}/: {tr[:80]}')


def check_strings(name):
    en_all = json.load(open(os.path.join(WORLD, name)))
    path = os.path.join(HERE, name)
    if not os.path.exists(path):
        err(f'{name}: missing')
        return 0
    tr = json.load(open(path))
    same(name, list(en_all), list(tr), 'key sets')
    for k, v in en_all.items():
        en = v['en']
        t = tr.get(k)
        lab = f'{name}:{k}'
        if t is None:
            continue
        if k.startswith('pl_'):
            if not isinstance(t, dict):
                err(f'{lab}: plural key must be an object {{one,few,...}}')
                continue
            if set(t) != CATS:
                err(f'{lab}: plural categories {sorted(t)} != CLDR {sorted(CATS)}')
            for c, s in t.items():
                if not isinstance(s, str) or not s.strip():
                    err(f'{lab}.{c}: empty')
                if PH.findall(s):
                    err(f'{lab}.{c}: plural forms must not carry placeholders')
        else:
            if isinstance(t, dict):
                err(f'{lab}: only pl_* keys may be objects')
                continue
            cmp_string(lab, en, t)
    return len(tr)


def walk(en, tr, path, n):
    if isinstance(en, dict):
        if not isinstance(tr, dict):
            err(f'texts:{path}: expected object')
            return n
        same(f'texts:{path}', list(en), list(tr), 'keys')
        for k in en:
            if k in tr:
                n = walk(en[k], tr[k], f'{path}.{k}', n)
    elif isinstance(en, list):
        if not isinstance(tr, list) or len(en) != len(tr):
            err(f'texts:{path}: list length differs')
            return n
        for i, (a, b) in enumerate(zip(en, tr)):
            n = walk(a, b, f'{path}[{i}]', n)
    elif isinstance(en, str):
        cmp_string(f'texts:{path}', en, tr)
        n += 1
    elif en != tr:
        err(f'texts:{path}: non-string value changed')
    return n


def check_texts():
    p = os.path.join(HERE, 'texts.json')
    if not os.path.exists(p):
        err('texts.json: missing')
        return 0
    tr = json.load(open(p))
    src = {'about_data': 'about_data.json', 'download': 'download.json'}
    flat = {'pay': 'pay.json', 'routes': 'routes.json'}  # L2 (LANG0 format): node path -> text
    same('texts.json', list(src) + ['sources_pages'] + list(flat), list(tr), 'top keys')
    n = 0
    for k, f in src.items():
        n = walk(json.load(open(os.path.join(WORLD, f)))['en'], tr.get(k), k, n)
    # sources_pages: same structure as EN; urls/kind unchanged, name/licence may be translated
    sp_en = json.load(open(os.path.join(WORLD, 'sources_pages.json')))
    sp = tr.get('sources_pages', {})
    same('texts:sources_pages', list(sp_en), list(sp), 'keys')
    for k, v in sp_en.items():
        t = sp.get(k, {})
        same(f'texts:sources_pages.{k}', list(v), list(t), 'fields')
        for f2, e in v.items():
            if f2 in ('url', 'licence_url', 'kind', 'attribution') or not isinstance(e, str):
                if t.get(f2) != e:
                    err(f'texts:sources_pages.{k}.{f2}: must stay as EN')
            elif not isinstance(t.get(f2), str) or not t.get(f2, '').strip():
                err(f'texts:sources_pages.{k}.{f2}: empty')
            else:
                n += 1
    for k, f in flat.items():
        nodes = []
        ml_nodes(json.load(open(os.path.join(WORLD, f))), '', nodes)
        got = tr.get(k, {})
        same(f'texts:{k}', [p for p, _ in nodes], list(got), 'node paths')
        for p, en in nodes:
            if p in got:
                cmp_string(f'texts:{k}.{p}', en, got[p])
                n += 1
    return n


def ml_nodes(o, p, out):
    """Multilingual nodes {en, sr|ru, ...} of pay.json / routes.json as (dot path, EN text)."""
    if isinstance(o, dict):
        if isinstance(o.get('en'), str) and ('sr' in o or 'ru' in o):
            out.append((p, o['en']))
            return
        for k, v in o.items():
            ml_nodes(v, f'{p}.{k}' if p else k, out)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            ml_nodes(v, f'{p}[{i}]', out)


def check_slugs():
    p = os.path.join(HERE, 'slugs.json')
    s = json.load(open(p))
    same('slugs.json', SLUG_KEYS, list(s), 'keys')
    for k, v in s.items():
        if k in SEGMENT_KEYS:
            if not SLUG.match(v):
                err(f'slugs.{k}: not an ASCII lowercase segment: {v}')
        else:
            if not v.startswith(f'/{LANG}/') or not v.endswith('/'):
                err(f'slugs.{k}: must be a full path /{LANG}/…/: {v}')
            segs = [x for x in v.strip('/').split('/')]
            for x in segs:
                if not SLUG.match(x):
                    err(f'slugs.{k}: bad segment {x!r}')
    paths = [v for k, v in s.items() if k not in SEGMENT_KEYS]
    if len(paths) != len(set(paths)):
        err('slugs.json: duplicate paths')
    return len(s)


def read_csv(name, cols):
    p = os.path.join(HERE, name)
    if not os.path.exists(p):
        err(f'{name}: missing')
        return []
    with open(p, newline='', encoding='utf-8') as f:
        r = csv.DictReader(f)
        if r.fieldnames != cols:
            err(f'{name}: columns {r.fieldnames} != {cols}')
        return list(r)


def check_countries():
    rows = read_csv('countries.csv', ['cc', 'name', 'slug', 'in_phrase', 'note'])
    src = [r['cc'] for r in csv.DictReader(open(os.path.join(NAMES, 'countries.csv'), newline=''))]
    got = [r['cc'] for r in rows]
    if sorted(got) != sorted(src):
        err(f'countries.csv: cc set differs (missing {sorted(set(src)-set(got))}, extra {sorted(set(got)-set(src))})')
    slugs = set()
    for r in rows:
        for c in ('name', 'slug', 'in_phrase'):
            if not r[c].strip():
                err(f'countries.csv:{r["cc"]}: empty {c}')
        if r['slug'] and not SLUG.match(r['slug']):
            err(f'countries.csv:{r["cc"]}: bad slug {r["slug"]}')
        if r['slug'] in slugs:
            err(f'countries.csv:{r["cc"]}: duplicate slug {r["slug"]}')
        slugs.add(r['slug'])
        if r['in_phrase'] and not re.match(r'^(у|в|на) ', r['in_phrase']):
            warn(f'countries.csv:{r["cc"]}: in_phrase without у/в/на: {r["in_phrase"]}')
    return len(rows)


def check_cities():
    rows = read_csv('cities.csv', ['geonameid', 'name', 'in_phrase', 'decl_ok', 'note'])
    src = {r['geonameid']: r for r in csv.DictReader(open(os.path.join(NAMES, 'cities.csv'), newline=''))}
    seen = set()
    for r in rows:
        g = r['geonameid']
        if g not in src:
            err(f'cities.csv:{g}: unknown geonameid')
        if g in seen:
            err(f'cities.csv:{g}: duplicate')
        seen.add(g)
        if not r['name'].strip() or not r['in_phrase'].strip():
            err(f'cities.csv:{g}: empty name/in_phrase')
        if r['decl_ok'] not in ('0', '1'):
            err(f'cities.csv:{g}: decl_ok must be 0/1')
        if r['in_phrase'] and not re.match(r'^(у|в|на) ', r['in_phrase']):
            warn(f'cities.csv:{g}: in_phrase without у/в/на: {r["in_phrase"]}')
    stage = {}
    for g, r in src.items():
        stage.setdefault(r['stage'], [0, 0])[0] += 1
        if g in seen:
            stage[r['stage']][1] += 1
    ua = [g for g, r in src.items() if r['cc'] == 'UA']
    miss_ua = [g for g in ua if g not in seen]
    if miss_ua:
        err(f'cities.csv: Ukrainian cities missing: {miss_ua}')
    return len(rows), stage


def main():
    out = {}
    for f in ('strings_map.json', 'strings_pages.json', 'strings_shell.json', 'strings_prices.json',
              'strings_pay.json', 'strings_press.json', 'strings_b2b.json', 'strings_embed.json'):
        out[f] = check_strings(f)
    out['texts.json strings'] = check_texts()
    out['slugs.json'] = check_slugs()
    out['countries.csv'] = check_countries()
    n, stage = check_cities()
    out['cities.csv'] = n
    for k, v in out.items():
        print(f'{k}: {v}')
    for s, (tot, got) in sorted(stage.items()):
        print(f'cities stage {s}: {got}/{tot}')
    for w in warnings:
        print('WARN', w)
    for e in errors:
        print('ERROR', e)
    print(f'{len(errors)} errors, {len(warnings)} warnings')
    sys.exit(1 if errors else 0)


if __name__ == '__main__':
    main()
