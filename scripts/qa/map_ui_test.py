# Map page: charger cards, drivers' reports, photo upload, lightbox, the "Potvrđeni" filter and favourites (★).
# /api/* is answered with fake data and every POST is caught, so nothing leaves the container.
# Usage (server running, see cfserve.py): python3 scripts/qa/map_ui_test.py [shots-dir]
import asyncio, json, time, sys, os
from pathlib import Path
from playwright.async_api import async_playwright
from PIL import Image

SHOTS = Path(sys.argv[1] if len(sys.argv) > 1 else '/tmp/bv-shots')
SHOTS.mkdir(parents=True, exist_ok=True)
for name, size in (('sample.jpg', (1600, 1067)), ('sample_th.jpg', (360, 240))):
    if not (SHOTS / name).exists():
        Image.new('RGB', size, (120, 160, 90)).save(SHOTS / name, quality=80)
STYLE = {"version": 8, "sources": {}, "glyphs": "https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf",
         "layers": [{"id": "bg", "type": "background", "paint": {"background-color": "#e9ecef"}}]}
NOW = int(time.time())
SUMM = {"ok": True, "at": NOW, "st": {"ocm-279311": {"a": 4.5, "nr": 2, "n": 3, "s": "ok", "t": NOW - 3600, "f": 1}}}
ONE = {"ok": True, "st": "ocm-279311", "avg": 4.5, "nr": 2, "n": 3,
       "items": [{"id": 3, "s": "ok", "r": 5, "c": "Radi odlično, oba punjača slobodna.", "n": "Marko", "at": NOW - 3600},
                 {"id": 2, "s": "problem", "r": 4, "c": None, "n": None, "at": NOW - 86400 * 3}],
       "photos": [{"id": "a" * 32, "cap": None, "w": 1600, "h": 1067, "at": NOW - 7200}]}
