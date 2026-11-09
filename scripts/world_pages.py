# -*- coding: utf-8 -*-
"""World SEO pages of blokvolt.com in EN / SR / RU (task K3, pool 2; P1 §3, contract v1 of claude/evdb_tasks2).

Input: a pages bundle `pages-YYYY-MM-DD/` made by evdb `product/pages_json.py` (schema: PAGES_SCHEMA.md there),
given by the environment variable BV_WORLD_PAGES. Without it the world layer is skipped and blokvolt.com builds as
before. Names: content/world/names/ (task K4) when present, else content/world/names_fallback/countries.csv and the
GeoNames names inside the bundle ("u gradu X" / "в городе X"). Strings: content/world/strings_pages.json (the build
stops when a language is missing). Config: content/world/config.json (created by K2; created here if missing).

Pages (contract §8): hub, country, city, network in a country, global network (stage "quarter"), about the data,
download. While config.public is false every page has robots noindex,nofollow, none is in a sitemap and no existing
page links to them (links to the world layer are added at launch, by KI).

State (lastmod, pages that fell below the threshold): content/world/state/pages_state.json
  url -> {hash, first_seen, last_changed, below_threshold_since, type, key, title, country_url}
It is updated only by `python3 scripts/world_pages.py update-state <pages-dir>` (the weekly data run, which commits
it with the data); a site build only reads it, so a rebuild without new data writes byte-identical HTML.
A page below the threshold (P1 §3.3): 8 weeks noindex,follow with a link to its country, then a stub with meta
refresh + canonical to the country; the lines for a future Cloudflare _redirects go to
content/world/state/redirects_world.txt. A page comes back only at 120 % of its threshold.

Hook in gen_com.py (one line before the link check): world_pages.run(<gen_com module>, local_hubs).
CLI:
  python3 scripts/world_pages.py update-state <pages-dir>     # weekly, before the site build
  python3 scripts/world_pages.py selftest                      # unit checks of helpers and state rules
"""
import csv
import datetime as dt
import hashlib
import json
import math
import os
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parent.parent
WORLD = ROOT / 'content' / 'world'
STATE = WORLD / 'state' / 'pages_state.json'
REDIRECTS = WORLD / 'state' / 'redirects_world.txt'
sys.path.insert(0, str(Path(__file__).resolve().parent))
import world_i18n as I   # noqa: E402  K8-i18n: registry of languages (content/world/config.json "langs")
LANGS = I.langs()        # enabled languages: en, sr, ru until gate G8 (BV_WORLD_LANGS for a local test build)
GRACE_DAYS = 56          # 8 weeks noindex,follow before the stub (P1 §3.3)
RETURN_FACTOR = 1.2      # a page below the threshold comes back at +20 %
SITEMAP_MAX = 50000

L = {l: I.loc(l) for l in LANGS}   # K8: formats and section paths from the registry + slugs.json
CONN_LABEL = {'TYPE2': 'Type 2', 'TYPE1': 'Type 1', 'TYPE3': 'Type 3', 'CCS2': 'CCS2', 'CCS1': 'CCS1',
              'CHADEMO': 'CHAdeMO', 'NACS_TESLA': 'Tesla (NACS)', 'SCHUKO': 'Schuko', 'CEE_INDUSTRIAL': 'CEE',
              'GBT_DC': 'GB/T DC', 'GBT_AC': 'GB/T AC', 'BS1363': 'BS 1363', 'NEMA': 'NEMA'}
BALKAN = ('RS', 'HR', 'BA', 'ME', 'MK', 'AL', 'XK')
BALKAN_LOCAL = {'HR': 'hr', 'BA': 'ba', 'ME': 'me', 'MK': 'mk', 'AL': 'al', 'XK': 'xk'}


# ------------------------------------------------------------------ small helpers

CYR = dict(zip('абвгдеёжзийклмнопрстуфхцчшщъыьэюяђјљњћџ',
               ['a','b','v','g','d','e','e','zh','z','i','j','k','l','m','n','o','p','r','s','t','u','f','h','c','ch','sh',
                'sht','a','y','','e','yu','ya','dj','j','lj','nj','c','dz']))
CYR_SR = dict(CYR, ж='ž', ч='č', ш='š', щ='št', ю='ju', я='ja', ђ='đ', ћ='ć', џ='dž', ъ='a', ы='i')


def translit(s, table=CYR):
    out = []
    for ch in s or '':
        lo = ch.lower()
        if lo in table:
            t = table[lo]
            out.append(t.capitalize() if ch != lo else t)
        else:
            out.append(ch)
    return ''.join(out)

def slugify(s):
    s = translit(s or '').replace('ß', 'ss').replace('đ', 'dj').replace('Đ', 'Dj').replace('ø', 'o').replace('Ø', 'O') \
        .replace('æ', 'ae').replace('Æ', 'Ae').replace('ł', 'l').replace('Ł', 'L').replace('ı', 'i').replace('&', ' and ')
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s or 'x' + hashlib.sha1(str(s).encode()).hexdigest()[:6]


def fmt_num(x, loc, d=0):
    if x is None:
        return ''
    s = f'{abs(float(x)):,.{d}f}'
    s = s.replace(',', '§').replace('.', loc['dec']).replace('§', loc['thou'])
    return ('−' if float(x) < 0 else '') + s


def fmt_date(iso):
    y, m, d = iso[:10].split('-')
    return f'{d}.{m}.{y}'


def fmt_month(ym):
    if not ym:
        return '—'
    y, m = ym[:7].split('-')
    return f'{m}.{y}'


pl_form = I.pl_form   # "one|few|many" for en/sr/ru (old rule), {CLDR category: text} for other languages


def seo_title(t):
    t = t + ' | BlokVolt'
    return t[:-len(' | BlokVolt')] if len(t) > 60 else t


def load_strings():
    S = json.load(open(WORLD / 'strings_pages.json', encoding='utf-8'))
    missing = [(k, l) for k, v in S.items() for l in LANGS if l in I.BASE and not (isinstance(v, dict) and v.get(l))]
    if missing:
        raise SystemExit(f'world_pages: strings_pages.json misses {len(missing)} translations, e.g. {missing[:5]}')
    return I.load('pages', LANGS)   # other languages: content/world/i18n/<code>/strings_pages.json (stops on a missing key)


def load_config():
    p = WORLD / 'config.json'
    if not p.exists():   # K2 owns this file; same content as the contract
        p.write_text(json.dumps({'public': False, 'data_base': 'https://tiles.blokvolt.rs/world/',
                                 'reports_api': 'https://www.blokvolt.rs/api/svet/prijava'}, indent=1) + '\n', encoding='utf-8')
    return json.load(open(p, encoding='utf-8'))


def read_csv(p):
    with open(p, encoding='utf-8') as f:
        return list(csv.DictReader(f))


