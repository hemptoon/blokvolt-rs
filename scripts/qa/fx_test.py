# Display currency (RSD / EUR / USD) in the browser — docs/RUNBOOK.md 3.29.
# RSD by default with the pages exactly as before; EUR / USD by the switcher, ?cur= and after a reload; what converts
# (price index, network and firm prices, data tables, calculators, the map card, list and pins) and what never does
# (guides, news, media kit, legal pages, the newsletter, calculator inputs); the footnote in SR/EN/RU; the fallback rate
# when /api/kurs does not answer; the switcher in the burger menu on a phone; no horizontal scroll; screenshots; map v2
# (connectors, Moj auto, Najbliži punjač) in SR/EN/RU × RSD/EUR/USD; the visit counter of bv.js (one request per page
# view, none for a currency switch).
# Usage (server running, see cfserve.py):
#   python3 scripts/qa/fx_test.py [shots-dir] [--before http://127.0.0.1:8790]
# --before: a server with a build of the same content without this feature (e.g. main); the main text of key pages in
# RSD must be identical there and here. /api/* is not served by cfserve: /api/kurs answers 404, the pages must fall back
# to the constants of fx.js silently (the date in the footnote is the constants' date).
import asyncio, json, re, sys
from pathlib import Path
from playwright.async_api import async_playwright

args = [a for a in sys.argv[1:]]
BEFORE = None
if '--before' in args:
    i = args.index('--before')
    BEFORE = args[i + 1]
    del args[i:i + 2]
SHOTS = Path(args[0] if args else '/tmp/bv-fx-shots')
SHOTS.mkdir(parents=True, exist_ok=True)
BASE = 'http://127.0.0.1:8787'
STYLE = {"version": 8, "sources": {}, "glyphs": "https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf",
         "layers": [{"id": "bg", "type": "background", "paint": {"background-color": "#e9ecef"}}]}
FALLBACK_DATE = '05.10.2026'
NOTES = {
    'sr': 'Iznosi u evrima i dolarima su informativni, po srednjem kursu NBS na 05.10.2026. Na punjačima i u računima cene su u dinarima.',
    'en': 'Amounts in euros and dollars are for reference, at the National Bank of Serbia middle rate on 05.10.2026. Chargers and bills charge in dinars.',
    'ru': 'Суммы в евро и долларах — справочные, по среднему курсу НБС на 05.10.2026. На зарядках и в счетах цены в динарах.',
}
# pages whose text must not change at all with RSD (and with EUR for the "never" group)
KEY_PAGES = ['/javno-punjenje/', '/javno-punjenje/chargego/', '/firme/stasanet/', '/cena-punjaca-za-elektricni-auto',
             '/podaci/wallbox-modeli/', '/podaci/tarife-eps/', '/podaci/registracija-i-porezi/', '/alati/kalkulator-troskova/',
             '/alati/racun-u-zgradi/', '/ko-placa-struju-za-punjenje', '/en/javno-punjenje/', '/ru/firme/', '/ru/alati/kalkulator-troskova/']
NEVER = ['/ko-placa-struju-za-punjenje', '/javno-punjenje/kako-jeftinije-puniti/', '/za-firme/oglasavanje/', '/politika-privatnosti',
         '/pregled/', '/vesti/', '/metodologija/', '/en/za-firme/oglasavanje/', '/ru/ko-placa-struju-za-punjenje']
fails, oks = 0, 0


def check(cond, what, detail=None):
    global fails, oks
    if cond:
        oks += 1
        print('ok   ' + what)
    else:
        fails += 1
        print('FAIL ' + what + (' — ' + json.dumps(detail, ensure_ascii=False)[:500] if detail is not None else ''))


MAIN_TEXT = "(() => { const m = document.querySelector('main') || document.body; return m.innerText.replace(/\\s+/g, ' ').trim(); })()"


async def new_ctx(b, w=1440, h=900, cur=None, mobile=False):
    ctx = await b.new_context(viewport={'width': w, 'height': h}, **({'is_mobile': True, 'has_touch': True} if mobile else {}))
    if cur:
        await ctx.add_init_script(f"try {{ localStorage.setItem('bv:cur', '{cur}'); }} catch (e) {{}}")
    await ctx.route('https://tiles.openfreemap.org/styles/**', lambda r: r.fulfill(status=200, content_type='application/json', body=json.dumps(STYLE)))
    await ctx.route('https://tiles.openfreemap.org/fonts/**', lambda r: r.fulfill(status=200, content_type='application/x-protobuf', body=b''))

    async def api(route):          # /api/kurs is left to the server (cfserve: 404); the rest gets an empty answer
        if route.request.url.split('?')[0].endswith('/api/kurs'):
            await route.continue_()
        else:
            await route.fulfill(status=200, content_type='application/json', body='{"ok":true,"st":{},"items":[],"photos":[]}')
    await ctx.route('**/api/**', api)
    return ctx


