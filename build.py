# -*- coding: utf-8 -*-
"""BlokVolt static site generator (blokvolt.rs). Python 3 + Jinja2 + Markdown + BeautifulSoup.
Usage: python3 build.py  -> dist/
"""
import json, os, re, shutil, glob, datetime, html
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
import markdown
from bs4 import BeautifulSoup

ROOT = Path(__file__).parent
DIST = ROOT / 'dist'
SITE = 'https://www.blokvolt.rs'
# Dates live in content/data/site.json: 'updated' = last content update (footer, home, sitemap lastmod),
# 'firms_checked' = last full revision of the firm register. Update them there, not here.
SITE_META = json.load(open(ROOT / 'content' / 'data' / 'site.json', encoding='utf-8'))
TODAY = SITE_META['updated']
ISO_TODAY = '-'.join(reversed(TODAY.split('.')))
FIRMS_CHECKED = SITE_META['firms_checked']

env = Environment(loader=FileSystemLoader(str(ROOT / 'templates')), autoescape=select_autoescape(['html']), trim_blocks=True, lstrip_blocks=True)

def sr_num(x, d=0):
    """Serbian number format: 1.234,56"""
    s_ = f'{abs(float(x)):,.{d}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    return ('−' if float(x) < 0 and round(abs(float(x)), d) != 0 else '') + s_
env.filters['sr'] = sr_num

GROUPS = {
    'A': ('Punjač sa ugradnjom — javna cena', 'Firme koje objavljuju cenu punjača zajedno sa ugradnjom.'),
    'B': ('Javna cena uređaja, ugradnja na upit', 'Cena uređaja je na sajtu, ugradnja se nudi ali se cena dobija na upit.'),
    'C': ('Samo uređaj — web-shop, bez ugradnje', 'Prodaju punjač; ugradnju ne pominju ili je ne nude.'),
    'D': ('Bez javne cene — samo na upit', 'Prodaju i/ili ugrađuju, ali cene ne objavljuju.'),
    'E': ('Samo ugradnja — električari', 'Ne prodaju uređaj; montiraju punjač koji donesete.'),
}
KINDS = {
    'instalater': 'Prodaja i ugradnja', 'prodavnica': 'Web-shop / prodavnica', 'distributer': 'Distributer brenda',
    'solar': 'Solarni integrator', 'elektricar': 'Električar', 'operator': 'Operator javne mreže', 'trag': 'Na proveri',
}
CITY_SLUGS = {'Beograd': 'beograd', 'Novi Sad': 'novi-sad', 'Niš': 'nis'}

# ---------- helpers ----------
def read_json_dir(d):
    out = []
    for f in sorted(glob.glob(str(ROOT / 'content' / d / '*.json'))):
        out.append(json.load(open(f, encoding='utf-8')))
    return out

def md_to_html(text):
    h = markdown.markdown(text, extensions=['tables', 'attr_list', 'md_in_html', 'sane_lists'])
    s = BeautifulSoup(h, 'html.parser')
    for t in s.find_all('table'):
        heads = [th.get_text(' ', strip=True) for th in t.find_all('th')]
        t['class'] = 'bva-tbl'
        for tr in t.find_all('tr'):
            for i, td in enumerate(tr.find_all('td')):
                if i < len(heads):
                    td['data-label'] = heads[i]
        wrap = s.new_tag('div', attrs={'class': 'bva-tw'})
        t.wrap(wrap)
    for ul in s.find_all('ul'):
        if ul.find_parent('li'):
            continue
    return str(s)

def front_matter(path):
    txt = open(path, encoding='utf-8').read()
    m = re.match(r'^---\n(.*?)\n---\n(.*)$', txt, re.S)
    meta = {}
    body = txt
    if m:
        for line in m.group(1).split('\n'):
            if ':' in line:
                k, v = line.split(':', 1)
                meta[k.strip()] = v.strip().strip('"')
        body = m.group(2)
    return meta, body

def write(path, content):
    p = DIST / path.lstrip('/')
    if path.endswith('/') or not os.path.splitext(path)[1]:
        p = p / 'index.html'
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding='utf-8')

def city_of(firm):
    c = firm.get('city', '')
    for name in CITY_SLUGS:
        if name in c:
            return name
    return None

