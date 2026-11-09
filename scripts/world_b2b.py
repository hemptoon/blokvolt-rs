"""G10 — "Data for business" of blokvolt.com: /data-for-business/, /sr/podaci-za-firme/, /ru/dannye-dlya-biznesa/.

A short page about the B2B data sets (coverage and prices; README bvcom §5 G10) with a request form. The form posts to the
blokvolt.rs API /api/zahtev with kind "b2b" (worker: KINDS + CORS for blokvolt.com); requests land in the table `requests`
and the owner's bot like every other request. Preview builds (BV_WORLD_PREVIEW=1) and builds without the reports API run the
form in demo mode: nothing is sent. No product prices on the page (G10: internal hypothesis only), no numbers at all.
Strings: content/world/strings_b2b.json ({key: {en, sr, ru}}); the build stops on a missing language.

    python3 scripts/world_b2b.py selftest
"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORLD = ROOT / 'content' / 'world'
LANGS = ('en', 'sr', 'ru')
URLS = {'en': '/data-for-business/', 'sr': '/sr/podaci-za-firme/', 'ru': '/ru/dannye-dlya-biznesa/'}


def load_strings():
    raw = json.load(open(WORLD / 'strings_b2b.json', encoding='utf-8'))
    miss = [f'{k}.{l}' for k, v in raw.items() for l in LANGS if not v.get(l)]
    if miss:
        raise SystemExit('world_b2b: missing strings ' + ', '.join(miss))
    return {l: {k: v[l] for k, v in raw.items()} for l in LANGS}


def footer_link(l):
    return [(URLS[l], load_strings()[l]['ft_link'])]


def request_api():
    """'' (demo) in previews; otherwise /api/zahtev on the host of the world reports API (content/world/config.json)."""
    if os.environ.get('BV_WORLD_PREVIEW') == '1':
        return ''
    cfg = json.load(open(WORLD / 'config.json', encoding='utf-8'))
    api = os.environ.get('BV_WORLD_REPORTS') or cfg.get('reports_api') or ''
    m = re.match(r'^(https://[^/]+)/', api)
    return m.group(1) + '/api/zahtev' if m else ''


def run(G, c):
    """Called by gen_com.main() after world_shell.run() (c = world_pages context; None = no world pages)."""
    if c is None:
        return
    W = sys.modules['world_pages']
    T = load_strings()
    import shutil, hashlib
    a = G.OUT / 'assets' / 'world'
    a.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / 'static' / 'com' / 'world-b2b.js', a / 'world-b2b.js')
    ver = hashlib.sha1((a / 'world-b2b.js').read_bytes()).hexdigest()[:10]
    api = request_api()
    dl = sys.modules['world_shell'].DOWNLOAD
    for l in LANGS:
        t = T[l]
        W.write_page(c, l, 'world_b2b.html', URLS[l], URLS, dict(
            title=t['title'].replace(' | BlokVolt', ''), h1=t['h1'], description=t['desc'], T=t, crumbs=None, kick=None,
            jsonld=None, api=api, js=f'/assets/world/world-b2b.js?v={ver}', download=dl[l]), 'b2b')
    print(f"world b2b: {len(LANGS)} pages ({', '.join(URLS.values())}), form {'live: ' + api if api else 'demo'}")


def selftest():
    T = load_strings()
    ok = True
    for l in LANGS:
        if set(T[l]) != set(T['en']):
            print('FAIL keys', l); ok = False
        for k, v in T[l].items():
            if re.search(r'\d', v) and k not in ('title', 'lic_p'):
                print('FAIL digit (no numbers on this page)', l, k); ok = False
            if re.search(r'24/7|Evolako|€|EUR\s*\d|\d\s*EUR|RSD|popust|скидк|discount', v, re.I):
                print('FAIL word', l, k); ok = False
    bad = [k for k, v in T['sr'].items() if re.search(r'\b(mi|naš|naša|naše|naši|odmah|redakcija)\b|[А-Яа-я]', v, re.I)]
    bad += [k for k, v in T['ru'].items() if re.search(r'\b(мы|наш|наша|наши|наше|редакция|сразу)\b', v, re.I)]
    bad += [k for k, v in T['en'].items() if re.search(r'\b(we|our|us)\b', v, re.I)]
    if bad:
        print('FAIL personal words', bad); ok = False
    for l in LANGS:
        if re.search(r'\d', T[l]['title'].replace('| BlokVolt', '')):
            print('FAIL digit in title', l); ok = False
    os.environ['BV_WORLD_PREVIEW'] = '1'
    if request_api() != '':
        print('FAIL preview must be demo'); ok = False
    del os.environ['BV_WORLD_PREVIEW']
    if request_api() != 'https://www.blokvolt.rs/api/zahtev':
        print('FAIL api', request_api()); ok = False
    print('world_b2b selftest:', 'OK' if ok else 'FAIL')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(selftest() if sys.argv[1:] == ['selftest'] else 0)
