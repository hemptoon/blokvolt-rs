# Map card, 25.10.2026: „Kako se puni ovde“ as a scheme for every charger in Serbia (network steps or a general scheme),
# the plug icons in „Priključci“, and no card part wider than the card (the buttons used to stick out on /ru/).
# Usage (server running, see cfserve.py): python3 scripts/qa/map_kako_test.py [shots-dir]
import asyncio, collections, json, sys
from pathlib import Path
from playwright.async_api import async_playwright

SHOTS = Path(sys.argv[1] if len(sys.argv) > 1 else '/tmp/bv-shots')
SHOTS.mkdir(parents=True, exist_ok=True)
BASE = 'http://127.0.0.1:8787'
STYLE = {"version": 8, "sources": {}, "layers": [{"id": "bg", "type": "background", "paint": {"background-color": "#e9ecef"}}]}
# one charger of every kind of scheme: network, Tesla, card at the desk (IKEA), staff (Obilićev venac), RFID (Lidl Liman),
# hotel guests, unknown network with a known operator (Best in Parking), unknown network
SAMPLE = {'cg-80': 'net', 'rm-4479035-2042305': 'net', 'ocm-150105': 'net', 'osm-n6797205414': 'desk', 'ocm-125797': 'staff',
          'osm-n10961949709': 'rfid', 'own-garni-hotel-element-novi-sad': 'guests', 'bp-garaza-banovina-novi-sad': 'unk',
          'tim-punjac-knin-novi-sad': 'unk'}
fails = []


def check(cond, what):
    print(('ok   ' if cond else 'FAIL ') + what)
    if not cond:
        fails.append(what)


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'])
        for w, h, tag in ((1180, 760, 'd'), (390, 844, 'm')):
            ctx = await b.new_context(viewport={'width': w, 'height': h}, is_mobile=tag == 'm', has_touch=tag == 'm', bypass_csp=True)
            pg = await ctx.new_page()
            errs = []
            pg.on('pageerror', lambda e: errs.append('JS ' + str(e)[:300]))
            await pg.route('https://tiles.openfreemap.org/**', lambda r: r.fulfill(status=200, content_type='application/json', body=json.dumps(STYLE)))
            await pg.route('**/api/**', lambda r: r.fulfill(status=200, content_type='application/json', body='{"ok":true,"st":{},"items":[],"photos":[],"facts":[]}'))
            await pg.goto(BASE + '/mapa/?qa=1', wait_until='load')
            await pg.wait_for_function('window.bvKakoQa && window.bvMapQa().length > 100', timeout=30000)
            if tag == 'd':
                rows = await pg.evaluate('window.bvKakoQa()')
                rs = [r for r in rows if not r['id'].startswith(('hr-', 'ba-', 'me-', 'al-', 'mk-')) and r['how'] is not None]
                ids_rs = {x['id'] for x in await pg.evaluate('window.bvMapQa()')}
                miss = [r['id'] for r in rows if r['id'] in ids_rs and not (r['how'] and len(r['how']['steps']) >= 2)]
                check(not miss, f'every charger in Serbia has a scheme ({len(ids_rs)} chargers), missing: {miss[:5]}')
                kinds = collections.Counter(r['how']['k'] for r in rs if r['id'] in ids_rs)
                print('     schemes:', dict(kinds))
                by = {r['id']: r['how'] for r in rows}
                for i, k in SAMPLE.items():
                    check(by.get(i) and by[i]['k'] == k, f'{i}: scheme {k} (got {by.get(i) and by[i]["k"]})')
                empty = [r['id'] for r in rs if any(not x[1] for x in r['how']['steps'] + r['how']['facts'])]
                check(not empty, f'no empty step or fact text: {empty[:5]}')
            for lang in ('sr', 'en', 'ru'):
                pre = '' if lang == 'sr' else '/' + lang
                for i, k in SAMPLE.items():
                    if lang != 'sr' and i not in ('cg-80', 'tim-punjac-knin-novi-sad', 'ocm-125797'):
                        continue
                    await pg.goto('about:blank')
                    await pg.goto(f'{BASE}{pre}/mapa/?qa=1#{i}', wait_until='load')
                    await pg.wait_for_selector('.ccard .hw', timeout=15000)
                    r = await pg.evaluate("""() => { const c = document.querySelector('.ccard'), R = c.getBoundingClientRect(), bad = [];
                      c.querySelectorAll('*').forEach(e => { const q = e.getBoundingClientRect(); if (q.width && q.right > R.right + .5) bad.push(e.tagName + '.' + e.className); });
                      const hw = c.querySelector('.hw');
                      return { over: bad.slice(0, 5), sw: c.scrollWidth, cw: c.clientWidth, steps: hw.querySelectorAll('.hw-steps li').length,
                               gen: hw.classList.contains('is-gen'), icons: c.querySelectorAll('.cns .cn-ic svg').length, conns: c.querySelectorAll('.cns li').length,
                               txt: hw.innerText }; }""")
                    check(not r['over'] and r['sw'] <= r['cw'], f'{tag} {lang} {i}: nothing wider than the card {r["over"]}')
                    check(r['steps'] >= 2 and r['gen'] == (k != 'net'), f'{tag} {lang} {i}: {r["steps"]} steps, general={r["gen"]}')
                    check(r['icons'] == r['conns'], f'{tag} {lang} {i}: an icon for every connector ({r["icons"]}/{r["conns"]})')
                    if lang != 'sr':
                        check(not any(x in r['txt'] for x in ('Priključite', 'Skenirajte', 'punjač')), f'{tag} {lang} {i}: scheme translated')
                    if lang == 'sr' or i == 'cg-80':
                        await (await pg.query_selector('.card-ov')).screenshot(path=str(SHOTS / f'kako_{tag}_{lang}_{i}.png'))
            check(not errs, f'{tag} no JS errors {errs[:3]}')
            await ctx.close()
        await b.close()
    print('FAILS:', len(fails))
    sys.exit(1 if fails else 0)

asyncio.run(main())
