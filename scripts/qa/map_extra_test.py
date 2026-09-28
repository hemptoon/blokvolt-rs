# Map page, 28.09.2026 additions: our checked facts (dopune.json), the "Imam Teslu" switch, prices next to the pins,
# the exact place ("Gde tačno": address, coordinates to copy, DMS, Plus Code), EN/RU strings.
# /api/* is answered with empty data. Usage (server running, see cfserve.py): python3 scripts/qa/map_extra_test.py [shots-dir]
import asyncio, json, sys
from pathlib import Path
from playwright.async_api import async_playwright

SHOTS = Path(sys.argv[1] if len(sys.argv) > 1 else '/tmp/bv-shots')
SHOTS.mkdir(parents=True, exist_ok=True)
BASE = 'http://127.0.0.1:8787'
STYLE = {"version": 8, "sources": {}, "glyphs": "https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf",
         "layers": [{"id": "bg", "type": "background", "paint": {"background-color": "#e9ecef"}}]}
fails = []


def check(cond, what):
    print(('ok   ' if cond else 'FAIL ') + what)
    if not cond:
        fails.append(what)


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'])
        for w, h, tag in ((1440, 900, 'd'), (390, 844, 'm')):
            ctx = await b.new_context(viewport={'width': w, 'height': h}, permissions=['clipboard-read', 'clipboard-write'])
            pg = await ctx.new_page()
            errs = []
            pg.on('pageerror', lambda e: errs.append('JS ' + str(e)[:200]))
            pg.on('console', lambda m: errs.append(m.type + ' ' + m.text[:200]) if m.type == 'error' and 'openfreemap' not in m.text else None)
            await pg.route('https://tiles.openfreemap.org/styles/**', lambda r: r.fulfill(status=200, content_type='application/json', body=json.dumps(STYLE)))
            await pg.route('https://tiles.openfreemap.org/fonts/**', lambda r: r.fulfill(status=200, content_type='application/x-protobuf', body=b''))
            await pg.route('**/api/**', lambda r: r.fulfill(status=200, content_type='application/json',
                           body=json.dumps({"ok": True, "st": {}, "avg": None, "nr": 0, "n": 0, "items": [], "photos": []})))

            async def card(url, name):
                await pg.goto('about:blank')
                await pg.goto(BASE + url, wait_until='load')
                await pg.wait_for_timeout(1400)
                txt = await pg.evaluate("(document.querySelector('.ccard')||{}).innerText || ''")
                await pg.screenshot(path=str(SHOTS / f'x_{name}_{tag}.png'))
                return txt

            # Tesla Supercharger Beograd, no Tesla: "Samo za Tesla vozila", exact place
            await pg.goto(BASE + '/mapa/', wait_until='load')
            await pg.evaluate("localStorage.removeItem('bv:tesla')")
            t = await card('/mapa/?qa=1#ocm-150105', 'tesla_off')
            check('Tesla Supercharger Beograd' in t, f'{tag} tesla card title')
            check('Samo za Tesla vozila' in t and '0 RSD za Tesla vozila' in t, f'{tag} tesla price without switch')
            check('0–24' in t and 'Samo Tesla vozila' in t, f'{tag} tesla badges')
            check('Astrid Lindgren 23, 11231 Beograd' in t and '44.71253, 20.56020' in t, f'{tag} tesla address + coordinates')
            check('8GP2PH76+23' in t and '44°42′45.1″N 20°33′36.7″E' in t, f'{tag} tesla plus code + DMS')
            check('Tačka je sa spiska mreže.' in t, f'{tag} tesla point quality')
            check('Tesla — Beograd' in t, f'{tag} tesla own source label')
            f = {x['id']: x for x in await pg.evaluate('window.bvMapQa ? window.bvMapQa() : []')}
            check(f.get('ocm-150105', {}).get('k') == 'tesla' and f['ocm-150105']['p'] == 'T' and f['ocm-150105']['pl'] == '', f'{tag} tesla pin (no switch): {f.get("ocm-150105")}')
            check(f.get('osm-n6797205414', {}).get('pl') == '0 RSD' and f['osm-n6797205414']['k'] == 'free', f'{tag} IKEA pin: {f.get("osm-n6797205414")}')
            check(f.get('osm-w1451968119', {}).get('pl') == '56-60 RSD/kWh', f'{tag} OMV Metro pin: {f.get("osm-w1451968119")}')
            check(f.get('ocm-260781', {}).get('pl') == '79 RSD/kWh', f'{tag} Stari Banovci pin: {f.get("ocm-260781")}')
            ests = [x['pl'] for x in f.values() if x['pl'].startswith('~')]
            unk = sum(1 for x in f.values() if x['pl'] == '?')
            print(f'{tag} pins: {len(f)}; estimates {len(ests)} e.g. {ests[:6]}; unknown {unk}; free {sum(1 for x in f.values() if x["pl"] == "0 RSD")}')
            # the switch
            await pg.click('#mchips [data-f="tesla"]')
            await pg.wait_for_timeout(500)
            t = await pg.evaluate("(document.querySelector('.ccard')||{}).innerText || ''")
            check('0 RSD za Tesla vozila' in t and 'Samo za Tesla vozila' not in t, f'{tag} tesla price with switch')
            check(await pg.evaluate("localStorage.getItem('bv:tesla')") == '1', f'{tag} switch saved')
            f = {x['id']: x for x in await pg.evaluate('window.bvMapQa()')}
            check(f['ocm-150105']['k'] == 'free' and f['ocm-150105']['pl'] == '0 RSD', f'{tag} tesla pin with switch: {f["ocm-150105"]}')
            await pg.screenshot(path=str(SHOTS / f'x_tesla_on_{tag}.png'))
            # copy coordinates
            await pg.click('.ccard [data-copy]')
            await pg.wait_for_timeout(300)
            clip = await pg.evaluate('navigator.clipboard.readText()')
            lbl = await pg.inner_text('.ccard [data-copy]')
            check(clip == '44.71253, 20.56020' and 'Kopirano' in lbl, f'{tag} copy coordinates: {clip!r} {lbl!r}')
            # free filter with and without the switch
            await pg.goto('about:blank')
            await pg.goto(BASE + '/mapa/?f=free&qa=1', wait_until='load')
            await pg.wait_for_timeout(1200)
            n_on = await pg.inner_text('#mcount')
            f_on = {x['id'] for x in await pg.evaluate('window.bvMapQa ? window.bvMapQa() : []')}
            await pg.click('#mchips [data-f="tesla"]')
            await pg.wait_for_timeout(400)
            n_off = await pg.inner_text('#mcount')
            await pg.goto(BASE + '/mapa/?f=free&qa=1', wait_until='load')
            await pg.wait_for_timeout(1200)
            f_off = {x['id'] for x in await pg.evaluate('window.bvMapQa()')}
            check('ocm-150105' in f_on or not f_on, f'{tag} free filter with Tesla: {n_on}')
            check('ocm-150105' not in f_off and 'osm-n6797205414' in f_off, f'{tag} free filter without Tesla: {n_off} ({len(f_off)} pins)')
            # IKEA, OMV Metro, Stari Banovci, Obilićev venac, hub, Lidl
            t = await card('/mapa/#osm-n6797205414', 'ikea')
            check('IKEA Beograd' in t and 'Besplatno' in t and '10–21 (kartica na info pultu)' in t and 'Parking IKEA, red A9' in t, f'{tag} IKEA card')
            check('na sajtu vlasnika lokacije' in t and 'IKEA Srbija' in t, f'{tag} IKEA verification + operator')
            t = await card('/mapa/#osm-w1451968119', 'omv_metro')
            check('OMV Metro (Zemun park)' in t and '56–60 RSD/kWh' in t and 'Po računima sa ovog punjača' in t and 'probnom radu' in t, f'{tag} OMV Metro card')
            t = await card('/mapa/#ocm-260781', 'stari_banovci')
            check(t.startswith('Gazprom Stari Banovci') or '\nGazprom Stari Banovci' in t or 'Gazprom Stari Banovci' in t.split('\n')[0:3].__str__(), f'{tag} Stari Banovci title without network prefix')
            check('79 RSD/kWh' in t, f'{tag} Stari Banovci receipt price')
            t = await card('/mapa/#ocm-125797', 'obilicev')
            check('Obilićev venac 14–16' in t and '0–24' in t and 'Potvrđeno' in t, f'{tag} Obilićev venac card')
            t = await card('/mapa/#rm-4479035-2042305', 'hub')
            check('10 priključaka' in t, f'{tag} hub note')
            t = await card('/mapa/#cg-65', 'cg65')
            check('≈' in t and 'RSD po kWh ako auto puni sa' in t, f'{tag} per-minute estimate line (cg-65)')
            # English and Russian
            t = await card('/en/mapa/#ocm-150105', 'tesla_en')
            check('exact location' in t.lower() and 'tesla vehicles only' in t.lower(), f'{tag} EN card strings')
            t = await card('/ru/mapa/#osm-n6797205414', 'ikea_ru')
            check('где именно' in t.lower() and 'бесплатно' in t.lower(), f'{tag} RU card strings')
            check(not errs, f'{tag} no JS errors: {errs[:4]}')
            await ctx.close()
        await b.close()
    print('FAILED:', len(fails)) if fails else print('ALL OK')

asyncio.run(main())
