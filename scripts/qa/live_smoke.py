#!/usr/bin/env python3
"""Checks the live BlokVolt sites from the outside, the way a visitor, a phone and a mail server see them.

Runs every night in GitHub Actions (.github/workflows/site-checks.yml, job "live") and by hand:

    python3 scripts/qa/live_smoke.py                       # www.blokvolt.rs, blokvolt.com and DNS
    python3 scripts/qa/live_smoke.py --base http://127.0.0.1:8787 --local
                                                           # a local dist/ served by scripts/qa/cfserve.py:
                                                           # pages, APK, assetlinks and headers only

Standard library only. Every check ends as OK, WARN (known or slow-moving: shown, does not fail the run)
or FAIL (something a visitor or a mail server would notice: the run exits with code 1). The summary is
printed and, inside GitHub Actions, written to the job summary. docs/RUNBOOK.md 3.21."""
import argparse, datetime as dt, email.utils, hashlib, json, os, re, socket, ssl, sys, time
import urllib.error, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UA = 'BlokVolt-site-check/1.0 (+https://github.com/hemptoon/blokvolt-rs)'
TIMEOUT = 25

# Pages every visitor path depends on; a marker is a string the page must contain.
PAGES = [
    ('/', ['hero2-media', 'ft-app', '/vesti/']),
    ('/mapa/', ['map']),
    ('/firme/', []),
    ('/cene/', []),
    ('/vodici/', ['vodic']),
    ('/vesti/', ['/vesti/']),
    ('/aplikacija/', ['app-phones', 'qr-aplikacija.svg', 'blokvolt.apk']),
    ('/javno-punjenje/', []),
    ('/alati/kalkulator-troskova/', []),
    ('/metodologija/', []),
    ('/izmene/', []),
    ('/pretraga/', []),
    ('/ispravka/', []),
    ('/en/', ['lang="en"']),
    ('/ru/', ['lang="ru"']),
    ('/en/mapa/', ['lang="en"']),
    ('/ru/aplikacija/', ['lang="ru"']),
]
FILES = ['/sitemap.xml', '/robots.txt', '/vesti/rss.xml', '/manifest.webmanifest', '/sw.js', '/offline']
HEADERS = ['content-security-policy', 'strict-transport-security', 'x-frame-options', 'x-content-type-options',
           'referrer-policy', 'permissions-policy', 'cross-origin-opener-policy']

results = []   # (level, name, detail)


def add(level, name, detail=''):
    results.append((level, name, detail))


def fetch(url, method='GET', follow=True, retries=1):
    """(status, headers dict lower-case, body bytes). Network errors come back as status 0."""
    last = None
    for _ in range(retries + 1):
        try:
            req = urllib.request.Request(url, method=method, headers={'User-Agent': UA, 'Accept': '*/*'})
            opener = urllib.request.build_opener() if follow else urllib.request.build_opener(NoRedirect)
            with opener.open(req, timeout=TIMEOUT) as r:
                return r.status, {k.lower(): v for k, v in r.headers.items()}, r.read()
        except urllib.error.HTTPError as e:
            return e.code, {k.lower(): v for k, v in e.headers.items()}, e.read() if hasattr(e, 'read') else b''
        except Exception as e:  # noqa: BLE001 - any network problem is a result, not a crash
            last = e
    return 0, {}, str(last).encode()


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def check_pages(base):
    for path, markers in PAGES:
        st, h, body = fetch(base + path)
        name = f'page {path}'
        if st != 200:
            add('FAIL', name, f'HTTP {st}')
            continue
        html = body.decode('utf-8', 'replace')
        miss = [m for m in markers if m not in html]
        bad = [s for s in ('Ilustracija (AI)', '{{', '{%', 'Traceback') if s in html]
        if '<title>' not in html:
            miss.append('<title>')
        if miss or bad:
            add('FAIL', name, ('missing ' + ', '.join(miss) if miss else '') + (' contains ' + ', '.join(bad) if bad else ''))
        else:
            add('OK', name)
    for path in FILES:
        st, h, body = fetch(base + path)
        add('OK' if st == 200 and body else 'FAIL', f'file {path}', '' if st == 200 else f'HTTP {st}')


