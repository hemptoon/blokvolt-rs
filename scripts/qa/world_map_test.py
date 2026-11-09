# -*- coding: utf-8 -*-
"""QA of the world map of blokvolt.com (/map/, /sr/mapa/, /ru/karta/; task K2).

Builds dist-com into a temp folder with BV_WORLD_DATA pointing at a local copy of the map data (a folder with latest.json,
manifest-*.json, world-*.pmtiles and cards-*/ — contract v1 §3–5), serves both from one local server that answers HTTP Range
requests (python -m http.server does not), and checks in Playwright (Chromium) at 360, 768 and 1440 px for EN, SR and RU:
  - no console errors, page errors or CSP reports;
  - the filters change the drawn points (MapLibre expressions, no data reload);
  - the filter state goes into the URL and comes back after a reload;
  - the card opens for 20 random pids (and with a real click on a point);
  - "Prijavi grešku" sends the right JSON to a fake address (request interception), and shows the texts for 429 and a network error;
  - the filters can be used with the keyboard;
  - touch targets on 360 px are at least 44 px; layout shift while loading;
  - screenshots.
The base map (tiles.openfreemap.org) is replaced by an empty background style, because the test may run without internet;
the points, cards and manifest are the real files.

Usage: python3 scripts/qa/world_map_test.py --data <folder with latest.json> [--out qa-world] [--langs en,sr,ru]
       [--sizes 360,768,1440] [--cards 20]
Exit code 1 when a check fails; report: <out>/report.json and report.md, screenshots: <out>/*.png"""
import argparse
import gzip
import http.server
import json
import os
import random
import re
import shutil
import socketserver
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAGES = {'en': '/map/', 'sr': '/sr/mapa/', 'ru': '/ru/karta/'}
ABOUT = {'en': '/charging-stations/about-data/', 'sr': '/sr/punjaci/o-podacima/', 'ru': '/ru/zaryadki/o-dannyh/'}
DOWNLOAD = {'en': '/charging-stations/download/', 'sr': '/sr/punjaci/preuzimanje/', 'ru': '/ru/zaryadki/skachat/'}
FAKE_API = 'https://reports.test.invalid/api/svet/prijava'
STUB_STYLE = {'version': 8, 'name': 'stub', 'sources': {}, 'glyphs': 'https://qa-glyphs.invalid/{fontstack}/{range}.pbf', 'layers': [{'id': 'bg', 'type': 'background', 'paint': {'background-color': '#E9EBE6'}}]}


# ------------------------------------------------------------------ Range-capable static server
class RangeHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Accept-Ranges', 'bytes')
        super().end_headers()

    def guess_type(self, path):
        if str(path).endswith('.pmtiles'):
            return 'application/octet-stream'
        if str(path).endswith('.mjs'):
            return 'text/javascript'
        return super().guess_type(path)

    def send_head(self):
        rng = self.headers.get('Range')
        path = self.translate_path(self.path)
        if not rng or os.path.isdir(path) or not os.path.isfile(path):
            return super().send_head()
        m = re.match(r'bytes=(\d*)-(\d*)', rng)
        size = os.path.getsize(path)
        if not m:
            self.send_error(416)
            return None
        a, b = m.group(1), m.group(2)
        if a == '':
            start, end = max(0, size - int(b)), size - 1
        else:
            start, end = int(a), min(size - 1, int(b) if b else size - 1)
        if start > end or start >= size:
            self.send_response(416)
            self.send_header('Content-Range', f'bytes */{size}')
            self.end_headers()
            return None
        f = open(path, 'rb')
        f.seek(start)
        self.send_response(206)
        self.send_header('Content-Type', self.guess_type(path))
        self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
        self.send_header('Content-Length', str(end - start + 1))
        self.end_headers()
        self._range_left = end - start + 1
        return f

    def copyfile(self, source, outputfile):
        left = getattr(self, '_range_left', None)
        if left is None:
            return super().copyfile(source, outputfile)
        while left > 0:
            buf = source.read(min(65536, left))
            if not buf:
                break
            outputfile.write(buf)
            left -= len(buf)
        self._range_left = None


