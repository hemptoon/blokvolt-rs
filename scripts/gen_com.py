# -*- coding: utf-8 -*-
"""Builds blokvolt.com — the regional site — into dist-com/ (docs/RUNBOOK.md 3.10 and 3.23).

Two layers, one design (the design system of www.blokvolt.rs: bv.css, bv.js, the same map script):

1. English: the hub `/`, one page per country (`/croatia/` …, from content/com/research/<CODE>.json), `/serbia/`
   (a summary that leads to blokvolt.rs), `/partners/`, `/404.html`.
2. Local sections in the country's language — `/hr/` (Croatian), `/ba/` (Bosnian), `/me/` (Montenegrin) — made of
   Markdown pages in content/com/local/<dir>/*.md (front matter + Jinja widgets from templates/com2/_w.html) with the
   facts of content/com/local/<dir>/country.json and the station list content/com/local/<cc>/stanice.json
   (scripts/region_map.py). UI words: content/com/local/strings.json.

hreflang: every local page names its variants in the other local sections (same `key`), the English country page for
the hub, and — for the pages that exist on blokvolt.rs too (map, prices, apps, home charging, subsidies, buildings,
statistics, method) — the Serbian page on blokvolt.rs with its /en/ and /ru/ versions (build.py writes the same
cluster on the blokvolt.rs side: REGION_ALTS). x-default follows blokvolt.rs where it is in the cluster.

Usage: python3 scripts/gen_com.py   (writes dist-com/; exits 1 on broken internal links or a missing widget value)"""
import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import urlparse

import markdown
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from markupsafe import Markup, escape

ROOT = Path(__file__).resolve().parent.parent
COM = ROOT / 'content' / 'com'
LOCAL = COM / 'local'
OUT = Path(os.environ.get('BV_COM_OUT') or ROOT / 'dist-com')   # BV_COM_OUT: build elsewhere (parallel drafts)
RS_DIST = ROOT / 'dist'

cfg = json.load(open(COM / 'site.json', encoding='utf-8'))
SITE = cfg['site']
RS = 'https://www.blokvolt.rs'
CHECKED, CHECKED_ISO, EMAIL = cfg['checked'], cfg['checked_iso'], cfg['email']

# ------------------------------------------------------------------ locales
LOCALES = {
    'hr': dict(key='hr', cc='HR', dir='hr', html='hr', hreflang='hr-HR', og='hr_HR', code='HR', en='/croatia/',
               country='Hrvatska', switch='Hrvatska', cur='EUR', cur_sign='€', dec=',', thou='.',
               lang_en='Croatian', open_local='Otvori vodič na hrvatskom'),
    'ba': dict(key='ba', cc='BA', dir='ba', html='bs', hreflang='bs-BA', og='bs_BA', code='BA', en='/bosnia-and-herzegovina/',
               country='Bosna i Hercegovina', switch='Bosna i Hercegovina', cur='KM', cur_sign='KM', dec=',', thou='.',
               lang_en='Bosnian', open_local='Otvori vodič na bosanskom'),
    'me': dict(key='me', cc='ME', dir='me', html='sr-Latn-ME', hreflang='sr-ME', og='sr_ME', code='ME', en='/montenegro/',
               country='Crna Gora', switch='Crna Gora', cur='EUR', cur_sign='€', dec=',', thou='.',
               lang_en='Montenegrin', open_local='Otvori vodič na crnogorskom'),
    # Albanian for Albania (sq-AL) and for Kosovo: "sq" alone, because Google takes ISO 3166-1 regions only and XK is not one
    'al': dict(key='al', cc='AL', dir='al', html='sq', hreflang='sq-AL', og='sq_AL', code='AL', en='/albania/',
               country='Shqipëria', switch='Shqipëria', cur='ALL', cur_sign='lekë', dec=',', thou='\u00a0', plural='sq', trim=True,
               lang_en='Albanian', open_local='Hap udhëzuesin në shqip'),
    'xk': dict(key='xk', cc='XK', dir='xk', html='sq', hreflang='sq', og='sq_AL', code='XK', en='/kosovo/',
               country='Kosova', switch='Kosova', cur='EUR', cur_sign='€', dec=',', thou='\u00a0', plural='sq', place='Place',
               lang_en='Albanian', open_local='Hap udhëzuesin në shqip'),
    'mk': dict(key='mk', cc='MK', dir='mk', html='mk', hreflang='mk-MK', og='mk_MK', code='MK', en='/north-macedonia/',
               country='Северна Македонија', switch='Северна Македонија', cur='MKD', cur_sign='ден.', dec=',', thou='.',
               plural='mk', script='cyrl', trim=True, lang_en='Macedonian', open_local='Отвори го водичот на македонски'),
}
EN = dict(key='en', html='en', hreflang='en', og='en_GB', code='EN', dec='.', thou=',')
# page keys that blokvolt.rs has too: one hreflang cluster across both domains (build.py writes the .rs side from
# the same list, scripts/region_pages.py)
from region_pages import RS_PAGES  # noqa: E402
MD_EXT = ['extra', 'sane_lists', 'md_in_html']
# a number never ends a line apart from its unit: 26 %, 0,35 €, 22 kW, 138 km, 3.000 kWh
NBSP_RE = re.compile(r'(\d) (%|€|KM|kWh|kW|km|h\b|mil\.|min\b|lekë|lek\b|ден\.?|кWh|км|мин)')
# a date written with the ordinal period ("28. 9. 2026.", "03.04.2026.") that ends a sentence takes no second period
DOT_RE = re.compile(r'(\d{4}\.)((?:</a>|</b>|</strong>|</em>)*)\.(?!\.)')

