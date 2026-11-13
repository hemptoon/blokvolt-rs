"""SEARCH (12.11.2026): one search for the whole of blokvolt.com — the field of the first screen, /map/, "Find a country"
and the 404 — over everything a driver may look for, in all 30 languages of the site and with typos.

Built at every build from the data of the bundle and of the repository, after all other world pages are written
(scripts/gen_com.py → run()), so new pages of WORLD2 and the weekly run join the index without edits:
  - countries: all countries of the layer (content/world/home/hero.json → countries, the counts of the home), names in
    every language (names/countries.csv, i18n/<code>/countries.csv) and content/world/search.json → country_alias;
  - cities: every city with charging places (places-<date>.json of the bundle, 13 000+); names of the city pages
    (names/cities.csv, i18n/<code>/cities.csv) and the GeoNames names cut by scripts/world_search_geo.py
    (content/world/search/cities15000.tsv.gz); a city without its own page leads to /map/?grad=<geonameid>;
  - regions: first-level regions (GeoNames admin1) of those cities → the map framed on their cities;
  - networks: every network of the manifest (+ search.json → network_alias); page of the network or /map/?mreza=<slug>;
    a network page of a country is found only together with the country ("ionity germany");
  - pages: the sections of the site with the synonyms of search.json (price, Preise, prix, цена…) and every page of
    prices, how to pay and routes, with the h1 of the page in its language.
Spelling (one fold shared with static/com/world-search.js — the index carries examples the test compares): lower case,
no diacritics (ü = u, and also ue as a second form; ø o/oe, å a/aa, æ ae, ß ss, ł l, ı i, đ dj), Cyrillic and Greek to
Latin, hyphens/apostrophes/dots = spaces, St/Sankt/Saint = st.
Output, one file per language: /assets/world/search-<code>.json (≤ 300 KB gzip each, the build stops above) — items,
a sorted dictionary of words with the items they belong to, full names, popular items per region, strings — and
the noindex page of all results /search/ (EN) · /<code>/search/.
    python3 scripts/world_search.py selftest
"""
import csv
import gzip
import json
import math
import os
import re
import sys
import unicodedata
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORLD = ROOT / 'content' / 'world'
sys.path.insert(0, str(ROOT / 'scripts'))
import world_i18n as I  # noqa: E402

BUDGET_GZ = 300 * 1024       # per language (SEARCH budget); above it the build stops — split the index then
MAX_TOKEN = 32

# ------------------------------------------------------------------ one spelling (mirror of world-search.js fold())
SPEC = {'ß': 'ss', 'ø': 'o', 'æ': 'ae', 'œ': 'oe', 'đ': 'dj', 'ð': 'd', 'þ': 'th', 'ł': 'l', 'ı': 'i', 'ħ': 'h',
        'ŀ': 'l', 'ŧ': 't'}