posts = []


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'])
        for w, h, tag in ((1440, 900, 'd'), (390, 844, 'm')):
            ua = {'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1'} if tag == 'm' else {}
            ctx = await b.new_context(viewport={'width': w, 'height': h}, permissions=['clipboard-read', 'clipboard-write'], **ua)
            pg = await ctx.new_page()
            errs = []
            pg.on('pageerror', lambda e: errs.append('JS ' + str(e)[:200]))
            pg.on('console', lambda m: errs.append(m.type + ' ' + m.text[:200]) if m.type == 'error' and 'openfreemap' not in m.text else None)

            async def style(route):
                await route.fulfill(status=200, content_type='application/json', body=json.dumps(STYLE))

            async def glyph(route):
                await route.fulfill(status=200, content_type='application/x-protobuf', body=b'')

            async def api(route):
                req = route.request
                u = req.url
                if req.method == 'POST':
                    posts.append((u, req.headers.get('content-type', '')[:40], len(req.post_data_buffer or b'')))
                    await route.fulfill(status=200, content_type='application/json', body=json.dumps({"ok": True, "pending": '/foto' in u}))
                elif u.endswith('/api/stanice'):
                    await route.fulfill(status=200, content_type='application/json', body=json.dumps(SUMM))
                elif '/api/stanica/' in u:
                    one = dict(ONE) if 'ocm-279311' in u else {"ok": True, "avg": None, "nr": 0, "n": 0, "items": [], "photos": []}
                    await route.fulfill(status=200, content_type='application/json', body=json.dumps(one))
                elif '/api/foto/' in u:
                    await route.fulfill(status=200, content_type='image/jpeg', body=(SHOTS / ('sample_th.jpg' if 'v=t' in u else 'sample.jpg')).read_bytes())
                else:
                    await route.fulfill(status=404, body='')
            await pg.route('https://tiles.openfreemap.org/styles/**', style)
            await pg.route('https://tiles.openfreemap.org/fonts/**', glyph)
            await pg.route('**/api/**', api)
            for sid in ('ocm-279311', 'cg-65'):
                await pg.goto('about:blank')
                await pg.goto(f'http://127.0.0.1:8787/mapa/#{sid}', wait_until='load')
                await pg.wait_for_timeout(1500)
                ok = await pg.evaluate("!!document.querySelector('.ccard')")
                await pg.screenshot(path=str(SHOTS / f'card_{sid}_{tag}.png'))
                print(tag, sid, 'card' if ok else 'NO CARD')
            # drivers' report + photo + lightbox
            await pg.goto('about:blank')
            await pg.goto('http://127.0.0.1:8787/mapa/#ocm-279311', wait_until='load')
            await pg.wait_for_timeout(1500)
            await pg.click('.rv [data-ci="broken"]')
            await pg.click('.rv-stars [data-r="4"]')
            await pg.fill('#rv-c', 'Test komentar')
            await pg.wait_for_timeout(2600)
            await pg.click('.rv-form [type=submit]')
            await pg.wait_for_timeout(800)
            msg = await pg.inner_text('.rv-msg')
            await pg.set_input_files('.rv-add input', str(SHOTS / 'sample.jpg'))
            await pg.wait_for_timeout(1500)
            note = await pg.inner_text('.rv-phnote')
            await pg.click('.rv-th')
            await pg.wait_for_timeout(500)
            lb = await pg.evaluate("!!document.querySelector('.lb img')")
            await pg.keyboard.press('Escape')
            print(tag, 'report msg:', msg, '| photo:', note, '| lightbox', lb)
            # favourites
            await pg.click('.ccard .fav')
            await pg.wait_for_timeout(300)
            st = await pg.evaluate("({pressed: document.querySelector('.ccard .fav').getAttribute('aria-pressed'), store: localStorage.getItem('bv:fav'), n: document.querySelector('[data-favn]').textContent, nh: document.querySelector('[data-favn]').hidden})")
            print(tag, 'fav after click:', st)
            await pg.screenshot(path=str(SHOTS / f'fav_card_{tag}.png'))
            await pg.goto('about:blank')
            await pg.goto('http://127.0.0.1:8787/mapa/?f=fav', wait_until='load')
            await pg.wait_for_timeout(1500)
            cnt = await pg.inner_text('#mcount')
            stars = await pg.evaluate("document.querySelectorAll('.st .fv').length")
            pressed = await pg.evaluate("document.querySelector('#mchips [data-f=fav]').getAttribute('aria-pressed')")
            await pg.screenshot(path=str(SHOTS / f'fav_list_{tag}.png'))
            print(tag, 'fav filter via URL:', cnt, '| stars in list:', stars, '| chip pressed:', pressed)
            await pg.click('.st')
            await pg.wait_for_timeout(800)
            await pg.click('.ccard .fav')
            await pg.wait_for_timeout(400)
            empty = await pg.evaluate("(document.querySelector('#mlist .empty')||{}).textContent || ''")
            store = await pg.evaluate("localStorage.getItem('bv:fav')")
            print(tag, 'after un-fav: store', store, '| empty text:', empty[:60])
            # confirmed filter still works
            await pg.goto('about:blank')
            await pg.goto('http://127.0.0.1:8787/mapa/', wait_until='load')
            await pg.wait_for_timeout(1200)
            await pg.click('#mchips [data-f="ok"]')
            await pg.wait_for_timeout(400)
            print(tag, 'ok-filter count:', await pg.inner_text('#mcount'))
            # "Potvrđeni" combines with another chip; CHAdeMO chip
            await pg.click('#mchips [data-f="fast"]')
            await pg.wait_for_timeout(400)
            both = await pg.evaluate("[...document.querySelectorAll('#mchips .chip[aria-pressed=true]')].map(c => c.dataset.f).join('+')")
            print(tag, 'fast+ok pressed:', both, '| count:', await pg.inner_text('#mcount'))
            await pg.click('#mchips [data-f="ok"]')
            await pg.click('#mchips [data-f="chademo"]')
            await pg.wait_for_timeout(400)
            print(tag, 'chademo count:', await pg.inner_text('#mcount'))
            # card actions: directions (platform order), share (clipboard fallback), stale price warning
            await pg.goto('about:blank')
            await pg.goto('http://127.0.0.1:8787/mapa/#ocm-279311', wait_until='load')
            await pg.wait_for_timeout(1200)
            navs = await pg.evaluate("[...document.querySelectorAll('.ccard [data-nav]')].map(a => a.dataset.nav).join(',')")
            await pg.click('.ccard [data-share]')
            await pg.wait_for_timeout(400)
            shared = await pg.inner_text('.ccard [data-share]')
            print(tag, 'nav order:', navs, '| share button after click:', shared)
            await pg.goto('about:blank')
            await pg.goto('http://127.0.0.1:8787/mapa/?mreza=parking-servis-beograd', wait_until='load')
            await pg.wait_for_timeout(1200)
            if await pg.evaluate("!!document.querySelector('.st')"):
                await pg.click('.st')
                await pg.wait_for_timeout(600)
                print(tag, 'stale price warning:', await pg.evaluate("(document.querySelector('.ccard .stale')||{}).textContent || 'NONE'"))
                await pg.screenshot(path=str(SHOTS / f'stale_card_{tag}.png'))
            print(tag, 'errors:', errs[:6])
            await ctx.close()
        await b.close()
    print('posts caught:', len(posts))

asyncio.run(main())