def watch(pg):
    errs = []
    pg.on('pageerror', lambda e: errs.append('JS ' + str(e)[:200]))
    pg.on('console', lambda m: errs.append('CON ' + m.text[:200]) if m.type == 'error' and not any(
        x in m.text for x in ('openfreemap', '/api/', '404', 'Failed to load resource')) else None)
    return errs


async def go(pg, path, wait=400):
    await pg.goto(BASE + path, wait_until='load')
    await pg.wait_for_timeout(wait)


async def shot(pg, name, selector=None, full=False):
    p = SHOTS / name
    if selector:
        el = await pg.query_selector(selector)
        if el is None:
            print('     (no ' + selector + ' for ' + name + ')')
            return
        await pg.add_style_tag(content='.hd{position:static!important}')     # the sticky header would cover the element
        await el.scroll_into_view_if_needed()
        await el.screenshot(path=str(p))
    else:
        await pg.screenshot(path=str(p), full_page=full)


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'])

        # ------------------------------------------------------------------ 1. RSD by default: nothing changes
        print('— RSD by default')
        ctx = await new_ctx(b)
        pg = await ctx.new_page()
        errs = watch(pg)
        rsd_text = {}
        for path in KEY_PAGES:
            await go(pg, path)
            st = await pg.evaluate("({cur: window.bvFx && bvFx.get(), conv: document.querySelectorAll('.fx-p,.fx-s').length, note: !!document.querySelector('.fx-note:not([hidden])')})")
            rsd_text[path] = await pg.evaluate(MAIN_TEXT)
            check(st['cur'] == 'RSD' and st['conv'] == 0 and not st['note'], f'{path}: RSD, nothing converted, no footnote', st)
        check(not errs, 'no JS errors with RSD', errs[:5])
        sel = await pg.evaluate("[...document.querySelectorAll('.fx-sel')].map(s => [s.value, [...s.options].map(o => o.value).join(','), s.getAttribute('aria-label'), s.getAttribute('translate')])")
        check(sel and sel[0] == ['RSD', 'RSD,EUR,USD', 'Валюта', 'no'], 'switcher: RSD · EUR · USD, label in the page language, translate=no', sel)
        await ctx.close()
        if BEFORE:
            ctx = await new_ctx(b)
            pg = await ctx.new_page()
            for path in KEY_PAGES:
                await pg.goto(BEFORE + path, wait_until='load')
                await pg.wait_for_timeout(300)
                t0 = await pg.evaluate(MAIN_TEXT)
                same = t0 == rsd_text[path]
                if not same:
                    i = next((k for k in range(min(len(t0), len(rsd_text[path]))) if t0[k] != rsd_text[path][k]), 0)
                    detail = [t0[max(0, i - 60):i + 60], rsd_text[path][max(0, i - 60):i + 60]]
                else:
                    detail = None
                check(same, f'{path}: text with RSD identical to the build before ({len(t0)} chars)', detail)
            await ctx.close()

        # ------------------------------------------------------------------ 2. EUR by the switcher, kept after a reload
        print('— EUR by the switcher')
        ctx = await new_ctx(b)
        pg = await ctx.new_page()
        errs = watch(pg)
        await go(pg, '/javno-punjenje/')
        await pg.evaluate("window.__ev = []; window.bvTrack = (n, p) => { window.__ev.push([n, p]); }; 0")
        await pg.select_option('.hd-cur .fx-sel', 'EUR')
        await pg.wait_for_timeout(200)
        r = await pg.evaluate("""({cur: bvFx.get(), ls: localStorage.getItem('bv:cur'), ev: window.__ev,
            card: [...document.querySelectorAll('.pl li b')].map(x => x.innerText.replace(/\\s+/g, ' ')).slice(0, 3),
            stat: document.querySelector('.stat .fx-1') && document.querySelector('.stat .fx-1').innerText.replace(/\\s+/g, ' '),
            note: document.querySelector('.fx-note') && document.querySelector('.fx-note').textContent,
            noteBeforeUpd: !!(document.querySelector('.fx-note') && document.querySelector('.fx-note').nextElementSibling && document.querySelector('.fx-note').nextElementSibling.matches('p.upd'))})""")
        check(r['cur'] == 'EUR' and r['ls'] == 'EUR', 'switcher sets EUR and keeps it in localStorage bv:cur', r)
        check(r['ev'] == [['currency_changed', {'from': 'RSD', 'to': 'EUR', 'surface': 'site'}]], 'event currency_changed {from, to, surface} through bvTrack', r['ev'])
        check(all(re.match(r'^≈ [\d.,–]+ €/min [\d.,–]+ RSD/min$', c) for c in r['card']), 'price cards: ≈ € first, RSD second', r['card'])
        check(r['stat'] and re.match(r'^≈ 0,\d\d–0,\d\d € 43–79 RSD$', r['stat']), 'stat 43–79 RSD → ≈ 0,37–0,67 € + RSD', r['stat'])
        check(r['note'] == NOTES['sr'], 'footnote (SR) with the date of the constants: /api/kurs not served → fallback, silently', r['note'])
        await pg.click('details summary >> text=Sve zabeležene cene')
        await pg.wait_for_timeout(200)
        cells = await pg.evaluate("[...document.querySelectorAll('td[data-label=\"Cena\"] b')].slice(0, 2).map(x => x.innerText.replace(/\\s+/g, ' '))")
        kwh = await pg.evaluate("[...document.querySelectorAll('td[data-label=\"≈ po kWh\"]')].slice(0, 1).map(x => x.innerText.replace(/\\s+/g, ' '))")
        check(cells and all(c.startswith('≈ ') and 'RSD/min' in c and '€/min' in c for c in cells), 'price index table: ≈ €/min first, RSD/min second', cells)
        check(kwh and kwh[0].startswith('≈ ') and '€' in kwh[0] and 'RSD pri' in kwh[0], 'price index ≈ per kWh column converted', kwh)
        await shot(pg, 'cene_eur_1440.png', '.pcards')
        await shot(pg, 'indeks_eur_1440.png', 'details.sec .tw, .tw.stack')
        await pg.reload(wait_until='load')
        await pg.wait_for_timeout(300)
        check(await pg.evaluate("bvFx.get() === 'EUR' && document.querySelector('.hd-cur .fx-sel').value === 'EUR' && document.querySelectorAll('.fx-p').length > 20"),
              'EUR survives a reload')
        # network page, firm prices, data tables, calculators
        await go(pg, '/javno-punjenje/chargego/')
        r = await pg.evaluate("[...document.querySelectorAll('td[data-label=\"Cena\"] b')].slice(0, 3).map(x => x.innerText.replace(/\\s+/g, ' '))")
        check(r and r[0].startswith('≈ 0,14 €/min') and '16,67 RSD/min' in r[0] and '≈ 8,51 €/sat' in r[0], 'network page: price table converted (both sums of a cell)', r)
        fact = await pg.evaluate("document.querySelector('.fact.wide b').innerText.replace(/\\s+/g, ' ')")
        check('≈ 0,14–1,08 €/min · 16,67–126,67 RSD/min' in fact, 'network page: price fact (range)', fact)
        await shot(pg, 'mreza_eur_1440.png', 'main .wrap.main')
        await go(pg, '/cena-punjaca-za-elektricni-auto')
        r = await pg.evaluate("[...document.querySelectorAll('.row .val')].slice(0, 3).map(x => x.innerText.replace(/\\s+/g, ' '))")
        check(r and all(re.match(r'^≈ [\d.]+ € [\d.,]+ RSD', x) for x in r if 'RSD' in x) and any('€ + PDV' in x for x in r),
              'charger prices (firm list): ≈ € first, RSD second; a price published in euros stays as published', r)
        await shot(pg, 'cena_punjaca_eur_1440.png', 'main .wrap.main')
        await go(pg, '/firme/stasanet/')
        fact = await pg.evaluate("document.querySelector('.fact.wide b').innerText.replace(/\\s+/g, ' ')")
        check(fact.startswith('11 kW: ≈ 809 € · 95.000 RSD'), 'firm page: price fact', fact)
        await go(pg, '/podaci/wallbox-modeli/')
        r = await pg.evaluate("[...document.querySelectorAll('td [data-rsd]')].slice(0, 2).map(x => x.innerText.replace(/\\s+/g, ' '))")
        check(r and all(re.match(r'^≈ \d+ € [\d.,]+ RSD$', x) for x in r), 'wallbox model table converted', r)
        await shot(pg, 'wallbox_eur_1440.png', 'main table')
        await go(pg, '/podaci/tarife-eps/')
        r = await pg.evaluate("[...document.querySelectorAll('td [data-rsd]')].slice(0, 2).map(x => x.innerText.replace(/\\s+/g, ' '))")
        check(r == ['≈ 0,035 € 4,15 RSD', '≈ 0,11 € 13,45 RSD'], 'EPS tariffs: rates with 3 decimals under 0,10', r)
        await go(pg, '/alati/kalkulator-troskova/')
        r = await pg.evaluate("""({ev: document.getElementById('o-ev').innerText.replace(/\\s+/g, ' '), save: document.getElementById('o-save').innerText.replace(/\\s+/g, ' '),
            ev100: document.getElementById('o-ev100').parentNode.innerText.replace(/\\s+/g, ' '),
            labels: [...document.querySelectorAll('#kalkulator label')].map(l => l.innerText).filter(t => /RSD/.test(t)),
            pub: document.getElementById('c-pub').value, chips: [...document.querySelectorAll('.calc-chips .chip')].map(c => c.innerText)})""")
        check(re.match(r'^≈ [\d.,]+ € [\d.]+ RSD$', r['ev']) and re.match(r'^≈ −?[\d.,]+ € mesečno [−\d.]+ RSD mesečno$', r['save']), 'calculator results: ≈ € first, RSD second', r)
        check('€' in r['ev100'] and 'na 100 km' in r['ev100'], 'calculator: per 100 km converted', r['ev100'])
        check(len(r['labels']) >= 4 and re.match(r'^\d+$', r['pub']) and all('RSD/kWh' in c and '€' not in c for c in r['chips']), 'calculator inputs and presets stay in RSD', r)
        await pg.fill('#c-km', '2000')
        await pg.wait_for_timeout(250)
        ev2 = await pg.evaluate("document.getElementById('o-ev').innerText.replace(/\\s+/g, ' ')")
        check(ev2 != r['ev'] and ev2.startswith('≈ '), 'calculator: a new input repaints the converted result', [r['ev'], ev2])
        await pg.evaluate("bvFx.set('RSD')")
        rsd_after = await pg.evaluate("document.getElementById('o-ev').innerHTML")
        first_rsd = r['ev'].split(' € ')[-1]
        check(re.match(r'^[\d.]+ RSD$', rsd_after) and rsd_after != first_rsd, 'calculator: back to RSD shows the new result, not the first one', [rsd_after, first_rsd])
        await pg.evaluate("bvFx.set('EUR')")
        await pg.fill('#c-km', '1250')
        await pg.wait_for_timeout(250)
        await shot(pg, 'kalkulator_eur_1440.png', 'form.calc')
        await go(pg, '/alati/racun-u-zgradi/')
        r = await pg.evaluate("[...document.querySelectorAll('.res [data-rsd]')].map(x => x.innerText.replace(/\\s+/g, ' '))")
        check(len(r) >= 7 and all('€' in x and 'RSD' in x for x in r), 'building calculator results converted', r)
        check(not errs, 'no JS errors with EUR', errs[:5])
        await ctx.close()

        # ------------------------------------------------------------------ 3. never converted
        print('— never converted')
        ctx = await new_ctx(b, cur='EUR')
        pg = await ctx.new_page()
        for path in NEVER:
            await go(pg, path, 300)
            r = await pg.evaluate("({conv: document.querySelectorAll('.fx-p').length, note: !!document.querySelector('.fx-note:not([hidden])'), sw: document.querySelectorAll('.fx-sel').length})")
            t = await pg.evaluate(MAIN_TEXT)
            check(r['conv'] == 0 and not r['note'] and r['sw'] >= 1, f'{path}: EUR chosen, nothing converted, no footnote', r)
            if path in rsd_text:
                check(t == rsd_text[path], f'{path}: text identical to RSD')
        await ctx.close()

        # ------------------------------------------------------------------ 4. ?cur=usd, EN and RU footnotes
        print('— ?cur=usd, languages')
        ctx = await new_ctx(b)
        pg = await ctx.new_page()
        await go(pg, '/javno-punjenje/?cur=usd')
        r = await pg.evaluate("({cur: bvFx.get(), ls: localStorage.getItem('bv:cur'), first: document.querySelector('.pl li b').innerText.replace(/\\s+/g, ' ')})")
        check(r['cur'] == 'USD' and r['ls'] == 'USD' and r['first'].startswith('≈ 0,16 $/min'), '?cur=usd sets and keeps USD', r)
        await go(pg, '/javno-punjenje/?cur=xyz')
        check(await pg.evaluate("bvFx.get()") == 'USD', '?cur=xyz is ignored')
        await go(pg, '/javno-punjenje/?cur=eur')
        for lang in ('en', 'ru'):
            await go(pg, f'/{lang}/javno-punjenje/chargego/')
            r = await pg.evaluate("({note: (document.querySelector('.fx-note') || {}).textContent, cell: document.querySelector('td[data-label] b [data-rsd]').innerText.replace(/\\s+/g, ' '), title: document.querySelector('td[data-label] b [data-rsd]').title.replace(/\\s+/g, ' ')})")
            check(r['note'] == NOTES[lang], f'{lang}: footnote in {lang.upper()}', r['note'])
            check(r['cell'].startswith('≈ 0,14 €/') and 'RSD/' in r['cell'], f'{lang}: converted, Serbian number format', r['cell'])
            check(r['title'].startswith({'en': 'Converted at the NBS rate on 05.10.2026.', 'ru': 'Пересчитано по курсу НБС на 05.10.2026.'}[lang]), f'{lang}: tooltip in {lang.upper()}', r['title'])
            await shot(pg, f'{lang}_mreza_eur_1440.png', 'main .wrap.main')
        await go(pg, '/ru/javno-punjenje/chargego/')
        await pg.evaluate("document.querySelector('.fx-note').scrollIntoView({block: 'center'})")
        await pg.wait_for_timeout(150)
        await pg.screenshot(path=str(SHOTS / 'ru_napomena_1440.png'))
        await ctx.close()

        # ------------------------------------------------------------------ 5. the map: card full, list and pins converted
        print('— the map')
        for w, h, tag, mob in ((1440, 900, '1440', False), (390, 844, '390', True)):
            ctx = await new_ctx(b, w, h, cur='EUR', mobile=mob)
            pg = await ctx.new_page()
            errs = watch(pg)
            await go(pg, '/mapa/?qa=1', 1500)
            pins = await pg.evaluate("window.bvMapQa ? bvMapQa().map(f => [f.id, f.pl]).filter(x => x[1]) : []")
            conv = [x for x in pins if 'EUR' in x[1]]
            rsd = [x for x in pins if 'RSD' in x[1]]
            check(len(conv) > 20 and not rsd and all(re.match(r'^(~?[\d,]+(-[\d,]+)? EUR(/kWh)?|\?)$', x[1]) for x in pins),
                  f'{tag}: pin labels converted, ASCII ({len(conv)})', pins[:6])
            sid = next((x[0] for x in conv if x[1].startswith('~')), None)
            await pg.goto('about:blank')
            await go(pg, f'/mapa/#{sid}', 1500)
            card = await pg.evaluate("(() => { const p = document.querySelector('.ccard .price'); return p ? p.innerText.replace(/\\s+/g, ' ') : null; })()")
            check(card and re.match(r'^≈ [\d,]+ €/min [\d,]+ RSD/min$', card), f'{tag}: station card price ≈ € first, RSD second', card)
            lst = await pg.evaluate("[...document.querySelectorAll('.st .pr .fxw')].slice(0, 3).map(x => [x.innerText.replace(/\\s+/g, ' '), x.title])")
            check(lst and all(x[0].startswith('≈ ') and '€' in x[0] and 'RSD' not in x[0] and 'RSD' in x[1] for x in lst), f'{tag}: list prices converted only (RSD in the tooltip)', lst)
            await shot(pg, f'mapa_kartica_eur_{tag}.png', '#mcard .ccard' if tag == '1440' else None)
            if tag == '1440':
                await shot(pg, 'mapa_lista_eur_1440.png', '.map-side')
            await pg.evaluate("bvFx.set('RSD')")
            await pg.wait_for_timeout(200)
            back = await pg.evaluate("(() => { const p = document.querySelector('.ccard .price'); return p ? p.innerText : null; })()")
            check(back and re.match(r'^[\d,]+ RSD/min$', back), f'{tag}: back to RSD: card shows RSD only', back)
            check(not errs, f'{tag}: no JS errors on the map', errs[:5])
            await ctx.close()

        # ------------------------------------------------------------------ 5b. map v2: connectors, "Moj auto", "Najbliži punjač"
        # SR/EN/RU × RSD/EUR/USD. With EUR/USD the card minus the euro/dollar parts must read exactly as with RSD (same
        # rounding, "≈" and ranges: nothing converted twice, nothing lost); pins, list and the nearest panel converted only.
        print('— map v2 × languages × currencies')
        km_u = {'sr': '/km', 'en': '/km', 'ru': '/км'}
        min_u = {'sr': '/min', 'en': '/min', 'ru': '/мин'}
        sym = {'EUR': '€', 'USD': '$'}
        rsd_only = """(() => { const c = document.querySelector('.ccard'); if (!c) return null; const k = c.cloneNode(true);
            k.querySelectorAll('.fx-p, .fx-sep').forEach(e => e.remove()); document.body.appendChild(k); const t = k.innerText.replace(/\\s+/g, ' ').trim(); k.remove(); return t; })()"""
        card_txt = "(document.querySelector('.ccard') || {innerText: ''}).innerText.replace(/\\s+/g, ' ').trim()"
        for lang in ('sr', 'en', 'ru'):
            pre = '' if lang == 'sr' else '/' + lang
            ctx = await new_ctx(b)
            await ctx.grant_permissions(['geolocation'])
            await ctx.set_geolocation({'latitude': 45.2551, 'longitude': 19.8452})
            pg = await ctx.new_page()
            errs = watch(pg)
            await go(pg, pre + '/mapa/?qa=1', 1200)
            m3 = await pg.evaluate("fetch(JSON.parse(document.getElementById('map-cfg').textContent).cars).then(r => r.json()).then(j => j.cars.find(c => /model-3-long-range-awd-2019/.test(c.id)).id)")
            base = {}
            for cur in ('RSD', 'EUR', 'USD'):
                tag = f'{lang} {cur}'
                await pg.evaluate(f"localStorage.setItem('bv:cur', '{cur}'); localStorage.removeItem('bv:car')")
                # every connector's price in the network's app
                await pg.goto('about:blank')
                await go(pg, pre + '/mapa/?qa=1#ocm-260806', 1400)
                pl = await pg.evaluate("[...document.querySelectorAll('.ccard ul.plines li b')].map(x => x.innerText.replace(/\\s+/g, ' ').trim())")
                if cur == 'RSD':
                    ok = len(pl) == 2 and all(re.match(r'^[\d,.]+ RSD' + min_u[lang] + '$', x) for x in pl)
                else:
                    ok = len(pl) == 2 and all(re.match(r'^≈ [\d,]+ ' + re.escape(sym[cur] + min_u[lang]) + r' · [\d,.]+ RSD' + min_u[lang] + '$', x) for x in pl)
                check(ok, f'map {tag}: every connector\'s price (Gazprom Sokolići)', pl)
                t_plain = await pg.evaluate(rsd_only if cur != 'RSD' else card_txt)
                if cur == 'RSD':
                    base['gz'] = t_plain
                else:
                    check(t_plain == base['gz'], f'map {tag}: connector card minus {sym[cur]} reads exactly as with RSD', [t_plain[:300], base['gz'][:300]])
                # "Moj auto": per km in the card, list and pins
                await pg.evaluate(f"localStorage.setItem('bv:car', JSON.stringify({{id: '{m3}', cons: null, cab: false, opt: false}}))")
                for sid in ('cg-80', 'rm-4479035-2042305', 'ocm-263893'):
                    await pg.goto('about:blank')
                    await go(pg, pre + f'/mapa/?qa=1#{sid}', 1400)
                    full = await pg.evaluate(card_txt)
                    cost = await pg.evaluate("(document.querySelector('.ccard .cost b') || {innerText: ''}).innerText.replace(/\\s+/g, ' ').trim()")
                    t_plain = await pg.evaluate(rsd_only if cur != 'RSD' else card_txt)
                    bad = [x for x in ('NaN', 'undefined', '≈ ≈', '€ €', '$ $', 'RSD RSD', '€ · €', '$ · $') if x in full]
                    check(not bad, f'map {tag} {sid}: no NaN / doubled signs', bad)
                    if cur == 'RSD':
                        base[sid] = t_plain
                        check(re.search(r'≈ [\d,.]+ RSD' + re.escape(km_u[lang]) + '$', cost) is not None and 'fx-p' not in await pg.evaluate("document.querySelector('.ccard').innerHTML"),
                              f'map {tag} {sid}: per km in RSD only', cost)
                    else:
                        n = await pg.evaluate("document.querySelectorAll('.ccard .fx-p').length")
                        check(re.search(r'≈ [\d,]+ ' + re.escape(sym[cur] + km_u[lang]) + r' · ≈ [\d,.]+ RSD' + re.escape(km_u[lang]) + '$', cost) is not None and n >= 6,
                              f'map {tag} {sid}: per km ≈ {sym[cur]} first, RSD after ({n} converted)', cost)
                        check(t_plain == base[sid], f'map {tag} {sid}: card minus {sym[cur]} reads exactly as with RSD', [t_plain[:400], base[sid][:400]])
                    if sid == 'ocm-263893':
                        # Promenada AC 22 kW: ≈ 15 RSD/km, 100 km ≈ 1.530 RSD — "1,530" on /en/, "1 530" on /ru/: thousands, not 1,53
                        h100 = await pg.evaluate("(document.querySelector('.ccard .cost small') || {innerText: ''}).innerText.replace(/\\s+/g, ' ')")
                        m100 = re.search(r'100 (?:km|км) ≈ (?:≈ )?(\d[\d,. ]*) ' + ('RSD' if cur == 'RSD' else re.escape(sym[cur])), h100)
                        v100 = float(m100.group(1).replace(' ', '').replace('.', '').replace(',', '.')) if m100 and cur != 'RSD' else None
                        check(m100 and (cur == 'RSD' or 9 < v100 < 17), f'map {tag} {sid}: 100 km over 1.000 RSD converted as thousands', h100)
                    if sid == 'cg-80' and lang == 'sr' and cur == 'EUR':
                        await shot(pg, 'mapa_mojauto_eur_1440.png', '#mcard .ccard')
                f = {x['id']: x['pl'] for x in await pg.evaluate('window.bvMapQa()')}
                code = {'RSD': 'RSD', 'EUR': 'EUR', 'USD': 'USD'}[cur]
                check(all(re.match(r'^~[\d,.]+ ' + code + '/km$', f.get(i) or '') for i in ('cg-80', 'ocm-263893', 'rm-4479035-2042305')),
                      f'map {tag}: pins per km, ASCII', [f.get('cg-80'), f.get('ocm-263893'), f.get('rm-4479035-2042305')])
                lst = await pg.evaluate("[...document.querySelectorAll('#mlist .st .pr')].map(e => [e.innerText.replace(/\\s+/g, ' ').trim(), (e.querySelector('.fxw') || {}).title || '']).filter(x => x[0])")
                if cur == 'RSD':
                    ok = lst and any('RSD' + km_u[lang] in x[0] for x in lst) and not any(re.search(r'[€$]', x[0]) for x in lst)
                else:
                    ok = lst and not any('RSD' in x[0] for x in lst) and any(sym[cur] + km_u[lang] in x[0] and 'RSD' in x[1] for x in lst)
                check(ok, f'map {tag}: list per km {"in RSD" if cur == "RSD" else "converted only (RSD in the tooltip)"}', lst[:3])
                # "Najbliži punjač" (fixed location in Novi Sad)
                await pg.evaluate("localStorage.removeItem('bv:car')")
                await pg.goto('about:blank')
                await go(pg, pre + '/mapa/?najblizi=brzi&qa=1', 300)
                await pg.wait_for_selector('.nrp .nrl', timeout=8000)
                await pg.wait_for_timeout(400)
                nr = await pg.evaluate("[...document.querySelectorAll('.nrp .nr-pr')].map(e => [e.innerText.replace(/\\s+/g, ' ').trim(), e.title || ''])")
                pat = r'^(≈ |~|od |from |от )?[\d,.–-]+ RSD' if cur == 'RSD' else r'^≈ [\d,.–]+ ' + re.escape(sym[cur])
                check(nr and all(re.match(pat, x[0]) for x in nr) and (cur == 'RSD' or all('RSD' not in x[0] and 'RSD' in x[1] for x in nr)),
                      f'map {tag}: "Najbliži punjač" prices {"in RSD" if cur == "RSD" else "converted only (RSD in the tooltip)"}', nr)
                if lang == 'sr' and cur == 'EUR':
                    await shot(pg, 'mapa_najblizi_eur_1440.png', '.nrp')
            # switch back to RSD on an open card: dinars only again, the same text as at first
            await pg.evaluate("localStorage.setItem('bv:cur', 'EUR')")
            await pg.goto('about:blank')
            await go(pg, pre + '/mapa/?qa=1#ocm-260806', 1400)
            await pg.evaluate("bvFx.set('RSD')")
            await pg.wait_for_timeout(250)
            check(await pg.evaluate(card_txt) == base['gz'] and await pg.evaluate("document.querySelectorAll('.ccard .fx-p, .ccard .fx-s').length") == 0,
                  f'map {lang}: EUR → RSD on an open card restores the dinars exactly')
            check(not errs, f'map {lang}: no JS errors', errs[:5])
            await ctx.close()

        # ------------------------------------------------------------------ 6. phones and tablets: header, menu, no overflow
        print('— layout')
        for w in (360, 768, 1440):
            ctx = await new_ctx(b, w, 800, cur='EUR', mobile=w < 900)
            pg = await ctx.new_page()
            for path in ('/javno-punjenje/', '/javno-punjenje/chargego/', '/cena-punjaca-za-elektricni-auto', '/podaci/wallbox-modeli/',
                         '/alati/kalkulator-troskova/', '/firme/stasanet/', '/ru/javno-punjenje/', '/en/podaci/tarife-eps/'):
                await go(pg, path, 250)
                r = await pg.evaluate("({sw: document.documentElement.scrollWidth, iw: innerWidth, bar: getComputedStyle(document.querySelector('.hd-cur')).display})")
                check(r['sw'] <= r['iw'], f'{w}px {path}: no horizontal scroll', r)
            bar = await pg.evaluate("getComputedStyle(document.querySelector('.hd-cur')).display")
            check((bar == 'none') == (w < 440), f'{w}px: switcher {"in the menu" if w < 440 else "in the header bar"}', bar)
            await go(pg, '/javno-punjenje/')
            if w < 440:
                await pg.click('.burger')
                await pg.wait_for_timeout(150)
                await pg.select_option('.hd-cur-m .fx-sel', 'USD')
                await pg.wait_for_timeout(150)
                check(await pg.evaluate("bvFx.get() === 'USD' && document.querySelector('.hd-cur-m label').getAttribute('for') === 'fx-sel-m'"), f'{w}px: switcher in the burger menu works')
                await pg.screenshot(path=str(SHOTS / f'zaglavlje_meni_{w}.png'), clip={'x': 0, 'y': 0, 'width': w, 'height': 760})
                await pg.select_option('.hd-cur-m .fx-sel', 'EUR')
                await pg.click('.burger')
            await pg.screenshot(path=str(SHOTS / f'zaglavlje_{w}.png'), clip={'x': 0, 'y': 0, 'width': w, 'height': 120})
            if w == 360:
                for path, name in (('/javno-punjenje/', 'cene_eur_360.png'), ('/javno-punjenje/chargego/', 'mreza_eur_360.png'),
                                   ('/podaci/wallbox-modeli/', 'wallbox_eur_360.png'), ('/alati/kalkulator-troskova/', 'kalkulator_eur_360.png')):
                    await go(pg, path, 250)
                    sel_ = {'cene_eur_360.png': '.pcards', 'mreza_eur_360.png': 'main .wrap.main', 'wallbox_eur_360.png': 'main table',
                            'kalkulator_eur_360.png': 'form.calc'}[name]
                    await shot(pg, name, sel_)
            await ctx.close()

        # ------------------------------------------------------------------ 7. the visit counter (bv.js, RUNBOOK 3.16)
        # One request per page view; choosing a currency (switcher or ?cur= on the same view) sends nothing more. The
        # counter only runs on www.blokvolt.rs and not in automated browsers: the pages are served under that name from
        # this server (with its CSP, so connect-src is checked too) and navigator.webdriver is hidden.
        print('— visit counter')
        ctx = await b.new_context(viewport={'width': 1440, 'height': 900}, service_workers='block')
        await ctx.add_init_script("Object.defineProperty(Navigator.prototype, 'webdriver', {get: () => false});")
        hits, csp = [], []

        async def site(route):
            resp = await route.fetch(url=route.request.url.replace('https://www.blokvolt.rs', BASE))
            await route.fulfill(response=resp)

        async def bot(route):
            hits.append(json.loads(route.request.post_data or '{}'))
            await route.fulfill(status=204, body='')
        await ctx.route('https://www.blokvolt.rs/**', site)
        await ctx.route('https://evolako-bot.mr-smekhov.workers.dev/**', bot)
        pg = await ctx.new_page()
        pg.on('console', lambda m: csp.append(m.text[:200]) if 'Content Security Policy' in m.text else None)
        await pg.goto('https://www.blokvolt.rs/javno-punjenje/', wait_until='load')
        await pg.wait_for_timeout(500)
        check(len(hits) == 1 and hits[0].get('p') == '/javno-punjenje/' and hits[0].get('h') == 'www.blokvolt.rs', 'counter: one request for the page view (CSP allows it)', hits)
        for c in ('EUR', 'USD', 'RSD', 'EUR'):
            await pg.select_option('.hd-cur .fx-sel', c)
            await pg.wait_for_timeout(300)
        conv = await pg.evaluate("document.querySelectorAll('.fx-p').length")
        check(len(hits) == 1 and conv > 20, f'counter: four currency switches, no extra request ({conv} converted)', len(hits))
        await pg.goto('https://www.blokvolt.rs/alati/kalkulator-troskova/?cur=usd', wait_until='load')
        await pg.wait_for_timeout(500)
        await pg.select_option('.hd-cur .fx-sel', 'RSD')
        await pg.fill('#c-km', '2000')
        await pg.wait_for_timeout(400)
        check(len(hits) == 2 and hits[1].get('p') == '/alati/kalkulator-troskova/', 'counter: next page with ?cur=usd → exactly one more, path without the query', hits[1:])
        check(not csp, 'counter: no CSP violations (connect-src: the counter and /api/kurs)', csp[:3])
        await ctx.close()
        await b.close()
    print(f'\n{oks} passed, {fails} failed')
    sys.exit(1 if fails else 0)


asyncio.run(main())
