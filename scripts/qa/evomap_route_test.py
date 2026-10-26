# „Punjači na putu“ on the Evolako map (scripts/evomap, 24.10.2026) on a mock evolako.rs page, against the local dist/:
# the button, suggestions, the route Beograd → Niš, the rows (the same as blokvolt.rs /mapa/ gives for the same line),
# radius chips, a card and back, errors, the phone's „show on map“, SR/EN/RU, no JS errors.
# Usage: python3 scripts/evomap/build.py && python3 build.py && python3 scripts/qa/cfserve.py dist 8787 &
#        python3 scripts/qa/evomap_route_test.py
import asyncio, json, sys
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from playwright.async_api import async_playwright

sys.argv = sys.argv[:1] + ['/tmp/evomap/shots']
HERE = Path(__file__).resolve().parent
src = (HERE / 'evomap_test.py').read_text().split('async def main():')[0]
exec(compile(src, 'evomap_test.py', 'exec'))            # page_html, route_all, ML, STYLE … from the main Evolako test
rt = (HERE / 'map_route_test.py').read_text()
exec(compile('import math\nBASE = "http://127.0.0.1:8787"\n' + rt[rt.index('BEOGRAD'):rt.index('async def main')], 'map_route_test.py', 'exec'))   # LINE, dense, ROUTE, PLACES, photon
fails = []


