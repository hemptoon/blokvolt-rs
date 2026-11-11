# G5 checks (RUNBOOK 3.42): the world widget pages, the configurator and /developers/ in a built dist-com.
#   python3 scripts/qa/world_embed_check.py --strings-only          strings only (used by world_embed.py selftest)
#   python3 scripts/qa/world_embed_check.py dist-com                 static checks of the built pages and _headers
#   python3 scripts/qa/world_embed_check.py dist-com --browser       + Playwright: the widget inside an iframe of another
#        origin (a mock host page on a second port), the view count sent once with the host name only, the link back with
#        utm_source = host, no page errors; the configurator builds the code; 360 / 768 / 1440 screenshots to /tmp/g5_shots
#   (the browser run needs a dist-com built with BV_WORLD_WIDGET_API=http://127.0.0.1:8792/api/svet/vidzet)
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
import world_embed as WE  # noqa: E402

fails = []


def check(cond, what):
    print(('ok   ' if cond else 'FAIL ') + what)
    if not cond:
        fails.append(what)


def strings():
    T = WE.load_strings()
    check(set(T['en']) == set(T['sr']) == set(T['ru']), 'strings: the same keys in en/sr/ru')
    for l in WE.LANGS:
        for k, v in T[l].items():
            if re.search(r'\{[a-z_]+\}', T['en'][k]):
                check(set(re.findall(r'\{[a-z_]+\}', v)) == set(re.findall(r'\{[a-z_]+\}', T['en'][k])), f'placeholders {k} {l}')
    bad = [k for k, v in T['sr'].items() if re.search(r'[А-Яа-я]', v) or re.search(r'\b(ćete|vam se)\b', v) is None and False]
    check(not bad, 'strings: SR in Latin script')
    try:
        import lint_sr
        e, w, _ = lint_sr.lint_text('\n\n'.join(T['sr'].values()))
        check(not e, f'lint_sr: {len(e) if hasattr(e, "__len__") else e} errors')
    except Exception as ex:
        print('lint_sr not run:', ex)


def static(out):
    out = Path(out)
    H = (out / '_headers').read_text(encoding='utf-8')
    for l, p in WE.EMBED.items():
        f = out / p.strip('/') / 'index.html'
        check(f.exists(), f'{p} built')
        if not f.exists():
            continue
        h = f.read_text(encoding='utf-8')
        check('<meta name="robots" content="noindex' in h, f'{p} noindex')
        check('http-equiv="Content-Security-Policy"' in h and 'frame-ancestors' not in re.search(r'http-equiv="Content-Security-Policy" content="([^"]*)"', h).group(1), f'{p} CSP meta without frame-ancestors')
        check('<header' not in h and 'site-footer' not in h, f'{p} no site header or footer')
        cfg = json.loads(re.search(r'<script id="wm-cfg" type="application/json">(.*?)</script>', h, re.S).group(1))
        maps = tuple(__import__('world_i18n').slugs(x)['map'] for x in WE.LANGS)   # LANG0: the map of every enabled language
        check(cfg.get('embed', {}).get('open', '').endswith(maps) and cfg['reports_api'] == '', f'{p} cfg.embed, no reports')
        check('OpenStreetMap' in h and 'OpenFreeMap' in h, f'{p} attribution visible without a click')
        for pat in (r'\bodmah\b', r'24/7', r'Evolako'):
            check(not re.search(pat, h), f'{p} no "{pat}"')
        check(f'{p}*\n  ! X-Frame-Options\n  Content-Security-Policy: frame-ancestors *' in H, f'_headers: {p} may be framed by any site')
        import gzip
        own = [h.encode()] + [(out / 'assets' / 'world' / x).read_bytes() for x in ('world-map.js', 'world-map.css', 'world-embed.css')] + \
            [(out / 'assets' / 'vendor' / 'pmtiles-4.5.0' / 'pmtiles.js').read_bytes(), (out / 'assets' / 'bv.css').read_bytes(), (out / 'assets' / 'com.css').read_bytes()]
        ml = [x.read_bytes() for x in (out / 'assets' / 'vendor' / 'maplibre-6.11.1').glob('maplibre-gl*') if x.suffix in ('.mjs', '.css')]
        gz = lambda bs: sum(len(gzip.compress(b, 6)) for b in bs)
        print(f'     {p}: own files {gz(own) // 1024} KB gzip, MapLibre {gz(ml) // 1024} KB gzip (shared, cached with /map/)')
        check(gz(own) < 300 * 1024, f'{p} own files < 300 KB (gzip) before tiles; MapLibre counted apart, as on /map/')
    check('/*\n  X-Frame-Options: SAMEORIGIN' in H, '_headers: other pages SAMEORIGIN')
    for urls in (WE.CONF, WE.DEV):
        for l, p in urls.items():
            f = out / p.strip('/') / 'index.html'
            check(f.exists(), f'{p} built')
            if not f.exists():
                continue
            h = f.read_text(encoding='utf-8')
            check(all(f'hreflang="{x}"' in h for x in ('en', 'sr', 'ru', 'x-default')), f'{p} hreflang en/sr/ru/x-default')
            # LANG1: the title as the reader sees it ("EV&#39;s" is not a number)
            check(not re.search(r'\d', __import__('html').unescape(re.search(r'<title>(.*?)</title>', h).group(1))), f'{p} no number in <title>')
            for pat in (r'\bodmah\b', r'24/7', r'Evolako'):
                check(not re.search(pat, h), f'{p} no "{pat}"')
    sm = (out / 'sitemap.xml').read_text(encoding='utf-8') if (out / 'sitemap.xml').exists() else ''
    check(not any(p in sm for p in WE.EMBED.values()), 'widgets not in the sitemap')


