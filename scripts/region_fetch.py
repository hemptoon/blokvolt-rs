# -*- coding: utf-8 -*-
"""Fetches the open charging data of Serbia and its neighbours (docs/RUNBOOK.md 3.23).

Runs in GitHub Actions (.github/workflows/region-data.yml) once a month and by hand, because the build
containers cannot reach Overpass or GitHub's API and the Actions runner can. The result goes to the branch
`region-data` (one commit, replaced every run) and is read by the builds through raw.githubusercontent.com:

    <CC>/osm.json   OpenStreetMap, every amenity=charging_station in the country (Overpass JSON: tags, centre
                    of ways and relations, version and timestamp; user names and ids removed). ODbL 1.0.
    <CC>/ocm.json   Open Charge Map points of the country from the public export github.com/openchargemap/ocm-export
                    (one list, as exported). Licence per data provider (referencedata.json → DataProviders);
                    provider 1 = OCM contributors, CC BY 4.0.
    referencedata.json   OCM lookup tables (operators, connection types, statuses, providers and their licences).
    meta.json       when each file was fetched, from where, element counts and the OCM export's commit date.

Usage: python3 scripts/region_fetch.py OUT_DIR [CC ...]      (default countries: see COUNTRIES)
Only the standard library; polite to the public Overpass servers (one query at a time, pauses, User-Agent)."""
import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

COUNTRIES = ['HR', 'BA', 'ME', 'MK', 'AL', 'XK', 'SI', 'RS']
OVERPASS = ['https://overpass-api.de/api/interpreter',
            'https://overpass.private.coffee/api/interpreter',
            'https://overpass.kumi.systems/api/interpreter']
UA = 'BlokVolt region data (https://blokvolt.com; hello@blokvolt.com)'
QUERY = ('[out:json][timeout:240];area["ISO3166-1"="{cc}"][admin_level=2]->.a;'
         '(nwr["amenity"="charging_station"](area.a););out center meta;')
OCM_REPO = 'https://github.com/openchargemap/ocm-export'


def now():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def overpass(cc):
    body = urllib.parse.urlencode({'data': QUERY.format(cc=cc)}).encode()
    last = None
    for attempt in range(3):
        for url in OVERPASS:
            try:
                req = urllib.request.Request(url, data=body, headers={'User-Agent': UA,
                                                                       'Content-Type': 'application/x-www-form-urlencoded'})
                with urllib.request.urlopen(req, timeout=300) as r:
                    j = json.loads(r.read().decode('utf-8'))
                if 'elements' not in j:
                    raise ValueError('no elements in the answer')
                if j.get('remark') and 'runtime error' in j['remark']:
                    raise ValueError(j['remark'])
                return url, j
            except Exception as e:  # try the next server, then wait and try again
                last = f'{url}: {e}'
                print(f'  overpass {cc}: {last}', file=sys.stderr)
                time.sleep(20)
        time.sleep(60 * (attempt + 1))
    raise SystemExit(f'Overpass failed for {cc}: {last}')


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
    out = Path(sys.argv[1])
    countries = [c.upper() for c in sys.argv[2:]] or COUNTRIES
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
            time.sleep(15)
        url, j = overpass(cc)
        osm = clean_osm(j)
        (d / 'osm.json').write_text(json.dumps(osm, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
        pois = []
        folder = data / cc
        if folder.exists():
            for p in sorted(folder.glob('*.json')):
                try:
                    pois.append(json.loads(p.read_text(encoding='utf-8')))
                except ValueError as e:
                    print(f'  ocm {cc}: {p.name}: {e}', file=sys.stderr)
        (d / 'ocm.json').write_text(json.dumps(pois, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
        meta['countries'][cc] = {'osm': {'fetched': now(), 'server': url,
                                         'timestamp_osm_base': (j.get('osm3s') or {}).get('timestamp_osm_base'),
                                         'elements': len(osm['elements'])},
                                 'ocm': {'pois': len(pois)}}
        print(f'{cc}: OSM {len(osm["elements"])} elements, OCM {len(pois)} points')
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
