# Price labels on the two charger maps never cover a pin or another label (docs/RUNBOOK.md 3.11, owner's request
# 28.10.2026): blokvolt.rs /mapa/ (static/assets/map.js, the English page) and the evolako.rs map (scripts/evomap, the
# build named in scripts/evomap/build.json, on a mock page). In the dense parts of Novi Sad, Belgrade and Niš, on a phone
# (390 px) and a computer (1440 px), with RSD, EUR and „Moj auto“:
#   - at every zoom from 12 (labels start there) to 18: no label touches a pin (its own or another one's) or another
#     label, and every pin in view is drawn (a label may wait for a closer zoom, a pin never does);
#   - from zoom 16 (street level): every charger in view has its label, and no two pins overlap;
#   - two chargers at one place (test copies of a station, one at the same point, one 5 m away) are drawn apart from
#     zoom 16, each with its label and a line to the real place, and a tap on each opens its own card; on the city view
#     (zoom 12) they are still one dot.
# How it measures: pins geometrically (projected centre + circle-radius + circle-stroke-width at the zoom); labels from
# pixels — every placed label is drawn once in its own colour, everything else transparent, and its box is read from the
# map's own canvas (the evolako.rs capsules from a second frame with the capsules only; the page's buttons and legend are
# not in the canvas). The map font (Noto Sans Bold, the style's font) comes from fixtures/glyphs: the container cannot
# reach OpenFreeMap, and without glyphs there are no labels.
# Usage (server running, see cfserve.py; python3 scripts/evomap/build.py and build.py done):
#   python3 scripts/qa/map_labels_test.py [shots-dir] [base-url] [bv,evo] [rsd,eur,car,copies]
import asyncio, base64, io, json, math, subprocess, sys, tarfile
from pathlib import Path
from urllib.parse import unquote
import numpy as np
from PIL import Image
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[2]
DIST = ROOT / 'dist'
SHOTS = Path(sys.argv[1] if len(sys.argv) > 1 else '/tmp/bv-shots/labels')
SHOTS.mkdir(parents=True, exist_ok=True)
BASE = sys.argv[2] if len(sys.argv) > 2 else 'http://localhost:8787'
MAPS = (sys.argv[3] if len(sys.argv) > 3 else 'bv,evo').split(',')                 # a part only: … bv  or  … evo copies
PARTS = (sys.argv[4] if len(sys.argv) > 4 else 'rsd,eur,car,copies').split(',')
GLYPHS = (ROOT / 'scripts' / 'qa' / 'fixtures' / 'glyphs' / 'noto-sans-bold-0-255.pbf').read_bytes()
BUILD = json.loads((ROOT / 'scripts' / 'evomap' / 'build.json').read_text())
ML = Path('/tmp/evomap/ml/package/dist')
if not (ML / 'maplibre-gl.js').exists():
    (ML.parent.parent).mkdir(parents=True, exist_ok=True)
    subprocess.check_call(['npm', 'pack', 'maplibre-gl@5.24.0', '--silent'], cwd=ML.parent.parent, stdout=subprocess.DEVNULL)
    with tarfile.open(ML.parent.parent / 'maplibre-gl-5.24.0.tgz') as t:
        t.extractall(ML.parent.parent, members=[m for m in t.getmembers() if m.name in ('package/dist/maplibre-gl.js', 'package/dist/maplibre-gl.css')])
# no paint transitions: the colour passes below change paint properties and must see the new colours at once
STYLE = {"version": 8, "glyphs": "https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf", "sources": {}, "transition": {"duration": 0, "delay": 0},
         "layers": [{"id": "bg", "type": "background", "paint": {"background-color": "#FFFFFF"}}]}
CAR = 'hyundai-kona-electric-64-kwh-11-kw-obc-my2020-2023'
# [lon, lat]: the founder's screenshot (Partizanska / Kisačka, Novi Sad) and its DC 75 pin (Partizanska, with Super Vero
# 140 m away), Novi Beograd by Ušće, central Belgrade, Niš, central Novi Sad
VIEWS = {'ns': (19.8290, 45.2680), 'ns-75': (19.82437, 45.26843), 'bg-usce': (20.4300, 44.8100), 'bg': (20.4600, 44.8140), 'nis': (21.8960, 43.3200),
         'ns-centar': (19.8450, 45.2545)}
