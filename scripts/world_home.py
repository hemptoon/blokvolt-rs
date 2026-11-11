"""World home of blokvolt.com — /, /sr/, /ru/ (task HOME2, 11.11.2026; replaces the G0 dev home of world_shell.py).

The first screen is the map: a "night lights" picture of the public layer (scripts/world_hero.py, static/com/hero/) that is
swapped in place for a live MapLibre map on the first tap or click (static/com/world-hero-map.js, loaded only then).
Below it: countries by region, what charging costs, how to pay and road trips, "is it working?", open data and tools,
regional guides (Western Balkans, Serbia) and where the data comes from.

Every number comes from the data of the build: the manifest (places, countries, date), the pages bundle (hub: public places
per country), the price model of world_prices (tariffs.json, home_electricity.json), world_pay (countries and routes) and
content/world/home/hero.json (views of the pictures, Asia-Pacific countries by size). Nothing is typed in by hand.

On by default when the world layer is built (BV_WORLD_PAGES); BV_WORLD_HOME=0 keeps the old regional home at / instead.
The old home lives on at /western-balkans/ (gen_com.py) either way.
Strings: content/world/strings_home.json ({key: {en, sr, ru}}); the build stops on a missing language or key.

Hook in gen_com.main(): world_home.run(G, wc) after world_embed.run(), before the world sitemaps.

    python3 scripts/world_home.py selftest
"""
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
HERO = STATIC / 'hero'
sys.path.insert(0, str(Path(__file__).resolve().parent))
import world_i18n as I   # noqa: E402
LANGS = I.langs()
HOME = {l: I.slugs(l)['home'] for l in LANGS}
WB = '/western-balkans/'
FORBIDDEN = [r'\bodmah\b', r'24/7', r'evolako', r'\bredakcij', r'\bmi\s', r'popust', r'скидк', r'\batest', r'\bwe\b', r'\bмы\b',
             r'\bnaš', r'\bour\b', r'\bнаш']
EUROPE_TOP, NA_TOP = 12, 2
PRICE_N = 6
PAY_N, ROUTES_N = 6, 6
# Asia/* time zones west of the Asia-Pacific picture: these visitors see Europe first (Middle East, Caucasus)
TZ_WEST = ['Dubai', 'Tbilisi', 'Yerevan', 'Baku', 'Jerusalem', 'Tel_Aviv', 'Beirut', 'Amman', 'Riyadh', 'Qatar', 'Tehran',
           'Baghdad', 'Kuwait', 'Bahrain', 'Muscat', 'Nicosia', 'Famagusta', 'Damascus', 'Gaza', 'Hebron', 'Aden']


def enabled():
    return bool(os.environ.get('BV_WORLD_PAGES')) and os.environ.get('BV_WORLD_HOME', '1') != '0'


def load_strings():
    raw = json.load(open(WORLD / 'strings_home.json', encoding='utf-8'))
    out = {}
    for l in LANGS:
        if l in I.BASE:
            miss = [k for k, v in raw.items() if not str(v.get(l) or '').strip()]
            if miss:
                raise SystemExit(f'content/world/strings_home.json: missing {l} for ' + ', '.join(miss))
            out[l] = {k: v[l] for k, v in raw.items()}
        else:   # K8: an extra language brings its own file; the build stops on a missing key
            p = I.i18n_dir(l) / 'strings_home.json'
            if not p.exists():
                raise SystemExit(f'world_home: {p} is missing (language {l} is enabled)')
            tr = json.load(open(p, encoding='utf-8'))
            miss = [k for k in raw if not tr.get(k)]
            if miss:
                raise SystemExit(f'world_home: {p} misses {miss[:5]}')
            out[l] = {k: tr[k] for k in raw}
    for l, d in out.items():
        for k, v in d.items():
            for pat in I.forbidden(FORBIDDEN, l):
                if re.search(pat, v, re.I):
                    raise SystemExit(f'content/world/strings_home.json: "{k}" ({l}) has a forbidden word ({pat}): {v}')
    return out


