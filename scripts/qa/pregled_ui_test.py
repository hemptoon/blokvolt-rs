# Nedeljni pregled end to end (docs/RUNBOOK.md 3.27, "Sending the issues"): the real build with the QA fixture issue,
# served like Cloudflare Pages with the real worker (scripts/qa/nalog_serve.mjs: Miniflare, D1, MAIL_MODE=log). The
# issue page in a browser (a preview: noindex, unlisted), three readers signed up and confirmed through the API, a tick →
# the three previews; then the same issue approved (a second build while the server runs) → a tick → each reader's mail
# in the reader's language and topics; the click counter and the admin counts on the real link table; the page public.
# The rendered mails (HTML, text, 600 px screenshots) go to shots-dir.
#   BV_QA_ACCOUNTS=1 BV_QA_PREGLED=1 BV_QA_PREGLED_FIXTURE=1 python3 build.py
#   MINIFLARE_DIR=/tmp/mf node scripts/qa/nalog_serve.mjs dist 8788 &
#   python3 scripts/qa/pregled_ui_test.py [shots-dir]
# dist/ is left as the approved QA build: build again without the BV_QA_* variables before packing.
import asyncio, json, os, re, subprocess, sys, time, urllib.request, urllib.error
from pathlib import Path
from playwright.async_api import async_playwright

REPO = Path(__file__).resolve().parents[2]
DIST = REPO / 'dist'
BASE = os.environ.get('BV_BASE', 'http://127.0.0.1:8788')
SHOTS = Path(sys.argv[1] if len(sys.argv) > 1 else '/tmp/bv-pregled')
(SHOTS / 'mail').mkdir(parents=True, exist_ok=True)
SITE = 'https://www.blokvolt.rs'
FIX = 'qa-probni-broj'
TEAM = 'hello@blokvolt.com'
ADMIN = 'dev-admin-key-0123456789'                     # nalog_serve.mjs
RUN = str(int(time.time()))[-6:]
fails, errors = [], []


def check(cond, what):
    print(('ok   ' if cond else 'FAIL ') + what)
    if not cond:
        fails.append(what)


def http(method, path, body=None, headers=None):
    """(status, headers, JSON or text) of one request to the local server; redirects are not followed."""
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None
    h = {'origin': BASE, 'x-qa-ip': '10.77.0.' + str(int(RUN) % 250), **(headers or {})}
    data = None
    if body is not None:
        data, h['content-type'] = json.dumps(body).encode(), 'application/json'
    rq = urllib.request.Request(BASE + path, data=data, method=method, headers=h)
    try:
        r = urllib.request.build_opener(NoRedirect).open(rq, timeout=60)
        st, hd, raw = r.status, r.headers, r.read().decode()
    except urllib.error.HTTPError as e:
        st, hd, raw = e.code, e.headers, e.read().decode()
    try:
        return st, hd, json.loads(raw)
    except ValueError:
        return st, hd, raw


def mails(kind=None):
    return [m for m in http('GET', '/__dev/mails')[2] if kind is None or m['kind'] == kind]


def mail(i):
    return http('GET', f'/__dev/mail?id={i}')[2]


def tick():
    """A tick now (a real one waits a minute after the last); waits while another one runs."""
    for _ in range(40):
        http('POST', '/__dev/tick-reset')
        st, hd, j = http('POST', '/api/posta/tick', headers={'origin': ''})
        if not (isinstance(j, dict) and j.get('skipped') == 'busy'):
            return st, hd, j
        time.sleep(0.25)
    return st, hd, j


def issue_json():
    return json.loads((DIST / 'pregled-mail' / f'{FIX}.json').read_text(encoding='utf-8'))


def subscribe(email, lang, topics=None, freq=None):
    """Sign-up, the confirmation mail, the button; then the settings. The token of the reader."""
    n0 = len([m for m in mails('confirm') if m['to_addr'] == email])
    st, _, j = http('POST', '/api/posta/prijava', {'email': email, 'lang': lang, 'src': '/pregled/', 't': 4000})
    for _ in range(100):
        if len([m for m in mails('confirm') if m['to_addr'] == email]) > n0:
            break
        time.sleep(0.05)
    conf = http('GET', f'/__dev/mail?to={email}&kind=confirm')[2]
    tok = re.search(r'potvrda/\?t=([0-9a-f]{32})', conf['html']).group(1)
    http('POST', '/api/posta/potvrdi', {'token': tok})
    if topics or freq:
        http('POST', '/api/posta/podesavanja', {'token': tok, **({'topics': topics} if topics else {}), **({'freq': freq} if freq else {})})
    return st, tok