STRINGS = json.load(open(LOCAL / 'strings.json', encoding='utf-8'))
# a section may keep its UI words next to its pages (content/com/local/<dir>/strings.json); they win over the shared file
for _l in LOCALES.values():
    _f = LOCAL / _l['dir'] / 'strings.json'
    if _f.exists():
        STRINGS[_l['key']] = json.load(open(_f, encoding='utf-8'))


# ------------------------------------------------------------------ helpers
def num(x, d=0, loc=None):
    """1234.5 -> '1.234,5' (local) or '1,234.5' (English). Sections with prices in lek or denars (loc trim=True) drop
    trailing zeros: 10,2 lekë, 40 lekë, 2,58 ден. — "10,200 lekë" would read as ten thousand."""
    loc = loc or EN
    if x is None:
        return ''
    s = f'{abs(float(x)):,.{d}f}'
    if loc.get('trim') and '.' in s:
        s = s.rstrip('0').rstrip('.')
    s = s.replace(',', '§').replace('.', loc['dec']).replace('§', loc['thou'])
    return ('−' if float(x) < 0 else '') + s


def money(x, loc, d=2, unit=None):
    return f'{num(x, d, loc)} {unit or loc["cur_sign"]}'


def dom(u):
    return (urlparse(u).netloc or u).replace('www.', '')


URL_RE = re.compile(r'https?://[^\s<>"\')\]]+')


def linkify(t):
    if t is None:
        return ''
    s = str(escape(t))

    def rep(m):
        u = m.group(0).rstrip('.,;:')
        return f'<a href="{u}" rel="noopener nofollow">{dom(u.replace("&amp;", "&"))}</a>' + m.group(0)[len(u):]
    return Markup(URL_RE.sub(rep, s))


def ver(p):
    return hashlib.sha1(p.read_bytes()).hexdigest()[:10]


env = Environment(loader=FileSystemLoader([str(ROOT / 'templates' / 'com2'), str(ROOT / 'templates')]),
                  autoescape=select_autoescape(['html']), trim_blocks=True, lstrip_blocks=True)
