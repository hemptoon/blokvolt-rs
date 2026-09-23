# -*- coding: utf-8 -*-
"""BlokVolt static site generator (blokvolt.rs). Python 3 + Jinja2 + Markdown + BeautifulSoup.
Usage: python3 build.py  -> dist/
"""
import json, os, re, shutil, glob, datetime, html, sys
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
import markdown
from bs4 import BeautifulSoup

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / 'scripts'))
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

def clip(text, n):
    """Shorten to at most n characters at a word boundary, with an ellipsis."""
    text = ' '.join(str(text).split())
    if len(text) <= n:
        return text
    head = text[:n + 1]
    end = head.rfind('. ')
    if end >= n // 2:                      # a whole sentence fits: stop there
        return head[:end + 1]
    cut = text[:n].rsplit(' ', 1)[0].rstrip(',;:–—- ')
    return cut + '…'

def sr_plural(n, one, few, many):
    """Serbian count agreement: 1 mreža / 2-4 mreže / 5+ mreža."""
    last, last2 = n % 10, n % 100
    if last == 1 and last2 != 11:
        return f'{n} {one}'
    if last in (2, 3, 4) and last2 not in (12, 13, 14):
        return f'{n} {few}'
    return f'{n} {many}'

env.filters['plural'] = sr_plural

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
CITY_CFG = json.load(open(ROOT / 'content' / 'data' / 'gradovi.json', encoding='utf-8'))['cities']
CITY_SLUGS = {c['name']: c['slug'] for c in CITY_CFG}

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
        t['class'] = 'bva-tbl agg-ev' if t.find('span', class_='evm') else 'bva-tbl'
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

def cities_of(firm):
    """Every configured city whose name or alias appears in the firm's seat (`city`)."""
    c = firm.get('city', '')
    return [cfg['name'] for cfg in CITY_CFG if any(a in c for a in cfg['aliases'])]

NATIONWIDE = ('cela srbija', 'citava srbija', 'čitava srbija', 'srbija i region', 'mreža instalatera')

_WORD = 'a-zà-ž0-9čćđšž'

def _word_in(term, text):
    """Whole-word match, so "nis" does not fire inside "nisu potvrđene"."""
    return re.search(f'(?<![{_WORD}])' + re.escape(term) + f'(?![{_WORD}])', text) is not None

def covers_city(entity, cfg):
    """True when the published `coverage` string reaches this city without a seat there:
    country-wide wording, the city itself, or one of the city's regions."""
    cov = (entity.get('coverage') or '').lower()
    if not cov:
        return False
    if cov.strip() in ('srbija', 'srbija.') or any(k in cov for k in NATIONWIDE):
        return True
    return any(_word_in(t, cov) for t in [cfg['name'].lower()] + cfg['regions'])

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
    f['city_list'] = cities_of(f)
    f['city_main'] = f['city_list'][0] if f['city_list'] else None
    f['city_slug'] = ' '.join(CITY_SLUGS[c] for c in f['city_list'])
    f['url'] = f"/firme/{f['slug']}/"
    f['group_label'] = GROUPS[f['group']][0]
    f['vclass'] = {k: verdict_class(v) for k, v in f.get('verdicts', {}).items()}
by_group = {g: [f for f in published if f['group'] == g] for g in GROUPS}

# Sub-hubs of the register by type of firm (/firme/<slug>/). Texts live in content/data/firme-tipovi.json;
# who belongs where is decided here, from the same verdicts and groups the register shows.
TYPE_RULES = {
    'ugradnja': lambda f: f['vclass'].get('ugradnja') in ('yes', 'ask'),   # says on its site that it installs
    'prodaja': lambda f: f['group'] in ('A', 'B', 'C'),                     # publishes a device price
    'distributer': lambda f: f.get('kind') == 'distributer',
    'solar': lambda f: f.get('kind') == 'solar',
    'elektricar': lambda f: f.get('kind') == 'elektricar',
}
TYPE_HUBS = []
for _h in json.load(open(ROOT / 'content' / 'data' / 'firme-tipovi.json', encoding='utf-8'))['hubs']:
    _m = [f for f in published if TYPE_RULES[_h['rule']](f)]
    TYPE_HUBS.append(dict(_h, url=f"/firme/{_h['slug']}/", firms=_m, n=len(_m)))
