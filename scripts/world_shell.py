"""Frame of the world layer of blokvolt.com (G0): one menu and one footer block for the world map and the world pages,
the short pages /about/, /sources/, /methodology/ (EN, SR, RU) that lead to "About the data", the home search (K3's static index of
countries and cities), and — only with BV_WORLD_HOME=1 (dev builds) — a world home page at /, /sr/, /ru/.

Runs only together with the world pages (BV_WORLD_PAGES, scripts/world_pages.py); without them blokvolt.com builds
exactly as before. Strings: content/world/strings_shell.json ({key: {en, sr, ru}}); the build stops on a missing
language. Menu: Map · Charging stations · Open data — sections that do not exist yet (prices, how to pay, routes) are not
shown. Nothing here writes a number that is not in the data (manifest counts, the pages bundle).

    python3 scripts/world_shell.py selftest
"""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORLD = ROOT / 'content' / 'world'
LANGS = ('en', 'sr', 'ru')
MAP = {'en': '/map/', 'sr': '/sr/mapa/', 'ru': '/ru/karta/'}
HUB = {'en': '/charging-stations/', 'sr': '/sr/punjaci/', 'ru': '/ru/zaryadki/'}
ABOUT_DATA = {l: HUB[l] + a + '/' for l, a in (('en', 'about-data'), ('sr', 'o-podacima'), ('ru', 'o-dannyh'))}
DOWNLOAD = {l: HUB[l] + a + '/' for l, a in (('en', 'download'), ('sr', 'preuzimanje'), ('ru', 'skachat'))}
SHELL = {
    'about': {'en': '/about/', 'sr': '/sr/o-sajtu/', 'ru': '/ru/o-sajte/'},
    'sources': {'en': '/sources/', 'sr': '/sr/izvori/', 'ru': '/ru/istochniki/'},
    'methodology': {'en': '/methodology/', 'sr': '/sr/metodologija/', 'ru': '/ru/metodologiya/'},
}
HOME = {'en': '/', 'sr': '/sr/', 'ru': '/ru/'}


def load_strings():
    raw = json.load(open(WORLD / 'strings_shell.json', encoding='utf-8'))
    miss = [f'{k}.{l}' for k, v in raw.items() for l in LANGS if not v.get(l)]
    if miss:
        raise SystemExit('world_shell: missing strings ' + ', '.join(miss))
    return {l: {k: v[l] for k, v in raw.items()} for l in LANGS}


def active():
    return bool(os.environ.get('BV_WORLD_PAGES'))


EXTRA = []      # G4: [(urls {lang: url}, labels {lang: label}, key)] — set by world_pay.prepare() (How to pay · Routes)
PRESS = None    # G7: {lang: (url, label)} — set by world_press.prepare() when an index issue exists
PRICES = None   # G3: {'hub': {lang: url}, 'nav': {lang: label}} — set by world_prices.prepare() when the price pages are built


def nav(l):
    """The world menu: Map · Charging stations · [Prices] · Open data (section keys match world_pages / world_map)."""
    T = load_strings()[l]
    out = [(MAP[l], T['nav_map'], 'map'), (HUB[l], T['nav_stations'], 'hub'), (ABOUT_DATA[l], T['nav_open'], 'about')]
    if PRICES:
        out.insert(2, (PRICES['hub'][l], PRICES['nav'][l], 'prices'))
    for urls, labels, key in EXTRA:
        out.insert(len(out) - 1, (urls[l], labels[l], key))
    return out


def footer(l):
    """Links of the world footer block (_footer.html, WORLD_FT)."""
    T = load_strings()[l]
    return {'h': T['ft_h'], 'links': [(ABOUT_DATA[l], T['ft_about_data']), (DOWNLOAD[l], T['ft_download']),
                                      (SHELL['sources'][l], T['ft_sources']), (SHELL['methodology'][l], T['ft_method']),
                                      (SHELL['about'][l], T['ft_about'])] + ([PRESS[l]] if PRESS else [])}