def hero_meta():
    p = WORLD / 'home' / 'hero.json'
    if not p.exists():
        raise SystemExit('world_home: content/world/home/hero.json is missing — run scripts/world_hero.py on the public layer')
    return json.load(open(p, encoding='utf-8'))


def copy_hero(G, meta):
    """static/com/hero/* → /assets/world/hero/ ; returns {name: versioned URL} (only files that exist)."""
    dst = G.OUT / 'assets' / 'world' / 'hero'
    dst.mkdir(parents=True, exist_ok=True)
    urls = {}
    for name in list(meta['files']) + ['og-world.jpg']:   # og-world.jpg is made once (--og), not every week
        src = HERO / name
        if not src.exists():
            continue
        shutil.copy2(src, dst / name)
        urls[name] = f'/assets/world/hero/{name}?v={hashlib.sha1(src.read_bytes()).hexdigest()[:10]}'
    return urls


def copy_js(G):
    a = G.OUT / 'assets' / 'world'
    out = {}
    for n in ('world-home.js', 'world-hero-map.js', 'world-home.css'):
        shutil.copy2(STATIC / n, a / n)
        out[n] = f"/assets/world/{n}?v={hashlib.sha1((a / n).read_bytes()).hexdigest()[:10]}"
    return out


def built(G, url):
    p = G.OUT / (url.strip('/') + '/index.html' if url != '/' else 'index.html')
    return p.exists()


def pictures(meta, urls):
    """[(region, {shape: {avif, webp, w, h, c, z}})] for the template and the script."""
    out = {}
    for reg, shapes in meta['views'].items():
        out[reg] = {}
        for shp, v in shapes.items():
            d = dict(c=v['c'], z=v['z'], w=v['w'], h=v['h'])
            for fmt in ('avif', 'webp'):
                n = f'hero-{reg}-{shp}.{fmt}'
                if n in urls:
                    d[fmt] = urls[n]
            if 'webp' not in d:
                raise SystemExit(f'world_home: hero-{reg}-{shp}.webp is missing in static/com/hero/')
            out[reg][shp] = d
    return out