_hub_slugs = {h['slug'] for h in TYPE_HUBS}
assert not _hub_slugs & {f['slug'] for f in firms}, 'a firm slug collides with a /firme/ sub-hub'
for f in published:
    f['hubs'] = [h for h in TYPE_HUBS if any(x['slug'] == f['slug'] for x in h['firms'])]
# brand -> firms that name it on their own site (curated `brands` in content/firme/*.json)
BRAND_INDEX = {}
for f in published:
    for b in f.get('brands', []):
        BRAND_INDEX.setdefault(b, []).append(f)
BRAND_INDEX = [(b, sorted(lst, key=lambda f: f['name'].lower())) for b, lst in sorted(BRAND_INDEX.items(), key=lambda kv: kv[0].lower())]
cities = {}
for cfg in CITY_CFG:
    lst = [f for f in published if cfg['name'] in f['city_list']]
    if lst:
        cities[cfg['name']] = lst

CALC = json.load(open(ROOT / 'content' / 'data' / 'kalkulator.json', encoding='utf-8'))
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
CITY_LINKS = [(f"/gradovi/{c['slug']}/", c['name']) for c in CITY_CFG]
base_ctx = dict(SITE=SITE, TODAY=TODAY, ISO_TODAY=ISO_TODAY, FIRMS_CHECKED=FIRMS_CHECKED, CITY_LINKS=CITY_LINKS, SITE_META=SITE_META, NAV=NAV, n_firms=len(published), n_leads=sum(1 for f in firms if not f.get('publish') and not f.get('excluded_reason')), n_excluded=sum(1 for f in firms if not f.get('publish') and f.get('excluded_reason')), n_vodica=7, n_ops=len(operators),
                TYPE_NAV=[(h['url'], h['nav'], h['nav_desc'], h['n']) for h in TYPE_HUBS])

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
    # the legacy pages say "cene 20 firmi" (genitive) and "20 firmi · 14 izvora" (a count label):
    # 51 needs "cene 51 firme" but "51 firma · 14 izvora", so the two contexts are replaced separately
    _n = len(published)
    html_text = html_text.replace('>20 firmi · ', '>' + sr_plural(_n, 'firma', 'firme', 'firmi') + ' · ')
    html_text = html_text.replace('20 firmi', sr_plural(_n, 'firme', 'firme', 'firmi'))
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
    render('firma.html', f['url'], firm=f, GROUPS=GROUPS, CITY_SLUGS=CITY_SLUGS, title=f"{f['name']} — punjači za električne automobile: cene, ugradnja, uslovi | BlokVolt",
           description=f"{f['name']} ({f['city']}): šta nudi, javne cene, da li ugrađuje, brojilo, papiri za skupštinu, garancija. Provereno {f['verified']}. Isti podaci za sve firme.")
    add_url(f['url'], '0.6')
EXCLUDED = sorted([f for f in firms if not f.get('publish') and f.get('excluded_reason')], key=lambda f: f['name'].lower())
render('firme_index.html', '/firme/', GROUPS=GROUPS, TYPE_HUBS=TYPE_HUBS, by_group=by_group, firms=published, cities=cities, CITY_SLUGS=CITY_SLUGS, KINDS=KINDS, EXCLUDED=EXCLUDED,
       title=f"Firme za punjače u Srbiji — registar od {sr_plural(len(published), 'prodavca i instalatera', 'prodavca i instalatera', 'prodavaca i instalatera')}, iste kolone za sve | BlokVolt",
       description=f"Registar od {sr_plural(len(published), 'firme', 'firme', 'firmi')} koje prodaju ili ugrađuju kućne punjače za električne automobile u Srbiji: javne cene, ugradnja, MID brojilo, papiri za skupštinu, garancija. Provereno {FIRMS_CHECKED}.")
