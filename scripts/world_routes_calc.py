# -*- coding: utf-8 -*-
"""G4 — fast chargers along 17 Balkan routes, from the public world layer (K1).

Rule (bvcom README G4, STATUS 09.11): public places, DC >= 50 kW (power classes dc_fast_50_149 / hpc_150plus),
confidence >= 70, within CORRIDOR_KM of the route polyline; a stop list with a step <= 150 km; gaps reported.
The polyline is the chain of waypoints (motorway towns); the distance is the straight-segment length + ROAD_FACTOR,
an estimate that the page states as such.

usage: python3 route_calc.py <layer_dir> <out.json>
layer_dir holds public_sites.geojsonseq.gz, manifest-*.json, places-*.json, cards-*.tar.gz (or the unpacked dir)
"""
import glob
import gzip
import json
import math
import os
import sys
import tarfile

CORRIDOR_KM = 5.0
STEP_KM = 150.0
ROAD_FACTOR = 1.15
MIN_CONF = 70

# id, waypoints (name, lat, lon) — motorway towns in driving order
ROUTES = [
    ('munich-belgrade', [('München', 48.137, 11.575), ('Salzburg', 47.809, 13.055), ('Villach', 46.610, 13.855),
                         ('Ljubljana', 46.056, 14.506), ('Zagreb', 45.815, 15.982), ('Slavonski Brod', 45.160, 18.016),
                         ('Beograd', 44.787, 20.457)]),
    ('vienna-belgrade', [('Wien', 48.208, 16.373), ('Győr', 47.687, 17.650), ('Budapest', 47.498, 19.040),
                         ('Kecskemét', 46.906, 19.692), ('Szeged', 46.253, 20.148), ('Subotica', 46.100, 19.667),
                         ('Novi Sad', 45.267, 19.833), ('Beograd', 44.787, 20.457)]),
    ('budapest-belgrade', [('Budapest', 47.498, 19.040), ('Kecskemét', 46.906, 19.692), ('Szeged', 46.253, 20.148),
                           ('Subotica', 46.100, 19.667), ('Novi Sad', 45.267, 19.833), ('Beograd', 44.787, 20.457)]),
    ('belgrade-zagreb', [('Beograd', 44.787, 20.457), ('Slavonski Brod', 45.160, 18.016), ('Zagreb', 45.815, 15.982)]),
    ('belgrade-thessaloniki', [('Beograd', 44.787, 20.457), ('Jagodina', 43.977, 21.261), ('Niš', 43.321, 21.896),
                               ('Vranje', 42.551, 21.900), ('Kumanovo', 42.132, 21.714), ('Skopje', 41.998, 21.425),
                               ('Veles', 41.716, 21.775), ('Gevgelija', 41.141, 22.502), ('Thessaloniki', 40.640, 22.944)]),
    ('belgrade-istanbul', [('Beograd', 44.787, 20.457), ('Jagodina', 43.977, 21.261), ('Niš', 43.321, 21.896),
                           ('Pirot', 43.153, 22.586), ('Sofia', 42.698, 23.322), ('Plovdiv', 42.142, 24.750),
                           ('Haskovo', 41.934, 25.555), ('Edirne', 41.677, 26.556), ('Lüleburgaz', 41.405, 27.356),
                           ('İstanbul', 41.015, 28.979)]),
    ('belgrade-podgorica-budva', [('Beograd', 44.787, 20.457), ('Čačak', 43.891, 20.350), ('Užice', 43.858, 19.848),
                                  ('Prijepolje', 43.390, 19.648), ('Bijelo Polje', 43.038, 19.747),
                                  ('Kolašin', 42.822, 19.517), ('Podgorica', 42.441, 19.263), ('Budva', 42.286, 18.840)]),
    ('belgrade-sarajevo', [('Beograd', 44.787, 20.457), ('Šabac', 44.756, 19.690), ('Loznica', 44.534, 19.223),
                           ('Zvornik', 44.386, 19.102), ('Vlasenica', 44.182, 18.940), ('Sarajevo', 43.856, 18.413)]),
    ('zagreb-sarajevo', [('Zagreb', 45.815, 15.982), ('Slavonski Brod', 45.160, 18.016), ('Doboj', 44.732, 18.084),
                         ('Zenica', 44.202, 17.908), ('Sarajevo', 43.856, 18.413)]),
    ('ljubljana-split', [('Ljubljana', 46.056, 14.506), ('Novo mesto', 45.804, 15.169), ('Zagreb', 45.815, 15.982),
                         ('Karlovac', 45.487, 15.548), ('Gospić', 44.546, 15.375), ('Zadar', 44.119, 15.231),
                         ('Šibenik', 43.735, 15.890), ('Split', 43.508, 16.440)]),
    ('budapest-split', [('Budapest', 47.498, 19.040), ('Siófok', 46.904, 18.058), ('Nagykanizsa', 46.453, 16.991),
                        ('Varaždin', 46.305, 16.338), ('Zagreb', 45.815, 15.982), ('Karlovac', 45.487, 15.548),
                        ('Gospić', 44.546, 15.375), ('Zadar', 44.119, 15.231), ('Šibenik', 43.735, 15.890),
                        ('Split', 43.508, 16.440)]),
    ('vienna-zagreb-split', [('Wien', 48.208, 16.373), ('Graz', 47.071, 15.439), ('Maribor', 46.554, 15.646),
                             ('Zagreb', 45.815, 15.982), ('Karlovac', 45.487, 15.548), ('Gospić', 44.546, 15.375),
                             ('Zadar', 44.119, 15.231), ('Šibenik', 43.735, 15.890), ('Split', 43.508, 16.440)]),
    ('zagreb-dubrovnik', [('Zagreb', 45.815, 15.982), ('Karlovac', 45.487, 15.548), ('Gospić', 44.546, 15.375),
                          ('Zadar', 44.119, 15.231), ('Split', 43.508, 16.440), ('Makarska', 43.297, 17.017),
                          ('Ploče', 43.053, 17.433), ('Dubrovnik', 42.650, 18.094)]),
    ('belgrade-skopje-ohrid', [('Beograd', 44.787, 20.457), ('Jagodina', 43.977, 21.261), ('Niš', 43.321, 21.896),
                               ('Vranje', 42.551, 21.900), ('Kumanovo', 42.132, 21.714), ('Skopje', 41.998, 21.425),
                               ('Tetovo', 42.010, 20.971), ('Gostivar', 41.796, 20.908), ('Kičevo', 41.512, 20.959),
                               ('Ohrid', 41.117, 20.802)]),
    ('belgrade-sofia-varna', [('Beograd', 44.787, 20.457), ('Jagodina', 43.977, 21.261), ('Niš', 43.321, 21.896),
                              ('Pirot', 43.153, 22.586), ('Sofia', 42.698, 23.322), ('Botevgrad', 42.907, 23.791),
                              ('Pleven', 43.417, 24.617), ('Veliko Tarnovo', 43.076, 25.617), ('Shumen', 43.271, 26.936),
                              ('Varna', 43.214, 27.914)]),
    ('belgrade-bucharest', [('Beograd', 44.787, 20.457), ('Vršac', 45.117, 21.300), ('Timișoara', 45.748, 21.208),
                            ('Lugoj', 45.689, 21.904), ('Deva', 45.877, 22.912), ('Sibiu', 45.798, 24.125),
                            ('Pitești', 44.857, 24.869), ('București', 44.427, 26.103)]),
    ('ljubljana-belgrade', [('Ljubljana', 46.056, 14.506), ('Novo mesto', 45.804, 15.169), ('Zagreb', 45.815, 15.982),
                            ('Slavonski Brod', 45.160, 18.016), ('Beograd', 44.787, 20.457)]),
]

