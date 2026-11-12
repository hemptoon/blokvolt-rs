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
        else:   # K8/LANG0: an extra language brings its own file; production stops on a missing key, a preview shows "[EN] …"
            out[l] = I.load('home', [l])[l]
    for l, d in out.items():
        for k, v0 in d.items():
            for pat in I.forbidden(FORBIDDEN, l):
                v = ' '.join(v0.values()) if isinstance(v0, dict) else v0   # LANG0: CLDR plural objects of other languages
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
                n = f'hero-{reg}-{shp}-light.{fmt}'   # THEME (12.11.2026): the light picture, "l" + format
                if n in urls:
                    d['l' + fmt] = urls[n]
            if 'webp' not in d or 'lwebp' not in d:
                raise SystemExit(f'world_home: hero-{reg}-{shp}.webp or its -light twin is missing in static/com/hero/ — run scripts/world_hero.py')
            out[reg][shp] = d
    return out


REGIONS = json.load(open(WORLD / 'regions.json', encoding='utf-8'))
REG_OF = {cc: r for r, v in REGIONS['regions'].items() for cc in v.split()}
CARDS = {'eu': 12, 'na': 2}   # HOME3: cards of the largest countries per region (other regions: 8)
_FOLD = str.maketrans({'đ': 'dj', 'ß': 'ss', 'ł': 'l', 'ø': 'o', 'æ': 'ae', 'ı': 'i', 'ə': 'e'})


def fold(x):
    import unicodedata
    x = unicodedata.normalize('NFD', str(x).lower().translate(_FOLD))
    return ''.join(ch for ch in x if not unicodedata.combining(ch))


def counts_by_country():
    """{cc: places} — all places of the map layer per country (stats.json → by_country, written into hero.json by
    world_hero.py --stats; HOME3 12: "charging places" = manifest.counts.sites, one definition everywhere)."""
    return dict(hero_meta().get('countries') or {})


def directory(G, c, l, t):
    """HOME3 3: one country directory for the home and the hub — every country of the data in its region, the largest as
    cards, all of them A–Z with the number of charging places. A country leads to its page, a Balkan country to its
    English guide, any other country to the map opened on it."""
    W = sys.modules['world_pages']
    Lc = W.L[l]
    bc = counts_by_country()
    if not bc:
        raise SystemExit('world_home: hero.json has no "countries" — run scripts/world_hero.py with --stats stats.json')
    en_guide = {x['code']: (x['url'] if x['code'] != 'RS' else '/serbia/') for x in G.countries}
    balkan = set((c.site.idx.get('balkan') if hasattr(c.site, 'idx') else None) or ['RS', 'HR', 'BA', 'ME', 'MK', 'AL', 'XK'])
    # names a visitor may type: this language, English and the language of the country itself (market languages)
    endo = {}
    for ml, ccs in (I.config().get('market_countries') or {}).items():
        for cc in ccs:
            endo.setdefault(cc, set()).add(ml)
    regions = {r: [] for r in REGIONS['order']}
    for cc, n in bc.items():
        r = REG_OF.get(cc)
        if not r:
            print(f'world_home: WARNING {cc} is not in content/world/regions.json — shown under Asia')
            r = 'as'
        name = c.N.country(cc, l)
        keys = {fold(name), fold(c.N.country(cc, 'en'))}
        for ml in endo.get(cc, ()):
            try:
                keys.add(fold(c.N.country(cc, ml)))
            except SystemExit:
                pass
        if cc in balkan and cc in en_guide:
            url, kind = en_guide[cc], 'guide'
        elif c.site.has(cc, l) and built(G, c.site.country(cc, l)):
            url, kind = c.site.country(cc, l), 'page'
        else:
            url, kind = c.map_url(l, {'zemlja': cc}), 'map'
        regions[r].append(dict(cc=cc, name=name, n=n, n_txt=W.fmt_num(n, Lc), unit=I.pl_form(n, t['pl_places'], l),
                               url=url, kind=kind, k=' '.join(sorted(keys))))
    out = []
    for r in REGIONS['order']:
        rows = regions[r]
        if not rows:
            continue
        cards = sorted(rows, key=lambda x: -x['n'])[:CARDS.get(r, 8)]
        az = sorted(rows, key=lambda x: fold(x['name']))
        out.append(dict(id=r, name=t['tab_' + r], cards=cards, az=az, total=sum(x['n'] for x in rows),
                        total_txt=W.fmt_num(sum(x['n'] for x in rows), Lc), n_c=len(rows)))
    total = sum(bc.values())
    return dict(regions=out, total=total, n=len(bc), tz={k: v for k, v in REGIONS['tz'].items() if k != 'about'})


def market_order(l, ccs, size):
    """HOME3 4: the markets of the page's language first (config market_countries, LANG0), then by size."""
    mk = (I.config().get('market_countries') or {}).get(l) or []
    return sorted(ccs, key=lambda cc: (mk.index(cc) if cc in mk else len(mk), -size.get(cc, 0)))


