# Map page: the neighbouring countries' layer (/assets/map/region.json, cfg.region; RUNBOOK 3.24). Checks the count line,
# the default list (Serbia only), search across the region, a neighbour's card (country, network, link to its blokvolt.com
# map, no prices, reports or "report an error"), the pins of both layers, EN/RU strings, 390 px and console errors.
# Usage (server running, see cfserve.py): python3 scripts/qa/map_region_test.py [shots-dir]
import asyncio, json, sys
from pathlib import Path
from playwright.async_api import async_playwright

SHOTS = Path(sys.argv[1] if len(sys.argv) > 1 else '/tmp/bv-shots')
SHOTS.mkdir(parents=True, exist_ok=True)
BASE = 'http://127.0.0.1:8787'
STYLE = {"version": 8, "sources": {}, "glyphs": "https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf",
         "layers": [{"id": "bg", "type": "background", "paint": {"background-color": "#e9ecef"}}]}
RG = json.load(open(Path(__file__).resolve().parents[2] / 'dist' / 'assets' / 'map' / 'region.json', encoding='utf-8'))
fails = []


def check(cond, what):
    print(('ok   ' if cond else 'FAIL ') + what)
    if not cond:
        fails.append(what)


async def main():
    n_rg = len(RG['stations'])
    hr = next(s for s in RG['stations'] if s['cc'] == 'hr' and s.get('n') and s.get('nn') and (s.get('dc') or 0) >= 50)
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'])
        for w, h, tag in ((1440, 900, 'd'), (390, 844, 'm')):
            ctx = await b.new_context(viewport={'width': w, 'height': h})
            pg = await ctx.new_page()
            errs = []
            pg.on('pageerror', lambda e: errs.append('JS ' + str(e)[:200]))
            pg.on('console', lambda m: errs.append(m.type + ' ' + m.text[:200]) if m.type == 'error' and 'openfreemap' not in m.text else None)
            await pg.route('https://tiles.openfreemap.org/styles/**', lambda r: r.fulfill(status=200, content_type='application/json', body=json.dumps(STYLE)))
            await pg.route('https://tiles.openfreemap.org/fonts/**', lambda r: r.fulfill(status=200, content_type='application/x-protobuf', body=b''))
            await pg.route('**/api/**', lambda r: r.fulfill(status=200, content_type='application/json',
                           body=json.dumps({"ok": True, "st": {}, "avg": None, "nr": 0, "n": 0, "items": [], "photos": []})))
            await pg.goto(BASE + '/mapa/?qa=1', wait_until='load')
            await pg.wait_for_timeout(1800)
            cnt = await pg.inner_text('#mcount')
            check(f'u regionu još {n_rg}' in cnt, f'{tag} count line: {cnt!r}')
            sr = await pg.evaluate('window.bvMapQa().length')
            rg = await pg.evaluate('window.bvMapQa(true).length')
            check(rg == n_rg and sr >= 200, f'{tag} pins: Serbia {sr}, region {rg}')
            rows = await pg.evaluate("[...document.querySelectorAll('#mlist .st')].map(e => e.innerText)")
            check(not any(any(c in r for c in ('Hrvatska', 'Albanija', 'Crna Gora')) for r in rows), f'{tag} default list is Serbia only')
            await pg.fill('#mq', 'Zagreb')
            await pg.wait_for_timeout(500)
            rows = await pg.evaluate("[...document.querySelectorAll('#mlist .st')].map(e => e.innerText.replace(/\\s+/g, ' '))")
            check(len(rows) > 3 and all('Hrvatska' in r for r in rows[:3]), f'{tag} search Zagreb: {len(rows)} rows, first {rows[:1]}')
            await pg.fill('#mq', 'Скопје')
            await pg.wait_for_timeout(500)
            rows = await pg.evaluate("[...document.querySelectorAll('#mlist .st')].map(e => e.innerText.replace(/\\s+/g, ' '))")
            check(len(rows) >= 1 and 'Severna Makedonija' in rows[0], f'{tag} search Скопје: {rows[:1]}')
            await pg.fill('#mq', '')
            await pg.wait_for_timeout(300)
            # chips: "Potvrđeni" hides the neighbours (not checked), "Brzi" keeps their DC ≥ 50 kW
            await pg.click('#mchips .chip[data-f="ok"]')
            await pg.wait_for_timeout(300)
            check(await pg.evaluate('window.bvMapQa(true).length') == 0, f'{tag} Potvrđeni hides the region')
            await pg.click('#mchips .chip[data-f="ok"]')
            await pg.click('#mchips .chip[data-f="fast"]')
            await pg.wait_for_timeout(300)
            fast = await pg.evaluate('window.bvMapQa(true).length')
            want = sum(1 for s in RG['stations'] if (s.get('dc') or 0) >= 50)
            check(fast == want, f'{tag} Brzi in the region: {fast} (data {want})')
            await pg.click('#mchips .chip[data-f="all"]')
            # a neighbour's card
            await pg.goto('about:blank')
            await pg.goto(BASE + '/mapa/?qa=1#' + hr['id'], wait_until='load')
            await pg.wait_for_timeout(1600)
            t = await pg.evaluate("(document.querySelector('.ccard')||{}).innerText || ''")
            check(hr['nn'] in t and 'Hrvatska' in t, f'{tag} card: network {hr["nn"]} and country')
            check('Cene mreža: Hrvatska' in t and 'Punjač je van Srbije' in t, f'{tag} card: price box points to blokvolt.com')
            check('Mapa zemlje na blokvolt.com' in t and 'Prijavi grešku' not in t and 'Iskustva vozača' not in t, f'{tag} card: actions')
            check('Iz otvorenih baza OpenStreetMap i Open Charge Map.' in t, f'{tag} card: not checked one by one')
            href = await pg.evaluate("[...document.querySelectorAll('.ccard .acts a')].map(a => a.href).find(h => h.indexOf('blokvolt.com') >= 0) || ''")
            check(href.startswith('https://blokvolt.com/hr/karta/#'), f'{tag} card link: {href}')
            for x in ('undefined', 'null', 'NaN', '{c}', '{n}'):
                check(x not in t, f'{tag} card has no {x}')
            await pg.screenshot(path=str(SHOTS / f'rg_card_{tag}.png'))
            if tag == 'm':
                sw = await pg.evaluate('[document.documentElement.scrollWidth, document.documentElement.clientWidth]')
                check(sw[0] <= sw[1], f'{tag} no horizontal scroll {sw}')
            for lang, word in (('en', 'more in the region'), ('ru', 'в регионе')):
                await pg.goto(BASE + f'/{lang}/mapa/', wait_until='load')
                await pg.wait_for_timeout(1500)
                c = await pg.inner_text('#mcount')
                check(word in c, f'{tag} {lang} count line: {c!r}')
            check(not errs, f'{tag} console: {errs[:3]}')
            await ctx.close()
        await b.close()
    print('FAILS:', len(fails))
    sys.exit(1 if fails else 0)

asyncio.run(main())