EXP = {'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'å': 'aa', 'ø': 'oe', 'æ': 'ae'}
TR = {  # Cyrillic (sr/mk/bg/uk/ru, as on blokvolt.rs: č = ч = c) and Greek → Latin, after the accents are gone
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'ґ': 'g', 'д': 'd', 'ђ': 'dj', 'е': 'e', 'є': 'je', 'ж': 'z', 'з': 'z',
    'ѕ': 'dz', 'и': 'i', 'і': 'i', 'ј': 'j', 'к': 'k', 'л': 'l', 'љ': 'lj', 'м': 'm', 'н': 'n', 'њ': 'nj', 'о': 'o',
    'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'ћ': 'c', 'у': 'u', 'ф': 'f', 'х': 'h', 'ц': 'c', 'ч': 'c', 'џ': 'dz',
    'ш': 's', 'щ': 'sc', 'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'ju', 'я': 'ja',
    'α': 'a', 'β': 'v', 'γ': 'g', 'δ': 'd', 'ε': 'e', 'ζ': 'z', 'η': 'i', 'θ': 'th', 'ι': 'i', 'κ': 'k', 'λ': 'l',
    'μ': 'm', 'ν': 'n', 'ξ': 'x', 'ο': 'o', 'π': 'p', 'ρ': 'r', 'σ': 's', 'ς': 's', 'τ': 't', 'υ': 'y', 'φ': 'f',
    'χ': 'ch', 'ψ': 'ps', 'ω': 'o'}
ABBR = {'st': 'st', 'sankt': 'st', 'saint': 'st', 'ste': 'ste', 'sainte': 'ste'}
COMB = re.compile('[̀-ͯ]')
NONW = re.compile('[^a-z0-9]+')


def shown_n(p):
    """TAILS P1.4 (13.11.2026): the number a suggestion shows is the first number of its page — every charging place on
    the map (n_all, WORLD2 P4; countries: HOME3) — not the public count of the bundle index; the pages say the public
    part separately. A bundle without n_all keeps the index number."""
    if not p:
        return None
    return (p.get('data') or {}).get('n_all') or p.get('n')


@lru_cache(maxsize=None)
def fold(s, exp=False):
    s = unicodedata.normalize('NFC', str(s or '').lower())
    if exp:
        s = ''.join(EXP.get(ch, ch) for ch in s)
    s = ''.join(SPEC.get(ch, ch) for ch in s)
    s = COMB.sub('', unicodedata.normalize('NFD', s))
    s = ''.join(TR.get(ch, ch) if 'Ͱ' <= ch <= 'ӿ' else ch for ch in s)
    return NONW.sub(' ', s).strip()


def words(s, exp=False):
    return [ABBR.get(w, w) for w in fold(s, exp).split() if len(w) <= MAX_TOKEN]


def keys(names):
    return _keys(tuple(names))


@lru_cache(maxsize=None)
def _keys(names):
    """Word tokens, the words that are a whole name by themselves (single), and full-name keys of names of two or more
    words (words joined: "newyork"), both spellings (ü = u and ue)."""
    tok, single, full = set(), set(), set()
    for n in names:
        if not n:
            continue
        for e in (False, True):
            w = words(n, e)
            if not w:
                continue
            tok.update(w)
            if len(w) == 1:
                single.add(w[0])
            elif len(w) <= 5:
                full.add(''.join(w)[:48])
    return tok, single, full


# ------------------------------------------------------------------ data
def read_csv(p):
    return list(csv.DictReader(open(p, encoding='utf-8'))) if Path(p).exists() else []


def dictionary():
    return json.load(open(WORLD / 'search.json', encoding='utf-8'))


def geo():
    rows = {}
    with gzip.open(WORLD / 'search' / 'cities15000.tsv.gz', 'rt', encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            rows[r['gid']] = r
    return rows


def places(G):
    """places-<date>.json of the bundle (cities and countries with a frame) — BV_WORLD_MANIFEST names it."""
    mp = os.environ.get('BV_WORLD_MANIFEST')
    if not mp or not Path(mp).exists():
        return {}
    m = json.load(open(mp, encoding='utf-8'))
    for p in (Path(mp).parent / str(m.get('places') or ''), Path(os.environ.get('BV_WORLD_PLACES') or '-')):
        if p.is_file():
            return json.load(open(p, encoding='utf-8'))
    return {}


def manifest():
    mp = os.environ.get('BV_WORLD_MANIFEST')
    return json.load(open(mp, encoding='utf-8')) if mp and Path(mp).exists() else {}


def h1_of(path):
    """The h1 (else the title) of a written page, plain text."""
    try:
        html = path.read_text(encoding='utf-8')
    except OSError:
        return None
    m = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.S) or re.search(r'<title>(.*?)</title>', html, re.S)
    if not m:
        return None
    t = re.sub(r'<[^>]+>', ' ', m.group(1))
    t = re.sub(r'\s+', ' ', t).replace(' | BlokVolt', '').strip()
    import html as H
    return H.unescape(t)


def alternates(path):
    """hreflang → path of a written page (its language versions)."""
    try:
        html = path.read_text(encoding='utf-8')
    except OSError:
        return {}
    out = {}
    for hl, u in re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="https://[^/"]+(/[^"]*)"', html):
        if hl != 'x-default':
            out[hl] = u
    return out


def zoom_for(b):
    """Map view (#z/lat/lon) that frames a box [w, s, e, n]."""
    w = max(b[2] - b[0], 0.01)
    h = max(b[3] - b[1], 0.01)
    z = min(math.log2(360 / w), math.log2(170 / h)) + 0.6
    return round(max(3.0, min(z, 11.0)), 1), round((b[1] + b[3]) / 2, 4), round((b[0] + b[2]) / 2, 4)


# ------------------------------------------------------------------ the index
class Item:
    __slots__ = ('kind', 'id', 'label', 'cc', 'n', 'url', 'w', 'x', 'names', 'extra', 'region', 'pop')

    def __init__(self, kind, id_, cc=None, n=None, w=0, x=0, names=(), extra=()):
        self.kind, self.id, self.cc, self.n, self.w, self.x = kind, id_, cc, n, w, x
        self.names, self.extra = list(names), list(extra)   # extra: synonyms that are not names (no full-name key)
        self.label, self.url, self.region, self.pop = {}, {}, None, 0


def lang_paths(l):
    s = I.slugs(l)
    return s


def build(G, c, langs):
    """Language-independent items with names + per-language label/url. Returns (items, stats)."""
    W = sys.modules.get('world_pages')
    D = dictionary()
    site = c.site
    N = c.N
    GEO = geo()
    P = places(G)
    M = manifest()
    hero = json.load(open(WORLD / 'home' / 'hero.json', encoding='utf-8'))
    ccount = hero.get('countries') or {}
    REG = json.load(open(WORLD / 'regions.json', encoding='utf-8'))
    reg_of = {cc: r for r, s in REG['regions'].items() for cc in s.split()}
    items = []

    # -------------------------------------------------------------- countries
    crows = {r['cc']: r for r in read_csv(WORLD / 'names' / 'countries.csv')}
    i18n_c = {l: I.countries(l) for l in langs if l not in I.BASE}
    cpages = {p['cc']: p for p in site.pages if p['type'] == 'country'}
    alias = D.get('country_alias', {})
    en_slug = {x['code']: x['url'] for x in G.countries}
    built = {x['key'] for x in G.BUILT}
    all_cc = sorted(set(ccount) | set(cpages) | ({cc for cc in (P.get('cc') or {})}))
    cname = {}
    for cc in all_cc:
        r = crows.get(cc) or {}
        names = [v for k, v in r.items() if k.startswith('name_') and v]
        for l, rows in i18n_c.items():
            x = rows.get(cc) or {}
            names += [x.get('name'), x.get('name_nom')]
        names += alias.get(cc, [])
        n = shown_n(cpages[cc]) if cc in cpages else ccount.get(cc)   # TAILS P1.4: the page's number first
        it = Item('c', cc, cc=cc, n=n, w=60 + (min(15, 4 * math.log10(n)) if n else 0) + (3 if cc in cpages else 0), names=names)
        it.region = reg_of.get(cc)
        for l in langs:
            nm = N.country(cc, l) if cc in N.c else (r.get('name_en') or cc)
            it.label[l] = nm
            cname.setdefault(l, {})[cc] = nm
            if cc in W.BALKAN:
                if cc == 'RS':
                    u = G.RS + ('/gradovi/' if l == 'sr' else '/ru/gradovi/' if l == 'ru' else '/en/gradovi/')
                else:
                    loc = f'/{W.BALKAN_LOCAL[cc]}/' if W.BALKAN_LOCAL.get(cc) in built else en_slug.get(cc)
                    u = en_slug.get(cc) if l == 'en' else loc
                it.url[l] = u
                it.kind = 'c'
            elif cc in cpages and l in site.langs(cpages[cc]):
                it.url[l] = site.url(cpages[cc], l)
            else:
                it.url[l] = None   # → the map on the country (?zemlja=)
        items.append(it)

    # -------------------------------------------------------------- cities (every city with places)
    city_csv = {r['geonameid']: r for r in read_csv(WORLD / 'names' / 'cities.csv')}
    i18n_t = {l: {str(k): r for k, r in I.cities(l).items()} for l in langs if l not in I.BASE}
    tpages = {str(p['gid']): p for p in site.pages if p['type'] == 'city'}
    pcity = P.get('city') or {}
    gids = sorted(set(pcity) | set(tpages), key=lambda g: int(g))
    region_cities = {}
    n_city = 0
    for gid in gids:
        g = GEO.get(gid) or {}
        p = tpages.get(gid)
        cc = (p or {}).get('cc') or g.get('cc')
        if not cc:
            continue
        cr = city_csv.get(gid) or {}
        # names: local, en, sr, ru, GeoNames name, the names of the 27 other languages, then the other GeoNames names
        # (Cyrillic and Greek first; all of them for a city with a page, fewer for a small one)
        names = [cr.get('name_local'), cr.get('name_en'), cr.get('name_sr'), cr.get('name_ru'), g.get('name')]
        pop0 = int(g.get('pop') or 0)
        for l, rows in i18n_t.items():
            names.append((rows.get(gid) or {}).get('name'))
        # other GeoNames names: one-word Latin names (exonyms: Monachium, Lissabon) and Cyrillic/Greek ones — the many-word
        # Latin ones are mostly old or district names ("New San Diego", "Lungsod ng …") that would answer "new"
        oth = [x for x in (g.get('other') or '').split('|') if x and (' ' not in x.strip() or re.search('[\u0370-\u04ff]', x))]
        names += oth[:40 if p else 12 if pop0 >= 200000 else 3 if pop0 >= 100000 else 1]
        it_known = bool(cr) or any(gid in rows for rows in i18n_t.values())
        info = p['data']['city'] if p else None
        pop = int(g.get('pop') or 0)
        n = p['n'] if p else None
        # size: places of its page and population together (Vienna before Vienne, Newark before New Bedford)
        size = 0.6 * min(10 * math.log10(n), 30) if n else 0
        size += 0.6 * 8 * (math.log10(pop) - 4) if pop > 10000 else 0
        it = Item('t', int(gid), cc=cc, n=shown_n(p), w=20 + min(size, 32) + (3 if p else 0), names=names)
        it.pop = pop if not it_known else max(pop, 200000)   # a city of our name lists keeps its names in the long tail
        it.region = reg_of.get(cc)
        for l in langs:
            if info is not None:
                lab = N.city_name(info, l)
            else:
                lab = None
                if l in I.BASE:
                    lab = cr.get('name_' + l)
                elif l in i18n_t:
                    lab = (i18n_t[l].get(gid) or {}).get('name')
                lab = lab or cr.get('name_en') or g.get('name') or gid
            it.label[l] = lab
            it.url[l] = site.url(p, l) if p and l in site.langs(p) else None
        bb = pcity.get(gid)
        if bb and g.get('region'):
            region_cities.setdefault((cc, g['region']), []).append((bb, pop, n or 0))
        items.append(it)
        n_city += 1

    # -------------------------------------------------------------- regions (admin1) framed on their cities
    ralias = D.get('region_alias', {})
    city_keys = {}
    for it in items:
        if it.kind in ('c', 't'):
            for f in keys(it.names)[1] | keys(it.names)[2]:
                city_keys.setdefault(f, set()).add(it.cc)
    n_reg = 0
    for (cc, rname), cs in sorted(region_cities.items()):
        if len(cs) < 2:
            continue
        names = [rname] + ralias.get(f'{cc}:{rname}', [])
        fk = keys([rname])[1] | keys([rname])[2]
        if any(cc in city_keys.get(f, ()) for f in fk) and not ralias.get(f'{cc}:{rname}'):
            continue   # Berlin, Vienna, Madrid… — the city (or the country) already answers
        b = [min(x[0][0] for x in cs), min(x[0][1] for x in cs), max(x[0][2] for x in cs), max(x[0][3] for x in cs)]
        z, la, lo = zoom_for(b)
        nn = sum(x[2] for x in cs)
        it = Item('r', f'{cc}:{rname}', cc=cc, n=None, w=18 + min(12, 3 * math.log10(len(cs))), names=names)
        it.region = reg_of.get(cc)
        for l in langs:
            al = ralias.get(f'{cc}:{rname}')
            it.label[l] = al[0] if al and cc in (I.market(l) or ()) else rname   # Bayern on the German pages, Bavaria elsewhere
            it.url[l] = f'#{z}/{la}/{lo}'
        items.append(it)
        n_reg += 1

    # -------------------------------------------------------------- networks (every network of the manifest)
    nalias = D.get('network_alias', {})
    nets = {}
    order = []
    merge = dict(D.get('network_merge', {}))
    first = {}
    for i, (disp, key, slug) in enumerate(zip(M.get('networks') or [], M.get('networks_key') or [], M.get('networks_slug') or [])):
        if not slug or not disp:
            continue
        f = fold(disp)
        if slug not in merge and f in first and first[f] != slug:
            merge[slug] = first[f]   # the same name twice in the manifest (IONITY / ionity-2): one network
        first.setdefault(f, slug)
    for i, (disp, key, slug) in enumerate(zip(M.get('networks') or [], M.get('networks_key') or [], M.get('networks_slug') or [])):
        if not slug or not disp:
            continue
        main = merge.get(slug, slug)
        if main not in nets:
            nets[main] = {'names': set(), 'rank': i, 'disp': disp, 'slugs': [main]}
            order.append(main)
        if slug != main and slug not in nets[main]['slugs']:
            nets[main]['slugs'].append(slug)
        nets[main]['names'].update(x for x in (disp, key) if x)
    for r in read_csv(WORLD / 'names' / 'networks.csv'):
        m = merge.get(r.get('slug'), r.get('slug'))
        if m in nets:
            nets[m]['names'].update(x for x in (r.get('network'), r.get('name_display')) if x)
            if r.get('name_display') and r.get('slug') == m:
                nets[m]['disp'] = r['name_display']
    gpages = {p['net']: p for p in site.pages if p['type'] == 'network_global'}
    npages = [p for p in site.pages if p['type'] == 'network']
    net_n = {}
    for p in npages:
        k = merge.get(p['slug'], p['slug'])
        net_n[k] = net_n.get(k, 0) + (p.get('n') or 0)
    for slug in order:
        x = nets[slug]
        names = sorted(x['names']) + nalias.get(slug, [])
        gp = next((p for k, p in gpages.items() if N.net_slug(k) in x['slugs']), None)
        n = shown_n(gp) if gp else None
        size = 12 - 3 * math.log10(x['rank'] + 1) + (5 * math.log10(net_n[slug]) if net_n.get(slug) else 0)
        it = Item('n', ','.join(x['slugs']), n=n, w=34 + max(0, min(size, 26)), names=names)
        it.pop = -x['rank']   # order of the manifest (most places first) for ties
        for l in langs:
            it.label[l] = x['disp']
            it.url[l] = site.url(gp, l) if gp and l in site.langs(gp) else None
        items.append(it)
    # a network page of a country — found together with the country only
    for p in npages:
        slug = merge.get(p['slug'], p['slug'])
        x = nets.get(slug) or {'names': {p['net']}, 'disp': p['net']}
        cc = p['cc']
        cnames = [v for v in (crows.get(cc) or {}).values() if v] + alias.get(cc, [])
        cnames += [(i18n_c[l].get(cc) or {}).get('name') for l in i18n_c]
        it = Item('n', f'{slug}@{cc}', cc=cc, n=shown_n(p), w=40, x=1, names=sorted(x['names']) + nalias.get(slug, []), extra=cnames)
        ok = False
        for l in langs:
            it.label[l] = f"{x['disp']} · {cname[l].get(cc, cc)}"
            it.url[l] = site.url(p, l) if l in site.langs(p) else None
            ok = ok or bool(it.url[l])
        if ok:
            items.append(it)

    # -------------------------------------------------------------- pages
    out = G.OUT
    syn = D.get('sections', {})

    def syn_words(key):
        s = syn.get(key) or {}
        return [w for l in s for w in s[l]]

    def page_item(key, en_path, w, x=0, extra=(), cc=None, need_en=True):
        f = out / en_path.strip('/') / 'index.html' if en_path.strip('/') else out / 'index.html'
        if need_en and not f.exists():
            return None
        alts = alternates(f) if f.exists() else {}
        alts.setdefault('en', en_path)
        it = Item('p', key, cc=cc, w=w, x=x, extra=list(extra))
        hl = {I.reg(l)['hreflang']: l for l in langs}
        for h, u in alts.items():
            if h in hl:
                it.url[hl[h]] = u
        titles = []
        for l in langs:
            u = it.url.get(l)
            t = h1_of(out / u.strip('/') / 'index.html') if u else None
            if t:
                titles.append(t)
            it.label[l] = t
        en_t = it.label.get('en') or key
        for l in langs:
            if not it.label[l]:
                it.label[l] = en_t
                it.url.setdefault(l, it.url.get('en'))
        it.names = titles
        return it

    S = {l: I.slugs(l) for l in langs}
    shell = __import__('world_shell')
    sec = [  # key, EN path, weight
        ('map', S['en']['map'], 14), ('hub', S['en']['hub'], 12), ('prices', S['en']['prices'], 14),
        ('pay', S['en'].get('pay'), 13), ('routes', S['en'].get('routes'), 12), ('networks', S['en'].get('gnet'), 9),
        ('download', site.download('en'), 11), ('about_data', site.about('en'), 9),
        ('widget', S['en'].get('map_conf'), 10), ('developers', S['en'].get('developers'), 10),
        ('press', S['en'].get('press'), 10), ('b2b', S['en'].get('b2b'), 9),
        ('sources', S['en'].get('sources'), 9), ('methodology', S['en'].get('methodology'), 9),
        ('terms', shell.TERMS.get('en') if hasattr(shell, 'TERMS') else '/terms/', 7),
        ('about', S['en'].get('shell_about'), 8), ('western_balkans', G.WB_PATH, 9)]
    n_pages = 0
    for key, path, w in sec:
        if not path:
            continue
        it = page_item(key, path, w, extra=syn_words(key))
        if it:
            items.append(it)
            n_pages += 1
    # every page under prices, how to pay and routes (country, network and route pages): found with their h1 words
    slug2cc = {r.get('slug_en'): cc for cc, r in crows.items() if r.get('slug_en')}
    for key, path in (('prices', S['en']['prices']), ('pay', S['en'].get('pay')), ('routes', S['en'].get('routes'))):
        if not path:
            continue
        base = out / path.strip('/')
        if not base.is_dir():
            continue
        for d in sorted(base.iterdir()):
            if not (d / 'index.html').is_file():
                continue
            cc = slug2cc.get(d.name)
            extra = syn_words(key)
            if cc:
                extra += [v for v in (crows.get(cc) or {}).values() if v] + alias.get(cc, [])
                extra += [(i18n_c[l].get(cc) or {}).get('name') for l in i18n_c]
            it = page_item(f'{key}/{d.name}', f'{path}{d.name}/', 8, x=0 if key == 'routes' else 1, extra=extra, cc=cc)
            if it:
                items.append(it)
                n_pages += 1
    return items, dict(countries=sum(1 for i in items if i.kind == 'c'), cities=n_city, regions=n_reg,
                       networks=sum(1 for i in items if i.kind == 'n' and not i.x),
                       network_country=sum(1 for i in items if i.kind == 'n' and i.x), pages=n_pages), reg_of


def is_tail(it, l, top):
    """The first file is small, so the first suggestions come at once: countries, regions, pages, the largest cities and
    networks. Everything else (other cities, small networks, network pages of countries) comes right after it, in
    columns (encode_tail), and the browser adds it when idle."""
    if it.kind == 'c' or (it.kind == 'p' and '/' not in str(it.id)):
        return False   # countries and the sections of the site
    return id(it) not in top


def first_set(items, l):
    t = sorted((it for it in items if it.kind == 't'), key=lambda it: -(it.w + (6 if it.url.get(l) else 0)))[:250]
    n = sorted((it for it in items if it.kind == 'n' and not it.x), key=lambda it: (-it.w, -it.pop))[:80]
    return {id(it) for it in t + n}


def encode(items, l, curl, offset=0):
    """Items [kind, id, label, cc, n, url, w, x, region] (url "+rest" = the url of its country page + rest), the sorted
    word dictionary with postings (item id × 2 + 1 where the word alone is a whole name of the item, delta-coded) and
    the full names of two or more words with postings."""
    rows, tok, full = [], {}, {}
    for i, it in enumerate(items):
        t, one, f = keys(it.names)
        te = keys(it.extra)[0]
        for w in t | te:
            tok.setdefault(w, set()).add(2 * (i + offset) + (1 if w in one else 0))
        for w in f:
            full.setdefault(w, set()).add(i + offset)
        u = it.url.get(l)
        cu = curl.get(it.cc) if it.kind in ('t', 'n') else None
        if u and cu and u.startswith(cu) and u != cu:
            u = '+' + u[len(cu):]
        row = [it.kind, it.id, it.label.get(l) or it.label.get('en') or str(it.id), it.cc, it.n, u, round(it.w), it.x]
        if it.region:
            row.append(it.region)
        while row and row[-1] in (None, 0) and len(row) > 3:
            row.pop()
        rows.append(row)
    tk = sorted(tok)
    fk = sorted(full)

    def delta(ids):
        out, prev = [], 0
        for x in sorted(ids):
            out.append(x - prev)
            prev = x
        return out
    return dict(items=rows, tok='\n'.join(tk), tp=[delta(tok[w]) for w in tk], nm='\n'.join(fk), np=[delta(full[w]) for w in fk])


def encode_tail(items, l, curl):
    """The long tail in columns, words not yet inverted (the browser builds the dictionary when the file arrives, after
    the first suggestions): kinds, ids, labels, countries, weights and the folded names of each item (names | , words
    space)."""
    k, ids, lb, cc, w, kw, extra = [], [], [], [], [], [], {}
    items = sorted(items, key=lambda it: (it.kind, it.id if isinstance(it.id, int) else 0, str(it.id)))
    prev = 0
    for it in items:
        k.append(it.kind)
        if isinstance(it.id, int):
            ids.append(it.id - prev)   # geonameids, delta-coded
            prev = it.id
        else:
            ids.append(it.id)
        lab = it.label.get(l) or it.label.get('en') or str(it.id)
        lb.append(lab)
        u = it.url.get(l)
        if u or it.n or it.x:   # a page here, a count, a page of a country: [n, url, x] by position
            cu = curl.get(it.cc)
            extra[str(len(k) - 1)] = [it.n, '+' + u[len(cu):] if u and cu and u.startswith(cu) and u != cu else u, it.x]
        cc.append(it.cc or '--')
        w.append(round(it.w))
        ns, xs = [], []
        cap = 9 if not (it.x or it.kind in ('p', 'r')) else 400
        src = [lab] + it.names
        if it.kind == 't' and it.url.get(l):
            cap = 60   # a city with its page here: all its names
        elif it.kind == 't':   # a city without its page here: its name here, local, English (+ ue/oe forms); a large one
            # also its names in the other languages (Warschau, Mailand, Kiev)
            cap = 16 if it.pop >= 200000 else 8 if it.pop >= 100000 else 4
            cyr = l in ('ru', 'uk', 'bg', 'mk', 'sr', 'el')
            if it.pop < 100000:
                src = [lab, it.names[0], it.names[1], it.names[4]] + ([it.names[3]] if cyr else [])
        for n in src:
            if len(ns) >= cap:
                break
            for e in (False, True):
                x = ' '.join(words(n, e))
                if x and x not in ns:
                    ns.append(x)
        # other words (synonyms of a section, the country of a page): words only, never a whole name
        xw = sorted({w for n in it.extra for e in (False, True) for w in words(n, e)} - {w for x in ns for w in x.split()})
        kw.append('|'.join(ns) + ('||' + ' '.join(xw) if xw else ''))
    return dict(k=''.join(k), id=ids, lb=lb, cc=''.join(cc), w=w, kw=kw, ex=extra)


def popular(items, reg_of):
    """Per region of the visitor: the largest countries and cities (indexes into items) for the empty field."""
    out = {}
    for r in set(reg_of.values()):
        cs = sorted((i for i, it in enumerate(items) if it.kind == 'c' and it.region == r and it.n), key=lambda i: -items[i].n)[:2]
        ts = sorted((i for i, it in enumerate(items) if it.kind == 't' and it.region == r and it.n), key=lambda i: -items[i].n)[:4]
        out[r] = cs + ts
    return out


def strings(langs):
    return I.load('search', langs)


def run(G, c):
    """Called by gen_com.main() after the world home (all world pages are written)."""
    if c is None:
        return None
    import time
    t0 = time.time()
    W = sys.modules['world_pages']
    langs = list(W.LANGS)
    items, st, reg_of = build(G, c, langs)
    # stable order: kinds, then weight — ids of the postings stay small
    order = {'c': 0, 't': 1, 'n': 2, 'r': 3, 'p': 4}
    items.sort(key=lambda it: (order[it.kind], -it.w, str(it.id)))
    T = strings(langs)
    D = dictionary()
    REG = json.load(open(WORLD / 'regions.json', encoding='utf-8'))
    tz = {k: v for k, v in REG['tz'].items() if k != 'about'}
    a = G.OUT / 'assets' / 'world'
    a.mkdir(parents=True, exist_ok=True)
    chk = sample_folds(items)
    sizes = {}
    stop = sorted({w for x in D.get('stop', {}).values() for s in x for w in words(s)})
    mods, taken = {}, set(stop) | set(D.get('mod_exclude', []))
    for k in ('ultra', 'fast', 'ac'):   # single words only; a word of two lists stays in the first
        mods[k] = sorted({words(s)[0] for x in D.get(k, {}).values() for s in x if len(words(s)) == 1} - taken)
        taken |= set(mods[k])
    for l in langs:
        S = I.slugs(l)
        top = first_set(items, l)
        core = [it for it in items if not is_tail(it, l, top)]
        tail = [it for it in items if is_tail(it, l, top)]
        curl = {it.cc: it.url.get(l) for it in items if it.kind == 'c' and it.url.get(l)}
        # the long tail in as many files as the budget needs (each ≤ 300 KB gzip; the weekly data may grow)
        parts = 1
        while True:
            size = -(-len(tail) // parts)
            chunks = [tail[i:i + size] for i in range(0, len(tail), size)] or [[]]
            raws = [json.dumps(dict(v=2, lang=l, n=len(ch), **encode_tail(ch, l, curl)), ensure_ascii=False, separators=(',', ':')).encode()
                    for ch in chunks]
            if max(len(gzip.compress(r, 6)) for r in raws) <= BUDGET_GZ - 20 * 1024 or parts >= 6:
                break
            parts += 1
        names = [f'search-{l}-{i + 2}.json' for i in range(len(raws))]
        doc = dict(v=2, date=c.date, lang=l, map=S['map'], all=search_url(l), hub=S['hub'], T=T[l], stop=stop, mod=mods,
                   pop=popular(core, reg_of), tz=tz, mk=list(I.market(l) or []), chk=chk, n=len(core),
                   tail=names, **encode(core, l, curl))
        pop0 = {r: [(doc['items'][i] + [None] * 6)[:6] + [None, 0, None] for i in ix] for r, ix in doc['pop'].items()}
        for r in pop0.values():   # absolute URLs (the first file resolves "+rest" against its countries)
            for row in r:
                if row[5] and row[5].startswith('+'):
                    row[5] = (curl.get(row[3]) or '/') + row[5][1:]
        cn = {it.cc: it.label.get(l) for it in items if it.kind == 'c'}
        small = dict(v=2, lang=l, map=S['map'], all=search_url(l), hub=S['hub'], T=T[l], tz=tz, pop=pop0,
                     cn={cc: cn[cc] for r in pop0.values() for row in r for cc in [row[3]] if cc in cn})
        files = [(f'search-{l}-0.json', json.dumps(small, ensure_ascii=False, separators=(',', ':')).encode()),
                 (f'search-{l}.json', json.dumps(doc, ensure_ascii=False, separators=(',', ':')).encode())] + list(zip(names, raws))
        tot = 0
        for name, raw in files:
            (a / name).write_bytes(raw)
            gz = len(gzip.compress(raw, 9, mtime=0))
            sizes[name] = (len(raw), gz)
            tot += gz
            if gz > BUDGET_GZ:
                raise SystemExit(f'world_search: {name} is {gz // 1024} KB in gzip > {BUDGET_GZ // 1024} KB — split the index')
        sizes[l] = (0, tot)
    js = ROOT / 'static' / 'com' / 'world-search.js'
    css = ROOT / 'static' / 'com' / 'world-search.css'
    for f in (js, css):
        (a / f.name).write_bytes(f.read_bytes())
    jgz = len(gzip.compress(js.read_bytes(), 9, mtime=0))
    write_pages(G, c, langs, T)
    stamp(G, langs, T, a)
    big = max(((k, v) for k, v in sizes.items() if k.endswith('.json')), key=lambda x: x[1][1])
    per = max(sizes[l][1] for l in langs)
    zero = max(sizes[f'search-{l}-0.json'][1] for l in langs)
    first = max(sizes[f'search-{l}.json'][1] for l in langs)
    print(f"world search: {len(items)} items ({st['countries']} countries, {st['cities']} cities, {st['regions']} regions, "
          f"{st['networks']} networks + {st['network_country']} network pages of countries, {st['pages']} pages) × {len(langs)} "
          f"languages; largest file {big[0]} {big[1][0] // 1024} KB, {big[1][1] // 1024} KB gzip (limit {BUDGET_GZ // 1024} per file); "
          f"popular {zero / 1024:.1f} KB, first file (suggestions) ≤ {first // 1024} KB gzip; largest language (all files) {per // 1024} KB gzip; "
          f"world-search.js {jgz // 1024} KB gzip; {time.time() - t0:.1f} s")
    return sizes


def stamp(G, langs, T, a):
    """The pages with a search field: placeholder and label of the language (the map and the 404 are written before
    this step) and one version for world-search.js, its CSS and the indexes (?v= — the script passes it on)."""
    import hashlib
    import html as H
    h = hashlib.sha1()
    for f in sorted(a.glob('search-*.json')) + [a / 'world-search.js', a / 'world-search.css']:
        h.update(f.read_bytes())
    v = h.hexdigest()[:10]
    n = 0
    targets = [('en', '/404.html')]
    for l in langs:
        S = I.slugs(l)
        targets += [(l, S['home']), (l, S['hub']), (l, S['map']), (l, search_url(l))]
    for l, u in targets:
        f = G.OUT / (u.strip('/') + ('' if u.endswith('.html') else '/index.html')) if u != '/' else G.OUT / 'index.html'
        if not f.is_file():
            continue
        t = f.read_text(encoding='utf-8')
        t2 = t.replace('/assets/world/world-search.js"', f'/assets/world/world-search.js?v={v}"') \
            .replace('@@BVS_PH@@', H.escape(T[l]['ph'])).replace('@@BVS_LABEL@@', H.escape(T[l]['label'])) \
            .replace('@@BVS_ALL@@', search_url(l))
        if t2 != t:
            f.write_text(t2, encoding='utf-8')
            n += 1
    left = [str(p) for p in G.OUT.rglob('*.html') if '@@BVS_' in p.read_text(encoding='utf-8', errors='ignore')][:3] if os.environ.get('BV_SEARCH_STRICT') else []
    if left:
        raise SystemExit(f'world_search: search placeholders left in {left}')
    return n


def sample_folds(items):
    """Pairs name → folded words for the test of the JS fold (static/com/world-search.js must give the same)."""
    out, seen = [], set()
    want = re.compile(r'[^\x00-\x7f]')
    for it in items:
        for n in it.names:
            if n and want.search(n) and n not in seen and len(out) < 240:
                seen.add(n)
                out.append([n, ' '.join(words(n)), ' '.join(words(n, True))])
    return out


def search_url(l):
    return '/search/' if l == 'en' else f"{I.slugs(l)['home']}search/"


def write_pages(G, c, langs, T):
    """The noindex page of all results, one per language; the results are drawn by world-search.js from ?q=."""
    W = sys.modules['world_pages']
    urls = {l: search_url(l) for l in langs}
    for l in langs:
        t = T[l]
        W.write_page(c, l, 'world_search.html', urls[l], urls, dict(
            title=t['page_title'], h1=t['page_h1'], description=t['page_desc'], T=t, TS=t, crumbs=None, kick=None, jsonld=None,
            idx=f'/assets/world/search-{l}.json', map_url=I.slugs(l)['map'], hub_url=I.slugs(l)['hub']),
            'search', robots='noindex,follow', indexable=False)


def selftest():
    ok = True
    cases = [('München', 'munchen', 'muenchen'), ('København', 'kobenhavn', 'koebenhavn'), ('Мюнхен', 'mjunhen', 'mjunhen'),
             ('Μόναχο', 'monacho', 'monacho'), ('Saint-Étienne', 'st etienne', 'st etienne'), ('St. Gallen', 'st gallen', 'st gallen'),
             ('Łódź', 'lodz', 'lodz'), ('Straße', 'strasse', 'strasse'), ('İstanbul', 'istanbul', 'istanbul'), ('Beč', 'bec', 'bec'),
             ('Беч', 'bec', 'bec'), ('Ålesund', 'alesund', 'aalesund'), ('Đakovo', 'djakovo', 'djakovo'), ('Frankfurt am Main', 'frankfurt am main', 'frankfurt am main')]
    for raw, a, b in cases:
        if ' '.join(words(raw)) != a or ' '.join(words(raw, True)) != b:
            print('FAIL fold', raw, words(raw), words(raw, True))
            ok = False
    D = dictionary()
    for k in ('sections', 'stop', 'fast', 'ultra', 'ac', 'country_alias', 'network_alias', 'region_alias'):
        if k not in D:
            print('FAIL search.json key', k)
            ok = False
    langs = I.langs() if callable(getattr(I, 'langs', None)) else list(I.BASE)
    for k in ('sections', 'stop', 'fast'):
        for sk, v in (D[k].items() if k == 'sections' else [(k, D[k])]):
            miss = [l for l in I.config()['langs_enabled_preview'] if l not in v]
            if miss:
                print('FAIL', k, sk, 'missing', miss)
                ok = False
    T = I.load('search', list(I.BASE))
    for l in I.BASE:
        if re.search(r'\d', T[l]['page_title']):
            print('FAIL digit in title', l)
            ok = False
    print('world_search selftest:', 'OK' if ok else 'FAIL')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(selftest() if sys.argv[1:] == ['selftest'] else 0)