PLAN = {'rsd': [('ns', (12, 13, 14, 15, 16, 17, 18)), ('ns-75', (14, 15, 16, 17, 18)), ('bg-usce', (12, 13, 14, 15, 16, 17, 18)), ('bg', (13, 14, 16)),
                ('nis', (13, 14, 16)), ('ns-centar', (14, 16))],
        'eur': [('ns', (13, 16)), ('bg-usce', (14, 17))],
        'car': [('ns', (13, 16)), ('bg-usce', (14, 17))]}
DUP = 'ocm-213274'   # Partizanska, Novi Sad (OMV, Orion eMobility DC 75 kW, a price label): two test copies at its place
fails = []


def check(ok, what):
    print(('OK   ' if ok else 'FAIL ') + what)
    if not ok:
        fails.append(what)


def with_copies(body, name):
    """punjaci.json with two copies of DUP (one at the same point, one 5 m to the east); mreze.json with the network's
    data of DUP for both (its name too: a price can depend on the place's name), so the copies get the same price label"""
    j = json.loads(body)
    if name.startswith('mreze'):
        for i in (1, 2):
            if DUP in j.get('upd', {}):
                j['upd'][f'qa-isto-mesto-{i}'] = j['upd'][DUP]
        return json.dumps(j).encode()
    s = next(x for x in j['stations'] if x['id'] == DUP)
    for i, dx in ((1, 0.0), (2, 5 / (111320 * math.cos(math.radians(s['lat']))))):
        c = json.loads(json.dumps(s))
        c['id'], c['n'], c['lon'] = f'qa-isto-mesto-{i}', f'QA isto mesto {i}', s['lon'] + dx
        j['stations'].append(c)
    return json.dumps(j).encode()


async def glyph(route):
    u = unquote(route.request.url)
    body = GLYPHS if '/Noto Sans Bold' in u and u.endswith('/0-255.pbf') else b''
    await route.fulfill(status=200, content_type='application/x-protobuf', headers={'Access-Control-Allow-Origin': '*'}, body=body)


async def open_bv(ctx, var, copies=False):
    pg = await ctx.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append('JS ' + str(e)[:200]))

    async def style(route):
        await route.fulfill(status=200, content_type='application/json', body=json.dumps(STYLE))

    async def api(route):
        await route.fulfill(status=200, content_type='application/json', body='{"ok":true,"at":0,"st":{}}')

    async def stations(route):
        r = await route.fetch()
        await route.fulfill(response=r, body=with_copies(await r.body(), route.request.url.split('/assets/map/', 1)[1]))
    await pg.route('**/styles/**', style)
    await pg.route('**/fonts/**', glyph)
    await pg.route('**/api/**', api)
    if copies:
        await pg.route('**/assets/map/punjaci.json*', stations)
        await pg.route('**/assets/map/mreze.json*', stations)
    if var == 'car':
        await pg.add_init_script("try { localStorage.setItem('bv:car', JSON.stringify({id: '%s'})); } catch (e) {}" % CAR)
    await pg.goto(BASE + '/en/mapa/?qa=1&cur=' + ('eur' if var == 'eur' else 'rsd'), wait_until='networkidle')
    for _ in range(300):
        if await pg.evaluate('!!(window.bvMapObjQa && window.bvMapObjQa() && window.bvMapObjQa().loaded() && window.bvMapObjQa().getLayer("pt"))'):
            break
        await pg.wait_for_timeout(100)
    return pg, errs


def evo_page():
    tag = f'<script src="https://www.blokvolt.rs{BUILD["file"]}" integrity="{BUILD["sri"]}" crossorigin="anonymous"></script>'
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><script>'
            + (ROOT / 'scripts' / 'evomap' / 'page_bvq.js').read_text() + '</script></head><body><div class="v3-ph"><h1>Map</h1></div>'
            + '<div class="evm-sec"><div class="evm-wrap"><div id="evm" class="evm"></div></div></div>' + tag + '</body></html>')


