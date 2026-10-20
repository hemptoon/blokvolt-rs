# Map without number clusters (docs/RUNBOOK.md 3.11, owner's decision 20.10.2026): every charger is drawn at every zoom,
# a tap on several dots zooms in, a tap on one dot (or any tap from zoom 13) opens the card; the region layer too.
# The tiles are not reachable from the container, so the style is a plain background; pass a GeoJSON folder as the
# second argument (countries.geojson, roads.geojson) to draw borders and roads under the dots for screenshots.
# Usage (server running, see cfserve.py): python3 scripts/qa/map_nocluster_test.py [shots-dir] [geojson-dir] [base-url]
import asyncio, json, sys
from pathlib import Path
from playwright.async_api import async_playwright

SHOTS = Path(sys.argv[1] if len(sys.argv) > 1 else '/tmp/bv-shots')
SHOTS.mkdir(parents=True, exist_ok=True)
GEO = Path(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2] != '-' else None
BASE = sys.argv[3] if len(sys.argv) > 3 else 'http://localhost:8787'
STYLE = {"version": 8, "sources": {}, "glyphs": "https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf",
         "layers": [{"id": "bg", "type": "background", "paint": {"background-color": "#F2F1EC"}}]}
if GEO:
    STYLE["sources"] = {"c": {"type": "geojson", "data": json.loads((GEO / 'countries.geojson').read_text())},
                        "r": {"type": "geojson", "data": json.loads((GEO / 'roads.geojson').read_text())}}
    STYLE["layers"] += [
        {"id": "land", "type": "fill", "source": "c", "paint": {"fill-color": ["match", ["get", "iso"], "RS", "#FBFAF7", "#EEEDE7"]}},
        {"id": "road", "type": "line", "source": "r", "filter": ["in", ["get", "t"], ["literal", ["Major Highway", "Secondary Highway"]]],
         "paint": {"line-color": ["match", ["get", "t"], "Major Highway", "#E7C873", "#DADAD2"], "line-width": ["interpolate", ["linear"], ["zoom"], 6, 0.8, 12, 3]}},
        {"id": "border", "type": "line", "source": "c", "paint": {"line-color": "#B9B6AC", "line-width": 1, "line-dasharray": [3, 2]}}]
fails = []


