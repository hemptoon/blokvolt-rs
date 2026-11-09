#!/usr/bin/env python3
"""Check content/world/names/*.csv (K4, contract v1 §7).

python3 content/world/names/check_names.py [names_dir] [--report out.md]   -> exit 1 on errors
python3 content/world/names/check_names.py --selftest

Checks: columns, uniqueness (ids, slugs per country / globally), ASCII slugs, no empty values, scripts
(Cyrillic only in ru / mk / bg columns, Serbian columns Latin only, Greek only in el), case forms start with the
right preposition and the fallback forms match decl_ok, Kosovo and North Macedonia as in RUNBOOK §3.10.
"""
import csv
import os
import re
import sys
import tempfile

SLUG = re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*$')
CYR = re.compile('[Ѐ-ӿ]')
GREEK = re.compile('[Ͱ-Ͽἀ-῿]')
NONLATIN = re.compile('[^\u0000-\u02AFḀ-ỿ -⁯·]')
FUTURE = ['hr', 'bs', 'sl', 'mk', 'sq', 'de', 'fr', 'it', 'es', 'pt', 'nl', 'pl', 'cs', 'sk', 'hu', 'ro', 'bg',
          'el', 'tr']
COLS = {
    'countries.csv': ['cc', 'name_en', 'name_sr', 'name_ru', 'slug_en', 'slug_sr', 'slug_ru', 'sr_u', 'ru_v'] +
                     ['name_' + l for l in FUTURE] + ['note'],
    'cities.csv': ['geonameid', 'cc', 'name_local', 'name_en', 'name_sr', 'name_ru', 'slug', 'sr_u', 'ru_v',
                   'decl_ok', 'note', 'stage', 'decl_ok_sr', 'decl_ok_ru'],
    'networks.csv': ['network', 'name_display', 'slug', 'note', 'kind'],
    'glossary.csv': ['key', 'en', 'sr', 'ru', 'hr', 'bs', 'sr_me', 'sl', 'mk', 'sq', 'de', 'fr', 'it', 'es', 'pl',
                     'note'],
}
OPTIONAL = {'note', 'kind'}
CYR_OK = {'name_ru', 'ru', 'ru_v', 'name_mk', 'mk', 'name_bg'}
LATIN_ONLY = {'name_sr', 'sr', 'sr_u', 'sr_me', 'name_hr', 'hr', 'name_bs', 'bs', 'slug', 'slug_en', 'slug_sr',
              'slug_ru', 'name_en', 'en', 'sq', 'name_sq', 'sl', 'name_sl', 'de', 'name_de', 'fr', 'name_fr',
              'it', 'name_it', 'es', 'name_es', 'pl', 'name_pl', 'name_pt', 'name_nl', 'name_cs', 'name_sk',
              'name_hu', 'name_ro', 'name_tr'}
LOCAL_SCRIPT = {'name_local', 'name_display', 'note', 'name_el', 'network'}  # any script allowed


def read(p):
    with open(p, newline='', encoding='utf-8') as f:
        r = csv.DictReader(f)
        return r.fieldnames or [], list(r)


