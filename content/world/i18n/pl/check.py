#!/usr/bin/env python3
"""Check an L-task language pack: content/world/i18n/<code>/ against the EN sources.

Usage: python3 content/world/i18n/pl/check.py      (code = folder name)
Exit 1 on any error. Warnings do not fail.
"""
import csv, json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CODE = HERE.name
WORLD = HERE.parent.parent
NAMES = WORLD / 'names'

PH = re.compile(r'\{[a-z_0-9]+\}')
TAG = re.compile(r'</?[a-zA-Z][^>]*>')
ENT = re.compile(r'&[a-z]+;|&#\d+;')
# EN "in {city}" needs a declined slot in inflected languages; the engine passes all of them (world_pages.render_*).
EQUIV = {'{city}': {'{city_u}', '{city_v}'}, '{country}': {'{country_u}', '{country_v}'},
         '{country_u}': {'{country_v}'}, '{city_u}': {'{city_v}'},
         '{name}': {'{name_nom}'}}  # FIXL D14: {name_nom} may stand where EN has {name}
STRING_FILES = ['strings_home', 'strings_map', 'strings_pages', 'strings_shell', 'strings_prices',
                'strings_pay', 'strings_press', 'strings_b2b', 'strings_embed']
SLUG_KEYS = ['home', 'map', 'hub', 'net', 'about', 'download', 'gnet', 'prices', 'shell_about', 'sources', 'methodology']
FULL = {'home', 'map', 'hub', 'gnet', 'prices', 'shell_about', 'sources', 'methodology'}
EXTRA = ['pay', 'routes', 'press', 'b2b', 'embed', 'map_conf', 'developers']  # FIXL F5: allowed in addition (full paths)

err, warn = [], []


def cldr():
    from babel import Locale
    return set(Locale(CODE).plural_form.tags) | {'other'}


def ph_ok(en, tr):
    a, b = set(PH.findall(en)), set(PH.findall(tr))
    if a == b:
        return True
    extra, missing = b - a, a - b
    for m in list(missing):
        alt = EQUIV.get(m, set()) & extra
        if alt:
            missing.discard(m)
            extra -= alt
    return not missing and not extra


def check_str(where, en, tr):
    if not isinstance(tr, str) or not tr.strip():
        err.append(f'{where}: empty'); return
    if not ph_ok(en, tr):
        err.append(f'{where}: placeholders {sorted(set(PH.findall(en)))} vs {sorted(set(PH.findall(tr)))}')
    if [re.sub(r'\s.*', '', t) for t in TAG.findall(en)] != [re.sub(r'\s.*', '', t) for t in TAG.findall(tr)]:
        err.append(f'{where}: HTML tags differ')
    if sorted(ENT.findall(en)) != sorted(ENT.findall(tr)):
        err.append(f'{where}: entities differ')
    for href in re.findall(r'href="([^"]+)"', en):
        if href not in tr:
            err.append(f'{where}: link {href} lost')


def strings(cats):
    n = 0
    for f in STRING_FILES:
        p = HERE / f'{f}.json'
        if not p.exists():
            err.append(f'{f}.json missing'); continue
        en = {k: v['en'] for k, v in json.load(open(WORLD / f'{f}.json', encoding='utf-8')).items()}
        tr = json.load(open(p, encoding='utf-8'))
        for k in en:
            if k not in tr:
                err.append(f'{f}.{k}: key missing'); continue
            v, e = tr[k], en[k]
            n += 1
            plural = '|' in e and not e.endswith('| BlokVolt') and ' | ' not in e
            if plural:
                if not isinstance(v, dict):
                    err.append(f'{f}.{k}: plural must be an object with CLDR categories'); continue
                if set(v) != cats:
                    err.append(f'{f}.{k}: plural categories {sorted(v)} != CLDR {sorted(cats)}')
                for c, s in v.items():
                    check_str(f'{f}.{k}.{c}', e.split('|')[0], s)
            else:
                check_str(f'{f}.{k}', e, v)
        for k in tr:
            if k not in en:
                err.append(f'{f}.{k}: extra key')
        if list(tr) != list(en):
            warn.append(f'{f}: key order differs from EN')
    return n