add_url('/firme/', '0.9')
_WB = json.load(open(ROOT / 'content' / 'data' / 'wallbox-modeli.json', encoding='utf-8'))
for h in TYPE_HUBS:
    _tctx = dict(n=h['n'], n_firms=len(published), checked=FIRMS_CHECKED, n_d=len(by_group['D']),
                 n_price=sum(1 for f in h['firms'] if f['group'] == 'A' or 'javna cena' in (f.get('verdicts', {}).get('ugradnja') or '').lower()),
                 wb_rows=len(_WB['rows']), wb_models=len({(r['brand'], r['model']) for r in _WB['rows']}), n_brands=len(BRAND_INDEX))
    _T = lambda txt: env.from_string(txt).render(**_tctx) if txt else ''
    _sections = [(g, GROUPS[g][0], [f for f in h['firms'] if f['group'] == g]) for g in GROUPS]
    render('firme_tip.html', h['url'], hub=h, TYPE_HUBS=TYPE_HUBS, sections=[x for x in _sections if x[2]],
           lead=_T(h['lead']), intro=_T(h.get('intro')), outro=_T(h.get('outro')), brand_intro=_T(h.get('brand_intro')),
           BRANDS=BRAND_INDEX if h['rule'] == 'distributer' else None, show_cities=h['rule'] in ('ugradnja', 'solar', 'elektricar'),
           title=_T(h['title']), description=_T(h['description']))
    add_url(h['url'], '0.7')
NT_HOURS = {h['region']: h['window'] for h in CALC['eps']['nt_hours']}
CITY_PAGES = []
for cfg in CITY_CFG:
    city, slug = cfg['name'], cfg['slug']
    local = cities.get(city, [])
    local_slugs = {f['slug'] for f in local}
    # installers based elsewhere whose published coverage reaches this city
    covering = [f for f in published if f['slug'] not in local_slugs and f['group'] in ('A', 'B', 'E')
                and covers_city(f, cfg)]
    shops = [f for f in published if f['slug'] not in local_slugs and f['group'] in ('C', 'D')
             and covers_city(f, cfg)]
    city_ops = [o for o in operators if covers_city(o, cfg) or city.lower() in (o.get('city') or '').lower()]
    n_all = len(local) + len(covering)
    render('grad.html', f'/gradovi/{slug}/', city=city, cfg=cfg, firms=local, covering=covering,
           shops=shops, city_ops=city_ops, n_all=n_all, nt=NT_HOURS.get(cfg['nt_region'], ''),
           GROUPS=GROUPS,
           title=f"Punjač za električni auto u {cfg['loc']} — {sr_plural(n_all, 'firma koja prodaje i ugrađuje', 'firme koje prodaju i ugrađuju', 'firmi koje prodaju i ugrađuju')} | BlokVolt",
           description=(f"Ko ugrađuje kućni punjač u {cfg['loc']}: "
                        + (f"{sr_plural(len(local), 'firma', 'firme', 'firmi')} sa sedištem u gradu i "
                           + (f"još jedna koja pokriva {cfg['acc']} sa strane" if len(covering) == 1
                              else f"još {len(covering)} koje pokrivaju {cfg['acc']} sa strane")
                           if local else
                           f"sedište u gradu nema nijedna, ali {sr_plural(len(covering), 'firma pokriva', 'firme pokrivaju', 'firmi pokriva')} grad sa cele teritorije Srbije")
                        + f" — javne cene, uslovi ugradnje, brojilo i garancija. Javno punjenje u gradu i sati niže tarife EPS-a. Provereno {FIRMS_CHECKED}."))
    add_url(f'/gradovi/{slug}/', '0.6')
    CITY_PAGES.append({'name': city, 'slug': slug, 'n': n_all, 'local': len(local)})

