#!/usr/bin/env python3
"""World map „Prijavi grešku“ end to end (K6): a report form on one localhost port posts cross-origin to the real worker
(dist/_worker.js in Miniflare with an in-memory D1, scripts/qa/nalog_serve.mjs, the site's real _headers and CSP) → rows in
D1 → the owner decides one place on /admin/svet/ in Chromium → scripts/world_reports.py reads the reports through the admin
API with the key from the environment, applies the automatic rules on the fixture layer and cards
(scripts/qa/fixtures/svet/), writes its decisions back and builds overrides.csv → an undo on /admin/svet/ → the next run
turns the hide into unhide. Nothing leaves the machine.

    python3 build.py                                   # dist/ with the new worker and /admin/svet/
    npm install --prefix /tmp/mf miniflare@4
    MINIFLARE_DIR=/tmp/mf python3 scripts/qa/svet_e2e_test.py [out-dir]
"""
import csv, re, http.server, json, os, socket, subprocess, sys, tempfile, threading, time, functools, urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FIX = REPO / 'scripts' / 'qa' / 'fixtures' / 'svet'
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(tempfile.mkdtemp(prefix='svet-e2e-'))
KEY = 'dev-admin-key-0123456789'          # the local server's key (scripts/qa/nalog_serve.mjs), never a real one
sys.path.insert(0, str(REPO / 'scripts'))
import world_reports as wr  # noqa: E402

oks = fails = 0
def check(cond, what, detail=None):
    global oks, fails
    if cond:
        oks += 1; print('ok   ' + what)
    else:
        fails += 1; print('FAIL ' + what + ('' if detail is None else ' — ' + str(detail)[:400]))

def free_port():
    s = socket.socket(); s.bind(('127.0.0.1', 0)); p = s.getsockname()[1]; s.close(); return p

def http_json(method, url, body=None, headers=None):
    rq = urllib.request.Request(url, method=method, data=None if body is None else json.dumps(body).encode(),
                                headers={'content-type': 'application/json', **(headers or {})})
    try:
        with urllib.request.urlopen(rq, timeout=20) as r:
            return r.status, json.loads(r.read() or b'null')
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b'null')

# ---- the places: picked from the fixture by what the rules need
layer = wr.load_layer(FIX / 'layer.geojsonseq')
cards = wr.Cards(FIX / 'data')
sites = wr.site_info(layer, wr.load_cards(cards, {p: (v['lat'], v['lon']) for p, v in layer.items()}), cards.gov_sources)
weak = [p for p, s in sorted(sites.items()) if (s['conf'] or 0) < 70 and s['nsrc'] == 1 and not s['gov']]
strong = [p for p, s in sorted(sites.items()) if (s['conf'] or 0) >= 70 or s['gov']]
assert len(weak) >= 4 and strong, 'fixture needs 4 weak and 1 protected place'
H, M, A, AM = weak[:4]            # hide by two reports; move by the owner; access by the rule; move by two agreeing reports
G = strong[0]                     # protected: never hidden automatically
print(f'places: hide {H}, owner move {M}, access {A}, auto move {AM}, protected {G}')

# ---- servers: the worker + dist, and the form page on another origin
if not (REPO / 'dist' / '_worker.js').exists():
    sys.exit('dist/ is missing: python3 build.py first')
PA, PB = free_port(), free_port()
API = f'http://127.0.0.1:{PA}'
srv = subprocess.Popen(['node', str(REPO / 'scripts' / 'qa' / 'nalog_serve.mjs'), str(REPO / 'dist'), str(PA)],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
for _ in range(100):
    try:
        socket.create_connection(('127.0.0.1', PA), timeout=0.2).close(); break
    except OSError:
        time.sleep(0.2)
H_ = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(FIX))
H_.log_message = lambda *a: None
form_srv = http.server.ThreadingHTTPServer(('127.0.0.1', PB), H_)
threading.Thread(target=form_srv.serve_forever, daemon=True).start()

try:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        page = br.new_page()
        console = []
        page.on('console', lambda m: m.type == 'error' and console.append(m.text))
        # 1. the visitor's reports, cross-origin from http://localhost:<PB> (CORS preflight: JSON body)
        page.goto(f'http://localhost:{PB}/prijava_form.html?api={API}')
        def send(pid, typ, text='', lat=None, lon=None, email=''):
            page.fill('#pid', str(pid)); page.select_option('#type', typ); page.fill('#text', text); page.fill('#email', email)
            page.fill('#lat', '' if lat is None else str(lat)); page.fill('#lon', '' if lon is None else str(lon))
            page.evaluate("document.getElementById('out').textContent = ''")
            page.click('#send')
            page.wait_for_function("document.getElementById('out').textContent !== ''")
            return page.text_content('#out')
        t = send(H, 'ne_postoji', 'Punjač je uklonjen, parking je prazan.', email='vozac@example.com')
        check(t.startswith('Hvala.'), 'form on another origin: report accepted (CORS works)', t)
        sm = sites[M]
        t = send(M, 'lokacija', 'Punjač je na drugom kraju parkinga.', lat=round(sm['lat'] + 0.0004, 6), lon=round(sm['lon'] + 0.0003, 6))
        check(t.startswith('Hvala.'), 'form: lokacija report accepted', t)
        t = send(M, 'lokacija', lat=sm['lat'], lon=sm['lon'])
        check(t.startswith('Hvala.'), 'form: the same place twice a day → still "Hvala" (stored once)', t)
        t = send(A, 'lokacija')
        check('400' in t and 'point' in t, 'form: lokacija without a point → 400 point is readable cross-origin', t)
        check(not [c for c in console if 'CORS' in c or 'blocked' in c], 'no CORS errors in the console', console)

        # 2. more visitors (other fingerprints) straight to the API, as other browsers would
        def api_rep(ip, body):
            return http_json('POST', API + '/api/svet/prijava', dict({'lang': 'en', 'hp': ''}, **body), {'x-qa-ip': ip})
        check(api_rep('10.20.0.2', {'pid': H, 'type': 'ne_radi'})[0] == 200, 'second, independent report for the weak place')
        check(api_rep('10.20.0.3', {'pid': A, 'type': 'nije_javni', 'text': 'Only for hotel guests.'})[0] == 200, 'nije_javni report')
        check(api_rep('10.20.0.9', {'pid': A, 'type': 'nije_javni'})[0] == 200, 'second, independent nije_javni (decision 18: 2 needed)')
        sg = sites[G]
        for ip, d in (('10.20.0.10', 0.0003), ('10.20.0.11', 0.00033)):   # agreeing points on a protected place
            api_rep(ip, {'pid': G, 'type': 'lokacija', 'lat': round(sg['lat'] + d, 6), 'lon': sg['lon']})
        sa = sites[AM]
        for ip, d in (('10.20.0.4', 0.0003), ('10.20.0.5', 0.00032)):
            api_rep(ip, {'pid': AM, 'type': 'lokacija', 'lat': round(sa['lat'] + d, 6), 'lon': sa['lon']})
        for ip in ('10.20.0.6', '10.20.0.7'):
            api_rep(ip, {'pid': G, 'type': 'ne_postoji'})
        api_rep('10.20.0.8', {'pid': H, 'type': 'drugo', 'text': 'Pogledajte www.example-shop.com'})
        st, ex = http_json('GET', API + '/api/admin/svet?view=export', headers={'authorization': 'Bearer ' + KEY})
        n_rows = len(ex['reports'])
        check(st == 200 and n_rows == 12, 'D1 holds the 12 stored reports (spam among them, rejected)', n_rows)

        # 3. the owner on /admin/svet/ (served with the site's real CSP): accept the owner-move place
        adm = br.new_page(viewport={'width': 1440, 'height': 900})
        aerr = []
        adm.on('console', lambda m: m.type == 'error' and aerr.append(m.text))
        adm.on('pageerror', lambda e: aerr.append(str(e)))
        adm.goto(API + '/admin/svet/')
        adm.fill('#key', KEY)
        adm.keyboard.press('Enter')
        # (the page's CSP forbids string evaluation, so wait with locators only)
        card = adm.locator('.card', has=adm.locator('select.act'), has_text=re.compile(rf'pid {M}\b')).first
        card.wait_for(timeout=10000)
        sel = card.locator('select.act')
        check(sel.count() == 1 and sel.input_value() == 'move', 'admin: the lokacija place is preselected as move', sel.input_value() if sel.count() else None)
        card.locator('button.ok').click()
        card.locator('button.ok[disabled]').wait_for(state='attached', timeout=10000)
        real = [e for e in aerr if 'tiles.blokvolt.rs' not in e]   # the card preview needs the R2 host (CSP + CORS), see FILES.md
        check(not real, 'admin page: no console errors under the site CSP (inline script hash ok)', aerr)
        adm.screenshot(path=str(OUT / 'admin_after_accept.png'), full_page=True)
        rows = {r['id']: r for r in http_json('GET', API + '/api/admin/svet?view=export', headers={'authorization': 'Bearer ' + KEY})[1]['reports']}
        mrows = [r for r in rows.values() if r['pid'] == M]
        check(mrows and all(r['status'] == 'accepted' and r['action'] == 'move' and r['decided_by'] == 'admin' for r in mrows),
              'D1: the owner decision is stored', mrows)

        # 4. the weekly script with the key from the environment
        def run_script(out):
            env = dict(os.environ, ADMIN_KEY=KEY)
            p = subprocess.run([sys.executable, str(REPO / 'scripts' / 'world_reports.py'), '--api', API,
                                '--layer', str(FIX / 'layer.geojsonseq'), '--data', str(FIX / 'data'), '--out', str(out)],
                               env=env, capture_output=True, text=True, timeout=120)
            return p
        p = run_script(OUT / 'run1')
        check(p.returncode == 0, 'script run 1', p.stdout[-400:] + p.stderr[-800:])
        check(KEY not in p.stdout + p.stderr and KEY not in (OUT / 'run1' / 'run.log').read_text(), 'the key is never printed or logged')
        ov = {int(r['pid']): r for r in csv.DictReader(open(OUT / 'run1' / 'overrides.csv'))}
        check(ov.get(H, {}).get('action') == 'hide', 'overrides: two independent reports hide the weak place', ov.get(H))
        check(ov.get(M, {}).get('action') == 'move' and ov[M]['lat'] and ov[M]['lon'], 'overrides: the owner move', ov.get(M))
        check(ov.get(A, {}).get('action') == 'access' and ov[A]['access'] == 'restricted_reported', 'overrides: access restricted', ov.get(A))
        check(ov.get(AM, {}).get('action') == 'move' and abs(float(ov[AM]['lat']) - (sa['lat'] + 0.00031)) < 2e-6, 'overrides: auto move to the mean point', ov.get(AM))
        check(G not in ov, 'overrides: the protected place is neither hidden nor moved (decision 18)')
        q = json.load(open(OUT / 'run1' / 'queue.json'))
        qtxt = json.dumps(q)
        check(str(G) in qtxt and 'gov_registry' in qtxt, 'queue: the protected place waits for the owner (gov_registry)')
        check('www.example-shop.com' not in open(OUT / 'run1' / 'overrides.csv').read(), 'overrides carry no reporter text')
        rows = {r['id']: r for r in http_json('GET', API + '/api/admin/svet?view=export', headers={'authorization': 'Bearer ' + KEY})[1]['reports']}
        hr = [r for r in rows.values() if r['pid'] == H and r['type'] in ('ne_postoji', 'ne_radi')]
        check(hr and all(r['status'] == 'auto_hidden' and r['decided_by'] == 'auto' for r in hr), 'D1: the script wrote its decisions back', hr)

        # 5. the owner undoes the automatic hide on /admin/svet/; the next run turns it into unhide
        adm.reload()
        adm.fill('#key', KEY); adm.keyboard.press('Enter')
        adm.locator('button', has_text='Poništi').first.wait_for(timeout=10000)
        ac = adm.locator('.card', has=adm.locator('button', has_text='Poništi'), has_text=re.compile(rf'pid {H}\b'))
        undo_card = ac.first.locator('button', has_text='Poništi') if ac.count() else None
        check(undo_card is not None, 'admin: the automatic hide is listed with „Poništi“')
        if undo_card is not None:
            undo_card.click()
            adm.wait_for_timeout(800)
        p = run_script(OUT / 'run2')
        ov2 = {int(r['pid']): r for r in csv.DictReader(open(OUT / 'run2' / 'overrides.csv'))}
        check(p.returncode == 0 and ov2.get(H, {}).get('action') == 'unhide', 'run 2: the undone hide becomes unhide', ov2.get(H))
        check(ov2.get(M, {}).get('action') == 'move', 'run 2: earlier decisions stay in overrides')
        for w in (360, 768, 1440):
            adm.set_viewport_size({'width': w, 'height': 900})
            ov_ = adm.evaluate('document.scrollingElement.scrollWidth - innerWidth')
            check(ov_ <= 1, f'admin page at {w}px: no horizontal scroll', ov_)
            adm.screenshot(path=str(OUT / f'admin_{w}.png'), full_page=True)
        br.close()
finally:
    form_srv.shutdown()
    srv.terminate()

print(f'\nout: {OUT}\n{oks} ok, {fails} FAIL')
sys.exit(1 if fails else 0)