def ml_nodes(o, p, out):
    """Paths of multilingual text nodes ({en: str, sr|ru: …}) in pay.json / routes.json, LANG0 notation a.b[i].c."""
    if isinstance(o, dict):
        if isinstance(o.get('en'), str) and ('sr' in o or 'ru' in o):
            out.append((p, o['en'])); return
        for k, v in o.items():
            ml_nodes(v, f'{p}.{k}' if p else k, out)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            ml_nodes(v, f'{p}[{i}]', out)


def texts():
    p = HERE / 'texts.json'
    if not p.exists():
        err.append('texts.json missing'); return 0
    t = json.load(open(p, encoding='utf-8'))
    src = {'about_data': json.load(open(WORLD / 'about_data.json', encoding='utf-8'))['en'],
           'download': json.load(open(WORLD / 'download.json', encoding='utf-8'))['en'],
           'sources_pages': json.load(open(WORLD / 'sources_pages.json', encoding='utf-8'))}
    cnt = [0, 0]

    def walk(a, b, path):
        if type(a) is not type(b):
            err.append(f'texts{path}: type {type(a).__name__} vs {type(b).__name__}'); return
        if isinstance(a, dict):
            if list(a) != list(b):
                err.append(f'texts{path}: keys differ')
            for k in a:
                if k in b:
                    walk(a[k], b[k], f'{path}.{k}')
        elif isinstance(a, list):
            if len(a) != len(b):
                err.append(f'texts{path}: list length {len(a)} vs {len(b)}')
            for i, (x, y) in enumerate(zip(a, b)):
                walk(x, y, f'{path}[{i}]')
        elif isinstance(a, str):
            cnt[0] += 1
            cnt[1] += a != b
            if a.strip():
                check_str(f'texts{path}', a, b)
        elif a != b:
            err.append(f'texts{path}: value changed')

    # L2/LANG0: multilingual nodes of pay.json / routes.json -> texts.json {pay|routes: {"a.b[i].c": text}}
    for sec in ('pay', 'routes'):
        nodes = []
        ml_nodes(json.load(open(WORLD / f'{sec}.json', encoding='utf-8')), '', nodes)
        got = t.get(sec)
        if got is None:
            err.append(f'texts.{sec} missing'); continue
        want = dict(nodes)
        for path, en in want.items():
            if path not in got:
                err.append(f'texts.{sec}["{path}"]: missing'); continue
            cnt[0] += 1
            cnt[1] += got[path] != en
            check_str(f'texts.{sec}["{path}"]', en, got[path])
        for path in got:
            if path not in want:
                err.append(f'texts.{sec}["{path}"]: no such multilingual node')
        if list(got) != list(want):
            warn.append(f'texts.{sec}: key order differs from the source file')
    for k, v in src.items():
        if k not in t:
            err.append(f'texts.{k} missing')
        else:
            walk(v, t[k], '.' + k)
    for sid, s in src['sources_pages'].items():
        for fld in ('name', 'url', 'licence_url', 'attribution', 'kind'):
            if fld in s and t.get('sources_pages', {}).get(sid, {}).get(fld) != s[fld]:
                err.append(f'texts.sources_pages.{sid}.{fld}: must stay as in EN')
    return cnt


def slugs():
    s = json.load(open(HERE / 'slugs.json', encoding='utf-8'))
    if list(s)[:len(SLUG_KEYS)] != SLUG_KEYS or set(s) - set(SLUG_KEYS) - set(EXTRA):
        err.append(f'slugs.json keys {list(s)}: need {SLUG_KEYS}, then optional {EXTRA}')
    for k, v in s.items():
        if k in EXTRA:
            if not re.fullmatch(rf'/{CODE}/([a-z0-9]+(-[a-z0-9]+)*/)+', v):
                err.append(f'slugs.{k}: {v!r} not /{CODE}/…/ ASCII lowercase')
        elif k in FULL:
            if not re.fullmatch(rf'/{CODE}/([a-z0-9]+(-[a-z0-9]+)*/)?', v):
                err.append(f'slugs.{k}: {v!r} not /{CODE}/…/ ASCII lowercase')
        elif not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', v):
            err.append(f'slugs.{k}: {v!r} not one ASCII segment')
    full = [v for k, v in s.items() if k in FULL or k in EXTRA]
    if len(set(full)) != len(full):
        err.append('slugs: duplicate paths')


