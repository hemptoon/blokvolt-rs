# /admin/svet/ (K6): the moderation page for error reports from the world map. Serves static/ locally, answers
# /api/admin/svet and the world data (tiles.blokvolt.rs/world/) from fixtures, so nothing leaves the container.
# Checks: key from sessionStorage, groups, preselected map action, POST bodies (accept/postpone/reject/answered/undo),
# dimming, error message, escaping, short card + fallback, stats, no console errors, no horizontal overflow at 360/768/1440.
# Usage: python3 scripts/qa/svet_admin_ui_test.py [shots-dir]
import functools, http.server, json, socket, sys, threading, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2] / 'static'
SHOTS = Path(sys.argv[1] if len(sys.argv) > 1 else '/tmp/k6_admin_shots')
SHOTS.mkdir(parents=True, exist_ok=True)
NOW = int(time.time())
KEY = 'test-key-not-real'

QUEUE = {'ok': True, 'open': 6, 'groups': [
    {'pid': 123456, 'cc': 'DE', 'g': 'u33dc0bcd', 'n': 3, 'types': {'ne_postoji': 2, 'ne_radi': 1}, 'first': NOW - 5 * 86400, 'last': NOW - 3600,
     'reports': [
         {'id': 1, 'type': 'ne_postoji', 'text': 'Nema punjača <b>x</b> & "y"', 'lat': None, 'lon': None, 'email': 'vozac@example.org', 'lang': 'sr', 'created_at': NOW - 5 * 86400, 'status': 'new'},
         {'id': 2, 'type': 'ne_postoji', 'text': None, 'lat': None, 'lon': None, 'email': None, 'lang': 'en', 'created_at': NOW - 86400, 'status': 'new'},
         {'id': 3, 'type': 'ne_radi', 'text': 'Broken since May', 'lat': None, 'lon': None, 'email': None, 'lang': 'en', 'created_at': NOW - 3600, 'status': 'postponed'}]},
    {'pid': 222, 'cc': 'FR', 'n': 2, 'types': {'lokacija': 2}, 'first': NOW - 7200, 'last': NOW - 600,
     'reports': [
         {'id': 4, 'type': 'lokacija', 'text': 'Na drugoj strani parkinga', 'lat': 48.856613, 'lon': 2.352222, 'email': None, 'lang': 'sr', 'created_at': NOW - 7200, 'status': 'new'},
         {'id': 5, 'type': 'lokacija', 'text': '', 'lat': 48.856701, 'lon': 2.352301, 'email': None, 'lang': 'ru', 'created_at': NOW - 600, 'status': 'new'}]},
    {'pid': 333, 'cc': None, 'g': 'zzzzz', 'n': 1, 'types': {'nije_javni': 1}, 'first': NOW - 300, 'last': NOW - 300,
     'reports': [{'id': 6, 'type': 'nije_javni', 'text': 'Samo za goste hotela', 'lat': None, 'lon': None, 'email': None, 'lang': 'sr', 'created_at': NOW - 300, 'status': 'new'}]},
], 'auto': [
    {'pid': 444, 'cc': 'IT', 'g': 'sr2yk', 'n': 2, 'types': {'ne_postoji': 2}, 'first': NOW - 9 * 86400, 'last': NOW - 8 * 86400,
     'reports': [{'id': 7, 'type': 'ne_postoji', 'text': None, 'lat': None, 'lon': None, 'email': None, 'lang': 'en', 'created_at': NOW - 9 * 86400, 'status': 'auto_hidden', 'rule': 'hide_2_reports'},
                 {'id': 8, 'type': 'ne_postoji', 'text': None, 'lat': None, 'lon': None, 'email': None, 'lang': 'en', 'created_at': NOW - 8 * 86400, 'status': 'auto_hidden', 'rule': 'hide_2_reports'}]}]}
STATS = {'ok': True, 'from': NOW - 30 * 86400, 'to': NOW, 'total': 41,
         'by_type': {'ne_postoji': 20, 'ne_radi': 9, 'lokacija': 7, 'snaga': 3, 'nije_javni': 1, 'drugo': 1},
         'by_status': {'new': 6, 'auto_hidden': 12, 'accepted': 10, 'rejected': 13},
         'by_country': [{'cc': 'C%02d' % i, 'n': 40 - i} for i in range(20)],
         'by_lang': {'en': 30, 'sr': 8, 'ru': 3},
         'auto_hidden': [{'pid': 444, 'cc': 'IT', 'decided_at': NOW - 8 * 86400, 'n': 2}, {'pid': 445, 'cc': 'ES', 'decided_at': NOW - 86400, 'n': 3}],
         'decided_by': {'auto': 25, 'admin': 10}}
