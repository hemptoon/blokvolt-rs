# -*- coding: utf-8 -*-
"""IndexNow for www.blokvolt.rs (docs/RUNBOOK.md 3.37): after a deploy, tell Bing, Yandex, Seznam, Naver and the other
IndexNow engines which pages are new or changed, so they crawl them now instead of on their next visit.

  python3 scripts/indexnow.py <live sitemap before the deploy> <dist/sitemap.xml> [--dry-run]

Called by .github/workflows/deploy.yml after a successful deploy (that step may fail without failing the deploy). A URL
is sent when it is in the new sitemap and was not in the old one, or its <lastmod> differs. Nothing is sent when nothing
changed, or when the old sitemap could not be read (no guessing: a lost download must not send the whole site). An empty
<urlset> as the old sitemap means "did not exist before" (the blokvolt.com workflow writes one on HTTP 404): all URLs are sent.

The key is the name of the one file static/<32 hex>.txt (its content is the key); build.py copies static/ to the site
root, so it is served at https://www.blokvolt.rs/<key>.txt — the keyLocation the engines check. A new key = a new file
(and the old one taken out by the owner).
"""
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
HOST = os.environ.get('INDEXNOW_HOST', 'www.blokvolt.rs')   # blokvolt.com: its workflow sets INDEXNOW_HOST (bvcom README §3)
SITE = 'https://' + HOST
ENDPOINT = 'https://api.indexnow.org/indexnow'
# HOME2 (11.11.2026): sitemaps whose URLs are sent again in full until the date, even when unchanged — for a batch an
# engine refused. 11.11 the first request of the first .com run (sitemap-world-ru-city.xml, 3 136 URLs) got 403: it went
# out right after the deploy, before the key file answered on blokvolt.com; the next requests of the same run were accepted.
# Remove an entry once the run log shows "HTTP 200/202" for it.
RESEND = {'blokvolt.com': {'sitemap-world-ru-city.xml': '2026-11-30'}}
KEY_WAIT = (0, 10, 20, 30, 60)     # seconds between checks that the live key file answers before the first request
LIMIT = 10000                       # the protocol's maximum per request (LANG0: longer lists go in several requests)
NS = '{http://www.sitemaps.org/schemas/sitemap/0.9}'


def key():
    keys = [p for p in (ROOT / 'static').glob('*.txt') if re.fullmatch(r'[0-9a-f]{32}\.txt', p.name)]
    if len(keys) != 1:
        sys.exit(f'indexnow: expected exactly one key file static/<32 hex>.txt, found {len(keys)}')
    k = keys[0].stem
    if keys[0].read_text(encoding='utf-8').strip() != k:
        sys.exit(f'indexnow: {keys[0].name} must contain its own name (the key)')
    return k


def lastmods(path):
    """{loc: lastmod} of a sitemap file; None when the file is missing or is not a sitemap."""
    p = Path(path)
    if not p.is_file() or not p.stat().st_size:
        return None
    try:
        root = ET.parse(p).getroot()
    except ET.ParseError:
        return None
    if root.tag != NS + 'urlset':
        return None
    out = {}
    for u in root.iter(NS + 'url'):
        loc, lm = u.findtext(NS + 'loc'), u.findtext(NS + 'lastmod')
        if loc:
            out[loc.strip()] = (lm or '').strip()
    return out


def changed(old, new):
    return [loc for loc, lm in new.items() if loc.startswith(SITE + '/') and old.get(loc) != lm]


def resend(name, new, today=None):
    """URLs of the new sitemap to send in full again (RESEND), [] when the sitemap is not listed or its date has passed."""
    import datetime as dt
    until = RESEND.get(HOST, {}).get(name)
    today = today or dt.date.today().isoformat()
    if not until or today > until:
        return []
    return [loc for loc in new if loc.startswith(SITE + '/')]


