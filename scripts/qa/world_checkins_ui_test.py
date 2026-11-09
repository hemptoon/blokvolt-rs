# -*- coding: utf-8 -*-
"""G6 in the browser: the check-in block of the world map card (/map/, /sr/mapa/, /ru/karta/).

Builds dist-com into a temp folder with the real map data (--data: a folder with latest.json, manifest, PMTiles and
cards — the K1 output) and a fake check-in address, adds the G3 price file of the map, and checks in Chromium at 390 and
1440 px for EN, SR and RU:
  - the card of a place whose network has a G3 tariff shows „Is it working?“, three buttons, „How much did you pay?“, the
    rules and privacy texts;
  - the summary from GET /api/svet/stanje is shown (relative date in the page language, number of check-ins);
  - „Working“ sends {pid, s, cls, cc, net, lang, hp} once, a second tap does not send again;
  - a price 3 × the list price is not sent at the first press (warning with the list price), it is at the second;
  - a normal price is sent with amount, unit, currency, month; 429 shows the limit text;
  - demo mode (checkins_api = "demo", the dev previews): the form works, nothing is requested, the demo text is shown;
  - a Balkan place (card with `more`) has no check-in block;
  - no console errors; touch targets ≥ 44 px on 390 px; screenshots.

Usage: python3 scripts/qa/world_checkins_ui_test.py --data <folder with latest.json> [--out qa-ci]"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'scripts' / 'qa'))
import world_map_test as WT  # noqa: E402  (Range server, readiness, stub base map)

FAKE = 'https://ci.test.invalid/api/svet/stanje'
PAGES = WT.PAGES


def build(site, base):
    env = dict(os.environ, BV_COM_OUT=str(site), BV_WORLD_DATA=base + '/world/', BV_WORLD_REPORTS=WT.FAKE_API, BV_WORLD_CHECKINS=FAKE)
    env.pop('BV_WORLD_PAGES', None)
    r = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'gen_com.py')], cwd=ROOT, env=env, capture_output=True, text=True)
    if r.returncode:
        print(r.stdout[-2000:], r.stderr[-2000:])
        raise SystemExit('gen_com.py failed')
    # the G3 price file of the map card (built only with the world pages): the same function, put next to the map
    import world_prices as WP
    os.environ['BV_WORLD_PAGES'] = 'x'
    try:
        P = WP.prepare(types.SimpleNamespace(OUT=site))
    finally:
        os.environ.pop('BV_WORLD_PAGES', None)
    for lang, path in PAGES.items():
        f = site / path.strip('/') / 'index.html'
        h = f.read_text(encoding='utf-8')
        h = h.replace('"prices": ""', '"prices": "' + P['map_json'] + '"')
        f.write_text(h, encoding='utf-8')
        d = site / ('demo' + path)      # the same page in demo mode
        d.mkdir(parents=True, exist_ok=True)
        (d / 'index.html').write_text(h.replace(json.dumps(FAKE)[1:-1], 'demo'), encoding='utf-8')
    return json.loads((site / P['map_json'].lstrip('/')).read_text(encoding='utf-8'))


def pick(data, prices):
    """a place with a G3 tariff (DC < 150 kW, EUR) and a Balkan place: cards from the card files, points from the layer
    (data/public_sites.geojsonseq.gz, the K1 output next to the cards)"""
    import gzip
    man = json.load(open(data / json.load(open(data / 'latest.json'))['manifest']))
    want = bal = None
    for f in sorted((data / ('cards-' + man['date'])).rglob('*.json')):
        for pid, c in (json.load(open(f)).get('sites') or {}).items():
            if c.get('more') and not bal:
                bal = [pid, c]
            e = prices['nets'].get(f"{c.get('cc')}|{c.get('net')}")
            if not want and e and e.get('dc') and e.get('cur') == 'EUR' and c.get('dc') and (c.get('kw') or 0) < 150 and c.get('net'):
                want = [pid, c, e]
        if want and bal:
            break
    need = {int(x[0]) for x in (want, bal) if x}
    with gzip.open(data / 'public_sites.geojsonseq.gz', 'rt') as fh:
        for line in fh:
            if not need:
                break
            m = re.search(r'"coordinates":\[([-0-9.]+),([-0-9.]+)\].*?"i":(\d+)', line)
            if m and int(m.group(3)) in need:
                ll = [float(m.group(1)), float(m.group(2))]
                for x in (want, bal):
                    if x and int(x[0]) == int(m.group(3)):
                        x[1] = dict(x[1], ll=ll)
                need.discard(int(m.group(3)))
    return want, bal


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', required=True)
    ap.add_argument('--out', default='qa-ci')
    a = ap.parse_args()
    from playwright.sync_api import sync_playwright
    data, out = Path(a.data).resolve(), Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix='ci-qa-'))
    site = tmp / 'site'
    srv, port = WT.serve(site)
    base = f'http://127.0.0.1:{port}'
    prices = build(site, base)
    os.symlink(data, site / 'world')
    want, bal = pick(data, prices)
    fails = []
    if not want:
        raise SystemExit('no card with a DC EUR tariff found in the data')
    pid, card, tariff = want
    ll = card['ll']
    print(f'place {pid}: {card.get("net")} {card["cc"]} DC list {tariff["dc"]} EUR; balkan {bal[0] if bal else None}')
    with sync_playwright() as pw:
        br = pw.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
        for lang in ('en', 'sr', 'ru'):
            for w in (390, 1440):
                f = one(br, base, lang, w, out, pid, ll, tariff, bal)
                fails += [f'{lang} {w}: {x}' for x in f]
        br.close()
    srv.shutdown()
    shutil.rmtree(tmp, ignore_errors=True)
    for x in fails:
        print('FAIL', x)
    print('world_checkins_ui_test:', 'OK' if not fails else f'{len(fails)} failure(s)')
    return 1 if fails else 0


def one(br, base, lang, w, out, pid, ll, tariff, bal):
    fails, errors, posted, got = [], [], [], []
    ctx = br.new_context(viewport={'width': w, 'height': 860}, has_touch=w < 900, is_mobile=w < 700,
                         locale={'en': 'en-GB', 'sr': 'sr-Latn-RS', 'ru': 'ru-RU'}[lang])
    ctx.route(re.compile(r'https://tiles\.openfreemap\.org/.*'), lambda r: r.fulfill(status=200, content_type='application/json', body=json.dumps(WT.STUB_STYLE)))
    ctx.route(re.compile(r'https://qa-glyphs\.invalid/.*'), lambda r: r.fulfill(status=200, body=b''))
    mode = {'v': 'ok'}
    import time as _t

    def api(route):
        req = route.request
        H = {'Access-Control-Allow-Origin': '*'}
        if req.method == 'OPTIONS':
            return route.fulfill(status=204, headers={**H, 'Access-Control-Allow-Headers': 'content-type', 'Access-Control-Allow-Methods': 'GET, POST'})
        if req.method == 'GET':
            got.append(req.url)
            now = int(_t.time())
            return route.fulfill(status=200, content_type='application/json', headers=H, body=json.dumps(
                {'ok': True, 'now': now, 'last_ok': now - 3 * 86400, 'last': {'s': 'radi', 'at': now - 3 * 86400}, 'd30': {'radi': 4, 'ne_radi': 1, 'zauzeto': 0}}))
        posted.append(json.loads(req.post_data or '{}'))
        if mode['v'] == '429':
            return route.fulfill(status=429, content_type='application/json', headers=H, body='{"ok":false,"error":"limit"}')
        return route.fulfill(status=200, content_type='application/json', headers=H, body='{"ok":true}')
    ctx.route(re.compile(re.escape(FAKE) + r'.*'), api)
    page = ctx.new_page()
    page.on('console', lambda m: errors.append(f'console: {m.text}') if m.type == 'error' else None)
    page.on('pageerror', lambda e: errors.append(f'pageerror: {e}'))
    T = None
    page.goto(base + PAGES[lang] + f'#12/{ll[1]}/{ll[0]}', wait_until='load')
    if not WT.wait_ready(page):
        return ['map not ready']
    T = page.evaluate("JSON.parse(document.getElementById('wm-i18n').textContent)")
    page.evaluate("([p, c]) => BVWorldMap.openCard(p, c, null)", [pid, ll])
    try:
        page.wait_for_selector('#wm-card .wm-ci [data-ci="radi"]', timeout=10000)
    except Exception:
        page.screenshot(path=str(out / f'{lang}-{w}-nobox.png'))
        return ['no check-in block in the card'] + errors[:3]
    page.wait_for_function("() => document.getElementById('wm-cis').textContent.length > 0", timeout=5000)
    s = page.text_content('#wm-cis')
    want = T['ci_last_ok'].split('{d}')[0]
    if want not in s or not re.search(r'\d', s):
        fails.append(f'summary text: {s!r}')
    if not got or f'pid={pid}' not in got[0]:
        fails.append(f'GET summary not requested: {got}')
    for k in ('ci_h', 'ci_paid', 'ci_rules_h'):
        if T[k] not in page.text_content('#wm-card'):
            fails.append(f'missing text {k}')
    if w < 700:
        small = page.evaluate("[...document.querySelectorAll('#wm-card .wm-ci .btn')].filter(b => b.getBoundingClientRect().height < 44).length")
        if small:
            fails.append(f'{small} check-in button(s) under 44 px')
    page.screenshot(path=str(out / f'{lang}-{w}-card.png'))
    # state: once
    page.click('#wm-card [data-ci="radi"]')
    page.wait_for_function("() => document.getElementById('wm-cis').textContent === JSON.parse(document.getElementById('wm-i18n').textContent).ci_thanks", timeout=5000)
    if len(posted) != 1 or posted[0].get('s') != 'radi' or posted[0].get('pid') != int(pid) or posted[0].get('lang') != lang or posted[0].get('hp') != '' \
            or posted[0].get('cls') not in ('dc', 'hpc') or not posted[0].get('cc') or not posted[0].get('net'):
        fails.append(f'state body: {posted}')
    if page.evaluate("document.querySelector('#wm-card [data-ci=\"ne_radi\"]').disabled") is not True:
        fails.append('state buttons not disabled after sending')
    # price: far → warning first
    page.click('#wm-card [data-paid]')
    page.wait_for_selector('#wm-pff')
    page.fill('#wm-pa', str(round(tariff['dc'] * 3, 2)).replace('.', ',' if lang != 'en' else '.'))
    page.select_option('#wm-pc', 'EUR')
    page.click('#wm-pff button[type="submit"]')
    msg = page.text_content('#wm-pff .wm-rmsg')
    if len(posted) != 1 or T['ci_far'].split('(')[0] not in msg:
        fails.append(f'far price not warned: {msg!r} {len(posted)}')
    page.screenshot(path=str(out / f'{lang}-{w}-far.png'))
    page.click('#wm-pff button[type="submit"]')
    page.wait_for_selector('#wm-pf .wm-ok', timeout=5000)
    p = posted[-1] if len(posted) == 2 else {}
    ym = page.evaluate("new Date().toISOString().slice(0, 7)")
    if not (abs(p.get('amt', 0) - round(tariff['dc'] * 3, 2)) < 1e-9 and p.get('unit') == 'kwh' and p.get('cur') == 'EUR' and p.get('ym') == ym):
        fails.append(f'price body: {posted}')
    # 429 on a fresh card
    mode['v'] = '429'
    page.evaluate("([p, c]) => BVWorldMap.openCard(p, c, null)", [pid, ll])
    page.wait_for_selector('#wm-card [data-paid]:not([disabled])')
    page.click('#wm-card [data-paid]')
    page.fill('#wm-pa', str(tariff['dc']).replace('.', ',' if lang != 'en' else '.'))
    page.select_option('#wm-pc', 'EUR')
    page.click('#wm-pff button[type="submit"]')
    page.wait_for_function("() => document.querySelector('#wm-pff .wm-rmsg').textContent === JSON.parse(document.getElementById('wm-i18n').textContent).ci_err_limit", timeout=5000)
    # demo mode: nothing requested
    n0 = len(posted) + len(got)
    page.goto(base + '/demo' + PAGES[lang] + f'#12/{ll[1]}/{ll[0]}', wait_until='load')
    if not WT.wait_ready(page):
        fails.append('demo map not ready')
    else:
        page.evaluate("([p, c]) => BVWorldMap.openCard(p, c, null)", [pid, ll])
        page.wait_for_selector('#wm-card [data-ci="zauzeto"]', timeout=10000)
        if page.text_content('#wm-cis') != T['ci_demo_note']:
            fails.append('demo note missing')
        page.click('#wm-card [data-ci="zauzeto"]')
        page.wait_for_function("() => document.getElementById('wm-cis').textContent === JSON.parse(document.getElementById('wm-i18n').textContent).ci_demo", timeout=5000)
        page.click('#wm-card [data-paid]')
        page.fill('#wm-pa', '0.5')
        page.click('#wm-pff button[type="submit"]')
        page.wait_for_selector('#wm-pf .wm-ok', timeout=5000)
        if T['ci_demo'] not in page.text_content('#wm-pf'):
            fails.append('demo price text missing')
        if len(posted) + len(got) != n0:
            fails.append('demo mode made a request')
        page.screenshot(path=str(out / f'{lang}-{w}-demo.png'))
        if bal:
            page.evaluate("([p, c]) => BVWorldMap.openCard(p, c, null)", [bal[0], bal[1]['ll']])
            page.wait_for_selector('#wm-card a.btn.dark', timeout=10000)
            if page.locator('#wm-card .wm-ci').count():
                fails.append('Balkan card has a check-in block')
    errs = [e for e in errors if 'ci.test.invalid' not in e and 'reports.test.invalid' not in e and '429' not in e]
    if errs:
        fails.append(f'{len(errs)} console error(s): ' + ' | '.join(errs[:3]))
    ctx.close()
    return fails


if __name__ == '__main__':
    sys.exit(main())
