# -*- coding: utf-8 -*-
"""Screenshots for the help pages (/pomoc/) — docs/RUNBOOK.md 3.24.

Made from the built site with Playwright: dist/ served by scripts/qa/cfserve.py on 127.0.0.1:8787. Each picture is
taken at twice the pixel density and saved as static/assets/img/pomoc-<id>-<w>.webp in two widths (the CSS width and
double), so build.py shows it sharp and at its natural size ([[shot:<id> | alt]] in content/pomoc/*.md).

The map background is a plain colour (the build containers cannot load the tiles of tiles.openfreemap.org), /api/*
answers with invented sample data — never real drivers' names, comments or photos — and forms are filled with invented
data and never sent. Run after build.py, when the map card, the forms or the pages in a picture change:

    python3 scripts/qa/cfserve.py dist 8787 &
    python3 scripts/pomoc_shots.py            # all
    python3 scripts/pomoc_shots.py mapa-prikljucci mapa-cena-kartica
"""
import asyncio
import io
import json
import sys
import time
from pathlib import Path

from PIL import Image
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'static' / 'assets' / 'img'
BASE = 'http://127.0.0.1:8787'
STYLE = {"version": 8, "sources": {}, "layers": [{"id": "bg", "type": "background", "paint": {"background-color": "#E8EBE4"}}]}
NOW = int(time.time())
# invented sample data for the "Iskustva vozača" block (the site shows what drivers send; these are not real)
SAMPLE = {'ok': True, 'avg': 4.4, 'nr': 9, 'n': 12, 'photos': [], 'items': [
    {'id': 101, 's': 'ok', 'r': 5, 'c': 'Punio sam bez problema, oba priključka rade.', 'n': 'Primer', 'at': NOW - 2 * 86400},
    {'id': 102, 's': 'problem', 'r': 3, 'c': 'Radi samo levi priključak.', 'n': 'Vozač iz primera', 'at': NOW - 9 * 86400},
    {'id': 103, 's': 'ok', 'r': 4, 'c': None, 'n': None, 'at': NOW - 20 * 86400}]}
PHONE = dict(viewport={'width': 390, 'height': 844}, device_scale_factor=2, is_mobile=True, has_touch=True,
             user_agent='Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Mobile Safari/537.36')
DESK = dict(viewport={'width': 1440, 'height': 900}, device_scale_factor=2)


async def api_routes(page):
    async def style(route):
        await route.fulfill(status=200, content_type='application/json', body=json.dumps(STYLE))
    await page.route('https://tiles.openfreemap.org/**', style)

    async def api(route):
        u = route.request.url
        if '/api/stanica/' in u and route.request.method == 'GET':
            body = dict(SAMPLE, st=u.rsplit('/', 1)[1])
        elif u.endswith('/api/stanice'):
            body = {'ok': True, 'st': {}}
        else:
            body = {'ok': True, 'pending': False}
        await route.fulfill(status=200, content_type='application/json', body=json.dumps(body))
    await page.route('**/api/**', api)


async def card(page, sid, extra=''):
    await page.goto(f'{BASE}/mapa/{extra}#{sid}', wait_until='networkidle')
    await page.wait_for_selector('.ccard', timeout=15000)
    await page.wait_for_timeout(700)


def union(boxes, pad=10, vw=None):
    x0 = min(b['x'] for b in boxes) - pad
    y0 = min(b['y'] for b in boxes) - pad
    x1 = max(b['x'] + b['width'] for b in boxes) + pad
    y1 = max(b['y'] + b['height'] for b in boxes) + pad
    x0 = max(0, x0)
    if vw:
        x1 = min(vw, x1)
    return {'x': x0, 'y': max(0, y0), 'width': x1 - x0, 'height': y1 - y0}


async def boxes(page, *sels):
    out = []
    for s in sels:
        el = page.locator(s).first
        await el.scroll_into_view_if_needed()
        out.append(await el.bounding_box())
    return out


async def shot_els(page, *sels, pad=10, first=None):
    """Clip around the union of the elements (document coordinates, so it works below the fold)."""
    bx = await page.evaluate("""(sels) => sels.map(s => { const e = document.querySelector(s); if (!e) return null;
        const r = e.getBoundingClientRect(); return {x: r.left + scrollX, y: r.top + scrollY, width: r.width, height: r.height}; })""", list(sels))
    missing = [s for s, b in zip(sels, bx) if not b]
    if missing:
        raise SystemExit(f'not on the page: {missing}')
    vw = (page.viewport_size or {}).get('width')
    return await page.screenshot(full_page=True, clip=union(bx, pad, vw), animations='disabled')