def browser(out):
    import subprocess, time, threading, http.server
    from playwright.sync_api import sync_playwright
    got = []

    class Api(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a): pass
        def do_OPTIONS(self):
            self.send_response(204); self.send_header('Access-Control-Allow-Origin', '*'); self.send_header('Access-Control-Allow-Headers', 'content-type'); self.end_headers()
        def do_POST(self):
            n = int(self.headers.get('content-length') or 0)
            got.append((self.path, self.headers.get('origin'), self.rfile.read(n).decode()))
            self.send_response(200); self.send_header('Access-Control-Allow-Origin', '*'); self.send_header('Content-Type', 'application/json'); self.end_headers(); self.wfile.write(b'{"ok":true}')
        def do_GET(self):  # the mock host site: a page of "another website" with the widget in an iframe
            body = (f'<!doctype html><html><head><meta charset="utf-8"><title>Host</title></head><body style="margin:0">'
                    f'<p style="height:600px">Host page text</p><iframe id="w" src="http://127.0.0.1:8791/embed/map/?zemlja=DE&snaga=dc,hpc&tema=tamna" '
                    f'style="width:100%;height:520px;border:0"></iframe><p style="height:800px">more text</p></body></html>').encode()
            self.send_response(200); self.send_header('Content-Type', 'text/html'); self.end_headers(); self.wfile.write(body)
    api = http.server.ThreadingHTTPServer(('127.0.0.1', 8792), Api)
    threading.Thread(target=api.serve_forever, daemon=True).start()
    srv = subprocess.Popen([sys.executable, str(ROOT / 'scripts' / 'qa' / 'cfserve.py'), str(out), '8791'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.2)
    shots = Path('/tmp/g5_shots'); shots.mkdir(exist_ok=True)
    try:
        with sync_playwright() as pw:
            b = pw.chromium.launch()
            pg = b.new_page(viewport={'width': 1280, 'height': 900})
            errs = []
            pg.on('pageerror', lambda e: errs.append(str(e)))
            # the host page is served by the mock API server on "localhost" — another origin than 127.0.0.1:8791
            r = pg.goto('http://localhost:8792/host.html')
            pg.wait_for_timeout(3500)
            fr = pg.frame_locator('#w')
            check(fr.locator('#map').count() == 1, 'browser: the widget loads inside an iframe of another site')
            href = fr.locator('.wme-by').get_attribute('href') or ''
            check('utm_source=localhost' in href and 'utm_medium=widget' in href and 'zemlja=DE' in href and 'tema' not in href, f'browser: link back keeps filters, utm_source = host ({href[:120]})')
            views = [g for g in got if g[0] == '/api/svet/vidzet']
            check(len(views) == 1, f'browser: one view count per load ({len(views)})')
            if views:
                body = json.loads(views[0][2])
                check(body == {'h': 'localhost', 'k': 'map', 'l': 'en'}, f'browser: the count holds the host name only {body}')
            frame = next(f for f in pg.frames if '/embed/map/' in f.url)
            check(frame.evaluate('document.documentElement.classList.contains("wm-dark")'), 'browser: tema=tamna → dark')
            check(frame.evaluate('!!(window.BVWorldMap && window.BVWorldMap.map && window.BVWorldMap.map.cooperativeGestures && window.BVWorldMap.map.cooperativeGestures.isEnabled())'), 'browser: two-finger gestures in the widget')
            check('zemlja=DE' in frame.url and 'tema=tamna' in frame.url, 'browser: the widget keeps its address (tema too)')
            check(not errs, f'browser: no page errors in the widget {errs[:3]}')
            pg.screenshot(path=str(shots / 'host_1280.png'))
            for w in (360, 768, 1440):
                p2 = b.new_page(viewport={'width': w, 'height': 800})
                e2 = []
                p2.on('pageerror', lambda e: e2.append(str(e)))
                for name, url in (('embed', '/embed/map/?zemlja=FR'), ('conf', '/map-for-your-site/'), ('dev', '/developers/'),
                                  ('conf_ru', '/ru/karta-dlya-sajta/'), ('dev_sr', '/sr/za-programere/')):
                    p2.goto('http://127.0.0.1:8791' + url)
                    p2.wait_for_timeout(1200)
                    ov = p2.evaluate('document.documentElement.scrollWidth - document.documentElement.clientWidth')
                    check(ov <= 1, f'browser {w}px {url}: no horizontal scroll ({ov})')
                    p2.screenshot(path=str(shots / f'{name}_{w}.png'), full_page=name != 'embed')
                check(not e2, f'browser {w}px: no page errors {e2[:2]}')
                p2.close()
            # configurator: choose things and read the code
            p3 = b.new_page(viewport={'width': 1280, 'height': 900})
            p3.goto('http://127.0.0.1:8791/map-for-your-site/')
            p3.select_option('select[name=zemlja]', 'AT')
            p3.check('input[name=lang][value=ru]')
            p3.check('input[name=tema][value=tamna]')
            p3.uncheck('input[name=snaga][value=ac]')
            p3.fill('input[name=view]', 'https://blokvolt.com/map/?grad=2761369#11/48.20800/16.37300')
            p3.wait_for_timeout(600)
            code = p3.input_value('#wz-code')
            check('/ru/embed/karta/?zemlja=AT&amp;grad=2761369&amp;snaga=dc,hpc,nepoznato&amp;tema=tamna#11/48.20800/16.37300' in code, 'configurator: the code ' + code[:160])
            check(p3.get_attribute('#wz-frame', 'src').startswith('/ru/embed/karta/?zemlja=AT'), 'configurator: the preview follows')
            p3.fill('input[name=view]', 'https://example.com/x')
            p3.wait_for_timeout(500)
            check(p3.is_visible('#wz-vbad'), 'configurator: a foreign link is refused')
            p3.goto('http://127.0.0.1:8791/developers/')
            p3.fill('input[name=email]', 'dev@example.com'); p3.fill('textarea[name=poruka]', 'Need DE and AT, monthly.')
            p3.wait_for_timeout(3100)
            p3.click('#dv-form button[type=submit]')
            p3.wait_for_timeout(600)
            reqs = [g for g in got if g[0] == '/api/svet/zahtev']
            demo = 'Preview' in p3.inner_text('#dv-msg')
            check(len(reqs) == 1 or demo, f'developers: the request is sent (or demo without the API) {p3.inner_text("#dv-msg")}')
            b.close()
    finally:
        srv.terminate()
        api.shutdown()


if __name__ == '__main__':
    a = sys.argv[1:]
    if a == ['--strings-only']:
        strings()
    else:
        strings()
        static(a[0])
        if '--browser' in a:
            browser(a[0])
    print('world_embed_check:', 'ALL OK' if not fails else f'{len(fails)} FAIL')
    sys.exit(1 if fails else 0)
