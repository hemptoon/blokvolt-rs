# Accounts ("Moj BlokVolt") and the newsletter (Nedeljni pregled) in a real browser, against the built site with the
# real worker: scripts/qa/nalog_serve.mjs (dist/ like Cloudflare Pages, dist/_headers, worker in Miniflare with D1 and
# MAIL_MODE=log — codes and links are read from its /__dev/mail). Build with both features on first:
#   BV_QA_ACCOUNTS=1 BV_QA_PREGLED=1 python3 build.py
#   MINIFLARE_DIR=/tmp/mf node scripts/qa/nalog_serve.mjs dist 8788 &
#   python3 scripts/qa/nalog_ui_test.py [shots-dir]
# Flows: sign-in by code (desktop) and by the mail's one-click link (phone: the page signs in only on its button),
# stars on /mapa/ synced to the account and shown in /nalog/, a report from the map listed under "Moje prijave",
# settings, the newsletter in the account, sign-up on /pregled/ → confirmation (only the button confirms) → preferences
# → unsubscribe → sign up again, deleting the account; the layout of the signed-in page (desktop columns, phone order)
# and the code field on the phone. Every page: no JS or CSP errors, no horizontal overflow at 360, 768 and 1440 px.
# Screenshots and the rendered e-mails (SR/EN/RU) go to shots-dir.
import asyncio, json, os, random, re, sys, time, urllib.request
from pathlib import Path
from playwright.async_api import async_playwright

BASE = os.environ.get('BV_BASE', 'http://127.0.0.1:8788')
SHOTS = Path(sys.argv[1] if len(sys.argv) > 1 else '/tmp/bv-nalog')
SHOTS.mkdir(parents=True, exist_ok=True)
(SHOTS / 'mail').mkdir(exist_ok=True)
RUN = str(int(time.time()))[-6:]
IP = f'10.{random.randint(0, 250)}.{random.randint(0, 250)}.{random.randint(1, 250)}'   # the rate limits start fresh
STYLE = {"version": 8, "sources": {}, "glyphs": "https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf",
         "layers": [{"id": "bg", "type": "background", "paint": {"background-color": "#e9ecef"}}]}
FAVS = ['ocm-279311', 'ocm-287963', 'ocm-150105']     # BIG Karaburma (CCS2), BIG Inđija, Tesla Beograd
fails, errors = [], []


def check(cond, what):
    print(('ok   ' if cond else 'FAIL ') + what)
    if not cond:
        fails.append(what)


def dev_mail(to, kind):
    with urllib.request.urlopen(f'{BASE}/__dev/mail?to={urllib.request.quote(to)}&kind={kind}') as r:
        return json.loads(r.read().decode())


def mail_count(to, kind):
    with urllib.request.urlopen(f'{BASE}/__dev/mails') as r:
        return sum(1 for m in json.loads(r.read().decode()) if m['to_addr'] == to and m['kind'] == kind)


async def new_mail(to, kind, before, timeout=8):
    """The mail an action sends: /api/nalog/kod and /api/posta/prijava answer first and send it right after."""
    end = time.time() + timeout
    while time.time() < end:
        if mail_count(to, kind) > before:
            return dev_mail(to, kind)
        await asyncio.sleep(0.1)
    raise TimeoutError(f'no new {kind} mail to {to}')


async def stanje(pg, tok, want=None, timeout=6):
    """The newsletter state by token (waiting for `want`: a sign-up is written right after the answer)."""
    end = time.time() + timeout
    while True:
        st = json.loads(await pg.evaluate(f"fetch('/api/posta/stanje?t={tok}').then(r => r.text())"))
        if want is None or st.get('status') == want or time.time() > end:
            return st
        await asyncio.sleep(0.1)


def ls(pg, key):
    return pg.evaluate(f"localStorage.getItem('{key}')")


async def wait_js(pg, expr, timeout=8000):
    """Poll a condition in the page. (Playwright's wait_for_function compiles it with eval, which the site's CSP blocks.)"""
    end = time.time() + timeout / 1000
    while time.time() < end:
        if await pg.evaluate(f'() => !!({expr})'):
            return
        await pg.wait_for_timeout(100)
    raise TimeoutError('timed out waiting for: ' + expr)


async def new_page(b, w, lang_tag='', ip=None):
    ctx = await b.new_context(viewport={'width': w, 'height': 900 if w > 900 else 844}, extra_http_headers={'x-qa-ip': ip or IP},
                              permissions=['clipboard-read', 'clipboard-write'])
    pg = await ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(f'{w}{lang_tag} JS {str(e)[:200]}'))
    pg.on('console', lambda m: errors.append(f'{w}{lang_tag} {m.type} {m.text[:200]}')
          if m.type == 'error' and ('Content Security Policy' in m.text or 'openfreemap' not in m.text) and 'Failed to load resource' not in m.text else None)
    await pg.route('https://tiles.openfreemap.org/styles/**', lambda r: r.fulfill(status=200, content_type='application/json', body=json.dumps(STYLE)))
    await pg.route('https://tiles.openfreemap.org/fonts/**', lambda r: r.fulfill(status=200, content_type='application/x-protobuf', body=b''))
    return ctx, pg