# ------------------------------------------------------------------ names (K4 or fallback)
class Names:
    def __init__(self, bundle):
        nd = WORLD / 'names'
        cf = nd / 'countries.csv' if (nd / 'countries.csv').exists() else WORLD / 'names_fallback' / 'countries.csv'
        self.src = {'countries': str(cf.relative_to(ROOT))}
        self.c = {r['cc']: r for r in read_csv(cf)}
        self.city = {}
        if (nd / 'cities.csv').exists():
            self.src['cities'] = 'content/world/names/cities.csv'
            for r in read_csv(nd / 'cities.csv'):
                self.city[int(r['geonameid'])] = r
        else:
            self.src['cities'] = 'fallback: GeoNames names of the bundle'
        self.net = {}
        if (nd / 'networks.csv').exists():
            self.src['networks'] = 'content/world/names/networks.csv'
            for r in read_csv(nd / 'networks.csv'):
                self.net[r['network']] = r
        else:
            self.src['networks'] = 'fallback: slug of operator_canonical'
        self.city_slugs = {}   # (cc, gid) -> slug, unique inside a country

    def country(self, cc, lang):
        r = self.c.get(cc)
        if not r:
            raise SystemExit(f'world_pages: no country name for {cc} (content/world/names*/countries.csv)')
        if lang not in I.BASE:   # K8: i18n/<code>/countries.csv, then the CLDR column of names/, then English (counted)
            x = I.countries(lang).get(cc)
            if x and x.get('name'):
                return x['name']
            if r.get(f'name_{lang}'):
                return r[f'name_{lang}']
            I.fallback(lang, 'country_name', cc)
            return r['name_en']
        return r[f'name_{lang}']

    def country_slug(self, cc, lang):
        if lang not in I.BASE:
            x = I.countries(lang).get(cc)
            if x and x.get('slug'):
                return x['slug']
            I.fallback(lang, 'country_slug', cc)
            return self.c[cc]['slug_en']
        return self.c[cc][f'slug_{lang}']

    def country_u(self, cc, lang):
        r = self.c[cc]
        if lang not in I.BASE:
            x = I.countries(lang).get(cc)
            if x and x.get('in_phrase'):
                return x['in_phrase']
            I.fallback(lang, 'country_in', cc)
            return self.country(cc, lang)
        return {'en': 'in ' + ('the ' if cc in ('US', 'GB', 'NL', 'PH', 'AE') else '') + r['name_en'],
                'sr': r['sr_u'], 'ru': r['ru_v']}[lang]

    def city_name(self, info, lang):
        r = self.city.get(info['gid'])
        if lang not in I.BASE:
            x = I.cities(lang).get(info['gid'])
            if x and x.get('name'):
                return x['name']
            if r and r.get(f'name_{lang}'):
                return r[f'name_{lang}']
            I.fallback(lang, 'city_name', info['gid'])
            return self.city_name(info, 'en')
        if r and r.get(f'name_{lang}'):
            return r[f'name_{lang}']
        nm = info['name'] or info['ascii']
        if lang != 'ru' and re.search(r'[^\u0000-\u024F\u1E00-\u1EFF]', nm):   # en/sr: Latin script only
            nm = info['ascii'] or nm
        return nm

    def city_u(self, info, lang, S):
        r = self.city.get(info['gid'])
        if lang not in I.BASE:   # K8: in_phrase of i18n/<code>/cities.csv (safe construction when decl_ok = 0)
            x = I.cities(lang).get(info['gid'])
            if x and x.get('in_phrase'):
                return x['in_phrase']
            return S[lang]['fallback_u'].format(x=self.city_name(info, lang))
        if lang == 'en':
            return 'in ' + self.city_name(info, 'en')
        ok = (r or {}).get(f'decl_ok_{lang}')
        if r and str(ok if ok not in (None, '') else r.get('decl_ok', '0')) == '1':
            return r['sr_u'] if lang == 'sr' else r['ru_v']
        return S[lang]['fallback_u'].format(x=self.city_name(info, lang))

    def assign_city_slugs(self, cities_by_cc):
        """cities_by_cc: cc -> list of info dicts. K4 slug when there is one; otherwise the ASCII name, made unique
        in the country with the admin1 code, then the geonameid (P1 §3.1: frankfurt-am-main / frankfurt-oder)."""
        for cc, infos in cities_by_cc.items():
            used = {}
            for info in sorted(infos, key=lambda i: (-i.get('pop', 0), i['gid'])):
                r = self.city.get(info['gid'])
                s = (r or {}).get('slug') or slugify(info['ascii'] or info['name']) or str(info['gid'])
                if s in used:
                    s2 = f"{s}-{slugify(info.get('admin1') or '')}".strip('-')
                    s = s2 if s2 not in used and s2 != s else f"{s}-{info['gid']}"
                used[s] = info['gid']
                self.city_slugs[(cc, info['gid'])] = s

    def net_name(self, net, lang=None):
        r = self.net.get(net)
        nm = (r or {}).get('name_display') or net
        if lang and lang != 'ru' and I.latin(lang) and re.search(r'[\u0400-\u04FF]', nm):   # Latin script on Latin pages
            nm = translit(nm, CYR_SR if lang == 'sr' else CYR)
        return nm

    def net_slug(self, net):
        r = self.net.get(net)
        return (r or {}).get('slug') or slugify(net)


# ------------------------------------------------------------------ bundle
def load_bundle(d):
    d = Path(d)
    idx = json.load(open(d / 'index.json', encoding='utf-8'))
    pages = []
    for e in idx['pages']:
        data = json.load(open(d / e['file'], encoding='utf-8'))
        pages.append(dict(e, data=data))
    return idx, pages


class Site:
    """URLs of every page in every language (contract §8)."""
    def __init__(self, names, idx, pages):
        self.N = names
        self.idx = idx
        self.pages = pages
        self.by_key = {}
        cities = {}
        for p in pages:
            p['key'] = page_key(p)
            self.by_key[p['key']] = p
            if p['type'] == 'city':
                cities.setdefault(p['cc'], []).append(p['data']['city'])
        names.assign_city_slugs(cities)
        self.country_pages = {p['cc'] for p in pages if p['type'] == 'country'}
        self.city_pages = {(p['cc'], p['gid']) for p in pages if p['type'] == 'city'}
        self.net_pages = {(p['cc'], p['net']) for p in pages if p['type'] == 'network'}
        self.gnet_pages = {p['net'] for p in pages if p['type'] == 'network_global'}
        # v2: SR pages exist only for Europe (bvcom §0); every page JSON names its languages
        self.cc_langs = {p['cc']: I.page_langs(p.get('langs')) for p in pages if p['type'] == 'country'}

    def langs(self, p):
        return I.page_langs(p.get('langs') or p['data'].get('langs'))

    def has(self, cc, l):
        return l in self.cc_langs.get(cc, LANGS)

    def hub(self, l):
        return L[l]['hub']

    def country(self, cc, l):
        return f"{L[l]['hub']}{self.N.country_slug(cc, l)}/"

    def city(self, cc, gid, l):
        return f"{self.country(cc, l)}{self.N.city_slugs[(cc, gid)]}/"

    def net(self, cc, net, l):
        return f"{self.country(cc, l)}{L[l]['net']}/{self.N.net_slug(net)}/"

    def gnet(self, net, l):
        return f"{L[l]['gnet']}{self.N.net_slug(net)}/"

    def about(self, l):
        return f"{L[l]['hub']}{L[l]['about']}/"

    def download(self, l):
        return f"{L[l]['hub']}{L[l]['download']}/"

    def url(self, p, l):
        t = p['type']
        if t == 'hub':
            return self.hub(l)
        if t == 'country':
            return self.country(p['cc'], l)
        if t == 'city':
            return self.city(p['cc'], p['gid'], l)
        if t == 'network':
            return self.net(p['cc'], p['net'], l)
        if t == 'network_global':
            return self.gnet(p['net'], l)
        raise ValueError(t)


def page_key(p):
    t = p['type']
    return {'hub': 'hub', 'country': f"c:{p.get('cc')}", 'city': f"t:{p.get('cc')}:{p.get('gid')}",
            'network': f"n:{p.get('cc')}:{p.get('net')}", 'network_global': f"g:{p.get('net')}"}[t]