env.filters['domain'] = dom
env.filters['lk'] = linkify
env.filters['mono'] = lambda n: ''.join(w[0] for w in re.findall(r'[^\W_]+', n or '?')[:2]).upper() or '?'
env.filters['tojson_safe'] = lambda o: Markup(json.dumps(o, ensure_ascii=False).replace('</', '<\\/'))
env.filters['zip'] = lambda a, b: zip(a, b)


def pl(n, one, few, many):
    """Noun form after a number in Croatian, Bosnian and Montenegrin: 1, 21, 101 -> one; 2-4, 22-24 -> few; else many."""
    n = abs(int(round(float(n))))
    if n % 10 == 1 and n % 100 != 11:
        return one
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return few
    return many


def plural_for(loc):
    """pl() of a local section. Albanian: 1 -> one, everything else plural (21 karikues/stacione). Macedonian: 1, 21, 101
    -> one, else plural (the 'few' and 'many' forms are the same). Pages call pl(n, one, few, many) in every language;
    in Albanian and Macedonian pass the plural twice."""
    rule = loc.get('plural')
    if rule == 'sq':
        return lambda n, one, few, many=None: one if abs(int(round(float(n)))) == 1 else few
    if rule == 'mk':
        return lambda n, one, few, many=None: one if (abs(int(round(float(n)))) % 10 == 1 and abs(int(round(float(n)))) % 100 != 11) else few
    return pl


env.globals['pl'] = pl
# only the local sections that have content are linked from menus and footers
BUILT = [l for l in LOCALES.values() if (LOCAL / l['dir'] / 'country.json').exists()]
env.globals['LOCALS_ALL'] = BUILT


# ------------------------------------------------------------------ writing pages
URLS = []   # (path, priority, lastmod, alternates)


def write(path, html):
    dest = OUT / ('index.html' if path == '/' else path.strip('/') + '/index.html' if path.endswith('/') else path.lstrip('/'))
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(html, encoding='utf-8')


def render(tpl, path, ctx, priority='0.7', lastmod=None, sitemap=True):
    base = dict(SITE=SITE, RS=RS, CHECKED=CHECKED, CHECKED_ISO=CHECKED_ISO, EMAIL=EMAIL, canon=path, path=path)
    base.update(ctx)
    html = env.get_template(tpl).render(**base)
    write(path, html)
    if sitemap and not base.get('noindex'):
        URLS.append((path, priority, lastmod or CHECKED_ISO))
    return html


# ------------------------------------------------------------------ English layer
countries = []
for c in cfg['countries']:
    c = dict(c)
    c['url'] = f"/{c['slug']}/"
    countries.append(c)
LOCAL_OF = {l['cc']: l for l in BUILT}


def en_switch():
    return [('en', '/', 'English', 'en'), ('rs', RS + '/', 'Srbija', 'sr')] + \
           [(l['key'], f"/{l['dir']}/", l['switch'], l['hreflang']) for l in BUILT]


EN_NAV = [('/#countries', 'Countries', 'countries'), ('/#local', 'In your language', 'local'), ('/serbia/', 'Serbia', 'serbia'),
          ('/partners/', 'For companies', 'partners')]


def rs_firm_count():
    n = 0
    for p in (ROOT / 'content' / 'firme').glob('*.json'):
        f = json.load(open(p, encoding='utf-8'))
        if f.get('publish') and f.get('group') != 'L':
            n += 1
    return n


def collect_sources(r):
    seen, out = set(), []

    def add(url, title, date):
        if not url or not str(url).startswith('http') or url in seen:
            return
        seen.add(url)
        out.append({'url': url, 'title': title or dom(url), 'date': date or ''})

    def walk(o):
        if isinstance(o, dict):
            if 'source' in o:
                add(o.get('source'), o.get('source_title'), o.get('source_date'))
            for v in o.values():
                if isinstance(v, (dict, list)):
                    walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk({k: v for k, v in r.items() if k != 'home_companies'})
    for h in r.get('home_companies', []):
        add(h.get('url'), f"{h['name']} — company website", h.get('source_date'))
    return out


