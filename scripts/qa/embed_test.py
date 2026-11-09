"""Widgets for other sites (RUNBOOK 3.40): /embed/mapa/ and /embed/cene/ inside an iframe on another origin.
Checks: the frame loads (no X-Frame-Options / frame-ancestors block), no JS or CSP errors, the wide and the narrow
layout (list sheet, card), ?grad= / ?mesto=&naziv= / ?mreza= / ?f=, the card's "Otvori na BlokVoltu" link with the host
as utm_source, the configurator's code and preview. Map tiles are stubbed (the container cannot reach OpenFreeMap).
Usage: python3 scripts/qa/cfserve.py dist 8787 &  then  python3 scripts/qa/embed_test.py [/tmp/emb-shots]"""
import json, sys, threading, http.server, functools, os
from playwright.sync_api import sync_playwright

SITE = 'http://127.0.0.1:8787'
HOST_PORT = 8799
OUT = sys.argv[1] if len(sys.argv) > 1 else '/tmp/emb-shots'
os.makedirs(OUT, exist_ok=True)
STYLE = {'version': 8, 'glyphs': 'https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf', 'sources': {},
         'layers': [{'id': 'bg', 'type': 'background', 'paint': {'background-color': '#ECEDE8'}}]}

# the host site: another origin (another port), a plain page with the widget's code
HOST_DIR = '/tmp/emb-host'
os.makedirs(HOST_DIR, exist_ok=True)


def host_page(src, w, h):
    return (f'<!doctype html><meta name=viewport content="width=device-width"><body style="margin:0;padding:20px;font:16px system-ui;background:#fff">'
            f'<h1 style="font-size:20px">Hotel test</h1><p>Tekst sajta pre mape.</p>'
            f'<div style="max-width:{w}px"><iframe id=w src="{src}" width="100%" height="{h}" style="border:1px solid #E2E4DF;border-radius:14px" '
            f'allow="geolocation" loading="eager"></iframe></div><p>Tekst posle.</p></body>')


class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


threading.Thread(target=lambda: http.server.ThreadingHTTPServer(('127.0.0.1', HOST_PORT), functools.partial(Q, directory=HOST_DIR)).serve_forever(), daemon=True).start()
fails = []


def check(cond, msg):
    print(('ok   ' if cond else 'FAIL ') + msg)
    if not cond:
        fails.append(msg)