def copy_dir_js(G):
    a = G.OUT / 'assets' / 'world'
    a.mkdir(parents=True, exist_ok=True)
    shutil.copy2(STATIC / 'world-dir.js', a / 'world-dir.js')
    return f"/assets/world/world-dir.js?v={hashlib.sha1((a / 'world-dir.js').read_bytes()).hexdigest()[:10]}"


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
    dir_js = copy_dir_js(G)
    pics = pictures(meta, hurls)
    mp = os.environ.get('BV_WORLD_MANIFEST')
    manifest = json.load(open(mp, encoding='utf-8')) if mp and Path(mp).exists() else {}
    counts = manifest.get('counts') or {}
    mdate = manifest.get('date') or c.date
    bc = counts_by_country()
    # HOME3 12: the number of the first screen = the sum of the directory = manifest.counts.sites
    if counts.get('sites') and sum(bc.values()) != counts['sites']:
        msg = (f"world_home: the directory adds up to {sum(bc.values())} places, the manifest says {counts['sites']} "
               f"(hero.json {meta.get('date')}, manifest {mdate}) — run scripts/world_hero.py --stats on the same build")
        if meta.get('date') == mdate:
            raise SystemExit(msg)
        print('WARNING', msg)
    hub = next((p['data'] for p in c.site.pages if p['type'] == 'hub'), {})
    cfg = world_map.load_config()
    th = cfg.get('map_theme') or {}
    a = G.OUT / 'assets' / 'world'
    idx = a / 'search-index.json'
    sver = hashlib.sha1(idx.read_bytes()).hexdigest()[:10] if idx.exists() else '0'
    P = getattr(G, 'WORLD_PRICES', None)
    R = getattr(G, 'WORLD_PAY', None)
    import world_pay
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
        D = directory(G, c, l, t)
        rows = hub.get('countries') or []
        size = dict(bc)
        # prices in Europe: the markets of the language first, then the largest (world_prices model)
        prices = None
        if P:
            M = P['model']
            cand = [cc for cc, x in M.countries.items() if x['cls']['dc']['value'] and x['home'] and x['cls']['dc']['method'] == 'w']
            items = []
            for cc in market_order(l, cand, size)[:PRICE_N]:
                x = M.countries[cc]
                dc, home = x['cls']['dc']['value'], x['home']
                url = P['country_pages'].get(cc, {}).get(l)
                items.append(dict(name=c.N.country(cc, l), dc=num(dc, 2), home=num(home, 2), dc_v=dc, home_v=home,
                                  ratio=t['p_ratio'].format(x=num(dc / home, 1)), url=url if url and built(G, url) else None))
            if items:
                ym = str(M.T['updated'])[:7]
                month = I.month_label(ym, l) if l not in I.BASE else __import__('world_prices').month_label(ym, l)
                prices = dict(items=items, maxv=max(max(i['dc_v'], i['home_v']) for i in items),
                              src=t['p_month'].format(month=month), hub=P['hub'][l])
        pay = []
        if R is not None:
            for cc in market_order(l, [cc for cc in R.countries if l in R.langs(cc)], size)[:PAY_N]:
                u = R.pay_url(cc, l)
                if built(G, u):
                    pay.append(dict(name=R.cname(cc, l), url=u))
        regional = [dict(path=WB, name=t['reg_wb'], hl='en', lang='en')] + \
                   [dict(path=h['path'], name=h['loc']['country'], hl=h['loc']['hreflang'], lang=h['loc']['html']) for h in c.local_hubs]
        routes_hub = world_pay.ROUTES[l] if built(G, world_pay.ROUTES[l]) else None
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
                        style_dark=th.get('style_dark', ''), dark_paint=th.get('dark_paint', {}), style=th.get('style', ''),
                        near_err=t['near_err'], err=t['map_err'], label=t['map_label'],
                        **({'intl': I.reg(l)['intl']} if l not in I.BASE else {}))   # LANG0: number locale of the other languages
        mapu = W.L[l]['map']
        html = W.write_page(c, l, 'world_home.html', HOME[l], HOME, dict(
            title=t['title'].replace(' | BlokVolt', ''), description=t['desc'], h1=t['h1'], T=t, crumbs=None, kick=None,
            jsonld=jsonld, stat=stat, pics=pics, hero_cfg=json.dumps(hero_cfg, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/'),
            search_url=world_shell.search_url(a, l, sver), map_url=mapu, hub_url=c.site.hub(l),
            q_dc=mapu + '?snaga=dc,hpc', q_hpc=mapu + '?snaga=hpc', q_pub=mapu + '?pristup=javni',
            D=D, DT=t, dir_js=dir_js, tz=json.dumps(D['tz'], separators=(',', ':')),
            prices=prices, pay=pay, pay_hub=world_pay.PAY[l], routes_hub=routes_hub, regional=regional,
            sources_url=world_shell.SHELL['sources'][l], method_url=world_shell.SHELL['methodology'][l],
            data_date=W.fmt_date(mdate),
            og_image=(G.SITE + hurls['og-world.jpg'].split('?')[0]) if 'og-world.jpg' in hurls else None,
            assets=assets, lcp=pics['eu']), 'home')
        out.append(HOME[l])
    js = sum((G.OUT / 'assets' / 'world' / n).stat().st_size for n in ('world-home.js', 'world-dir.js'))
    print(f"world home: {', '.join(out)} — {counts.get('sites')} places, {counts.get('countries')} countries, data {mdate}; "
          f"directory {D['n']} countries / {D['total']} places in {len(D['regions'])} regions; prices {len(prices['items']) if prices else 0}; "
          f"pay {len(pay)}; pictures {', '.join(meta.get('formats', []))} of {meta.get('date')}; home JS {js // 1024} KB")
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
            if not (HERO / f'hero-{reg}-{shp}.webp').exists() or not (HERO / f'hero-{reg}-{shp}-light.webp').exists():
                print('FAIL picture', reg, shp)
                ok = False
            for f in [HERO / f'hero-{reg}-{shp}{suf}.{fmt}' for suf in ('', '-light') for fmt in ('avif', 'webp')]:
                if f.exists() and f.stat().st_size > 150_000:
                    print('FAIL over 150 KB', f.name)
                    ok = False
            if not (1 <= v['z'] <= 6):
                ok = False
    print('world_home selftest:', 'OK' if ok else 'FAIL')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(selftest() if sys.argv[1:] == ['selftest'] else 0)
