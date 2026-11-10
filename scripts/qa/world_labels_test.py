# -*- coding: utf-8 -*-
"""Base-map labels on the world map of blokvolt.com stay readable over dense points (FIX1, owner 10.11.2026 01:45:
"keep all the points, make city and country names stand out").

The container cannot reach OpenFreeMap, so the base map is a stand-in with the same shape as positron: a vector source
with a "place" layer (countries, cities from content/world/names/cities.csv, served as MVT tiles from the test itself) and
the positron layer ids label_other, label_state, label_town, label_city, label_country_3/2/1. Points, cards and manifest
are the real files (--data, as world_map_test.py).

Checks for EN, SR and RU at 1440 and 390 px:
  - wm-pt and wm-kw are drawn under the first symbol layer of the base map, wm-sel above everything;
  - every place label layer has the halo, colours and (countries) uppercase from FIX1;
  - the rendered city names are in the page language (Берлин on /ru/karta/, Beč on /sr/mapa/, Vienna on /map/);
  - screenshots before (--before <world-map.js>, e.g. from origin/dev) and after, three views: Europe z4.2, Benelux z6.6,
    Balkans z6.2.
Usage: python3 scripts/qa/world_labels_test.py --data <folder with latest.json> [--out qa-labels] [--before old.js]"""
import argparse, csv, json, math, os, re, subprocess, sys, tempfile, time
from collections import defaultdict
from pathlib import Path

import mapbox_vector_tile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from world_map_test import ROOT, PAGES, FAKE_API, serve, wait_ready, idle  # noqa: E402

GLYPHS = (ROOT / 'scripts' / 'qa' / 'fixtures' / 'glyphs' / 'noto-sans-bold-0-255.pbf').read_bytes()
VIEWS = {'europe': (48.5, 12, 4.2), 'benelux': (51.9, 5.2, 6.6), 'balkans': (44.3, 20.5, 6.2)}
# rendered names in the Balkans view at 1440 px; the glyph fixture covers 0-255 only, so Cyrillic (and č, ć, š) cannot be
# drawn here: RU is checked through text-field only
EXPECT = {'en': ['Belgrade', 'Sofia'], 'sr': ['Beograd', 'Sofija'], 'ru': []}
STYLE = {'version': 8, 'name': 'positron-stand-in', 'glyphs': 'https://qa-glyphs.invalid/{fontstack}/{range}.pbf',
         'sources': {'openmaptiles': {'type': 'vector', 'tiles': ['https://qa-place.invalid/{z}/{x}/{y}.pbf'], 'minzoom': 0, 'maxzoom': 8}},
         'layers': [{'id': 'background', 'type': 'background', 'paint': {'background-color': '#F2F3F0'}}]}
for lid, flt, mz, size, col in (
        ('label_other', ['==', ['get', 'class'], 'other'], 6, 10, '#8C8C8C'),
        ('label_state', ['==', ['get', 'class'], 'state'], 4, 10, '#8C8C8C'),
        ('label_town', ['==', ['get', 'class'], 'town'], 6, 11, '#6E6E6E'),
        ('label_city', ['==', ['get', 'class'], 'city'], 3, 13, '#5A5A5A'),
        ('label_country_3', ['all', ['==', ['get', 'class'], 'country'], ['>=', ['get', 'rank'], 3]], 2, 11, '#7A7A7A'),
        ('label_country_2', ['all', ['==', ['get', 'class'], 'country'], ['==', ['get', 'rank'], 2]], 2, 12, '#7A7A7A'),
        ('label_country_1', ['all', ['==', ['get', 'class'], 'country'], ['==', ['get', 'rank'], 1]], 1, 13, '#7A7A7A')):
    STYLE['layers'].append({'id': lid, 'type': 'symbol', 'source': 'openmaptiles', 'source-layer': 'place', 'minzoom': mz, 'filter': flt,
                            'layout': {'text-field': ['get', 'name'], 'text-font': ['Noto Sans Bold'], 'text-size': size},
                            'paint': {'text-color': col, 'text-halo-color': 'rgba(255,255,255,0.6)', 'text-halo-width': 1}})


