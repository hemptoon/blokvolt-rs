# -*- coding: utf-8 -*-
"""Fetches the open charging data of Serbia and its neighbours (docs/RUNBOOK.md 3.23).

Runs in GitHub Actions (.github/workflows/region-data.yml) once a month and by hand, because the build
containers cannot reach Overpass or GitHub's API and the Actions runner can. The result goes to the branch
`region-data` (one commit, replaced every run) and is read by the builds through raw.githubusercontent.com:

    <CC>/osm.json   OpenStreetMap, every amenity=charging_station in the country (Overpass JSON: tags, centre
                    of ways and relations, version and timestamp; user names and ids removed). ODbL 1.0.
                    Source: the country extract of Geofabrik (updated daily), cut to the country's own boundary
                    relation with osmium; if that fails, the public Overpass servers (28.09.2026 every Overpass mirror
                    failed for Croatia: timeouts, a stale copy, an empty answer).
    <CC>/ocm.json   Open Charge Map points of the country from the public export github.com/openchargemap/ocm-export
                    (one list, as exported). Licence per data provider (referencedata.json → DataProviders);
                    provider 1 = OCM contributors, CC BY 4.0.
    referencedata.json   OCM lookup tables (operators, connection types, statuses, providers and their licences).
    meta.json       when each file was fetched, from where, element counts and the OCM export's commit date.

Usage: python3 scripts/region_fetch.py OUT_DIR [--prev PREV_DIR] [CC ...]      (default countries: see COUNTRIES)
With --prev (the previous region-data branch), a country for which both Geofabrik and Overpass fail keeps its previous
osm.json, and meta.json says so; without it such a run stops with an error.
Standard library plus the osmium command (apt package osmium-tool); polite to the public servers (one download or
query at a time, pauses, User-Agent)."""
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

COUNTRIES = ['HR', 'BA', 'ME', 'MK', 'AL', 'XK', 'SI', 'RS']
OVERPASS = ['https://overpass-api.de/api/interpreter',
            'https://overpass.kumi.systems/api/interpreter',
            'https://overpass.private.coffee/api/interpreter']
MAX_AGE_H = 72   # a mirror whose database is older than this is not used (28.09.2026 one mirror answered with July data
                 # and another with an empty result for Croatia)
UA = 'BlokVolt region data (https://blokvolt.com; hello@blokvolt.com)'
QUERY = ('[out:json][timeout:240];area["ISO3166-1"="{cc}"][admin_level=2]->.a;'
         '(nwr["amenity"="charging_station"](area.a););out center meta;')
OCM_REPO = 'https://github.com/openchargemap/ocm-export'
GEOFABRIK = 'https://download.geofabrik.de/'
EXTRACT = {'HR': 'europe/croatia', 'BA': 'europe/bosnia-herzegovina', 'ME': 'europe/montenegro', 'MK': 'europe/macedonia',
           'AL': 'europe/albania', 'XK': 'europe/kosovo', 'SI': 'europe/slovenia', 'RS': 'europe/serbia'}


def now():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def db_age_hours(j):
    ts = (j.get('osm3s') or {}).get('timestamp_osm_base')
    if not ts:
        return None
    t = datetime.strptime(ts, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - t).total_seconds() / 3600


def overpass(cc):
    body = urllib.parse.urlencode({'data': QUERY.format(cc=cc)}).encode()
    last = None
    for attempt in range(2):
        for url in OVERPASS:
            try:
                req = urllib.request.Request(url, data=body, headers={'User-Agent': UA,
                                                                       'Content-Type': 'application/x-www-form-urlencoded'})
                with urllib.request.urlopen(req, timeout=240) as r:
                    j = json.loads(r.read().decode('utf-8'))
                if 'elements' not in j:
                    raise ValueError('no elements in the answer')
                if j.get('remark') and 'runtime error' in j['remark']:
                    raise ValueError(j['remark'])
                if not j['elements']:
                    raise ValueError('empty answer (every country on the list has chargers)')
                age = db_age_hours(j)
                if age is None or age > MAX_AGE_H:
                    raise ValueError(f'stale database ({(j.get("osm3s") or {}).get("timestamp_osm_base")})')
                return url, j
            except Exception as e:  # try the next server, then wait and try again
                last = f'{url}: {e}'
                print(f'  overpass {cc}: {last}', file=sys.stderr)
                time.sleep(20)
        time.sleep(60)
    raise RuntimeError(f'Overpass failed for {cc}: {last}')


