# Service map (/servisi/, docs/RUNBOOK.md 3.31): the layer draws every service, the list and the chips filter, a row and a
# tap open the card (phone, navigation, site, report link), #id opens a card, the list by town opens a card, EN/RU have
# the script texts translated, no JS errors and no horizontal scroll at 360/768/1440.
# The tiles are not reachable from the container: the style is a plain background (like map_nocluster_test.py).
# Usage (server running, see cfserve.py): python3 scripts/qa/servisi_ui_test.py [shots-dir] [base-url]
import asyncio, json, sys
from pathlib import Path
from playwright.async_api import async_playwright

SHOTS = Path(sys.argv[1] if len(sys.argv) > 1 else '/tmp/bv-shots')
SHOTS.mkdir(parents=True, exist_ok=True)
BASE = sys.argv[2] if len(sys.argv) > 2 else 'http://localhost:8787'
STYLE = {"version": 8, "sources": {}, "glyphs": "https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf",
         "layers": [{"id": "bg", "type": "background", "paint": {"background-color": "#F2F1EC"}}]}
DATA = json.loads((Path(__file__).resolve().parents[2] / 'dist' / 'assets' / 'servisi' / 'servisi.json').read_text(encoding='utf-8'))
N, NO = len(DATA['p']), sum(1 for p in DATA['p'] if p['t'] == 'o')
NP, NL = sum(1 for p in DATA['p'] if p['t'] == 'p'), sum(1 for p in DATA['p'] if 'limarija' in (p.get('k') or []))
fails = []


async def until(pg, expr, ms=20000):
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