def build_english(local_hubs):
    n_rs = rs_firm_count()
    research, all_sources, n_companies = {}, set(), n_rs
    pages = []
    en_ctx = dict(LOC=EN, S=STRINGS['en'], NAV=EN_NAV, SWITCH=en_switch(), home='/', COUNTRIES=countries, LOCALS=local_hubs)
    for c in countries:
        if c['code'] == 'RS':
            continue
        r = json.load(open(COM / 'research' / f"{c['code']}.json", encoding='utf-8'))
        research[c['code']] = r
        srcs = collect_sources(r)
        all_sources.update(s['url'] for s in srcs)
        n_companies += len(r.get('home_companies', []))
        loc = LOCAL_OF.get(c['code'])
        alts = []
        if loc:
            alts = [('en', SITE + c['url']), (loc['hreflang'], SITE + f"/{loc['dir']}/"), ('x-default', SITE + c['url'])]
        title = f"EV charging in {c['name']}: public networks, prices, home chargers and subsidies | BlokVolt"
        desc = (f"{c['name']}: public charging networks and prices, electricity at home, subsidies and the rules for "
                f"apartment buildings — every figure with a source, checked {r['checked']}.")
        render('en_country.html', c['url'], dict(en_ctx, c=c, r=r, glance=list(zip(('EV fleet', 'Public charging', 'Subsidies', 'Home chargers'), c['facts'])),
                                                 sources=srcs, n_sources=len(srcs), title=title, description=desc, alts=alts,
                                                 section='countries', local=loc), priority='0.8')
        pages.append(c['url'])
    render('en_serbia.html', '/serbia/', dict(en_ctx, RSX=cfg['serbia'], n_rs_firms=n_rs, section='serbia', alts=[],
                                              title='EV charging in Serbia: public charging, prices, installers and subsidies | BlokVolt',
                                              description=(f'Serbia in short — {n_rs} installers and sellers of home chargers, public charging networks, '
                                                           'EPS electricity prices, the €5,000 subsidy and the rules for apartment buildings — with the full guide on blokvolt.rs.')),
           priority='0.8')
    render('en_home.html', '/', dict(en_ctx, n_companies=n_companies, n_sources=len(all_sources), n_rs_firms=n_rs, section='', alts=[],
                                     title='EV charging in Serbia and the Western Balkans — maps, prices, subsidies | BlokVolt',
                                     description=('Public charging networks and prices, electricity at home, subsidies and apartment-building rules in Serbia, '
                                                  'Croatia, Bosnia and Herzegovina, Montenegro, North Macedonia, Albania, Kosovo and Slovenia — with maps and local-language guides.')),
           priority='1.0')
    render('en_partners.html', '/partners/', dict(en_ctx, section='partners', alts=[], title='For companies and suppliers | BlokVolt',
                                                  description='How to get a company listed or corrected on BlokVolt — free and by the same rules for everyone — and where charging-hardware quotations go.'),
           priority='0.3')
    render('en_404.html', '/404.html', dict(en_ctx, section='', alts=[], title='Page not found | BlokVolt',
                                            description='This page does not exist.', noindex=True), sitemap=False)
    return len(all_sources), n_companies


# ------------------------------------------------------------------ local layer
FM_RE = re.compile(r'^---\n(.*?)\n---\n(.*)$', re.S)


def front_matter(text):
    m = FM_RE.match(text)
    if not m:
        raise SystemExit('no front matter')
    meta = {}
    for line in m.group(1).splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        k, _, v = line.partition(':')
        meta[k.strip()] = v.strip()
    return meta, m.group(2)


def load_local(loc):
    d = LOCAL / loc['dir']
    C = json.load(open(d / 'country.json', encoding='utf-8'))
    st = json.load(open(LOCAL / loc['cc'].lower() / 'stanice.json', encoding='utf-8'))
    pages = []
    for p in sorted(d.glob('*.md')):
        meta, body = front_matter(p.read_text(encoding='utf-8'))
        meta['file'] = p.name
        meta['body'] = body
        meta['order'] = int(meta.get('order', 50))
        pages.append(meta)
    pages.sort(key=lambda m: m['order'])
    for m in pages:
        m['path'] = f"/{loc['dir']}/{m['slug']}" if m.get('slug') else f"/{loc['dir']}/"
    return C, st, pages