def check(c, msg):
    print(('ok   ' if c else 'FAIL ') + msg)
    if not c:
        fails.append(msg)


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'])
        # the same rows as blokvolt.rs /mapa/ for the same line (the local dist, served by cfserve.py)
        bp = await (await b.new_context(bypass_csp=True)).new_page()   # the local CSP forbids the string checks below
        await bp.route('https://tiles.openfreemap.org/**', lambda r: r.fulfill(status=200, content_type='application/json', body=json.dumps(STYLE)) if '/styles/' in r.request.url else r.fulfill(status=200, body=b''))
        await bp.route('**/api/**', lambda r: r.fulfill(status=200, content_type='application/json', body='{"ok":true,"st":{},"items":[],"photos":[],"facts":[]}'))
        await bp.goto(BASE + '/mapa/?qa=1', wait_until='load')
        await bp.wait_for_function('window.bvRouteLineQa && window.bvMapQa && window.bvMapQa().length > 100', timeout=30000)
        bv = await bp.evaluate('(l) => window.bvRouteLineQa(l, 238.1249, 5, true).filter(x => !/^osm-|^ocm-/.test("") ).map(x => x.id)', dense(LINE))
        await bp.close()
        for lang, w, h in [('sr', 1440, 900), ('en', 1440, 900), ('ru', 390, 844), ('sr', 390, 844)]:
            ctx = await b.new_context(viewport={'width': w, 'height': h}, geolocation={'latitude': 44.8125, 'longitude': 20.4573}, permissions=['geolocation'],
                                      is_mobile=w < 900, has_touch=w < 900)
            pg = await ctx.new_page()
            errs, calls = [], []
            pg.on('pageerror', lambda e: errs.append('JS ' + str(e)[:200]))
            pg.on('console', lambda m: errs.append('CON ' + m.text[:200]) if m.type == 'error' and 'status of 500' not in m.text else None)
            await route_all(pg, lang)

            async def geo(route):
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
            await pg.goto('https://www.evolako.rs/mapa-punjaca?qa=1', wait_until='load')
            await pg.evaluate('''async () => { for (let i = 0; i < 300 && !(document.querySelectorAll('.evm-st').length > 5 && window.evmMap && window.evmRouteQa); i++) await new Promise(r => setTimeout(r, 100)); }''')
            await pg.wait_for_timeout(800)
            tag = f'{lang}-{w}'
            word = {'sr': 'Punjači na putu', 'en': 'Chargers on the way', 'ru': 'Зарядки по пути'}[lang]
            btn = await pg.inner_text('.evm-rt')
            check(word in btn, f'{tag} button {btn!r}')
            await pg.click('.evm-rt')
            await pg.wait_for_timeout(300)
            await pg.fill('#evm-rt-to', 'Nis')
            await pg.wait_for_timeout(900)
            sug = await pg.evaluate("[...document.querySelectorAll('#evm-rt-to-l button')].map(b=>b.innerText)")
            check(len(sug) == 2 and sug[0].startswith('Niš'), f'{tag} suggestions {sug}')
            await pg.click('#evm-rt-to-l button[data-sug="0"]')
            await pg.wait_for_timeout(1800)
            q = await pg.evaluate('window.evmRouteQa()')
            rows = q['rows']
            check(q['shown'] and q['km'] and abs(q['km'] - 238.1) < 0.2, f'{tag} route drawn')
            check(len(rows) >= 3 and all(r['dc'] >= 50 and r['d'] <= 5 and r['v'] == 'ok' for r in rows), f'{tag} {len(rows)} rows, DC ≥ 50, ≤ 5 km, confirmed')
            check([r['at'] for r in rows] == sorted(r['at'] for r in rows), f'{tag} ordered along the route')
            mine = await pg.evaluate('(l) => window.evmRouteLineQa(l, 238.1249, 5, true).map(x => x.id)', dense(LINE))
            check(mine == bv, f'{tag} same rows as blokvolt.rs (with unconfirmed): {len(mine)} / {len(bv)} ' + str([x for x in mine if x not in bv][:3]) + str([x for x in bv if x not in mine][:3]))
            t = await pg.evaluate("document.querySelector('.evm-rtp').innerText")
            check('238' in t and ({'sr': 'km od polaska', 'en': 'km from the start', 'ru': 'км от старта'}[lang] in t), f'{tag} panel text')
            check(any(c[0] == 'osrm' and c[1].startswith('20.45730,44.81250;21.89590,43.32110') for c in calls), f'{tag} OSRM from my location')
            check([c[2] for c in calls if c[0] == 'photon'][-1] == ('default' if lang == 'ru' else 'en'), f'{tag} Photon language')
            await pg.screenshot(path=f'/tmp/evomap/shots/route_{tag}.png')
            await pg.click('.evm-rtp [data-rt-r="10"]')
            check(len((await pg.evaluate('window.evmRouteQa()'))['rows']) >= len(rows), f'{tag} radius 10')
            await pg.click('.evm-rtp [data-rt-r="5"]')
            await pg.click('.evm-rtp .evm-rt-row .evm-nr-main')
            await pg.wait_for_timeout(500)
            check(await pg.evaluate("!!document.querySelector('.evm-cc [data-rt=\"back\"]')"), f'{tag} card with back link')
            await pg.click('.evm-cc [data-rt="back"]')
            await pg.wait_for_timeout(300)
            check(await pg.evaluate("!!document.querySelector('.evm-rtp .evm-rt-row')"), f'{tag} back to the list')
            if w < 900:
                await pg.click('.evm-rtp [data-rt="map"]')
                await pg.wait_for_timeout(1000)
                q = await pg.evaluate('window.evmRouteQa()')
                check(q['shown'] and not q['open'] and await pg.evaluate("document.querySelector('.evm-card').hidden"), f'{tag} sheet hidden, route on the map')
                await pg.screenshot(path=f'/tmp/evomap/shots/route_map_{tag}.png')
                await pg.click('.evm-rt')
                await pg.wait_for_timeout(400)
            await pg.fill('#evm-rt-to', 'Qqqzzz')
            await pg.press('#evm-rt-to', 'Enter')
            await pg.wait_for_timeout(1000)
            t = await pg.evaluate("document.querySelector('.evm-rtp').innerText")
            check('Qqqzzz' in t and not (await pg.evaluate('window.evmRouteQa()'))['shown'], f'{tag} not found')
            await pg.click('.evm-rtp .evm-x')
            check(not (await pg.evaluate('window.evmRouteQa()'))['open'], f'{tag} closed')
            # ---- the destination picked on the map (27.10.2026): a place name tapped, a long press, a right click ----
            if lang == 'sr' and w > 900:
                import importlib.util, sys as _s
                _s.path.insert(0, str(HERE.parent))
                import map_data
                check(await pg.evaluate('window.evmTownsQa()') == [list(t) for t in map_data.TOWNS], f'{tag} TOWNS = scripts/map_data.py TOWNS')
            words = {'sr': ('Punjači na putu dovde', 'Polazak odavde', 'Izabrana tačka', 'Niš'), 'en': ('Chargers on the way here', 'Start from here', 'Selected point', 'Niš'),
                     'ru': ('Зарядки по пути сюда', 'Старт отсюда', 'Выбранная точка', 'Ниш')}[lang]
            await pg.evaluate("document.querySelector('.evm-map').scrollIntoView({block: 'center'})")
            await pg.wait_for_timeout(400)
            fr = await pg.evaluate(FREE_PX)
            check(len(fr['px']) >= 3, f'{tag} empty map pixels {fr["px"]}')
            P = [(fr['left'] + x, fr['top'] + y) for x, y in fr['px']]
            await pg.evaluate(MOCK_PLACE, [fr['px'][0][0], fr['px'][0][1], 21.8959, 43.3211])
            tap = pg.touchscreen.tap if w < 900 else pg.mouse.click
            await tap(*P[1])
            await pg.wait_for_timeout(400)
            check(not await pg.evaluate("!!document.querySelector('.evm-pop')"), f'{tag} tap on an empty spot: no popup')
            n_rev = len([c for c in calls if c[0] == 'rev'])
            await tap(*P[0])
            await pg.wait_for_timeout(500)
            t = await pg.evaluate("(document.querySelector('.evm-pop')||{}).innerText||''")
            check(words[3] in t and words[0] in t and words[1] in t, f'{tag} place name tapped → popup {t!r}')
            check(len([c for c in calls if c[0] == 'rev']) == n_rev, f'{tag} a tapped name is not sent to Photon')
            box = await pg.evaluate("(() => { const r = document.querySelector('.maplibregl-popup').getBoundingClientRect(); return [r.left, r.right, innerWidth, document.documentElement.scrollWidth]; })()")
            check(box[0] >= 0 and box[1] <= box[2] and box[3] <= box[2], f'{tag} popup inside the screen {box}')
            await pg.screenshot(path=f'/tmp/evomap/shots/route_pick_{tag}.png')
            n_osrm = len([c for c in calls if c[0] == 'osrm'])
            if w > 900:
                check(await pg.evaluate("document.activeElement && document.activeElement.getAttribute('data-pop')") == 'to', f'{tag} popup button has the keyboard focus')
                await pg.keyboard.press('Enter')
            else:
                await pg.click('.evm-pop [data-pop="to"]')
            await pg.wait_for_timeout(1800)
            q = await pg.evaluate('window.evmRouteQa()')
            check(q['open'] and q['shown'] and await pg.input_value('#evm-rt-to') == words[3], f'{tag} popup → route panel with the destination {await pg.input_value("#evm-rt-to")!r}')
            o = [c for c in calls if c[0] == 'osrm'][n_osrm:]
            check(o and o[-1][1] == '20.45730,44.81250;21.89590,43.32110', f'{tag} route runs at once to the label point {o}')
            tip = await pg.evaluate("(document.querySelector('.evm-rtp .evm-rt-tip')||{}).innerText||''")
            check(('dugo pritisni' if lang == 'sr' else 'press and hold' if lang == 'en' else 'долго удерживай') in tip, f'{tag} the panel says a destination can be picked on the map {tip!r}')
            await pg.click('.evm-rtp .evm-x')
            await pg.wait_for_timeout(300)
            if w > 900:
                await pg.evaluate("document.addEventListener('contextmenu', e => { window.__cm = e.defaultPrevented; })")
                await pg.mouse.click(*P[2], button='right')
            else:
                cdp = await ctx.new_cdp_session(pg)
                await cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': P[2][0], 'y': P[2][1]}]})
                await pg.wait_for_timeout(800)
                await cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
            await pg.wait_for_timeout(700)
            t = await pg.evaluate("(document.querySelector('.evm-pop')||{}).innerText||''")
            check('Ćuprija' in t and words[1] in t, f'{tag} {"right click" if w > 900 else "long press"} → popup named by reverse lookup {t!r}')
            rv = [c for c in calls if c[0] == 'rev']
            check(rv and rv[-1][3] == ('default' if lang == 'ru' else 'en'), f'{tag} reverse lookup sent {rv[-1:]}')
            if w > 900:
                check(await pg.evaluate('window.__cm') is True, f'{tag} right click: the browser menu is not opened')
            n_osrm = len([c for c in calls if c[0] == 'osrm'])
            await pg.click('.evm-pop [data-pop="from"]')
            await pg.wait_for_timeout(1500)
            check(await pg.input_value('#evm-rt-from') == 'Ćuprija, Serbia' and await pg.input_value('#evm-rt-to') == words[3], f'{tag} „Polazak odavde“ sets the start, keeps the destination')
            o = [c for c in calls if c[0] == 'osrm'][n_osrm:]
            check(o and not o[-1][1].startswith('20.45730') and o[-1][1].endswith(';21.89590,43.32110'), f'{tag} route from the pressed point {o}')
            await pg.click('.evm-rtp .evm-x')
            await pg.wait_for_timeout(300)
            if w < 900:
                for pts, mv in (([P[1]], 40), ([P[1], (P[1][0] + 80, P[1][1] + 40)], 0)):
                    await cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': x, 'y': y} for x, y in pts]})
                    for k in range(1, 6 if mv else 1):
                        await cdp.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': x + mv * k / 5, 'y': y} for x, y in pts]})
                        await pg.wait_for_timeout(30)
                    await pg.wait_for_timeout(800)
                    await cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
                    await pg.wait_for_timeout(600)
                    check(not await pg.evaluate("!!document.querySelector('.evm-pop')"), f'{tag} {"a drag" if mv else "two fingers"}: no popup')
                # a long press on a charger opens it
                await pg.evaluate("window.evmMap.jumpTo({zoom: 14, center: [20.46, 44.81]})")
                await pg.wait_for_timeout(900)
                st = await pg.evaluate('''() => { const m = window.evmMap, c = m.getCanvas().getBoundingClientRect();
                  const f = m.queryRenderedFeatures({ layers: ['pt'] }).map(f => m.project(f.geometry.coordinates)).find(p => p.x > 40 && p.y > 40 && p.x < c.width - 60 && p.y < c.height - 40);
                  return f ? [c.left + f.x, c.top + f.y] : null; }''')
                check(st is not None, f'{tag} a charger on the screen')
                await cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': st[0], 'y': st[1]}]})
                await pg.wait_for_timeout(800)
                await cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
                await pg.wait_for_timeout(700)
                check(not await pg.evaluate("!!document.querySelector('.evm-pop')") and await pg.evaluate("!!document.querySelector('.evm-card:not([hidden]) .evm-cc:not(.evm-rtp)')"), f'{tag} long press on a charger opens its card')
                await pg.click('.evm-card .evm-x')
                await pg.wait_for_timeout(300)
            else:
                REV[0] = False
                await pg.mouse.click(*P[1], button='right')
                await pg.wait_for_timeout(800)
                t = await pg.evaluate("(document.querySelector('.evm-pop')||{}).innerText||''")
                check(words[2] in t, f'{tag} reverse lookup failed → {t!r}')
                REV[0] = True
                await pg.keyboard.press('Escape')
                await pg.wait_for_timeout(200)
                check(not await pg.evaluate("!!document.querySelector('.evm-pop')"), f'{tag} Escape closes the popup')
            # search without diacritics: the town first
            await pg.click('.evm-rt')
            await pg.wait_for_timeout(300)
            for typed, first in (('Cacak', 'Čačak, Serbia'), ('Zajecar', 'Зајечар' if lang == 'ru' else 'Zaječar'), ('Uzice', 'Ужице' if lang == 'ru' else 'Užice')):
                await pg.fill('#evm-rt-to', '')
                await pg.fill('#evm-rt-to', typed)
                await pg.wait_for_timeout(900)
                sug = await pg.evaluate("[...document.querySelectorAll('#evm-rt-to-l button')].map(b=>b.innerText)")
                check(sug and sug[0] == first, f'{tag} „{typed}“ offers {first} first: {sug[:3]}')
            await pg.click('.evm-rtp .evm-x')
            check(not errs, f'{tag} no errors {errs[:3]}')
            await ctx.close()
        await b.close()
    print('ALL OK' if not fails else f'{len(fails)} FAILED')
    sys.exit(1 if fails else 0)

asyncio.run(main())
