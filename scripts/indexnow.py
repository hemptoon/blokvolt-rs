# -*- coding: utf-8 -*-
"""IndexNow for www.blokvolt.rs (docs/RUNBOOK.md 3.37): after a deploy, tell Bing, Yandex, Seznam, Naver and the other
IndexNow engines which pages are new or changed, so they crawl them now instead of on their next visit.

  python3 scripts/indexnow.py <live sitemap before the deploy> <dist/sitemap.xml> [--dry-run]

Called by .github/workflows/deploy.yml after a successful deploy (that step may fail without failing the deploy). A URL
is sent when it is in the new sitemap and was not in the old one, or its <lastmod> differs. Nothing is sent when nothing
changed, or when the old sitemap could not be read (no guessing: a lost download must not send the whole site).

The key is the name of the one file static/<32 hex>.txt (its content is the key); build.py copies static/ to the site
root, so it is served at https://www.blokvolt.rs/<key>.txt — the keyLocation the engines check. A new key = a new file
(and the old one taken out by the owner).
"""
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
HOST = 'www.blokvolt.rs'
SITE = 'https://' + HOST
ENDPOINT = 'https://api.indexnow.org/indexnow'
LIMIT = 10000                       # the protocol's maximum per request
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


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    dry = '--dry-run' in sys.argv
    if len(args) != 2:
        sys.exit(__doc__)
    k = key()
    old, new = lastmods(args[0]), lastmods(args[1])
    if new is None:
        sys.exit(f'indexnow: {args[1]} is not a sitemap')
    if not old:
        print(f'IndexNow: the live sitemap before the deploy could not be read ({args[0]}) — nothing sent')
        return
    urls = changed(old, new)
    print(f'IndexNow: {len(new)} URLs in the new sitemap, {len(old)} in the old one, {len(urls)} new or changed')
    if not urls:
        print('IndexNow: nothing changed — nothing sent')
        return
    if len(urls) > LIMIT:
        print(f'IndexNow: {len(urls)} URLs, only the first {LIMIT} are sent (protocol limit)')
        urls = urls[:LIMIT]
    for u in urls[:20]:
        print('  ' + u)
    if len(urls) > 20:
        print(f'  … and {len(urls) - 20} more')
    body = json.dumps({'host': HOST, 'key': k, 'keyLocation': f'{SITE}/{k}.txt', 'urlList': urls}).encode('utf-8')
    if dry:
        print(f'IndexNow: dry run, {len(urls)} URLs not sent ({len(body)} bytes)')
        return
    req = urllib.request.Request(ENDPOINT, data=body, method='POST',
                                 headers={'Content-Type': 'application/json; charset=utf-8', 'User-Agent': 'BlokVolt-deploy (+' + SITE + '/)'})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            status = r.status
    except urllib.error.HTTPError as e:
        status = e.code
    except urllib.error.URLError as e:
        sys.exit(f'IndexNow: {len(urls)} URLs not sent — {e.reason}')
    # 200 accepted, 202 accepted (the key is being checked); 400 bad request, 403 key not valid, 422 URLs not of this
    # host or key mismatch, 429 too many requests
    print(f'IndexNow: sent {len(urls)} URLs → HTTP {status}')
    if status not in (200, 202):
        sys.exit(1)


if __name__ == '__main__':
    main()
