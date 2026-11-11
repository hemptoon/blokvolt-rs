"""Frame of the world layer of blokvolt.com (G0): one menu and one footer block for the world map and the world pages,
the short pages /about/, /sources/, /methodology/ (EN, SR, RU) that lead to "About the data", the home search (K3's static index of
countries and cities). The world home itself (/, /sr/, /ru/) is scripts/world_home.py (HOME2).

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
sys.path.insert(0, str(Path(__file__).resolve().parent))
import world_i18n as I   # noqa: E402  K8-i18n: languages and addresses from content/world/config.json + i18n/<code>/slugs.json
LANGS = I.langs()
_SL = {l: I.slugs(l) for l in LANGS}
MAP = {l: _SL[l]['map'] for l in LANGS}
HUB = {l: _SL[l]['hub'] for l in LANGS}
ABOUT_DATA = {l: HUB[l] + _SL[l]['about'] + '/' for l in LANGS}
DOWNLOAD = {l: HUB[l] + _SL[l]['download'] + '/' for l in LANGS}
SHELL = {
    'about': {l: _SL[l]['shell_about'] for l in LANGS},
    'sources': {l: _SL[l]['sources'] for l in LANGS},
    'methodology': {l: _SL[l]['methodology'] for l in LANGS},
}
HOME = {l: _SL[l]['home'] for l in LANGS}


def load_strings():
    raw = json.load(open(WORLD / 'strings_shell.json', encoding='utf-8'))
    miss = [f'{k}.{l}' for k, v in raw.items() for l in LANGS if l in I.BASE and not v.get(l)]
    if miss:
        raise SystemExit('world_shell: missing strings ' + ', '.join(miss))
    return I.load('shell', LANGS)   # other languages: i18n/<code>/strings_shell.json (stops on a missing key)


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
        if key == 'routes':   # HOME3: every route goes through Belgrade — not in the world menu (footer and regional guides)
            continue
        out.insert(len(out) - 1, (urls[l], labels[l], key))
    return out


# HOME3 (11.11.2026): one footer for the world — every world page, the map, and the English pages of gen_com (404,
# /partners/, /western-balkans/, the English guides of the Balkan countries). The local sections keep their own footer.
LOCAL_SECTIONS = [('wb', None), ('rs', None), ('hr', 'Hrvatska'), ('ba', 'Bosna i Hercegovina'), ('me', 'Crna Gora'),
                  ('mk', 'Северна Македонија'), ('al', 'Shqipëria'), ('xk', 'Kosova'), ('si', 'Slovenija')]
LOCAL_HTML = {'hr': ('hr', 'hr-HR'), 'ba': ('bs', 'bs-BA'), 'me': ('sr-Latn-ME', 'sr-ME'), 'mk': ('mk', 'mk-MK'),
              'al': ('sq', 'sq-AL'), 'xk': ('sq', 'sq'), 'si': ('sl', 'sl-SI')}
OG_WORLD = '/assets/world/hero/og-world.jpg'   # HOME3: the share picture of every world page (scripts/world_hero.py --og)
TERMS = {'en': '/terms/', 'sr': '/sr/uslovi/', 'ru': '/ru/usloviya/'}   # other languages lead to the English page


def terms_url(l):
    return TERMS.get(l, TERMS['en'])


def wfooter(l, G, built_locals=None):
    """Columns of the world footer (templates/com2/_wfooter.html): Charging · Western Balkans · Data & tools · BlokVolt."""
    T = load_strings()[l]
    sl = _SL[l]
    nav_l = {k: (u, n) for u, n, k in nav(l)}
    charging = [(MAP[l], T['nav_map']), (HUB[l], T['ft_hub_by'])]
    for k in ('prices', 'pay'):
        if k in nav_l:
            charging.append(nav_l[k])
    built_locals = set(built_locals if built_locals is not None else [x['dir'] for x in G.BUILT])
    wb = [('/western-balkans/', T['ft_wb_guide'], 'en', 'en'), (G.RS + {'en': '/en/', 'ru': '/ru/'}.get(l, '/'), T['ft_rs'], 'sr', 'sr')]
    for d, name in LOCAL_SECTIONS[2:]:
        if d in built_locals:
            wb.append((f'/{d}/', name, LOCAL_HTML[d][1], LOCAL_HTML[d][0]))
    if 'routes' in sl:
        wb.append((sl['routes'], T['ft_routes'], None, None))
    wb.append(('/partners/', T['ft_partners'], 'en', 'en'))
    data = [(DOWNLOAD[l], T['ft_open']), (sl['map_conf'], T['ft_widget']), (sl['developers'], T['ft_dev'])]
    if PRESS:
        data.append((PRESS[l][0], T['ft_press2']))
    data += [(sl['b2b'], T['ft_b2b']), (SHELL['sources'][l], T['ft_sources']), (SHELL['methodology'][l], T['ft_method'])]
    bv = [(SHELL['about'][l], T['ft_about']), ('mailto:' + G.EMAIL, T['contact'] + ' (' + G.EMAIL + ')'), (terms_url(l), T['ft_terms'])]
    import datetime
    return {'cols': [(T['ft_c_charging'], [(u, n, None, None) for u, n in charging]), (T['ft_c_wb'], wb),
                     (T['ft_c_data'], [(u, n, None, None) for u, n in data]), ('BlokVolt', [(u, n, None, None) for u, n in bv])],
            'line': T['ft_line'], 'nopaid': T['ft_nopaid'], 'sources': SHELL['sources'][l], 'sources_name': T['ft_sources'],
            'year': datetime.date.today().year, 'lang': T['ft_lang']}


def footer(l):
    """Links of the world footer block (_footer.html, WORLD_FT)."""
    T = load_strings()[l]
    return {'h': T['ft_h'], 'links': [(ABOUT_DATA[l], T['ft_about_data']), (DOWNLOAD[l], T['ft_download']),
                                      (SHELL['sources'][l], T['ft_sources']), (SHELL['methodology'][l], T['ft_method']),
                                      (SHELL['about'][l], T['ft_about'])] + ([PRESS[l]] if PRESS else []) + __import__('world_b2b').footer_link(l)}


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
                about_data=ABOUT_DATA[l], download=DOWNLOAD[l], terms=terms_url(l)), 'shell')
            out.append(urls[l])
    # HOME3 (11.11.2026): terms of use and privacy in EN, SR, RU; the other languages link to the English page (no hreflang
    # to pages that do not exist). The visit-counting paragraph is the one of /about/ (content/com/counter_note.json).
    TJ = json.load(open(WORLD / 'terms.json', encoding='utf-8'))
    cn = json.load(open(ROOT / 'content' / 'com' / 'counter_note.json', encoding='utf-8'))
    turls = {l: TERMS[l] for l in TERMS if l in LANGS}
    for l in turls:
        tt = TJ[l]
        fill = lambda x: x.replace('{sources}', SHELL['sources'][l]).replace('{about_data}', ABOUT_DATA[l]) \
            .replace('{download}', DOWNLOAD[l]).replace('{email}', G.EMAIL).replace('{date}', W.fmt_date(c.date))   # noqa: E731
        tt = dict(tt, sections=[(h, [fill(p) for p in ps]) for h, ps in tt['sections']], contact_p=fill(tt['contact_p']))
        W.write_page(c, l, 'world_shell_terms.html', turls[l], turls, dict(
            title=tt['title'], h1=tt['h1'], description=tt['desc'], T=T[l], TT=tt, CN=cn.get(l), crumbs=None, kick=None,
            jsonld=None), 'shell')
        out.append(turls[l])
    # HOME2 (11.11.2026): the world home is written by scripts/world_home.py (after prices, pay and widgets)
    print(f"world shell: {len(out)} pages ({', '.join(out[:3])} …), search index {n_idx} places")


def search_url(a, l, sver):
    """K8: an extra language searches its own index (search-index-<code>.json: en, sr, ru + that language)."""
    if l in I.BASE:
        return f'/assets/world/search-index.json?v={sver}'
    import hashlib
    f = a / f'search-index-{l}.json'
    return f'/assets/world/{f.name}?v={hashlib.sha1(f.read_bytes()).hexdigest()[:10]}'


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
            if re.search(r'\d', str(T[l][k])):
                print('FAIL digit in title', l, k); ok = False
    if any('Evolako' in str(v) for l in LANGS for v in T[l].values()):
        print('FAIL Evolako'); ok = False
    print('world_shell selftest:', 'OK' if ok else 'FAIL')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(selftest() if sys.argv[1:] == ['selftest'] else 0)