async def open_evo(ctx, var, copies=False):
    pg = await ctx.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append('JS ' + str(e)[:200]))
    cors = {'Access-Control-Allow-Origin': '*'}

    async def route(r):
        u = r.request.url
        if u.startswith('https://www.evolako.rs/'):
            return await r.fulfill(status=200, content_type='text/html; charset=utf-8', body=evo_page())
        if u.startswith('https://www.blokvolt.rs/'):
            p = DIST / u.split('https://www.blokvolt.rs/', 1)[1].split('?')[0].split('#')[0]
            if p.is_file():
                ct = {'.json': 'application/json', '.js': 'application/javascript'}.get(p.suffix, 'application/octet-stream')
                body = p.read_bytes()
                if copies and p.name in ('punjaci.json', 'mreze.json'):
                    body = with_copies(body, p.name)
                return await r.fulfill(status=200, content_type=ct, headers=cors, body=body)
            return await r.fulfill(status=404, headers=cors, body='nf')
        if 'maplibre-gl@5.24.0/dist/maplibre-gl.' in u:
            f = ML / ('maplibre-gl.css' if u.endswith('.css') else 'maplibre-gl.js')
            return await r.fulfill(status=200, content_type='text/css' if u.endswith('.css') else 'application/javascript', headers=cors, body=f.read_bytes())
        if u.startswith('https://tiles.openfreemap.org/styles/'):
            return await r.fulfill(status=200, content_type='application/json', headers=cors, body=json.dumps(STYLE))
        if u.startswith('https://tiles.openfreemap.org/fonts/'):
            return await glyph(r)
        return await r.fulfill(status=204, body='')
    await pg.route('**/*', route)
    await pg.goto('https://www.evolako.rs/en/mapa-punjaca?qa=1', wait_until='load')
    for _ in range(300):
        if await pg.evaluate("!!(window.evmMap && window.evmMap.loaded() && window.evmMap.getLayer('pt') && document.querySelectorAll('.evm-st').length > 5)"):
            break
        await pg.wait_for_timeout(100)
    if var == 'car':
        # „Moj auto“ on evolako.rs is kept for the visit only: pick it in the panel
        await pg.click('.evm-car:not(.evm-rt)')
        await pg.wait_for_selector('.evm-carp select[data-car="mk"]', timeout=15000)
        await pg.select_option('.evm-carp select[data-car="mk"]', 'Hyundai')
        v = await pg.evaluate("[...document.querySelectorAll('.evm-carp select[data-car=md] option')].map(o => o.value).filter(x => /kona/i.test(x))[0]")
        await pg.select_option('.evm-carp select[data-car="md"]', v)
        await pg.click('.evm-carp [data-car="save"]')
        await pg.wait_for_timeout(400)
        await pg.evaluate("(() => { const x = document.querySelector('.evm-card .evm-x'); if (x) x.click(); })()")
    return pg, errs


def M(evo):
    return 'window.evmMap' if evo else 'window.bvMapObjQa()'


async def settle(pg, evo):
    for _ in range(300):
        try:
            if await pg.evaluate(f'(() => {{ const m = {M(evo)}; return m.loaded() && !m.isMoving() && m.areTilesLoaded(); }})()'):
                break
        except Exception:
            pass
        await pg.wait_for_timeout(100)
    await pg.wait_for_timeout(500)
    # the labels' places are settled: the same placed labels three times in a row, 250 ms apart (a fade takes 300 ms)
    prev, same = None, 0
    for _ in range(40):
        cur = await pg.evaluate(f'(() => {{ const m = {M(evo)}; m.triggerRepaint(); return JSON.stringify(m.queryRenderedFeatures({{layers: ["pt-pr"]}}).map(f => f.properties.id).sort()); }})()')
        same = same + 1 if cur == prev else 0
        prev = cur
        if same >= 2:
            break
        await pg.wait_for_timeout(250)


