# Site search in a real browser (docs/RUNBOOK.md 3.8): /pretraga/ in the three languages, the help blocks when nothing
# is found, „Niste našli šta tražite?“, the search-by-meaning block (fake /api), the home suggestions with the keyboard,
# no JS or CSP errors, phone and desktop screenshots. Needs a build and a local server:
#   python3 scripts/qa/cfserve.py dist 8787 &   then   python3 scripts/qa/pretraga_ui_test.py [/tmp/bv-search-shots]
import json, os, sys
from playwright.sync_api import sync_playwright

BASE = os.environ.get('BV_BASE', 'http://127.0.0.1:8787')
OUT = sys.argv[1] if len(sys.argv) > 1 else '/tmp/bv-search-shots'
os.makedirs(OUT, exist_ok=True)
fails, logged, asked = [], [], []


def check(ok, what):
    print(('ok   ' if ok else 'FAIL ') + what)
    if not ok:
        fails.append(what)


def fake_api(page, smisao=None):
    def handle(route):
        u = route.request.url
        if '/api/pretraga' in u:
            logged.append(json.loads(route.request.post_data or '{}'))
            return route.fulfill(status=200, content_type='application/json', body='{"ok":true}')
        if '/api/zahtev' in u:
            asked.append(json.loads(route.request.post_data or '{}'))
            return route.fulfill(status=200, content_type='application/json', body='{"ok":true}')
        if '/api/smisao' in u:
            return route.fulfill(status=200, content_type='application/json', body=json.dumps(smisao or {'ok': False, 'error': 'off'}))
        return route.fulfill(status=200, content_type='application/json', body='{"ok":true}')
    page.route('**/api/**', handle)


def errors_of(page):
    errs = []
    page.on('pageerror', lambda e: errs.append('pageerror: ' + str(e)))
    page.on('console', lambda m: errs.append('console: ' + m.text) if m.type == 'error' and 'favicon' not in m.text else None)
    return errs


def first_hit(page):
    page.wait_for_selector('#s-status:not(:text("Učitavanje…"))', timeout=15000)
    page.wait_for_timeout(300)
    a = page.query_selector('#s-results:not([hidden]) a.hit')
    return a.get_attribute('href') if a else None