def run(G, c):
    if c is None or not enabled():
        print('world home: off (old regional home at /)' if c is not None else 'world home: skipped (no world layer)')
        return None
    W = sys.modules['world_pages']
    import world_shell
    import world_map
    T = load_strings()
    meta = hero_meta()
    hurls = copy_hero(G, meta)
    assets = copy_js(G)
    pics = pictures(meta, hurls)
    mp = os.environ.get('BV_WORLD_MANIFEST')
    manifest = json.load(open(mp, encoding='utf-8')) if mp and Path(mp).exists() else {}
    counts = manifest.get('counts') or {}
    mdate = manifest.get('date') or c.date
    hub = next((p['data'] for p in c.site.pages if p['type'] == 'hub'), {})
    cfg = world_map.load_config()
    # search index (K3) as world_shell prepares it
    a = G.OUT / 'assets' / 'world'
    idx = a / 'search-index.json'
    sver = hashlib.sha1(idx.read_bytes()).hexdigest()[:10] if idx.exists() else '0'
    P = getattr(G, 'WORLD_PRICES', None)
    R = getattr(G, 'WORLD_PAY', None)
    press = getattr(world_shell, 'PRESS', None)
    import world_embed
    import world_b2b  # noqa: F401  (footer link is added by world_shell.footer)
    out = []
    for l in LANGS:
        t = T[l]
        Lc = W.L[l]
        num = lambda x, d=0: W.fmt_num(x, Lc, d)   # noqa: E731
        pl = lambda x, k: f"{num(x)} {I.pl_form(x, t[k], l)}"   # noqa: E731
        stat = []
        if counts.get('sites'):
            stat.append(pl(counts['sites'], 'pl_places'))
        if counts.get('countries'):
            stat.append(pl(counts['countries'], 'pl_countries'))
        stat.append(t['data_as_of'].format(date=W.fmt_date(mdate)))

        def ccard(cc, n, dc50):
            url = c.site.country(cc, l)
            ok = c.site.has(cc, l) and built(G, url)
            return dict(cc=cc, name=c.N.country(cc, l), n=n, n_txt=num(n), unit=I.pl_form(n, t['pl_public'], l),
                        dc=t['dc_line'].format(n=num(dc50)) if dc50 else '', url=url if ok else c.map_url(l, {'zemlja': cc}),
                        page=ok)
        rows = hub.get('countries') or []
        eu = [ccard(cc, n, d) for cc, n, d, r in rows if r == 'EU' and cc not in hub.get('balkan', [])][:EUROPE_TOP]
        na = [ccard(cc, n, d) for cc, n, d, r in rows if r == 'NA'][:NA_TOP]
        allc = sorted([ccard(cc, n, d) for cc, n, d, r in rows], key=lambda x: x['name'])
        below = sorted([dict(name=c.N.country(cc, l), url=c.map_url(l, {'zemlja': cc})) for cc, n, r in hub.get('countries_below', [])],
                       key=lambda x: x['name'])
        ap = []
        places_cc = (c.places or {}).get('cc', {}) if isinstance(c.places, dict) else {}
        for cc in meta.get('apac', []):
            if places_cc and cc not in places_cc:
                continue
            try:
                ap.append(dict(name=c.N.country(cc, l), url=c.map_url(l, {'zemlja': cc})))
            except SystemExit:
                continue
        # prices: the largest markets with a weighted DC average and a household price (world_prices model)
        prices = None
        if P:
            M = P['model']
            cand = [(cc, x) for cc, x in M.countries.items() if x['cls']['dc']['value'] and x['home'] and x['cls']['dc']['method'] == 'w']
            size = {cc: n for cc, n, _, _ in rows}
            cand.sort(key=lambda kv: -size.get(kv[0], 0))
            items = []
            for cc, x in cand[:PRICE_N]:
                dc, home = x['cls']['dc']['value'], x['home']
                url = P['country_pages'].get(cc, {}).get(l)
                items.append(dict(name=c.N.country(cc, l), dc=num(dc, 2), home=num(home, 2), dc_v=dc, home_v=home,
                                  ratio=t['p_ratio'].format(x=num(dc / home, 1)), url=url if url and built(G, url) else None))
            if items:
                hsrc = M.H.get('source', {})
                home_name = '; '.join(v['name'] for v in hsrc.values() if isinstance(v, dict) and v.get('name'))
                prices = dict(items=items, maxv=max(max(i['dc_v'], i['home_v']) for i in items),
                              src=t['p_src'].format(date=W.fmt_date(M.T['updated']), home=home_name), hub=P['hub'][l])
        pay, routes = [], []
        if R is not None:
            size = {cc: n for cc, n, _, _ in rows}
            for cc in sorted((cc for cc in R.countries if l in R.langs(cc)), key=lambda x: -size.get(x, 0))[:PAY_N]:
                u = R.pay_url(cc, l)
                if built(G, u):
                    pay.append(dict(name=R.cname(cc, l), url=u))
            for rt in R.RT['routes'][:ROUTES_N]:
                u = R.route_url(rt, l)
                if built(G, u):
                    routes.append(dict(name=R.route_title(rt, l), url=u))
        import world_pay
        tools = [(world_shell.DOWNLOAD[l], t['o_dl'], t['o_dl_p']), (world_embed.CONF[l], t['o_widget'], t['o_widget_p']),
                 (world_embed.DEV[l], t['o_dev'], t['o_dev_p'])]
        if press:
            tools.append((press[l][0], t['o_press'], t['o_press_p']))
        tools = [x for x in tools if built(G, x[0])]
        regional = [dict(path=WB, name=t['reg_wb'], hl='en', lang='en')] + \
                   [dict(path=h['path'], name=h['loc']['country'], hl=h['loc']['hreflang'], lang=h['loc']['html']) for h in c.local_hubs]
        site = G.SITE + HOME[l]
        jsonld = W.ld([
            {'@type': 'WebSite', '@id': G.SITE + '/#website', 'name': 'BlokVolt', 'url': site, 'inLanguage': Lc['html'],
             'description': t['desc'], 'publisher': {'@id': G.SITE + '/#org'},
             'potentialAction': {'@type': 'SearchAction', 'target': {'@type': 'EntryPoint', 'urlTemplate': site + '?q={search_term_string}'},
                                 'query-input': 'required name=search_term_string'}},
            {'@type': 'Organization', '@id': G.SITE + '/#org', 'name': 'BlokVolt', 'url': G.SITE + '/', 'email': G.EMAIL,
             'logo': G.SITE + '/assets/apple-touch-icon.png', 'description': t['org_desc'],
             'sameAs': [G.RS + '/']},
        ])
        hero_cfg = dict(lang=l, data_base=cfg['data_base'], pics=pics, map=HOME_MAP(l), font=world_map.FONT,
                        borders=hurls.get('borders.json'), lib='/assets/vendor/maplibre-6.11.1/maplibre-gl.mjs',
                        pmtiles=f'/assets/vendor/pmtiles-{world_map.PMTILES_VER}/pmtiles.js',
                        tz_west=TZ_WEST, near_err=t['near_err'], err=t['map_err'], label=t['map_label'])
        html = W.write_page(c, l, 'world_home.html', HOME[l], HOME, dict(
            title=t['title'].replace(' | BlokVolt', ''), description=t['desc'], h1=t['h1'], T=t, crumbs=None, kick=None,
            jsonld=jsonld, stat=stat, pics=pics, hero_cfg=json.dumps(hero_cfg, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/'),
            search_url=world_shell.search_url(a, l, sver), map_url=W.L[l]['map'], hub_url=c.site.hub(l),
            q_dc=W.L[l]['map'] + '?snaga=dc,hpc', q_hpc=W.L[l]['map'] + '?snaga=hpc',
            eu=eu, na=na, ap=ap, allc=allc, below=below, prices=prices, pay=pay, routes=routes,
            pay_hub=world_pay.PAY[l], routes_hub=world_pay.ROUTES[l], tools=tools, regional=regional,
            sources_url=world_shell.SHELL['sources'][l], method_url=world_shell.SHELL['methodology'][l],
            og_image=(G.SITE + hurls['og-world.jpg'].split('?')[0]) if 'og-world.jpg' in hurls else None,
            assets=assets, lcp=pics['eu']), 'home')
        out.append(HOME[l])
    js = sum((G.OUT / 'assets' / 'world' / n).stat().st_size for n in ('world-home.js',))
    print(f"world home: {', '.join(out)} — {counts.get('sites')} places, {counts.get('countries')} countries, data {mdate}; "
          f"Europe {len(eu)} cards, North America {len(na)}, Asia-Pacific {len(ap)}; prices {len(prices['items']) if prices else 0}; "
          f"pay {len(pay)}, routes {len(routes)}; pictures {', '.join(meta.get('formats', []))} of {meta.get('date')}; home JS {js // 1024} KB")
    return out


def HOME_MAP(l):
    return I.slugs(l)['map']


def selftest():
    ok = True
    T = load_strings()
    for l in LANGS:
        if set(T[l]) != set(T['en']):
            print('FAIL keys', l)
            ok = False
    for l in LANGS:
        if re.search(r'\d', T[l]['title'] + T[l]['h1']):
            print('FAIL digit in title/h1', l)
            ok = False
    bad = [k for k, v in T['sr'].items() if re.search(r'[А-Яа-я]', v) or re.search(r'\b(otvori|istraži|pronađi|traži)\b', v, re.I)]
    if bad:
        print('FAIL sr (Cyrillic or "ti" imperative)', bad)
        ok = False
    m = hero_meta()
    for reg in ('eu', 'na', 'ap'):
        for shp in ('w', 't'):
            v = m['views'][reg][shp]
            if not (HERO / f'hero-{reg}-{shp}.webp').exists():
                print('FAIL picture', reg, shp)
                ok = False
            for fmt in ('avif', 'webp'):
                f = HERO / f'hero-{reg}-{shp}.{fmt}'
                if f.exists() and f.stat().st_size > 150_000:
                    print('FAIL over 150 KB', f.name)
                    ok = False
            if not (1 <= v['z'] <= 6):
                ok = False
    print('world_home selftest:', 'OK' if ok else 'FAIL')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(selftest() if sys.argv[1:] == ['selftest'] else 0)