def mini_name(p):
    t = p['type']
    if t == 'country':
        return f"c-{p['cc'].lower()}"
    if t == 'city':
        return f"t-{p['cc'].lower()}-{p['gid']}"
    if t == 'network':
        return f"n-{p['cc'].lower()}-{slugify(p['net'])}"
    return None


# ------------------------------------------------------------------ state (weekly, data run only)
def thresholds(idx):
    th = idx['thresholds']
    return {'country': th['country'], 'city': th['city'], 'network': th['net'], 'network_global': th['gnet'], 'hub': 0}


def update_state(bundle_dir, state_path=STATE, redirects_path=REDIRECTS):
    idx, pages = load_bundle(bundle_dir)
    names = Names(bundle_dir)
    site = Site(names, idx, pages)
    date = idx['date']
    th = thresholds(idx)
    state = json.load(open(state_path, encoding='utf-8')) if Path(state_path).exists() else {}
    seen = set()
    for p in pages:
        for l in site.langs(p):
            u = site.url(p, l)
            seen.add(u)
            s = state.get(u)
            curl = site.country(p['cc'], l) if p.get('cc') else site.hub(l)
            if s is None:
                state[u] = dict(hash=p['hash'], first_seen=date, last_changed=date, below_threshold_since=None,
                                type=p['type'], key=p['key'], country_url=curl)
                continue
            if s.get('below_threshold_since'):
                need = th[p['type']] * RETURN_FACTOR
                if (p.get('n50') or 0) < need:
                    continue          # still below: stays noindex / stub (hysteresis)
                s['below_threshold_since'] = None
                s['last_changed'] = date
            if s['hash'] != p['hash']:
                s['hash'], s['last_changed'] = p['hash'], date
            s['country_url'] = curl
    for u, s in state.items():
        if u not in seen and not s.get('below_threshold_since'):
            s['below_threshold_since'] = date
            s['last_changed'] = date
    Path(state_path).parent.mkdir(parents=True, exist_ok=True)
    Path(state_path).write_text(json.dumps(state, ensure_ascii=False, indent=0, sort_keys=True) + '\n', encoding='utf-8')
    lines = []
    for u, s in sorted(state.items()):
        b = s.get('below_threshold_since')
        if b and (dt.date.fromisoformat(date) - dt.date.fromisoformat(b)).days >= GRACE_DAYS:
            lines.append(f"{u} {s['country_url']} 301")
    Path(redirects_path).write_text(''.join(l + '\n' for l in lines), encoding='utf-8')
    return state


# ------------------------------------------------------------------ mini map (SVG file, no JS)
def mini_svg(dots):
    w, h = dots['w'], dots['h']
    ac = ''.join(f'M{x} {y}h0' for x, y, k in dots['d'] if k & 2)    # k: 1 DC only, 2 no DC, 3 both
    dc = ''.join(f'M{x} {y}h0' for x, y, k in dots['d'] if k & 1)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
            f'<rect width="{w}" height="{h}" fill="#F4F4EF"/>'
            f'<path d="{ac}" stroke="#9AA3AF" stroke-width="4" stroke-linecap="round" fill="none"/>'
            f'<path d="{dc}" stroke="#2E6BFF" stroke-width="2.5" stroke-linecap="round" fill="none"/></svg>\n')


# ------------------------------------------------------------------ rendering
class Ctx:
    def __init__(self, G, local_hubs, names, site, S, cfg, state, out):
        self.G, self.local_hubs, self.N, self.site, self.S, self.cfg, self.state, self.out = G, local_hubs, names, site, S, cfg, state, out
        self.public = bool(cfg.get('public'))
        self.date = site.idx['date']
        self.map_rel = (out / 'map' / 'index.html').exists()   # K2's map built in the same run?
        self.sources = json.load(open(WORLD / 'sources_pages.json', encoding='utf-8'))
        self.written = []       # (lang, type, url, lastmod, indexable)
        a = out / 'assets'
        self.ver = {n: G.ver(a / n) for n in ('bv.css', 'bv.js', 'map.js', 'com.css') if (a / n).exists()}
        self.places = None

    # text helpers
    def t(self, l, key, **kw):
        for a, b in (('country_u', 'country_v'), ('city_u', 'city_v')):   # sr "u …" and ru "в …" are one slot
            if a in kw and b not in kw:
                kw[b] = kw[a]
        return self.S[l][key].format(**kw)

    def n(self, l, x, d=0):
        return fmt_num(x, L[l], d)

    def pn(self, l, x, key):
        return f"{fmt_num(x, L[l])} {pl_form(x, self.S[l][key], l)}"

    def pct(self, l, x):
        return L[l]['pct'].format(x=fmt_num(x, L[l]))

    def map_url(self, l, params=None, center=None, zoom=None):
        base = L[l]['map'] if self.map_rel else self.G.SITE + L[l]['map']
        q = ('?' + urlencode(params, safe=',')) if params else ''
        h = f'#{zoom}/{center[0]}/{center[1]}' if center else ''
        return base + q + h

    def lastmod(self, url):
        s = self.state.get(url)
        return (s or {}).get('last_changed') or self.date


def nav(c, l):
    import world_shell   # G0: one menu for the world layer — Map · Charging stations · Open data
    return world_shell.nav(l)


def switch(c, urls, l):
    return [(x, urls[x], c.S[x]['lang_label'] if x in I.BASE else I.label(x), L[x]['hreflang']) for x in LANGS if x in urls]


def write_page(c, l, tpl, url, urls, ctx, ptype, robots=None, indexable=True):
    G = c.G
    S = dict(c.S[l])
    alts = [(L[x]['hreflang'], G.SITE + urls[x]) for x in LANGS if x in urls] + [('x-default', G.SITE + urls['en'])]
    if not c.public:
        robots, indexable = 'noindex,nofollow', False
    base = dict(SITE=G.SITE, RS=G.RS, EMAIL=G.EMAIL, CHECKED=fmt_date(c.date), CHECKED_ISO=c.date, canon=url, path=url,
                LOC=L[l], S=S, NAV=nav(c, l), SWITCH=switch(c, urls, l), home=c.site.hub(l), alts=alts,
                COUNTRIES=G.countries, LOCALS=c.local_hubs, C={'checked': fmt_date(c.lastmod(url))},
                robots=robots, W=c, l=l, section=ptype, PAGES={}, WORLD_FT=__import__('world_shell').footer(l))
    base.update(ctx)
    base['title'] = seo_title(base['title'])
    html = G.env.get_template(tpl).render(**base)
    for n, h in c.ver.items():
        html = html.replace(f'/assets/{n}"', f'/assets/{n}?v={h}"')
    G.write(url, html)
    c.written.append((l, ptype, url, c.lastmod(url), indexable and not robots))
    return html


def crumbs_ld(c, items):
    return {'@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': c.G.SITE + u} for i, (n, u) in enumerate(items)]}


def ld(graph):
    return json.dumps({'@context': 'https://schema.org', '@graph': graph}, ensure_ascii=False, indent=1).replace('</', '<\\/')