# 4) markdown pages (podaci, o-sajtu, metodologija, ispravka, izmene)
PODACI = []
CHECKS = []
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
    if meta.get('next_check'):
        _kick = meta.get('kicker', '').split('·')[-1].strip()
        _name = (_kick[:1].upper() + _kick[1:]) if _kick else meta['title'].split(' — ')[0].split(':')[0]
        CHECKS.append({'name': _name, 'path': path, 'updated': meta.get('updated', ''), 'next': meta['next_check']})
PODACI.sort(key=lambda m: (-float(m.get('priority', '0.5')), m.get('title', '')))
render('podaci_index.html', '/podaci/', pages=PODACI, title='Podaci: subvencije, statistika, tarife, propisi za električne automobile u Srbiji | BlokVolt',
       description='Proverene brojke i propisi za vlasnike električnih automobila u Srbiji — subvencije 2026, registracija i porezi, osiguranje, krediti, uvoz i carina, servisi, statistika, putarina i parking. Svaka stranica sa izvorom i datumom.')
add_url('/podaci/', '0.8')

# 4b) public charging (ring 2)
for o in operators:
    render('operator.html', o['url'], op=o, title=f"{o['name']} — javno punjenje: cene, naplata, uslovi | BlokVolt",
           description=f"{o['name']}: {clip(o['short'], 150)} Provereno {o['verified']}.")
    add_url(o['url'], '0.6')
# 4b') monthly archive of the price index (content/javno/indeks-arhiva/YYYY-MM.json, written by
# scripts/snapshot_index.py). Pages appear only from the second archived month on: one frozen page per
# past month plus /javno-punjenje/cene/ with what changed; the current month is the live table above.
MONTHS_SR = ['januar', 'februar', 'mart', 'april', 'maj', 'jun', 'jul', 'avgust', 'septembar', 'oktobar', 'novembar', 'decembar']
MONTHS_SR_GEN = ['januara', 'februara', 'marta', 'aprila', 'maja', 'juna', 'jula', 'avgusta', 'septembra', 'oktobra', 'novembra', 'decembra']
ARCHIVE = []
for _p in sorted((ROOT / 'content' / 'javno' / 'indeks-arhiva').glob('*.json')):
    _a = json.load(open(_p, encoding='utf-8'))
    _y, _m = _a['month'].split('-')
    _a['label'] = f'{MONTHS_SR[int(_m) - 1]} {_y}'
    _a['label_gen'] = f"{MONTHS_SR_GEN[int(_m) - 1]} {_y}"   # "iz septembra 2026"
    _a['url'] = f"/javno-punjenje/cene/{_a['month']}/"
    for row in _a['rows']:
        if not row.get('free'):
            row['kwh_html'] = kwh_html(row)
    ARCHIVE.append(_a)
