# -*- coding: utf-8 -*-
"""Builds the K6 fixture (world map reports) from real rows of the world snapshot: ~40 sites in Berlin, Paris,
Amsterdam and San Francisco with a mix of weak single-source, protected (confidence ≥ 70 or a government registry) and
multi-source sites; the K1 layer, latest.json + manifest + cards (Berlin's geohash-3 prefix is split into 4-char card
files) and an export of crafted reports so that every rule of scripts/world_reports.py fires once.

  python3 scripts/qa/fixtures/svet/make_fixture.py [/home/claude/data/sites_world.csv.gz]

Writes next to itself: layer.geojsonseq, data/latest.json, data/manifest-2026-11-09.json,
data/cards-2026-11-09/<prefix>.json, reports.json (with "fixture.roles": role -> pid, used by the tests).
"""
import csv
import gzip
import json
import math
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from world_reports import geohash  # noqa: E402

DATE = '2026-11-09'
SRC = sys.argv[1] if len(sys.argv) > 1 else '/home/claude/data/sites_world.csv.gz'
GOV = {'bnetza': 'Bundesnetzagentur Ladesäulenregister', 'afdc': 'US DOE AFDC', 'irve': 'data.gouv.fr IRVE',
       'ndw': 'NDW (NL)'}
OTHER = {'osm': 'OpenStreetMap', 'ocm': 'Open Charge Map', 'atp': 'All the Places', 'ovt': 'Overture',
         'ovt_atp': 'Overture (ATP)'}
CITIES = {  # cc: (lat0, lat1, lon0, lon1)
    'DE': (52.45, 52.56, 13.30, 13.50),
    'FR': (48.82, 48.90, 2.28, 2.40),
    'NL': (52.33, 52.40, 4.85, 4.95),
    'US': (37.73, 37.80, -122.45, -122.39),
}
QUOTA = {'lo1': 4, 'gov1': 1, 'hi1': 2, 'multi': 3, 'himulti': 1}
SPLIT = ['u33']   # Berlin: card files u33<x>.json


def category(row):
    src = row['sources'].split(',')
    conf = float(row['confidence'] or 0)
    gov = any(s in GOV for s in src)
    if len(src) == 1:
        if gov:
            return 'gov1' if conf < 70 else None
        return 'lo1' if conf < 70 else 'hi1'
    if not gov and conf < 70:
        return 'multi'
    return 'himulti' if conf >= 70 else None