async def in_card(page, *sels, pad=10, head=False):
    """The map card scrolls inside its own panel: bring the parts into view, then clip within the card. The close and
    star buttons float over the card while it scrolls, so they are hidden unless the picture shows the card's head."""
    await page.add_style_tag(content='.map-top{visibility:hidden}' + ('' if head else '.ccard .x,.ccard .fav{visibility:hidden}'))
    await page.evaluate("""(a) => { const [sels, head] = a; const c = document.querySelector('.ccard');
        if (head) { c.scrollTop = 0; return; }
        const e = document.querySelector(sels[0]); if (!e) return;
        c.scrollTop += e.getBoundingClientRect().top - c.getBoundingClientRect().top - 24; }""", [list(sels), head])
    await page.evaluate("() => document.activeElement && document.activeElement.blur && document.activeElement.blur()")
    await page.wait_for_timeout(300)
    bx = await page.evaluate("""(sels) => sels.map(s => { const e = document.querySelector(s); if (!e) return null;
        const r = e.getBoundingClientRect(); return {x: r.left, y: r.top, width: r.width, height: r.height}; })""", list(sels))
    missing = [s for s, b in zip(sels, bx) if not b]
    if missing:
        raise SystemExit(f'not on the page: {missing}')
    cb = await page.evaluate("() => { const r = document.querySelector('.ccard').getBoundingClientRect(); return {x: r.left, y: r.top, width: r.width, height: r.height}; }")
    u = union(bx, pad)
    # stay inside the card
    x0, y0 = max(u['x'], cb['x']), max(u['y'], cb['y'])
    x1, y1 = min(u['x'] + u['width'], cb['x'] + cb['width']), min(u['y'] + u['height'], cb['y'] + cb['height'])
    return await page.screenshot(clip={'x': x0, 'y': y0, 'width': x1 - x0, 'height': y1 - y0}, animations='disabled')


# ---------------------------------------------------------------- the pictures
async def mapa_filteri_mobilni(page):
    await page.goto(BASE + '/mapa/?f=fast&ok=1', wait_until='networkidle')
    await page.wait_for_timeout(600)
    return await shot_els(page, '.map-top', pad=0)


async def mapa_kartica_mobilni(page):
    await card(page, 'cg-80', '?grad=novi-sad')
    return await in_card(page, '.ccard h2', '.ccard .where', pad=16, head=True)


async def mapa_kartica_potvrdjeno(page):
    await card(page, 'cg-80')
    return await in_card(page, '.ccard h2', '.ccard .vf', pad=14, head=True)


async def mapa_kartica_nije_potvrdjeno(page):
    await card(page, 'ocm-156420')
    return await in_card(page, '.ccard h2', '.ccard .vf-warn', pad=14, head=True)


async def mapa_poslednja_prijava(page):
    await card(page, 'cg-80')
    await page.wait_for_selector('.rv-sum', timeout=8000)
    return await in_card(page, '.ccard .rv > span', '.ccard .rv-btns', pad=14)


async def mapa_iskustva_vozaca(page):
    await card(page, 'cg-80')
    await page.wait_for_selector('.rv-sum', timeout=8000)
    return await in_card(page, '.ccard .rv-q', '.ccard .rv-btns', pad=8)


async def mapa_prijava_forma(page):
    await card(page, 'cg-80')
    await page.wait_for_selector('.rv-sum', timeout=8000)
    await page.click('.ccard [data-ci="ok"]')
    await page.click('.ccard .rv-stars [data-r="5"]')
    await page.fill('#rv-c', 'Oba priključka rade, punjenje je krenulo odmah.')
    await page.wait_for_timeout(300)
    return await in_card(page, '.ccard .rv-btns', '.ccard .rv-form', pad=12)


async def mapa_kartica_izvori(page):
    await card(page, 'ocm-150105')
    return await in_card(page, '.ccard .where', pad=12)


async def mreza_podrska(page):
    await page.goto(BASE + '/javno-punjenje/chargego/', wait_until='networkidle')
    det = page.locator('details', has_text='Podrška').first
    await det.evaluate('d => d.open = true')
    await page.wait_for_timeout(300)
    b = await det.bounding_box()
    await det.scroll_into_view_if_needed()
    b = await det.bounding_box()
    return await page.screenshot(clip={'x': b['x'] - 10, 'y': b['y'] - 10, 'width': b['width'] + 20, 'height': b['height'] + 20})


async def ispravka_punjac_na_mapi(page):
    await page.goto(BASE + '/ispravka/?stanica=cg-80', wait_until='networkidle')
    await page.fill('#f-gde', 'https://www.blokvolt.rs/mapa/#cg-80')      # the page fills in its own address; show the real one
    await page.fill('#f-poruka', 'Na parkingu je sada jedan punjač više, sa desne strane ulaza.')
    await page.evaluate("() => document.activeElement.blur()")
    return await shot_els(page, 'form[data-bv-form]', pad=12)