def check(d):
    errors, warns, stats = [], [], {}

    def err(f, i, m):
        errors.append(f'{f}:{i + 2}: {m}')

    data = {}
    for fn, cols in COLS.items():
        p = os.path.join(d, fn)
        if not os.path.exists(p):
            errors.append(f'{fn}: missing')
            continue
        head, rows = read(p)
        data[fn] = rows
        stats[fn] = len(rows)
        if head != cols:
            errors.append(f'{fn}: columns {head} != {cols}')
            continue
        for i, r in enumerate(rows):
            for c in cols:
                v = r[c] or ''
                if not v.strip() and c not in OPTIONAL:
                    err(fn, i, f'empty {c}')
                if v != v.strip():
                    err(fn, i, f'spaces around {c}')
                if c in LOCAL_SCRIPT or not v:
                    continue
                if CYR.search(v) and c not in CYR_OK:
                    err(fn, i, f'Cyrillic in {c}: {v}')
                if c in LATIN_ONLY and NONLATIN.search(v):
                    err(fn, i, f'non-Latin in {c}: {v}')
                if c in ('name_ru', 'ru', 'ru_v') and not CYR.search(v) and fn != 'glossary.csv':
                    err(fn, i, f'no Cyrillic in {c}: {v}')
                if GREEK.search(v) and c != 'name_el':
                    err(fn, i, f'Greek in {c}: {v}')
            for c in cols:
                if c.startswith('slug') and r[c] and not SLUG.match(r[c]):
                    err(fn, i, f'bad slug {c}={r[c]}')

    def uniq(fn, key, scope=None):
        seen = {}
        for i, r in enumerate(data.get(fn, [])):
            k = (r[scope], r[key]) if scope else r[key]
            if k in seen:
                err(fn, i, f'duplicate {key} {k} (also line {seen[k] + 2})')
            seen[k] = i

    uniq('countries.csv', 'cc')
    for c in ('slug_en', 'slug_sr', 'slug_ru'):
        uniq('countries.csv', c)
    uniq('cities.csv', 'geonameid')
    uniq('cities.csv', 'slug', 'cc')
    uniq('networks.csv', 'network')
    uniq('networks.csv', 'slug')
    uniq('glossary.csv', 'key')

    for fn, (u, v) in {'countries.csv': ('sr_u', 'ru_v'), 'cities.csv': ('sr_u', 'ru_v')}.items():
        for i, r in enumerate(data.get(fn, [])):
            if not re.match(r'^(u|na) \S', r[u]):
                err(fn, i, f'{u} must start with "u "/"na ": {r[u]}')
            if not re.match(r'^(в|во|на) \S', r[v]):
                err(fn, i, f'{v} must start with "в "/"во "/"на ": {r[v]}')
    cities = data.get('cities.csv', [])
    for i, r in enumerate(cities):
        if r['decl_ok'] not in ('0', '1') or r['decl_ok_sr'] not in ('0', '1') or r['decl_ok_ru'] not in ('0', '1'):
            err('cities.csv', i, 'decl_ok* must be 0/1')
            continue
        if r['decl_ok'] != str(int(r['decl_ok_sr'] == '1' and r['decl_ok_ru'] == '1')):
            err('cities.csv', i, 'decl_ok != decl_ok_sr AND decl_ok_ru')
        if (r['decl_ok_sr'] == '0') != r['sr_u'].startswith('u gradu '):
            err('cities.csv', i, f'decl_ok_sr={r["decl_ok_sr"]} but sr_u={r["sr_u"]}')
        if (r['decl_ok_ru'] == '0') != r['ru_v'].startswith('в городе '):
            err('cities.csv', i, f'decl_ok_ru={r["decl_ok_ru"]} but ru_v={r["ru_v"]}')
        if r['stage'] not in ('month', 'quarter', 'balkan'):
            err('cities.csv', i, f'bad stage {r["stage"]}')
    order = [{'month': 0, 'quarter': 1, 'balkan': 2}.get(r['stage'], 9) for r in cities]
    if order != sorted(order):
        errors.append('cities.csv: order must be month, quarter, balkan')
    cc = {r['cc']: r for r in data.get('countries.csv', [])}
    for code, field, want in [('XK', 'name_en', 'Kosovo'), ('XK', 'name_sr', 'Kosovo'),
                              ('MK', 'name_en', 'North Macedonia'), ('MK', 'name_sr', 'Severna Makedonija'),
                              ('MK', 'name_mk', 'Северна Македонија')]:
        if code in cc and cc[code][field] != want:
            errors.append(f'countries.csv: {code} {field}={cc[code][field]!r}, RUNBOOK §3.10 wants {want!r}')
    if cities:
        n = len(cities)
        ok = sum(r['decl_ok'] == '1' for r in cities)
        stats['decl_ok'] = f'{ok}/{n} ({100 * ok / n:.1f} %)'
        stats['decl_ok_sr'] = sum(r['decl_ok_sr'] == '1' for r in cities)
        stats['decl_ok_ru'] = sum(r['decl_ok_ru'] == '1' for r in cities)
        for s in ('month', 'quarter', 'balkan'):
            stats['cities_' + s] = sum(r['stage'] == s for r in cities)
        stats['cities_with_note'] = sum(bool(r['note']) for r in cities)
    nets = data.get('networks.csv', [])
    if nets:
        stats['networks_host'] = sum('хост' in r['note'] for r in nets)
        stats['networks_dup'] = sum('дубль' in r['note'] for r in nets)
    return errors, warns, stats