def verdict_class(v):
    v = (v or '').lower()
    if v.startswith('ne pominje') or v.startswith('uređaj ne') or v in ('', 'ne', 'ne nudi', 'nije navedena', 'nije navedeno'):
        return 'no'
    if v.startswith('na upit') or 'renta' in v:
        return 'ask'
    return 'yes'

# ---------- load content ----------
firms = read_json_dir('firme')
published = [f for f in firms if f.get('publish')]
order = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4}
def firm_sort(f):
    return (order.get(f['group'], 9), 0 if f.get('is_us') else 1, f['name'].lower())
published.sort(key=firm_sort)
for f in published:
    f['kind_label'] = KINDS.get(f.get('kind', ''), '')
    f['city_main'] = city_of(f)
    f['city_slug'] = CITY_SLUGS.get(f['city_main'] or '', '')
    f['url'] = f"/firme/{f['slug']}/"
    f['group_label'] = GROUPS[f['group']][0]
    f['vclass'] = {k: verdict_class(v) for k, v in f.get('verdicts', {}).items()}
by_group = {g: [f for f in published if f['group'] == g] for g in GROUPS}
cities = {}
for f in published:
    if f['city_main']:
        cities.setdefault(f['city_main'], []).append(f)

operators = sorted([o for o in read_json_dir('operateri') if o.get('publish')], key=lambda o: o.get('order', 99))
for o in operators:
    o['url'] = f"/javno-punjenje/{o['slug']}/"
    o['network_short'] = o.get('card') or ''
KIND_GROUPS = [('cpo', 'Komercijalne mreže'), ('drzavni', 'Državni punjači'), ('host', 'Domaćini — benzinske stanice'), ('app', 'Aplikacije za plaćanje'), ('besplatno', 'Besplatno punjenje')]
KIND_RANK = {k: i for i, (k, _) in enumerate(KIND_GROUPS)}
operators.sort(key=lambda o: (KIND_RANK.get(o['kind'], 9), o.get('order', 99)))
ops_by_kind = {k: [o for o in operators if o['kind'] == k] for k, _ in KIND_GROUPS}
price_index = json.load(open(ROOT / 'content' / 'javno' / 'indeks-cena.json', encoding='utf-8'))

def _r(x):
    return int(x + 0.5)

def kwh_html(row):
    parts = []
    if row.get('kwh'):  # a real receipt: exact price per kWh
        return f'<span class="k">= {_r(row["rsd_total"] / row["kwh"])} RSD po kWh</span><span class="k">stvarni račun</span>'
    if row.get('unit_rsd'):  # billed per operator-defined "charging unit", not per kWh
        return '<span class="k">ne preračunava se</span><span class="k">„jedinica“ nije kWh</span>'
    if row.get('rsd_hour'):
        for k in row['assume_kw']:
            parts.append(f'<span class="k">≈{_r(row["rsd_hour"] / k)} RSD pri {k} kW</span>')
        return ''.join(parts)
    vals = row['rsd_min']
    for k in row['assume_kw']:
        lo, hi = _r(min(vals) / (k / 60)), _r(max(vals) / (k / 60))
        txt = f'≈{lo}' if lo == hi else f'≈{lo}–{hi}'
        parts.append(f'<span class="k">{txt} RSD pri {k} kW</span>')
    return ''.join(parts)

for row in price_index['rows']:
    if not row.get('free'):
        row['kwh_html'] = kwh_html(row)

# ---------- shared context ----------
NAV = [('/firme/', 'Firme'), ('/cena-punjaca-za-elektricni-auto', 'Cene'), ('/javno-punjenje/', 'Javno punjenje'), ('/alati/kalkulator-troskova/', 'Kalkulator'), ('/vodici/', 'Vodiči'), ('/podaci/', 'Podaci')]
base_ctx = dict(SITE=SITE, TODAY=TODAY, FIRMS_CHECKED=FIRMS_CHECKED, SITE_META=SITE_META, NAV=NAV, n_firms=len(published), n_leads=len(firms) - len(published), n_vodica=7, n_ops=len(operators))

def render(tpl, path, **ctx):
    t = env.get_template(tpl)
    c = dict(base_ctx); c.update(ctx); c['path'] = path
    write(path, t.render(**c))

# ---------- build ----------
if DIST.exists():
    shutil.rmtree(DIST)
DIST.mkdir()
shutil.copytree(ROOT / 'static', DIST, dirs_exist_ok=True)

urls = []
def add_url(path, prio='0.6', lastmod=ISO_TODAY):
    urls.append((SITE + path, prio, lastmod))