def map_stats(st):
    ss = st['stations']
    by_net = {}
    for s in ss:
        if s['net']:
            by_net[s['net']] = by_net.get(s['net'], 0) + 1
    return {'n': len(ss), 'dc50': sum(1 for s in ss if (s['dc'] or 0) >= 50), 'hpc': sum(1 for s in ss if (s['dc'] or 0) >= 150),
            'ac': sum(1 for s in ss if not s['dc']), 'by_net': by_net, 'retrieved': st['retrieved'], 'osm_base': st['osm_base'],
            'ocm_export': st['ocm_export'], 'public': sum(1 for s in ss if s['acc'] == 'public')}


def price_file(C, loc):
    """/assets/region/<cc>/cijene.json for the map (map.js 'nets'): per-kWh tiers by current and power."""
    nets = {}
    for n in C['networks']:
        tiers = []
        for p in n.get('prices', []):
            if p.get('v') is None or p.get('seg') not in ('AC', 'DC', 'HPC'):
                continue
            cur = 'ac' if p['seg'] == 'AC' else 'dc'
            lo, hi = p.get('lo', 0), p.get('hi', 1000)
            tiers.append({'cur': cur, 'lo': lo, 'hi': hi, 'v': p['v'], 'label': f"{num(p['v'], 2, loc)} {loc['cur_sign']}/kWh",
                          'extra': p.get('cond', ''), 'date': n.get('valid_from') or n.get('checked') or '', 'src': n.get('src_label', ''), 'where': []})
        nets[n['slug']] = {'name': n['name'], 'kwh': True, 'tiers': tiers, 'places': [], 'receipts': [],
                           'note': n.get('map_note', ''), 'site': n.get('site', ''),
                           'page': f"/{loc['dir']}/{C['slugs']['prices']}#{n['slug']}"}
    return {'about': 'Our table of public charging prices per network (not open data).', 'nets': nets}


def hreflang(key, loc, all_pages):
    alts = []
    for l2 in LOCALES.values():
        pg = all_pages.get(l2['key'], {}).get(key)
        if pg:
            alts.append((l2['hreflang'], SITE + pg['path']))
    if key == 'hub':
        alts.append(('en', SITE + loc['en']))
        alts.append(('x-default', SITE + loc['en']))
    elif key in RS_PAGES and loc['key'] != 'xk':   # blokvolt.rs does not list /xk/ (scripts/region_pages.py)
        rp = RS_PAGES[key]
        alts += [('sr', RS + rp), ('en', RS + '/en' + rp), ('ru', RS + '/ru' + rp), ('x-default', RS + rp)]
    if len(alts) < 2:
        return []
    return alts