async def mapa_komentar_prijavi(page):
    await card(page, 'cg-80')
    await page.wait_for_selector('.rv-its li', timeout=8000)
    return await in_card(page, '.ccard .rv-its li', pad=10)


async def mapa_dodaj_fotografiju(page):
    await card(page, 'cg-80')
    return await in_card(page, '.ccard .rv-ph', pad=12)


async def mapa_prikljucci(page):
    await card(page, 'ocm-265195')
    el = page.locator('.ccard .cbox', has_text='Priključci').first
    await el.evaluate("e => e.classList.add('bv-shot')")
    return await in_card(page, '.ccard .bv-shot', pad=12)


async def mapa_imam_teslu(page):
    await card(page, 'ocm-150105', '?tesla=1')
    el = page.locator('.ccard .cbox', has_text='Cena').first
    await el.evaluate("e => e.classList.add('bv-shot')")
    return await in_card(page, '.ccard h2', '.ccard .bv-shot', pad=14, head=True)


async def mapa_cena_kartica(page):
    await card(page, 'osm-n13316918840')
    el = page.locator('.ccard .cbox', has_text='Cena').first
    await el.evaluate("e => e.classList.add('bv-shot')")
    return await in_card(page, '.ccard h2', '.ccard .bv-shot', pad=14, head=True)


async def kalkulator_unos(page):
    await page.goto(BASE + '/alati/kalkulator-troskova/', wait_until='networkidle')
    return await shot_els(page, '.calc-in', pad=12)


async def kalkulator_rezultat(page):
    await page.goto(BASE + '/alati/kalkulator-troskova/', wait_until='networkidle')
    await page.wait_for_timeout(400)
    return await shot_els(page, '.box.res', pad=12)


async def apk_preuzimanje(page):
    await page.goto(BASE + '/aplikacija/', wait_until='networkidle')
    return await page.screenshot(clip={'x': 0, 'y': 60, 'width': 390, 'height': 640})


async def apk_za_proveru_fajla(page):
    await page.goto(BASE + '/aplikacija/', wait_until='networkidle')
    det = page.locator('details', has_text='Za proveru fajla').first
    await det.evaluate("d => { d.open = true; d.classList.add('bv-shot'); }")
    await page.wait_for_timeout(300)
    return await shot_els(page, 'details.bv-shot', pad=10)


async def aplikacija_verzija(page):
    await page.goto(BASE + '/aplikacija/', wait_until='networkidle')
    el = page.locator('p.upd', has_text='Verzija').first
    await el.evaluate("e => { e.classList.add('bv-shot'); e.style.display = 'inline-block'; }")
    return await shot_els(page, 'p.bv-shot', pad=12)


async def offline_stranica(page):
    await page.goto(BASE + '/offline', wait_until='networkidle')
    return await page.screenshot(clip={'x': 0, 'y': 0, 'width': 390, 'height': 700})


async def ispravka_novi_punjac(page):
    await page.goto(BASE + '/ispravka/', wait_until='networkidle')
    await page.select_option('#f-sta', 'novi-punjac')
    await page.fill('#f-gde', 'Parking tržnog centra, Kragujevac (primer)')
    await page.fill('#f-poruka', 'Dva punjača Type 2, 22 kW, na ulazu u garažu; punjenje preko aplikacije mreže, samo za kupce u radno vreme.')
    await page.fill('#f-izvor', 'https://www.primer.rs/punjaci')
    await page.evaluate("() => document.activeElement.blur()")
    return await shot_els(page, 'form[data-bv-form]', pad=12)


async def ispravka_forma_firma(page):
    await page.goto(BASE + '/ispravka/', wait_until='networkidle')
    await page.select_option('#f-sta', 'firma')
    await page.fill('#f-gde', BASE.replace('http://127.0.0.1:8787', 'https://www.blokvolt.rs') + '/firme/primer/')
    await page.fill('#f-poruka', 'Cena ugradnje na našoj stranici je promenjena 1. oktobra (primer).')
    await page.fill('#f-izvor', 'https://www.primer.rs/cenovnik')
    await page.evaluate("() => document.activeElement.blur()")
    return await shot_els(page, 'form[data-bv-form]', pad=12)


async def za_firme_forma(page):
    await page.goto(BASE + '/za-firme/', wait_until='networkidle')
    return await shot_els(page, 'form[data-bv-form]', pad=12)


async def mapa_blizu_mene(page):
    await page.goto(BASE + '/mapa/', wait_until='networkidle')
    await page.wait_for_timeout(500)
    return await shot_els(page, '#mme', pad=40)