with sync_playwright() as p:
    b = p.chromium.launch()

    def run(name, src, w, h, vw=None, act=None):
        open(f'{HOST_DIR}/{name}.html', 'w').write(host_page(SITE + src, w, h))
        ctx = b.new_context(viewport={'width': vw or (w + 40), 'height': h + 200}, device_scale_factor=2)
        ctx.route('https://tiles.openfreemap.org/styles/**', lambda r: r.fulfill(status=200, content_type='application/json', body=json.dumps(STYLE)))
        ctx.route('https://tiles.openfreemap.org/fonts/**', lambda r: r.fulfill(status=404, body=''))
        ctx.route('https://static.cloudflareinsights.com/**', lambda r: r.fulfill(status=200, content_type='text/javascript', body=''))
        pg = ctx.new_page()
        errs = []
        pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' and 'pbf' not in m.text and '404' not in m.text else None)
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.goto(f'http://127.0.0.1:{HOST_PORT}/{name}.html')
        fr = pg.frame_locator('#w')
        fr.locator('body').wait_for()
        pg.wait_for_timeout(1800)
        f = pg.frames[1]
        res = act(pg, f) if act else None
        pg.wait_for_timeout(400)
        pg.locator('#w').screenshot(path=f'{OUT}/{name}.png')
        check(not errs, f'{name}: no errors {errs[:3]}')
        ctx.close()
        return res

    def wide(pg, f):
        n = f.locator('#mlist .st').count()
        check(n > 20, f'wide: list has rows ({n})')
        check(f.locator('.emb-foot').is_visible(), 'wide: signature under the list')
        check(not f.locator('[data-emb-list]').is_visible(), 'wide: no list button')
        href = f.locator('.emb-foot').get_attribute('href')
        check('utm_source=127.0.0.1' in href, f'wide: signature names the host ({href})')
        f.locator('#mlist .st').first.click()
        pg.wait_for_timeout(500)
        check(f.locator('.card-ov.is-open').is_visible(), 'wide: card opens')
        box, side = f.locator('.card-ov').bounding_box(), f.locator('.map-side').bounding_box()
        check(abs(box['x'] - side['x']) < 2 and abs(box['width'] - side['width']) < 2, 'wide: card covers the list column')
        o = f.locator('.emb-open')
        check(o.count() == 1 and 'utm_medium=vidzet' in o.get_attribute('href') and '#' in o.get_attribute('href'), 'wide: card has "Otvori na BlokVoltu" with the station')
        check(f.locator('.ccard .fav').count() == 0 and f.locator('.ccard [data-share]').count() == 0, 'wide: no favourite or share in the card')
        check(f.locator('.add-ctl, .maplibregl-ctrl-add').count() == 0, 'wide: no "Dodaj punjač"')
        check(f.evaluate("getComputedStyle(document.querySelector('.ccard')).position") != 'fixed', 'wide: card is not a bottom sheet')

    def narrow(pg, f):
        check(f.locator('[data-emb-list]').is_visible(), 'narrow: list button visible')
        check(not f.locator('.emb-sheet').is_visible() or f.evaluate("getComputedStyle(document.getElementById('emb-sheet')).visibility") == 'hidden', 'narrow: sheet closed at start')
        lbl = f.locator('[data-emb-list]').inner_text()
        check(any(c.isdigit() for c in lbl), f'narrow: list button shows a count ({lbl!r})')
        f.locator('[data-emb-list]').click()
        pg.wait_for_timeout(500)
        check(f.evaluate("getComputedStyle(document.getElementById('emb-sheet')).visibility") == 'visible', 'narrow: sheet opens')
        pg.locator('#w').screenshot(path=f'{OUT}/narrow-list.png')
        f.locator('#mlist .st').first.click()
        pg.wait_for_timeout(600)
        check(f.evaluate("getComputedStyle(document.getElementById('emb-sheet')).visibility") == 'hidden', 'narrow: picking a row closes the sheet')
        check(f.locator('.card-ov.is-open').is_visible(), 'narrow: card opens')

    def host(pg, f):
        check(f.locator('.host-pin').count() == 1, 'mesto: host pin drawn')
        check('Hotel Dunav' in f.locator('.host-n').inner_text(), 'mesto: host name shown')
        txt = f.locator('#mcount').inner_text()
        check(any(w in txt for w in ('najbliži', 'nearest', 'ближайшие')), f'mesto: list ordered by distance ({txt!r})')

    def net(pg, f):
        on = f.locator('.chip[aria-pressed="true"]').inner_text()
        check('Charge' in on, f'mreza: the network chip is on ({on!r})')

    def ru(pg, f):
        check(f.evaluate('document.documentElement.lang').startswith('ru'), 'ru: page language')
        check('Найти' in f.locator('#mq').get_attribute('placeholder') or 'Город' in f.locator('#mq').get_attribute('placeholder'), 'ru: search placeholder translated')

    run('wide', '/embed/mapa/', 980, 600, act=wide)
    run('wide-760', '/embed/mapa/?grad=novi-sad', 760, 560)
    run('narrow', '/embed/mapa/', 375, 600, vw=420, act=narrow)
    run('narrow-low', '/embed/mapa/?f=fast', 340, 420, vw=380)
    run('mesto', '/embed/mapa/?mesto=45.2551,19.8452&naziv=Hotel%20Dunav', 760, 560, act=host)
    run('mreza', '/embed/mapa/?mreza=chargego', 980, 560, act=net)
    run('ru', '/ru/embed/mapa/', 375, 560, vw=420, act=ru)
    run('en-wide', '/en/embed/mapa/', 1100, 640)
    run('cene', '/embed/cene/', 420, 640, vw=460)
    run('cene-wide', '/en/embed/cene/', 640, 560)

    # the configurator: the code follows the form, the preview loads the widget
    ctx = b.new_context(viewport={'width': 1360, 'height': 1100}, device_scale_factor=1)
    ctx.route('https://tiles.openfreemap.org/styles/**', lambda r: r.fulfill(status=200, content_type='application/json', body=json.dumps(STYLE)))
    ctx.route('https://tiles.openfreemap.org/fonts/**', lambda r: r.fulfill(status=404, body=''))
    pg = ctx.new_page()
    errs = []
    pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' and 'pbf' not in m.text and '404' not in m.text else None)
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(SITE + '/mapa-za-vas-sajt/')
    pg.wait_for_timeout(1500)
    code = pg.locator('#vz-kod').input_value()
    check('/embed/mapa/' in code and 'allow="geolocation"' in code and 'Mapa punjača BlokVolt' in code, 'configurator: default code')
    pg.select_option('#vz-pogled', 'mesto')
    pg.fill('#vz-ll', '45,2551 19,8452')
    pg.fill('#vz-naziv', 'Hotel "Dunav" <b>')
    pg.select_option('#vz-filter', 'fast')
    pg.locator('input[name=jezik][value=en]').check(force=True)
    pg.wait_for_timeout(1200)
    code = pg.locator('#vz-kod').input_value()
    check('/en/embed/mapa/?mesto=45.2551,19.8452&amp;naziv=Hotel%20%22Dunav%22%20%3Cb%3E&amp;f=fast' in code, f'configurator: place, filter, language in the code')
    check('EV charging map of Serbia' in code and 'BlokVolt charging map' in code, 'configurator: English texts in the code')
    src = pg.locator('[data-vz-frame]').get_attribute('src')
    check(src.startswith('/en/embed/mapa/?mesto='), f'configurator: preview follows ({src})')
    pg.fill('#vz-ll', 'abc')
    pg.wait_for_timeout(200)
    check(pg.locator('#vz-ll-e').is_visible(), 'configurator: bad coordinates explained')
    pg.locator('input[name=tip][value=cene]').check(force=True)
    pg.wait_for_timeout(1200)
    code = pg.locator('#vz-kod').input_value()
    check('/embed/cene/' in code and 'geolocation' not in code, 'configurator: price widget code')
    check(not pg.locator('[data-vz-map]').is_visible(), 'configurator: map step hidden for prices')
    pg.locator('input[name=tip][value=mapa]').check(force=True)
    pg.select_option('#vz-pogled', 'grad')
    pg.locator('input[name=jezik][value=sr]').check(force=True)
    pg.wait_for_timeout(2500)
    pg.screenshot(path=f'{OUT}/configurator.png', full_page=True)
    pg.locator('.vz-dev label', has_text='Telefon').click()
    pg.wait_for_timeout(1500)
    pg.screenshot(path=f'{OUT}/configurator-tel.png')
    check(not errs, f'configurator: no errors {errs[:3]}')
    pg.set_viewport_size({'width': 390, 'height': 900})
    pg.wait_for_timeout(800)
    pg.screenshot(path=f'{OUT}/configurator-phone.png', full_page=True)
    ov = pg.evaluate('document.documentElement.scrollWidth > innerWidth + 1')
    check(not ov, 'configurator: no horizontal overflow on a phone')
    pg.goto(SITE + '/za-programere/')
    pg.wait_for_timeout(600)
    pg.screenshot(path=f'{OUT}/za-programere.png', full_page=True)
    ctx.close()
    b.close()

print('\n' + ('ALL OK' if not fails else f'{len(fails)} FAILED'))
sys.exit(1 if fails else 0)