async def page(b, w, h, mob, path):
    ctx = await b.new_context(viewport={'width': w, 'height': h}, has_touch=mob, is_mobile=mob, device_scale_factor=2 if mob else 1)
    pg = await ctx.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append('JS ' + str(e)[:200]))
    pg.on('console', lambda m: errs.append(m.type + ' ' + m.text[:200]) if m.type == 'error' and 'openfreemap' not in m.text else None)

    async def style(route):
        await route.fulfill(status=200, content_type='application/json', body=json.dumps(STYLE))

    async def glyph(route):
        await route.fulfill(status=200, content_type='application/x-protobuf', body=b'')
    async def api(route):
        await route.fulfill(status=200, content_type='application/json', body='{"ok":true}')
    await pg.route('**/styles/**', style)
    await pg.route('**/fonts/**', glyph)
    await pg.route('**/api/**', api)
    await pg.goto(BASE + path, wait_until='networkidle')
    return ctx, pg, errs


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'])
        for w, h, tag in ((1440, 900, 'd'), (390, 844, 'm')):
            mob = tag == 'm'
            ctx, pg, errs = await page(b, w, h, mob, '/servisi/?qa=1')
            await until(pg, '!!(window.bvSrvQa && window.bvSrvQa() && window.bvSrvQa().loaded() && window.bvSrvQa().getLayer("sv-pt"))', 30000)
            cnt = await pg.evaluate('window.bvSrvQaVis().length')
            check(cnt == N, f'{tag}: all {N} services on the map (got {cnt})')
            rows = await pg.evaluate('document.querySelectorAll("#slist .st").length')
            check(rows == (N if not mob else min(N, 25)), f'{tag}: list rows {rows}')
            await pg.click('#schips [data-f="o"]')
            await pg.wait_for_timeout(200)
            no = await pg.evaluate('window.bvSrvQaVis().every(t => t === "o") && window.bvSrvQaVis().length === %d && document.querySelectorAll("#slist .st .dot.sv-n").length === 0' % NO)
            check(no, f'{tag}: chip Ovlašćeni shows only authorized services')
            # tow services (t p) and body shops (k limarija), since 25.10.2026
            await pg.click('#schips [data-f="slep"]')
            await pg.wait_for_timeout(200)
            sl = await pg.evaluate('window.bvSrvQaVis().every(t => t === "p") && window.bvSrvQaVis().length === %d' % NP)
            check(NP > 0 and sl, f'{tag}: chip Šlep shows only the {NP} tow services')
            await pg.click('#slist .st')
            await until(pg, 'document.querySelector("#scard.is-open .ccard h2")')
            tow = await pg.evaluate('document.querySelector("#scard .ccard").innerText')
            check('prevoz vozila' in tow.lower() and 'gde radi' in tow.lower(), f'{tag}: a tow card shows the flatbed claim and where it works')
            await pg.click('#scard .x')
            await pg.wait_for_timeout(200)
            await pg.click('#schips [data-f="lim"]')
            await pg.wait_for_timeout(200)
            nl = await pg.evaluate('window.bvSrvQaVis().length')
            check(NL > 0 and nl == NL, f'{tag}: chip Limarija shows the {NL} body shops (got {nl})')
            await pg.click('#schips [data-f="all"]')
            # a town whose name is in no other town's service name or street ("Beograd" is also in "Beogradski put",
            # "Čačak" in "Autočačak Promet" in Beograd)
            from collections import Counter
            import unicodedata
            fold = lambda x: ''.join(c for c in unicodedata.normalize('NFD', (x or '').lower().replace('đ', 'd')) if unicodedata.category(c) != 'Mn')
            town = next(t for t, _ in Counter(p['g'] for p in DATA['p']).most_common()
                        if not any(fold(t) in fold(' '.join((p['n'], p.get('a', ''), p.get('ar') or ''))) for p in DATA['p'] if p['g'] != t))
            first = {'g': town}
            await pg.fill('#sq', first['g'])
            await pg.wait_for_timeout(400)
            ok_q = await pg.evaluate('[...document.querySelectorAll("#slist .st .sb")].every(e => e.textContent.indexOf(%s) >= 0)' % json.dumps(first['g']))
            check(ok_q, f'{tag}: search by town keeps only that town')
            await pg.fill('#sq', '')
            await pg.wait_for_timeout(300)
            await pg.click('#slist .st')
            await until(pg, 'document.querySelector("#scard.is-open .ccard h2")')
            card = await pg.evaluate('''(() => { const c = document.querySelector('#scard .ccard'); return {
              nav: !!c.querySelector('[data-nav]'), rep: !!c.querySelector('a[href*="/ispravka/?servis="]'), src: !!c.querySelector('.src a'),
              h: location.hash } })()''')
            check(card['nav'] and card['rep'] and card['src'] and card['h'].startswith('#sv-'), f'{tag}: card has navigation, report link, source; hash {card["h"]}')
            await pg.screenshot(path=str(SHOTS / f'servisi-{tag}-card.png'))
            await pg.click('#scard .x')
            await pg.wait_for_timeout(200)
            check(not await pg.evaluate('document.querySelector("#scard").classList.contains("is-open")'), f'{tag}: card closes')
            # a tap on the map at a service's point
            s = [x for x in DATA["p"] if x.get("lat") is not None][-1]   # the last service with a point
            await pg.evaluate(f'window.bvSrvQa().jumpTo({{center: [{s["lon"]}, {s["lat"]}], zoom: 16}})')
            await until(pg, 'window.bvSrvQa().loaded() && !window.bvSrvQa().isMoving()')
            await pg.wait_for_timeout(400)
            pt = await pg.evaluate(f'(() => {{ const q = window.bvSrvQa().project([{s["lon"]}, {s["lat"]}]); const r = document.getElementById("smap").getBoundingClientRect(); return [q.x + r.left, q.y + r.top]; }})()')
            await pg.mouse.click(pt[0], pt[1])
            await pg.wait_for_timeout(400)
            opened = await pg.evaluate('location.hash')
            check(opened.startswith('#sv-'), f'{tag}: tap on a point opens a card ({opened})')
            ov = await pg.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1')
            check(ov, f'{tag}: no horizontal scroll')
            await pg.screenshot(path=str(SHOTS / f'servisi-{tag}.png'), full_page=False)
            check(not errs, f'{tag}: no JS errors {errs[:3]}')
            await ctx.close()
        # deep link and the list by town
        ctx, pg, errs = await page(b, 1440, 900, False, '/servisi/?qa=1#' + DATA['p'][0]['id'])
        await until(pg, 'document.querySelector("#scard.is-open .ccard h2")')
        h2 = await pg.evaluate('document.querySelector("#scard .ccard h2").textContent')
        check(h2 == DATA['p'][0]['n'], f'#id opens that card ({h2})')
        await pg.click('#scard .x')
        await pg.evaluate('document.querySelector(".svc details").open = true')
        await pg.click('.svc details a[data-sv]')
        await until(pg, 'document.querySelector("#scard.is-open .ccard h2")')
        check(True, 'the list by town opens a card')
        await ctx.close()
        # several firms on one spot (one auto centre): the card names the others and opens them
        pair = next(((a, c) for a in DATA['p'] for c in DATA['p'] if a is not c and a.get('lat') and c.get('lat')
                     and abs(a['lat'] - c['lat']) < 0.0003 and abs(a['lon'] - c['lon']) < 0.0004), None)
        if pair:
            ctx, pg, errs = await page(b, 390, 844, True, '/servisi/?qa=1#' + pair[0]['id'])
            await until(pg, 'document.querySelector("#scard.is-open .sv-same [data-same]")')
            await pg.screenshot(path=str(SHOTS / 'servisi-same-spot.png'))
            await pg.click('#scard .sv-same [data-same]')
            await pg.wait_for_timeout(300)
            hh = await pg.evaluate('location.hash')
            check(hh.startswith('#sv-') and hh != '#' + pair[0]['id'] and not errs, f'same spot: {pair[0]["n"]} lists {pair[1]["n"]} and opens it ({hh})')
            await ctx.close()
        for lang in ('en', 'ru'):
            ctx, pg, errs = await page(b, 1440, 900, False, f'/{lang}/servisi/?qa=1')
            await until(pg, '!!(window.bvSrvQa && window.bvSrvQa() && window.bvSrvQa().loaded())', 30000)
            await pg.click('#slist .st')
            await until(pg, 'document.querySelector("#scard.is-open .ccard h2")')
            txt = await pg.evaluate('document.querySelector("#scard .ccard").innerText + " " + document.querySelector("#scount").innerText')
            sr = [w for w in ('Ovlašćeni servis', 'Nezavisni servis', 'Navigacija', 'Prijavi grešku', 'servisa') if w in txt]
            check(not sr, f'{lang}: card and count translated {sr}')
            await pg.screenshot(path=str(SHOTS / f'servisi-{lang}.png'))
            check(not errs, f'{lang}: no JS errors {errs[:3]}')
            await ctx.close()
        await b.close()
    print('FAILED: %d' % len(fails) if fails else 'ALL OK')
    sys.exit(1 if fails else 0)


asyncio.run(main())