async def mapa_podeli_link(page):
    await card(page, 'cg-80')
    await page.click('.ccard [data-share]')
    await page.wait_for_timeout(300)
    return await in_card(page, '.ccard .acts', pad=12)


async def mapa_omiljeni_zvezdica(page):
    await card(page, 'cg-80')
    await page.click('.ccard .fav')
    await page.wait_for_timeout(300)
    return await in_card(page, '.ccard .fav', '.ccard h2', '.ccard .vf', pad=14, head=True)


async def ispravka_forma(page):
    await page.goto(BASE + '/ispravka/', wait_until='networkidle')
    return await shot_els(page, 'form[data-bv-form]', pad=12)


async def mapa_prijavi_gresku(page):
    await card(page, 'cg-80')
    return await in_card(page, '.ccard .acts', pad=12)


async def mapa_atribucija(page):
    await page.goto(BASE + '/mapa/', wait_until='networkidle')
    await page.wait_for_timeout(500)
    return await shot_els(page, '.map-attr', pad=8)


SHOTS = {  # id: (phone or desktop, function)
    'mapa-filteri-mobilni': ('m', mapa_filteri_mobilni), 'mapa-kartica-mobilni': ('m', mapa_kartica_mobilni),
    'mapa-kartica-potvrdjeno': ('m', mapa_kartica_potvrdjeno), 'mapa-kartica-nije-potvrdjeno': ('m', mapa_kartica_nije_potvrdjeno),
    'mapa-poslednja-prijava': ('m', mapa_poslednja_prijava), 'mapa-iskustva-vozaca': ('m', mapa_iskustva_vozaca),
    'mapa-prijava-forma': ('m', mapa_prijava_forma), 'mapa-kartica-izvori': ('m', mapa_kartica_izvori),
    'mreza-podrska': ('d', mreza_podrska), 'ispravka-punjac-na-mapi': ('m', ispravka_punjac_na_mapi),
    'mapa-komentar-prijavi': ('m', mapa_komentar_prijavi), 'mapa-dodaj-fotografiju': ('m', mapa_dodaj_fotografiju),
    'mapa-prikljucci': ('m', mapa_prikljucci), 'mapa-imam-teslu': ('m', mapa_imam_teslu), 'mapa-cena-kartica': ('m', mapa_cena_kartica),
    'kalkulator-unos': ('d', kalkulator_unos), 'kalkulator-rezultat': ('d', kalkulator_rezultat),
    'apk-preuzimanje': ('m', apk_preuzimanje), 'apk-za-proveru-fajla': ('m', apk_za_proveru_fajla),
    'aplikacija-verzija': ('d', aplikacija_verzija), 'offline-stranica': ('m', offline_stranica),
    'ispravka-novi-punjac': ('m', ispravka_novi_punjac), 'ispravka-forma-firma': ('d', ispravka_forma_firma),
    'za-firme-forma': ('d', za_firme_forma), 'mapa-blizu-mene': ('d', mapa_blizu_mene),
    'mapa-podeli-link': ('d', mapa_podeli_link), 'mapa-omiljeni-zvezdica': ('m', mapa_omiljeni_zvezdica),
    'ispravka-forma': ('m', ispravka_forma), 'mapa-prijavi-gresku': ('m', mapa_prijavi_gresku), 'mapa-atribucija': ('d', mapa_atribucija),
}


def save(sid, png, maxw):
    im = Image.open(io.BytesIO(png)).convert('RGB')
    css = min(im.width // 2, maxw)
    for w in (css, css * 2):
        w = min(w, im.width)
        h = round(im.height * w / im.width)
        im.resize((w, h), Image.LANCZOS).save(OUT / f'pomoc-{sid}-{w}.webp', 'WEBP', quality=86, method=6)
    return css, round(im.height / 2)


async def main():
    only = sys.argv[1:]
    todo = {k: v for k, v in SHOTS.items() if not only or k in only}
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'])
        for sid, (kind, fn) in todo.items():
            ctx = await b.new_context(**(PHONE if kind == 'm' else DESK), permissions=['clipboard-read', 'clipboard-write'],
                                      locale='sr-Latn-RS', timezone_id='Europe/Belgrade')
            page = await ctx.new_page()
            await api_routes(page)
            try:
                png = await fn(page)
                css, h = save(sid, png, 340 if kind == 'm' else 760)
                print(f'{sid}: {css}×{h} css px')
            except Exception as e:  # keep going; the missing picture is simply left out of the page
                print(f'{sid}: FAILED {str(e)[:160]}')
            await ctx.close()
        await b.close()

asyncio.run(main())
