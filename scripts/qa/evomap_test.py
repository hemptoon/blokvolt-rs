# The Evolako charger map (scripts/evomap, RUNBOOK 3.25) on a mock evolako.rs page, against the local dist/:
# per-connector prices, Lapovo (guard), „Moj auto“ (the cost engine must match blokvolt.rs: Super Vero NS 8,38 RSD/km),
# the cheapest sort, „Najbliži punjač“, SR/EN/RU, phone width, no JS errors.
# Usage: python3 scripts/evomap/build.py && python3 build.py && python3 scripts/qa/evomap_test.py
# (MapLibre 5.24.0 is taken from npm into /tmp/evomap/ml the first time; the container cannot reach jsDelivr or OpenFreeMap.)
import asyncio, json, os, re, subprocess, sys, tarfile
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[2]
DIST = ROOT / 'dist'
TMP = Path('/tmp/evomap')
ML = TMP / 'ml' / 'package' / 'dist'
if not (ML / 'maplibre-gl.js').exists():
    (TMP / 'ml').mkdir(parents=True, exist_ok=True)
    subprocess.check_call(['npm', 'pack', 'maplibre-gl@5.24.0', '--silent'], cwd=TMP / 'ml', stdout=subprocess.DEVNULL)
    with tarfile.open(TMP / 'ml' / 'maplibre-gl-5.24.0.tgz') as t:
        t.extractall(TMP / 'ml', members=[m for m in t.getmembers() if m.name in ('package/dist/maplibre-gl.js', 'package/dist/maplibre-gl.css')])
HEAD = ((TMP / 'head_style.html').read_text() + '\n<script>' + (ROOT / 'scripts' / 'evomap' / 'page_bvq.js').read_text() + '</script>')
FOOT = (TMP / 'footer_tag.html').read_text()
STYLE = {"version": 8, "glyphs": "https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf", "sources": {},
         "layers": [{"id": "bg", "type": "background", "paint": {"background-color": "#e9ecef"}}]}
OUT = sys.argv[1] if len(sys.argv) > 1 else '/tmp/evomap/shots'
os.makedirs(OUT, exist_ok=True)

def page_html(lang):
    return ('<!doctype html><html lang="%s"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">' % lang
            + HEAD + '</head><body><div class="v3-ph"><h1>Mapa</h1></div>'
            + '<div class="evm-sec"><div class="evm-wrap"><div id="evm" class="evm"></div></div></div>' + FOOT + '</body></html>')

async def route_all(pg, lang):
    async def route(r):
        u = r.request.url
        if u.startswith('https://www.evolako.rs/mapa-punjaca'):
            return await r.fulfill(status=200, content_type='text/html; charset=utf-8', body=page_html(lang))
        if u.startswith('https://www.blokvolt.rs/'):
            p = DIST / u.split('https://www.blokvolt.rs/', 1)[1].split('?')[0].split('#')[0]
            if p.is_file():
                ct = {'.json': 'application/json', '.js': 'application/javascript', '.svg': 'image/svg+xml', '.png': 'image/png'}.get(p.suffix, 'application/octet-stream')
                return await r.fulfill(status=200, content_type=ct, headers={'Access-Control-Allow-Origin': '*'}, body=p.read_bytes())
            return await r.fulfill(status=404, headers={'Access-Control-Allow-Origin': '*'}, body='nf')
        if 'maplibre-gl@5.24.0/dist/maplibre-gl.js' in u:
            return await r.fulfill(status=200, content_type='application/javascript', headers={'Access-Control-Allow-Origin': '*'}, body=(ML / 'maplibre-gl.js').read_bytes())
        if 'maplibre-gl@5.24.0/dist/maplibre-gl.css' in u:
            return await r.fulfill(status=200, content_type='text/css', headers={'Access-Control-Allow-Origin': '*'}, body=(ML / 'maplibre-gl.css').read_bytes())
        if u.startswith('https://tiles.openfreemap.org/styles/'):
            return await r.fulfill(status=200, content_type='application/json', headers={'Access-Control-Allow-Origin': '*'}, body=json.dumps(STYLE))
        if u.startswith('https://tiles.openfreemap.org/fonts/'):
            return await r.fulfill(status=200, content_type='application/x-protobuf', headers={'Access-Control-Allow-Origin': '*'}, body=b'')
        if u.endswith('.js'):
            return await r.fulfill(status=200, content_type='application/javascript', body='')
        return await r.fulfill(status=204, body='')
    await pg.route('**/*', route)