async def render(pg, m, name):
    """The mail as a reader sees it, 600 px; the cover (on www.blokvolt.rs) is served from dist/."""
    f = SHOTS / 'mail' / f'{name}.html'
    f.write_text(m['html'], encoding='utf-8')
    (SHOTS / 'mail' / f'{name}.txt').write_text(f"Subject: {m['subject']}\nHeaders: {m['hdr']}\n\n{m['text']}", encoding='utf-8')
    await pg.goto('file://' + str(f), wait_until='load')
    await pg.wait_for_timeout(200)
    await pg.screenshot(path=str(SHOTS / 'mail' / f'{name}.png'), full_page=True)
    return await pg.evaluate('''() => ({w: document.documentElement.scrollWidth, img: [...document.images].map(i => [i.naturalWidth, i.getAttribute('src')])})''')


async def page_checks(b, path, w, what):
    ctx = await b.new_context(viewport={'width': w, 'height': 900})
    pg = await ctx.new_page()
    pg.on('pageerror', lambda e: errors.append(f'{path} {w} JS {str(e)[:160]}'))
    pg.on('console', lambda m: errors.append(f'{path} {w} {m.text[:160]}') if m.type == 'error' and '/api/' not in m.text else None)
    await pg.goto(BASE + path, wait_until='load')
    await pg.wait_for_timeout(300)
    r = await pg.evaluate('''() => ({sw: document.documentElement.scrollWidth, iw: innerWidth, secs: document.querySelectorAll('section[data-pg-topic]').length,
      robots: (document.querySelector('meta[name=robots]') || {}).content || '', cover: (document.querySelector('img[data-pg=cover]') || {}).naturalWidth || 0,
      h2: [...document.querySelectorAll('section[data-pg-topic] h2')].map(h => h.textContent)})''')
    check(r['sw'] <= r['iw'] + 1 and r['secs'] == 4 and r['cover'] > 0, f'{what} @{w}: four sections, the cover, no horizontal overflow ({r["h2"]})')
    await pg.screenshot(path=str(SHOTS / f'{what.replace(" ", "-").replace("/", "")}-{w}.png'), full_page=True)
    await ctx.close()
    return r