def pick():
    got = {cc: {k: [] for k in QUOTA} for cc in CITIES}
    with gzip.open(SRC, 'rt', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            cc = row['country_iso2']
            if cc not in CITIES or row.get('map_ok') != '1':
                continue
            k = category(row)
            a, b, c, d = CITIES[cc]
            # weak and multi-source sites from one city (Berlin shares a geohash-3 prefix -> split cards); the rare
            # protected single-source sites from anywhere in the country
            if k not in ('hi1', 'gov1') and not (a <= float(row['lat']) <= b and c <= float(row['lon']) <= d):
                continue
            if k and len(got[cc][k]) < QUOTA[k]:
                got[cc][k].append(row)
            if all(len(got[x][k]) >= QUOTA[k] for x in got for k in QUOTA):
                break
    return got


def num(x, f=float):
    try:
        return f(float(x))
    except (TypeError, ValueError):
        return None


PCODE = {'unknown': 0, 'ac_slow_7': 1, 'ac_11_22': 2, 'dc_under_50': 3, 'dc_fast_50_149': 4, 'hpc_150plus': 5,
         'ac_power_unknown': 6, 'dc_power_unknown': 7}


def main():
    got = pick()
    rows = [r for cc in got for k in QUOTA for r in got[cc][k]]
    nets = sorted({r['operator_canonical'] for r in rows if r['operator_canonical']})
    layer, cards = [], {}
    for r in rows:
        pid, lat, lon = int(r['site_id']), float(r['lat']), float(r['lon'])
        src = r['sources'].split(',')
        gov = any(s in GOV for s in src)
        # attributes exactly as contract v1 §3 (tiles) and §4 (cards)
        pc = PCODE.get(r['power_class'], 0)
        acc = r['access_class'] or ''
        a = 0 if acc.startswith('public') else 1 if acc.startswith(('restricted', 'private')) else 2
        sbits = 0
        for x in src:
            sbits |= 1 if x in GOV else 2 if x in ('osm', 'ocm') else 4 if x in ('atp', 'overture') else 0
        conf = num(r['confidence'], int)
        layer.append({'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [round(lon, 6), round(lat, 6)]},
                      'properties': {'i': pid, 'p': pc,
                                     'o': nets.index(r['operator_canonical']) + 1 if r['operator_canonical'] else 0,
                                     'c': int(round((conf or 0) / 5.0) * 5), 'a': a, 's': sbits}})
        g = geohash(lat, lon, 5)
        n = 3
        while g[:n] in SPLIT:
            n += 1
        conn = []
        for part in (r['connector_types'] or '').split(','):
            if part:
                t, _, k = part.partition('x')
                conn.append([t, int(k) if k.isdigit() else 1, num(r['max_power_kw'])])
        cards.setdefault(g[:n], {})[str(pid)] = {
            'n': r['name'] or None, 'net': r['operator_canonical'] or None, 'kw': num(r['max_power_kw']),
            'dc': r['has_dc'] == '1', 'p': pc, 'conn': conn,
            'pts': num(r['num_points_est'], int), 'acc': acc or None, 'cc': r['country_iso2'],
            'city': None,
            'src': [{'k': x, 'u': None} for x in src],
            'lc': (r['last_confirmed'] or '')[:7] or None, 'conf': conf, 'osm': None, 'more': None}

    data = HERE / 'data'
    if data.exists():
        shutil.rmtree(data)
    (data / f'cards-{DATE}').mkdir(parents=True)
    (HERE / 'layer.geojsonseq').write_text(''.join(json.dumps(f, ensure_ascii=False) + '\n' for f in layer),
                                            encoding='utf-8')
    for prefix, sites in sorted(cards.items()):
        (data / f'cards-{DATE}' / f'{prefix}.json').write_text(
            json.dumps({'v': 1, 'date': DATE, 'sites': sites}, ensure_ascii=False), encoding='utf-8')
    (data / 'latest.json').write_text(json.dumps({'date': DATE, 'manifest': f'manifest-{DATE}.json'}) + '\n')
    manifest = {'v': 1, 'date': DATE, 'sites': len(rows), 'cards_base': f'cards-{DATE}', 'cards_split': SPLIT,
                'cards_files': len(cards), 'layer': 'public_sites.geojsonseq',
                'sources': [{'k': k, 'name': v, 'gov': True} for k, v in GOV.items()]
                + [{'k': k, 'name': v, 'gov': False} for k, v in OTHER.items()],
                'networks': [None] + nets}
    (data / f'manifest-{DATE}.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + '\n')

    # ---------------------------------------------------------------------------------------------- reports
    def pid(cc, k, i=0):
        return int(got[cc][k][i]['site_id'])

    def site(p):
        r = next(x for x in rows if int(x['site_id']) == p)
        return float(r['lat']), float(r['lon'])

    def off(p, north_m, east_m):
        lat, lon = site(p)
        return round(lat + north_m / 111_195, 6), round(lon + east_m / (111_195 * math.cos(math.radians(lat))), 6)

    roles = {
        'hide': pid('DE', 'lo1', 0), 'same_ip': pid('DE', 'lo1', 1), 'undo_hide': pid('DE', 'lo1', 2),
        'admin_move': pid('DE', 'lo1', 3), 'conf70': pid('DE', 'hi1', 0), 'gov': pid('NL', 'gov1', 0),
        'multi': pid('DE', 'multi', 0),
        'move': pid('FR', 'lo1', 0), 'move_disagree': pid('FR', 'lo1', 1), 'move_far': pid('FR', 'lo1', 2),
        'move_single': pid('FR', 'hi1', 0),
        'access': pid('NL', 'lo1', 0), 'access_protected': pid('NL', 'hi1', 0), 'snaga': pid('NL', 'lo1', 1),
        'drugo': pid('NL', 'multi', 0), 'undo_access': pid('NL', 'lo1', 2), 'old_spam': pid('NL', 'hi1', 1),
        'spam_link': pid('US', 'lo1', 0), 'spam_rude_sr': pid('US', 'lo1', 1), 'spam_rude_ru': pid('US', 'lo1', 2),
        'spam_rude_en': pid('US', 'hi1', 0), 'repeat_a': pid('US', 'multi', 0), 'repeat_b': pid('US', 'multi', 1),
        'repeat_c': pid('US', 'himulti', 0), 'ip_text_a': pid('US', 'gov1', 0), 'ip_text_b': pid('NL', 'multi', 1),
        'balkan': 900000017, 'unknown': 77,
    }
    now = 1794225600   # 2026-11-09 12:00 UTC, the export's "now"
    t0 = now - 86400
    reps = []

    def add(p, typ, ip, text=None, lat=None, lon=None, lang='en', dt=0, **kw):
        r = {'id': len(reps) + 1, 'pid': p, 'type': typ, 'text': text, 'lat': lat, 'lon': lon, 'lang': lang,
             'ip_hash': ip, 'created_at': t0 + dt + len(reps) * 60, 'status': 'new', 'decided_at': None,
             'decided_by': None, 'rule': None, 'action': None, 'access': None, 'alat': None, 'alon': None,
             'cc': kw.pop('cc', None), 'g': None}
        r.update(kw)
        reps.append(r)

    ip = lambda n: f'{n:024x}'  # noqa: E731
    old = {'created_at': t0 - 20 * 86400}
    # decided rows first (older)
    add(roles['undo_hide'], 'ne_radi', ip(101), status='rejected', decided_at=t0 - 10 * 86400, decided_by='admin',
        rule='undo', action='unhide', **old)
    add(roles['undo_hide'], 'ne_postoji', ip(102), status='rejected', decided_at=t0 - 10 * 86400, decided_by='admin',
        rule='undo', action='unhide', **old)
    a = off(roles['admin_move'], 40, 10)
    add(roles['admin_move'], 'lokacija', ip(103), lat=a[0], lon=a[1], status='accepted', decided_at=t0 - 5 * 86400,
        decided_by='admin', rule='admin', action='move', alat=a[0], alon=a[1], **old)
    add(roles['undo_access'], 'nije_javni', ip(104), text='Parking samo za stanare', lang='sr', status='rejected',
        decided_at=t0 - 3 * 86400, decided_by='admin', rule='undo', action='none', **old)
    add(roles['old_spam'], 'drugo', ip(105), text='buy cheap chargers', status='rejected', decided_at=t0 - 15 * 86400,
        decided_by='auto', rule='spam_insert', action='none', **old)
    add(roles['drugo'], 'drugo', ip(106), text='Treba proveriti radno vreme', lang='sr', status='postponed', **old)
    # new rows
    add(roles['hide'], 'ne_radi', ip(1), text='Charger is dead, screen off')
    add(roles['hide'], 'ne_postoji', ip(2), text='Nothing here any more', lang='en')
    add(roles['same_ip'], 'ne_radi', ip(3), text='ne radi')
    add(roles['same_ip'], 'ne_radi', ip(3), text='i dalje ne radi', dt=3600)
    add(roles['conf70'], 'ne_radi', ip(4))
    add(roles['conf70'], 'ne_postoji', ip(5))
    add(roles['gov'], 'ne_postoji', ip(6))
    add(roles['gov'], 'ne_postoji', ip(7))
    add(roles['multi'], 'ne_radi', ip(8))
    add(roles['multi'], 'ne_radi', ip(9))
    p1, p2 = off(roles['move'], 40, 0), off(roles['move'], 46, 8)
    add(roles['move'], 'lokacija', ip(10), lat=p1[0], lon=p1[1], text="L'entrée est rue derrière")
    add(roles['move'], 'lokacija', ip(11), lat=p2[0], lon=p2[1])
    p1, p2 = off(roles['move_disagree'], 60, 0), off(roles['move_disagree'], -60, 0)
    add(roles['move_disagree'], 'lokacija', ip(12), lat=p1[0], lon=p1[1])
    add(roles['move_disagree'], 'lokacija', ip(13), lat=p2[0], lon=p2[1])
    p1, p2 = off(roles['move_far'], 400, 0), off(roles['move_far'], 30, 0)
    add(roles['move_far'], 'lokacija', ip(14), lat=p1[0], lon=p1[1])
    add(roles['move_far'], 'lokacija', ip(15), lat=p2[0], lon=p2[1])
    p1 = off(roles['move_single'], 20, 20)
    add(roles['move_single'], 'lokacija', ip(16), lat=p1[0], lon=p1[1])
    add(roles['access'], 'nije_javni', ip(17), text='Alleen voor bewoners van de garage', lang='en')
    add(roles['access_protected'], 'nije_javni', ip(18))
    add(roles['snaga'], 'snaga', ip(19), text='Only 11 kW, not 22')
    add(roles['drugo'], 'drugo', ip(20), text='Kabl je oštećen', lang='sr')
    add(roles['spam_link'], 'drugo', ip(21), text='Best deals at cheapcharge.shop now')
    add(roles['spam_rude_sr'], 'ne_radi', ip(22), text='Jebem ti ovaj punjač', lang='sr')
    add(roles['spam_rude_ru'], 'ne_radi', ip(23), text='Нихуя не работает, бля', lang='ru')
    add(roles['spam_rude_en'], 'drugo', ip(24), text='this shit never works')
    rep = 'Call me for a better charger offer!'
    add(roles['repeat_a'], 'drugo', ip(25), text=rep)
    add(roles['repeat_b'], 'drugo', ip(26), text=rep.upper())
    add(roles['repeat_c'], 'drugo', ip(27), text=rep + ' ')
    add(roles['ip_text_a'], 'ne_radi', ip(28), text='Ovo je lažna stanica')
    add(roles['ip_text_b'], 'ne_radi', ip(28), text='ovo je lažna stanica!', lang='sr')
    add(roles['balkan'], 'ne_radi', ip(29), cc='RS', lang='sr')
    add(roles['unknown'], 'ne_postoji', ip(30))
    export = {'ok': True, 'now': now, 'reports': reps, 'fixture': {'date': DATE, 'roles': roles}}
    (HERE / 'reports.json').write_text(json.dumps(export, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    total = sum(f.stat().st_size for f in HERE.rglob('*') if f.is_file())
    print(f'{len(rows)} sites ({", ".join(f"{cc} {sum(len(v) for v in got[cc].values())}" for cc in got)}), '
          f'{len(cards)} card files, {len(reps)} reports, {total // 1024} KB')


if __name__ == '__main__':
    main()