def common_blocks(c, l, d):
    """Paragraphs, tables and tiles shared by country / city / network pages."""
    st = d['stats']
    S = c.S[l]
    paras = [c.t(l, 'p_shown', n=c.pn(l, st['n'], 'pl_publoc')),
             c.t(l, 'p_dc', dc=c.pn(l, st['dc50'], 'pl_place'), pct_dc=c.pct(l, st['pct_dc50']), hpc=c.pn(l, st['hpc'], 'pl_place')),
             c.t(l, 'p_multi', pct_multi=c.pct(l, st['pct_multi']), pct_recent=c.pct(l, st['pct_recent']))]
    if st['nonet']:
        paras.append(c.t(l, 'p_nonet', nonet=c.pn(l, st['nonet'], 'pl_place')))
    tiles = [(c.n(l, st['n']), S['st_n']), (c.n(l, st['dc50']), S['st_dc50']), (c.n(l, st['hpc']), S['st_hpc']),
             (c.n(l, st['n_nets']), S['st_nets'])]
    power = [(S[f'p{k}'], c.n(l, st['power'][str(k)]), c.pct(l, round(100 * st['power'][str(k)] / st['n']) if st['n'] else 0))
             for k in (1, 2, 3, 4, 5, 6, 7, 0) if st['power'][str(k)]]
    conn = [(CONN_LABEL.get(t, t.title()), c.n(l, k)) for t, k in st['conn']]
    srcs = []
    for k, n in st['sources']:
        s = c.sources.get(k, {})
        srcs.append(dict(name=s.get('name', k), url=s.get('url'), licence=s.get('licence', '—'),
                         licence_url=s.get('licence_url'), n=c.n(l, n)))
    return dict(paras=paras, tiles=tiles, power=power, conn=conn, srcs=srcs)


def mini(c, p):
    name = mini_name(p)
    if not name or not p['data'].get('dots', {}).get('d'):
        return None
    svg = mini_svg(p['data']['dots'])
    dst = c.out / 'assets' / 'world' / 'mini' / f'{name}.svg'
    if not dst.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(svg, encoding='utf-8')
    v = hashlib.sha1(svg.encode()).hexdigest()[:10]
    return dict(src=f'/assets/world/mini/{name}.svg?v={v}', w=p['data']['dots']['w'], h=p['data']['dots']['h'])


def render_country(c, p, urls, l):
    d, cc, S, site, N = p['data'], p['cc'], c.S[l], c.site, c.N
    cname = N.country(cc, l)
    kw = dict(country=cname, country_u=N.country_u(cc, l), country_v=N.country_u(cc, l))
    title = c.t(l, 't_country', **kw)
    b = common_blocks(c, l, d)
    cities = [dict(name=N.city_name(d['city_info'][str(g)], l), url=site.city(cc, g, l), n=c.n(l, n)) for g, n in d['city_pages']]
    others = [dict(name=N.city_name(d['city_info'][str(g)], l), url=c.map_url(l, {'zemlja': cc, 'grad': g}), n=c.n(l, n)) for g, n in d['cities_other']]
    nets = [dict(name=N.net_name(net, l), url=site.net(cc, net, l) if (cc, net) in site.net_pages else c.map_url(l, {'zemlja': cc, 'mreza': N.net_slug(net)}),
                 page=(cc, net) in site.net_pages, n=c.n(l, n)) for net, n in d['stats']['nets']]
    for net, n in d['net_pages']:   # network pages outside the top list are still linked
        if net not in {x for x, _ in d['stats']['nets']}:
            nets.append(dict(name=N.net_name(net, l), url=site.net(cc, net, l), page=True, n=c.n(l, n)))
    regional = next((x for x in c.G.countries if x['code'] == cc), None)
    dl = c.G.SITE + site.download(l)
    graph = [{'@type': 'CollectionPage', 'name': title, 'url': c.G.SITE + urls[l], 'inLanguage': L[l]['html'],
              'dateModified': c.lastmod(urls[l]), 'isPartOf': {'@type': 'WebSite', 'name': 'BlokVolt', 'url': c.G.SITE + '/'}},
             crumbs_ld(c, [('BlokVolt', site.hub(l)), (cname, urls[l])]),
             {'@type': 'Dataset', 'name': c.t(l, 'dataset_name', **kw), 'description': c.t(l, 'dataset_desc', **kw),
              'url': c.G.SITE + urls[l], 'inLanguage': L[l]['html'], 'isAccessibleForFree': True,
              'license': 'https://opendatacommons.org/licenses/odbl/1-0/', 'dateModified': c.lastmod(urls[l]),
              'creator': {'@type': 'Organization', 'name': 'BlokVolt', 'url': c.G.SITE + '/'},
              'spatialCoverage': {'@type': 'Place', 'name': N.country(cc, 'en')},
              'distribution': [{'@type': 'DataDownload', 'encodingFormat': 'text/csv', 'contentUrl': dl}]}]
    return write_page(c, l, 'world_country.html', urls[l], urls, dict(
        title=title, h1=title, description=c.t(l, 'd_country', **kw), kick=S['k_country'], cname=cname,
        crumbs=[(S['nav_hub'], site.hub(l))], jsonld=ld(graph), b=b, cities=cities, others=others, nets=nets,
        map_link=c.map_url(l, {'zemlja': cc}, *view_of(c.places, 'cc', cc, d['center'], d['zoom'])), mini=mini(c, p), d=d,
        regional=regional, data_date=fmt_date(c.lastmod(urls[l]))), 'country')


def render_city(c, p, urls, l, dup_titles):
    d, cc, S, site, N = p['data'], p['cc'], c.S[l], c.site, c.N
    info = d['city']
    cname, city = N.country(cc, l), N.city_name(info, l)
    kw = dict(country=cname, country_u=N.country_u(cc, l), country_v=N.country_u(cc, l), city=city,
              city_u=N.city_u(info, l, c.S), city_v=N.city_u(info, l, c.S))
    key = 't_city_cc' if (l, p['key']) in dup_titles else 't_city'
    title = c.t(l, key, **kw)
    near_other = [g for g, _ in d['near'] if N.city_name(d['near_info'][str(g)], l) != city]
    if (l, p['key']) in dup_titles and near_other and kw['city_u'] != kw['country_u']:   # same name twice in one country (Senden, Senden): "(near Ulm)"
        title += c.t(l, 't_near', x=N.city_name(d['near_info'][str(near_other[0])], l))
    b = common_blocks(c, l, d)
    st = d['stats']
    b['paras'].append(c.t(l, 'p_city_cmp', city=c.n(l, st['dc50_per10'], 1), country=c.n(l, d['country_dc50_per10'], 1), country_name=cname))
    fast = []
    for pid, name, net, kwv, conn, lc, lat, lon in d['fast']:
        conn = ', '.join(CONN_LABEL.get(x.split('×')[0], x.split('×')[0]) + ('×' + x.split('×')[1] if '×' in x else '')
                         for x in (conn or '').split(', ') if x)   # NACS_TESLA×16 -> Tesla (NACS)×16
        fast.append(dict(name=name, net=N.net_name(net, l) if net else None, kw=c.n(l, kwv) if kwv else '—', conn=conn or '—',
                         lc=fmt_month(lc), url=c.map_url(l, {'id': pid})))
    near = [dict(name=N.city_name(d['near_info'][str(g)], l), url=site.city(cc, g, l), km=c.t(l, 'km_away', km=c.n(l, km, 1 if km < 10 else 0))) for g, km in d['near']]
    nets = [dict(name=N.net_name(net, l), url=site.net(cc, net, l) if (cc, net) in site.net_pages else c.map_url(l, {'grad': info['gid'], 'mreza': N.net_slug(net)}),
                 page=(cc, net) in site.net_pages, n=c.n(l, n)) for net, n in st['nets']]
    graph = [{'@type': 'CollectionPage', 'name': title, 'url': c.G.SITE + urls[l], 'inLanguage': L[l]['html'],
              'dateModified': c.lastmod(urls[l]), 'about': {'@type': 'City', 'name': N.city_name(info, 'en'),
                                                           'containedInPlace': {'@type': 'Country', 'name': N.country(cc, 'en')}},
              'isPartOf': {'@type': 'WebSite', 'name': 'BlokVolt', 'url': c.G.SITE + '/'}},
             crumbs_ld(c, [('BlokVolt', site.hub(l)), (cname, site.country(cc, l)), (city, urls[l])])]
    return write_page(c, l, 'world_city.html', urls[l], urls, dict(
        title=title, h1=title, description=c.t(l, 'd_city', **kw), kick=S['k_city'], cname=cname, city=city,
        crumbs=[(S['nav_hub'], site.hub(l)), (cname, site.country(cc, l))], jsonld=ld(graph), b=b, fast=fast,
        fast_more=c.t(l, 'fast_more', shown=c.n(l, len(fast)), total=c.n(l, d['fast_total'])) if d['fast_total'] > len(fast) else None,
        ac=c.t(l, 'p_ac', ac=c.n(l, st['ac'])), ac_link=c.map_url(l, {'grad': info['gid'], 'snaga': 'ac'}, d['center'], d['zoom']),
        dc_link=c.map_url(l, {'grad': info['gid'], 'snaga': 'dc,hpc'}, d['center'], d['zoom']),
        near=near, nets=nets, map_link=c.map_url(l, {'zemlja': cc, 'grad': info['gid']}, *view_of(c.places, 'city', info['gid'], d['center'], d['zoom'])),
        mini=mini(c, p), d=d, data_date=fmt_date(c.lastmod(urls[l]))), 'city')


