# -*- coding: utf-8 -*-
"""G4: turns the output of scripts/world_routes_calc.py (run on the mac against the public layer) into the small
content/world/routes.json the site builds from: per route the waypoints, distance estimate, counts, gaps, the stop list
and per-country fast-charger counts and networks. City names come from content/world/names/cities.csv.

    python3 scripts/world_routes_slim.py routes_g4.json content/world/routes.json
"""
import collections
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main(src, dst):
    r = json.load(open(src, encoding='utf-8'))
    cities = {row['geonameid']: row for row in csv.DictReader(open(ROOT / 'content/world/names/cities.csv', encoding='utf-8'))}
    out = {'v': 1, 'layer_date': r['date'], 'rule': r['rule'], 'routes': []}
    for rt in r['routes']:
        by = {s['pid']: s for s in rt['sites']}
        order, per = [], collections.OrderedDict()
        for s in rt['sites']:
            cc = s['cc'] or '?'
            if cc not in per:
                per[cc] = {'n': 0, 'hpc': 0, 'nets': collections.Counter()}
            per[cc]['n'] += 1
            per[cc]['hpc'] += s['cls'] == 5
            if s['net']:
                per[cc]['nets'][s['net']] += 1

        def city(s):
            c = cities.get(str(s['city'])) if s['city'] else None
            return {'en': c['name_en'], 'sr': c['name_sr'], 'ru': c['name_ru']} if c else None
        stops = []
        for pid in rt['stops']:
            s = by[pid]
            stops.append({k: s[k] for k in ('pid', 'km', 'off_km', 'lat', 'lon', 'cls', 'conf', 'net', 'name', 'kw', 'cc', 'pts')} | {'city': city(s)})
        out['routes'].append({
            'id': rt['id'], 'waypoints': rt['waypoints'], 'km': rt['km'], 'km_straight': rt['km_straight'],
            'n_fast': rt['n_fast'], 'n_hpc': rt['n_hpc'], 'gaps': rt['gaps'], 'stops': stops,
            'countries': [{'cc': cc, 'n': v['n'], 'hpc': v['hpc'], 'nets': v['nets'].most_common(6)} for cc, v in per.items() if cc != '?'],
        })
    json.dump(out, open(dst, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print(dst, len(out['routes']), 'routes')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