# the pins in view (drawn: queryRenderedFeatures; in the data: querySourceFeatures), their radius, and the placed labels
JS_INFO = r'''(evo) => {
  const m = evo ? window.evmMap : window.bvMapObjQa(), z = m.getZoom(), cv = m.getCanvas(), W = cv.clientWidth, H = cv.clientHeight;
  const ev = e => { if (typeof e === 'number') return e; if (Array.isArray(e) && e[0] === 'interpolate') { const st = e.slice(3);
      if (z <= st[0]) return ev(st[1]); for (let i = 0; i + 2 < st.length; i += 2) if (z <= st[i + 2]) return ev(st[i + 1]) + (ev(st[i + 3]) - ev(st[i + 1])) * (z - st[i]) / (st[i + 2] - st[i]);
      return ev(st[st.length - 1]); } return NaN; };
  const inV = p => p.x >= 0 && p.y >= 0 && p.x <= W && p.y <= H;
  const pins = [], seen = new Set(), data = new Set();
  [['pt', 'st'], ['rg-pt', 'rg']].forEach(([l, src]) => {
    if (!m.getLayer(l)) return;
    const r = ev(m.getPaintProperty(l, 'circle-radius')) + ev(m.getPaintProperty(l, 'circle-stroke-width'));
    m.querySourceFeatures(src).forEach(f => { if (inV(m.project(f.geometry.coordinates))) data.add(f.properties.id); });
    m.queryRenderedFeatures({ layers: [l] }).forEach(f => {
      const id = f.properties.id; if (seen.has(id)) return; seen.add(id);
      const p = m.project(f.geometry.coordinates);
      pins.push({ id, x: p.x, y: p.y, r, pl: f.properties.pl || '', rg: src === 'rg' });
    });
  });
  const drawn = pins.filter(p => inV(p)).length;
  return { z, W, H, pins, data: data.size, drawn, lbl: [...new Set(m.queryRenderedFeatures({ layers: ['pt-pr'] }).map(f => f.properties.id))] };
}'''
# pass 'A': every placed label in its own colour (no halo), everything else transparent; 'B': the capsules only; 'restore'
JS_PAINT = r'''([evo, mode, ids, cols]) => {
  const m = evo ? window.evmMap : window.bvMapObjQa(), L = m.getStyle().layers.filter(l => l.id !== 'bg');
  if (!window.__qaP) { window.__qaP = {}; L.forEach(l => { const P = {};
      ['circle-opacity', 'circle-stroke-opacity', 'text-opacity', 'icon-opacity', 'line-opacity', 'fill-opacity', 'text-color', 'text-halo-width'].forEach(k => {
        try { P[k] = m.getPaintProperty(l.id, k); } catch (e) { /* not this type */ } });
      window.__qaP[l.id] = P; }); }
  const S = (id, k, v) => { try { m.setPaintProperty(id, k, v); } catch (e) { /* not this type */ } };
  if (mode === 'restore') { Object.keys(window.__qaP).forEach(id => Object.keys(window.__qaP[id]).forEach(k => S(id, k, window.__qaP[id][k] === undefined ? null : window.__qaP[id][k]))); return true; }
  L.forEach(l => { ['circle-opacity', 'circle-stroke-opacity', 'text-opacity', 'icon-opacity', 'line-opacity', 'fill-opacity'].forEach(k => S(l.id, k, 0)); });
  if (mode === 'A') { const ex = ['match', ['get', 'id']]; ids.forEach((id, i) => ex.push(id, cols[i])); ex.push('rgba(0,0,0,0)');
    if (ids.length) S('pt-pr', 'text-color', ex); S('pt-pr', 'text-halo-width', 0); S('pt-pr', 'text-opacity', 1); }
  if (mode === 'B') S('pt-pr', 'icon-opacity', 1);
  m.triggerRepaint(); return true;
}'''