def build_local(loc, C, st, pages, all_pages):
    S = STRINGS[loc['key']]
    M = map_stats(st)
    by_key = {p['key']: p for p in pages}
    NAV = [(p['path'], p['nav'], p['key']) for p in pages if p.get('nav')]
    SWITCH = en_switch()
    # map and price data for the map page
    reg = OUT / 'assets' / 'region' / loc['cc'].lower()
    reg.mkdir(parents=True, exist_ok=True)
    (reg / 'stanice.json').write_text(json.dumps(st, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    (reg / 'cijene.json').write_text(json.dumps(price_file(C, loc), ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    # statistics CSV (CC BY 4.0)
    if C.get('csv'):
        rows = ['﻿' + ';'.join(C['csv']['head'])] + [';'.join(str(x) for x in r) for r in C['csv']['rows']]
        (OUT / loc['dir']).mkdir(parents=True, exist_ok=True)
        (OUT / loc['dir'] / C['csv']['file']).write_text('\n'.join(rows) + '\n', encoding='utf-8')
    ctx0 = dict(LOC=loc, S=S, C=C, M=M, NAV=NAV, SWITCH=SWITCH, home=f"/{loc['dir']}/", PAGES=by_key, pl=plural_for(loc),
                num=lambda x, d=0: num(x, d, loc), money=lambda x, d=2, unit=None: money(x, loc, d, unit), EN_URL=loc['en'])
    body_tpl_head = "{% import '_w.html' as w with context %}"
    for p in pages:
        ctx = dict(ctx0, page=p, section=p['key'])
        text = env.from_string(body_tpl_head + p['body']).render(**ctx)
        html = markdown.markdown(text, extensions=MD_EXT, output_format='html')
        html = html.replace('<table>', '<div class="tw"><table>').replace('</table>', '</table></div>')
        html = NBSP_RE.sub('\\1\u00a0\\2', html)
        html = DOT_RE.sub('\\1\\2', html)
        related = [by_key[k.strip()] for k in p.get('related', '').split(',') if k.strip() in by_key]
        tpl = {'hub': 'loc_hub.html', 'map': 'loc_map.html'}.get(p.get('template', 'page'), 'loc_page.html')
        extra = {}
        if p.get('template') == 'map':
            extra['map_cfg'] = json.dumps({
                'style': 'https://tiles.openfreemap.org/styles/positron', 'font': ['Noto Sans Bold'],
                'stations': f"/assets/region/{loc['cc'].lower()}/stanice.json?v={ver(reg / 'stanice.json')}",
                'prices': f"/assets/region/{loc['cc'].lower()}/cijene.json?v={ver(reg / 'cijene.json')}",
                'center': C['map']['center'], 'zoom': C['map']['zoom'], 'cur': loc['cur'],
                'num': {'dec': loc['dec'], 'thou': loc['thou'], 'trim': bool(loc.get('trim'))},
                'fix': 'mailto:' + EMAIL + '?subject=' + S['map_fix_subject'].replace(' ', '%20') + '%20{id}',
            }, ensure_ascii=False).replace('</', '<\\/')
            extra['map_i18n'] = json.dumps(S['map'], ensure_ascii=False)
            extra['chips'] = [(slug, C['net_names'].get(slug, slug), n) for slug, n in sorted(M['by_net'].items(), key=lambda x: -x[1]) if n >= 3][:7]
        render(tpl, p['path'], dict(ctx, **extra, title=p['title'], description=p['description'], meta=p, body=Markup(html),
                                    related=related, alts=hreflang(p['key'], loc, all_pages)),
               priority=p.get('priority', '0.7'), lastmod=C.get('checked_iso'))
    return M


# ------------------------------------------------------------------ assets, sitemap, link check
def copy_assets():
    a = OUT / 'assets'
    for rel in ('bv.css', 'bv.js', 'map.js', 'favicon.svg', 'apple-touch-icon.png'):
        (a / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / 'static' / 'assets' / rel, a / rel)
    shutil.copytree(ROOT / 'static' / 'assets' / 'vendor' / 'maplibre-6.11.1', a / 'vendor' / 'maplibre-6.11.1', dirs_exist_ok=True)
    fonts = ROOT / 'static' / 'assets' / 'fonts'
    (a / 'fonts').mkdir(parents=True, exist_ok=True)
    for f in fonts.glob('onest-*.woff2'):
        shutil.copy2(f, a / 'fonts' / f.name)
    shutil.copy2(ROOT / 'static' / 'com' / 'com.css', a / 'com.css')
    (a / 'og').mkdir(exist_ok=True)
    for f in (ROOT / 'static' / 'com').glob('og-*.png'):
        shutil.copy2(f, a / 'og' / f.name)
    logos = ROOT / 'static' / 'com' / 'logos'
    if logos.exists():
        shutil.copytree(logos, a / 'logos', dirs_exist_ok=True)


def bust():
    a = OUT / 'assets'
    v = {n: ver(a / n) for n in ('bv.css', 'bv.js', 'map.js', 'com.css')}
    for p in OUT.rglob('*.html'):
        t = p.read_text(encoding='utf-8')
        for n, h in v.items():
            t = t.replace(f'/assets/{n}"', f'/assets/{n}?v={h}"')
        p.write_text(t, encoding='utf-8')


def link_check():
    bad = []
    for p in OUT.rglob('*.html'):
        for href in re.findall(r'href="([^"]+)"', p.read_text(encoding='utf-8')):
            if href.startswith('/') and not href.startswith('//'):
                path = href.split('#')[0].split('?')[0]
                if not path:
                    continue
                t = OUT / path.lstrip('/')
                if not (t.is_file() or (t / 'index.html').is_file()):
                    bad.append((p.relative_to(OUT), href))
            elif href.startswith(RS + '/') and RS_DIST.exists():
                path = urlparse(href).path
                t = RS_DIST / path.lstrip('/')
                if not (t.is_file() or (t / 'index.html').is_file() or t.with_suffix('.html').is_file() or path == '/'):
                    bad.append((p.relative_to(OUT), href))
    return bad


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    loaded, all_pages, local_hubs = {}, {}, []
    for loc in LOCALES.values():
        if not (LOCAL / loc['dir'] / 'country.json').exists():
            continue
        C, st, pages = load_local(loc)
        loaded[loc['key']] = (C, st, pages)
        all_pages[loc['key']] = {p['key']: p for p in pages}
        hub = next(p for p in pages if p['key'] == 'hub')
        local_hubs.append(dict(loc=loc, path=hub['path'], title=hub['h1'], lead=hub.get('card', hub.get('lead', '')), C=C))
    n_sources, n_companies = build_english(local_hubs)
    for key, (C, st, pages) in loaded.items():
        M = build_local(LOCALES[key], C, st, pages, all_pages)
        print(f"/{LOCALES[key]['dir']}/: {len(pages)} pages, map {M['n']} stations (DC ≥ 50 kW {M['dc50']})")
    copy_assets()
    bust()
    (OUT / 'CNAME').write_text('blokvolt.com\n', encoding='utf-8')
    (OUT / 'README.md').write_text(
        '# blokvolt.com\n\nThe regional site of BlokVolt: an English guide to EV charging in Serbia and its neighbours and local-language '
        'sections (' + ', '.join(f"/{l['dir']}/" for l in BUILT) + '). Served by GitHub Pages (custom domain blokvolt.com).\n\nThis repository holds the built site only. '
        'Pages are generated by `scripts/gen_com.py` in [hemptoon/blokvolt-rs](https://github.com/hemptoon/blokvolt-rs) from `content/com/` — '
        'edit the data there, rebuild and upload; do not edit the HTML here by hand. Procedure: `docs/RUNBOOK.md`, sections 3.10 and 3.23.\n\n'
        'Map data: © OpenStreetMap contributors (ODbL 1.0) and Open Charge Map (CC BY 4.0); see /assets/region/<cc>/stanice.json.\n',
        encoding='utf-8')
    (OUT / '.nojekyll').write_text('\n', encoding='utf-8')
    (OUT / 'robots.txt').write_text(f'User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n', encoding='utf-8')
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u, pr, lm in URLS:
        sm.append(f'  <url><loc>{SITE}{u}</loc><lastmod>{lm}</lastmod><priority>{pr}</priority></url>')
    sm.append('</urlset>')
    (OUT / 'sitemap.xml').write_text('\n'.join(sm) + '\n', encoding='utf-8')
    bad = link_check()
    files = [p for p in OUT.rglob('*') if p.is_file()]
    print(f'blokvolt.com: {len(URLS)} pages in the sitemap, {len(files)} files, {n_companies} companies, {n_sources} English sources; broken links: {len(bad)}')
    for b in bad:
        print('  broken:', *b)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