# nav + footer html (rendered once, used to patch legacy pages)
nav_html = env.get_template('_nav.html').render(**base_ctx, path='')
foot_html = env.get_template('_footer.html').render(**base_ctx)

SCRIPTS = ('<script src="/assets/vendor/gsap.min.js" defer></script>\n'
           '<script src="/assets/meganav.js" defer></script>\n'
           '<script src="/assets/site.js" defer></script>')

def patch_legacy(html_text, current=None):
    """Replace legacy nav/footer with the new ones and fix counts/dates."""
    nav = nav_html if not current else env.get_template('_nav.html').render(**base_ctx, path=current)
    html_text = re.sub(r'<div class="v3-nav">.*?(?=<div class="v3-ph">)', nav, html_text, count=1, flags=re.S)
    html_text = re.sub(r'<div class="v3-foot">.*?<div class="v3-legal">.*?</div></div>', foot_html, html_text, count=1, flags=re.S)
    html_text = html_text.replace('<link rel="stylesheet" href="/assets/webflow.css">\n', '')
    html_text = html_text.replace('<link rel="stylesheet" href="/assets/site.css">', '<link rel="stylesheet" href="/assets/site.css">\n<link rel="stylesheet" href="/assets/agg.css">')
    html_text = html_text.replace('<script src="/assets/site.js" defer></script>', SCRIPTS)
    html_text = html_text.replace('cene 20 firmi', 'cene 42 firme').replace('Cene 20 firmi', 'Cene 42 firme').replace('20 firmi', '42 firme')
    return html_text

# 1) legacy guides (passthrough with new chrome)
LEGACY = ['cena-punjaca-za-elektricni-auto', 'punjac-u-zgradi-skupstina', 'ko-placa-struju-za-punjenje', 'punjac-u-iznajmljenoj-garazi',
          'bezbednost-punjenja-atest', 'wallbox-cena-srbija', 'punjenje-elektricnog-auta-u-zgradi', 'politika-privatnosti']
GUIDES_META = []
for slug in LEGACY:
    src = (ROOT / 'content' / 'vodici' / f'{slug}.html').read_text(encoding='utf-8')
    title = re.search(r'<title>(.*?)</title>', src).group(1)
    desc = re.search(r'<meta name="description" content="([^"]*)"', src).group(1)
    GUIDES_META.append({'slug': slug, 'title': html.unescape(title.split(' | ')[0]), 'desc': html.unescape(desc)})
    out = patch_legacy(src, current='/' + slug)
    if slug == 'cena-punjaca-za-elektricni-auto':
        # regenerate the comparison tables from JSON
        tbl = env.get_template('_cena_tabela.html').render(**base_ctx, GROUPS=GROUPS, by_group=by_group)
        out = re.sub(r'<div class="bva bva-wide" id="tabela">.*?</div></div>(?=<div class="bva")', tbl, out, count=1, flags=re.S)
        out = out.replace('stanje 07.09.2026', 'stanje 22.09.2026').replace('Ažurirano 7. septembra 2026.', 'Ažurirano 22. septembra 2026.').replace('ažurirano 07.09.2026', 'ažurirano 22.09.2026')
        out = out.replace('Zato smo 7. septembra 2026. prošli kroz sajtove', 'Zato smo u septembru 2026. (prva provera 7. septembra, dopuna 22. septembra) prošli kroz sajtove')
        out = out.replace('prepisane su sa navedenih stranica 7. septembra 2026.', 'prepisane su sa navedenih stranica 7. i 22. septembra 2026. (datum provere stoji uz svaku firmu).')
        out = out.replace('"dateModified": "2026-09-07"', '"dateModified": "2026-09-22"')
    write('/' + slug + '.html', out)
    add_url('/' + slug, '0.8' if slug != 'politika-privatnosti' else '0.2')

# 2) vodici hub = legacy index moved to /vodici/
src = (ROOT / 'content' / 'vodici' / 'index.html').read_text(encoding='utf-8')
out = patch_legacy(src, current='/vodici/')
out = out.replace('<link rel="canonical" href="https://www.blokvolt.rs/">', '<link rel="canonical" href="https://www.blokvolt.rs/vodici/">')
out = out.replace('<meta property="og:url" content="https://www.blokvolt.rs/">', '<meta property="og:url" content="https://www.blokvolt.rs/vodici/">')
out = out.replace('"url": "https://www.blokvolt.rs/",\n   "publisher"', '"url": "https://www.blokvolt.rs/vodici/",\n   "publisher"')
out = out.replace('<a href="/" aria-current="page">Svi vodiči</a>', '<a href="/vodici/" aria-current="page">Svi vodiči</a>')
write('/vodici/', out)
add_url('/vodici/', '0.8')

