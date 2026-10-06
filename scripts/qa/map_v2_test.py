# Map page, 06.10.2026 additions: the network's price of every connector (Charge&GO app), own cable, hours with "open now",
# "Kako se puni ovde", "Moj auto" with the cost per km, "Najbliži punjač" (with a fixed location), the drivers' short
# answers and the "Izdvojeno" line. /api/* is answered with sample data and every POST is recorded.
# Usage (server running, see cfserve.py): python3 scripts/qa/map_v2_test.py [shots-dir]
import asyncio, json, re, sys
from pathlib import Path
from playwright.async_api import async_playwright

SHOTS = Path(sys.argv[1] if len(sys.argv) > 1 else '/tmp/bv-shots')
SHOTS.mkdir(parents=True, exist_ok=True)
BASE = 'http://127.0.0.1:8787'
STYLE = {"version": 8, "sources": {}, "glyphs": "https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf",
         "layers": [{"id": "bg", "type": "background", "paint": {"background-color": "#e9ecef"}}]}
NOVI_SAD = {'latitude': 45.2551, 'longitude': 19.8452}   # Bulevar oslobođenja, Novi Sad
fails = []


def check(cond, what):
    print(('ok   ' if cond else 'FAIL ') + what)
    if not cond:
        fails.append(what)


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'])
        for w, h, tag in ((1440, 900, 'd'), (390, 844, 'm')):
            ctx = await b.new_context(viewport={'width': w, 'height': h}, geolocation=NOVI_SAD, permissions=['geolocation'],
                                      is_mobile=tag == 'm', has_touch=tag == 'm')
            pg = await ctx.new_page()
            errs, posts = [], []
            pg.on('pageerror', lambda e: errs.append('JS ' + str(e)[:300]))
            pg.on('console', lambda m: errs.append(m.type + ' ' + m.text[:200]) if m.type == 'error' and 'openfreemap' not in m.text else None)
            await pg.route('https://tiles.openfreemap.org/styles/**', lambda r: r.fulfill(status=200, content_type='application/json', body=json.dumps(STYLE)))
            await pg.route('https://tiles.openfreemap.org/fonts/**', lambda r: r.fulfill(status=200, content_type='application/x-protobuf', body=b''))

            async def api(route):
                req = route.request
                if req.method == 'POST':
                    posts.append((req.url.split('/api/')[1], req.post_data))
                    return await route.fulfill(status=200, content_type='application/json', body=json.dumps({'ok': True, 'pending': False}))
                body = {"ok": True, "st": {}, "avg": None, "nr": 0, "n": 0, "items": [], "photos": [],
                        "facts": [{"f": "cab", "v": "att", "n": 3, "last": 1759700000}, {"f": "cab", "v": "own", "n": 1, "last": 1759700000},
                                  {"f": "why", "v": "busy", "n": 2, "last": 1759700000}]}
                await route.fulfill(status=200, content_type='application/json', body=json.dumps(body))
            await pg.route('**/api/**', api)

            async def card(url, name, wait=1400):
                await pg.goto('about:blank')
                await pg.goto(BASE + url, wait_until='load')
                await pg.wait_for_timeout(wait)
                txt = await pg.evaluate("(document.querySelector('.ccard')||{}).innerText || ''")
                await pg.screenshot(path=str(SHOTS / f'v2_{name}_{tag}.png'))
                return txt

            await pg.goto(BASE + '/mapa/', wait_until='load')
            await pg.evaluate("localStorage.removeItem('bv:car'); localStorage.removeItem('bv:tesla'); localStorage.removeItem('bv:nav')")

            # 1. the network's price of every connector, own cable, "Kako se puni ovde"
            t = await card('/mapa/?qa=1#ocm-260806', 'gazprom')
            check('58,33 RSD/min' in t and '16,67 RSD/min' in t and 'DC 50 kW' in t and 'AC 22 kW' in t, f'{tag} per-connector prices (Gazprom Sokolići)')
            check('Cena ovog punjača u aplikaciji mreže · 05.10.2026' in t, f'{tag} per-connector price source')
            check('Kako se puni ovde — Charge&GO' in t, f'{tag} how-to summary')
            await pg.click('.ccard details.kako summary')
            t = await pg.evaluate("document.querySelector('.ccard').innerText")
            check('1.000 RSD' in t and '2.000 RSD' in t and '20 %' in t, f'{tag} how-to facts (top-up 1.000, guest 2.000, 20 %)')
            check('Izaberite auto' in t, f'{tag} "choose a car" link without a car')
            check('Izdvojeno' in t and 'Kod kuće noću' in t, f'{tag} Izdvojeno line')
            href = await pg.get_attribute('.ccard a[data-evo]', 'href')
            check(href and 'utm_source=blokvolt' in href and 'proveri-svoju-garazu' in href and 'lang=' not in href, f'{tag} Evolako link: {href}')
            t = await card('/mapa/?qa=1#ocm-262055', 'hitauto')
            check('Ponesite svoj Tip 2 kabl' in t, f'{tag} own cable badge (HIT Auto)')
            check('kabl je' in t.lower() or 'Kabl: na punjaču' in t, f'{tag} drivers\' answers shown: cable')
            check('Mesto zauzeto ×2' in t, f'{tag} drivers\' answers shown: reasons')
            t = await card('/mapa/?qa=1#ocm-260785', 'borca')
            check('Ograničen pristup 01–05 h' in t and ('sada radi do 01:00' in t or 'sada zatvoreno, otvara u 05:00' in t), f'{tag} hours + open now (Stop Shop Borča)')
            t = await card('/mapa/?qa=1#rm-4479035-2042305', 'edrive')
            check('BEX Konjarnik' in t and '48 RSD/kWh' in t and '199 RSD' in t, f'{tag} eDrive own price')
            check('eDrive' in t and 'Kako se puni ovde — eDrive' in t, f'{tag} eDrive network + how-to')
            f = {x['id']: x for x in await pg.evaluate('window.bvMapQa()')}
            check(f['rm-4479035-2042305']['pl'] == '~56 RSD/kWh', f"{tag} eDrive pin: {f['rm-4479035-2042305']['pl']}")
            check(f['cg-80']['pl'].startswith('~') and f['cg-80']['pl'].endswith('RSD/kWh'), f"{tag} Super Vero NS pin: {f['cg-80']['pl']}")

            # 2. "Moj auto": Tesla Model 3 Long Range AWD (2019–2023)
            await pg.goto('about:blank')
            await pg.goto(BASE + '/mapa/?qa=1', wait_until='load')
            await pg.wait_for_timeout(1200)
            await pg.click('#mcar')
            await pg.wait_for_selector('.carp select[name=mk]')
            await pg.select_option('.carp select[name=mk]', 'Tesla')
            ids = await pg.evaluate("[...document.querySelectorAll('.carp select[name=id] option')].map(o => o.value).filter(Boolean)")
            m3 = next(i for i in ids if 'model-3-long-range-awd-2019' in i)
            await pg.select_option('.carp select[name=id]', m3)
            ph = await pg.get_attribute('.carp input[name=cons]', 'placeholder')
            check(ph == '15,5', f'{tag} consumption placeholder: {ph}')
            await pg.screenshot(path=str(SHOTS / f'v2_carpicker_{tag}.png'))
            await pg.click('.carp button[type=submit]')
            await pg.wait_for_timeout(500)
            car = json.loads(await pg.evaluate("localStorage.getItem('bv:car')") or 'null')
            check(car and car['id'] == m3 and car['cons'] is None, f'{tag} car saved: {car}')
            check(await pg.evaluate("localStorage.getItem('bv:tesla')") == '1', f'{tag} a Tesla switches "Imam Teslu" on')
            lbl = await pg.inner_text('[data-carlbl]')
            check('Tesla Model 3 Long Range AWD' in lbl, f'{tag} car button label: {lbl}')
            check(await pg.is_visible('#mchips [data-f="cheap"]') or tag == 'm', f'{tag} cheapest chip visible')
            lst = await pg.inner_text('#mlist')
            check('RSD/km' in lst, f'{tag} list shows RSD/km')
            f = {x['id']: x for x in await pg.evaluate('window.bvMapQa()')}
            check(f['cg-80']['pl'].endswith('RSD/km'), f"{tag} pin per km: {f['cg-80']['pl']}")
            co = await pg.evaluate("window.bvCostQa('cg-80')")
            # eDrive BEX Konjarnik above: 48 RSD/kWh + 199 RSD start over a typical 25 kWh session ≈ 56 RSD/kWh
            # Super Vero NS, DC 150 kW, 114,17 RSD/min: the car takes min(146, 0,88 × 150 = 132) = 132 kW → 51,9 RSD/kWh → × 15,5 / 100 / 0,96 ≈ 8,38 RSD/km
            check(co and abs(co['kw'] - 132) < 0.5 and abs(co['kwh'] - 51.9) < 0.3 and abs(co['km'] - 8.38) < 0.1, f'{tag} cost engine Super Vero NS: {co}')
            co = await pg.evaluate("window.bvCostQa('ocm-263893')")
            # Promenada AC 22 kW, 16,67 RSD/min: Model 3 takes 11 kW → 90,9 RSD/kWh → × 15,5 / 100 / 0,92 ≈ 15,3 RSD/km
            check(co and abs(co['kw'] - 11) < 0.1 and abs(co['km'] - 15.3) < 0.15, f'{tag} cost engine Promenada AC: {co}')
            t = await card('/mapa/?qa=1#cg-80', 'cost_supervero')
            check('Za vaš Tesla Model 3 Long Range AWD: ≈ 8,4 RSD/km' in t, f'{tag} cost line in card')
            check('100 km ≈ 838 RSD' in t and 'auto ovde prima ≈ 132 kW' in t, f'{tag} cost details')
            check('Benzin ≈ 13 RSD/km' in t and 'kod kuće noću ≈ 0,7–1,0 RSD/km' in t, f'{tag} comparison line')
            check('Kod kuće noću ≈ 0,7–1,0 RSD/km' in t, f'{tag} Izdvojeno per km')
            # cheapest first
            if tag == 'd':
                await pg.click('#mchips [data-f="cheap"]')
                await pg.wait_for_timeout(300)
                cnt = await pg.inner_text('#mcount')
                check('najjeftinije za vaš auto prvo' in cnt, f'{tag} cheapest sort: {cnt}')
                first = await pg.evaluate("[...document.querySelectorAll('#mlist .st .pr')].slice(0, 3).map(e => e.innerText)")
                check(all(('Besplatno' in x) for x in first), f'{tag} free first: {first}')
                await pg.click('#mchips [data-f="cheap"]')
            # a Nissan Leaf (CHAdeMO) cannot use a CCS-only charger
            leaf = await pg.evaluate("fetch(JSON.parse(document.getElementById('map-cfg').textContent).cars).then(r => r.json()).then(j => j.cars.find(c => /leaf-40/.test(c.id)).id)")
            await pg.evaluate(f"localStorage.setItem('bv:car', JSON.stringify({{id: '{leaf}', cons: null, cab: false, opt: false}}))")
            t = await card('/mapa/?qa=1#cg-80', 'leaf_ccs')
            check('ne može da puni na DC priključku' in t, f'{tag} CHAdeMO car at a CCS charger')

            # 3. "Najbliži punjač" with a fixed location in Novi Sad (no car)
            await pg.evaluate("localStorage.removeItem('bv:car'); localStorage.removeItem('bv:tesla')")
            await pg.goto('about:blank')
            await pg.goto(BASE + '/mapa/?qa=1', wait_until='load')
            await pg.wait_for_timeout(1200)
            btn = '#mnear' if tag == 'd' else '.near-m'
            check(await pg.is_visible(btn), f'{tag} nearest button visible ({btn})')
            await pg.click(btn)
            await pg.wait_for_selector('.nrp .nrl')
            await pg.wait_for_timeout(500)
            t = await pg.inner_text('.nrp')
            rows = await pg.evaluate("[...document.querySelectorAll('.nrp .nr')].length")
            check(rows == 3, f'{tag} three nearest rows: {rows}')
            go = await pg.get_attribute('.nrp .nr.first a.nr-go', 'href')
            check(go and ('dir_action=navigate' in go or 'maps.apple.com' in go), f'{tag} first route link: {go}')
            qa = await pg.evaluate(f"window.bvNearQa({NOVI_SAD['latitude']}, {NOVI_SAD['longitude']})")
            names = await pg.evaluate("[...document.querySelectorAll('.nrp .nr-nm > b')].map(e => e.innerText)")
            check([x['t'] for x in qa] == names, f'{tag} panel = bvNearQa: {names}')
            check(all(m1 <= m2 for m1, m2 in zip([x['m'] for x in qa], [x['m'] for x in qa][1:])), f'{tag} sorted by distance: {[x["m"] for x in qa]}')
            check('Lokacija ostaje na vašem uređaju.' in t, f'{tag} privacy line')
            await pg.screenshot(path=str(SHOTS / f'v2_nearest_{tag}.png'))
            # fast only
            await pg.click('.nrp [data-nr="fast"]')
            await pg.wait_for_timeout(400)
            qa2 = await pg.evaluate(f"window.bvNearQa({NOVI_SAD['latitude']}, {NOVI_SAD['longitude']})")
            dcs = await pg.evaluate("ids => ids.map(id => window.bvMapQa().find(f => f.id === id)).map(f => f && f.k)", [x['id'] for x in qa2])
            check(all(k in ('dc', 'free') for k in dcs), f'{tag} fast only: {dcs}')
            # change the navigation app: remembered
            await pg.click('.nrp [data-nr="apps"]')
            await pg.click('.nrp [data-app="waze"]')
            await pg.wait_for_timeout(200)
            go = await pg.get_attribute('.nrp .nr.first a.nr-go', 'href')
            check('waze.com' in go and await pg.evaluate("localStorage.getItem('bv:nav')") == 'waze', f'{tag} navigation app remembered: {go}')
            # a row opens the card with "back"
            await pg.click('.nrp .nr.first .nr-main')
            await pg.wait_for_timeout(500)
            check(await pg.is_visible('.ccard .nr-back'), f'{tag} card from the panel has "back"')
            nav = await pg.get_attribute('.ccard .acts a[data-nav]', 'href')
            check('waze.com' in nav, f'{tag} card uses the chosen app first: {nav}')
            await pg.click('.ccard .nr-back')
            await pg.wait_for_timeout(300)
            check(await pg.is_visible('.nrp .nrl'), f'{tag} back to the panel')
            await pg.keyboard.press('Escape')
            await pg.wait_for_timeout(200)
            check(not await pg.is_visible('.nrp'), f'{tag} Escape closes the panel')
            # ?najblizi=brzi with the permission granted opens it at once
            await pg.goto('about:blank')
            await pg.goto(BASE + '/mapa/?najblizi=brzi&qa=1', wait_until='load')
            await pg.wait_for_selector('.nrp .nrl', timeout=8000)
            fast = await pg.get_attribute('.nrp [data-nr="fast"]', 'aria-pressed')
            check(fast == 'true', f'{tag} ?najblizi=brzi: fast on')

            # 4. drivers' short answers after a report
            await pg.evaluate("localStorage.removeItem('bv:nav')")
            t = await card('/mapa/?qa=1#ocm-262055', 'report')
            await pg.click('.rv [data-ci="problem"]')
            check(await pg.is_visible('.rv-why'), f'{tag} reasons shown for "Radi, uz problem"')
            await pg.click('.rv-why [data-why="cable"]')
            await pg.wait_for_timeout(3000)   # the worker refuses reports sent faster than 2,5 s
            await pg.click('.rv-form [type=submit]')
            await pg.wait_for_timeout(500)
            sent = [json.loads(d) for u, d in posts if u.endswith('/prijava')]
            check(sent and sent[-1].get('why') == 'cable' and sent[-1]['s'] == 'problem', f'{tag} reason sent: {sent[-1] if sent else None}')
            check(await pg.is_visible('.rv-facts'), f'{tag} three short questions after the report')
            await pg.click('.rv-facts [data-fact="cab"] [data-v="own"]')
            await pg.wait_for_timeout(400)
            fp = [(u, json.loads(d)) for u, d in posts if u.endswith('/podatak')]
            check(fp and fp[-1][1]['f'] == 'cab' and fp[-1][1]['v'] == 'own' and 'ocm-262055' in fp[-1][0], f'{tag} answer sent: {fp[-1] if fp else None}')
            await pg.screenshot(path=str(SHOTS / f'v2_facts_{tag}.png'))

            # 5. EN and RU
            for lang, needle in (('en', 'How to charge here'), ('ru', 'Как здесь заряжаться')):
                t = await card(f'/{lang}/mapa/?qa=1#ocm-260806', 'lang_' + lang)
                check(needle in t, f'{tag} {lang} how-to title')
                href = await pg.get_attribute('.ccard a[data-evo]', 'href')
                check(href and f'lang={lang}' in href, f'{tag} {lang} Evolako link has the language: {href}')
            # 6. overflow, errors
            await pg.goto('about:blank')
            await pg.goto(BASE + '/mapa/?qa=1', wait_until='load')
            await pg.wait_for_timeout(1000)
            sw = await pg.evaluate('[document.documentElement.scrollWidth, window.innerWidth]')
            check(sw[0] <= sw[1], f'{tag} no horizontal scroll {sw}')
            check(not [e for e in errs if 'api/zamka' not in e], f'{tag} no JS errors: {errs[:3]}')
            await ctx.close()
        await b.close()
    print('ALL OK' if not fails else f'FAILS: {len(fails)}')
    sys.exit(1 if fails else 0)

asyncio.run(main())
