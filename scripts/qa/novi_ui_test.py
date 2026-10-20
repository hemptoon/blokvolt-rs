# "Dodaj punjač" on /mapa/ (RUNBOOK 3.11d): the button under the zoom buttons, the add mode (pin, bar, „Dalje“ zooms in
# first), the duplicate warning near a charger already on the map, the form (confirmation required, power check), what is
# sent, the thanks, Escape, and an approved charger from /api/novi-punjaci on the map and in its card. /api/* is answered
# here and every POST is caught, so nothing leaves the container.
# Usage (server running, see cfserve.py): python3 scripts/qa/novi_ui_test.py [shots-dir] [base-url]
import asyncio, json, sys, time
from pathlib import Path
from playwright.async_api import async_playwright

SHOTS = Path(sys.argv[1] if len(sys.argv) > 1 else '/tmp/bv-shots')
SHOTS.mkdir(parents=True, exist_ok=True)
BASE = sys.argv[2] if len(sys.argv) > 2 else 'http://localhost:8787'
STYLE = {"version": 8, "sources": {}, "glyphs": "https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf",
         "layers": [{"id": "bg", "type": "background", "paint": {"background-color": "#e9ecef"}}]}
NOW = int(time.time())
APPROVED = {"ok": True, "at": NOW, "st": [{"id": "vz-7", "lat": 44.0101, "lon": 20.9105, "n": "Hotel Primer", "k": "ac", "kw": 11, "pl": ["type2"],
                                         "acc": "gosti", "fee": "besplatno", "c": "Parking iza hotela, levo od ulaza", "at": NOW - 86400, "ok": NOW - 3600}]}
fails = []


def check(ok, what):
    print(('ok   ' if ok else 'FAIL ') + what)
    if not ok:
        fails.append(what)