# 3) firms
for f in published:
    render('firma.html', f['url'], firm=f, GROUPS=GROUPS, title=f"{f['name']} — punjači za električne automobile: cene, ugradnja, uslovi | BlokVolt",
           description=f"{f['name']} ({f['city']}): šta nudi, javne cene, da li ugrađuje, brojilo, papiri za skupštinu, garancija. Provereno {f['verified']}. Isti podaci za sve firme.")
    add_url(f['url'], '0.6')
render('firme_index.html', '/firme/', GROUPS=GROUPS, by_group=by_group, firms=published, cities=cities, CITY_SLUGS=CITY_SLUGS, KINDS=KINDS,
       title=f"Firme za punjače u Srbiji — {len(published)} prodavaca i instalatera, iste kolone za sve | BlokVolt",
       description=f"Registar {len(published)} firmi koje prodaju ili ugrađuju kućne punjače za električne automobile u Srbiji: javne cene, ugradnja, MID brojilo, papiri za skupštinu, garancija. Provereno {FIRMS_CHECKED}.")
add_url('/firme/', '0.9')
for city, lst in cities.items():
    slug = CITY_SLUGS[city]
    render('grad.html', f'/gradovi/{slug}/', city=city, firms=lst, GROUPS=GROUPS,
           title=f"Punjači za električni auto — {city}: {len(lst)} firmi koje prodaju i ugrađuju | BlokVolt",
           description=f"Ko prodaje i ugrađuje kućne punjače u gradu {city}: {len(lst)} firmi sa javnim cenama, uslovima ugradnje i garancijom. Provereno {FIRMS_CHECKED}.")
    add_url(f'/gradovi/{slug}/', '0.6')

# 4) markdown pages (podaci, o-sajtu, metodologija, ispravka, izmene)
PODACI = []
CRUMBS = [('/podaci/', ('Podaci', '/podaci/')), ('/javno-punjenje/', ('Javno punjenje', '/javno-punjenje/'))]
md_files = sorted(glob.glob(str(ROOT / 'content' / 'podaci' / '*.md'))) + sorted(glob.glob(str(ROOT / 'content' / 'javno' / '*.md')))
for mdf in md_files:
    meta, body = front_matter(mdf)
    slug = Path(mdf).stem
    path = meta.get('path') or f'/podaci/{slug}/'
    body_html = md_to_html(body)
    crumb = next((c for pre, c in CRUMBS if path.startswith(pre) and path != pre), None)
    render('article.html', path, meta=meta, body=body_html, crumb=crumb, title=meta.get('title') + ' | BlokVolt', description=meta.get('description', ''), sources=[s for s in meta.get('sources', '').split(' | ') if s])
    add_url(path, meta.get('priority', '0.7'))
    if path.startswith('/podaci/'):
        PODACI.append(dict(meta, path=path))
PODACI.sort(key=lambda m: (-float(m.get('priority', '0.5')), m.get('title', '')))
render('podaci_index.html', '/podaci/', pages=PODACI, title='Podaci: subvencije, statistika, tarife, propisi za električne automobile u Srbiji | BlokVolt',
       description='Proverene brojke i propisi za vlasnike električnih automobila u Srbiji — subvencije 2026, registracija i porezi, osiguranje, krediti, uvoz i carina, servisi, statistika, putarina i parking. Svaka stranica sa izvorom i datumom.')
add_url('/podaci/', '0.8')

# 4b) public charging (ring 2)
for o in operators:
    render('operator.html', o['url'], op=o, title=f"{o['name']} — javno punjenje: cene, naplata, uslovi | BlokVolt",
           description=f"{o['name']}: {o['short'][:150]} Provereno {o['verified']}.")
    add_url(o['url'], '0.6')
index_checked = price_index['updated']
render('javno_index.html', '/javno-punjenje/', ops=operators, ops_by_kind=ops_by_kind, KIND_GROUPS=KIND_GROUPS, index=price_index,
       title='Javni punjači u Srbiji — mreže, cene po minutu i po kWh, besplatni punjači | BlokVolt',
       description=f'Ko vodi javne punjače u Srbiji (Charge&GO, Orion eMobility, JP Putevi Srbije, Tesla, OMV…), poslednje zabeležene cene sa računicom po kWh, 36 besplatnih državnih punjača na autoputevima i propisi. Provereno {index_checked}.')