PRICE_HISTORY = None
if len(ARCHIVE) >= 2:
    ARCHIVE[-1]['url'] = '/javno-punjenje/#cene'   # the latest month is the live index
    def _key(r):
        return (r['op'], r.get('where', ''), r.get('charger', ''))
    def _unit(r):
        if r.get('free'):
            return 'free'
        return next((k for k in ('rsd_min', 'rsd_hour', 'unit_rsd') if r.get(k)), None)
    def _val(r):
        v = r.get(_unit(r)) if _unit(r) not in (None, 'free') else None
        return float(v[0] if isinstance(v, list) else v) if v else None
    _shown = ARCHIVE[-3:]
    _keys = []
    for _a in _shown:
        for r in _a['rows']:
            if not r.get('rsd_total') and _key(r) not in _keys:   # receipts are one-off, not tariffs
                _keys.append(_key(r))
    _lines = []
    for k in _keys:
        cells = [next((r for r in _a['rows'] if not r.get('rsd_total') and _key(r) == k), None) for _a in _shown]
        last = cells[-1]
        prev = next((c for c in reversed(cells[:-1]) if c), None)
        if last is None:
            change, cls = 'nije u poslednjem snimku', 'no'
        elif prev is None:
            change, cls = 'novo u indeksu', 'ask'
        elif last.get('date') == prev.get('date'):
            change, cls = 'nije ponovo provereno', 'no'
        elif prev.get('free') and not last.get('free'):
            change, cls = 'više nije besplatno', 'yes'
        elif _unit(prev) != _unit(last):
            change, cls = 'promenjen način naplate', 'yes'
        elif _val(prev) and _val(last) is not None:
            pct = (_val(last) - _val(prev)) / _val(prev) * 100
            change, cls = ('bez promene', 'ask') if abs(pct) < 0.5 else (('+' if pct > 0 else '−') + sr_num(abs(pct)) + ' %', 'yes')
        else:
            change, cls = ('bez promene', 'ask') if last.get('label') == prev.get('label') else ('promenjen način naplate', 'yes')
        first = next(c for c in cells if c)
        _lines.append({'op': first['op'], 'op_name': first['op_name'], 'where': first.get('where', ''), 'charger': first.get('charger', ''),
                       'cells': cells, 'change': change, 'cls': cls})
    _lines.sort(key=lambda l: {'yes': 0, 'ask': 1, 'no': 2}[l['cls']])   # what changed first; stable within a class
    PRICE_HISTORY = {'shown': _shown, 'lines': _lines, 'n_changed': sum(1 for l in _lines if l['cls'] == 'yes')}
    for i, _a in enumerate(ARCHIVE[:-1]):
        render('javno_snimak.html', _a['url'], snap=_a, newer=ARCHIVE[i + 1], older=ARCHIVE[i - 1] if i else None,
               title=f"Cene javnog punjenja u Srbiji — {_a['label']} (arhiva) | BlokVolt",
               description=f"Arhivski snimak indeksa cena javnog punjenja za {_a['label']}: tarife iz aplikacija Charge&GO, Orion eMobility i Emobility Spectra, stvarni računi i besplatni punjači, sa računicom po kWh. Snimljeno {_a['captured']}.")
        add_url(_a['url'], '0.4', '-'.join(reversed(_a['captured'].split('.'))))
    render('javno_istorija.html', '/javno-punjenje/cene/', archive=ARCHIVE, hist=PRICE_HISTORY,
           title='Istorija cena javnog punjenja u Srbiji — promene po mesecima | BlokVolt',
           description=f"Kako su se menjale cene javnog punjenja u Srbiji od {ARCHIVE[0]['label_gen']}: mesečni snimci indeksa (Charge&GO, Orion eMobility, Emobility Spectra, besplatni punjači) i šta je poskupelo ili pojeftinilo.")
    add_url('/javno-punjenje/cene/', '0.6')

index_checked = price_index['updated']
render('javno_index.html', '/javno-punjenje/', ops=operators, ops_by_kind=ops_by_kind, KIND_GROUPS=KIND_GROUPS, index=price_index, hist=PRICE_HISTORY,
       title='Javni punjači u Srbiji — mreže, cene po minutu i po kWh, besplatni punjači | BlokVolt',
       description=f'Ko vodi javne punjače u Srbiji (Charge&GO, Orion eMobility, JP Putevi Srbije, Tesla, OMV…), poslednje zabeležene cene sa računicom po kWh, 36 besplatnih državnih punjača na autoputevima i propisi. Provereno {index_checked}.')
add_url('/javno-punjenje/', '0.9')


# 4c) cost calculator (tools)
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
    _zpay = 'mesec dana' if _m <= 1 else (sr_plural(_m, 'mesec', 'meseca', 'meseci') if _m < 24 else f'{_m / 12:.1f}'.replace('.', ',') + ' godine')
