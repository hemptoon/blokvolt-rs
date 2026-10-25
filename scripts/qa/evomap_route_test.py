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
            pg.on('console', lambda m: errs.append('CON ' + m.text[:200]) if m.type == 'error' else None)
            await route_all(pg, lang)

            async def geo(route):
                q = parse_qs(urlparse(route.request.url).query)
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
            check(not errs, f'{tag} no errors {errs[:3]}')
            await ctx.close()
        await b.close()
    print('ALL OK' if not fails else f'{len(fails)} FAILED')
    sys.exit(1 if fails else 0)

asyncio.run(main())
