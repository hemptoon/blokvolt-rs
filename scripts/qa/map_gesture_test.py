# One-finger zoom on every web map (owner's wish 27.10.2026): a tap, then the finger down again and dragged — finger UP
# zooms OUT, finger DOWN zooms IN, as in Google Maps. MapLibre's own tapDragZoom does exactly this (zoomDelta = dy / 128,
# in 6.11.1 on blokvolt.rs and in 5.24.0 of the Evolako map), so the maps keep it; this test makes sure nothing turns it
# around. Also: a double tap still zooms in by one step, a pinch still zooms, a double tap held still before the drag is
# not a long press (no route popup), and a long press (one touch, no tap before it) still opens the route popup.
# Maps: blokvolt.rs /mapa/ (map.js), /servisi/ (servisi.js) and the Evolako map (scripts/evomap) on a mock evolako.rs page.
# Touches are real CDP touch events on a phone viewport (390×844).
# Usage: python3 scripts/evomap/build.py && python3 build.py && python3 scripts/qa/cfserve.py dist 8787 &
#        python3 scripts/qa/map_gesture_test.py
import asyncio, json, sys
from pathlib import Path
from playwright.async_api import async_playwright

sys.argv = sys.argv[:1] + ['/tmp/evomap/shots']
HERE = Path(__file__).resolve().parent
src = (HERE / 'evomap_test.py').read_text().split('async def main():')[0]
exec(compile(src, 'evomap_test.py', 'exec'))            # page_html, route_all, STYLE … from the main Evolako test

BASE = 'http://127.0.0.1:8787'
fails = []


def check(cond, what):
    print(('ok   ' if cond else 'FAIL ') + what)
    if not cond:
        fails.append(what)


# empty pixels of the map (no charger within 24 px), in page coordinates, away from the edges and the controls
FREE_PX = '''async (get) => {
  const m = eval(get), c = m.getCanvas().getBoundingClientRect();
  let out = [];
  // a quiet part of the country at zoom 9 (few chargers), else the first spots found
  for (const ctr of [[20.6, 43.25], [19.5, 44.2], [22.2, 43.9], [20.0, 45.6]]) {
    m.jumpTo({ center: ctr, zoom: 9 });
    await new Promise(r => setTimeout(r, 300));
    out = [];
  const ls = ['pt', 'rg-pt', 'srv', 'srv-pt'].filter(l => m.getLayer(l));
  for (let y = 0.35; y <= 0.7 && out.length < 3; y += 0.05) for (let x = 0.25; x <= 0.7 && out.length < 3; x += 0.05) {
    const px = Math.round(c.width * x), py = Math.round(c.height * y);
    if ((!ls.length || !m.queryRenderedFeatures([[px - 24, py - 24], [px + 24, py + 24]], { layers: ls }).length) && !out.some(q => Math.hypot(q[0] - c.left - px, q[1] - c.top - py) < 80))
      out.push([px + c.left, py + c.top]);
  }
    if (out.length >= 2) break;
  }
  return out;
}'''