async def until(pg, expr, ms=15000):
    for _ in range(ms // 100):
        try:
            if await pg.evaluate(expr):
                return True
        except Exception:
            pass
        await pg.wait_for_timeout(100)
    return False


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'])
        for w, h, tag in ((1440, 900, 'd'), (390, 844, 'm')):
            mob = tag == 'm'
            ctx = await b.new_context(viewport={'width': w, 'height': h}, has_touch=mob, is_mobile=mob, device_scale_factor=2 if mob else 1)
            pg = await ctx.new_page()
            errs, posts = [], []
            pg.on('pageerror', lambda e: errs.append('JS ' + str(e)[:200]))
            pg.on('console', lambda m: errs.append(m.type + ' ' + m.text[:200]) if m.type == 'error' and 'openfreemap' not in m.text else None)

            async def style(route):
                await route.fulfill(status=200, content_type='application/json', body=json.dumps(STYLE))

            async def glyph(route):
                await route.fulfill(status=200, content_type='application/x-protobuf', body=b'')

            async def api(route):
                rq = route.request
                u = rq.url
                if rq.method == 'POST':
                    posts.append({'url': u, 'ct': rq.headers.get('content-type', ''), 'body': rq.post_data_buffer})
                    return await route.fulfill(status=200, content_type='application/json', body='{"ok":true,"pending":true}')
                if '/api/novi-punjaci' in u:
                    return await route.fulfill(status=200, content_type='application/json', body=json.dumps(APPROVED))
                await route.fulfill(status=200, content_type='application/json', body='{"ok":true,"at":0,"st":{}}')
            await pg.route('**/styles/**', style)
            await pg.route('**/fonts/**', glyph)
            await pg.route('**/api/**', api)
            await pg.goto(BASE + '/mapa/?qa=1', wait_until='networkidle')
            ready = await until(pg, '!!(window.bvMapObjQa && window.bvMapObjQa() && window.bvMapObjQa().loaded())', 30000)
            check(ready, f'{tag}: map loaded')
            # the approved charger from drivers is on the map
            ok = await until(pg, 'window.bvMapQa().some(f => f.id === "vz-7")')
            n = await pg.evaluate('window.bvMapQa().length')
            base = await pg.evaluate("parseInt((document.querySelector('.map-top p') || {}).textContent || '0', 10)")
            check(ok and n == base + 1, f'{tag}: approved driver charger on the map (stations {n} = {base} + 1)')
            v = await pg.evaluate('(window.bvMapQa().find(f => f.id === "vz-7") || {}).v')
            check(v == 'nep', f'{tag}: drawn as not confirmed ({v})')
            # its card
            await pg.evaluate('location.hash = "vz-7"; window.dispatchEvent(new HashChangeEvent("hashchange"))')
            await pg.evaluate("document.querySelector('#mlist').scrollTop = 0")
            await pg.fill('#mq', 'Hotel Primer')
            await pg.wait_for_timeout(400)
            await pg.click('#mlist .st[data-id="vz-7"]')
            await pg.wait_for_timeout(500)
            card = await pg.evaluate("(document.querySelector('.ccard') || {}).innerText || ''")
            check('Punjač je dodao vozač' in card and 'Dodato' in card and 'Parking iza hotela' in card and 'besplatno' in card and 'Samo za goste ili kupce' in card,
                  f'{tag}: card of the driver charger: who added it, date, how to find, price words, access')
            check('Besplatno' not in card.split('Cena')[0], f'{tag}: no "free" badge before the price box')
            await pg.screenshot(path=str(SHOTS / f'novi-{tag}-kartica.png'))
            await pg.keyboard.press('Escape')
            await pg.fill('#mq', '')
            await pg.wait_for_timeout(300)
            # the button and the add mode
            btn = await pg.query_selector('.map-addctl button')
            check(btn is not None, f'{tag}: "Dodaj punjač" button under the zoom buttons')
            await pg.evaluate('window.bvMapObjQa().jumpTo({center: [20.46, 44.81], zoom: 9})')
            await pg.wait_for_timeout(400)
            await btn.click()
            await pg.wait_for_timeout(300)
            pin = await pg.evaluate("!!document.querySelector('.map-wrap.is-adding .add-pin') && !!document.querySelector('.add-bar')")
            check(pin, f'{tag}: add mode: pin and bar')
            near_hidden = await pg.evaluate("getComputedStyle(document.querySelector('#mnear')).display === 'none' && getComputedStyle(document.querySelector('#mme')).display === 'none'")
            check(near_hidden, f'{tag}: "Najbliži" and "Blizu mene" hidden in add mode')
            await pg.screenshot(path=str(SHOTS / f'novi-{tag}-1-oznaka.png'))
            await pg.click('.add-bar [data-add="next"]')
            await pg.wait_for_timeout(900)
            z = await pg.evaluate('window.bvMapObjQa().getZoom()')
            hint = await pg.evaluate("document.querySelector('.add-hint').textContent")
            check(z >= 15 and 'uvećana' in hint, f'{tag}: "Dalje" from zoom 9 zooms in first ({z:.1f}) with a hint')
            # Escape leaves the add mode
            await pg.keyboard.press('Escape')
            await pg.wait_for_timeout(200)
            check(await pg.evaluate("!document.querySelector('.add-pin') && !document.querySelector('.map-wrap.is-adding')"), f'{tag}: Escape ends the add mode')
            # next to a charger already on the map: the form offers its card
            first = await pg.evaluate("(async () => { const j = await (await fetch(JSON.parse(document.getElementById('map-cfg').textContent).stations)).json(); const s = j.stations.find(x => x.id.indexOf('osm-') === 0 && x.lat > 44.7 && x.lat < 44.9); return s ? {id: s.id, c: [s.lon, s.lat]} : null; })()")
            await btn.click()
            await pg.wait_for_timeout(200)
            await pg.evaluate(f"window.bvMapObjQa().jumpTo({{center: [{first['c'][0]} + 0.0002, {first['c'][1]}], zoom: 17}})")
            await pg.wait_for_timeout(500)
            await pg.click('.add-bar [data-add="next"]')
            await pg.wait_for_timeout(500)
            form = await pg.query_selector('.add-form')
            check(form is not None, f'{tag}: "Dalje" at zoom 17 opens the form')
            dup = await pg.evaluate("(document.querySelector('.addp .vf-warn') || {}).innerText || ''")
            check(' m je već punjač' in dup, f'{tag}: duplicate warning near {first["id"]}: {dup[:60]!r}')
            await pg.screenshot(path=str(SHOTS / f'novi-{tag}-2-forma.png'), full_page=False)
            # fill and send: without the confirmation first
            await pg.click('.add-form .opts label.chip:has(input[name=k][value=dc])')
            await pg.click('.add-form .opts label.chip:has(input[name=pl][value=ccs2])')
            await pg.fill('.add-form input[name=kw]', '500')
            await pg.click('.add-form label.chip:has(input[name=fee][value=placa])')
            await pg.fill('.add-form textarea[name=c]', 'Ulaz iz bočne ulice')
            await pg.click('.add-form [type=submit]')
            await pg.wait_for_timeout(200)
            m1 = await pg.evaluate("document.querySelector('.add-msg').textContent")
            check('Potvrdite' in m1 and not posts, f'{tag}: without the confirmation nothing is sent ({m1[:40]!r})')
            await pg.click('.add-form label.add-ja')
            await pg.click('.add-form [type=submit]')
            await pg.wait_for_timeout(200)
            m2 = await pg.evaluate("document.querySelector('.add-msg').textContent")
            check('400' in m2 and not posts, f'{tag}: power 500 kW is refused in the browser ({m2[:40]!r})')
            await pg.fill('.add-form input[name=kw]', '50')
            await pg.wait_for_timeout(4200)          # the worker refuses a send in the first 4 s
            await pg.click('.add-form [type=submit]')
            ok = await until(pg, "!!document.querySelector('.add-done')")
            check(ok, f'{tag}: thanks after sending')
            sent = [x for x in posts if x['url'].endswith('/api/novi-punjac')]
            body = sent[0]['body'].decode('utf-8', 'replace') if sent else ''
            fields = {k: (f'name="{k}"\r\n\r\n{v}\r\n' in body) for k, v in (('k', 'dc'), ('pl', 'ccs2'), ('kw', '50'), ('fee', 'placa'), ('acc', 'nz'), ('ja', '1'), ('lang', 'sr'))}
            check(len(sent) == 1 and 'multipart/form-data' in sent[0]['ct'] and all(fields.values()) and 'name="lat"' in body,
                  f'{tag}: one multipart POST with the point and the answers {fields}')
            await pg.screenshot(path=str(SHOTS / f'novi-{tag}-3-hvala.png'))
            if mob:
                sw = await pg.evaluate('[document.documentElement.scrollWidth, document.documentElement.clientWidth]')
                check(sw[0] <= sw[1], f'{tag}: no horizontal scroll {sw}')
            check(not errs, f'{tag}: no JS errors ' + ('' if not errs else '; '.join(errs[:3])))
            await ctx.close()
        await b.close()
    print('\n' + ('ALL OK' if not fails else f'{len(fails)} FAIL'))
    sys.exit(1 if fails else 0)


asyncio.run(main())
