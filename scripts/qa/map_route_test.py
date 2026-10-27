# "Punjači na putu" on /mapa/ (24.10.2026): the panel, place suggestions (Photon), the route (OSRM/FOSSGIS), the fast
# chargers along it, the radius chips, a card opened from the list and back, errors, closing, EN/RU, desktop and phone.
# Photon and OSRM are answered with fixed data (the route Beograd → Niš, from the FOSSGIS server on 24.10.2026, simplified
# and filled in every ~300 m); the CSP of dist/_headers still applies, so a blocked host shows up as a console error.
# Usage (server running, see cfserve.py): python3 scripts/qa/map_route_test.py [shots-dir]
import asyncio, json, math, sys
from pathlib import Path
from playwright.async_api import async_playwright

SHOTS = Path(sys.argv[1] if len(sys.argv) > 1 else '/tmp/bv-shots')
SHOTS.mkdir(parents=True, exist_ok=True)
BASE = 'http://127.0.0.1:8787'
STYLE = {"version": 8, "sources": {}, "glyphs": "https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf",
         "layers": [{"id": "bg", "type": "background", "paint": {"background-color": "#e9ecef"}}]}
BEOGRAD = {'latitude': 44.8125, 'longitude': 20.4573}
# Beograd → Niš, routing.openstreetmap.de (overview=simplified), 24.10.2026: 238,1 km, 152 min
LINE = [[20.4573, 44.8126], [20.4489, 44.7983], [20.5328, 44.7617], [20.5407, 44.7261], [20.6264, 44.6538], [20.6554, 44.5678],
        [20.8573, 44.5866], [20.9157, 44.5726], [20.9777, 44.5796], [21.0381, 44.4757], [21.1178, 44.2415], [21.1124, 44.1519],
        [21.1993, 44.0658], [21.2607, 44.034], [21.2852, 43.9788], [21.3852, 43.9425], [21.4067, 43.8734], [21.4365, 43.863],
        [21.4424, 43.7542], [21.516, 43.7363], [21.5687, 43.6233], [21.6529, 43.5875], [21.6971, 43.533], [21.7507, 43.5086],
        [21.7977, 43.4507], [21.7947, 43.4031], [21.8228, 43.3591], [21.8958, 43.3209]]


def dense(line, step=0.3):
    out = [line[0]]
    for a, b in zip(line, line[1:]):
        km = math.hypot((b[0] - a[0]) * 79, (b[1] - a[1]) * 111)
        n = max(1, int(km / step))
        out += [[a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n] for i in range(1, n + 1)]
    return out


ROUTE = {'code': 'Ok', 'routes': [{'distance': 238124.9, 'duration': 9134.5, 'geometry': {'type': 'LineString', 'coordinates': dense(LINE)}}]}
PLACES = {
    'nis': [('Niš', None, 'Serbia', 21.8959, 43.3211), ('Nis', 'Niš', 'Serbia', 21.8773, 43.3166)],
    'beograd': [('Београд', None, 'Serbia', 20.4573, 44.8125)],
    'novi sad': [('Нови Сад', None, 'Serbia', 19.8452, 45.2551)],
    # typed without diacritics (27.10.2026): Photon puts the railway station first — the town must come first
    'cacak': [('Železnička stanica Čačak', 'Čačak', 'Serbia', 20.3466, 43.8937, 'railway', 'station'),
              ('Čačak', None, 'Serbia', 20.3497, 43.8914, 'place', 'town')],
    # only a street in Belgrade from Photon: the town comes from the site's own list (cfg.towns)
    'zajecar': [('Zaječarska', 'Beograd', 'Serbia', 20.4801, 44.7912, 'highway', 'residential')],
}
# the point named by Photon's reverse lookup (a long press or a right click); REV[0] = False answers with an error
REV = [True]
fails = []


def check(cond, what):
    print(('ok   ' if cond else 'FAIL ') + what)
    if not cond:
        fails.append(what)