def serve(root):
    class H(RangeHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=str(root), **k)
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    srv = socketserver.ThreadingTCPServer(('127.0.0.1', 0), H)
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, srv.server_address[1]


# ------------------------------------------------------------------ weight
def gz(p):
    return len(gzip.compress(Path(p).read_bytes(), 9))


def weight(dist):
    a = dist / 'assets'
    world = {
        'HTML /map/': dist / 'map' / 'index.html',
        'bv.css': a / 'bv.css', 'com.css': a / 'com.css', 'maplibre-gl.css': a / 'vendor/maplibre-6.11.1/maplibre-gl.css',
        'world-map.css': a / 'world/world-map.css', 'bv.js': a / 'bv.js', 'pmtiles.js': a / 'vendor/pmtiles-4.5.0/pmtiles.js',
        'world-map.js': a / 'world/world-map.js', 'maplibre-gl.mjs': a / 'vendor/maplibre-6.11.1/maplibre-gl.mjs',
        'maplibre-gl-shared.mjs': a / 'vendor/maplibre-6.11.1/maplibre-gl-shared.mjs',
        'maplibre-gl-worker.mjs': a / 'vendor/maplibre-6.11.1/maplibre-gl-worker.mjs',
    }
    rows = {k: (Path(v).stat().st_size, gz(v)) for k, v in world.items() if Path(v).exists()}
    ml = sum(v[1] for k, v in rows.items() if k.startswith('maplibre'))
    total = sum(v[1] for v in rows.values())
    # the same for a regional map of blokvolt.com (loc_map.html + map.js), the closest thing to /mapa/ in this build
    hr = next((p for p in dist.glob('*/*/index.html') if 'map-cfg' in p.read_text(encoding='utf-8')), None)
    mapa = None
    if hr:
        mapa = gz(hr) + gz(a / 'bv.css') + gz(a / 'com.css') + gz(a / 'bv.js') + gz(a / 'map.js') + ml + gz(a / 'vendor/maplibre-6.11.1/maplibre-gl.css')
    return {'files': {k: {'bytes': b, 'gzip': g} for k, (b, g) in rows.items()}, 'total_gzip': total, 'maplibre_gzip': ml,
            'without_maplibre_gzip': total - ml, 'regional_map_page': str(hr.relative_to(dist)) if hr else None, 'regional_map_total_gzip': mapa,
            'fonts_woff2': sum(f.stat().st_size for f in (a / 'fonts').glob('onest-latin*.woff2'))}