def code(i):
    return (8 + (i % 20) * 12, 8 + (i // 20) * 12)


async def canvas(pg, evo):
    # the map's own pixels, read in the render event (the drawing buffer is whole then); the page's buttons and legend
    # above the map are not in it
    url = await pg.evaluate(f'new Promise(res => {{ const m = {M(evo)}; m.once("render", () => res(m.getCanvas().toDataURL("image/png"))); m.triggerRepaint(); }})')
    img = Image.open(io.BytesIO(base64.b64decode(url.split(',', 1)[1]))).convert('RGBA')
    bg = Image.new('RGBA', img.size, (255, 255, 255, 255))
    return np.asarray(Image.alpha_composite(bg, img).convert('RGB')).astype(float)


def ink_boxes(img, n):
    # each label's colour is (code(i), blue 0) on white: un-blend the anti-aliased edge (blue = 255 (1 - alpha)), keep alpha >= 0.55
    R, G, B = img[..., 0], img[..., 1], img[..., 2]
    a = np.maximum(1 - B / 255.0, 0.55)
    cr, cg = (R - 255 * (1 - a)) / a, (G - 255 * (1 - a)) / a
    ri, gi = np.rint((cr - 8) / 12).astype(int), np.rint((cg - 8) / 12).astype(int)
    tol = 2.5 / a + 1
    ok = (1 - B / 255.0 >= 0.55) & (np.abs(cr - 8 - ri * 12) <= tol) & (np.abs(cg - 8 - gi * 12) <= tol) & (ri >= 0) & (ri < 20) & (gi >= 0)
    idx = np.where(ok, gi * 20 + ri, -1)
    out = []
    for i in range(n):
        ys, xs = np.nonzero(idx == i)
        out.append((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1) if len(xs) >= 3 else None)
    return out


def capsules(img):
    from scipy import ndimage
    d = np.minimum(np.abs(img - [0x0B, 0x12, 0x20]).sum(-1), np.abs(img - [0x23, 0x58, 0xE0]).sum(-1))
    lab, _ = ndimage.label(d < 90)
    return [(s[1].start, s[0].start, s[1].stop, s[0].stop) for s in ndimage.find_objects(lab) if s and s[1].stop - s[1].start >= 6 and s[0].stop - s[0].start >= 6]


def hits_circle(b, x, y, r):
    return math.hypot(max(b[0] - x, 0, x - b[2]), max(b[1] - y, 0, y - b[3])) < r - 0.5


def hits_box(a, b):
    return a[0] < b[2] - 0.5 and b[0] < a[2] - 0.5 and a[1] < b[3] - 0.5 and b[1] < a[3] - 0.5


async def measure(pg, evo):
    """overlaps in the current view: label-pin, label-label, pin-pin; labels missing in the middle of the view"""
    info = await pg.evaluate(JS_INFO, evo)
    W, H, pins, placed = info['W'], info['H'], info['pins'], set(info['lbl'])
    inview = [p for p in pins if 0 <= p['x'] <= W and 0 <= p['y'] <= H]
    core = [p for p in inview if 90 <= p['x'] <= W - 90 and 24 <= p['y'] <= H - 24]
    ids = [p['id'] for p in pins if p['id'] in placed]
    await pg.evaluate(JS_PAINT, [evo, 'A', ids, ['rgb(%d,%d,0)' % code(i) for i in range(len(ids))]])
    await pg.wait_for_timeout(250)
    ink = ink_boxes(await canvas(pg, evo), len(ids))
    caps = []
    if evo:
        await pg.evaluate(JS_PAINT, [evo, 'B', [], []])
        await pg.wait_for_timeout(250)
        caps = capsules(await canvas(pg, evo))
    await pg.evaluate(JS_PAINT, [evo, 'restore', [], []])
    await pg.wait_for_timeout(200)
    inside = lambda c, b: c[0] - 1 <= b[0] and c[1] - 1 <= b[1] and c[2] + 1 >= b[2] and c[3] + 1 >= b[3]
    box, shared = {}, 0
    for pid, b in zip(ids, ink):
        if b is None:
            continue
        if evo:
            cs = [c for c in caps if inside(c, b)]
            box[pid] = min(cs, key=lambda c: (c[2] - c[0]) * (c[3] - c[1])) if cs else (b[0] - 7, b[1] - 3, b[2] + 7, b[3] + 2)
        else:
            box[pid] = (b[0] - 2, b[1] - 2, b[2] + 2, b[3] + 2)   # the white halo around the text
    for c in caps:   # one capsule shape around two texts = two capsules touching or overlapping
        shared += max(0, sum(1 for b in ink if b and inside(c, b)) - 1)
    lp = [(a, p['id']) for a, b in box.items() for p in pins if hits_circle(b, p['x'], p['y'], p['r'])]
    k = list(box)
    ll = [(k[i], k[j]) for i in range(len(k)) for j in range(i + 1, len(k)) if hits_box(box[k[i]], box[k[j]])]
    pp = [(a['id'], b['id']) for i, a in enumerate(inview) for b in inview[i + 1:] if math.hypot(a['x'] - b['x'], a['y'] - b['y']) < a['r'] + b['r'] - 0.5]
    return {'z': info['z'], 'pins': len(inview), 'data': info['data'], 'drawn': info['drawn'],
            'want': sum(1 for p in inview if p['pl'] and not p['rg']), 'placed': sum(1 for p in inview if p['pl'] and not p['rg'] and p['id'] in placed),
            'missing': [p['id'] for p in core if p['pl'] and not p['rg'] and p['id'] not in placed],
            'lp': lp, 'll': ll + [('capsule', 'shared')] * shared, 'pp': pp,
            'noink': [pid for pid, b in zip(ids, ink) if b is None and pid in {p['id'] for p in core}]}


async def views(pg, evo, tag, var, mob):
    for vn, zs in PLAN[var]:
        lon, lat = VIEWS[vn]
        for z in zs:
            await pg.evaluate(f'{M(evo)}.jumpTo({{center: [{lon}, {lat}], zoom: {z}}})')
            await settle(pg, evo)
            r = await measure(pg, evo)
            what = f'{tag} {var} {vn} z{z}: {r["pins"]} pins, labels {r["placed"]}/{r["want"]}'
            check(not r['lp'] and not r['ll'], f'{what} — no label on a pin or a label' + (f' (label-pin {r["lp"][:3]}, label-label {r["ll"][:3]})' if r['lp'] or r['ll'] else ''))
            check(r['drawn'] >= r['data'], f'{what} — every pin drawn ({r["drawn"]} of {r["data"]})')
            check(not r['noink'], f'{what} — every placed label found on screen' + (f' {r["noink"][:3]}' if r['noink'] else ''))
            if z >= 16:
                check(not r['missing'] and not r['pp'], f'{what} — street zoom: every charger with its label, pins apart' + (f' (missing {r["missing"]}, pins {r["pp"][:3]})' if r['missing'] or r['pp'] else ''))
            if var == 'rsd' and z in (14, 16):
                el = await pg.query_selector('.evm-map' if evo else '#map')
                await el.screenshot(path=str(SHOTS / f'labels-{tag}-{vn}-z{z}.png'))


async def copies(pg, evo, tag, mob):
    """two copies of DUP at its place: apart from zoom 16 with labels and lines, one dot at zoom 12, each tap its own card"""
    ids = [DUP, 'qa-isto-mesto-1', 'qa-isto-mesto-2']
    js_ids = json.dumps(ids)
    pos = await pg.evaluate(f'''(() => {{ const m = {M(evo)}; return m.querySourceFeatures('st').filter(f => {js_ids}.includes(f.properties.id))
        .reduce((o, f) => (o[f.properties.id] = f.geometry.coordinates, o), {{}}); }})()''')
    check(len(pos) == 3, f'{tag} copies: the three points are in the data ({sorted(pos)})')
    if len(pos) < 3:
        return
    lon, lat = pos[DUP]
    pins = f'''(() => {{ const m = {M(evo)}, o = {{}}; m.queryRenderedFeatures({{layers: ['pt']}}).forEach(f => {{
        if ({js_ids}.includes(f.properties.id)) {{ const p = m.project(f.geometry.coordinates); o[f.properties.id] = [p.x, p.y]; }} }}); return o; }})()'''
    for z in (12, 16, 17, 18):
        # the group in the middle of the view (the country view's tiles round the coordinates, so centre on the drawn pins)
        await pg.evaluate(f'{M(evo)}.jumpTo({{center: [{lon}, {lat}], zoom: {z}}})')
        await settle(pg, evo)
        xy = await pg.evaluate(pins)
        if len(xy) == 3:
            cx, cy = sum(v[0] for v in xy.values()) / 3, sum(v[1] for v in xy.values()) / 3
            await pg.evaluate(f'(() => {{ const m = {M(evo)}; m.jumpTo({{center: m.unproject([{cx}, {cy}]), zoom: {z}}}); }})()')
            await settle(pg, evo)
            xy = await pg.evaluate(pins)
        if z == 12:
            far = max(math.hypot(a[0] - b[0], a[1] - b[1]) for a in xy.values() for b in xy.values()) if len(xy) == 3 else 99
            check(len(xy) == 3 and far < 5, f'{tag} copies z12: one dot on the city view (drawn {len(xy)}, {far:.2f} px apart; a pin is 23 px across)')
            continue
        r = await measure(pg, evo)
        legs = await pg.evaluate(f"{M(evo)}.queryRenderedFeatures({{layers: ['pt-leg']}}).length")
        mine = [p for p in r['pp'] if set(p) & set(ids)]
        placed = await pg.evaluate(f"{M(evo)}.queryRenderedFeatures({{layers: ['pt-pr']}}).map(f => f.properties.id)")
        W = await pg.evaluate(f'{M(evo)}.getCanvas().clientWidth')
        # every label of the three; at zoom 18 on a phone the group is wider than the map, so there only the pins with room
        # for a label on both sides (90 px, as in the views above) must have one
        need = [i for i in ids if z < 18 or 90 <= xy.get(i, [0])[0] <= W - 90]
        lab = [i for i in ids if i in placed]
        check(len(xy) == 3 and not mine and all(i in lab for i in need) and not r['lp'] and not r['ll'] and legs >= 2,
              f'{tag} copies z{z}: three pins apart, labels {lab} (needed {need}), {legs} lines to the place (pins {mine}, label-pin {r["lp"][:2]}, label-label {r["ll"][:2]})')
        if z == 17:
            el = await pg.query_selector('.evm-map' if evo else '#map')
            await el.screenshot(path=str(SHOTS / f'labels-{tag}-isto-mesto-z17.png'))
            box = await pg.evaluate(f"(() => {{ const r = {M(evo)}.getCanvas().getBoundingClientRect(); return [r.left, r.top]; }})()")
            for i in ids:
                x, y = xy[i]
                if mob:
                    await pg.touchscreen.tap(box[0] + x, box[1] + y)
                else:
                    await pg.mouse.click(box[0] + x, box[1] + y)
                await pg.wait_for_timeout(700)
                h = await pg.evaluate('decodeURIComponent(location.hash.slice(1))')
                check(h == i, f'{tag} copies z17: a tap on {i} opens its card ({h})')
                await pg.evaluate("(() => { const x = document.querySelector('#mcard .ccard .x, .evm-card .evm-x'); if (x) x.click(); })()")
                await pg.wait_for_timeout(400)


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'])
        for mp in MAPS:
            evo = mp == 'evo'
            for w, h in ((390, 844), (1440, 900)):
                mob = w < 500
                tag = f'{mp}-{w}'
                for var in PARTS:
                    if evo and var == 'eur':
                        continue   # the evolako.rs labels stay in dinars: its currency script converts the page, not the map canvas
                    ctx = await b.new_context(viewport={'width': w, 'height': h}, device_scale_factor=1, is_mobile=mob, has_touch=mob)
                    pg, errs = await (open_evo if evo else open_bv)(ctx, 'rsd' if var == 'copies' else var, copies=var == 'copies')
                    if var == 'copies':
                        await copies(pg, evo, tag, mob)
                    else:
                        await views(pg, evo, tag, var, mob)
                    check(not errs, f'{tag} {var}: no JS errors' + (f' {errs[:2]}' if errs else ''))
                    await ctx.close()
        await b.close()
    print('\n' + ('ALL OK' if not fails else f'{len(fails)} FAIL'))
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    asyncio.run(main())