else:
    _zpay = 'paušal već pokriva trošak'
_zex = dict(real=_zreal, real_y=_zreal * 12, per_flat=_zper, per_flat_y=_zper * 12,
            others_y=_zper * max(0, _zd['stanovi'] - _zd['auta']) * 12, gap=_zgap,
            gap_note='ostatak i dalje plaćaju svi stanovi' if _zgap > 0 else 'paušal tačno pokriva trošak',
            payback=_zpay, owner=_zper + _zd['pausal'], owner_fair=_zd['kwh_auto'] * _zd['cena_kwh'])
render('kalkulator_zgrada.html', '/alati/racun-u-zgradi/', z=ZG, d=_zd, ex=_zex,
       z_json=json.dumps(ZG, ensure_ascii=False).replace('</', '<\\/'), modified_iso=ISO_TODAY,
       title='Ko koliko plaća punjenje u zgradi — kalkulator zajedničke struje | BlokVolt',
       description=f"Koliko stanari bez automobila plate tuđe punjenje kad punjač visi na zajedničkom brojilu: računica po stanu, mesečno i godišnje, i za koliko se vrati brojilo. Cene overenog merenja {sr_num(ZG['meter_cost']['low'])}–{sr_num(ZG['meter_cost']['high'])} RSD.")
add_url('/alati/racun-u-zgradi/', '0.8')

CHECKS.append({'name': f'Registar firmi ({len(published)})', 'path': '/firme/', 'updated': FIRMS_CHECKED, 'next': 'kvartalno'})
CHECKS.append({'name': 'Indeks cena javnog punjenja', 'path': '/javno-punjenje/#cene', 'updated': price_index['updated'], 'next': price_index.get('next_check', '')})
def _d(x):
    p = (x.get('updated') or '').split('.')
    return (p[2], p[1], p[0]) if len(p) == 3 else ('0', '0', '0')
CHECKS.sort(key=_d, reverse=True)

# 4e) open data — CSV exports of everything the site publishes as a table
import open_data
EV_DATA = json.load(open(ROOT / 'content' / 'data' / 'ev-modeli.json', encoding='utf-8'))
WALLBOX = json.load(open(ROOT / 'content' / 'data' / 'wallbox-modeli.json', encoding='utf-8'))
DATASETS = open_data.export_all(DIST, SITE, published, operators, price_index, EV_DATA, WALLBOX, FIRMS_CHECKED)
DL_META = {
    'blokvolt-firme.csv': ('Registar firmi', f'Sve firme iz registra ({len(published)}) koje u Srbiji prodaju ili ugrađuju kućni punjač: sedište, pokrivenost, brendovi koje nude, javna cena, da li nude ugradnju, brojilo, papire za skupštinu, uslugu i garanciju, sajt i datum provere.', f'kvartalno (poslednja revizija {FIRMS_CHECKED})'),
    'blokvolt-cene-elektricnih-automobila.csv': ('Cene električnih automobila', 'Svaki model sa cenom koju uvoznik javno objavljuje: cena od, cena posle subvencije, redovna i akcijska cena, da li je subvencija već uračunata, link na cenovnik.', f'mesečno (poslednja provera {EV_DATA["checked"]})'),
    'blokvolt-wallbox-modeli.csv': ('Wallbox modeli i cene', 'Javno objavljene cene samih uređaja kod prodavaca u Srbiji, po modelu i snazi, sa PDV-statusom i linkom na proizvod.', f'kvartalno (poslednja provera {WALLBOX["checked"]})'),
    'blokvolt-javno-punjenje-cene.csv': ('Indeks cena javnog punjenja', 'Zabeležene tarife i računi sa javnih punjača: cena po minutu, po satu ili po „jedinici“, stvarni računi sa cenom po kWh, snaga punjača, datum i izvor.', f'mesečno (poslednji snimak {index_checked})'),
    'blokvolt-mreze-javnog-punjenja.csv': ('Mreže javnog punjenja', 'Operatori, aplikacije i domaćini: pokrivenost, veličina mreže, način plaćanja, kartica, roming i podrška.', f'mesečno (poslednja provera {index_checked})'),
}
for d in DATASETS:
    d['title'], d['desc'], d['cadence'] = DL_META[d['name']]
    d['kb'] = round(d['bytes'] / 1024, 1)