async def overflow(pg, what):
    r = await pg.evaluate('''() => ({sw: document.documentElement.scrollWidth, iw: innerWidth,
      wide: [...document.querySelectorAll('main *')].filter(e => e.getBoundingClientRect().right > innerWidth + 1 && getComputedStyle(e).position !== 'fixed')
        .slice(0, 3).map(e => e.tagName + '.' + (e.className || '').toString().slice(0, 30))})''')
    check(r['sw'] <= r['iw'] + 1 and not r['wide'], f'{what}: no horizontal overflow {r["wide"] if r["wide"] else ""}')


async def widths(pg, what, ws=(360, 768, 1440)):
    """The page as it is now, at three widths (the viewport changes, the state stays)."""
    size = pg.viewport_size
    for w in ws:
        await pg.set_viewport_size({'width': w, 'height': 900})
        await pg.wait_for_timeout(150)
        await overflow(pg, f'{what} @{w}')
    await pg.set_viewport_size(size)


async def shot(pg, name):
    # from the top (the sticky header would land mid-page), without a passing toast or a hover state
    await pg.mouse.move(0, 0)
    await pg.evaluate("() => { scrollTo(0, 0); const t = document.getElementById('nl-toast'); if (t) t.hidden = true; }")
    await pg.wait_for_timeout(250)
    await pg.screenshot(path=str(SHOTS / f'{name}.png'), full_page=True)