def places():
    """Countries (centre of their cities) and cities, with the name fields of OpenMapTiles."""
    feats, by_cc = [], defaultdict(list)
    P = json.load(open(ARGS.data / json.load(open(ARGS.data / 'latest.json'))['manifest'].replace('manifest', 'places'), encoding='utf-8'))
    with open(ROOT / 'content/world/names/cities.csv', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            b = P['city'].get(r['geonameid'])
            if not b or len(b) < 6:
                continue
            lat, lon = b[4], b[5]
            by_cc[r['cc']].append((lat, lon))
            feats.append({'lat': lat, 'lon': lon, 'minz': 4 if r['stage'] == 'month' else 6,
                          'p': {'class': 'city' if r['stage'] == 'month' else 'town', 'name': r['name_local'], 'name:en': r['name_en'],
                                'name_en': r['name_en'], 'name:latin': r['name_en'], 'name:sr-Latn': r['name_sr'], 'name:ru': r['name_ru']}})
    with open(ROOT / 'content/world/names/countries.csv', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            pts = by_cc.get(r['cc'])
            if not pts:
                continue
            lat = sorted(p[0] for p in pts)[len(pts) // 2]
            lon = sorted(p[1] for p in pts)[len(pts) // 2]
            feats.append({'lat': lat, 'lon': lon, 'minz': 0, 'p': {'class': 'country', 'rank': 1 if len(pts) > 60 else 2 if len(pts) > 15 else 3,
                          'name': r['name_en'], 'name:en': r['name_en'], 'name_en': r['name_en'], 'name:latin': r['name_en'],
                          'name:sr-Latn': r['name_sr'], 'name:ru': r['name_ru']}})
    return feats


def tile(feats, z, x, y):
    n = 2 ** z
    out = []
    for f in feats:
        if z < f['minz']:
            continue
        tx = (f['lon'] + 180) / 360 * n
        s = math.sin(math.radians(f['lat']))
        ty = (0.5 - math.log((1 + s) / (1 - s)) / (4 * math.pi)) * n
        if x - 0.05 <= tx < x + 1.05 and y - 0.05 <= ty < y + 1.05:
            # mapbox_vector_tile flips y by default (origin bottom-left)
            out.append({'geometry': f'POINT({round((tx - x) * 4096)} {round((1 - (ty - y)) * 4096)})', 'properties': f['p']})
    return mapbox_vector_tile.encode([{'name': 'place', 'features': out}]) if out else b''


def main():
    from playwright.sync_api import sync_playwright
    out = ARGS.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    feats = places()
    tmp = Path(tempfile.mkdtemp(prefix='wm-lab-'))
    site = tmp / 'site'
    srv, port = serve(site)
    base = f'http://127.0.0.1:{port}'
    env = dict(os.environ, BV_COM_OUT=str(site), BV_WORLD_DATA=base + '/world/', BV_WORLD_REPORTS=FAKE_API)
    r = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'gen_com.py')], cwd=ROOT, env=env, capture_output=True, text=True)
    if r.returncode:
        print(r.stdout[-2000:], r.stderr[-2000:])
        raise SystemExit('gen_com.py failed')
    os.symlink(ARGS.data.resolve(), site / 'world')
    old = Path(ARGS.before).read_text(encoding='utf-8') if ARGS.before else None
    fails, rep = [], []
    with sync_playwright() as pw:
        br = pw.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        for lang in ('en', 'sr', 'ru'):
            for w, h in ((1440, 900), (390, 844)):
                for ver in (['before'] if old else []) + ['after']:
                    ctx = br.new_context(viewport={'width': w, 'height': h}, device_scale_factor=1, is_mobile=w < 700, has_touch=w < 700)
                    ctx.route(re.compile(r'https://tiles\.openfreemap\.org/.*'), lambda rt: rt.fulfill(status=200, content_type='application/json', body=json.dumps(STYLE)))
                    ctx.route(re.compile(r'https://qa-glyphs\.invalid/.*'), lambda rt: rt.fulfill(status=200, content_type='application/x-protobuf',
                                                                                             body=GLYPHS if '/0-255.pbf' in rt.request.url else b''))

                    def place(rt):
                        z, x, y = map(int, re.search(r'/(\d+)/(\d+)/(\d+)\.pbf', rt.request.url).groups())
                        rt.fulfill(status=200, content_type='application/x-protobuf', body=tile(feats, z, x, y))
                    ctx.route(re.compile(r'https://qa-place\.invalid/.*'), place)
                    if ver == 'before':
                        ctx.route(re.compile(r'.*/assets/world/world-map[^/]*\.js(\?.*)?$'), lambda rt: rt.fulfill(status=200, content_type='text/javascript', body=old))
                    errs = []
                    pg = ctx.new_page()
                    pg.on('pageerror', lambda e: errs.append(str(e)))
                    for name, (lat, lon, z) in VIEWS.items():
                        zz = round(z - (1.3 if w < 700 else 0), 2)
                        pg.goto(f'{base}{PAGES[lang]}#{zz}/{lat}/{lon}', wait_until='load')
                        if not wait_ready(pg):
                            fails.append(f'{lang} {w} {ver} {name}: map not ready')
                            continue
                        idle(pg)
                        pg.wait_for_timeout(800)
                        pg.screenshot(path=str(out / f'{name}_{lang}_{w}_{ver}.png'))
                        if ver == 'after' and name == 'balkans' and w == 1440:
                            props = pg.evaluate("() => BVWorldMap.map.queryRenderedFeatures().filter(x => x.sourceLayer === 'place').map(x => x.properties)")
                            key = {'en': 'name:en', 'sr': 'name:sr-Latn', 'ru': 'name:ru'}[lang]
                            shown = {x.get(key) or x.get('name:latin') or x.get('name') for x in props}
                            miss = [n for n in EXPECT[lang] if n not in shown]
                            if miss:
                                fails.append(f'{lang} {w}: city names not in the page language: {miss}')
                    if ver == 'after':
                        info = pg.evaluate("""() => {
                          const m = BVWorldMap.map; if (!m) return null;
                          const ls = m.getStyle().layers, ids = ls.map(l => l.id);
                          const firstSym = ls.findIndex(l => l.type === 'symbol' && !l.id.startsWith('wm-'));
                          const lab = ls.filter(l => l['source-layer'] === 'place').map(l => ({ id: l.id,
                            halo: m.getPaintProperty(l.id, 'text-halo-color'), hw: m.getPaintProperty(l.id, 'text-halo-width'),
                            blur: m.getPaintProperty(l.id, 'text-halo-blur'), col: m.getPaintProperty(l.id, 'text-color'),
                            tt: m.getLayoutProperty(l.id, 'text-transform'), ls: m.getLayoutProperty(l.id, 'text-letter-spacing'),
                            tf: JSON.stringify(m.getLayoutProperty(l.id, 'text-field')) }));
                          return { pt: ids.indexOf('wm-pt'), kw: ids.indexOf('wm-kw'), sel: ids.indexOf('wm-sel'), n: ids.length, firstSym, lab };
                        }""")
                        f = []
                        if not info:
                            f.append('no map handle')
                        else:
                            if not (0 <= info['pt'] < info['firstSym'] and 0 <= info['kw'] < info['firstSym']):
                                f.append(f"points not under the labels: {info['pt']},{info['kw']} vs first label {info['firstSym']}")
                            if info['sel'] != info['n'] - 1:
                                f.append('wm-sel is not on top')
                            for l in info['lab']:
                                ctry = l['id'].startswith('label_country')
                                soft = l['id'] in ('label_state', 'label_other')
                                if l['halo'] != 'rgba(255,255,255,0.95)' or l['hw'] != (2.4 if ctry else 2) or l['blur'] != 0.3:
                                    f.append(f"{l['id']}: halo {l['halo']} {l['hw']} {l['blur']}")
                                if l['col'] != ('#3A404C' if soft else '#0D111A'):
                                    f.append(f"{l['id']}: colour {l['col']}")
                                if ctry and (l['tt'] != 'uppercase' or l['ls'] != 0.08):
                                    f.append(f"{l['id']}: not uppercase")
                                key = {'en': 'name:en', 'sr': 'name:sr-Latn', 'ru': 'name:ru'}[lang]
                                if key not in l['tf']:
                                    f.append(f"{l['id']}: text-field without {key}")
                        txt = pg.evaluate("() => BVWorldMap.map.queryRenderedFeatures().filter(x => x.sourceLayer === 'place').length")
                        rep.append({'lang': lang, 'w': w, 'fails': f + errs[:3], 'labels_in_view': txt})
                        fails += [f'{lang} {w}: {x}' for x in f + errs[:3]]
                    ctx.close()
        br.close()
    srv.shutdown()
    (out / 'report.json').write_text(json.dumps({'runs': rep, 'fails': fails}, ensure_ascii=False, indent=1), encoding='utf-8')
    for x in rep:
        print(x['lang'], x['w'], 'OK' if not x['fails'] else 'FAIL ' + '; '.join(x['fails']), '· labels in view', x['labels_in_view'])
    print('Result:', 'OK' if not fails else f'{len(fails)} failure(s)')
    return 1 if fails else 0


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', required=True, type=Path)
    ap.add_argument('--out', default=Path('qa-labels'), type=Path)
    ap.add_argument('--before', default='')
    ARGS = ap.parse_args()
    sys.exit(main())