def csvs():
    src_c = [r['cc'] for r in csv.DictReader(open(NAMES / 'countries.csv', encoding='utf-8'))]
    rows = list(csv.DictReader(open(HERE / 'countries.csv', encoding='utf-8')))
    if rows and list(rows[0]) not in (['cc', 'name', 'slug', 'in_phrase', 'note'], ['cc', 'name', 'slug', 'in_phrase', 'note', 'name_nom']):
        err.append(f'countries.csv header {list(rows[0])}')
    if [r['cc'] for r in rows] != src_c:
        err.append(f'countries.csv: {len(rows)} rows, cc list differs from names/countries.csv ({len(src_c)})')
    sl = [r['slug'] for r in rows]
    if len(set(sl)) != len(sl):
        err.append('countries.csv: duplicate slugs')
    for r in rows:
        if not (r['name'] and r['in_phrase']):
            err.append(f"countries.csv {r['cc']}: empty name/in_phrase")
        if not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', r['slug']):
            err.append(f"countries.csv {r['cc']}: slug {r['slug']!r}")
    src_g = [r['geonameid'] for r in csv.DictReader(open(NAMES / 'cities.csv', encoding='utf-8'))]
    p = HERE / 'cities.csv'
    if not p.exists():
        err.append('cities.csv missing'); return len(rows), 0, 0
    cr = list(csv.DictReader(open(p, encoding='utf-8')))
    if cr and list(cr[0]) != ['geonameid', 'name', 'in_phrase', 'decl_ok', 'note']:
        err.append(f'cities.csv header {list(cr[0])}')
    ids = [r['geonameid'] for r in cr]
    if len(set(ids)) != len(ids) or not set(ids) <= set(src_g):
        err.append('cities.csv: duplicate or unknown geonameid')
    if len(ids) < len(src_g):
        warn.append(f'cities.csv: {len(ids)} of {len(src_g)} cities (rest falls back to EN)')
    for r in cr:
        if not (r['name'] and r['in_phrase']) or r['decl_ok'] not in ('0', '1'):
            err.append(f"cities.csv {r['geonameid']}: empty field or bad decl_ok")
    # FIXL: every city page of state/pages_state.json must have a row
    ps = WORLD / 'state' / 'pages_state.json'
    if ps.exists():
        page_g = {v['key'].split(':')[-1] for v in json.load(open(ps, encoding='utf-8')).values()
                  if v.get('type') == 'city' and str(v.get('key', '')).startswith('t:')}
        if page_g - set(ids):
            err.append(f'cities.csv: {len(page_g - set(ids))} city pages without a row, e.g. {sorted(page_g - set(ids))[:5]}')
    else:
        warn.append('state/pages_state.json not found: city pages not checked')
    return len(rows), len(cr), sum(r['decl_ok'] == '1' for r in cr)


def style():
    bad = re.compile(r'\b(my|nasz\w*|prosimy|dziękujemy|zapraszamy|redakcj\w*|24/7|od razu|natychmiast\w*)\b', re.I)
    for f in HERE.glob('*.json'):
        for m in bad.finditer(f.read_text(encoding='utf-8')):
            warn.append(f'{f.name}: style word {m.group(0)!r}')


if __name__ == '__main__':
    cats = cldr()
    n = strings(cats)
    tc = texts()
    slugs()
    nc, ncity, ndecl = csvs()
    style()
    print(f'[{CODE}] CLDR plural categories: {sorted(cats)}')
    print(f'[{CODE}] strings checked: {n}; texts strings: {tc[0] if tc else 0} (changed vs EN: {tc[1] if tc else 0}); '
          f'countries: {nc}; cities: {ncity} (decl_ok=1: {ndecl})')
    for w in warn:
        print('WARN', w)
    for e in err:
        print('ERR ', e)
    print(f'[{CODE}] {len(err)} errors, {len(warn)} warnings')
    sys.exit(1 if err else 0)