R = 6371.0


def xy(lat, lon, lat0):
    return (math.radians(lon) * R * math.cos(math.radians(lat0)), math.radians(lat) * R)


def hav(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def load_cards(d):
    cards = {}
    cdirs = [p for p in glob.glob(os.path.join(d, 'cards-*')) if os.path.isdir(p)]
    if cdirs:
        files = glob.glob(os.path.join(cdirs[0], '*.json'))
        for f in files:
            cards.update(json.load(open(f, encoding='utf-8')).get('sites', {}))
        return cards
    tgz = glob.glob(os.path.join(d, 'cards-*.tar.gz'))[0]
    with tarfile.open(tgz) as t:
        for m in t:
            if m.isfile() and m.name.endswith('.json'):
                cards.update(json.load(t.extractfile(m)).get('sites', {}))
    return cards


def main(d, out):
    man = json.load(open(sorted(glob.glob(os.path.join(d, 'manifest-*.json')))[-1], encoding='utf-8'))
    nets, slugs = man['networks'], man['networks_slug']
    places = json.load(open(sorted(glob.glob(os.path.join(d, 'places-*.json')))[-1], encoding='utf-8'))
    cards = load_cards(d)
    lat_min, lat_max, lon_min, lon_max = 39.5, 49.5, 10.5, 30.0
    pts = []
    for line in gzip.open(os.path.join(d, 'public_sites.geojsonseq.gz'), 'rt'):
        f = json.loads(line)
        p = f['properties']
        lon, lat = f['geometry']['coordinates']
        if not (lat_min < lat < lat_max and lon_min < lon < lon_max):
            continue
        if p.get('p') not in (4, 5) or p.get('c', 0) < MIN_CONF or p.get('a', 0) != 0:
            continue
        pts.append((lat, lon, p))
    res = {'date': man['date'], 'rule': {'corridor_km': CORRIDOR_KM, 'step_km': STEP_KM, 'min_conf': MIN_CONF,
                                         'power': 'DC >= 50 kW', 'road_factor': ROAD_FACTOR}, 'routes': []}
    city_names = places.get('city') or places.get('cities') or {}
    for rid, wps in ROUTES:
        lat0 = sum(w[1] for w in wps) / len(wps)
        segs, acc = [], 0.0
        for a, b in zip(wps, wps[1:]):
            L = hav(a[1:], b[1:])
            segs.append((xy(a[1], a[2], lat0), xy(b[1], b[2], lat0), acc, L))
            acc += L
        straight = acc
        found = []
        for lat, lon, p in pts:
            P = xy(lat, lon, lat0)
            best = None
            for A, B, s0, L in segs:
                dx, dy = B[0] - A[0], B[1] - A[1]
                ll = dx * dx + dy * dy
                t = 0 if ll == 0 else max(0, min(1, ((P[0] - A[0]) * dx + (P[1] - A[1]) * dy) / ll))
                qx, qy = A[0] + t * dx, A[1] + t * dy
                dist = math.hypot(P[0] - qx, P[1] - qy)
                if best is None or dist < best[0]:
                    best = (dist, s0 + t * L)
            if best[0] <= CORRIDOR_KM:
                c = cards.get(str(p['i'])) or {}
                o = p.get('o') or 0
                found.append({'pid': p['i'], 'km': round(best[1] * ROAD_FACTOR, 1), 'off_km': round(best[0], 1),
                              'lat': round(lat, 5), 'lon': round(lon, 5), 'cls': p['p'], 'conf': p.get('c'),
                              'net': nets[o] if o < len(nets) else None, 'net_slug': slugs[o] if o < len(slugs) else None,
                              'name': c.get('n'), 'kw': c.get('kw'), 'cc': c.get('cc'), 'city': c.get('city'),
                              'pts': c.get('pts'), 'conn': c.get('conn')})
        found.sort(key=lambda r: r['km'])
        total = round(straight * ROAD_FACTOR)
        # greedy stops: from the start, the farthest station within STEP_KM of the last stop; prefer HPC on ties (±15 km)
        stops, pos, gaps = [], 0.0, []
        while pos + STEP_KM < total:
            cand = [r for r in found if pos < r['km'] <= pos + STEP_KM]
            if not cand:
                nxt = [r for r in found if r['km'] > pos]
                gap_to = nxt[0]['km'] if nxt else total
                gaps.append([round(pos), round(gap_to)])
                if not nxt:
                    break
                stops.append(nxt[0]['pid'])
                pos = nxt[0]['km']
                continue
            far = max(r['km'] for r in cand)
            near = [r for r in cand if r['km'] >= far - 15]
            pick = max(near, key=lambda r: (r['cls'], r['kw'] or 0, r['km']))
            stops.append(pick['pid'])
            pos = pick['km']
        ccs = sorted({r['cc'] for r in found if r['cc']})
        res['routes'].append({'id': rid, 'waypoints': wps, 'km_straight': round(straight), 'km': total,
                              'n_fast': len(found), 'n_hpc': sum(1 for r in found if r['cls'] == 5),
                              'stops': stops, 'gaps': gaps, 'countries_found': ccs, 'sites': found})
        print(rid, total, 'km', len(found), 'fast', len(stops), 'stops', 'gaps', gaps)
    res['cities'] = {}
    ids = {r['city'] for rt in res['routes'] for r in rt['sites'] if r['city']}
    if isinstance(city_names, dict):
        for k in ids:
            v = city_names.get(str(k))
            if v is not None:
                res['cities'][str(k)] = v
    json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