add_url('/javno-punjenje/', '0.9')

# 4c) cost calculator (tools)
CALC = json.load(open(ROOT / 'content' / 'data' / 'kalkulator.json', encoding='utf-8'))
_E, _d = CALC['eps'], CALC['defaults']
def all_in(x):
    return (x + _E['oie'] + _E['ee']) * (1 + _E['akciza']) * (1 + _E['pdv'])
_k100 = _d['kwh100'] * (1 + _d['loss'] / 100)
tariff_rows = [dict(name=z['name'], range=z['range'], nt_raw=z['nt'], vt_raw=z['vt'], nt=all_in(z['nt']), vt=all_in(z['vt']), per100=all_in(z['nt']) * _k100) for z in _E['zones']]
_zone = next(z for z in _E['zones'] if z['id'] == _d['zone'])
home_default = all_in(_zone[_d['tariff']])
public_default = next(p['rsd_kwh'] for p in CALC['public'] if p['id'] == _d['public'])
snaga_brutto = _E['snaga_rsd_kw'] * (1 + _E['akciza']) * (1 + _E['pdv'])
_need = _d['km'] * _d['kwh100'] / 100
_share = _d['public_share'] / 100
_ex = dict(home_kwh=_need * (1 - _share) * (1 + _d['loss'] / 100), pub_kwh=_need * _share)
_ex['home_cost'] = _ex['home_kwh'] * home_default
_ex['pub_cost'] = _ex['pub_kwh'] * public_default
_ex['kw_cost'] = _d['extra_kw'] * snaga_brutto
_ex['ev'] = _ex['home_cost'] + _ex['pub_cost'] + _ex['kw_cost']
_ex['ev100'] = _ex['ev'] / _d['km'] * 100
_ex['ice'] = _d['km'] * _d['l100_' + _d['fuel']] / 100 * CALC['fuel'][_d['fuel']]
_ex['ice100'] = _ex['ice'] / _d['km'] * 100
_ex['save'] = _ex['ice'] - _ex['ev']
_desc = (f"Koliko košta 100 km na struju u Srbiji: kod kuće noću oko {sr_num(tariff_rows[1]['per100'])} RSD (plava zona), "
         f"benzin oko {sr_num(_ex['ice100'])} RSD. Kalkulator sa tarifama EPS-a, cenama goriva od {CALC['fuel']['date']} i računima sa javnih punjača.")
render('kalkulator.html', '/alati/kalkulator-troskova/', calc=CALC, eps=_E, fuel=CALC['fuel'], public=CALC['public'], d=_d,
       tariff_rows=tariff_rows, home_default=home_default, public_default=public_default, snaga_brutto=snaga_brutto, ex=_ex,
       calc_json=json.dumps(CALC, ensure_ascii=False).replace('</', '<\\/'), modified_iso=ISO_TODAY,
       title='Kalkulator troškova električnog automobila — struja kod kuće, javni punjači, benzin i dizel | BlokVolt',
       description=_desc)
add_url('/alati/kalkulator-troskova/', '0.9')

