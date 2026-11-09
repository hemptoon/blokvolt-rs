# -*- coding: utf-8 -*-
"""World map of blokvolt.com — /map/ (EN), /sr/mapa/ (SR), /ru/karta/ (RU). Task K2 of pool 2, P1 §2, contract v1 §3–5, §8–11.

Called once by scripts/gen_com.py (one line in main(), after copy_assets() and before bust()):
    __import__('world_map').build(sys.modules[__name__])
It renders templates/com2/world_map.html three times through gen_com's render() and copies its own files:
    /assets/world/world-map.js, /assets/world/world-map.css   (from static/com/)
    /assets/vendor/pmtiles-4.5.0/pmtiles.js + LICENSE         (npm pmtiles@4.5.0, dist/pmtiles.js, BSD-3-Clause; fflate MIT inside)
The map reads its data at run time from content/world/config.json → data_base (latest.json → manifest → PMTiles and card
files; nothing of it is in this repository) and sends "Prijavi grešku" to reports_api (contract §10; no button when empty).

While config.public is false every page carries <meta name="robots" content="noindex,nofollow">, stays out of the sitemap
and no existing page links to it (contract §9). All interface words: content/world/strings_map.json, {key: {en, sr, ru}};
the build stops when a language or a key used by the template or the script is missing.

Local test data: BV_WORLD_DATA=<url ending in /> and BV_WORLD_REPORTS=<url or empty> override config.json for one build
(scripts/qa/world_map_test.py does that); the committed config never points at a test server.

Usage:  python3 scripts/world_map.py --selftest     (checks strings, config, the JS keys, then builds dist-com into a temp
                                                     folder and checks the three pages; exit 1 on any problem)"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
WORLD = ROOT / 'content' / 'world'
STATIC = ROOT / 'static' / 'com'
PMTILES_VER = '4.5.0'
VENDOR = ROOT / 'static' / 'assets' / 'vendor' / f'pmtiles-{PMTILES_VER}'
LANGS = ('en', 'sr', 'ru')
PAGES = {'en': '/map/', 'sr': '/sr/mapa/', 'ru': '/ru/karta/'}
# pages of task K3 (contract §8); linked from the map only through the script, so gen_com's link check does not depend on K3
ABOUT = {'en': '/charging-stations/about-data/', 'sr': '/sr/punjaci/o-podacima/', 'ru': '/ru/zaryadki/o-dannyh/'}
DOWNLOAD = {'en': '/charging-stations/download/', 'sr': '/sr/punjaci/preuzimanje/', 'ru': '/ru/zaryadki/skachat/'}
LOCS = {
    'en': dict(key='en', html='en', hreflang='en', og='en_GB', code='EN', dec='.', thou=','),
    'sr': dict(key='sr', html='sr-Latn', hreflang='sr', og='sr_RS', code='SR', dec=',', thou='.'),
    'ru': dict(key='ru', html='ru', hreflang='ru', og='ru_RU', code='RU', dec=',', thou=' ', script='cyrl'),
}
SWITCH = [('en', PAGES['en'], 'English', 'en'), ('sr', PAGES['sr'], 'Srpski', 'sr'), ('ru', PAGES['ru'], 'Русский', 'ru')]
STYLE = 'https://tiles.openfreemap.org/styles/positron'     # the same base map as /mapa/ (OpenFreeMap, no key)
FONT = ['Noto Sans Bold']                                   # the label font of the positron style (as /mapa/)
VIEW = {'center': [12.0, 50.0], 'zoom': 3.4}                # Europe when the link has no #z/lat/lon
# keys the script builds at run time ('acc_' + access_class, 'r_' + report type)
DYN_KEYS = ['acc_' + a for a in ('public', 'public_membership', 'public_pay_at_location', 'public_notice_required',
                                  'restricted_customers_staff', 'restricted_private', 'private_notice_required', 'unknown')] + \
           ['r_' + x for x in ('ne_postoji', 'ne_radi', 'lokacija', 'snaga', 'nije_javni', 'drugo')]
CHROME = ('skip', 'home', 'menu', 'country_menu', 'ft_claim', 'ft_checked', 'ft_data', 'report', 'fix_subject', 'ft_charging', 'ft_region')
FORBIDDEN = [r'\bodmah\b', r'24/7', r'evolako', r'\bredakcij', r'\bmi\s', r'proverili smo', r'računamo', r'javimo']


def ver(p):
    return hashlib.sha1(Path(p).read_bytes()).hexdigest()[:10]


def load_strings():
    """content/world/strings_map.json → {lang: {key: text}}; stops the build when a language is missing or empty."""
    raw = json.load(open(WORLD / 'strings_map.json', encoding='utf-8'))
    bad = [f'{k}: {lang}' for k, v in raw.items() for lang in LANGS if not isinstance(v, dict) or not str(v.get(lang) or '').strip()]
    if bad:
        raise SystemExit('content/world/strings_map.json: missing translations — ' + ', '.join(bad[:20]))
    used = set(re.findall(r"\bt\('([a-z0-9_]+)'", (STATIC / 'world-map.js').read_text(encoding='utf-8')))
    used |= set(re.findall(r'\bT\.([a-z0-9_]+)', (ROOT / 'templates' / 'com2' / 'world_map.html').read_text(encoding='utf-8')))
    used |= set(DYN_KEYS) | {'ch_' + k for k in CHROME} | {'title', 'description', 'ch_nav_map', 'ch_nav_rs', 'ch_nav_region'}
    missing = sorted(k for k in used if k not in raw and not k.endswith('_'))
    if missing:
        raise SystemExit('content/world/strings_map.json: keys used by the map but missing — ' + ', '.join(missing))
    for k, v in raw.items():
        for lang in LANGS:
            for pat in FORBIDDEN:
                if re.search(pat, v[lang], re.I) and not k.startswith('ch_ft_data'):
                    raise SystemExit(f'content/world/strings_map.json: "{k}" ({lang}) has a forbidden word ({pat}): {v[lang]}')
    if re.search(r'\d', ''.join(raw['title'][lang] for lang in LANGS)):
        raise SystemExit('content/world/strings_map.json: a <title> must not hold a number (RUNBOOK 3.34)')
    return {lang: {k: v[lang] for k, v in raw.items()} for lang in LANGS}


def load_config():
    """content/world/config.json (contract §9); BV_WORLD_DATA / BV_WORLD_REPORTS override it for a local test build."""
    p = WORLD / 'config.json'
    if not p.exists():
        raise SystemExit('content/world/config.json is missing (contract §9)')
    c = json.load(open(p, encoding='utf-8'))
    if not isinstance(c.get('public'), bool) or not isinstance(c.get('data_base'), str) or not isinstance(c.get('reports_api'), str):
        raise SystemExit('content/world/config.json: needs "public" (bool), "data_base" and "reports_api" (strings)')
    c = dict(c)
    if os.environ.get('BV_WORLD_DATA'):
        c['data_base'] = os.environ['BV_WORLD_DATA']
    if 'BV_WORLD_REPORTS' in os.environ:
        c['reports_api'] = os.environ['BV_WORLD_REPORTS']
    if not c['data_base'].endswith('/'):
        c['data_base'] += '/'
    return c


def chrome(lang, T, G):
    """Header and footer words (S) and the menu (NAV) for a page of the world map."""
    if lang == 'en':
        S = dict(G.STRINGS['en'])
        S.setdefault('ft_charging', T['ch_ft_charging'])
        S.setdefault('ft_region', T['ch_ft_region'])
        return S, list(G.EN_NAV)
    S = {k: T['ch_' + k] for k in CHROME}
    rs = G.RS + ('/ru/' if lang == 'ru' else '/')
    NAV = [(PAGES[lang], T['ch_nav_map'], 'map'), (rs, T['ch_nav_rs'], 'rs'), ('/', T['ch_nav_region'], 'region')]
    return S, NAV


def copy_files(OUT):
    a = OUT / 'assets'
    (a / 'world').mkdir(parents=True, exist_ok=True)
    shutil.copy2(STATIC / 'world-map.js', a / 'world' / 'world-map.js')
    shutil.copy2(STATIC / 'world-map.css', a / 'world' / 'world-map.css')
    shutil.copytree(VENDOR, a / 'vendor' / f'pmtiles-{PMTILES_VER}', dirs_exist_ok=True)
    # base.html names the share image by language: og-sr / og-ru do not exist on blokvolt.com, so they reuse og-en
    for lang in ('sr', 'ru'):
        dst = a / 'og' / f'og-{lang}.png'
        if not dst.exists() and (a / 'og' / 'og-en.png').exists():
            shutil.copy2(a / 'og' / 'og-en.png', dst)


def build(G):
    """Render the three pages into G.OUT with gen_com's environment (G = the gen_com module). Returns the page paths."""
    STR = load_strings()
    cfg = load_config()
    OUT = G.OUT
    copy_files(OUT)
    v_js, v_css = ver(STATIC / 'world-map.js'), ver(STATIC / 'world-map.css')
    u = urlparse(cfg['data_base'])
    origin = f'{u.scheme}://{u.netloc}' if u.netloc else G.SITE
    alts = [(LOCS[l]['hreflang'], G.SITE + PAGES[l]) for l in LANGS] + [('x-default', G.SITE + PAGES['en'])]
    locals_ = [dict(loc=l, path=f"/{l['dir']}/") for l in G.BUILT]
    out = []
    for lang in LANGS:
        T = STR[lang]
        S, NAV = chrome(lang, T, G)
        import world_shell   # G0: with the world pages built in the same run, the world menu and footer block
        WFT = None
        if world_shell.active():
            NAV, WFT = world_shell.nav(lang), world_shell.footer(lang)
        wm_cfg = {'lang': lang, 'data_base': cfg['data_base'], 'reports_api': cfg['reports_api'], 'style': STYLE,
                  'center': VIEW['center'], 'zoom': VIEW['zoom'], 'font': FONT, 'about': ABOUT[lang], 'download': DOWNLOAD[lang], 'pages': PAGES,
                  'prices': (getattr(G, 'WORLD_PRICES', None) or {}).get('map_json', '')}   # G3: price line of the card
        ctx = dict(WORLD_FT=WFT, LOC=LOCS[lang], S=S, NAV=NAV, SWITCH=SWITCH, home=PAGES[lang] if lang != 'en' else '/', section='map',
                   COUNTRIES=G.countries, LOCALS=locals_, PAGES={'method': None}, T=T, title=T['title'],
                   description=T['description'], alts=alts, public=cfg['public'], noindex=False,
                   wm_cfg=json.dumps(wm_cfg, ensure_ascii=False).replace('</', '<\\/'),
                   wm_i18n=json.dumps(T, ensure_ascii=False).replace('</', '<\\/'),
                   v_js=v_js, v_css=v_css, pmtiles_ver=PMTILES_VER, data_origin=origin)
        G.render('world_map.html', PAGES[lang], ctx, priority='0.6', sitemap=cfg['public'])
        out.append(PAGES[lang])
    print(f"world map: {', '.join(out)} ({'public' if cfg['public'] else 'noindex, not in the sitemap'}; data {cfg['data_base']})")
    return out