async def until(pg, expr, ms=20000):
    # wait_for_function evaluates a string, which the page's CSP refuses; poll with evaluate instead
    for _ in range(ms // 100):
        try:
            if await pg.evaluate(expr):
                return True
        except Exception:
            pass
        await pg.wait_for_timeout(100)
    raise TimeoutError(expr)


def check(ok, what):
    print(('OK   ' if ok else 'FAIL ') + what)
    if not ok:
        fails.append(what)


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'])
        for w, h, tag in ((1440, 900, 'd'), (390, 844, 'm')):
            mob = tag == 'm'
            ctx = await b.new_context(viewport={'width': w, 'height': h}, has_touch=mob, is_mobile=mob,
                                      device_scale_factor=2 if mob else 1)
            pg = await ctx.new_page()
            errs = []
            pg.on('pageerror', lambda e: errs.append('JS ' + str(e)[:200]))
            pg.on('console', lambda m: errs.append(m.type + ' ' + m.text[:200]) if m.type == 'error' and 'openfreemap' not in m.text else None)

            async def style(route):
                await route.fulfill(status=200, content_type='application/json', body=json.dumps(STYLE))

            async def glyph(route):
                await route.fulfill(status=200, content_type='application/x-protobuf', body=b'')

            async def api(route):
                await route.fulfill(status=200, content_type='application/json', body='{"ok":true,"at":0,"st":{}}')
            await pg.route('**/styles/**', style)
            await pg.route('**/fonts/**', glyph)
            await pg.route('**/api/**', api)
            await pg.goto(BASE + '/mapa/?qa=1', wait_until='networkidle')
            await until(pg, '!!(window.bvMapObjQa && window.bvMapObjQa() && window.bvMapObjQa().loaded() && window.bvMapObjQa().getLayer("pt"))', 30000)
            new = await pg.evaluate('!!window.bvMapObjQa().getLayer("pt") && !window.bvMapObjQa().getLayer("cl")')
            st = await pg.evaluate('JSON.stringify(window.bvMapObjQa().getStyle().sources.st || {}).indexOf("cluster") < 0')
            check(new and st, f'{tag}: no cluster layer and no clustered source')

            async def view(lon, lat, z):
                await pg.evaluate(f'window.bvMapObjQa().jumpTo({{center: [{lon}, {lat}], zoom: {z}}})')
                await until(pg, 'window.bvMapObjQa().loaded() && !window.bvMapObjQa().isMoving()', 20000)
                await pg.wait_for_timeout(400)

            async def rendered(layer):
                return await pg.evaluate(f'new Set(window.bvMapObjQa().queryRenderedFeatures({{layers: ["{layer}"]}}).map(f => f.properties.id)).size')

            # the whole country in view: every Serbian charger is drawn, none is hidden in a cluster
            await pg.evaluate('window.bvMapObjQa().fitBounds([[18.8, 41.85], [23.05, 46.2]], {padding: 10, duration: 0})')
            await until(pg, 'window.bvMapObjQa().loaded() && !window.bvMapObjQa().isMoving()', 20000)
            await pg.wait_for_timeout(500)
            n_all = await pg.evaluate('window.bvMapQa().length')
            n_pt = await rendered('pt')
            check(n_all > 200 and n_pt == n_all, f'{tag}: all {n_all} Serbian chargers drawn on the country view (drawn: {n_pt})')
            z_fit = await pg.evaluate('window.bvMapObjQa().getZoom()')
            n_rg = await rendered('rg-pt')
            check(n_rg > 50, f'{tag}: neighbouring countries drawn as points ({n_rg} at zoom {z_fit:.1f})')
            await pg.screenshot(path=str(SHOTS / f'nocl-{tag}-1-srbija.png'))

            # a tap on the dense Belgrade centre on the country view zooms in instead of opening one card
            await view(20.46, 44.81, 7)
            z0 = await pg.evaluate('window.bvMapObjQa().getZoom()')
            dense = await pg.evaluate('''(() => { const m = window.bvMapObjQa(), p = m.project([20.46, 44.81]);
                const r = 14, f = m.queryRenderedFeatures([[p.x - r, p.y - r], [p.x + r, p.y + r]], {layers: ["pt"]});
                return {x: p.x, y: p.y, n: new Set(f.map(x => x.properties.id)).size}; })()''')
            box = await pg.evaluate('(() => { const r = document.getElementById("map").getBoundingClientRect(); return [r.left, r.top]; })()')
            await pg.screenshot(path=str(SHOTS / f'nocl-{tag}-2-beograd-z7.png'))
            if mob:
                await pg.touchscreen.tap(box[0] + dense['x'], box[1] + dense['y'])
            else:
                await pg.mouse.click(box[0] + dense['x'], box[1] + dense['y'])
            await pg.wait_for_timeout(1200)
            await until(pg, '!window.bvMapObjQa().isMoving()', 20000)
            z1 = await pg.evaluate('window.bvMapObjQa().getZoom()')
            card = await pg.evaluate('!!document.querySelector(".ccard, #mcard.is-open, .is-open .ccard")')
            check(dense['n'] > 1 and z1 >= z0 + 1.9 and not card, f'{tag}: tap on {dense["n"]} dots at zoom {z0:.1f} zooms in to {z1:.1f}, no card')

            # Belgrade at city zoom and at street zoom, for the screenshots
            await view(20.44, 44.80, 10)
            await pg.screenshot(path=str(SHOTS / f'nocl-{tag}-3-beograd-z10.png'))
            # from zoom 13 a tap on a dot opens its card
            await view(20.4155, 44.8155, 13.5)
            one = await pg.evaluate('''(() => { const m = window.bvMapObjQa(), f = m.queryRenderedFeatures({layers: ["pt"]});
                if (!f.length) return null; const p = m.project(f[0].geometry.coordinates); return {x: p.x, y: p.y, id: f[0].properties.id}; })()''')
            if one:
                if mob:
                    await pg.touchscreen.tap(box[0] + one['x'], box[1] + one['y'])
                else:
                    await pg.mouse.click(box[0] + one['x'], box[1] + one['y'])
                await pg.wait_for_timeout(900)
                opened = await pg.evaluate('location.hash')
                check(opened.strip('#') != '', f'{tag}: tap on a dot at zoom 13.5 opens a card ({opened})')
                await pg.screenshot(path=str(SHOTS / f'nocl-{tag}-4-kartica.png'))
            else:
                check(False, f'{tag}: no dot found at zoom 13.5 in Novi Beograd')
            check(not errs, f'{tag}: no JS errors ' + ('' if not errs else '; '.join(errs[:3])))
            await ctx.close()
        await b.close()
    print('\n' + ('ALL OK' if not fails else f'{len(fails)} FAIL'))
    sys.exit(1 if fails else 0)


asyncio.run(main())