async def sign_in_by_code(pg, email, lang='', optin=False, shots=None):
    await pg.goto(f'{BASE}{lang}/nalog/', wait_until='load')
    await pg.wait_for_timeout(400)
    if shots:
        await shot(pg, shots + '-odjavljen')
    await pg.fill('#nl-mail', email)
    if optin:
        await pg.check('#nl-optin')
    before = mail_count(email, 'code')
    await pg.click('#nl-f-mail [type=submit]')
    await pg.wait_for_selector('#nl-f-code:not([hidden])', timeout=8000)
    focused = await pg.evaluate('document.activeElement && document.activeElement.id')
    check(focused == 'nl-code', f'{lang or "sr"}: code step, the code field has the focus')
    if shots:
        await shot(pg, shots + '-kod')
    m = await new_mail(email, 'code', before)
    code = m['subject'][:6]
    await pg.fill('#nl-code', code[:3] + ' ' + code[3:])          # typed with a space: still six digits, sent by itself
    await pg.wait_for_selector('html.nl-in', timeout=8000)
    await pg.wait_for_timeout(600)
    return m


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'])
        email = f'vozac.{RUN}@example.com'

        # ---------------------------------------------------------------- desktop, Serbian: sign-in by code
        ctx, pg = await new_page(b, 1440)
        await pg.goto(f'{BASE}/nalog/', wait_until='load')
        check(await pg.evaluate("!document.documentElement.classList.contains('nl-in')"), 'no cookie: the sign-in form, no skeleton')
        await widths(pg, '/nalog/ signed out')
        await pg.fill('#nl-mail', 'nije-adresa')
        await pg.click('#nl-f-mail [type=submit]')
        check('ispravnu e-mail adresu' in await pg.inner_text('#nl-msg-mail'), 'invalid address: "Upišite ispravnu e-mail adresu."')
        mail = await sign_in_by_code(pg, email, shots='nalog-sr-1440')
        check(await pg.inner_text('.nl-who') == email, 'signed in: the address in the head')
        check(await pg.evaluate("document.activeElement && document.activeElement.id") == 'nl-h1', 'signed in: focus on the heading')
        ck = {c['name']: c for c in await ctx.cookies()}
        check('bv_s' in ck and ck['bv_s']['httpOnly'] and ck['bv_s']['path'] == '/api' and ck['bv_in']['value'] == '1' and not ck['bv_in']['httpOnly'],
              'cookies: bv_s HttpOnly Path=/api, bv_in=1 readable')
        check(await pg.evaluate("document.querySelector('#nl-favs-none').hidden === false"), 'no favourites yet: the empty text')
        owner = json.loads(await pg.evaluate("fetch('/api/nalog/ja').then(r => r.text())"))['user']['owner']
        check(await ls(pg, 'bv:fav-owner') == owner and await pg.is_hidden('#nl-ask'), 'nothing in this browser yet: no question, the list belongs to the account (bv:fav-owner)')
        await widths(pg, '/nalog/ signed in (empty)')

        # ---- stars on the map go to the account (the map asks /api/nalog/ja once, then posts every star)
        posts = []
        pg.on('request', lambda r: posts.append((r.url, r.post_data)) if r.method == 'POST' and '/api/nalog/' in r.url else None)
        for i, sid in enumerate(FAVS):
            async with pg.expect_response(lambda r: '/api/nalog/ja' in r.url):
                await pg.goto('about:blank')
                await pg.goto(f'{BASE}/mapa/#{sid}', wait_until='load')
            await pg.wait_for_selector('.ccard .fav', timeout=8000)
            await pg.wait_for_timeout(300)
            await pg.click('.ccard .fav')
            await pg.wait_for_timeout(500)
            if i == 0:
                # a report from the map while signed in: "Moje prijave sa mape"
                await pg.click('.rv [data-ci="ok"]')
                await pg.click('.rv-stars [data-r="4"]')
                await pg.fill('#rv-c', 'Radi, oba mesta slobodna.')
                await pg.wait_for_timeout(2700)
                await pg.click('.rv-form [type=submit]')
                await pg.wait_for_timeout(800)
                check('Hvala' in await pg.inner_text('.rv-msg'), 'map: report sent while signed in')
        adds = [json.loads(d) for u, d in posts if u.endswith('/api/nalog/omiljeni') and d]
        check(sum(1 for a in adds if a.get('add')) == 3, f'map: each star posted to the account ({len(adds)} posts)')
        ja = json.loads(await pg.evaluate("fetch('/api/nalog/ja').then(r => r.text())"))
        check(sorted(ja['favs']) == sorted(FAVS), f'account favourites = the three stars: {ja["favs"]}')
        check(sorted(json.loads(await pg.evaluate("localStorage.getItem('bv:fav')"))) == sorted(FAVS), 'localStorage bv:fav keeps the same list (offline copy)')

        # ---- /nalog/ with 3 favourites and the report
        await pg.goto(f'{BASE}/nalog/', wait_until='load')
        await wait_js(pg, "document.querySelectorAll('#nl-favs .nl-st').length === 3 && document.querySelectorAll('#nl-ci .nl-ci').length >= 1", timeout=10000)
        fav_text = await pg.inner_text('#nl-favs')
        check('BIG Beograd Karaburma' in fav_text and 'Tesla Supercharger Beograd' in fav_text and 'Na mapi' in fav_text, '/nalog/: three favourites with names and "Na mapi"')
        check('(3)' in await pg.inner_text('#nl-fav-h'), '/nalog/: "Omiljeni punjači (3)"')
        ci_text = await pg.inner_text('#nl-ci')
        check('BIG Beograd Karaburma' in ci_text and 'Radi' in ci_text and 'Objavljeno' in ci_text, f'/nalog/: the report with status and comment state ({ci_text[:80]!r})')
        check(await pg.evaluate("document.querySelector('#nl-favs a.btn').getAttribute('href')") == '/mapa/#ocm-279311', '"Na mapi" opens the station on the map')

        # ---- settings: car, DC, Tesla, city
        await pg.select_option('#nl-model', 'BYD Dolphin Surf')
        await pg.check('#nl-f-car [name=dc][value=ccs2]')
        await pg.check('#nl-tesla')
        await pg.select_option('#nl-city', 'novi-sad')
        await pg.click('#nl-f-car [type=submit]')
        await pg.wait_for_selector('#nl-toast:not([hidden])', timeout=5000)
        check(await pg.inner_text('#nl-toast') == 'Sačuvano', 'settings: toast "Sačuvano"')
        check(await pg.evaluate("localStorage.getItem('bv:tesla')") == '1', 'settings: "Imam Teslu" also in localStorage for the map')
        await pg.select_option('#nl-model', '*')
        check(await pg.is_visible('#nl-other'), '"Drugi model" shows the text field')
        await pg.fill('#nl-other', 'Tesla Model 3 Long Range')
        await pg.click('#nl-f-car [type=submit]')
        await pg.wait_for_timeout(700)
        await pg.reload(wait_until='load')
        await wait_js(pg, "document.getElementById('nl-city').value === 'novi-sad'", timeout=8000)
        st = await pg.evaluate("({m: document.getElementById('nl-model').value, o: document.getElementById('nl-other').value, dc: (document.querySelector('#nl-f-car [name=dc]:checked')||{}).value, t: document.getElementById('nl-tesla').checked})")
        check(st == {'m': '*', 'o': 'Tesla Model 3 Long Range', 'dc': 'ccs2', 't': True}, f'settings kept after reload: {st}')
        # the map marks the connector of the reader's car
        await pg.goto(f'{BASE}/mapa/#ocm-279311', wait_until='load')
        await pg.wait_for_selector('.ccard .cbox b.mine', timeout=8000)
        check('vaš auto' in await pg.inner_text('.ccard .cbox b.mine'), 'map card: CCS2 marked "vaš auto"')
        check(await pg.evaluate("document.querySelector('#mchips [data-f=tesla]').getAttribute('aria-pressed')") == 'true', 'map: "Imam Teslu" from the account')

        # ---- the newsletter in the account
        await pg.goto(f'{BASE}/nalog/', wait_until='load')
        await pg.wait_for_selector('html.nl-in #nl-favs .nl-st', timeout=8000)
        check(await pg.evaluate("document.querySelector('#nl-pg-topics').disabled"), 'newsletter off: its settings are disabled')
        wel = mail_count(email, 'welcome')
        await pg.check('#nl-pg-on')
        await wait_js(pg, "!document.querySelector('#nl-pg-st [data-st=on]').hidden", timeout=5000)
        check('Uključen' in await pg.inner_text('#nl-pg-st'), 'account: newsletter on at once ("Uključen — stiže petkom ujutru")')
        check(await new_mail(email, 'welcome', wel) is not None, 'account: welcome mail sent')
        await pg.uncheck('#nl-pg-topics input[value=punjaci]')
        await pg.wait_for_timeout(500)
        ja = json.loads(await pg.evaluate("fetch('/api/nalog/ja').then(r => r.text())"))
        check(ja['sub']['status'] == 'on' and 'punjaci' not in ja['sub']['topics'], f'account: topics saved {ja["sub"]}')
        lay = await pg.evaluate('''() => { const x = k => document.querySelector('.nl-s-' + k).getBoundingClientRect().left;
          return {left: ['fav', 'ci', 'acc'].every(k => x(k) === x('fav')), right: ['car', 'pg'].every(k => x(k) === x('car')) && x('car') > x('fav'),
            cols: [...document.querySelectorAll('.nl-grid > .nl-col')].map(c => Math.round(c.getBoundingClientRect().height))}; }''')
        check(lay['left'] and lay['right'], f'desktop: Omiljeni, Moje prijave, Nalog on the left; Moj auto, Nedeljni pregled on the right (column heights {lay["cols"]})')
        await shot(pg, 'nalog-sr-1440-prijavljen')
        await widths(pg, '/nalog/ signed in (3 favourites, report, settings)')
        # the delete dialog
        await pg.click('#nl-del')
        await pg.wait_for_timeout(300)
        check(await pg.evaluate("document.getElementById('nl-dlg').open"), 'delete: native dialog open')
        check(await pg.evaluate("document.activeElement.id") == 'nl-del-no', 'delete: focus on "Otkažite"')
        await pg.screenshot(path=str(SHOTS / 'nalog-sr-1440-brisanje.png'))
        await pg.keyboard.press('Escape')
        await pg.wait_for_timeout(200)
        check(not await pg.evaluate("document.getElementById('nl-dlg').open"), 'delete: Escape closes the dialog')

        # ---------------------------------------------------------------- phone, Serbian: the one-click link from the mail
        ctx2, pg2 = await new_page(b, 390)
        await pg2.goto(f'{BASE}/nalog/', wait_until='load')
        await shot(pg2, 'nalog-sr-390-odjavljen')
        await pg2.fill('#nl-mail', email)
        before = mail_count(email, 'code')
        await pg2.click('#nl-f-mail [type=submit]')
        await pg2.wait_for_selector('#nl-f-code:not([hidden])', timeout=8000)
        phone_mail = await new_mail(email, 'code', before)
        otp = await pg2.evaluate('''() => { const i = document.getElementById('nl-code'), b = document.querySelector('#nl-f-code [type=submit]'), cs = getComputedStyle(i);
          return {iw: Math.round(i.getBoundingClientRect().width), bw: Math.round(b.getBoundingClientRect().width), fs: parseFloat(cs.fontSize),
            tab: cs.fontVariantNumeric, ls: parseFloat(cs.letterSpacing)}; }''')
        check(otp['iw'] == otp['bw'] and otp['fs'] >= 16 and 'tabular-nums' in otp['tab'] and otp['ls'] > 0,
              f'phone: the code field as wide as the button, digits {otp["fs"]:.0f} px (no iOS zoom), tabular, spaced ({otp})')
        await pg2.fill('#nl-code', '4821')                              # four digits: how they look (sent only at six)
        await shot(pg2, 'nalog-sr-390-kod')
        await widths(pg2, '/nalog/ code step')
        link = re.search(r'(/nalog/\?prijava=[0-9a-f]{64})', phone_mail['html']).group(1)
        await pg2.goto(BASE + link, wait_until='load')
        await pg2.wait_for_selector('#nl-f-link:not([hidden])', timeout=8000)
        await wait_js(pg2, "document.querySelector('#nl-f-link [data-nl-link]').textContent.indexOf('***@') > 0", timeout=8000)
        check('prijava=' not in pg2.url, 'link: the token is removed from the address bar')
        check('Prijava na BlokVolt' in await pg2.inner_text('#nl-f-link') and 'v***@example.com' in await pg2.inner_text('#nl-f-link'),
              'link page: "Prijava na BlokVolt", the masked address and one button')
        await pg2.wait_for_timeout(1500)
        check(await pg2.evaluate("fetch('/api/nalog/ja').then(r => r.status)") == 401 and not any(c['name'] == 'bv_in' and c['value'] for c in await ctx2.cookies()),
              'link page: opening it signs nobody in (a scanner that runs the script spends nothing)')
        await shot(pg2, 'nalog-sr-390-link')
        await widths(pg2, '/nalog/ link card')
        await pg2.set_viewport_size({'width': 1440, 'height': 900})
        await shot(pg2, 'nalog-sr-1440-link')
        await pg2.set_viewport_size({'width': 390, 'height': 844})
        await pg2.click('#nl-f-link [type=submit]')
        await wait_js(pg2, "document.querySelectorAll('#nl-favs .nl-st').length === 3", timeout=10000)
        check(await pg2.evaluate("document.documentElement.classList.contains('nl-in')"), 'link page: the button signs in')
        order = await pg2.evaluate('''() => ['fav', 'car', 'pg', 'ci', 'acc'].map(k => [k, document.querySelector('.nl-s-' + k).getBoundingClientRect().top])
          .sort((a, b) => a[1] - b[1]).map(x => x[0]).join()''')
        check(order == 'fav,car,pg,ci,acc', f'phone: Omiljeni, Moj auto, Nedeljni pregled, Moje prijave, Nalog ({order})')
        check(sorted(json.loads(await pg2.evaluate("localStorage.getItem('bv:fav')"))) == sorted(FAVS), 'second device: the account favourites land in this browser too')
        await wait_js(pg2, "document.querySelectorAll('#nl-ci .nl-ci').length >= 1", timeout=8000)
        await shot(pg2, 'nalog-sr-390-prijavljen')
        await pg2.click('#nl-del')
        await pg2.wait_for_timeout(300)
        await pg2.screenshot(path=str(SHOTS / 'nalog-sr-390-brisanje.png'))
        await pg2.click('#nl-del-no')
        # a star removed on /nalog/ leaves the map's list too
        await pg2.click('#nl-favs .nl-st[data-id="ocm-287963"] .nl-star')
        await wait_js(pg2, "document.querySelectorAll('#nl-favs .nl-st').length === 2", timeout=5000)
        check('ocm-287963' not in json.loads(await pg2.evaluate("localStorage.getItem('bv:fav')")), 'remove on /nalog/: gone from localStorage as well')
        # "Odjavite se" on this device only
        await pg2.click('#nl-out')
        await pg2.wait_for_selector('html:not(.nl-in)', timeout=5000)
        check(not any(c['name'] == 'bv_in' and c['value'] for c in await ctx2.cookies()), 'sign out: bv_in removed')
        check(await pg2.evaluate("['bv:fav', 'bv:tesla', 'bv:fav-owner'].every(k => localStorage.getItem(k) === null)"),
              'sign out: the favourites, "Imam Teslu" and their owner are removed from this browser')
        await pg2.goto(BASE + link, wait_until='load')
        await pg2.wait_for_selector('#nl-f-mail:not([hidden])', timeout=8000)
        check('nije ispravan' in await pg2.inner_text('#nl-msg-top') and await pg2.is_hidden('#nl-f-link'), 'a used link: "Link za prijavu nije ispravan ili je istekao…" and the form')
        ja = await pg.evaluate("fetch('/api/nalog/ja').then(r => r.status)")
        check(ja == 200, 'sign out on the phone keeps the desktop signed in')

        # ---------------------------------------------------------------- a browser list from before the sign-in
        acct = sorted(json.loads(await pg.evaluate("fetch('/api/nalog/ja').then(r => r.text())"))['favs'])
        for answer, w in (('yes', 390), ('no', 1440)):
            c7, p7 = await new_page(b, w, ip=IP.rsplit('.', 1)[0] + '.' + ('201' if answer == 'yes' else '202'))
            await p7.goto(f'{BASE}/mapa/', wait_until='load')
            mine = ['ocm-150105', 'cg-65'] if answer == 'yes' else ['ocm-287963']
            await p7.evaluate(f"localStorage.setItem('bv:fav', JSON.stringify({json.dumps(mine)}))")
            await sign_in_by_code(p7, email)
            await p7.wait_for_selector('#nl-ask:not([hidden])', timeout=8000)
            q = await p7.inner_text('#nl-ask')
            want = 'U ovom pregledaču ima 2 omiljena punjača. Dodati ih u nalog?' if answer == 'yes' else 'U ovom pregledaču ima 1 omiljeni punjač. Dodati ga u nalog?'
            check(want in q and 'Dodajte' in q, f'unowned list in this browser: asked first ("{want}")')
            check(sorted(json.loads(await ls(p7, 'bv:fav'))) == sorted(mine) and await ls(p7, 'bv:fav-owner') is None, 'while asking: nothing joined, nothing sent')
            if answer == 'yes':
                await shot(p7, 'nalog-sr-390-pitanje')
                await widths(p7, '/nalog/ question card')
                await p7.click('#nl-ask-yes')
                await p7.wait_for_selector('#nl-ask[hidden]', state='attached', timeout=5000)
                ja7 = json.loads(await p7.evaluate("fetch('/api/nalog/ja').then(r => r.text())"))
                check(sorted(ja7['favs']) == sorted(set(acct) | set(mine)) and sorted(json.loads(await ls(p7, 'bv:fav'))) == sorted(ja7['favs']),
                      f'"Dodajte": the lists joined in the account and here ({len(ja7["favs"])})')
                acct = sorted(ja7['favs'])
            else:
                await p7.click('#nl-ask-no')
                await p7.wait_for_selector('#nl-ask[hidden]', state='attached', timeout=5000)
                ja7 = json.loads(await p7.evaluate("fetch('/api/nalog/ja').then(r => r.text())"))
                check(sorted(ja7['favs']) == acct and sorted(json.loads(await ls(p7, 'bv:fav'))) == acct, '"Ne": the account unchanged, this browser takes the account\'s list')
            check(await ls(p7, 'bv:fav-owner') == owner, 'after the answer the list belongs to the account')
            await c7.close()
        # a list that belongs to another account: replaced, never joined, no question
        c8, p8 = await new_page(b, 390, ip=IP.rsplit('.', 1)[0] + '.203')
        await p8.goto(f'{BASE}/mapa/', wait_until='load')
        await p8.evaluate("localStorage.setItem('bv:fav', JSON.stringify(['osm-n6797205414'])); localStorage.setItem('bv:fav-owner', 'ffffffffffffffff')")
        await sign_in_by_code(p8, email)
        await p8.wait_for_timeout(800)
        ja8 = json.loads(await p8.evaluate("fetch('/api/nalog/ja').then(r => r.text())"))
        check(await p8.is_hidden('#nl-ask') and sorted(ja8['favs']) == acct and sorted(json.loads(await ls(p8, 'bv:fav'))) == acct and await ls(p8, 'bv:fav-owner') == owner,
              "another account's list in this browser: replaced by this account's, not joined, no question")
        # the map with an unowned list and a session: leaves the list alone until /nalog/ has asked
        await p8.evaluate("localStorage.setItem('bv:fav', JSON.stringify(['osm-n6797205414'])); localStorage.removeItem('bv:fav-owner')")
        posts8 = []
        p8.on('request', lambda r: posts8.append(r.url) if r.method == 'POST' and '/api/nalog/' in r.url else None)
        async with p8.expect_response(lambda r: '/api/nalog/ja' in r.url):
            await p8.goto(f'{BASE}/mapa/', wait_until='load')
        await p8.wait_for_timeout(800)
        check(json.loads(await ls(p8, 'bv:fav')) == ['osm-n6797205414'] and not posts8, 'map, unowned list: nothing joined or sent before the question on /nalog/')
        await c8.close()

        # ---------------------------------------------------------------- English and Russian (phone)
        for lang in ('en', 'ru'):
            c3, p3 = await new_page(b, 390, lang)
            await sign_in_by_code(p3, email, lang=f'/{lang}')
            await wait_js(p3, "document.querySelectorAll('#nl-favs .nl-st').length >= 2", timeout=10000)
            await wait_js(p3, "document.querySelectorAll('#nl-ci .nl-ci').length >= 1", timeout=8000)
            t = await p3.inner_text('main')
            want = {'en': ('My BlokVolt', 'Favourite chargers', 'On the map'), 'ru': ('Мой BlokVolt', 'Избранные', 'На карте')}[lang]
            check(all(x in t for x in want), f'{lang}: signed-in page in {lang} ({[x for x in want if x not in t]})')
            href = await p3.evaluate("document.querySelector('#nl-favs a.btn').getAttribute('href')")
            check(href.startswith(f'/{lang}/mapa/#'), f'{lang}: "on the map" link keeps the language ({href})')
            await shot(p3, f'nalog-{lang}-390-prijavljen')
            await p3.goto(f'{BASE}/{lang}/pregled/', wait_until='load')
            await shot(p3, f'pregled-{lang}-390')
            await c3.close()

        # ---------------------------------------------------------------- the newsletter without an account
        for w in (1440, 390):
            c4, p4 = await new_page(b, w)
            n_email = f'citalac.{w}.{RUN}@example.com'
            await p4.goto(f'{BASE}/pregled/', wait_until='load')
            await shot(p4, f'pregled-sr-{w}')
            if w == 1440:
                await widths(p4, '/pregled/')
            await p4.fill('#pg-mail', n_email)
            await p4.click('.pg-main [type=submit]')
            await p4.wait_for_selector('.pg-main [data-m=ok]:not([hidden])', timeout=8000)
            check(n_email in await p4.inner_text('.pg-main [data-m=ok]'), f'/pregled/ @{w}: "Proverite inbox: … {n_email}"')
            conf = await new_mail(n_email, 'confirm', 0)
            check(conf and conf['subject'] == 'Potvrdite prijavu na Nedeljni pregled', f'@{w}: confirmation mail')
            url = re.search(r'(/pregled/potvrda/\?t=[0-9a-f]{32})', conf['html']).group(1)
            tok = url[-32:]
            await p4.goto(BASE + url, wait_until='load')
            await p4.wait_for_selector('[data-s=ask]:not([hidden])', timeout=8000)
            check('t=' not in p4.url, f'@{w}: potvrda — the token is taken out of the address bar')
            txt = await p4.inner_text('.pg-state')
            check('Potvrdite prijavu na Nedeljni pregled' in txt and 'c***@example.com' in txt and await p4.is_visible('#pg-yes'),
                  f'@{w}: potvrda — "Potvrdite prijavu na Nedeljni pregled", the masked address, the button')
            await p4.wait_for_timeout(1200)
            st = json.loads(await p4.evaluate(f"fetch('/api/posta/stanje?t={tok}').then(r => r.text())"))
            check(st['status'] == 'pending' and dev_mail(n_email, 'welcome') is None, f'@{w}: opening the link confirms nothing (still pending, no welcome mail)')
            await shot(p4, f'pregled-potvrda-sr-{w}')
            if w == 1440:
                await widths(p4, '/pregled/potvrda/ card')
            await p4.click('#pg-yes')
            await p4.wait_for_selector('[data-s=ok]:not([hidden])', timeout=8000)
            check('Prijava je potvrđena' in await p4.inner_text('.pg-state'), f'@{w}: the button — "Prijava je potvrđena. Prvi broj stiže u petak ujutru."')
            prefs = await p4.get_attribute('[data-nl-prefs]', 'href')
            check(prefs == '/pregled/odjava/', f'@{w}: the link to the preferences has no token in the page ({prefs})')
            await shot(p4, f'pregled-potvrda-ok-sr-{w}')
            if w == 1440:
                await widths(p4, '/pregled/potvrda/ ok')
            check(await new_mail(n_email, 'welcome', 0) is not None, f'@{w}: welcome mail after the click')
            await p4.click('[data-nl-prefs]')
            await p4.wait_for_selector('[data-s=on]:not([hidden])', timeout=8000)
            check('/pregled/odjava/' in p4.url and 't=' not in p4.url and await p4.evaluate("document.getElementById('pg-teme').open"),
                  f'@{w}: the click takes the token to the preferences (open), which take it out of the address bar again')
            await p4.goto(BASE + url, wait_until='load')
            await p4.wait_for_selector('[data-s=ok]:not([hidden])', timeout=8000)
            check(await p4.is_hidden('#pg-yes'), f'@{w}: the link again after confirming: "Prijava je potvrđena", no button')
            await p4.goto(f'{BASE}/pregled/odjava/?t={tok}', wait_until='load')
            await p4.wait_for_selector('[data-s=on]:not([hidden])', timeout=8000)
            check('c***@example.com' in await p4.inner_text('.pg-who') and 't=' not in p4.url, f'@{w}: odjava shows the masked address; no token in the address bar')
            await shot(p4, f'pregled-odjava-sr-{w}')
            if w == 1440:
                await widths(p4, '/pregled/odjava/ on')
                await p4.click('#pg-month')
                await p4.wait_for_selector('.pg-st [data-st=m]:not([hidden])', timeout=5000)
                check(await p4.is_hidden('#pg-month'), '"Radije jednom mesečno": monthly, the button goes')
                await p4.goto(f'{BASE}/pregled/odjava/?t={tok}&teme=1', wait_until='load')
                await p4.wait_for_selector('[data-s=on]:not([hidden])', timeout=8000)
                check(await p4.evaluate("document.getElementById('pg-teme').open"), '&teme=1 opens the topics')
                await p4.uncheck('#pg-f-teme input[value=vesti]')
                await p4.select_option('#pg-lang', 'en')
                await p4.click('#pg-f-teme [type=submit]')
                await p4.wait_for_selector('#nl-toast:not([hidden])', timeout=5000)
                st = json.loads(await p4.evaluate(f"fetch('/api/posta/stanje?t={tok}').then(r => r.text())"))
                check(st['topics'] == ['cene', 'punjaci'] and st['lang'] == 'en' and st['freq'] == 'm', f'topics, language saved: {st}')
            await p4.click('#pg-off')
            await p4.wait_for_selector('[data-s=off]:not([hidden])', timeout=5000)
            check('Odjavljeni ste' in await p4.inner_text('.pg-state'), f'@{w}: "Odjavljeni ste. Više vam nećemo slati Nedeljni pregled."')
            await shot(p4, f'pregled-odjavljen-sr-{w}')
            await p4.reload(wait_until='load')
            await p4.wait_for_selector('[data-s=off]:not([hidden])', timeout=8000)
            check(await p4.is_hidden('#pg-off'), f'@{w}: the unsubscribe page reloaded after unsubscribing: "Odjavljeni ste" (the token kept for this tab)')
            await p4.goto(f'{BASE}/pregled/odjava/?t={tok}&teme=1', wait_until='load')
            await p4.wait_for_selector('[data-s=off]:not([hidden])', timeout=8000)
            await p4.wait_for_timeout(300)
            check(not await p4.evaluate("document.getElementById('pg-teme').open"), f'@{w}: &teme=1 for an unsubscribed address: "Odjavljeni ste", the preferences stay closed')
            conf_n = mail_count(n_email, 'confirm')
            await p4.click('#pg-again')
            await p4.wait_for_selector('[data-s=again]:not([hidden])', timeout=8000)
            st = await stanje(p4, tok, 'pending')
            check(st['status'] == 'pending' and await new_mail(n_email, 'confirm', conf_n) is not None, f'@{w}: "Prijavite se ponovo" → pending, new confirmation mail')
            await p4.reload(wait_until='load')
            await p4.wait_for_selector('[data-s=on]:not([hidden])', timeout=8000)
            check(await p4.is_visible('.pg-st [data-st=pending]'), f'@{w}: the page of a sign-up waiting for confirmation: "Čeka potvrdu"')
            await c4.close()
        # the box under a news item (topic cene on /javno-punjenje/)
        c5, p5 = await new_page(b, 390)
        await p5.goto(f'{BASE}/javno-punjenje/', wait_until='load')
        box_email = f'cene.{RUN}@example.com'
        await p5.fill('#pgb-mail', box_email)
        await p5.click('.pg-box [type=submit]')
        await p5.wait_for_selector('.pg-box [data-m=ok]:not([hidden])', timeout=8000)
        conf = await new_mail(box_email, 'confirm', 0)
        tok = re.search(r'potvrda/\?t=([0-9a-f]{32})', conf['html']).group(1)
        st = json.loads(await p5.evaluate(f"fetch('/api/posta/stanje?t={tok}').then(r => r.text())"))
        check(st['topics'] == ['cene'], f'/javno-punjenje/ box: topic cene ({st["topics"]})')
        scrub = await p5.evaluate('''() => window.bvTrack.scrub({
          $current_url: 'https://www.blokvolt.rs/pregled/odjava/?t=' + 'a'.repeat(32) + '&teme=1', $referrer: 'https://www.blokvolt.rs/nalog/?prijava=' + 'b'.repeat(64),
          $pathname: '/nalog/', url: '/pregled/potvrda/?t=' + 'c'.repeat(32) + '#x', note: 'Why?t=1', n: 3,
          $snapshot_data: [{type: 4, data: {href: 'https://www.blokvolt.rs/en/nalog/?prijava=' + 'd'.repeat(64) + '&a=1'}}] })''')
        check(scrub['$current_url'] == 'https://www.blokvolt.rs/pregled/odjava/?teme=1' and scrub['$referrer'] == 'https://www.blokvolt.rs/nalog/'
              and scrub['url'] == '/pregled/potvrda/#x' and scrub['note'] == 'Why?t=1' and scrub['n'] == 3
              and scrub['$snapshot_data'][0]['data']['href'] == 'https://www.blokvolt.rs/en/nalog/?a=1', f'analytics: t= and prijava= taken out of every URL property and the replay address ({scrub})')
        await p5.goto(f'{BASE}/pregled/potvrda/?t=' + 'a' * 32, wait_until='load')
        await p5.wait_for_selector('[data-s=bad]:not([hidden])', timeout=8000)
        check('Link nije ispravan' in await p5.inner_text('.pg-state'), 'unknown token: "Link nije ispravan ili je istekao."')
        await c5.close()

        # ---------------------------------------------------------------- delete the account (desktop)
        await pg.goto(f'{BASE}/nalog/', wait_until='load')
        await pg.wait_for_selector('html.nl-in #nl-favs .nl-st', timeout=8000)
        await pg.click('#nl-del')
        await pg.click('#nl-del-yes')
        await pg.wait_for_selector('html:not(.nl-in)', timeout=8000)
        check(await pg.inner_text('#nl-toast') == 'Nalog je obrisan.', 'delete: signed out, "Nalog je obrisan."')
        check(await pg.evaluate("fetch('/api/nalog/ja').then(r => r.status)") == 401, 'delete: the session is gone')
        check(await pg.evaluate("['bv:fav', 'bv:tesla', 'bv:fav-owner'].every(k => localStorage.getItem(k) === null)"),
              'delete: the favourites, "Imam Teslu" and their owner are removed from this browser')
        await ctx.close()
        await ctx2.close()

        # ---------------------------------------------------------------- the e-mails, rendered (SR/EN/RU), 600 px
        c6, p6 = await new_page(b, 600)
        for lang in ('sr', 'en', 'ru'):
            addr = f'pregled.{lang}.{RUN}@example.com'
            for path, body in (('/api/nalog/kod', {'email': addr, 'lang': lang, 't': 4000}),
                               ('/api/posta/prijava', {'email': addr, 'lang': lang, 'src': '/pregled/', 't': 4000})):
                await p6.goto(f'{BASE}/pregled/', wait_until='load')
                r = await p6.evaluate('([p, b]) => fetch(p, {method: "POST", headers: {"content-type": "application/json"}, body: JSON.stringify(b)}).then(r => r.status)', [path, body])
                check(r == 200, f'mail preview {lang}: {path} → {r}')
            await new_mail(addr, 'code', 0)
            tok = re.search(r'potvrda/\?t=([0-9a-f]{32})', (await new_mail(addr, 'confirm', 0))['html']).group(1)
            await p6.evaluate('(t) => fetch("/api/posta/potvrdi", {method: "POST", headers: {"content-type": "application/json"}, body: JSON.stringify({token: t})})', tok)
            await new_mail(addr, 'welcome', 0)
            for kind in ('code', 'confirm', 'welcome'):
                m = dev_mail(addr, kind)
                f = SHOTS / 'mail' / f'{kind}-{lang}.html'
                f.write_text(m['html'], encoding='utf-8')
                (SHOTS / 'mail' / f'{kind}-{lang}.txt').write_text(f"Subject: {m['subject']}\n{('Headers: ' + m['hdr']) if m.get('hdr') else ''}\n\n{m['text']}", encoding='utf-8')
                await p6.goto('file://' + str(f))
                await p6.wait_for_timeout(150)
                await p6.screenshot(path=str(SHOTS / 'mail' / f'{kind}-{lang}.png'), full_page=True)
                check(not re.search(r'<img|<link|<script|https?://[^"]*\.(png|jpg|gif)', m['html']), f'mail {kind}-{lang}: no remote images or scripts')
        await c6.close()
        await b.close()
    check(not errors, f'no JS errors or CSP violations: {errors[:6]}')
    print(f'\n{len(fails)} failed' if fails else '\nALL OK')
    sys.exit(1 if fails else 0)

asyncio.run(main())