TARGETS = [
    # name, url, JS that returns the map, popup selector (None: no route picker on that map)
    ('mapa', BASE + '/mapa/?qa=1', 'window.bvMapObjQa()', '.rtpop'),
    ('servisi', BASE + '/servisi/?qa=1', 'window.bvSrvQa()', None),
    ('evomap', 'https://www.evolako.rs/mapa-punjaca?qa=1', 'window.evmMap', '.evm-pop'),
]


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'])
        for name, url, get, pop in TARGETS:
            ctx = await b.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
            pg = await ctx.new_page()
            errs = []
            pg.on('pageerror', lambda e: errs.append('JS ' + str(e)[:300]))
            if name == 'evomap':
                await route_all(pg, 'sr')
            else:
                await pg.route('https://tiles.openfreemap.org/styles/**', lambda r: r.fulfill(status=200, content_type='application/json', body=json.dumps(STYLE)))
                await pg.route('https://tiles.openfreemap.org/fonts/**', lambda r: r.fulfill(status=200, content_type='application/x-protobuf', body=b''))
                await pg.route('**/api/**', lambda r: r.fulfill(status=200, content_type='application/json', body=json.dumps({'ok': True, 'st': {}, 'items': [], 'photos': [], 'facts': []})))
                await pg.route('https://photon.komoot.io/**', lambda r: r.fulfill(status=500, headers={'Access-Control-Allow-Origin': '*'}, body='err'))
            await pg.goto(url, wait_until='load')
            await pg.evaluate('''async (get) => { for (let i = 0; i < 300; i++) { try { const m = eval(get); if (m && m.loaded()) return; } catch (e) {} await new Promise(r => setTimeout(r, 100)); } }''', get)
            await pg.wait_for_timeout(800)
            cdp = await ctx.new_cdp_session(pg)

            async def T(t, pts):
                await cdp.send('Input.dispatchTouchEvent', {'type': t, 'touchPoints': [{'x': x, 'y': y, 'id': i} for i, (x, y) in enumerate(pts)]})

            async def zoom(z=None):
                if z is not None:
                    await pg.evaluate('([get, z]) => eval(get).jumpTo({ zoom: z })', [get, z])
                    await pg.wait_for_timeout(250)
                return await pg.evaluate('(get) => eval(get).getZoom()', get)

            async def has_pop():
                return bool(pop) and await pg.evaluate('(s) => !!document.querySelector(s)', pop)

            async def close_pop():
                if pop:
                    await pg.evaluate('(s) => document.querySelectorAll(s).forEach(e => (e.closest(".maplibregl-popup") || e).remove())', pop)
                    await pg.keyboard.press('Escape')
                await pg.wait_for_timeout(900)    # past the 800 ms guard after a long press

            async def tap_drag(x, y, dy, hold=0):
                await T('touchStart', [(x, y)])
                await T('touchEnd', [])
                await pg.wait_for_timeout(80)
                await T('touchStart', [(x, y)])
                if hold:
                    await pg.wait_for_timeout(hold)
                for k in range(1, 11):
                    await T('touchMove', [(x, y + dy * k / 10)])
                    await pg.wait_for_timeout(16)
                await T('touchEnd', [])
                await pg.wait_for_timeout(400)

            free = await pg.evaluate(FREE_PX, get)
            check(len(free) >= 2, f'{name}: free spots on the map {free}')
            x, y = free[0]

            # finger up = zoom out, finger down = zoom in (Google Maps), about 1 step per 128 px
            await zoom(9)
            await tap_drag(x, y, -150)
            z = await zoom()
            check(z < 8.5, f'{name}: tap, then drag UP 150 px zooms OUT (9 → {z:.2f})')
            await zoom(9)
            await tap_drag(x, y, 150)
            z = await zoom()
            check(z > 9.5, f'{name}: tap, then drag DOWN 150 px zooms IN (9 → {z:.2f})')
            check(not await has_pop(), f'{name}: no route popup after the one-finger zoom')

            # a double tap still zooms in by one step
            await zoom(9)
            for _ in range(2):
                await T('touchStart', [(x, y)])
                await T('touchEnd', [])
                await pg.wait_for_timeout(80)
            await pg.wait_for_timeout(900)
            z = await zoom()
            check(9.8 < z < 10.2, f'{name}: double tap zooms in one step (9 → {z:.2f})')

            # a pinch still zooms (two fingers apart = in)
            await zoom(9)
            await T('touchStart', [(x - 30, y), (x + 30, y)])
            for k in range(1, 11):
                await T('touchMove', [(x - 30 - 6 * k, y), (x + 30 + 6 * k, y)])
                await pg.wait_for_timeout(16)
            await T('touchEnd', [])
            await pg.wait_for_timeout(400)
            z = await zoom()
            check(z > 9.5, f'{name}: pinch out zooms in (9 → {z:.2f})')
            check(not await has_pop(), f'{name}: no route popup after a pinch')

            if pop:
                await close_pop()
                # a double tap held still for 0,8 s, then dragged: the one-finger zoom, never the long-press popup
                await zoom(9)
                await pg.wait_for_timeout(600)
                await tap_drag(x, y, 150, hold=800)
                z = await zoom()
                check(not await has_pop(), f'{name}: double tap held still is not a long press (no popup)')
                check(z > 9.5, f'{name}: … and the drag down after the hold zooms in (9 → {z:.2f})')
                # a long press (one touch, no tap before it) still opens the popup
                await close_pop()
                x2, y2 = free[1]
                await T('touchStart', [(x2, y2)])
                await pg.wait_for_timeout(800)
                await T('touchEnd', [])
                await pg.wait_for_timeout(600)
                check(await has_pop(), f'{name}: long press opens the route popup')
                # a tap, a pause longer than a double tap, then a long press at the same spot: still a long press
                await close_pop()
                await T('touchStart', [(x2, y2)])
                await T('touchEnd', [])
                await pg.wait_for_timeout(700)
                await T('touchStart', [(x2, y2)])
                await pg.wait_for_timeout(800)
                await T('touchEnd', [])
                await pg.wait_for_timeout(600)
                check(await has_pop(), f'{name}: a tap, a 0,7 s pause, then a long press opens the popup')

            check(not errs, f'{name}: no JS errors {errs[:3]}')
            await ctx.close()
        await b.close()
    print('FAILS:', len(fails), fails)
    sys.exit(1 if fails else 0)

asyncio.run(main())