# ------------------------------------------------------------------ self-test
def selftest():
    errs = []
    try:
        STR = load_strings()
        load_config()
    except SystemExit as e:
        print('FAIL', e)
        return 1
    # Serbian strings through the site's linter (ekavica, "vi", no "mi"), when it can be imported
    try:
        sys.path.insert(0, str(ROOT / 'scripts'))
        import lint_sr
        sr_text = '\n\n'.join(v for k, v in STR['sr'].items() if not k.startswith('ch_ft_data'))
        e, w, _ = lint_sr.lint_text(sr_text)
        if e:
            errs.append(f'lint_sr errors: {e}')
        print(f'lint_sr: {len(e) if hasattr(e, "__len__") else e} errors, {len(w) if hasattr(w, "__len__") else w} warnings')
    except Exception as ex:  # the linter is optional here
        print('lint_sr not run:', ex)
    for f in ('pmtiles.js', 'LICENSE'):
        if not (VENDOR / f).exists():
            errs.append(f'missing {VENDOR / f}')
    tmp = Path(tempfile.mkdtemp(prefix='wm-selftest-'))
    env = dict(os.environ, BV_COM_OUT=str(tmp / 'dist-com'))
    r = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'gen_com.py')], cwd=ROOT, env=env, capture_output=True, text=True)
    print(r.stdout.strip().splitlines()[-1] if r.stdout.strip() else '', r.stderr.strip()[-500:])
    if r.returncode:
        errs.append(f'gen_com.py exit {r.returncode}')
    out = tmp / 'dist-com'
    public = json.load(open(WORLD / 'config.json', encoding='utf-8'))['public']
    sm = (out / 'sitemap.xml').read_text(encoding='utf-8') if (out / 'sitemap.xml').exists() else ''
    for lang, path in PAGES.items():
        p = out / path.strip('/') / 'index.html'
        if not p.exists():
            errs.append(f'{path}: not built')
            continue
        h = p.read_text(encoding='utf-8')
        if not public and '<meta name="robots" content="noindex,nofollow">' not in h:
            errs.append(f'{path}: no noindex,nofollow')
        if not public and path in sm:
            errs.append(f'{path}: in the sitemap')
        if f'<html lang="{LOCS[lang]["html"]}">' not in h:
            errs.append(f'{path}: wrong lang')
        title = re.search(r'<title>(.*?)</title>', h).group(1)
        if re.search(r'\d', title):
            errs.append(f'{path}: number in <title>')
        for pat in (r'odmah', r'24/7', r'Evolako', r'evolako\.png'):
            if re.search(pat, h):
                errs.append(f'{path}: forbidden "{pat}"')
        if '/assets/world/world-map.js?v=' not in h or f'/assets/vendor/pmtiles-{PMTILES_VER}/pmtiles.js' not in h:
            errs.append(f'{path}: script tags missing')
    if not public:
        # no existing page may link to the world map while it is not public
        for f in out.rglob('*.html'):
            rel = '/' + str(f.relative_to(out).parent).strip('.') + '/'
            if rel.replace('//', '/') in PAGES.values():
                continue
            t = f.read_text(encoding='utf-8')
            for path in PAGES.values():
                if f'href="{path}' in t or f'href="https://blokvolt.com{path}' in t:
                    errs.append(f'{f.relative_to(out)} links to {path}')
    shutil.rmtree(tmp, ignore_errors=True)
    for e in errs:
        print('FAIL', e)
    print('world_map selftest:', 'OK' if not errs else f'{len(errs)} problem(s)')
    return 1 if errs else 0


if __name__ == '__main__':
    if '--selftest' in sys.argv:
        sys.exit(selftest())
    print(__doc__)