def download(url, dest):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=600) as r, open(dest, 'wb') as f:
        shutil.copyfileobj(r, f, 1 << 20)


def osmium(*args):
    subprocess.run(['osmium'] + list(args), check=True, capture_output=True, text=True)


def geofabrik(cc, work):
    """Every amenity=charging_station inside the country's boundary relation, from the Geofabrik extract, as the
    Overpass answer would give it ("out center meta": nodes with lat/lon, ways and relations with the centre of
    their bounding box)."""
    if not shutil.which('osmium'):
        raise RuntimeError('osmium is not installed')
    work.mkdir(parents=True, exist_ok=True)
    base = GEOFABRIK + EXTRACT[cc]
    state = urllib.request.urlopen(urllib.request.Request(base + '-updates/state.txt', headers={'User-Agent': UA}),
                                   timeout=60).read().decode()
    ts = next((ln.split('=', 1)[1].replace('\\', '') for ln in state.splitlines() if ln.startswith('timestamp=')), None)
    pbf = work / f'{cc}.osm.pbf'
    download(base + '-latest.osm.pbf', pbf)
    # the country's own boundary: the extract reaches a few kilometres over the border on purpose
    osmium('tags-filter', '-O', '-o', str(work / f'{cc}-l2.osm.pbf'), str(pbf), 'r/admin_level=2')
    osmium('tags-filter', '-O', '-o', str(work / f'{cc}-border.osm'), str(work / f'{cc}-l2.osm.pbf'), f'r/ISO3166-1={cc}')
    osmium('extract', '-O', '-p', str(work / f'{cc}-border.osm'), '-o', str(work / f'{cc}-in.osm.pbf'), str(pbf))
    osmium('tags-filter', '-O', '-o', str(work / f'{cc}-cs.osm'), str(work / f'{cc}-in.osm.pbf'), 'nwr/amenity=charging_station')
    root = ET.parse(work / f'{cc}-cs.osm').getroot()
    nodes = {n.get('id'): (float(n.get('lat')), float(n.get('lon'))) for n in root.iter('node') if n.get('lat')}
    ways = {w.get('id'): [nd.get('ref') for nd in w.iter('nd')] for w in root.iter('way')}
    out = []

    def centre(pts):
        pts = [p for p in pts if p]
        if not pts:
            return None
        la, lo = [p[0] for p in pts], [p[1] for p in pts]
        return {'lat': round((min(la) + max(la)) / 2, 7), 'lon': round((min(lo) + max(lo)) / 2, 7)}
    for el in root:
        tags = {t.get('k'): t.get('v') for t in el.iter('tag')}
        if tags.get('amenity') != 'charging_station':
            continue
        x = {'type': el.tag, 'id': int(el.get('id'))}
        if el.tag == 'node':
            x['lat'], x['lon'] = float(el.get('lat')), float(el.get('lon'))
        elif el.tag == 'way':
            c = centre([nodes.get(r) for r in ways.get(el.get('id'), [])])
            if not c:
                continue
            x['center'] = c
        elif el.tag == 'relation':
            pts = []
            for m in el.iter('member'):
                if m.get('type') == 'node':
                    pts.append(nodes.get(m.get('ref')))
                elif m.get('type') == 'way':
                    pts += [nodes.get(r) for r in ways.get(m.get('ref'), [])]
            c = centre(pts)
            if not c:
                continue
            x['center'] = c
        else:
            continue
        x['tags'] = tags
        if el.get('version'):
            x['version'] = int(el.get('version'))
        if el.get('timestamp'):
            x['timestamp'] = el.get('timestamp')
        out.append(x)
    for f in work.glob(f'{cc}*'):
        f.unlink()
    if not out:
        raise RuntimeError('no charging stations inside the boundary (boundary relation not found?)')
    return base + '-latest.osm.pbf', {'generator': 'Geofabrik extract + osmium (BlokVolt region_fetch.py)',
                                      'osm3s': {'timestamp_osm_base': ts}, 'elements': out}


def clean_osm(j):
    """Keep what the map needs; drop the mappers' user names and ids (not needed, personal data)."""
    out = []
    for e in j['elements']:
        x = {k: e[k] for k in ('type', 'id', 'lat', 'lon', 'center', 'tags', 'version', 'timestamp') if k in e}
        out.append(x)
    return {'generator': j.get('generator'), 'osm3s': j.get('osm3s'), 'elements': out}