def render_network(c, p, urls, l):
    d, cc, S, site, N = p['data'], p['cc'], c.S[l], c.site, c.N
    cname, net = N.country(cc, l), N.net_name(p['net'], l)
    kw = dict(country=cname, country_u=N.country_u(cc, l), country_v=N.country_u(cc, l), net=net)
    title = c.t(l, 't_network', **kw)
    b = common_blocks(c, l, d)
    b['paras'].insert(1, c.t(l, 'p_net_share', n_cities=c.pn(l, d['n_cities'], 'pl_city_in'), share=c.pct(l, d['share_of_country']),
                             country_u=kw['country_u']))
    cities = [dict(name=N.city_name(d['city_info'][str(g)], l),
                   url=site.city(cc, g, l) if (cc, g) in site.city_pages else c.map_url(l, {'grad': g, 'mreza': N.net_slug(p['net'])}),
                   page=(cc, g) in site.city_pages, n=c.n(l, n)) for g, n in d['cities']]
    graph = [{'@type': 'CollectionPage', 'name': title, 'url': c.G.SITE + urls[l], 'inLanguage': L[l]['html'],
              'dateModified': c.lastmod(urls[l]), 'isPartOf': {'@type': 'WebSite', 'name': 'BlokVolt', 'url': c.G.SITE + '/'}},
             crumbs_ld(c, [('BlokVolt', site.hub(l)), (cname, site.country(cc, l)), (net, urls[l])])]
    gl = site.gnet(p['net'], l) if p['net'] in site.gnet_pages else None
    return write_page(c, l, 'world_network.html', urls[l], urls, dict(
        title=title, h1=title, description=c.t(l, 'd_network', **kw), kick=S['k_network'], cname=cname, net=net,
        crumbs=[(S['nav_hub'], site.hub(l)), (cname, site.country(cc, l))], jsonld=ld(graph), b=b, cities=cities,
        map_link=c.map_url(l, {'zemlja': cc, 'mreza': N.net_slug(p['net'])}, d['center'], d['zoom']), gnet_link=gl,
        mini=mini(c, p), d=d, data_date=fmt_date(c.lastmod(urls[l]))), 'network')


def render_gnet(c, p, urls, l):
    d, S, site, N = p['data'], c.S[l], c.site, c.N
    net = N.net_name(p['net'], l)
    title = c.t(l, 't_gnet', net=net)
    b = common_blocks(c, l, d)
    b['paras'].insert(0, c.t(l, 'p_gnet', net=net, n_countries=c.pn(l, len(d['countries']), 'pl_country_in')))
    rows = [dict(name=N.country(cc, l) if cc in N.c else cc,
                 url=site.net(cc, p['net'], l) if (cc, p['net']) in site.net_pages and site.has(cc, l) else c.map_url(l, {'zemlja': cc, 'mreza': N.net_slug(p['net'])}),
                 n=c.n(l, n)) for cc, n in d['countries']]
    graph = [{'@type': 'CollectionPage', 'name': title, 'url': c.G.SITE + urls[l], 'inLanguage': L[l]['html'], 'dateModified': c.lastmod(urls[l])},
             crumbs_ld(c, [('BlokVolt', site.hub(l)), (net, urls[l])])]
    return write_page(c, l, 'world_network_global.html', urls[l], urls, dict(
        title=title, h1=title, description=c.t(l, 'd_gnet', net=net), kick=S['k_network'], net=net,
        crumbs=[(S['nav_hub'], site.hub(l))], jsonld=ld(graph), b=b, rows=rows,
        map_link=c.map_url(l, {'mreza': N.net_slug(p['net'])}), data_date=fmt_date(c.lastmod(urls[l]))), 'network_global')


def render_hub(c, p, urls, l):
    d, S, site, N, G = p['data'], c.S[l], c.site, c.N, c.G
    stage = c.site.idx['stage']
    title = S['t_hub_' + ('month' if stage.startswith('month') else stage)]
    eu_only = l == 'sr' or (l not in I.BASE and I.scope(l) == 'europe')   # K8: extra languages follow Serbian by default
    if eu_only and 'stats_eu' in d:   # the Serbian layer covers Europe only (bvcom §0)
        d = dict(d, stats=d['stats_eu'], countries=[r for r in d['countries'] if site.has(r[0], l)],
                 countries_below=[r for r in d['countries_below'] if len(r) < 3 or r[2] == 'EU'])
    elif stage == 'month' and d.get('countries') and any(not site.has(r[0], 'sr') for r in d['countries']):
        title = S['t_hub_month_na']
    b = common_blocks(c, l, d)
    b['tiles'][3] = (c.n(l, len(d['countries'])), S['st_countries'])
    rows = [dict(name=N.country(cc, l), url=site.country(cc, l), n=c.n(l, n), dc50=c.n(l, dc)) for cc, n, dc, *_ in d['countries']]
    rows.sort(key=lambda r: r['name'])
    balkan = []
    en_slug = {x['code']: x['url'] for x in G.countries}
    built = {x['key'] for x in G.BUILT}
    for cc in d['balkan']:
        if cc == 'RS':
            u = G.RS + {'en': '/en/gradovi/', 'sr': '/gradovi/', 'ru': '/ru/gradovi/'}.get(l, '/en/gradovi/')   # K8: extra languages → EN
        elif l != 'en' and BALKAN_LOCAL.get(cc) in built:
            u = f'/{BALKAN_LOCAL[cc]}/'
        else:
            u = en_slug.get(cc, '/')
        balkan.append(dict(name=N.country(cc, l), url=u))
    balkan.sort(key=lambda r: r['name'])
    below = [dict(name=N.country(cc, l) if cc in N.c else cc, url=c.map_url(l, {'zemlja': cc}), n=c.n(l, n))
             for cc, n, *_ in d['countries_below'] if n >= 1]
    below.sort(key=lambda r: r['name'])
    graph = [{'@type': 'CollectionPage', 'name': title, 'url': G.SITE + urls[l], 'inLanguage': L[l]['html'], 'dateModified': c.lastmod(urls[l])},
             crumbs_ld(c, [('BlokVolt', urls[l])])]
    return write_page(c, l, 'world_hub.html', urls[l], urls, dict(
        title=title, h1=title, description=S['d_hub'], kick=S['k_hub'], crumbs=[], jsonld=ld(graph), b=b, rows=rows,
        balkan=balkan, below=below, hub_p=S['p_hub'] + ((' ' + S['p_hub_na']) if not eu_only and any(not site.has(r[0], 'sr') for r in d['countries']) else ''),
        map_link=c.map_url(l), data_date=fmt_date(c.lastmod(urls[l]))), 'hub')