def check_sitemap_sample(base):
    """Checks a rotating slice of the sitemap, so that every page is opened about once in two weeks."""
    st, h, body = fetch(base + '/sitemap.xml')
    locs = re.findall(r'<loc>([^<]+)</loc>', body.decode('utf-8', 'replace')) if st == 200 else []
    if len(locs) < 300:
        add('FAIL', 'sitemap', f'{len(locs)} URLs (expected 300+)')
        return
    wrong = [u for u in locs if not u.startswith('https://www.blokvolt.rs/')]
    add('FAIL' if wrong else 'OK', 'sitemap', f'{len(locs)} URLs' + (f', {len(wrong)} outside www.blokvolt.rs' if wrong else ''))
    day = dt.date.today().toordinal()
    step = 14
    sample = [u for i, u in enumerate(locs) if i % step == day % step]
    broken = []
    for u in sample:
        path = urllib.parse.urlsplit(u).path
        st, _, _ = fetch(base + path)
        if st != 200:
            broken.append(f'{path} ({st})')
    add('FAIL' if broken else 'OK', f'sitemap sample {len(sample)} pages', ', '.join(broken[:10]))


def check_app(base):
    app = json.loads((ROOT / 'content' / 'data' / 'app.json').read_text(encoding='utf-8'))
    st, h, body = fetch(f"{base}/aplikacija/{app['apk']}")
    if st != 200:
        add('FAIL', 'APK download', f'HTTP {st}')
    else:
        sha = hashlib.sha256(body).hexdigest()
        ok = len(body) == app['bytes'] and sha == app['sha256']
        add('OK' if ok else 'FAIL', 'APK size and SHA-256 match app.json',
            '' if ok else f'{len(body)} bytes, sha256 {sha[:16]} (app.json {app["bytes"]}, {app["sha256"][:16]})')
    st, h, body = fetch(base + '/.well-known/assetlinks.json')
    try:
        links = json.loads(body)
        t = links[0]['target']
        ok = t['package_name'] == app['package'] and app['cert_sha256'] in t['sha256_cert_fingerprints']
        add('OK' if ok else 'FAIL', 'assetlinks.json names the app and its certificate')
    except Exception as e:  # noqa: BLE001
        add('FAIL', 'assetlinks.json', f'HTTP {st}, {e}')


def check_headers(base):
    st, h, _ = fetch(base + '/')
    miss = [k for k in HEADERS if k not in h]
    add('FAIL' if miss else 'OK', 'security headers on /', 'missing ' + ', '.join(miss) if miss else '')


def check_api(base):
    ts = int(dt.datetime.now().timestamp())
    for path, key in (('/api/zdravlje', 'ok'), ('/api/stanice', 'ok')):
        st, h, body = fetch(f'{base}{path}?nc={ts}')
        try:
            ok = st == 200 and json.loads(body).get(key) is True
        except Exception:  # noqa: BLE001
            ok = False
        add('OK' if ok else 'FAIL', f'API {path}', '' if ok else f'HTTP {st} {body[:80]!r}')


def check_freshness(base):
    st, h, body = fetch(base + '/')
    m = re.search(r'podaci ažurirani (\d{2})\.(\d{2})\.(\d{4})', body.decode('utf-8', 'replace'))
    if m:
        d = dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        age = (dt.date.today() - d).days
        add('WARN' if age > 40 else 'OK', 'data date in the footer', f'{d:%d.%m.%Y}, {age} days ago')
    else:
        add('WARN', 'data date in the footer', 'not found')
    st, h, body = fetch(base + '/vesti/rss.xml')
    dates = []
    for s in re.findall(r'<pubDate>([^<]+)</pubDate>', body.decode('utf-8', 'replace')):
        try:
            dates.append(email.utils.parsedate_to_datetime(s).date())
        except Exception:  # noqa: BLE001
            pass
    if dates:
        age = (dt.date.today() - max(dates)).days
        add('WARN' if age > 21 else 'OK', 'latest news', f'{max(dates):%d.%m.%Y}, {age} days ago')
    else:
        add('WARN', 'latest news', 'no dates in the RSS feed')