with sync_playwright() as p:
    b = p.chromium.launch()
    for label, vp in (('phone', {'width': 390, 'height': 844}), ('desktop', {'width': 1440, 'height': 900})):
        ctx = b.new_context(viewport=vp, locale='sr-RS')
        page = ctx.new_page()
        errs = errors_of(page)
        fake_api(page)
        cases = [('/pretraga/?q=evolnako', '/firme/evolako/'), ('/pretraga/?q=kraljevo', '/gradovi/kraljevo/'),
                 ('/pretraga/?q=%D0%9D%D0%BE%D0%B2%D0%B8+%D0%A1%D0%B0%D0%B4', '/gradovi/novi-sad/'),
                 ('/ru/pretraga/?q=%D1%8D%D0%B2%D0%BE%D0%BB%D0%B0%D0%BA%D0%BE', '/ru/firme/evolako/'),
                 ('/en/pretraga/?q=volbox', '/en/wallbox-cena-srbija')]
        for path, want in cases:
            page.goto(BASE + path)
            got = first_hit(page)
            check(got == want, f'{label} {path}: first result {got}')
        # nothing found: the message, the help blocks and the question box; the box sends kind "pretraga" with the query
        page.goto(BASE + '/pretraga/?q=xyzqwv')
        first_hit(page)
        st = page.inner_text('#s-status')
        check('xyzqwv' in st and page.is_visible('#s-more') and page.is_visible('#s-ask') and not page.is_visible('#s-results'),
              f'{label} no results: status „{st}“, help blocks and the question box shown')
        check(page.locator('#s-more .row').count() == 6 and page.locator('#s-more .ncard').count() == 3, f'{label} 6 popular pages and 3 news')
        page.screenshot(path=f'{OUT}/pretraga-none-{label}.png', full_page=True)
        page.fill('#s-ask textarea', 'Tražim punjač za kamp prikolicu')
        page.wait_for_timeout(3100)               # the server refuses a form sent in under 3 s
        page.click('#s-ask [type=submit]')
        page.wait_for_selector('#s-ask [data-m=poslato]:not([hidden])', timeout=5000)
        check(bool(asked) and asked[-1]['kind'] == 'pretraga' and asked[-1]['data']['upit'] == 'xyzqwv', f'{label} question box sent: {asked[-1] if asked else None}')
        # the empty page: hint, help blocks, no question box
        page.goto(BASE + '/pretraga/')
        page.wait_for_selector('#s-status:not(:text("Učitavanje…"))')
        check(page.is_visible('#s-more') and not page.is_visible('#s-ask'), f'{label} empty search page: help blocks, no question box')
        # the search log: one line per query, without anything but the query, language and counts
        page.goto(BASE + '/pretraga/?q=subvencije')
        first_hit(page)
        page.click('#s-results a.hit >> nth=0')
        page.wait_for_timeout(800)
        keys = sorted({k for x in logged for k in x})
        check(any(x.get('q') == 'subvencije' and not x.get('c') for x in logged) and any(x.get('q') == 'subvencije' and x.get('c') == 1 for x in logged),
              f'{label} search log: the query and the opened result ({len(logged)} lines, fields {keys})')
        check(set(keys) <= {'q', 'l', 'n', 'w', 'c', 'f'}, f'{label} search log carries only q, l, n, w, c, f')
        # search by meaning (a fake answer): the block lists pages the words did not find
        page2 = ctx.new_page()
        e2 = errors_of(page2)
        fake_api(page2, {'ok': True, 'hits': [{'u': '/podaci/tarife-eps/', 's': 0.71}, {'u': '/alati/kalkulator-troskova/', 's': 0.66}]})
        page2.goto(BASE + '/pretraga/?q=gde+da+napunim+ako+parkiram+na+ulici')
        page2.wait_for_selector('#s-sim:not([hidden])', timeout=8000)
        n_sim = page2.locator('#s-sim a.hit').count()
        check(n_sim >= 1, f'{label} search by meaning: {n_sim} pages in „Slično po smislu“')
        page2.screenshot(path=f'{OUT}/pretraga-smisao-{label}.png', full_page=True)
        errs += e2
        page2.close()
        # home suggestions: type, see the list, arrows and Enter open the first page
        page.goto(BASE + '/')
        page.click('#home-q')
        page.keyboard.type('evol', delay=40)
        page.wait_for_selector('#home-sug:not([hidden]) .sug-i', timeout=8000)
        first = page.get_attribute('#home-sug .sug-i >> nth=0', 'href')
        check(first == '/firme/evolako/', f'{label} home suggestion for „evol“: {first}')
        page.screenshot(path=f'{OUT}/pocetna-predlozi-{label}.png')
        box = page.eval_on_selector('#home-sug', 'e => { const r = e.getBoundingClientRect(); return [r.left, r.right, r.top] }')
        inp = page.eval_on_selector('#home-q', 'e => { const r = e.getBoundingClientRect(); return [r.left, r.right, r.bottom] }')
        check(abs(box[0] - inp[0]) < 2 and abs(box[1] - inp[1]) < 2 and 0 <= box[2] - inp[2] < 12, f'{label} suggestions sit under the box: {box} vs {inp}')
        page.keyboard.press('ArrowDown')
        page.keyboard.press('Enter')
        page.wait_for_url('**/firme/evolako/', timeout=8000)
        check(True, f'{label} ArrowDown + Enter opened the first suggestion')
        page.goto(BASE + '/')
        page.click('#home-q')
        page.keyboard.type('xyzqwv', delay=20)
        page.wait_for_selector('#home-sug:not([hidden])', timeout=8000)
        check(page.is_visible('#home-sug .sug-none') and page.is_visible('#home-sug .sug-all'), f'{label} home: nothing found, „Svi rezultati“ still offered')
        page.keyboard.press('Escape')
        check(not page.is_visible('#home-sug'), f'{label} Escape closes the suggestions')
        page.goto(BASE + '/ru/')
        page.click('#home-q')
        page.keyboard.type('тесл', delay=40)
        page.wait_for_selector('#home-sug:not([hidden]) .sug-i', timeout=8000)
        t = page.inner_text('#home-sug')
        check('/ru/' in (page.get_attribute('#home-sug .sug-i >> nth=0', 'href') or '') and 'Все результаты' in t, f'{label} RU home suggestions: {t[:80]!r}')
        check(not errs, f'{label} no JS or CSP errors: {errs[:3]}')
        ctx.close()
    b.close()
print(f'search UI: {len(fails)} failed' if fails else 'search UI: all passed')
sys.exit(1 if fails else 0)
