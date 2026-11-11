# -*- coding: utf-8 -*-
"""World widgets and open data of blokvolt.com (task G5 of the bvcom pool, RUNBOOK 3.42).

Pages (EN, SR, RU):
  /embed/map/ · /sr/embed/mapa/ · /ru/embed/karta/          the world map (static/com/world-map.js, cfg.embed) for an iframe on
                                                            any site: no header or footer, noindex, never in the sitemap
  /map-for-your-site/ · /sr/mapa-za-vas-sajt/ · /ru/karta-dlya-sajta/   configurator: country, city/view, network, power,
                                                            language, theme, height → live preview + the iframe code
  /developers/ · /sr/za-programere/ · /ru/razrabotchikam/   widget parameters, the ODbL CSV (link to "Download"), Balkan
                                                            JSON files, update rhythm, attribution, "Request access" form
Called by scripts/gen_com.py after world_shell (one line); runs only together with the world pages (BV_WORLD_PAGES), like
world_shell. Words: content/world/strings_embed.json ({key: {en, sr, ru}}); the build stops on a missing language.

Framing: dist-com/_headers (Cloudflare Pages) gets Content-Security-Policy: frame-ancestors * for the three widget paths
only; every other page of the world layer gets frame-ancestors 'self' through the same file. GitHub Pages (prod .com today)
ignores _headers and sends no framing header at all, so the widget works there too.

View counts (host name only) and the request form go to the blokvolt.rs worker: config.json "widget_api" (POST
/api/svet/vidzet) and "requests_api" (POST /api/svet/zahtev). Both are empty until "релиз G5" → the widget sends nothing and
the form says it is a preview (demo mode). BV_WORLD_WIDGET_API / BV_WORLD_REQUESTS_API override them for a local test.

    python3 scripts/world_embed.py selftest
"""
import csv
import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORLD = ROOT / 'content' / 'world'
STATIC = ROOT / 'static' / 'com'
sys.path.insert(0, str(Path(__file__).resolve().parent))
import world_i18n as I   # noqa: E402  LANG0: languages and section paths from the registry (config.json / slugs.json)
LANGS = I.langs()
EMBED = {l: I.slugs(l)['embed'] for l in LANGS}      # /embed/map/ /sr/embed/mapa/ /ru/embed/karta/ /de/embed/map/ …
CONF = {l: I.slugs(l)['map_conf'] for l in LANGS}    # /map-for-your-site/ /sr/mapa-za-vas-sajt/ /ru/karta-dlya-sajta/ …
DEV = {l: I.slugs(l)['developers'] for l in LANGS}   # /developers/ /sr/za-programere/ /ru/razrabotchikam/ …
STYLE_DARK = 'https://tiles.openfreemap.org/styles/dark'
FORBIDDEN = [r'\bodmah\b', r'24/7', r'evolako', r'\bredakcij', r'\bmi\s', r'\bnaš', r'\bмы\b', r'\bнаш', r'редакци', r'\bwe\b', r'\bour\b', r'сразу']
# the CSP of the widget pages as <meta> (all but frame-ancestors, which a <meta> cannot carry); data hosts are added at build
CSP = ["default-src 'self'", "script-src 'self'", "style-src 'self' 'unsafe-inline'",
       "img-src 'self' data: blob: https://tiles.openfreemap.org", "font-src 'self' https://tiles.openfreemap.org",
       "worker-src 'self' blob:", "child-src 'self' blob:", "object-src 'none'", "base-uri 'self'", "form-action 'self'"]


def load_strings():
    raw = json.load(open(WORLD / 'strings_embed.json', encoding='utf-8'))
    miss = [f'{k}.{l}' for k, v in raw.items() for l in I.BASE if l in LANGS and not str(v.get(l) or '').strip()]
    if miss:
        raise SystemExit('content/world/strings_embed.json: missing translations — ' + ', '.join(miss[:20]))
    raw = I.strings_raw('embed', LANGS)   # LANG0: other languages from i18n/<code>/strings_embed.json (stops on a missing key)
    for k, v in raw.items():
        for l in LANGS:
            for pat in I.forbidden(FORBIDDEN, l):
                if re.search(pat, v[l], re.I):
                    raise SystemExit(f'content/world/strings_embed.json: "{k}" ({l}) has a forbidden word ({pat}): {v[l]}')
    for k in ('cf_title', 'dv_title', 'emb_title'):
        if re.search(r'\d', ''.join(raw[k].values())):
            raise SystemExit(f'content/world/strings_embed.json: a <title> must not hold a number ({k}, RUNBOOK 3.34)')
    return {l: {k: v[l] for k, v in raw.items()} for l in LANGS}