def photon(q):
    q = q.lower().replace('š', 's')
    for k, v in PLACES.items():
        if q.startswith(k[:3]) and k.startswith(q[:3]):
            return {'type': 'FeatureCollection', 'features': [{'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [x[3], x[4]]},
                    'properties': dict({'name': x[0], 'city': x[1], 'country': x[2], 'type': 'city'}, **({'osm_key': x[5], 'osm_value': x[6]} if len(x) > 5 else {}))} for x in v]}
    return {'type': 'FeatureCollection', 'features': []}


def reverse(lat, lon):
    return {'type': 'FeatureCollection', 'features': [{'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [lon, lat]},
            'properties': {'name': 'Ćuprija', 'country': 'Serbia', 'osm_key': 'place', 'osm_value': 'town', 'type': 'city'}}]}


# a place name of the base map under a pixel: the test style has no vector tiles, so queryRenderedFeatures answers a
# 'place' feature (OpenMapTiles schema) at that one pixel, as OpenFreeMap's labels do
MOCK_PLACE = '''([x, y, lon, lat]) => {
  const m = window.bvMapObjQa ? window.bvMapObjQa() : window.evmMap, o = m.__qrf || m.queryRenderedFeatures.bind(m);
  m.__qrf = o;
  m.queryRenderedFeatures = (g, opt) => {
    if (!opt || !opt.layers) {
      const a = Array.isArray(g) && Array.isArray(g[0]) ? [(g[0][0] + g[1][0]) / 2, (g[0][1] + g[1][1]) / 2] : g && g.x != null ? [g.x, g.y] : null;
      if (a && Math.abs(a[0] - x) < 3 && Math.abs(a[1] - y) < 3)
        return [{ sourceLayer: 'place', properties: { class: 'city', name: 'Ниш', 'name:latin': 'Niš', 'name:en': 'Niš', 'name:ru': 'Ниш' }, geometry: { type: 'Point', coordinates: [lon, lat] } }];
    }
    return o(g, opt);
  };
}'''
# empty pixels of the map (no charger within 18 px), in the map's own coordinates, away from the edges and the controls
FREE_PX = '''() => {
  const m = window.bvMapObjQa ? window.bvMapObjQa() : window.evmMap, c = m.getCanvas().getBoundingClientRect(), out = [];
  const ls = ['pt', 'rg-pt'].filter(l => m.getLayer(l));
  for (let y = 0.3; y <= 0.75 && out.length < 4; y += 0.05) for (let x = 0.2; x <= 0.7 && out.length < 4; x += 0.05) {
    const px = Math.round(c.width * x), py = Math.round(c.height * y);
    if (!m.queryRenderedFeatures([[px - 18, py - 18], [px + 18, py + 18]], { layers: ls }).length && !out.some(q => Math.hypot(q[0] - px, q[1] - py) < 60)) out.push([px, py]);
  }
  return { px: out, left: c.left, top: c.top };
}'''


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'])
        for w, h, tag in ((1440, 900, 'd'), (390, 844, 'm')):
            ctx = await b.new_context(viewport={'width': w, 'height': h}, geolocation=BEOGRAD, permissions=['geolocation'],
                                      is_mobile=tag == 'm', has_touch=tag == 'm')
            pg = await ctx.new_page()
            errs, calls = [], []
            pg.on('pageerror', lambda e: errs.append('JS ' + str(e)[:300]))
            pg.on('console', lambda m: errs.append(m.type + ' ' + m.text[:200]) if m.type == 'error' and 'openfreemap' not in m.text and 'status of 500' not in m.text else None)
            await pg.route('https://tiles.openfreemap.org/styles/**', lambda r: r.fulfill(status=200, content_type='application/json', body=json.dumps(STYLE)))
            await pg.route('https://tiles.openfreemap.org/fonts/**', lambda r: r.fulfill(status=200, content_type='application/x-protobuf', body=b''))
            await pg.route('**/api/**', lambda r: r.fulfill(status=200, content_type='application/json', body=json.dumps({'ok': True, 'st': {}, 'items': [], 'photos': [], 'facts': []})))

            async def geo(route):
                from urllib.parse import urlparse, parse_qs
                u = urlparse(route.request.url)
                q = parse_qs(u.query)
                if u.path.startswith('/reverse'):
                    calls.append(('rev', q.get('lat', [''])[0], q.get('lon', [''])[0], q.get('lang', [''])[0]))
                    if not REV[0]:
                        return await route.fulfill(status=500, headers={'Access-Control-Allow-Origin': '*'}, body='err')
                    return await route.fulfill(status=200, content_type='application/json', headers={'Access-Control-Allow-Origin': '*'},
                                               body=json.dumps(reverse(float(q['lat'][0]), float(q['lon'][0]))))
                calls.append(('photon', q.get('q', [''])[0], q.get('lang', [''])[0]))
                await route.fulfill(status=200, content_type='application/json', headers={'Access-Control-Allow-Origin': '*'}, body=json.dumps(photon(q.get('q', [''])[0])))

            async def osrm(route):
                calls.append(('osrm', route.request.url.split('/driving/')[1].split('?')[0]))
                await route.fulfill(status=200, content_type='application/json', headers={'Access-Control-Allow-Origin': '*'}, body=json.dumps(ROUTE))
            await pg.route('https://photon.komoot.io/**', geo)
            await pg.route('https://routing.openstreetmap.de/**', osrm)

            await pg.goto(BASE + '/mapa/?qa=1', wait_until='load')
            await pg.evaluate("localStorage.removeItem('bv:car'); localStorage.removeItem('bv:tesla')")
            await pg.goto(BASE + '/mapa/?qa=1', wait_until='load')
            await pg.wait_for_timeout(1500)
            btn = await pg.inner_text('#mroute')
            check('Punjači na putu' in btn, f'{tag} button: {btn!r}')
            await pg.click('#mroute')
            await pg.wait_for_timeout(300)
            t = await pg.evaluate("(document.querySelector('.rtp')||{}).innerText||''")
            check('Brzi punjači na putu' in t and 'Polazak' in t and 'Odredište' in t, f'{tag} panel opens')
            # suggestions
            await pg.fill('#rt-to', 'Nis')
            await pg.wait_for_timeout(900)
            sug = await pg.evaluate("[...document.querySelectorAll('#rt-to-l button')].map(b=>b.innerText)")
            check(len(sug) == 2 and sug[0] == 'Niš, Serbia', f'{tag} suggestions {sug}')
            await pg.click('#rt-to-l button[data-sug="0"]')
            await pg.wait_for_timeout(1800)
            q = await pg.evaluate('window.bvRouteQa()')
            t = await pg.evaluate("document.querySelector('.rtp').innerText")
            check(q['shown'] and q['line'] == 'Feature' and abs(q['km'] - 238.1) < 0.2, f'{tag} route drawn {q["km"]} km')
            check('238 km' in t and '2 h 30 min' in t, f'{tag} summary in the panel')
            rows = q['rows']
            check(len(rows) >= 3, f'{tag} chargers along Beograd → Niš at 5 km: {len(rows)}')
            check(all(r['dc'] >= 50 and r['v'] == 'ok' and r['d'] <= 5 for r in rows), f'{tag} all rows DC ≥ 50, confirmed, ≤ 5 km')
            check([r['at'] for r in rows] == sorted(r['at'] for r in rows), f'{tag} rows ordered along the route')
            check(any(c[0] == 'osrm' and c[1].startswith('20.45730,44.81250;21.89590,43.32110') for c in calls), f'{tag} OSRM got my location → Niš: {[c for c in calls if c[0]=="osrm"]}')
            li = await pg.evaluate("document.querySelectorAll('.rtp .rt-row').length")
            check(li == len(rows), f'{tag} list rows = data rows ({li})')
            first = await pg.evaluate("(document.querySelector('.rtp .rt-row .nr-meta')||{}).innerText||''")
            check('km od polaska' in first and 'od puta' in first or 'uz put' in first, f'{tag} row meta: {first!r}')
            lbl = await pg.inner_text('#mroute')
            check('Niš' in lbl and str(len(rows)) in lbl, f'{tag} button label after route: {lbl!r}')
            # same rows as the independent line check
            same = await pg.evaluate('(l) => window.bvRouteLineQa(l, 238.1249, 5, false).map(x => x.id)', dense(LINE))
            check(same == [r['id'] for r in rows], f'{tag} rows = bvRouteLineQa {len(same)} / {len(rows)} ' + str([x for x in same if x not in [r['id'] for r in rows]][:3]) + str([r['id'] for r in rows if r['id'] not in same][:3]))
            await pg.screenshot(path=str(SHOTS / f'route_list_{tag}.png'))
            if tag == 'm':
                # phone: "Prikaži rutu na mapi" hides the sheet and keeps the route; the route button brings the list back
                await pg.click('.rtp [data-rt="map"]')
                await pg.wait_for_timeout(1200)
                q = await pg.evaluate('window.bvRouteQa()')
                check(q['shown'] and not q['open'] and not await pg.evaluate("document.querySelector('#mcard').classList.contains('is-open')"), f'{tag} route on the map, sheet hidden')
                await pg.screenshot(path=str(SHOTS / f'route_map_{tag}.png'))
                await pg.click('#mroute')
                await pg.wait_for_timeout(500)
                check((await pg.evaluate('window.bvRouteQa()'))['open'], f'{tag} route button brings the list back')
            else:
                vis = await pg.evaluate("getComputedStyle(document.querySelector('.rtp [data-rt=\"map\"]')).display")
                check(vis == 'none', f'{tag} no "show on map" button on a computer')
            # radius 10 km and "show unconfirmed"
            await pg.click('.rtp [data-rt-r="10"]')
            q10 = await pg.evaluate('window.bvRouteQa()')
            check(q10['r'] == 10 and len(q10['rows']) >= len(rows), f'{tag} radius 10 km: {len(q10["rows"])} rows')
            await pg.click('.rtp [data-rt-r="2"]')
            q2 = await pg.evaluate('window.bvRouteQa()')
            check(len(q2['rows']) <= len(rows) and all(r['d'] <= 2 for r in q2['rows']), f'{tag} radius 2 km: {len(q2["rows"])} rows')
            await pg.click('.rtp [data-rt-r="5"]')
            nep = await pg.evaluate("!!document.querySelector('.rtp [data-rt=\"nep\"]')")
            if nep:
                await pg.click('.rtp [data-rt="nep"]')
                qn = await pg.evaluate('window.bvRouteQa()')
                check(len(qn['rows']) > len(rows), f'{tag} unconfirmed added: {len(qn["rows"])}')
            # open a charger from the list, then back
            await pg.click('.rtp .rt-row .nr-main')
            await pg.wait_for_timeout(500)
            t = await pg.evaluate("document.querySelector('.ccard').innerText")
            check('← Brzi punjači na putu' in t, f'{tag} card has the back link')
            check((await pg.evaluate('window.bvRouteQa()'))['shown'], f'{tag} route stays drawn under the card')
            await pg.click('.ccard [data-rt="back"]')
            await pg.wait_for_timeout(300)
            t = await pg.evaluate("(document.querySelector('.rtp')||{}).innerText||''")
            check('238 km' in t, f'{tag} back to the route panel')
            # Tesla-only and broken chargers never appear
            bad = await pg.evaluate("window.bvRouteQa().rows.filter(r => !window.bvMapQa().some(p => p.id === r.id && p.k !== 'off' && p.k !== 'tesla')).map(r=>r.id)")
            check(not bad, f'{tag} no broken / Tesla-only rows {bad}')
            # destination link
            href = await pg.get_attribute('.rtp .rt-dest', 'href')
            check(href and '43.32' in href and '21.89' in href, f'{tag} navigation to destination: {href}')
            # close: the route disappears
            await pg.click('.rtp .x')
            q = await pg.evaluate('window.bvRouteQa()')
            check(not q['shown'] and not q['open'], f'{tag} closed panel clears the route')
            # reopen keeps the last trip
            await pg.click('#mroute')
            await pg.wait_for_timeout(600)
            q = await pg.evaluate('window.bvRouteQa()')
            check(q['shown'] and await pg.input_value('#rt-to') == 'Niš, Serbia', f'{tag} reopen shows the last route')
            # an explicit start typed, then a place that does not exist
            await pg.fill('#rt-from', 'Novi Sad')
            await pg.fill('#rt-to', 'Nis')
            await pg.press('#rt-to', 'Enter')
            await pg.wait_for_timeout(1500)
            check(await pg.input_value('#rt-from') == 'Novi Sad, Serbia', f'{tag} start in Latin script: {await pg.input_value("#rt-from")!r}')
            check(any(c[0] == 'osrm' and c[1].startswith('19.84520,45.25510') for c in calls), f'{tag} OSRM from Novi Sad')
            await pg.fill('#rt-to', 'Qqqzzz')
            await pg.press('#rt-to', 'Enter')
            await pg.wait_for_timeout(1200)
            t = await pg.evaluate("document.querySelector('.rtp').innerText")
            check('„Qqqzzz“ nije pronađeno' in t, f'{tag} not found message')
            check(not (await pg.evaluate('window.bvRouteQa()'))['shown'], f'{tag} failed search clears the route')
            await pg.fill('#rt-to', '')
            await pg.press('#rt-to', 'Enter')
            await pg.wait_for_timeout(300)
            check('Upišite odredište.' in await pg.evaluate("document.querySelector('.rtp').innerText"), f'{tag} empty destination')
            await pg.keyboard.press('Escape')
            await pg.wait_for_timeout(200)
            check(not (await pg.evaluate('window.bvRouteQa()'))['open'], f'{tag} Escape closes the panel')
            # "Najbliži punjač" after a route: the route is not left on the map
            await pg.click('#mroute')
            await pg.fill('#rt-to', 'Nis'); await pg.fill('#rt-from', '')
            await pg.press('#rt-to', 'Enter')
            await pg.wait_for_timeout(1500)
            await pg.click('[data-near]' if tag == 'm' else '#mnear')
            await pg.wait_for_timeout(800)
            check(not (await pg.evaluate('window.bvRouteQa()'))['shown'], f'{tag} Najbliži clears the route')
            await pg.screenshot(path=str(SHOTS / f'route_near_{tag}.png'))
            # ---- the destination picked on the map (27.10.2026): a place name tapped, a long press, a right click ----
            await pg.goto(BASE + '/mapa/?qa=1', wait_until='load')
            await pg.wait_for_timeout(1500)
            await pg.evaluate("document.getElementById('map').scrollIntoView({block: 'center'})")
            await pg.wait_for_timeout(300)
            fr = await pg.evaluate(FREE_PX)
            check(len(fr['px']) >= 3, f'{tag} empty map pixels for the test: {fr["px"]}')
            P = [(fr['left'] + x, fr['top'] + y) for x, y in fr['px']]
            await pg.evaluate(MOCK_PLACE, [fr['px'][0][0], fr['px'][0][1], 21.8959, 43.3211])

            async def tap(x, y):
                if tag == 'm':
                    await pg.touchscreen.tap(x, y)
                else:
                    await pg.mouse.click(x, y)
            # a tap on an empty spot: nothing
            await tap(*P[1])
            await pg.wait_for_timeout(400)
            check(not await pg.evaluate("!!document.querySelector('.rtpop')"), f'{tag} tap on an empty spot: no popup')
            # a tap on the place name: the popup, nothing sent anywhere
            n_rev = len([c for c in calls if c[0] == 'rev'])
            await tap(*P[0])
            await pg.wait_for_timeout(500)
            t = await pg.evaluate("(document.querySelector('.rtpop')||{}).innerText||''")
            check('Niš' in t and 'Punjači na putu dovde' in t and 'Polazak odavde' in t, f'{tag} place name tapped → popup {t!r}')
            check(len([c for c in calls if c[0] == 'rev']) == n_rev, f'{tag} a tapped name is not sent to Photon')
            box = await pg.evaluate("(() => { const r = document.querySelector('.maplibregl-popup').getBoundingClientRect(); return [r.left, r.right, innerWidth, document.documentElement.scrollWidth]; })()")
            check(box[0] >= 0 and box[1] <= box[2] and box[3] <= box[2], f'{tag} popup inside the screen {box}')
            if tag == 'd':
                check(await pg.evaluate("document.activeElement && document.activeElement.dataset.pop") == 'to', f'{tag} popup button has the keyboard focus')
                await pg.keyboard.press('Tab')
                check(await pg.evaluate("document.activeElement && document.activeElement.dataset.pop") == 'from', f'{tag} Tab reaches „Polazak odavde“')
                await pg.keyboard.press('Shift+Tab')
            await pg.screenshot(path=str(SHOTS / f'route_pick_{tag}.png'))
            n_osrm = len([c for c in calls if c[0] == 'osrm'])
            if tag == 'd':
                await pg.keyboard.press('Enter')
            else:
                await pg.click('.rtpop [data-pop="to"]')
            await pg.wait_for_timeout(1800)
            q = await pg.evaluate('window.bvRouteQa()')
            check(q['open'] and q['shown'] and await pg.input_value('#rt-to') == 'Niš' and await pg.input_value('#rt-from') == '', f'{tag} popup → route panel with the destination, from my location')
            o = [c for c in calls if c[0] == 'osrm'][n_osrm:]
            check(o and o[-1][1] == '20.45730,44.81250;21.89590,43.32110', f'{tag} route runs at once to the label point {o}')
            check(not await pg.evaluate("!!document.querySelector('.rtpop')"), f'{tag} popup closed after the choice')
            await pg.screenshot(path=str(SHOTS / f'route_pick_run_{tag}.png'))
            await pg.click('.rtp .x')
            await pg.wait_for_timeout(300)
            if tag == 'd':
                # right click: no browser menu, the popup at the point, named by Photon's reverse lookup
                await pg.evaluate("document.addEventListener('contextmenu', e => { window.__cm = e.defaultPrevented; })")
                await pg.mouse.click(*P[2], button='right')
                await pg.wait_for_timeout(700)
                t = await pg.evaluate("(document.querySelector('.rtpop')||{}).innerText||''")
                check(await pg.evaluate('window.__cm') is True, f'{tag} right click: the browser menu is not opened')
                check('Ćuprija' in t and 'Polazak odavde' in t, f'{tag} right click → popup named by reverse lookup {t!r}')
                rv = [c for c in calls if c[0] == 'rev']
                check(rv and rv[-1][3] == 'en', f'{tag} reverse lookup sent {rv[-1:]}')
                n_osrm = len([c for c in calls if c[0] == 'osrm'])
                await pg.click('.rtpop [data-pop="from"]')
                await pg.wait_for_timeout(1500)
                check(await pg.input_value('#rt-from') == 'Ćuprija, Serbia' and await pg.input_value('#rt-to') == 'Niš', f'{tag} „Polazak odavde“ sets the start, keeps the destination')
                o = [c for c in calls if c[0] == 'osrm'][n_osrm:]
                check(o and not o[-1][1].startswith('20.45730') and o[-1][1].endswith(';21.89590,43.32110'), f'{tag} route from the pressed point {o}')
                await pg.click('.rtp .x')
                # reverse lookup fails: "Izabrana tačka" with the coordinates; Escape closes the popup
                REV[0] = False
                await pg.mouse.click(*P[1], button='right')
                await pg.wait_for_timeout(800)
                t = await pg.evaluate("(document.querySelector('.rtpop')||{}).innerText||''")
                check('Izabrana tačka' in t, f'{tag} reverse lookup failed → {t!r}')
                REV[0] = True
                await pg.keyboard.press('Escape')
                await pg.wait_for_timeout(200)
                check(not await pg.evaluate("!!document.querySelector('.rtpop')"), f'{tag} Escape closes the popup')
            else:
                cdp = await ctx.new_cdp_session(pg)

                async def hold(pts, move=None, ms=800):
                    await cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': x, 'y': y} for x, y in pts]})
                    if move:
                        for k in range(1, 6):
                            await cdp.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': x + move * k / 5, 'y': y} for x, y in pts]})
                            await pg.wait_for_timeout(30)
                    await pg.wait_for_timeout(ms)
                    await cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
                    await pg.wait_for_timeout(700)
                await hold([P[2]])
                t = await pg.evaluate("(document.querySelector('.rtpop')||{}).innerText||''")
                check('Ćuprija' in t and 'Punjači na putu dovde' in t, f'{tag} long press → popup named by reverse lookup {t!r}')
                await pg.screenshot(path=str(SHOTS / f'route_press_{tag}.png'))
                await pg.click('.rtpop [data-pop="x"]')
                await pg.wait_for_timeout(200)
                check(not await pg.evaluate("!!document.querySelector('.rtpop')"), f'{tag} popup × closes it')
                n_rev = len([c for c in calls if c[0] == 'rev'])
                await hold([P[1]], move=40)
                check(not await pg.evaluate("!!document.querySelector('.rtpop')") and len([c for c in calls if c[0] == 'rev']) == n_rev, f'{tag} a drag is not a long press')
                await hold([P[1], (P[1][0] + 80, P[1][1] + 40)])
                check(not await pg.evaluate("!!document.querySelector('.rtpop')"), f'{tag} two fingers are not a long press')
                await hold([P[1]], ms=250)
                check(not await pg.evaluate("!!document.querySelector('.rtpop')"), f'{tag} a short touch is not a long press')
                # a long press on a charger keeps opening it, as a tap does (from zoom 13 the nearest dot)
                await pg.evaluate("window.bvMapObjQa().jumpTo({zoom: 14, center: [20.46, 44.81]})")
                await pg.wait_for_timeout(800)
                st = await pg.evaluate('''() => { const m = window.bvMapObjQa(), c = m.getCanvas().getBoundingClientRect();
                  const f = m.queryRenderedFeatures({ layers: ['pt'] }).map(f => m.project(f.geometry.coordinates)).find(p => p.x > 40 && p.y > 40 && p.x < c.width - 60 && p.y < c.height - 40);
                  return f ? [c.left + f.x, c.top + f.y, m.getZoom()] : null; }''')
                check(st is not None, f'{tag} a charger on the screen for the long press')
                await hold([(st[0], st[1])])
                z = await pg.evaluate('window.bvMapObjQa().getZoom()')
                card = await pg.evaluate("!!document.querySelector('#mcard.is-open .ccard:not(.rtp)')")
                check(not await pg.evaluate("!!document.querySelector('.rtpop')") and card, f'{tag} long press on a charger opens its card, no popup')
            # search without diacritics: the town first
            await pg.goto(BASE + '/mapa/?qa=1', wait_until='load')
            await pg.wait_for_timeout(1200)
            await pg.click('#mroute')
            check('dugo pritisnite' in await pg.evaluate("document.querySelector('.rtp').innerText"), f'{tag} the panel says a destination can be picked on the map')
            for typed, first in (('Nis', 'Niš, Serbia'), ('Cacak', 'Čačak, Serbia'), ('Zajecar', 'Zaječar'), ('Uzice', 'Užice'), ('Ниш', 'Niš')):
                await pg.fill('#rt-to', '')
                await pg.fill('#rt-to', typed)
                await pg.wait_for_timeout(900)
                sug = await pg.evaluate("[...document.querySelectorAll('#rt-to-l button')].map(b=>b.innerText)")
                check(sug and sug[0] == first, f'{tag} „{typed}“ offers {first} first: {sug}')
            await pg.fill('#rt-to', 'Zajecar')
            await pg.press('#rt-to', 'Enter')
            await pg.wait_for_timeout(1500)
            check(await pg.input_value('#rt-to') == 'Zaječar' and any(c[0] == 'osrm' and c[1].endswith(';22.28470,43.90360') for c in calls), f'{tag} Enter on „Zajecar“ routes to Zaječar')
            await pg.click('.rtp .x')
            # English and Russian
            for lang, word, title in (('en', 'Chargers on the way', 'Fast chargers on the road'), ('ru', 'Зарядки по пути', 'Быстрые зарядки в пути')):
                await pg.goto(BASE + f'/{lang}/mapa/?qa=1', wait_until='load')
                await pg.wait_for_timeout(1200)
                check(word in await pg.inner_text('#mroute'), f'{tag} {lang} button')
                await pg.click('#mroute')
                await pg.fill('#rt-to', 'Nis')
                await pg.press('#rt-to', 'Enter')
                await pg.wait_for_timeout(1500)
                t = await pg.evaluate("document.querySelector('.rtp').innerText")
                check(title in t and ('km from the start' in t if lang == 'en' else 'км от старта' in t), f'{tag} {lang} panel')
                await pg.screenshot(path=str(SHOTS / f'route_{lang}_{tag}.png'))
                await pg.fill('#rt-to', 'Zajecar')
                await pg.wait_for_timeout(900)
                sug = await pg.evaluate("[...document.querySelectorAll('#rt-to-l button')].map(b=>b.innerText)")
                check(sug and sug[0] == ('Zaječar' if lang == 'en' else 'Зајечар'), f'{tag} {lang} „Zajecar“ first: {sug[:2]}')
                await pg.click('.rtp .x')
                await pg.evaluate("document.getElementById('map').scrollIntoView({block: 'center'})")
                await pg.wait_for_timeout(300)
                fr = await pg.evaluate(FREE_PX)
                await pg.evaluate(MOCK_PLACE, [fr['px'][0][0], fr['px'][0][1], 21.8959, 43.3211])
                await (pg.touchscreen.tap if tag == 'm' else pg.mouse.click)(fr['left'] + fr['px'][0][0], fr['top'] + fr['px'][0][1])
                await pg.wait_for_timeout(500)
                t = await pg.evaluate("(document.querySelector('.rtpop')||{}).innerText||''")
                want = ('Niš', 'Chargers on the way here', 'Start from here') if lang == 'en' else ('Ниш', 'Зарядки по пути сюда', 'Старт отсюда')
                check(all(w in t for w in want), f'{tag} {lang} popup {t!r}')
                await pg.screenshot(path=str(SHOTS / f'route_pick_{lang}_{tag}.png'))
                await pg.click('.rtpop [data-pop="to"]')
                await pg.wait_for_timeout(1500)
                check(await pg.input_value('#rt-to') == want[0], f'{tag} {lang} destination from the popup')
            ru_lang = [c[2] for c in calls if c[0] == 'photon'][-1]
            check(ru_lang == 'default', f'{tag} Photon lang on /ru/: {ru_lang}')
            check(not errs, f'{tag} no JS/console errors {errs[:4]}')
            await ctx.close()
        await b.close()
    print('ALL OK' if not fails else f'{len(fails)} FAILED')
    sys.exit(1 if fails else 0)

asyncio.run(main())