# 4d) building billing calculator (tools)
ZG = json.load(open(ROOT / 'content' / 'data' / 'kalkulator-zgrada.json', encoding='utf-8'))
_zd = ZG['defaults']
_zreal = _zd['auta'] * _zd['kwh_auto'] * _zd['cena_kwh']
_zper = _zreal / _zd['stanovi']
_zgap = max(0.0, _zreal - _zd['pausal'] * _zd['auta'])
_zerr = _zreal - _zd['pausal'] * _zd['auta']
if _zerr > 0.5:
    _m = int(-(-(_zd['brojilo'] * _zd['auta']) // _zerr))
    _zpay = 'mesec dana' if _m <= 1 else (f'{_m} meseci' if _m < 24 else f'{_m / 12:.1f}'.replace('.', ',') + ' godine')
else:
    _zpay = 'paušal već pokriva trošak'
_zex = dict(real=_zreal, real_y=_zreal * 12, per_flat=_zper, per_flat_y=_zper * 12,
            others_y=_zper * max(0, _zd['stanovi'] - _zd['auta']) * 12, gap=_zgap,
            gap_note='ostatak i dalje plaćaju svi stanovi' if _zgap > 0 else 'paušal tačno pokriva trošak',
            payback=_zpay, owner=_zper + _zd['pausal'], owner_fair=_zd['kwh_auto'] * _zd['cena_kwh'])
render('kalkulator_zgrada.html', '/alati/racun-u-zgradi/', z=ZG, d=_zd, ex=_zex,
       z_json=json.dumps(ZG, ensure_ascii=False).replace('</', '<\\/'), modified_iso=ISO_TODAY,
       title='Ko koliko plaća punjenje u zgradi — kalkulator zajedničke struje | BlokVolt',
       description=f"Koliko stanari bez automobila plate tuđe punjenje kad punjač visi na zajedničkom brojilu: računica po stanu, mesečno i godišnje, i za koliko se vrati brojilo. Cene overenog merenja {ZG['meter_cost']['low']:,.0f}–{ZG['meter_cost']['high']:,.0f} RSD.".replace(',', '.'))
add_url('/alati/racun-u-zgradi/', '0.8')

# 5) home
render('home.html', '/', GUIDES=GUIDES_META, PODACI=PODACI, by_group=by_group, cities=cities, CITY_SLUGS=CITY_SLUGS,
       title='BlokVolt — sve o električnim automobilima u Srbiji: firme, cene, procedure',
       description=f'Nezavisni vodič za vlasnike električnih automobila u Srbiji: {len(published)} firmi za punjače sa javnim cenama, javni punjači i cene, besplatni punjači, 7 vodiča o punjenju u zgradi, subvencije 2026, statistika i propisi. Sve sa izvorom i datumom provere.')
add_url('/', '1.0')

# 6) sitemap, robots, redirects, 404
sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for u, p, lm in urls:
    sm.append(f'<url><loc>{u}</loc><lastmod>{lm}</lastmod><priority>{p}</priority></url>')
sm.append('</urlset>')
(DIST / 'sitemap.xml').write_text('\n'.join(sm), encoding='utf-8')
(DIST / 'robots.txt').write_text(f'User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n', encoding='utf-8')
(DIST / '_redirects').write_text('\n'.join([
    '/paketi-i-cene https://www.evolako.rs/paketi-i-cene 301',
    '/proveri-svoju-garazu https://www.evolako.rs/proveri-svoju-garazu 301',
    '/cesta-pitanja https://www.evolako.rs/cesta-pitanja 301',
    '/kontakt https://www.evolako.rs/kontakt 301',
    '/vodici /vodici/ 301',
    '/firme /firme/ 301',
    '/podaci /podaci/ 301',
    '/javno-punjenje /javno-punjenje/ 301',
    '/alati /alati/kalkulator-troskova/ 302',
    '/alati/ /alati/kalkulator-troskova/ 302',
    '/kalkulator /alati/kalkulator-troskova/ 301',
    'https://blokvolt.rs/* https://www.blokvolt.rs/:splat 301',
]) + '\n', encoding='utf-8')
(DIST / '_headers').write_text('/assets/*\n  Cache-Control: public, max-age=31536000, immutable\n/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n', encoding='utf-8')
render('article.html', '/404.html', crumb=None, meta={'title': 'Stranica nije pronađena', 'kicker': 'Greška 404', 'updated': ''}, body='<p class="bva-lead">Ta stranica ne postoji ili je premeštena.</p><p>Probajte <a href="/firme/">registar firmi</a>, <a href="/javno-punjenje/">javno punjenje</a>, <a href="/vodici/">vodiče</a> ili <a href="/podaci/">podatke</a>.</p>', title='404 | BlokVolt', description='', sources=[])
import hashlib as _hl
_ver = {}
for _a in ('site.css', 'agg.css', 'site.js', 'meganav.js', 'vendor/gsap.min.js'):
    _ver[_a] = _hl.sha1((DIST / 'assets' / _a).read_bytes()).hexdigest()[:10]
for _f in DIST.rglob('*.html'):
    _t = _f.read_text(encoding='utf-8')
    _n = _t
    for _a, _h in _ver.items():
        _n = _n.replace(f'"/assets/{_a}"', f'"/assets/{_a}?v={_h}"')
    if _n != _t:
        _f.write_text(_n, encoding='utf-8')
print('built', len(urls), 'urls;', len(published), 'firms;', len(operators), 'operators;', len(PODACI), 'data pages')