def render_about(c, l, sources_used):
    S, site = c.S[l], c.site
    A = I.texts(l, 'about_data')
    urls = {x: site.about(x) for x in LANGS}
    rows = []
    for k in sources_used:
        s = c.sources.get(k)
        if s:
            rows.append(dict(name=s['name'], url=s.get('url'), licence=s.get('licence'), licence_url=s.get('licence_url'),
                             attribution=s.get('attribution', '').replace('{date}', fmt_date(c.date))))
    rows.sort(key=lambda r: r['name'].lower())
    fill = lambda t: t.replace('{download_url}', c.G.SITE + site.download(l)).replace('{email}', c.G.EMAIL).replace('{build_date}', fmt_date(c.date))
    A = {k: (fill(v) if isinstance(v, str) else [[fill(x) for x in r] if isinstance(r, list) else fill(r) for r in v]) for k, v in A.items()}
    graph = [{'@type': 'WebPage', 'name': A['title'], 'url': c.G.SITE + urls[l], 'inLanguage': L[l]['html']},
             crumbs_ld(c, [('BlokVolt', site.hub(l)), (A['h1'], urls[l])])]
    return write_page(c, l, 'world_about.html', urls[l], urls, dict(
        title=A['title'].replace(' | BlokVolt', ''), h1=A['h1'], description=A['description'], A=A, rows=rows,
        crumbs=[(S['nav_hub'], site.hub(l))], kick=S['nav_about'], jsonld=ld(graph), dl_url=site.download(l),
        data_date=fmt_date(c.date)), 'about')


def render_download(c, l, manifest):
    S, site = c.S[l], c.site
    D = I.texts(l, 'download')
    urls = {x: site.download(x) for x in LANGS}
    f = None
    if manifest and manifest.get('odbl_dump'):
        f = manifest['odbl_dump'] if str(manifest['odbl_dump']).startswith('http') else c.cfg['data_base'] + str(manifest['odbl_dump'])
    graph = [{'@type': 'WebPage', 'name': D['title'], 'url': c.G.SITE + urls[l], 'inLanguage': L[l]['html']},
             crumbs_ld(c, [('BlokVolt', site.hub(l)), (D['h1'], urls[l])])]
    return write_page(c, l, 'world_download.html', urls[l], urls, dict(
        title=D['title'].replace(' | BlokVolt', ''), h1=D['h1'], description=D['description'], D=D, file=f,
        crumbs=[(S['nav_hub'], site.hub(l))], kick=S['nav_download'], jsonld=ld(graph), about_url=site.about(l),
        data_date=fmt_date(c.date)), 'download')


def render_below(c, url, s, l):
    """A page under the threshold: 8 weeks noindex,follow with a link to the country, then a refresh stub."""
    since = s['below_threshold_since']
    days = (dt.date.fromisoformat(c.date) - dt.date.fromisoformat(since)).days
    urls = {x: url for x in LANGS}   # the language versions are separate entries of the state
    stub = days >= GRACE_DAYS
    ctx = dict(title=c.S[l]['below_title'], h1=c.S[l]['below_title'], description=c.S[l]['below_p'], kick='',
               canon=s['country_url'] if stub else url,
               crumbs=[(c.S[l]['nav_hub'], c.site.hub(l))], country_url=s['country_url'], stub=stub, jsonld=None,
               data_date=fmt_date(since))
    html = write_page(c, l, 'world_gone.html', url, urls, dict(ctx, alts=[]), s.get('type', 'gone'),
                      robots='noindex' if stub else 'noindex,follow', indexable=False)
    return html


def load_places():
    """K1 v2 places-<date>.json: {"cc": {CC: [w,s,e,n]}, "city": {gid: [w,s,e,n,lat,lon]}} — from BV_WORLD_PLACES, or the
    file the manifest names (`places`) next to BV_WORLD_MANIFEST. Missing → None (the bundle's own centre and zoom)."""
    p = os.environ.get('BV_WORLD_PLACES')
    mp = os.environ.get('BV_WORLD_MANIFEST')
    if not p and mp and Path(mp).exists():
        name = (json.load(open(mp, encoding='utf-8')) or {}).get('places')
        if name and not str(name).startswith('http'):
            p = str(Path(mp).parent / Path(str(name)).name)
    if p and Path(p).exists():
        return json.load(open(p, encoding='utf-8'))
    return None


def view_of(places, kind, key, center, zoom):
    """Centre and zoom for an «Otvori na mapi» link: the K1 frame when there is one (the same frame the map fits to for
    zemlja / grad), otherwise the bundle's own."""
    try:
        b = places[kind][str(key)]
    except (TypeError, KeyError):
        return center, zoom
    w, s, e, n = b[:4]
    span = max(e - w, (n - s) * 1.6, 0.01)
    z = max(3, min(14, int(math.log2(360 / span))))
    if kind == 'city':
        z = max(z, 10)
    return [round((s + n) / 2, 4), round((w + e) / 2, 4)], z


def lang_of(url):
    for l in LANGS[1:]:   # K8: the language whose home prefix (/sr/, /ru/, /de/ …) starts the URL
        if url.startswith(I.slugs(l)['home']):
            return l
    return 'en'