render('preuzimanje.html', '/preuzimanje/', datasets=DATASETS,
       title='Podaci za preuzimanje — CSV tabele o električnim automobilima u Srbiji | BlokVolt',
       description=f'Svi podaci sa BlokVolta u CSV formatu, besplatno i uz slobodnu licencu: registar od {sr_plural(len(published), "firme", "firme", "firmi")}, cene električnih automobila kod uvoznika, cene wallbox uređaja, indeks cena javnog punjenja i mreže. Sa izvorom i datumom provere uz svaki red.')
add_url('/preuzimanje/', '0.6')

# 5) home
render('home.html', '/', GUIDES=GUIDES_META, PODACI=PODACI, CHECKS=CHECKS, by_group=by_group, cities=cities, CITY_SLUGS=CITY_SLUGS,
       title='BlokVolt — sve o električnim automobilima u Srbiji: firme, cene, procedure',
       description=f'Nezavisni vodič za vlasnike električnih automobila u Srbiji: {sr_plural(len(published), "firma", "firme", "firmi")} za punjače sa javnim cenama, javni punjači i cene, besplatni punjači, 7 vodiča o punjenju u zgradi, subvencije 2026, statistika i propisi. Sve sa izvorom i datumom provere.')
add_url('/', '1.0')

# 5b) search page + index
render('pretraga.html', '/pretraga/', title='Pretraga sajta | BlokVolt',
       description='Pretraga svih stranica BlokVolta: firme, cene punjača, javno punjenje, podaci, propisi i vodiči.')
add_url('/pretraga/', '0.3')

# 6) robots, redirects, headers, 404
(DIST / 'robots.txt').write_text(f'User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n', encoding='utf-8')
_dir_redirects = ['/vodici', '/firme', '/podaci', '/javno-punjenje']
(DIST / '_redirects').write_text('\n'.join([
    '/paketi-i-cene https://www.evolako.rs/paketi-i-cene 301',
    '/proveri-svoju-garazu https://www.evolako.rs/proveri-svoju-garazu 301',
    '/cesta-pitanja https://www.evolako.rs/cesta-pitanja 301',
    '/kontakt https://www.evolako.rs/kontakt 301',
] + [f'{pre}{d} {pre}{d}/ 301' for pre in ('', '/en', '/ru') for d in _dir_redirects] + [
    '/en /en/ 301',
    '/ru /ru/ 301',
    '/alati /alati/kalkulator-troskova/ 302',
    '/alati/ /alati/kalkulator-troskova/ 302',
    '/en/alati /en/alati/kalkulator-troskova/ 302',
    '/en/alati/ /en/alati/kalkulator-troskova/ 302',
    '/ru/alati /ru/alati/kalkulator-troskova/ 302',
    '/ru/alati/ /ru/alati/kalkulator-troskova/ 302',
    '/kalkulator /alati/kalkulator-troskova/ 301',
    'https://blokvolt.rs/* https://www.blokvolt.rs/:splat 301',
]) + '\n', encoding='utf-8')
(DIST / '_headers').write_text('/assets/*\n  Cache-Control: public, max-age=31536000, immutable\n/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n', encoding='utf-8')
render('article.html', '/404.html', crumb=None, meta={'title': 'Stranica nije pronađena', 'kicker': 'Greška 404', 'updated': ''}, body='<p class="bva-lead">Ta stranica ne postoji ili je premeštena.</p><p>Probajte <a href="/firme/">registar firmi</a>, <a href="/javno-punjenje/">javno punjenje</a>, <a href="/vodici/">vodiče</a> ili <a href="/podaci/">podatke</a>.</p><p lang="en" translate="no">Page not found — try the <a href="/en/firme/">company register</a> or the <a href="/en/">English home page</a>.</p><p lang="ru" translate="no">Страница не найдена — попробуйте <a href="/ru/firme/">реестр компаний</a> или <a href="/ru/">главную страницу на русском</a>.</p>', title='404 | BlokVolt', description='', sources=[])
import hashlib as _hl
import i18n as _i18n
_ver = {}