WORLD = {
    'latest.json': {'date': '2026-11-08', 'manifest': '2026-11-08/manifest.json'},
    '2026-11-08/manifest.json': {'cards_base': '2026-11-08/cards', 'cards_split': ['u33']},
    '2026-11-08/cards/u33d.json': {'sites': {'123456': {'n': 'Rewe Parkplatz', 'net': 'EnBW', 'kw': 150, 'dc': 2, 'acc': 'public', 'conf': 55,
                                                        'src': [{'k': 'osm'}, {'k': 'ocm'}]}}},
    '2026-11-08/cards/zzz.json': {'sites': {}},   # pid 333 is not in its card file → fallback
}

fails, oks = [], []


def check(ok, what, extra=''):
    print(('ok   ' if ok else 'FAIL ') + what + (('  ' + str(extra)) if not ok and extra != '' else ''))
    (oks if ok else fails).append(what)


def free_port():
    s = socket.socket(); s.bind(('127.0.0.1', 0)); p = s.getsockname()[1]; s.close(); return p


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def main():
    port = free_port()
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', port), functools.partial(Quiet, directory=str(ROOT)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = 'http://127.0.0.1:%d' % port
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            for w in (1440, 768, 360):
                run(b, base, w)
            b.close()
    finally:
        srv.shutdown()
    print('%d ok, %d FAIL' % (len(oks), len(fails)))
    sys.exit(1 if fails else 0)