fails = []
def ok(c, msg, extra=''):
    print(('ok   ' if c else 'FAIL ') + msg, extra)
    if not c: fails.append(msg)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for lang, w, h in [('sr', 1440, 900), ('en', 1440, 900), ('ru', 390, 844), ('sr', 390, 844)]:
            ctx = await b.new_context(viewport={'width': w, 'height': h}, geolocation={'latitude': 45.2551, 'longitude': 19.8452}, permissions=['geolocation'])
            pg = await ctx.new_page()
            errs = []
            pg.on('pageerror', lambda e: errs.append('JS ' + str(e)[:200]))
            pg.on('console', lambda m: errs.append('CON ' + m.text[:200]) if m.type == 'error' else None)
            await route_all(pg, lang)
            await pg.goto('https://www.evolako.rs/mapa-punjaca?qa=1', wait_until='load')
            await pg.evaluate('''async () => { for (let i = 0; i < 300 && !(document.querySelectorAll('.evm-st').length > 5 && window.evmMap && window.evmCostQa); i++) await new Promise(r => setTimeout(r, 100)); }''')
            tag = f'{lang}-{w}'
            n = await pg.evaluate("document.querySelector('.evm-count').textContent")
            ok('239' in n, f'{tag} count line', n)
            # Lapovo and per-connector prices (without a car)
            res = await pg.evaluate('''async () => {
              const q = document.getElementById('evm-q'); const look = async (t) => { q.value = t; q.dispatchEvent(new Event('input', {bubbles: true})); await new Promise(r => setTimeout(r, 400)); return [...document.querySelectorAll('.evm-st')].slice(0, 6).map(b => [b.dataset.id, b.querySelector('.evm-pr').textContent]); };
              const r = {lap: await look('Lapovo'), vero: await look('Super Vero Novi Sad'), west: await look('West End')}; q.value = ''; q.dispatchEvent(new Event('input', {bubbles: true})); await new Promise(r => setTimeout(r, 300)); return r; }''')
            lap = dict(res['lap'])
            ok('91' in lap.get('cg-52', ''), f'{tag} Lapovo AC price', lap.get('cg-52'))
            ok('108' in lap.get('cg-127', ''), f'{tag} Lapovo DC 50 price', lap.get('cg-127'))
            ok(any('71' in x[1] for x in res['vero']), f'{tag} Super Vero NS ≈71/kWh', res['vero'])
            ok(any('56' in x[1] for x in res['west']), f'{tag} West End eDrive with start fee', res['west'])
            # a card with per-connector lines and the how-to block
            card = await pg.evaluate('''async () => { const b = document.querySelector('.evm-st[data-id="cg-108"]') || null; 
              const q = document.getElementById('evm-q'); q.value = 'DeLasol'; q.dispatchEvent(new Event('input', {bubbles: true})); await new Promise(r => setTimeout(r, 400));
              document.querySelector('.evm-st[data-id="cg-108"]').click(); await new Promise(r => setTimeout(r, 200));
              const c = document.querySelector('.evm-card .evm-cc'); return {lines: c.querySelectorAll('.evm-plines li').length, kako: !!c.querySelector('.evm-kako summary'), kakoT: (c.querySelector('.evm-kako summary')||{}).textContent, pick: !!c.querySelector('[data-car-open]'), txt: c.innerText.slice(0, 400)}; }''')
            ok(card['lines'] >= 2, f'{tag} per-connector lines', card['lines'])
            ok(card['kako'], f'{tag} how-to block', card['kakoT'])
            ok(card['pick'], f'{tag} "choose your car" link in the card')
            await pg.screenshot(path=f'{OUT}/{tag}-card.png')
            # choose a car from the card link
            await pg.click('.evm-card [data-car-open]')
            await pg.wait_for_selector('.evm-carp select[data-car="mk"]', timeout=10000)
            await pg.select_option('.evm-carp select[data-car="mk"]', 'Tesla')
            mdv = await pg.evaluate("[...document.querySelectorAll('.evm-carp select[data-car=md] option')].map(o => [o.value, o.textContent]).filter(x => /Model 3 Long Range/.test(x[1]))[0]")
            await pg.select_option('.evm-carp select[data-car="md"]', mdv[0])
            await pg.screenshot(path=f'{OUT}/{tag}-carform.png')
            await pg.click('.evm-carp [data-car="save"]')
            await pg.wait_for_timeout(400)
            after = await pg.evaluate('''() => { const c = document.querySelector('.evm-card .evm-cc'); return {back: c ? c.querySelector('h2').textContent : null, cost: c && c.querySelector('.evm-cost b') ? c.querySelector('.evm-cost b').textContent : null,
              cmp: c && c.querySelector('.evm-cmp') ? c.querySelector('.evm-cmp').textContent : null, btn: document.querySelector('.evm-car-v').textContent, cheap: !!document.querySelector('.evm-chip[data-f=cheap]'),
              vero: window.evmCostQa('cg-80'), prom: window.evmCostQa('ocm-263893')}; }''')
            ok(after['back'] and 'DeLasol' in after['back'], f'{tag} back to the card after the car', after['back'])
            ok(after['cost'] and ('RSD/km' in after['cost'] or 'RSD/км' in after['cost']), f'{tag} cost line', after['cost'])
            ok(after['cmp'] is not None, f'{tag} petrol/home comparison', after['cmp'])
            ok('Tesla' in after['btn'], f'{tag} car button label', after['btn'])
            ok(after['cheap'], f'{tag} cheapest chip')
            v = after['vero'] or {}
            ok(abs((v.get('km') or 0) - 8.38) < 0.3, f'{tag} cost engine Super Vero NS ≈ 8,4 RSD/km (blokvolt.rs: 8,38)', v)
            pr = after['prom'] or {}
            ok(abs((pr.get('km') or 0) - 15.3) < 0.5, f'{tag} cost engine Promenada AC ≈ 15,3 RSD/km', pr)
            await pg.screenshot(path=f'{OUT}/{tag}-cost.png')
            await pg.keyboard.press('Escape')
            # list per km and the cheapest sort
            await pg.click('.evm-chip[data-f=cheap]')
            await pg.wait_for_timeout(300)
            lst = await pg.evaluate("[...document.querySelectorAll('.evm-st')].slice(0, 5).map(b => b.querySelector('.evm-pr').textContent)")
            ok(all(('RSD/km' in x or 'RSD/км' in x or x in ('Besplatno', 'Free', 'Бесплатно')) for x in lst), f'{tag} list per km, cheapest first', lst)
            # Najbliži
            await pg.click('.evm-near')
            await pg.wait_for_selector('.evm-nrl .evm-nr', timeout=10000)
            rows = await pg.evaluate("[...document.querySelectorAll('.evm-nrl .evm-nr')].map(r => r.querySelector('.evm-nr-nm b').textContent + ' | ' + r.querySelector('.evm-nr-meta').textContent)")
            ok(len(rows) == 3, f'{tag} three nearest', rows)
            await pg.screenshot(path=f'{OUT}/{tag}-near.png')
            sw = await pg.evaluate('[document.documentElement.scrollWidth, innerWidth]')
            ok(sw[0] <= sw[1] + 1, f'{tag} no horizontal scroll', sw)
            ok(not errs, f'{tag} no JS errors', errs[:3])
            await ctx.close()
        await b.close()
    print('FAILS:', len(fails), fails)
    sys.exit(1 if fails else 0)
asyncio.run(main())