def report(d, out=None):
    errors, warns, stats = check(d)
    lines = ['# check_names report', '', f'Folder: `{d}`', '', '## Counts', '']
    lines += [f'- {k}: {v}' for k, v in stats.items()]
    lines += ['', f'## Errors: {len(errors)}', ''] + [f'- {e}' for e in errors[:300]]
    if len(errors) > 300:
        lines.append(f'- … and {len(errors) - 300} more')
    text = '\n'.join(lines) + '\n'
    if out:
        with open(out, 'w', encoding='utf-8') as f:
            f.write(text)
    print(text if len(text) < 6000 else text[:6000] + '\n…')
    return 1 if errors else 0


def selftest():
    d = tempfile.mkdtemp()

    def w(fn, rows):
        with open(os.path.join(d, fn), 'w', newline='', encoding='utf-8') as f:
            wr = csv.DictWriter(f, fieldnames=COLS[fn], lineterminator='\n')
            wr.writeheader()
            for r in rows:
                wr.writerow(r)

    country = {'cc': 'DE', 'name_en': 'Germany', 'name_sr': 'Nemačka', 'name_ru': 'Германия', 'slug_en': 'germany',
               'slug_sr': 'nemacka', 'slug_ru': 'germaniya', 'sr_u': 'u Nemačkoj', 'ru_v': 'в Германии', 'note': ''}
    country.update({'name_' + l: 'Deutschland' for l in FUTURE})
    country.update(name_mk='Германија', name_bg='Германия', name_el='Γερμανία')
    city = {'geonameid': '1', 'cc': 'DE', 'name_local': 'München', 'name_en': 'Munich', 'name_sr': 'Minhen',
            'name_ru': 'Мюнхен', 'slug': 'munchen', 'sr_u': 'u Minhenu', 'ru_v': 'в Мюнхене', 'decl_ok': '1',
            'note': '', 'stage': 'month', 'decl_ok_sr': '1', 'decl_ok_ru': '1'}
    net = {'network': 'IONITY', 'name_display': 'IONITY', 'slug': 'ionity', 'note': '', 'kind': 'cpo'}
    gl = {k: 'x' for k in COLS['glossary.csv']}
    gl.update(key='kw', ru='кВт', mk='kW')
    w('countries.csv', [country]); w('cities.csv', [city]); w('networks.csv', [net]); w('glossary.csv', [gl])
    e, _, s = check(d)
    assert not e, e
    bad = dict(city, geonameid='2', slug='munchen', name_sr='Минхен', decl_ok='1', decl_ok_ru='0')
    w('cities.csv', [city, bad])
    e, _, _ = check(d)
    assert any('duplicate slug' in x for x in e) and any('Cyrillic in name_sr' in x for x in e) \
        and any('decl_ok !=' in x for x in e), e
    print('check_names selftest ok')
    return 0


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[:1] == ['--selftest']:
        sys.exit(selftest())
    rep = None
    if '--report' in a:
        i = a.index('--report')
        rep = a[i + 1]
        a = a[:i] + a[i + 2:]
    sys.exit(report(a[0] if a else os.path.dirname(os.path.abspath(__file__)), rep))