def cert_days(host):
    ctx = ssl.create_default_context()
    with socket.create_connection((host, 443), timeout=TIMEOUT) as s, ctx.wrap_socket(s, server_hostname=host) as t:
        na = t.getpeercert()['notAfter']
    return int((ssl.cert_time_to_seconds(na) - time.time()) // 86400)


def check_tls_and_redirects():
    for host in ('www.blokvolt.rs', 'blokvolt.rs', 'blokvolt.com'):
        try:
            d = cert_days(host)
            add('FAIL' if d < 10 else 'WARN' if d < 20 else 'OK', f'TLS certificate {host}', f'{d} days left')
        except Exception as e:  # noqa: BLE001
            add('FAIL', f'TLS certificate {host}', str(e)[:120])
    for url in ('http://blokvolt.rs/', 'https://blokvolt.rs/', 'http://www.blokvolt.rs/'):
        st, h, _ = fetch(url, follow=False)
        loc = h.get('location', '')
        ok = st in (301, 302, 307, 308) and loc.startswith('https://www.blokvolt.rs')
        add('OK' if ok else 'FAIL', f'redirect {url}', f'{st} -> {loc}' if not ok else '')
    for path in ('/', '/serbia/'):
        st, h, body = fetch('https://blokvolt.com' + path)
        add('OK' if st == 200 and b'<title>' in body else 'FAIL', f'blokvolt.com{path}', '' if st == 200 else f'HTTP {st}')


def dns(name, rtype):
    st, h, body = fetch(f'https://dns.google/resolve?name={name}&type={rtype}')
    if st != 200:
        raise RuntimeError(f'dns.google HTTP {st}')
    j = json.loads(body)
    return [a['data'].strip('"').replace('" "', '') for a in j.get('Answer', []) if a.get('type') != 5]


def check_dns():
    """Name servers and anti-spoofing mail records. An unexpected change is how a hijack looks from outside."""
    try:
        ns = ' '.join(dns('blokvolt.rs', 'NS'))
        add('OK' if 'ns.cloudflare.com' in ns else 'FAIL', 'DNS blokvolt.rs name servers', ns)
        txt = dns('blokvolt.rs', 'TXT')
        add('OK' if 'v=spf1 -all' in txt else 'FAIL', 'DNS blokvolt.rs SPF (no mail)')
        dm = ' '.join(dns('_dmarc.blokvolt.rs', 'TXT'))
        add('OK' if 'p=reject' in dm else 'FAIL', 'DNS blokvolt.rs DMARC reject')
        ds = dns('blokvolt.rs', 'DS')
        add('OK' if ds else 'WARN', 'DNS blokvolt.rs DNSSEC (DS at the registry)', '' if ds else 'no DS yet — the owner asks the registrar')
        for d in ('blokvolt.com', 'evolako.com'):
            ns = ' '.join(dns(d, 'NS'))
            add('OK' if 'spaceship.net' in ns else 'FAIL', f'DNS {d} name servers', ns)
            mx = ' '.join(dns(d, 'MX'))
            add('OK' if 'spacemail.com' in mx else 'FAIL', f'DNS {d} MX (mailbox)', mx)
            spf = [t for t in dns(d, 'TXT') if t.startswith('v=spf1')]
            add('OK' if spf and 'spf.spacemail.com' in spf[0] else 'FAIL', f'DNS {d} SPF', spf[0] if spf else 'missing')
            dm = ' '.join(dns('_dmarc.' + d, 'TXT'))
            if 'p=quarantine' in dm or 'p=reject' in dm:
                add('OK', f'DNS {d} DMARC')
            else:
                add('WARN' if 'p=none' in dm else 'FAIL', f'DNS {d} DMARC', 'p=none (quarantine planned after the mail check)' if 'p=none' in dm else 'missing')
        ns = ' '.join(dns('evolako.rs', 'NS'))
        add('OK', 'DNS evolako.rs name servers', ns)
        spf = [t for t in dns('evolako.rs', 'TXT') if t.startswith('v=spf1')]
        dm = ' '.join(dns('_dmarc.evolako.rs', 'TXT'))
        add('OK' if spf and 'p=reject' in dm else 'WARN', 'DNS evolako.rs anti-spoofing (SPF -all, DMARC reject)',
            '' if spf and 'p=reject' in dm else 'not set yet — planned with the move to Cloudflare')
    except Exception as e:  # noqa: BLE001
        add('WARN', 'DNS checks', f'could not run: {e}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', default='https://www.blokvolt.rs')
    ap.add_argument('--local', action='store_true', help='local dist: skip API, freshness, TLS, redirects and DNS')
    a = ap.parse_args()
    base = a.base.rstrip('/')
    check_pages(base)
    check_sitemap_sample(base)
    check_app(base)
    check_headers(base)
    if not a.local:
        check_api(base)
        check_freshness(base)
        check_tls_and_redirects()
        check_dns()
    fails = [r for r in results if r[0] == 'FAIL']
    warns = [r for r in results if r[0] == 'WARN']
    lines = [f'# BlokVolt live check {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%M} UTC — '
             f'{len(results) - len(fails) - len(warns)} OK, {len(warns)} WARN, {len(fails)} FAIL', '']
    for level in ('FAIL', 'WARN', 'OK'):
        for lv, name, detail in results:
            if lv == level:
                lines.append(f'- **{lv}** {name}' + (f' — {detail}' if detail else ''))
    out = '\n'.join(lines) + '\n'
    print(out)
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8') as f:
            f.write(out)
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