def build_search(prefix=''):
    """Search index for one language (built from the generated pages, so legacy pages are in it too)."""
    idx = []
    base = DIST / prefix.strip('/') if prefix else DIST
    for f in sorted(base.rglob('*.html')):
        rel = '/' + str(f.relative_to(DIST)).replace('\\', '/')
        if not prefix and rel.startswith(('/en/', '/ru/')):
            continue
        if rel in (f'{prefix}/404.html', f'{prefix}/pretraga/index.html'):
            continue
        url = rel[:-len('index.html')] if rel.endswith('/index.html') else rel
        soup = BeautifulSoup(f.read_text(encoding='utf-8'), 'html.parser')
        t = (soup.title.string or '').split(' | ')[0].strip() if soup.title else ''
        d = (soup.find('meta', attrs={'name': 'description'}) or {}).get('content', '')
        kick = soup.find(class_='v3-kick')
        h = ' · '.join(x.get_text(' ', strip=True) for x in soup.find_all(['h2', 'h3'])[:14])
        main = soup.find('div', class_='bva') or soup.find('main') or soup
        for junk in main.find_all(['script', 'style', 'nav']):
            junk.decompose()
        body = re.sub(r'\s+', ' ', main.get_text(' ', strip=True))
        idx.append({'u': url, 't': t, 'd': clip(d, 220), 's': kick.get_text(' ', strip=True).split('·')[0].strip() if kick else '',
                    'h': h[:400], 'b': body[:1200]})
    name = 'search.json' if not prefix else f'search-{prefix.strip("/")}.json'
    (DIST / 'assets' / name).write_text(json.dumps(idx, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    return len(idx), (DIST / 'assets' / name).stat().st_size // 1024


_n, _kb = build_search()
print(f'search index: {_n} pages, {_kb} KB')

# 7) English and Russian versions (scripts/i18n.py, translation memory in content/i18n/)
I18N = _i18n.render_all(DIST)
for _l in _i18n.LANGS:
    _st = I18N.stats[_l]
    _n, _kb = build_search('/' + _l)
    print(f'i18n {_l}: {_st["hit"]} segments translated, {_st["miss"]} left in Serbian ({len(_st["missing"])} distinct); search {_n} pages, {_kb} KB')

# 8) sitemap with language alternates
sm = ['<?xml version="1.0" encoding="UTF-8"?>',
      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
for u, p, lm in urls:
    path = u[len(SITE):]
    langs = ['sr'] + (list(_i18n.LANGS) if I18N.is_page(path) else [])
    alts = ''
    if len(langs) > 1:
        alts = ''.join(f'<xhtml:link rel="alternate" hreflang="{_i18n.HREFLANG[l]}" href="{SITE}{_i18n.lang_url(path, l)}"/>' for l in langs)
        alts += f'<xhtml:link rel="alternate" hreflang="x-default" href="{u}"/>'
    for l in langs:
        sm.append(f'<url><loc>{SITE}{_i18n.lang_url(path, l)}</loc><lastmod>{lm}</lastmod><priority>{p}</priority>{alts}</url>')
sm.append('</urlset>')
(DIST / 'sitemap.xml').write_text('\n'.join(sm), encoding='utf-8')

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