def run(b, base, w):
    full = w == 1440
    ctx = b.new_context(viewport={'width': w, 'height': 900})
    ctx.add_init_script("try{sessionStorage.setItem('bvkey'," + json.dumps(KEY) + ")}catch(e){}")
    pg = ctx.new_page()
    errs, posts, gets, world = [], [], [], []
    pg.on('pageerror', lambda e: errs.append('JS ' + str(e)[:200]))
    pg.on('console', lambda m: errs.append(m.type + ' ' + m.text[:200]) if m.type == 'error' else None)

    def api(route):
        rq = route.request
        if rq.method == 'POST':
            body = json.loads(rq.post_data or '{}')
            posts.append({'body': body, 'auth': rq.headers.get('authorization', '')})
            if body.get('pid') == 333:
                return route.fulfill(status=200, content_type='application/json', body='{"ok":false,"error":"test_fail"}')
            return route.fulfill(status=200, content_type='application/json', body='{"ok":true,"n":1}')
        gets.append({'url': rq.url, 'auth': rq.headers.get('authorization', '')})
        data = STATS if 'view=stats' in rq.url else QUEUE
        route.fulfill(status=200, content_type='application/json', body=json.dumps(data))

    def tiles(route):
        path = route.request.url.split('/world/', 1)[1].split('?')[0]
        world.append(path)
        if path in WORLD:
            return route.fulfill(status=200, content_type='application/json', body=json.dumps(WORLD[path]),
                                 headers={'access-control-allow-origin': '*'})
        route.fulfill(status=200, content_type='application/json', body='{}', headers={'access-control-allow-origin': '*'})

    pg.route('**/api/admin/svet**', api)
    pg.route('https://tiles.blokvolt.rs/world/**', tiles)
    pg.goto(base + '/admin/svet/')
    pg.wait_for_selector('#queue .card', timeout=10000)
    t = '[%d] ' % w

    check(pg.input_value('#key') == KEY, t + 'key taken from sessionStorage')
    check(gets and 'view=queue' in gets[0]['url'] and gets[0]['auth'] == 'Bearer ' + KEY, t + 'GET queue with Bearer key', gets[:1])
    cards = pg.locator('#queue > .card')
    check(cards.count() == 3, t + '3 groups rendered', cards.count())
    check(pg.locator('#auto > .card').count() == 1, t + '1 auto item rendered')
    sel = [cards.nth(i).locator('select.act').input_value() for i in range(3)]
    check(sel == ['hide', 'move', 'access'], t + 'preselected actions hide/move/access', sel)
    check(pg.locator('#queue b:text-is("x")').count() == 0 and pg.locator('#queue .txt b').count() == 0, t + 'report text escaped (no <b> element)')
    check('<b>x</b> & "y"' in cards.nth(0).inner_text(), t + 'escaped text shown literally')
    c0 = cards.nth(0).inner_text()
    check('Ne postoji × 2' in c0 and 'Ne radi × 1' in c0 and 'DE' in c0, t + 'types with counts and cc', c0[:200])
    check('vozac@example.org' in c0 and 'ostavljena za odgovor' in c0, t + 'e-mail shown and marked')
    check(cards.nth(0).locator('button.ans').count() == 1 and cards.nth(1).locator('button.ans').count() == 0, t + '„Odgovoreno“ only where an e-mail exists')
    href = cards.nth(0).locator('a:text("Otvori na mapi")').get_attribute('href')
    rel = cards.nth(0).locator('a:text("Otvori na mapi")').get_attribute('rel')
    check(href == 'https://blokvolt.com/map/?id=123456' and rel == 'noopener', t + 'map link', (href, rel))
    osm = cards.nth(1).locator('a:text("OSM")').first.get_attribute('href')
    check(osm == 'https://www.openstreetmap.org/?mlat=48.856613&mlon=2.352222#map=19/48.856613/2.352222', t + 'OSM link for proposed point', osm)

    # short cards: lazy (scroll each into view)
    for i in range(3):
        cards.nth(i).locator('.kart').scroll_into_view_if_needed()
    pg.wait_for_function("[].every.call(document.querySelectorAll('#queue .kart'), function(k){return k.textContent.indexOf('učitava')<0})", timeout=10000)
    k = [cards.nth(i).locator('.kart').inner_text() for i in range(3)]
    check('Rewe Parkplatz' in k[0] and 'EnBW' in k[0] and '150' in k[0] and 'osm, ocm' in k[0] and 'conf: 55' in k[0], t + 'card from world data rendered', k[0])
    check(k[1] == 'Kartica nije dostupna (otvorite mapu)', t + 'no g → fallback', k[1])
    check(k[2] == 'Kartica nije dostupna (otvorite mapu)', t + 'pid missing in card file → fallback', k[2])
    check(world.count('latest.json') == 1 and world.count('2026-11-08/manifest.json') == 1, t + 'manifest fetched once (cached)', world)
    check('2026-11-08/cards/u33d.json' in world and '2026-11-08/cards/zzz.json' in world, t + 'card file prefix via cards_split (u33 split → u33d, zzz not split → zzz)', world)

    if full:
        cards.nth(0).locator('button.ans').click()
        pg.wait_for_function("document.querySelector('#queue .card .ans').disabled")
        check(posts[-1]['body'] == {'pid': 123456, 'a': 'answered'} and posts[-1]['auth'] == 'Bearer ' + KEY, t + 'Odgovoreno → answered', posts[-1:])
        check('vozac@example.org' not in cards.nth(0).inner_text(), t + 'e-mail hidden after Odgovoreno')
        cards.nth(0).locator('button.ok').click()
        pg.wait_for_function("document.querySelector('#queue .card').style.opacity !== ''")
        check(posts[-1]['body'] == {'pid': 123456, 'a': 'accept', 'action': 'hide'}, t + 'Prihvati → accept + action', posts[-1:])
        op = pg.evaluate("getComputedStyle(document.querySelector('#queue .card')).opacity")
        dis = pg.evaluate("[].every.call(document.querySelectorAll('#queue .card:first-child button'), function(b){return b.disabled})")
        check(float(op) < 0.5 and dis, t + 'accepted card dimmed, buttons disabled', (op, dis))
        cards.nth(1).locator('select.act').select_option('none')
        cards.nth(1).locator('button.later').click()
        pg.wait_for_function("document.querySelectorAll('#queue .card')[1].style.opacity !== ''")
        check(posts[-1]['body'] == {'pid': 222, 'a': 'postpone'}, t + 'Odloži → postpone', posts[-1:])
        cards.nth(2).locator('button.no').click()
        pg.wait_for_function("document.getElementById('msg').textContent.length > 0")
        check(posts[-1]['body'] == {'pid': 333, 'a': 'reject'}, t + 'Odbij → reject', posts[-1:])
        check('test_fail' in pg.inner_text('#msg') and pg.evaluate("document.querySelectorAll('#queue .card')[2].style.opacity") == '', t + 'error shown in #msg, card not dimmed')
        pg.locator('#auto .card button').click()
        pg.wait_for_function("document.querySelector('#auto .card').style.opacity !== ''")
        check(posts[-1]['body'] == {'pid': 444, 'a': 'undo'}, t + 'Poništi → undo', posts[-1:])
        check('hide_2_reports' in pg.inner_text('#auto') and 'automatski sakriveno' in pg.inner_text('#auto'), t + 'auto item shows status and rule')
        check(len(posts) == 5, t + 'exactly 5 POSTs', len(posts))

    pg.select_option('#sdays', '30')
    pg.click('#loadS')
    pg.wait_for_selector('#stats table', timeout=10000)
    check(any('view=stats&days=30' in g['url'] for g in gets), t + 'GET stats days=30', [g['url'] for g in gets])
    st = pg.inner_text('#stats')
    check('prijava 41' in st and 'Ne postoji' in st and 'automatski sakriveno mesta 2' in st, t + 'stats totals, types, auto-hidden', st[:200])
    ccs = pg.locator('#stats table').nth(2).locator('tr').count() - 1
    check(ccs == 15, t + 'top 15 countries', ccs)
    check('čovek' in st and '25' in st, t + 'decided_by shown')
    check(pg.locator('a[href="/admin/"]').count() == 1, t + 'link back to /admin/')
    check(pg.locator('meta[name=robots][content*=noindex]').count() == 1, t + 'noindex meta')

    pg.wait_for_timeout(200)
    ov = pg.evaluate("[document.scrollingElement.scrollWidth, innerWidth]")
    check(ov[0] <= ov[1] + 1, t + 'no horizontal overflow', ov)
    pg.screenshot(path=str(SHOTS / ('svet_admin_%d.png' % w)), full_page=True)
    check(not errs, t + 'no console errors', errs[:3])
    ctx.close()


if __name__ == '__main__':
    main()