def run(G, local_hubs):
    """Called by gen_com.main() with its own module (helpers, env, OUT, SITE …) after the regional site is built."""
    bdir = os.environ.get('BV_WORLD_PAGES')
    if not bdir:
        print('world pages: skipped (BV_WORLD_PAGES not set)')
        return None
    import time
    t0 = time.time()
    S = load_strings()
    cfg = load_config()
    I.check_collisions(G.OUT)   # K8: an extra language must not take a path of the regional sections (/hr/, /mk/ …)
    idx, pages = load_bundle(bdir)
    names = Names(bdir)
    site = Site(names, idx, pages)
    state = json.load(open(STATE, encoding='utf-8')) if STATE.exists() else {}
    c = Ctx(G, local_hubs, names, site, S, cfg, state, G.OUT)
    G.env.globals['fmt_num'] = fmt_num
    # titles that repeat (same city name twice in a language) get the country (t_city_cc)
    dup = set()
    for l in LANGS:
        seen = {}
        for p in pages:
            if p['type'] == 'city':
                nm = (names.city_u(p['data']['city'], l, S) if l != 'en' else names.city_name(p['data']['city'], l) + p['cc'])
                seen.setdefault(nm, []).append(p['key'])
        for v in seen.values():
            if len(v) > 1:
                dup.update((l, k) for k in v)
        for p in pages:   # a city named like its country (Luxembourg, Monaco): "u Luksemburgu, Luksemburg"
            if p['type'] == 'city' and l != 'en' and names.city_u(p['data']['city'], l, S) == names.country_u(p['cc'], l):
                dup.add((l, p['key']))
    c.places = load_places()
    below_urls = {u for u, s in state.items() if s.get('below_threshold_since')}
    sources_used = sorted({k for p in pages if p['type'] == 'hub' for k, _ in p['data']['stats']['sources']})
    manifest = None
    mp = os.environ.get('BV_WORLD_MANIFEST')
    if mp and Path(mp).exists():
        manifest = json.load(open(mp, encoding='utf-8'))
    n = 0
    for p in pages:
        urls = {l: site.url(p, l) for l in site.langs(p)}
        if any(u in below_urls for u in urls.values()):
            continue
        for l in urls:
            if p['type'] == 'country':
                render_country(c, p, urls, l)
            elif p['type'] == 'city':
                render_city(c, p, urls, l, dup)
            elif p['type'] == 'network':
                render_network(c, p, urls, l)
            elif p['type'] == 'network_global':
                render_gnet(c, p, urls, l)
            elif p['type'] == 'hub':
                render_hub(c, p, urls, l)
            n += 1
    for l in LANGS:
        render_about(c, l, sources_used)
        render_download(c, l, manifest)
        n += 2
    for u in sorted(below_urls):
        render_below(c, u, state[u], lang_of(u))
        n += 1
    og = G.OUT / 'assets' / 'og'
    for l in LANGS[1:]:     # share image of the world pages: the English card until KI draws its own
        if (og / 'og-en.png').exists() and not (og / f'og-{l}.png').exists():
            (og / f'og-{l}.png').write_bytes((og / 'og-en.png').read_bytes())
    if c.public:
        write_sitemaps(c)
    si = search_index(c)
    ll = write_llms(c)
    print(f"world pages: {n} HTML ({len(site.country_pages)} countries, {len(site.city_pages)} cities, {len(site.net_pages)} networks, "
          f"{len(site.gnet_pages)} global networks; SR only for Europe; below threshold {len(below_urls)}); "
          f"search index {si[0]} entries, {si[2] // 1024} KB gzip; llms.txt {'written' if ll else 'not written (not public)'}; public={c.public}; "
          f"names: {names.src}; {time.time() - t0:.1f} s")
    if len(LANGS) > 3 or tuple(LANGS) != I.BASE:   # K8: English fallbacks of country/city names per extra language
        print(f"world pages: languages {', '.join(LANGS)}")
        for line in I.fallback_report():
            print(line)
    return c


def search_index(c):
    """Static search index for the home page of blokvolt.com (bvcom G0/G2): every country and city page and the Balkan
    countries (their own BlokVolt pages), with names in EN/SR/RU, other spellings and the page URL per language (null
    where the language has no page). /assets/world/search-index.json, ≤ 300 KB in gzip (checked in the build)."""
    import gzip
    site, N, G = c.site, c.N, c.G
    items = []
    for p in sorted(site.pages, key=lambda p: p['key']):
        if p['type'] not in ('country', 'city'):
            continue
        langs = site.langs(p)
        if p['type'] == 'country':
            cc = p['cc']
            alt = sorted({v for k, v in N.c[cc].items() if k.startswith('name_') and v and v not in
                          (N.country(cc, 'en'), N.country(cc, 'sr'), N.country(cc, 'ru'))})[:12]
            if len(LANGS) > 3:   # K8: names of the extra languages join the other names (base layout of the index unchanged)
                alt = sorted(set(alt) | {N.country(cc, l) for l in LANGS if l not in I.BASE} - {N.country(cc, x) for x in I.BASE})
            items.append(['c', cc, N.country(cc, 'en'), N.country(cc, 'sr'), N.country(cc, 'ru'), alt,
                          [site.url(p, l) if l in langs else None for l in LANGS], p['n']])
        else:
            info = p['data']['city']
            r = N.city.get(info['gid']) or {}
            names3 = [N.city_name(info, l) for l in I.BASE]   # columns name_en/sr/ru stay fixed; extra languages → other names
            alt = sorted({x for x in (r.get('name_local'), info.get('name'), info.get('ascii'),
                                      *[N.city_name(info, l) for l in LANGS if l not in I.BASE]) if x and x not in names3})
            items.append(['t', p['cc'], *names3, alt, [site.url(p, l) if l in langs else None for l in LANGS], p['n']])
    en_slug = {x['code']: x['url'] for x in G.countries}
    built = {x['key'] for x in G.BUILT}
    for cc in BALKAN:
        if cc not in N.c:
            continue
        if cc == 'RS':
            urls = [G.RS + '/en/gradovi/', G.RS + '/gradovi/', G.RS + '/ru/gradovi/']
        else:
            loc = f'/{BALKAN_LOCAL[cc]}/' if BALKAN_LOCAL.get(cc) in built else en_slug.get(cc, '/')
            urls = [en_slug.get(cc, '/'), loc, loc]
        urls += [loc if cc != 'RS' else G.RS + '/en/gradovi/' for _ in LANGS[3:]]   # K8: extra languages → the local section
        items.append(['b', cc, N.country(cc, 'en'), N.country(cc, 'sr'), N.country(cc, 'ru'), [], urls, None])
    doc = {'v': 1, 'date': c.date, 'langs': list(LANGS),
           'fields': ['kind (c country, t city, b Balkan country on its own BlokVolt pages)', 'cc', 'name_en', 'name_sr',
                      'name_ru', 'other names', 'url per language (en, sr, ru; null = no page)', 'public places'],
           'items': items}
    raw = json.dumps(doc, ensure_ascii=False, separators=(',', ':')).encode()
    dst = G.OUT / 'assets' / 'world' / 'search-index.json'
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(raw)
    gz = len(gzip.compress(raw, 9, mtime=0))
    if gz > 300 * 1024:
        raise SystemExit(f'world_pages: search index {gz} bytes in gzip > 300 KB')
    return len(items), len(raw), gz


def llms_text(c):
    """The world section of /llms.txt (llmstxt.org): what exists, the hubs, the licence, the date. Written only when the
    world layer is public, or with BV_WORLD_PREVIEW=1 (dev) — the production llms.txt must not point to noindex pages."""
    G, site = c.G, c.site
    hub = next(p for p in site.pages if p['type'] == 'hub')
    st = hub['data']['stats']
    n_c, n_t, n_n = len(site.country_pages), len(site.city_pages), len(site.net_pages)
    na = any(not site.has(cc, 'sr') for cc in site.country_pages)
    scope = 'Europe, the United States and Canada' if na else 'Europe'
    lines = [
        '## World EV charging data (blokvolt.com)', '',
        f'Public EV charging locations in {scope}, merged from open data (OpenStreetMap, Open Charge Map, national '
        'registries and others), with power, connectors, network, sources and a reliability score. '
        'No ratings of networks, no paid placements.', '',
        f'- Data as of: {c.date}',
        f'- Public locations shown: {st["n"]:,} · countries with a page: {n_c} · city pages: {n_t} · network pages: {n_n}',
        '- Languages: English and Russian for every page; Serbian for Europe',
        '- Licence of the merged data: Open Database License (ODbL) 1.0 (contains © OpenStreetMap contributors); city names © GeoNames (CC BY 4.0)', '',
        f'- [EV charging stations by country (English)]({G.SITE}{site.hub("en")})',
        f'- [Зарядки для электромобилей по странам (Russian)]({G.SITE}{site.hub("ru")})',
        f'- [Punjači za električne automobile (Serbian, Europe)]({G.SITE}{site.hub("sr")})',
        f'- [Map]({c.map_url("en") if c.map_url("en").startswith("http") else G.SITE + c.map_url("en")})',
        f'- [About the data: sources, licences, reliability]({G.SITE}{site.about("en")})',
        f'- [Download the open data (ODbL)]({G.SITE}{site.download("en")})',
        f'- [Serbia: chargers by town (blokvolt.rs)]({G.RS}/en/gradovi/)', '',
    ]
    return '\n'.join(lines)