# ------------------------------------------------------------------ browser checks
def run(args):
    from playwright.sync_api import sync_playwright
    data = Path(args.data).resolve()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix='wm-qa-'))
    site = tmp / 'site'
    # 1) build with the test data address (port chosen first: one server for the site and the data)
    srv, port = serve(tmp / 'site')
    base = f'http://127.0.0.1:{port}'
    env = dict(os.environ, BV_COM_OUT=str(site), BV_WORLD_DATA=base + '/world/', BV_WORLD_REPORTS=FAKE_API)
    t0 = time.time()
    r = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'gen_com.py')], cwd=ROOT, env=env, capture_output=True, text=True)
    build_s = round(time.time() - t0, 1)
    if r.returncode:
        print(r.stdout[-2000:], r.stderr[-2000:])
        raise SystemExit('gen_com.py failed')
    os.symlink(data, site / 'world')
    W = weight(site)
    man = json.load(open(data / json.load(open(data / 'latest.json'))['manifest']))
    rep = {'base': base, 'build_s': build_s, 'weight': W, 'manifest': {k: man.get(k) for k in ('date', 'tiles', 'counts')}, 'runs': [], 'fails': []}
    fails = rep['fails']
    langs = args.langs.split(',')
    sizes = [int(x) for x in args.sizes.split(',')]
    with sync_playwright() as pw:
        br = pw.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        for lang in langs:
            for w in sizes:
                h = {360: 760, 768: 1024, 1440: 900}.get(w, 900)
                ctx = br.new_context(viewport={'width': w, 'height': h}, has_touch=w < 900, is_mobile=w < 700, device_scale_factor=1,
                                     locale={'en': 'en-GB', 'sr': 'sr-Latn-RS', 'ru': 'ru-RU'}[lang])
                ctx.grant_permissions(['clipboard-read', 'clipboard-write'], origin=base)
                res = one(ctx, base, lang, w, out, args, man)
                rep['runs'].append(res)
                for f in res['fails']:
                    fails.append(f'{lang} {w}: {f}')
                ctx.close()
        br.close()
    srv.shutdown()
    shutil.rmtree(tmp, ignore_errors=True)
    (out / 'report.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding='utf-8')
    md = [f'# World map QA ({time.strftime("%Y-%m-%d %H:%M")})', '', f"Data: {man.get('date')} · {man.get('tiles')} · build {build_s} s", '',
          '## Weight before the first tile (gzip -9)', '']
    for k, v in W['files'].items():
        md.append(f"- {k}: {v['bytes']:,} B, gzip {v['gzip']:,} B")
    md += [f"- **total {W['total_gzip']:,} B** (MapLibre {W['maplibre_gzip']:,} B, everything else {W['without_maplibre_gzip']:,} B); fonts woff2 {W['fonts_woff2']:,} B not counted",
           f"- regional map page for comparison ({W['regional_map_page']}): {W['regional_map_total_gzip']:,} B", '', '## Runs', '']
    for x in rep['runs']:
        md.append(f"- {x['lang']} {x['w']}px: {'OK' if not x['fails'] else 'FAIL: ' + '; '.join(x['fails'])} — " +
                  ', '.join(f'{k}={v}' for k, v in x['info'].items()))
    md += ['', f"Result: {'OK' if not fails else str(len(fails)) + ' failure(s)'}"]
    (out / 'report.md').write_text('\n'.join(md) + '\n', encoding='utf-8')
    print('\n'.join(md))
    return 1 if fails else 0


def one(ctx, base, lang, w, out, args, man):
    fails, info, errors, posted = [], {}, [], []
    page = ctx.new_page()
    page.on('console', lambda m: errors.append(f'console {m.type}: {m.text}') if m.type == 'error' or m.text.startswith('map:') else None)
    page.on('pageerror', lambda e: errors.append(f'pageerror: {e}'))
    ctx.route(re.compile(r'https://tiles\.openfreemap\.org/.*'), lambda route: route.fulfill(status=200, content_type='application/json', body=json.dumps(STUB_STYLE)))

    def glyphs(route):
        # glyphs for the kW labels: from --glyphs (a folder <fontstack>/<range>.pbf, e.g. openmaptiles/fonts) or an empty answer
        from urllib.parse import unquote
        m = re.search(r'qa-glyphs\.invalid/([^/]+)/([0-9]+-[0-9]+)\.pbf', route.request.url)
        f = Path(args.glyphs or '/nonexistent') / unquote(m.group(1)).split(',')[0] / (m.group(2) + '.pbf') if m else None
        route.fulfill(status=200, content_type='application/x-protobuf', body=f.read_bytes() if f and f.exists() else b'')
    ctx.route(re.compile(r'https://qa-glyphs\.invalid/.*'), glyphs)
    mode = {'v': 'ok'}

    def api(route):
        req = route.request
        if req.method == 'OPTIONS':
            return route.fulfill(status=204, headers={'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': 'content-type', 'Access-Control-Allow-Methods': 'POST'})
        posted.append(json.loads(req.post_data or '{}'))
        if mode['v'] == 'net':
            return route.abort('failed')
        if mode['v'] == '429':
            return route.fulfill(status=429, content_type='application/json', headers={'Access-Control-Allow-Origin': '*'}, body='{"ok":false,"error":"limit"}')
        return route.fulfill(status=200, content_type='application/json', headers={'Access-Control-Allow-Origin': '*'}, body='{"ok":true}')
    ctx.route(FAKE_API, api)
    page.add_init_script("""window.__cls=0;try{new PerformanceObserver(l=>{for(const e of l.getEntries()){if(!e.hadRecentInput)window.__cls+=e.value}}).observe({type:'layout-shift',buffered:true})}catch(e){}""")
    view = '#7/45.8/15.6'         # Slovenia / Croatia: EU points and the BlokVolt Balkans in one view
    url = base + PAGES[lang]
    page.goto(url + view, wait_until='load')
    ok = wait_ready(page)
    if not ok:
        fails.append('map not ready')
        page.screenshot(path=str(out / f'{lang}-{w}-fail.png'))
        info['errors'] = errors[:5]
        return {'lang': lang, 'w': w, 'fails': fails + errors[:5], 'info': info}
    page.screenshot(path=str(out / f'{lang}-{w}-map.png'))
    info['cls'] = round(page.evaluate('window.__cls'), 4)
    if info['cls'] > 0.1:
        fails.append(f"layout shift {info['cls']}")
    # robots
    if page.locator('meta[name="robots"][content="noindex,nofollow"]').count() != 1:
        fails.append('no noindex,nofollow')
    # attribution from the manifest
    attr = page.locator('#wm-attr').inner_text()
    info['attr'] = attr[:160]
    if 'OpenStreetMap' not in attr or 'GeoNames' not in attr or not re.search(r'\d', attr):
        fails.append('attribution incomplete: ' + attr[:120])
    hrefs = page.eval_on_selector_all('#wm-attr a', 'as => as.map(a => a.getAttribute("href"))')
    for need in (ABOUT[lang], DOWNLOAD[lang]):
        if need not in hrefs:
            fails.append(f'attribution has no link {need}')
    if w <= 480:
        page.wait_for_function("document.getElementById('wm-attr').classList.contains('is-min')", timeout=9000)
        if page.locator('#wm-attr .wm-attr-full').is_visible():
            fails.append('attribution did not fold after 5 s')
        page.click('#wm-attr .wm-attr-i')
        if not page.locator('#wm-attr .wm-attr-full').is_visible():
            fails.append('(i) did not open the attribution')
        page.screenshot(path=str(out / f'{lang}-{w}-attr-open.png'))
        page.click('#wm-attr .wm-attr-i')
        info['attr_fold'] = 'ok'
    elif page.locator('#wm-attr .wm-attr-i').is_visible():
        fails.append('(i) visible on a wide screen')
    # --- filters change the drawn points
    n0 = count(page)
    info['points_view'] = n0
    open_filters(page, w)
    page.click('[data-snaga="ac"]')
    idle(page)
    n1 = count(page)
    info['points_no_ac'] = n1
    if not (n1 < n0):
        fails.append(f'AC filter did not change the points ({n0} → {n1})')
    page.click('[data-p="70"]')
    idle(page)
    n2 = count(page)
    info['points_no_ac_p70'] = n2
    if not (n2 <= n1):
        fails.append(f'reliability filter did not reduce ({n1} → {n2})')
    # network filter: first chip of "most common in this part of the map"
    chip = page.locator('#wm-top [data-net]:not([data-net="nepoznata"])').first
    if chip.count():
        page.click('[data-p="40"]')
        page.click('[data-snaga="ac"]')
        idle(page)
        slug = chip.get_attribute('data-net')
        chip.click()
        idle(page)
        n3 = count(page)
        info['points_net_' + slug] = n3
        if not (0 < n3 < n0):
            fails.append(f'network filter {slug}: {n3} of {n0}')
        q = page.evaluate('location.search')
        if 'mreza=' + slug not in q:
            fails.append('network not in URL: ' + q)
        page.click(f'#wm-sel [data-unnet="{slug}"]')
        idle(page)
        page.click('[data-snaga="ac"]')
        page.click('[data-p="70"]')
        idle(page)
    else:
        fails.append('no network chips in view')
    # --- URL state survives a reload
    page.click('[data-pristup="svi"]')
    idle(page)
    q = page.evaluate('location.search')
    info['url'] = q
    for need in ('snaga=dc,hpc,nepoznato', 'p=70', 'pristup=svi'):
        if need not in q:
            fails.append(f'URL lacks {need}: {q}')
    page.reload(wait_until='load')
    wait_ready(page)
    st = page.evaluate("({s:[...BVWorldMap.state.snaga].sort().join(','),p:BVWorldMap.state.p,a:BVWorldMap.state.pristup,ac:document.querySelector('[data-snaga=ac]').getAttribute('aria-pressed'),p70:document.querySelector('[data-p=\"70\"]').getAttribute('aria-pressed')})")
    if st != {'s': 'dc,hpc,nepoznato', 'p': 70, 'a': 'svi', 'ac': 'false', 'p70': 'true'}:
        fails.append(f'state after reload: {st}')
    flt = page.evaluate("JSON.stringify(BVWorldMap.map.getFilter('wm-pt'))")
    if '70' not in flt:
        fails.append('filter not applied after reload: ' + flt[:100])
    if w == 360:
        open_filters(page, w)
        page.screenshot(path=str(out / f'{lang}-{w}-filters.png'), full_page=False)
    # back to defaults
    page.goto(url + view, wait_until='load')
    wait_ready(page)
    # --- keyboard: Tab to the first filter chip, Space toggles it
    open_filters(page, w, keyboard=True)
    page.focus('body')
    got = False
    for _ in range(60):
        page.keyboard.press('Tab')
        if page.evaluate("document.activeElement && document.activeElement.dataset && document.activeElement.dataset.snaga === 'ac'"):
            got = True
            break
    if not got:
        fails.append('keyboard: the first filter is not reachable with Tab')
    else:
        page.keyboard.press('Space')
        idle(page)
        if page.get_attribute('[data-snaga="ac"]', 'aria-pressed') != 'false' or 'snaga=' not in page.evaluate('location.search'):
            fails.append('keyboard: Space did not toggle the filter')
        page.keyboard.press('Space')
        idle(page)
        # Tab onwards to the reliability buttons and press Enter on one
        for _ in range(40):
            page.keyboard.press('Tab')
            if page.evaluate("document.activeElement && document.activeElement.dataset && document.activeElement.dataset.p === '50'"):
                page.keyboard.press('Enter')
                break
        idle(page)
        if 'p=50' not in page.evaluate('location.search'):
            fails.append('keyboard: reliability not set with Enter')
        page.click('[data-p="40"]')
    if w < 900:
        page.click('#wm-ft')     # close the filters again on mobile
    # --- touch targets
    if w == 360:
        small = page.evaluate("""() => { const open = document.getElementById('wm-filters'); open.classList.add('is-open');
          const out = []; document.querySelectorAll('#wm-filters button, #wm-ft').forEach(b => { const r = b.getBoundingClientRect();
          if (r.width && r.height && (r.height < 44 || r.width < 44)) out.push((b.textContent||'').trim().slice(0,30)+' '+Math.round(r.width)+'x'+Math.round(r.height)); });
          open.classList.remove('is-open'); return out; }""")
        info['small_targets'] = len(small)
        if small:
            fails.append('targets < 44 px: ' + '; '.join(small[:5]))
    # --- cards for random pids among the drawn points (zoom in first so all points are there)
    page.evaluate("BVWorldMap.map.jumpTo({zoom: 9, center: [15.2, 46.1]})")   # Slovenia (evdb) and Zagreb (BlokVolt)
    idle(page)
    feats = page.evaluate("BVWorldMap.map.queryRenderedFeatures({layers:['wm-pt']}).map(f=>[String(f.properties.i), f.geometry.coordinates])")
    if len(feats) < 5:
        page.evaluate("BVWorldMap.map.jumpTo({zoom: 10, center: [14.5, 46.05]})")
        idle(page)
        feats = page.evaluate("BVWorldMap.map.queryRenderedFeatures({layers:['wm-pt']}).map(f=>[String(f.properties.i), f.geometry.coordinates])")
    uniq = {}
    for pid, c in feats:
        uniq.setdefault(pid, c)
    random.seed(7 + w)
    pick = random.sample(sorted(uniq), min(args.cards, len(uniq)))
    okc, bad = 0, []
    for pid in pick:
        page.evaluate("([p, c]) => BVWorldMap.openCard(p, c, null)", [pid, uniq[pid]])
        try:
            page.wait_for_function("() => { const h = document.querySelector('#wm-card h2'); return h && !document.querySelector('#wm-card .wm-skel'); }", timeout=8000)
            if page.locator('#wm-card .wm-err').count():
                bad.append(pid)
            else:
                okc += 1
        except Exception:
            bad.append(pid)
    info['cards_ok'] = f'{okc}/{len(pick)}'
    if bad or len(pick) < min(args.cards, 5):
        fails.append(f'cards failed: {bad[:5]} (of {len(pick)})')
    # a Balkan point (BlokVolt data) shows the short card with the regional link
    bv = page.evaluate("""() => { const f = BVWorldMap.map.queryRenderedFeatures({layers:['wm-pt']}).find(f => f.properties.i >= 900000000);
                           return f ? [String(f.properties.i), f.geometry.coordinates] : null; }""")
    if bv:
        page.evaluate("([p, c]) => BVWorldMap.openCard(p, c, null)", bv)
        page.wait_for_selector('#wm-card h2:not(:has-text("…"))', timeout=8000)
        page.wait_for_timeout(300)
        more = page.locator('#wm-card a.btn.dark')
        info['balkan_card'] = more.get_attribute('href') if more.count() else None
        if not more.count() or page.locator('#wm-card [data-report]').count():
            fails.append('Balkan card: no regional link or has a report button')
        page.screenshot(path=str(out / f'{lang}-{w}-card-balkan.png'))
    else:
        info['balkan_card'] = 'no Balkan point in view'
    # --- a real click on a point
    page.evaluate("BVWorldMap.map.jumpTo({zoom: 14, center: [%f, %f]})" % tuple(uniq[pick[0]]))
    idle(page)
    xy = page.evaluate("(c) => { const p = BVWorldMap.map.project(c); const r = BVWorldMap.map.getCanvas().getBoundingClientRect(); return [r.left + p.x, r.top + p.y]; }", uniq[pick[0]])
    page.evaluate("document.getElementById('wm-card').classList.remove('is-open')")
    page.mouse.click(xy[0], xy[1])
    try:
        page.wait_for_function("() => document.getElementById('wm-card').classList.contains('is-open') && !document.querySelector('#wm-card .wm-skel')", timeout=8000)
        info['click_card'] = 'ok'
        if 'id=' not in page.evaluate('location.search'):
            fails.append('card open but no ?id= in URL')
    except Exception:
        fails.append('a click on a point did not open its card')
    # --- report form (an evdb point, not Balkan)
    target = next((p for p in pick if int(p) < 900000000), None)
    if not target:
        fails.append('no evdb point among the sampled cards: report form not tested')
    if target:
        page.evaluate("([p, c]) => BVWorldMap.openCard(p, c, null)", [target, uniq[target]])
        page.wait_for_selector('#wm-card [data-report]', timeout=8000)
        page.screenshot(path=str(out / f'{lang}-{w}-card.png'))
        page.click('#wm-card [data-report]')
        page.check('#wm-rf input[value="lokacija"]')
        page.fill('#wm-rt', 'QA test')
        page.fill('#wm-re', 'qa@example.com')
        page.screenshot(path=str(out / f'{lang}-{w}-report.png'))
        e0 = len(errors)
        mode['v'] = '429'
        page.click('#wm-rf button[type="submit"]')
        page.wait_for_function("() => /\\S/.test(document.querySelector('#wm-rf .wm-rmsg').textContent) && !document.querySelector('#wm-rf button[type=submit]').disabled", timeout=8000)
        m429 = page.inner_text('#wm-rf .wm-rmsg')
        mode['v'] = 'net'
        page.click('#wm-rf button[type="submit"]')
        page.wait_for_function("(a) => document.querySelector('#wm-rf .wm-rmsg').textContent !== a && !document.querySelector('#wm-rf button[type=submit]').disabled", arg=m429, timeout=8000)
        mnet = page.inner_text('#wm-rf .wm-rmsg')
        mode['v'] = 'ok'
        page.click('#wm-rf button[type="submit"]')
        page.wait_for_selector('#wm-rep .wm-ok', timeout=8000)
        mok = page.inner_text('#wm-rep .wm-ok')
        # the browser itself logs the two failures the test provokes (429 and the aborted request): expected, not errors
        errors[e0:] = [e for e in errors[e0:] if not re.search(r'Failed to load resource: (the server responded with a status of 429|net::ERR_FAILED)', e)]
        T = page.evaluate("JSON.parse(document.getElementById('wm-i18n').textContent)")
        if m429 != T['r_err_limit']:
            fails.append('429 text: ' + m429)
        if mnet != T['r_err_net']:
            fails.append('network error text: ' + mnet)
        if mok != T['r_ok']:
            fails.append('thank-you text: ' + mok)
        last = posted[-1] if posted else {}
        info['report'] = last
        need = {'pid': int(target), 'type': 'lokacija', 'text': 'QA test', 'email': 'qa@example.com', 'lang': lang, 'hp': ''}
        for k, v in need.items():
            if last.get(k) != v:
                fails.append(f'report field {k}: {last.get(k)!r} != {v!r}')
        if not isinstance(last.get('lat'), (int, float)) or not isinstance(last.get('lon'), (int, float)):
            fails.append('report: no lat/lon for lokacija')
        if not re.fullmatch(r'[A-Z]{2}', str(last.get('cc', ''))) or not re.fullmatch(r'[0-9b-hjkmnp-z]{5}', str(last.get('g', ''))):
            fails.append(f"report: cc/g hints missing ({last.get('cc')!r}, {last.get('g')!r})")
        if set(last) - {'pid', 'type', 'lat', 'lon', 'text', 'email', 'lang', 'hp', 'cc', 'g'}:
            fails.append(f'report: extra fields {set(last)}')
        page.screenshot(path=str(out / f'{lang}-{w}-report-sent.png'))
    # kW labels inside the points from zoom 12 (decision 6): only where the tile has k
    page.evaluate("BVWorldMap.map.jumpTo({zoom: 13, center: [%f, %f]})" % tuple(uniq[pick[0]]))
    idle(page)
    has_k = page.evaluate("BVWorldMap.map.queryRenderedFeatures({layers:['wm-pt']}).some(f => f.properties.k != null)")
    nk = page.evaluate("BVWorldMap.map.queryRenderedFeatures({layers:['wm-kw']}).length")
    info['kw_labels'] = nk if has_k else 'tiles have no k'
    if has_k and not nk:
        fails.append('kW labels missing at z13')
    page.evaluate("BVWorldMap.map.jumpTo({zoom: 11.5})")
    idle(page)
    if page.evaluate("BVWorldMap.map.queryRenderedFeatures({layers:['wm-kw']}).length"):
        fails.append('kW labels below z12')
    if has_k and w == 1440:
        page.evaluate("BVWorldMap.map.jumpTo({zoom: 14})")
        idle(page)
        page.evaluate("document.getElementById('wm-card').classList.remove('is-open')")
        page.screenshot(path=str(out / f'{lang}-{w}-kw-z14.png'))
    # sources dialog
    page.locator('#wm-data [data-sources]').first.click()
    page.wait_for_selector('#wm-src[open]', timeout=4000)
    nsrc = page.locator('#wm-src-body li').count()
    info['sources_listed'] = nsrc
    if nsrc < 2:
        fails.append('sources dialog empty')
    if w == 1440:
        page.screenshot(path=str(out / f'{lang}-{w}-sources.png'))
    page.keyboard.press('Escape')
    # zemlja / grad: the view fits the frame from manifest.places; without the file the parameter is ignored quietly
    if man.get('places') and w == 1440:
        P = json.load(open(Path(args.data) / man['places']))
        cc = 'HR' if 'HR' in P.get('cc', {}) else sorted(P['cc'])[0]
        b = P['cc'][cc]
        page.goto(url + '?zemlja=' + cc, wait_until='load')
        wait_ready(page)
        page.wait_for_timeout(500)
        c = page.evaluate("(() => { const c = BVWorldMap.map.getCenter(); return [c.lng, c.lat, BVWorldMap.map.getZoom()]; })()")
        if not (b[0] <= c[0] <= b[2] and b[1] <= c[1] <= b[3]):
            fails.append(f'zemlja={cc}: centre {c} outside {b}')
        g, cb = max(P.get('city', {}).items(), key=lambda kv: (kv[1][2] - kv[1][0]) * (kv[1][3] - kv[1][1]))
        page.goto(url + '?grad=' + g, wait_until='load')
        wait_ready(page)
        page.wait_for_timeout(500)
        c2 = page.evaluate("(() => { const c = BVWorldMap.map.getCenter(); return [c.lng, c.lat, BVWorldMap.map.getZoom()]; })()")
        if not (cb[0] <= c2[0] <= cb[2] and cb[1] <= c2[1] <= cb[3]) or c2[2] < c[2]:
            fails.append(f'grad={g}: view {c2} not on {cb}')
        if 'grad=' + g not in page.evaluate('location.search'):
            fails.append('grad lost from the URL')
        info['places'] = f'{cc} z{c[2]:.1f}, city {g} z{c2[2]:.1f}'
    elif w == 1440:
        page.goto(url + '?zemlja=DE&grad=2867714', wait_until='load')
        wait_ready(page)
        info['places'] = 'no places file: ignored'
    if errors:
        fails.append(f'{len(errors)} console/page error(s): ' + ' | '.join(errors[:3]))
    page.close()
    return {'lang': lang, 'w': w, 'fails': fails, 'info': info}


def wait_ready(page):
    try:
        page.wait_for_function("() => window.BVWorldMap && BVWorldMap.ready && BVWorldMap.map.loaded()", timeout=30000)
        idle(page)
        return True
    except Exception:
        return False


def idle(page):
    page.wait_for_timeout(150)
    try:
        page.wait_for_function("() => BVWorldMap.map.loaded() && BVWorldMap.map.areTilesLoaded()", timeout=15000)
    except Exception:
        pass
    page.evaluate("() => new Promise(r => { const m = BVWorldMap.map; if (!m.isMoving() && m.loaded()) { m.once('idle', r); m.triggerRepaint(); setTimeout(r, 1500); } else m.once('idle', r); })")


def count(page):
    return page.evaluate("new Set(BVWorldMap.map.queryRenderedFeatures({layers:['wm-pt']}).map(f => f.properties.i)).size")


def open_filters(page, w, keyboard=False):
    if w < 900 and page.get_attribute('#wm-ft', 'aria-expanded') != 'true':
        if keyboard:
            page.focus('#wm-ft')
            page.keyboard.press('Enter')
        else:
            page.click('#wm-ft')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', required=True)
    ap.add_argument('--out', default='qa-world')
    ap.add_argument('--langs', default='en,sr,ru')
    ap.add_argument('--sizes', default='360,768,1440')
    ap.add_argument('--cards', type=int, default=20)
    ap.add_argument('--glyphs', default='', help='folder <fontstack>/<range>.pbf for the kW labels (optional)')
    sys.exit(run(ap.parse_args()))