def api(cfg, key, env):
    v = os.environ.get(env)
    return v if v is not None else str(cfg.get(key) or '')


def countries(l):
    rows = list(csv.DictReader(open(WORLD / 'names' / 'countries.csv', encoding='utf-8')))
    if l not in I.BASE:   # LANG0: i18n/<code>/countries.csv first
        return sorted(((r['cc'], I.country_name(r, l)) for r in rows), key=lambda x: x[1])
    key = 'name_' + l
    return sorted(((r['cc'], r[key] or r['name_en']) for r in rows), key=lambda x: x[1])


def networks():
    rows = list(csv.DictReader(open(WORLD / 'names' / 'networks.csv', encoding='utf-8')))
    seen, out = set(), []
    for r in rows:
        if r['slug'] and r['slug'] not in seen:
            seen.add(r['slug'])
            out.append((r['slug'], r['name_display'] or r['network']))
    return sorted(out, key=lambda x: x[1].lower())


def headers(OUT):
    """_headers for Cloudflare Pages: the widget paths may be framed by any site, the rest of the world layer only by itself."""
    lines = ['# G5 (RUNBOOK 3.42): widgets may sit in an iframe on any site; other pages only on blokvolt.com itself',
             '# (the same pattern as /embed/* of blokvolt.rs: X-Frame-Options for all, detached for the widget paths)',
             '/*', '  X-Frame-Options: SAMEORIGIN', '  X-Content-Type-Options: nosniff']
    for p in EMBED.values():
        lines += [p + '*', '  ! X-Frame-Options', '  Content-Security-Policy: frame-ancestors *', '  X-Robots-Tag: noindex']
    h = OUT / '_headers'
    old = h.read_text(encoding='utf-8') + '\n' if h.exists() else ''
    h.write_text(old + '\n'.join(lines) + '\n', encoding='utf-8')