async def main():
    if not (DIST / 'pregled-mail' / f'{FIX}.json').exists():
        sys.exit('dist/ has no QA issue: BV_QA_ACCOUNTS=1 BV_QA_PREGLED=1 BV_QA_PREGLED_FIXTURE=1 python3 build.py, then start nalog_serve.mjs')
    j0 = issue_json()
    async with async_playwright() as p:
        b = await p.chromium.launch()

        # ---------------------------------------------------------------- the preview page
        for lang, pre in (('sr', ''), ('en', '/en'), ('ru', '/ru')):
            for w in ((390, 1440) if lang == 'sr' else (390,)):
                r = await page_checks(b, f'{pre}/pregled/{FIX}/', w, f'preview {lang}')
                check('noindex' in r['robots'], f'preview page {lang}: noindex')
        st, _, idx = http('GET', '/pregled/')
        check(FIX not in idx, '/pregled/: the preview is not under „Prethodni brojevi“')

        # ---------------------------------------------------------------- readers
        readers = {'sr': f'pregled.sr.{RUN}@example.com', 'en': f'pregled.en.{RUN}@example.com', 'ru': f'pregled.ru.{RUN}@example.com'}
        toks = {'sr': subscribe(readers['sr'], 'sr')[1], 'en': subscribe(readers['en'], 'en', topics=['cene'])[1],
                'ru': subscribe(readers['ru'], 'ru', freq='m')[1]}
        check(all(len(t) == 32 for t in toks.values()), 'three readers on: sr (every topic), en (cene only), ru (monthly)')

        # ---------------------------------------------------------------- the previews
        st, _, t1 = tick()
        act = next((i for i in t1.get('issues', []) if i['slug'] == FIX), {}).get('action') if isinstance(t1, dict) else None
        pv = [m for m in mails('preview') if f'[PREVIEW {j0["hash"][:8]}]' in m['subject']]
        check(st == 200 and act in ('preview_sent', 'previewed') and len(pv) == 3, f'tick: the three previews of hash {j0["hash"][:8]} ({act}; the first /api request may have started it)')
        check(all(m['to_addr'] == TEAM and 'List-Unsubscribe' not in m['hdr'] for m in pv), 'previews: only to the team address, without List-Unsubscribe')
        c6 = await b.new_context(viewport={'width': 600, 'height': 900})
        pgm = await c6.new_page()
        await pgm.route(SITE + '/assets/**', lambda route: route.fulfill(path=str(DIST / route.request.url.split('?')[0][len(SITE) + 1:])))
        for m in pv:
            full = mail(m['id'])
            lang = re.search(r'<html lang="(\w+)"', full['html']).group(1)
            r = await render(pgm, full, f'preview-{lang}')
            check(r['w'] <= 600 and r['img'] and r['img'][0][0] > 0, f'preview {lang}: 600 px, the cover loads ({r["img"][0][1][:60]}…)')
        st, _, t2 = tick()
        check(len(mails('preview')) == 3 and len(mails('pregled')) == 0, 'a second tick: no second preview, nothing to readers')

        # ---------------------------------------------------------------- approved: a new build while the server runs
        env = dict(os.environ, BV_QA_ACCOUNTS='1', BV_QA_PREGLED='1', BV_QA_PREGLED_FIXTURE='approved')
        out = subprocess.run([sys.executable, 'build.py'], cwd=REPO, env=env, capture_output=True, text=True)
        check(out.returncode == 0, 'build with the issue approved')
        j1 = issue_json()
        check(j1['hash'] == j0['hash'] and j1['approved_hash'] == j0['hash'], 'the approved file has the previewed hash')
        st, _, t3 = tick()
        i3 = next((i for i in t3.get('issues', []) if i['slug'] == FIX), {}) if isinstance(t3, dict) else {}
        got = {m['to_addr']: m for m in mails('pregled')}
        check(st == 200 and i3.get('action') == 'enqueued' and all(readers[l] in got for l in readers), f'tick: queued and sent to the three readers ({i3})')
        for lang, addr in readers.items():
            m = mail(got[addr]['id'])
            hdr = json.loads(m['hdr'])
            check(hdr.get('List-Unsubscribe', '').startswith(f'<{BASE}/api/posta/odjava?t={toks[lang]}>') and hdr.get('List-Unsubscribe-Post') == 'List-Unsubscribe=One-Click'
                  and hdr.get('Idempotency-Key', '').startswith(f'pregled-{FIX}-'), f'{lang}: List-Unsubscribe with the reader\'s token, Idempotency-Key')
            check(f'<html lang="{lang}">' in m['html'] and m['subject'] == j1['langs'][lang]['subject'] and f'/pregled/odjava/?t={toks[lang]}&amp;teme=1' in m['html'],
                  f'{lang}: the issue in the reader\'s language, with the reader\'s settings link')
            hrefs = re.findall(r'href="([^"]*)"', m['html'])
            check(all(h.startswith(SITE + f'/api/posta/klik?i={FIX}&amp;l=') or '/pregled/odjava/?t=' in h for h in hrefs), f'{lang}: every other link through the click counter')
            n_secs = m['html'].count('<h2 ')
            want = 2 if lang == 'en' else 4
            check(n_secs == want, f'{lang}: {n_secs} sections (the intro and the reader\'s topics: {want})')
            r = await render(pgm, m, f'pregled-{lang}')
            check(r['w'] <= 600, f'{lang}: the mail fits 600 px')
        en = mail(got[readers['en']]['id'])['html']
        check(re.search(r'<h2[^>]*>What it means</h2>', en) and re.search(r'<h2[^>]*>Public charging prices</h2>', en) and not re.search(r'<h2[^>]*>News</h2>', en),
              'en (cene): the intro and the prices, no news section')
        st, _, t4 = tick()
        check(len(mails('pregled')) == 3 and next(i for i in t4['issues'] if i['slug'] == FIX)['action'] == 'done', 'next tick: done, nobody gets it twice')

        # ---------------------------------------------------------------- the click counter and the counts
        u2 = j1['links']['2']
        st, hd, _ = http('GET', f'/api/posta/klik?i={FIX}&l=2')
        check(st == 302 and hd['location'] == u2, f'klik: link 2 → {u2}')
        st, hd, _ = http('GET', f'/api/posta/klik?i={FIX}&l=999')
        check(st == 302 and hd['location'] == BASE + '/pregled/', 'klik: an unknown link → /pregled/')
        time.sleep(0.4)
        st, _, adm = http('GET', '/api/admin/posta', headers={'authorization': 'Bearer ' + ADMIN})
        ai = next((i for i in adm['pregled']['issues'] if i['slug'] == FIX), {})
        check(ai.get('rows', {}).get('sent') == 3 and any(c['l'] == 2 and c['n'] >= 1 and c['url'] == u2 for c in ai.get('clicks', [])),
              f'admin/posta: 3 sent, the click on link 2 ({ai.get("rows")}, {ai.get("clicks")})')

        # ---------------------------------------------------------------- the page is public now
        r = await page_checks(b, f'/pregled/{FIX}/', 1440, 'approved sr')
        check('noindex' not in r['robots'], 'approved page: indexable')
        st, _, idx = http('GET', '/pregled/')
        check(f'/pregled/{FIX}/' in idx, '/pregled/: the approved issue under „Prethodni brojevi“')
        await c6.close()
        await b.close()
    check(not errors, f'no JS errors or CSP violations: {errors[:4]}')
    print(f'\n{len(fails)} failed' if fails else '\nALL OK')
    print('dist/ is the approved QA build now: build again without BV_QA_* before packing.')
    sys.exit(1 if fails else 0)

asyncio.run(main())