def ocm_export(workdir, countries):
    repo = workdir / 'ocm-export'
    if not repo.exists():
        subprocess.check_call(['git', 'clone', '-q', '--depth', '1', '--filter=blob:none', '--sparse', OCM_REPO, str(repo)])
    subprocess.check_call(['git', '-C', str(repo), 'sparse-checkout', 'set'] + [f'data/{cc}' for cc in countries])
    commit = subprocess.check_output(['git', '-C', str(repo), 'log', '-1', '--format=%H %cI'], text=True).split()
    return repo / 'data', {'repo': OCM_REPO, 'commit': commit[0], 'date': commit[1]}


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    args = sys.argv[1:]
    prev = None
    if '--prev' in args:
        k = args.index('--prev')
        prev = Path(args[k + 1])
        del args[k:k + 2]
    out = Path(args[0])
    countries = [c.upper() for c in args[1:]] or COUNTRIES
    prev_meta = {}
    if prev and (prev / 'meta.json').exists():
        prev_meta = json.loads((prev / 'meta.json').read_text(encoding='utf-8')).get('countries', {})
    out.mkdir(parents=True, exist_ok=True)
    meta = {'about': 'Open charging data of Serbia and its neighbours for blokvolt.com / blokvolt.rs — see README.md',
            'started': now(), 'countries': {}}
    data, ocm_meta = ocm_export(out.parent / '.work', countries)
    meta['ocm_export'] = ocm_meta
    ref = data / 'referencedata.json'
    if ref.exists():
        (out / 'referencedata.json').write_bytes(ref.read_bytes())
    for i, cc in enumerate(countries):
        d = out / cc
        d.mkdir(exist_ok=True)
        if i:
            time.sleep(30)
        try:
            try:
                url, j = geofabrik(cc, out.parent / '.work' / 'osm')
                source = 'geofabrik'
            except Exception as e:  # the download, osmium or the boundary; Overpass is the second way
                print(f'  geofabrik {cc}: {e}', file=sys.stderr)
                url, j = overpass(cc)
                source = 'overpass'
        except RuntimeError as e:
            old = prev / cc / 'osm.json' if prev else None
            if not (old and old.exists()):
                raise SystemExit(str(e))
            (d / 'osm.json').write_bytes(old.read_bytes())
            osm_meta = dict((prev_meta.get(cc) or {}).get('osm') or {})
            osm_meta['kept'] = f'previous file kept: {e}'
            n_old = len(json.loads(old.read_text(encoding='utf-8')).get('elements', []))
            print(f'{cc}: Geofabrik and Overpass failed, previous osm.json kept ({n_old} elements)', file=sys.stderr)
            url, j, osm = None, None, None
        if j is not None:
            osm = clean_osm(j)
            (d / 'osm.json').write_text(json.dumps(osm, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
            osm_meta = {'fetched': now(), 'source': source, 'server': url,
                        'timestamp_osm_base': (j.get('osm3s') or {}).get('timestamp_osm_base'),
                        'elements': len(osm['elements'])}
        pois = []
        folder = data / cc
        if folder.exists():
            for p in sorted(folder.glob('*.json')):
                try:
                    pois.append(json.loads(p.read_text(encoding='utf-8')))
                except ValueError as e:
                    print(f'  ocm {cc}: {p.name}: {e}', file=sys.stderr)
        (d / 'ocm.json').write_text(json.dumps(pois, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
        meta['countries'][cc] = {'osm': osm_meta, 'ocm': {'pois': len(pois)}}
        print(f'{cc}: OSM {osm_meta.get("elements")} elements, OCM {len(pois)} points')
    meta['finished'] = now()
    (out / 'meta.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding='utf-8')
    (out / 'README.md').write_text(
        '# region-data\n\nOpen charging data for Serbia and its neighbours, fetched by `scripts/region_fetch.py` in '
        '`.github/workflows/region-data.yml` on the `main` branch (monthly and by hand). This branch is replaced on '
        'every run — do not edit it.\n\n'
        '- `<CC>/osm.json` — © OpenStreetMap contributors, Open Database License 1.0 (https://www.openstreetmap.org/copyright).\n'
        '- `<CC>/ocm.json`, `referencedata.json` — Open Charge Map (https://openchargemap.org), from the public export '
        'https://github.com/openchargemap/ocm-export; licence per data provider, CC BY 4.0 for OCM contributors.\n'
        '- `meta.json` — fetch times, servers and counts.\n', encoding='utf-8')
    return 0


if __name__ == '__main__':
    sys.exit(main())