def run(G, c):
    """Called by gen_com.main() after world_shell.run() (c = world_pages' context, None without the world pages)."""
    if c is None:
        return
    import world_map
    W = sys.modules['world_pages']
    T = load_strings()
    MS = world_map.load_strings()
    cfg = world_map.load_config()
    wapi = api(cfg, 'widget_api', 'BV_WORLD_WIDGET_API')
    rapi = api(cfg, 'requests_api', 'BV_WORLD_REQUESTS_API')
    OUT = G.OUT
    a = OUT / 'assets' / 'world'
    a.mkdir(parents=True, exist_ok=True)
    for f in ('world-embed.css', 'world-widget.js'):
        shutil.copy2(STATIC / f, a / f)
    ver = {f: hashlib.sha1((a / f).read_bytes()).hexdigest()[:10] for f in ('world-embed.css', 'world-widget.js', 'world-map.js', 'world-map.css')}
    from urllib.parse import urlparse
    hosts = sorted({f'{u.scheme}://{u.netloc}' for u in (urlparse(x) for x in (cfg['data_base'], wapi, cfg.get('reports_api', ''))) if u.netloc})
    csp = '; '.join(CSP + ["connect-src 'self' https://tiles.openfreemap.org " + ' '.join(hosts)])
    out = []
    # ---- the widget pages
    for l in LANGS:
        t, M = T[l], MS[l]
        wm_cfg = {'lang': l, 'data_base': cfg['data_base'], 'reports_api': '', 'style': world_map.STYLE, 'style_dark': STYLE_DARK,
                  'center': world_map.VIEW['center'], 'zoom': world_map.VIEW['zoom'], 'font': world_map.FONT,
                  'about': G.SITE + world_map.ABOUT[l], 'download': G.SITE + world_map.DOWNLOAD[l], 'pages': world_map.PAGES,
                  'embed': {'open': G.SITE + world_map.PAGES[l], 'utm': 'world-map', 'views': wapi}}
        if l not in I.BASE:   # LANG0: number/date locale of the other languages (world-map.js: cfg.intl)
            wm_cfg.update(intl=I.reg(l)['intl'], dec=I.reg(l)['dec'], thou=I.reg(l)['thou'])
        html = G.env.get_template('world_embed.html').render(
            LOC=world_map.LOCS[l], T=M, E=t, SITE=G.SITE, canon=world_map.PAGES[l], CSP=csp, data_origin=hosts[0] if hosts else G.SITE,
            full=G.SITE + world_map.PAGES[l], pmtiles_ver=world_map.PMTILES_VER, v=ver,
            wm_cfg=json.dumps(wm_cfg, ensure_ascii=False).replace('</', '<\\/'),
            wm_i18n=json.dumps(M, ensure_ascii=False).replace('</', '<\\/'))
        for n, h in c.ver.items():   # the same cache-busting as the other world pages
            html = html.replace(f'/assets/{n}"', f'/assets/{n}?v={h}"')
        G.write(EMBED[l], html)
        out.append(EMBED[l])
    # ---- configurator and developers (normal world pages: header, footer, hreflang; noindex while the world is not public)
    nets = networks()
    n_fields = len(json.load(open(WORLD / 'download.json', encoding='utf-8'))['en']['fields'])
    dl = json.load(open(WORLD / 'download.json', encoding='utf-8'))
    balkan_all = [(x['cc'], f"/assets/region/{x['cc'].lower()}/stanice.json") for x in G.BUILT
                  if (OUT / 'assets' / 'region' / x['cc'].lower() / 'stanice.json').exists()]
    for l in LANGS:
        t = T[l]
        vz = {'site': G.SITE, 'embed': EMBED, 'map': world_map.PAGES, 'lang': l, 'copied': t['cf_copied'],
              'frame_title': {x: T[x]['cf_frame_title'] for x in LANGS}, 'src': {x: T[x]['cf_src'] for x in LANGS},
              'link': {x: T[x]['cf_link'] for x in LANGS}, 'bad': t['cf_view_bad']}
        W.write_page(c, l, 'world_embed_conf.html', CONF[l], CONF, dict(
            title=t['cf_title'].replace(' | BlokVolt', ''), h1=t['cf_h1'], description=t['cf_desc'], T=t, crumbs=None, kick=None,
            jsonld=None, data_date=W.fmt_date(c.date), COUNTRIES_ALL=countries(l), NETS=nets, MT=MS[l], dev_url=DEV[l],
            WLANGS=[(x, I.label(x)) for x in LANGS],
            preview_src=EMBED[l], map_url=world_map.PAGES[l], vz=json.dumps(vz, ensure_ascii=False).replace('</', '<\\/'),
            css=f"/assets/world/world-embed.css?v={ver['world-embed.css']}", js=f"/assets/world/world-widget.js?v={ver['world-widget.js']}"), 'conf')
        out.append(CONF[l])
        W.write_page(c, l, 'world_developers.html', DEV[l], DEV, dict(
            title=t['dv_title'].replace(' | BlokVolt', ''), h1=t['dv_h1'], description=t['dv_desc'], T=t, crumbs=None, kick=None,
            jsonld=None, data_date=W.fmt_date(c.date), conf_url=CONF[l], download=world_map.DOWNLOAD[l], embed_url=EMBED[l],
            open_p=t['dv_open_p'].format(n=n_fields), attribution=(dl[l] if l in dl else I.texts(l, 'download'))['attribution_p'],
            balkan=[(cc, dict(countries(l)).get(cc, cc), u) for cc, u in balkan_all],
            rs_dev=G.RS + {'sr': '/za-programere/', 'ru': '/ru/za-programere/'}.get(l, '/en/za-programere/'),
            requests_api=rapi, EMAIL=G.EMAIL,
            css=f"/assets/world/world-embed.css?v={ver['world-embed.css']}", js=f"/assets/world/world-widget.js?v={ver['world-widget.js']}"), 'developers')
        out.append(DEV[l])
    headers(OUT)
    print(f"world widgets (G5): {len(out)} pages ({', '.join(out[:3])} …); views {'→ ' + wapi if wapi else 'off (demo)'}; "
          f"requests {'→ ' + rapi if rapi else 'demo'}; {len(nets)} networks in the configurator")


def selftest():
    try:
        load_strings()
    except SystemExit as e:
        print('FAIL', e)
        return 1
    import subprocess
    r = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'qa' / 'world_embed_check.py'), '--strings-only'], cwd=ROOT)
    print('world_embed selftest:', 'OK' if r.returncode == 0 else 'FAIL')
    return r.returncode


if __name__ == '__main__':
    sys.exit(selftest() if sys.argv[1:] == ['selftest'] else 0)