def key_live(k):
    """True once https://<host>/<key>.txt answers with the key (an engine checks it; right after a deploy it may not yet)."""
    import time
    for w in KEY_WAIT:
        if w:
            time.sleep(w)
        try:
            with urllib.request.urlopen(urllib.request.Request(f'{SITE}/{k}.txt', headers={'Cache-Control': 'no-cache'}), timeout=20) as r:
                if r.status == 200 and r.read().decode('utf-8', 'replace').strip() == k:
                    return True
        except Exception:
            pass
    return False


def post(body):
    req = urllib.request.Request(ENDPOINT, data=body, method='POST',
                                 headers={'Content-Type': 'application/json; charset=utf-8', 'User-Agent': 'BlokVolt-deploy (+' + SITE + '/)'})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    dry = '--dry-run' in sys.argv
    if len(args) != 2:
        sys.exit(__doc__)
    k = key()
    old, new = lastmods(args[0]), lastmods(args[1])
    if new is None:
        sys.exit(f'indexnow: {args[1]} is not a sitemap')
    if old is None:
        print(f'IndexNow: the live sitemap before the deploy could not be read ({args[0]}) — nothing sent')
        return
    if not old:   # an empty <urlset>: the caller says the sitemap did not exist before (HTTP 404) — first publication
        print(f'IndexNow: {args[0]} is an empty sitemap — first publication, every URL of the new one is sent')
    urls = changed(old, new)
    print(f'IndexNow: {len(new)} URLs in the new sitemap, {len(old)} in the old one, {len(urls)} new or changed')
    again = [u for u in resend(Path(args[1]).name, new) if u not in set(urls)]
    if again:
        print(f'IndexNow: {len(again)} unchanged URLs sent again (RESEND {Path(args[1]).name} until {RESEND[HOST][Path(args[1]).name]})')
        urls += again
    if not urls:
        print('IndexNow: nothing changed — nothing sent')
        return
    for u in urls[:20]:
        print('  ' + u)
    if len(urls) > 20:
        print(f'  … and {len(urls) - 20} more')
    if not dry and not key_live(k):
        print(f'IndexNow: {SITE}/{k}.txt does not answer with the key yet — sending anyway (the engine may refuse with 403)')
    failed = 0
    for lang, part in batches(urls):   # LANG0: one request per language, at most LIMIT URLs each (nothing is cut off)
        failed += not send(k, part, f'{lang}, {len(part)} URLs', dry)
    if failed:
        sys.exit(1)


def lang_of(url):
    """Language of a URL by its first path segment (/de/…, /sr/…); the English pages (no prefix) and the regional
    sections are "en" here — the grouping only keeps one request per language."""
    m = re.match(re.escape(SITE) + r'/([a-z]{2})(?:/|$)', url)
    return m.group(1) if m else 'en'


def batches(urls):
    """[(language, ≤ LIMIT URLs)] in a stable order: English first, then the other languages A–Z."""
    groups = {}
    for u in urls:
        groups.setdefault(lang_of(u), []).append(u)
    out = []
    for lang in sorted(groups, key=lambda x: (x != 'en', x)):
        g = groups[lang]
        out += [(lang, g[i:i + LIMIT]) for i in range(0, len(g), LIMIT)]
    return out


def send(k, urls, what, dry=False):
    body = json.dumps({'host': HOST, 'key': k, 'keyLocation': f'{SITE}/{k}.txt', 'urlList': urls}).encode('utf-8')
    if dry:
        print(f'IndexNow: dry run, {what} not sent ({len(body)} bytes)')
        return True
    try:
        status = post(body)
        if status in (403, 429):   # key not visible to the engine yet / too fast: one more try after a pause
            import time
            print(f'IndexNow: HTTP {status}, one more try in 45 s')
            time.sleep(45)
            status = post(body)
    except urllib.error.URLError as e:
        print(f'IndexNow: {what} not sent — {e.reason}')
        return False
    # 200 accepted, 202 accepted (the key is being checked); 400 bad request, 403 key not valid, 422 URLs not of this
    # host or key mismatch, 429 too many requests
    print(f'IndexNow: sent {what} → HTTP {status}')
    return status in (200, 202)


if __name__ == '__main__':
    main()