def write_llms(c):
    if not (c.public or os.environ.get('BV_WORLD_PREVIEW') == '1'):
        return None
    p = c.G.OUT / 'llms.txt'
    sec = llms_text(c)
    if p.exists():
        t = p.read_text(encoding='utf-8')
        if '## World EV charging data' not in t:
            p.write_text(t.rstrip('\n') + '\n\n' + sec, encoding='utf-8')
    else:
        p.write_text('# BlokVolt\n\n> Where to charge an electric car, what it costs and what the rules are: Serbia and the '
                     'Western Balkans (regional guide) and the world charging data.\n\n' + sec, encoding='utf-8')
    return p


def write_sitemaps(c):
    G = c.G
    groups = {}
    for l, t, url, lm, ok in c.written:
        if ok:
            groups.setdefault((l, t), []).append((url, lm))
    files = []
    for (l, t), rows in sorted(groups.items()):
        rows.sort()
        for i in range(0, len(rows), SITEMAP_MAX):
            name = f'sitemap-world-{l}-{t}' + (f'-{i // SITEMAP_MAX + 1}' if len(rows) > SITEMAP_MAX else '') + '.xml'
            body = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
            body += [f'  <url><loc>{G.SITE}{u}</loc><lastmod>{lm}</lastmod></url>' for u, lm in rows[i:i + SITEMAP_MAX]]
            body.append('</urlset>')
            (G.OUT / name).write_text('\n'.join(body) + '\n', encoding='utf-8')
            files.append((name, max(lm for _, lm in rows[i:i + SITEMAP_MAX])))
    idx = ['<?xml version="1.0" encoding="UTF-8"?>', '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    idx += [f'  <sitemap><loc>{G.SITE}/{n}</loc><lastmod>{lm}</lastmod></sitemap>' for n, lm in files]
    idx.append('</sitemapindex>')
    (G.OUT / 'sitemap-world.xml').write_text('\n'.join(idx) + '\n', encoding='utf-8')
    rb = G.OUT / 'robots.txt'
    if rb.exists() and 'sitemap-world.xml' not in rb.read_text(encoding='utf-8'):
        rb.write_text(rb.read_text(encoding='utf-8') + f'Sitemap: {G.SITE}/sitemap-world.xml\n', encoding='utf-8')


# ------------------------------------------------------------------ self test
def selftest():
    ok = True

    def chk(c, m):
        nonlocal ok
        print('ok  ' if c else 'FAIL', m)
        ok &= bool(c)
    chk(fmt_num(1234567, L['en']) == '1,234,567' and fmt_num(1234567, L['sr']) == '1.234.567' and fmt_num(1234.5, L['ru'], 1) == '1 234,5', 'numbers')
    chk([pl_form(n, 'a|b|c', 'sr') for n in (1, 2, 5, 11, 21, 22, 25, 112)] == list('abccabcc'), 'pl sr/ru')
    chk([pl_form(n, 'a|b|c', 'en') for n in (1, 2, 21)] == ['a', 'b', 'b'], 'pl en')
    chk(fmt_date('2026-11-09') == '09.11.2026' and fmt_month('2026-03') == '03.2026', 'dates')
    chk(seo_title('x' * 40) == 'x' * 40 + ' | BlokVolt' and seo_title('x' * 55) == 'x' * 55, 'seo_title')
    S = load_strings()
    chk(set(S['en']) == set(S['sr']) == set(S['ru']), 'strings: same keys in en/sr/ru')
    bad = [k for k, v in S['sr'].items() if re.search(r'\b(mi|naš|naša|naše|naši|odmah|redakcija)\b|24/7|[А-Яа-я]', re.sub(r'<[^>]+>', '', v), re.I)]
    chk(not bad, f'sr strings: no mi/odmah/24-7/Cyrillic {bad}')
    chk(not [k for k in S['en'] if k.startswith('t_') and re.search(r'\d', S['en'][k] + S['sr'][k] + S['ru'][k])], 'titles have no digits')
    # state rules on a tiny synthetic bundle
    import tempfile
    d = Path(tempfile.mkdtemp())
    def bundle(date, n50_city, h):
        b = d / f'pages-{date}'
        (b / 'cities' / 'DE').mkdir(parents=True, exist_ok=True)
        city = dict(type='city', cc='DE', gid=1, city=dict(gid=1, name='Testburg', ascii='Testburg', admin1='01', pop=50000))
        (b / 'cities/DE/1.json').write_text(json.dumps(city))
        pages = [dict(type='city', cc='DE', gid=1, file='cities/DE/1.json', hash=h, n=n50_city, n50=n50_city)] if n50_city else []
        (b / 'index.json').write_text(json.dumps(dict(date=date, stage='month', pages=pages,
                                                      thresholds=dict(country=100, city=20, net=20, gnet=100))))
        return b
    sp, rp = d / 'state.json', d / 'red.txt'
    s = update_state(bundle('2026-11-09', 30, 'h1'), sp, rp)
    u = '/charging-stations/germany/testburg/'
    chk(s[u]['first_seen'] == '2026-11-09' and s[u]['last_changed'] == '2026-11-09', 'state: new page')
    s = update_state(bundle('2026-11-16', 30, 'h1'), sp, rp)
    chk(s[u]['last_changed'] == '2026-11-09', 'state: same hash keeps lastmod')
    s = update_state(bundle('2026-11-23', 31, 'h2'), sp, rp)
    chk(s[u]['last_changed'] == '2026-11-23', 'state: new hash moves lastmod')
    s = update_state(bundle('2026-11-30', 0, ''), sp, rp)
    chk(s[u]['below_threshold_since'] == '2026-11-30' and rp.read_text() == '', 'state: drop -> below, no redirect yet')
    s = update_state(bundle('2026-12-07', 22, 'h3'), sp, rp)
    chk(s[u]['below_threshold_since'] == '2026-11-30', 'state: back at 22 < 24 (120 %) stays below')
    s = update_state(bundle('2027-01-25', 0, ''), sp, rp)
    chk(f'{u} /charging-stations/germany/ 301\n' in rp.read_text() and len(rp.read_text().splitlines()) == 3, 'state: after 8 weeks a redirect line per language')
    s = update_state(bundle('2027-02-01', 24, 'h4'), sp, rp)
    chk(s[u]['below_threshold_since'] is None and s[u]['last_changed'] == '2027-02-01' and rp.read_text() == '', 'state: back at 120 %')
    print('selftest:', 'PASS' if ok else 'FAIL')
    return 0 if ok else 1


if __name__ == '__main__':
    if len(sys.argv) >= 2 and sys.argv[1] == 'selftest':
        sys.exit(selftest())
    if len(sys.argv) >= 3 and sys.argv[1] == 'update-state':
        st = update_state(sys.argv[2])
        print(f'world state: {len(st)} URLs, below threshold {sum(1 for s in st.values() if s.get("below_threshold_since"))}')
        sys.exit(0)
    print(__doc__)
    sys.exit(2)