def run(G, c):
    """Called by gen_com.main() after world_pages.run() (c = its context). Writes the shell pages and the index."""
    if c is None:
        return
    W = sys.modules['world_pages']
    T = load_strings()
    out = []
    mp = os.environ.get('BV_WORLD_MANIFEST')
    manifest = json.load(open(mp, encoding='utf-8')) if mp and Path(mp).exists() else None
    # search index: K3's /assets/world/search-index.json (world_pages.search_index); the home page loads it on first focus
    import hashlib
    a = G.OUT / 'assets' / 'world'
    idx = a / 'search-index.json'
    sver = hashlib.sha1(idx.read_bytes()).hexdigest()[:10] if idx.exists() else '0'
    n_idx = len(json.load(open(idx, encoding='utf-8'))['items']) if idx.exists() else 0
    shutil_copy(ROOT / 'static' / 'com' / 'world-home.js', a / 'world-home.js')
    hver = hashlib.sha1((a / 'world-home.js').read_bytes()).hexdigest()[:10]
    n_sources = len([k for k in (manifest or {}).get('sources', {}) if not k.startswith('ocm:')]) if manifest else 0
    for kind, tpl in (('about', 'world_shell_about.html'), ('sources', 'world_shell_sources.html'),
                      ('methodology', 'world_shell_method.html')):
        urls = SHELL[kind]
        for l in LANGS:
            t = T[l]
            key = {'about': 'about', 'sources': 'sources', 'methodology': 'method'}[kind]
            W.write_page(c, l, tpl, urls[l], urls, dict(
                title=t[key + '_title'].replace(' | BlokVolt', ''), h1=t[key + '_h1'], description=t[key + '_desc'],
                T=t, crumbs=None, kick=None, jsonld=None, data_date=W.fmt_date(c.date), n_sources=n_sources,
                about_data=ABOUT_DATA[l], download=DOWNLOAD[l]), 'shell')
            out.append(urls[l])
    if os.environ.get('BV_WORLD_HOME') == '1':
        counts = (manifest or {}).get('counts') or {}
        for l in LANGS:
            t = T[l]
            lead = ''
            if counts.get('sites') and counts.get('countries'):
                n = W.fmt_num(counts['sites'], W.L[l]) + ' ' + W.pl_form(counts['sites'], t['pl_loc'], l)
                k = W.fmt_num(counts['countries'], W.L[l]) + ' ' + W.pl_form(counts['countries'], t['pl_cc'], l)
                lead = t['home_lead'].format(n=n, c=k)
            countries = sorted(((c.N.country(p['cc'], l), c.site.country(p['cc'], l)) for p in c.site.pages
                                if p['type'] == 'country' and l in c.site.langs(p)), key=lambda x: x[0])
            locals_ = [dict(path=h['path'], name=h['loc']['country'], hl=h['loc']['hreflang'], lang=h['loc']['html'])
                       for h in c.local_hubs]
            W.write_page(c, l, 'world_home.html', HOME[l], HOME, dict(
                title=t['home_title'].replace(' | BlokVolt', ''), h1=t['home_h1'], description=t['home_desc'], T=t,
                lead=lead, crumbs=None, kick=t['home_kick'], jsonld=None, data_date=W.fmt_date(c.date),
                countries=countries, regional=locals_, map_url=MAP[l], hub_url=HUB[l],
                search_url=f'/assets/world/search-index.json?v={sver}', home_js=f'/assets/world/world-home.js?v={hver}'), 'home')
            out.append(HOME[l])
    print(f"world shell: {len(out)} pages ({', '.join(out[:3])} …), search index {n_idx} places; home {'on' if os.environ.get('BV_WORLD_HOME') == '1' else 'off'}")


def shutil_copy(a, b):
    import shutil
    shutil.copy2(a, b)


def selftest():
    T = load_strings()
    ok = True
    for l in LANGS:
        if set(T[l]) != set(T['en']):
            print('FAIL keys', l); ok = False
    bad = [k for k, v in T['sr'].items() if re.search(r'\b(mi|naš|naša|naše|naši|odmah|redakcija)\b|24/7|[А-Яа-я]', v, re.I)]
    if bad:
        print('FAIL sr words', bad); ok = False
    for l in LANGS:
        for k in ('home_title', 'about_title', 'sources_title', 'method_title'):
            if re.search(r'\d', T[l][k]):
                print('FAIL digit in title', l, k); ok = False
    if any('Evolako' in v for l in LANGS for v in T[l].values()):
        print('FAIL Evolako'); ok = False
    print('world_shell selftest:', 'OK' if ok else 'FAIL')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(selftest() if sys.argv[1:] == ['selftest'] else 0)
