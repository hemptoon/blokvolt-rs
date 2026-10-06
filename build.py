# -*- coding: utf-8 -*-
"""BlokVolt static site generator (www.blokvolt.rs), portal design of September 2026.

Python 3 + Jinja2 + Markdown + BeautifulSoup.  Usage: python3 build.py  ->  dist/

  content/firme/*.json       companies (register), content/operateri/*.json  public-charging networks
  content/podaci, javno, vodici/*.md   articles (front matter + Markdown; style: docs/CONTENT_STYLE.md)
  content/mapa/*.json        open charger snapshots for /mapa/ (scripts/map_data.py)
  content/data/*.json        calculators, cities, hubs, logos, site dates
  templates/*.html           Jinja templates (base.html + _header/_footer/_macros/_icons)
  static/                    copied as is (assets/bv.css, bv.js, map.js, vendor/, logos/, fonts/)

After the Serbian pages exist, scripts/i18n.py writes /en/ and /ru/ from the translation memory."""
import json, os, re, shutil, glob, html, sys, hashlib, unicodedata, datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
import markdown
from bs4 import BeautifulSoup

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / 'scripts'))
import map_data  # noqa: E402

DIST = ROOT / 'dist'
SITE = 'https://www.blokvolt.rs'
# Dates live in content/data/site.json: 'updated' = last content update (footer, sitemap lastmod),
# 'firms_checked' = last full revision of the firm register.
SITE_META = json.load(open(ROOT / 'content' / 'data' / 'site.json', encoding='utf-8'))
# the Android app (docs/RUNBOOK.md 3.20): version, APK file name, size, SHA-256 and the signing certificate
_APP_F = ROOT / 'content' / 'data' / 'app.json'
APP = json.load(open(_APP_F, encoding='utf-8')) if _APP_F.exists() else {}
TODAY = SITE_META['updated']
ISO_TODAY = '-'.join(reversed(TODAY.split('.')))
FIRMS_CHECKED = SITE_META['firms_checked']
EVOLAKO = 'https://www.evolako.rs/'

# ---------------------------------------------------------------- advertising (docs/RUNBOOK.md 3.26)
# content/data/oglasavanje.json: the media kit (/za-firme/oglasavanje/: prices, rubrics, last month's visits) and the
# booked ads. One ad per page, at the end of the text, labelled "Oglas"; only on the pages of its rubric, only from
# 'od' to 'do' (today in Belgrade; bv.js hides it again once 'do' has passed, even without a new build), never on the
# paths in 'ne_na'. Never on the map, the register, the prices, the home-charging guides and calculators, and never in
# the installed apps (bv.css, display-mode). Links carry rel="sponsored" and utm_source=blokvolt.
OGL = json.load(open(ROOT / 'content' / 'data' / 'oglasavanje.json', encoding='utf-8'))
try:
    from zoneinfo import ZoneInfo
    NOW_ISO = datetime.datetime.now(ZoneInfo('Europe/Belgrade')).date().isoformat()
except Exception:                                        # no tz data: UTC is at most a couple of hours off
    NOW_ISO = datetime.datetime.utcnow().date().isoformat()


def rubrika_of(path):
    for key, r in OGL['rubrike'].items():
        if path in r.get('putanje', []) or (r.get('prefiks') and path.startswith(r['prefiks'])):
            return key
    return None


def oglas_za(path, tekst=''):
    """The ad for a page, or None. `tekst`: the page's own words (news title, lead and body); an ad whose
    'ne_uz' words appear there is not shown, so a network's ad never stands next to news about that network."""
    rk = rubrika_of(path)
    if not rk:
        return None
    plain = html.unescape(re.sub(r'<[^>]+>', ' ', tekst)).casefold()
    for o in OGL.get('oglasi', []):
        if o.get('rubrika') != rk or path in o.get('ne_na', []) or not (o['od'] <= NOW_ISO <= o['do']):
            continue
        if any(w.casefold() in plain for w in o.get('ne_uz', []) if w.strip()):
            continue
        href = o['url'] + ('&' if '?' in o['url'] else '?') + 'utm_source=blokvolt&utm_medium=oglas&utm_campaign=' + o['id']
        base = {'naslov': o['naslov'], 'tekst': o['tekst'], 'alt': o.get('alt') or o['naslov']}
        if any(o.get(l) for l in ('en', 'ru')):     # translated ad: one block per language (strip_lang_only keeps one)
            variants = [dict(base, lang='sr', html_lang='sr-Latn')]
            for l in ('en', 'ru'):
                t = o.get(l) or {}
                own = bool(t.get('naslov'))             # no own headline = the Serbian text on that version too
                variants.append({'naslov': t.get('naslov') or base['naslov'], 'tekst': t.get('tekst') or base['tekst'],
                                 'alt': t.get('alt') or (t['naslov'] if own else base['alt']),
                                 'lang': l, 'html_lang': l if own else 'sr-Latn'})
        else:                                       # Serbian text on every language version
            variants = [dict(base, lang=None, html_lang='sr-Latn')]
        return dict(o, href=href, variants=variants)
    return None


env = Environment(loader=FileSystemLoader(str(ROOT / 'templates')), autoescape=select_autoescape(['html']), trim_blocks=True, lstrip_blocks=True)


# ---------------------------------------------------------------- helpers
def sr_num(x, d=0):
    """Serbian number format: 1.234,56"""
    s_ = f'{abs(float(x)):,.{d}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    return ('−' if float(x) < 0 and round(abs(float(x)), d) != 0 else '') + s_


def sr_plural(n, one, few, many):
    """Serbian count agreement: 1 mreža / 2-4 mreže / 5+ mreža."""
    last, last2 = n % 10, n % 100
    if last == 1 and last2 != 11:
        return f'{n} {one}'
    if last in (2, 3, 4) and last2 not in (12, 13, 14):
        return f'{n} {few}'
    return f'{n} {many}'


def mono(name):
    """Two-letter monogram for an entity without a logo file."""
    words = [w for w in re.findall(r'[^\W_]+', name or '') if w.lower() not in ('d', 'o', 'doo', 'jp', 'jkp')]
    if not words:
        return '?'
    if len(words) == 1:
        return words[0][:2].upper()
    return (words[0][0] + words[1][0]).upper()


def clip(text, n):
    """Shorten to at most n characters at a word boundary, with an ellipsis."""
    text = ' '.join(str(text).split())
    if len(text) <= n:
        return text
    head = text[:n + 1]
    end = head.rfind('. ')
    if end >= n // 2:
        return head[:end + 1]
    cut = text[:n].rsplit(' ', 1)[0].rstrip(',;:–—- ')
    return cut + '…'


def iso(d):
    """'22.09.2026' -> '2026-09-22' (anything else -> today)."""
    p = (d or '').split('.')
    return f'{p[2]}-{p[1]}-{p[0]}' if len(p) == 3 and all(x.isdigit() for x in p) else ISO_TODAY


def fold(s):
    s = (s or '').lower().replace('đ', 'd')
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


def fmt_rsd(v):
    return sr_num(v, 2) if abs(v - round(v)) > 0.004 else sr_num(v, 0)


def clean_src(label):
    """Source labels are shown to readers: no in-house wording ("snimak ekrana redakcije")."""
    t = label or ''
    t = re.sub(r'\s*[—-]\s*snimak ekrana redakcije', '', t)
    t = re.sub(r'\s*\((?:punjenje|snimak|snimci ekrana|račun) redakcije\)', '', t)
    t = re.sub(r'\s*\(snimci ekrana redakcije\)', '', t)
    t = t.replace('računi redakcije', 'računi').replace('račun redakcije', 'račun').replace(' redakcije', '')
    return t.strip()


env.filters['sr'] = sr_num
env.filters['plural'] = sr_plural
env.filters['pword'] = lambda n, one, few, many: sr_plural(n, one, few, many).split(' ', 1)[1]   # the noun only
env.filters['mono'] = mono
env.filters['iso'] = iso


def read_json_dir(d):
    return [json.load(open(f, encoding='utf-8')) for f in sorted(glob.glob(str(ROOT / 'content' / d / '*.json')))]


def front_matter(path):
    txt = open(path, encoding='utf-8').read()
    m = re.match(r'^---\n(.*?)\n---\n(.*)$', txt, re.S)
    meta, body = {}, txt
    if m:
        for line in m.group(1).split('\n'):
            if ':' in line:
                k, v = line.split(':', 1)
                meta[k.strip()] = v.strip().strip('"')
        body = m.group(2)
    return meta, body


# ---------------------------------------------------------------- images and videos
# static/assets/img/<name>-<width>.webp (illustrations, see docs/RUNBOOK.md §3.13); content/data/video.json (YouTube)
from markupsafe import Markup, escape  # noqa: E402
from PIL import Image as _PIL  # noqa: E402
IMG_DIR = ROOT / 'static' / 'assets' / 'img'
IMGS, IMG_SIZE = {}, {}
for _p in sorted(IMG_DIR.glob('*.webp')):
    _m = re.match(r'(.+)-(\d+)\.webp$', _p.name)
    if _m:
        IMGS.setdefault(_m.group(1), []).append(int(_m.group(2)))
for _n, _ws in IMGS.items():
    _ws.sort()
    with _PIL.open(IMG_DIR / f'{_n}-{_ws[-1]}.webp') as _im:
        IMG_SIZE[_n] = _im.size
VIDEOS = json.load(open(ROOT / 'content' / 'data' / 'video.json', encoding='utf-8'))
# free-licence photos (news): author, licence, caption, alt; tag pools for news without their own photo (RUNBOOK 3.19)
FOTO = json.load(open(ROOT / 'content' / 'data' / 'foto.json', encoding='utf-8'))
for _n, _f in FOTO['photos'].items():
    assert _n in IMGS and (ROOT / 'static' / 'assets' / 'og' / 'foto' / f'{_n}.jpg').exists(), f'photo {_n}: run scripts/news_photo.py'
    assert _f['src'] in ('Unsplash', 'Wikimedia Commons') and _f.get('au') and _f.get('page') and _f.get('cap') and _f.get('alt'), f'photo {_n}: incomplete credit'
for _t, _ns in FOTO['pools'].items():
    assert _ns and all(x in FOTO['photos'] for x in _ns), f'photo pool {_t}: unknown photo'


def photo_caption(name):
    """'What the photo shows. Foto: Author / Unsplash' or '…, CC BY-SA 4.0, Wikimedia Commons, isečeno' (with links)."""
    f = FOTO['photos'][name]
    au = f'<a href="{escape(f["page"])}" rel="nofollow noopener" translate="no">{escape(f["au"])}</a>'
    if f['src'] == 'Unsplash':
        credit = f'{au} / <span translate="no">Unsplash</span>'
    else:
        lic = f'<a href="{escape(f["licurl"])}" rel="nofollow noopener" translate="no">{escape(f["lic"])}</a>'
        credit = f'{au}, {lic}, <span translate="no">Wikimedia Commons</span>' + (', isečeno' if f['lic'].startswith('CC BY') else '')
    return Markup(f'{escape(f["cap"].rstrip("."))}. Foto: {credit}')


def fig_html(name, alt, caption=None, sizes='(max-width: 820px) 100vw, 760px', cls='', eager=False):
    """A responsive <figure>; the caption defaults to the photo credit (foto.json); illustrations get none."""
    ws = IMGS[name]
    w, h = IMG_SIZE[name]
    srcset = ', '.join(f'/assets/img/{name}-{x}.webp {x}w' for x in ws)
    mid = next((x for x in ws if x >= 800), ws[-1])
    if caption is None:
        cap = photo_caption(name) if name in FOTO['photos'] else None   # illustrations: no caption (26.09.2026)
    else:
        cap = caption
    if not alt and name in FOTO['photos']:
        alt = FOTO['photos'][name]['alt']
    img = (f'<img src="/assets/img/{name}-{mid}.webp" srcset="{srcset}" sizes="{sizes}" width="{w}" height="{h}" alt="{escape(alt)}" '
           + ('fetchpriority="high" ' if eager else 'loading="lazy" ') + 'decoding="async">')
    return Markup(f'<figure class="fig {cls}">{img}' + (f'<figcaption>{escape(cap)}</figcaption>' if cap else '') + '</figure>')


def yt_html(vid, cls=''):
    """YouTube video behind a click: nothing loads from YouTube until the reader presses play (bv.js)."""
    v = VIDEOS[vid]
    t, ch = escape(v['title']), escape(v['channel'])
    bg = f'<img class="yt-bg" src="/assets/img/{v["poster"]}-800.webp" alt="" loading="lazy" decoding="async">' if v.get('poster') in IMGS else ''
    return Markup(f'<figure class="yt {cls}"><button class="yt-play" type="button" data-yt="{vid}">{bg}'
                  f'<span class="yt-in"><span class="yt-ic" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M8 5.5v13l11-6.5z" fill="currentColor"/></svg></span>'
                  f'<span class="sr-only">Pusti video:</span><span class="yt-t" translate="no">{t}</span><span class="yt-c">{ch} · YouTube</span></span></button>'
                  f'<figcaption>Video: {ch}, YouTube. Učitava se tek kad pritisnete.</figcaption></figure>')


def photo_credits_html():
    """[[fotografije]]: every news photo with its caption and credit (the same HTML as under the photo, so the
    EN/RU translation of a caption exists before a news item uses that photo)."""
    items = ''.join(f'<li><img src="/assets/img/{n}-480.webp" width="96" height="54" alt="{escape(f["alt"])}" loading="lazy" decoding="async">'
                    f'<span>{photo_caption(n)}</span></li>' for n, f in FOTO['photos'].items())
    return ('<details class="src foto-src"><summary>Fotografije na sajtu: autori i licence</summary>'
            f'<ul class="foto-list">{items}</ul></details>')


env.globals['fig'] = fig_html
env.globals['yt'] = yt_html


def md_to_html(text):
    h = markdown.markdown(text, extensions=['tables', 'attr_list', 'md_in_html', 'sane_lists'])
    # [[yt:ID]] and [[fig:name|alt]] on their own line
    h = re.sub(r'<p>\[\[yt:([\w-]+)\]\]</p>', lambda m: str(yt_html(m.group(1))), h)
    h = re.sub(r'<p>\[\[fig:([\w-]+)\|([^\]]+)\]\]</p>', lambda m: str(fig_html(m.group(1), html.unescape(m.group(2)))), h)
    h = h.replace('<p>[[fotografije]]</p>', photo_credits_html())
    s = BeautifulSoup(h, 'html.parser')
    for t in s.find_all('table'):
        heads = [th.get_text(' ', strip=True) for th in t.find_all('th')]
        for tr in t.find_all('tr'):
            for i, td in enumerate(tr.find_all('td')):
                if i < len(heads) and not td.get('data-label'):
                    td['data-label'] = heads[i]
        if t.parent is not None and 'tw' in (t.parent.get('class') or []):
            continue
        t.wrap(s.new_tag('div', attrs={'class': 'tw stack'}))
    for a in s.find_all('a', href=True):
        if a['href'].startswith('http') and 'blokvolt' not in a['href'] and not a.get('rel'):
            a['rel'] = 'noopener'
    return str(s)


def write(path, content):
    p = DIST / path.lstrip('/')
    if path.endswith('/') or not os.path.splitext(path)[1]:
        p = p / 'index.html'
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding='utf-8')


def canon_of(path):
    if path == '/404.html':
        return '/404'
    return path[:-5] if path.endswith('.html') else path


def sources_of(meta):
    """Front-matter 'sources: label :: url | label :: url' -> [{label, url}]."""
    out = []
    for s in (meta.get('sources') or '').split(' | '):
        if not s.strip():
            continue
        label, _, url = s.partition(' :: ')
        out.append({'label': clean_src(label.strip()), 'url': url.strip()})
    return out


# ---------------------------------------------------------------- logos
# content/data/logos.json: {"<slug>": {"file": "stasanet.svg", "dark": false, "source": "https://…"}}
# Files live in static/assets/logos/. A logo is shown only when its file exists.
LOGO_DIR = ROOT / 'static' / 'assets' / 'logos'
_logos_path = ROOT / 'content' / 'data' / 'logos.json'
LOGO_META = json.load(open(_logos_path, encoding='utf-8')).get('logos', {}) if _logos_path.exists() else {}
LOGOS, LOGO_DARK = {}, set()
for _slug, _l in LOGO_META.items():
    _f = LOGO_DIR / _l.get('file', '')
    if _l.get('file') and _f.is_file():
        LOGOS[_slug] = f"/assets/logos/{_l['file']}?v={hashlib.sha1(_f.read_bytes()).hexdigest()[:8]}"
        if _l.get('dark'):
            LOGO_DARK.add(_slug)


def attach_logo(e, key=None):
    """Networks use the key 'op-<slug>' and fall back to the firm with the same slug."""
    keys = [key, e['slug']] if key else [e['slug']]
    k = next((x for x in keys if x in LOGOS), None)
    e['logo'] = LOGOS.get(k, '') if k else ''
    e['logo_dark'] = k in LOGO_DARK
    e['logo_abs'] = (SITE + e['logo'].split('?')[0]) if e['logo'] else ''


# ---------------------------------------------------------------- firms
GROUPS = {
    'A': 'Punjač sa ugradnjom, javna cena',
    'B': 'Uređaj sa cenom, ugradnja na upit',
    'C': 'Samo uređaj',
    'D': 'Cena na upit',
    'E': 'Električari: samo ugradnja',
}
# Lists show A and B as one section (since 06.10.2026): the firm marked "Izdvojeno" (is_us) first, the rest A–Z.
# The group itself stays in the data (price note "sa ugradnjom", city coverage, price page filters).
SECTIONS = {'A': 'AB', 'B': 'AB', 'C': 'C', 'D': 'D', 'E': 'E'}
SECTION_LABELS = {'AB': 'Javna cena, ugradnja uključena ili na upit', 'C': GROUPS['C'], 'D': GROUPS['D'], 'E': GROUPS['E']}
SECTION_ORDER = ['AB', 'C', 'D', 'E']


def list_key(f):
    """Order of firms in every list: „Izdvojeno“ first, then by section, then A–Z."""
    return (0 if f.get('is_us') else 1, SECTION_ORDER.index(SECTIONS[f['group']]), f['name'].lower())
KINDS = {
    'instalater': 'Prodaja i ugradnja', 'prodavnica': 'Prodavnica', 'distributer': 'Distributer',
    'solar': 'Solarni integrator', 'elektricar': 'Električar', 'operator': 'Mreža punjača', 'trag': 'Na proveri',
}
CITY_CFG = json.load(open(ROOT / 'content' / 'data' / 'gradovi.json', encoding='utf-8'))['cities']
CITY_SLUGS = {c['name']: c['slug'] for c in CITY_CFG}
TOWN_XY = {t[0]: (t[1], t[2]) for t in map_data.TOWNS}
NATIONWIDE = ('cela srbija', 'citava srbija', 'čitava srbija', 'srbija i region', 'mreža instalatera')
_WORD = 'a-zà-ž0-9čćđšž'


def _word_in(term, text):
    return re.search(f'(?<![{_WORD}])' + re.escape(term) + f'(?![{_WORD}])', text) is not None


def cities_of(firm):
    c = firm.get('city', '')
    return [cfg['name'] for cfg in CITY_CFG if any(a in c for a in cfg['aliases'])]


def covers_city(entity, cfg):
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
    if v.startswith('šablon'):
        # only templates (the client fills in and submits the papers): partial, so no "Papiri za skupštinu" badge
        return 'ask'
    return 'yes'


def split_cell(h):
    """Register cell HTML -> {'head': the bold answer, 'rest': details and quotes, one line}."""
    s = BeautifulSoup(h or '', 'html.parser')
    b = s.find('b')
    head = b.decode_contents().strip() if b else ''
    if b:
        b.extract()
    for br in s.find_all('br'):
        br.replace_with(' · ')
    for sm in s.find_all('small'):
        sm.insert_before(' · ')
        sm.unwrap()
    rest = re.sub(r'(\s*·\s*){2,}', ' · ', str(s)).strip()
    rest = re.sub(r'^(·\s*)+|(\s*·)+$', '', rest).strip()
    return {'head': head, 'rest': rest}


def firm_price(f):
    h = (f.get('price_headline') or '').strip()
    if not h or re.search(r'(?i)nije objavljen|na upit|cena nije', h):
        return None, None
    model, sep, val = h.rpartition(':')
    if not sep:
        model, val = '', h
    model, val = model.strip(), val.strip()
    if f['group'] == 'A':
        note = f'{model}, sa ugradnjom' if model else 'sa ugradnjom'
    else:
        note = model
    return val, clip(note, 34) if note else ''


POS = [('ugradnja', 'Ugradnja'), ('brojilo', 'MID brojilo'), ('skupstina', 'Papiri za skupštinu'), ('usluga', 'Mesečna usluga')]
TYPE_RULES = {
    'ugradnja': lambda f: f['vclass'].get('ugradnja') in ('yes', 'ask'),
    'prodaja': lambda f: f['group'] in ('A', 'B', 'C'),
    'distributer': lambda f: f.get('kind') == 'distributer',
    'solar': lambda f: f.get('kind') == 'solar',
    'elektricar': lambda f: f.get('kind') == 'elektricar',
}

firms = read_json_dir('firme')
published = sorted([f for f in firms if f.get('publish')], key=list_key)
for f in published:
    f['kind_label'] = KINDS.get(f.get('kind', ''), '')
    f.setdefault('contact', {})
    f['city_list'] = cities_of(f)
    f['url'] = f"/firme/{f['slug']}/"
    f['group_label'] = GROUPS[f['group']]
    f['vclass'] = {k: verdict_class(v) for k, v in f.get('verdicts', {}).items()}
    f['cell'] = {k: split_cell(v) for k, v in f.get('cells', {}).items()}
    for k in ('cena', 'ugradnja', 'brojilo', 'skupstina', 'usluga'):
        f['cell'].setdefault(k, {'head': '', 'rest': ''})
    f['price_val'], f['price_note'] = firm_price(f)
    pos = []
    for k, label in POS:
        if f['vclass'].get(k) == 'yes':
            if k == 'usluga' and 'garanc' in (f['verdicts'].get(k) or '').lower():
                label = 'Produžena garancija'
            pos.append(label)
    f['pos'] = pos
    f['tips'] = ' '.join(k for k, rule in TYPE_RULES.items() if rule(f))
    f['src_items'] = [{'url': s['url'], 'label': clean_src(s.get('label') or s['url']), 'date': s.get('date', '')} for s in f.get('sources', [])]
    f['verified_iso'] = iso(f.get('verified'))
    attach_logo(f)
    grad = [CITY_SLUGS[c] for c in f['city_list']]
    if f['group'] in ('A', 'B', 'E'):
        grad += [cfg['slug'] for cfg in CITY_CFG if cfg['slug'] not in grad and covers_city(f, cfg)]
    f['grad'] = ' '.join(grad)
    f['q'] = fold(' '.join([f['name'], f.get('domain', ''), f.get('city', ''), ' '.join(f.get('brands', [])), f['kind_label']]))

TYPE_HUBS = []
for _h in json.load(open(ROOT / 'content' / 'data' / 'firme-tipovi.json', encoding='utf-8'))['hubs']:
    _m = [f for f in published if TYPE_RULES[_h['rule']](f)]
    TYPE_HUBS.append(dict(_h, url=f"/firme/{_h['slug']}/", firms=_m, n=len(_m)))
assert not {h['slug'] for h in TYPE_HUBS} & {f['slug'] for f in firms}, 'a firm slug collides with a /firme/ sub-hub'
for f in published:
    f['hubs'] = [h for h in TYPE_HUBS if any(x is f for x in h['firms'])]
BRAND_INDEX = {}
for f in published:
    for b in f.get('brands', []):
        BRAND_INDEX.setdefault(b, []).append(f)
BRAND_INDEX = [(b, sorted(lst, key=lambda f: f['name'].lower())) for b, lst in sorted(BRAND_INDEX.items(), key=lambda kv: kv[0].lower())]
EXCLUDED = sorted([f for f in firms if not f.get('publish') and f.get('excluded_reason')], key=lambda f: f['name'].lower())
CITY_OPTS = [(c['slug'], c['name']) for c in CITY_CFG]
TYPE_CHIPS = [('', 'Sve')] + [(h['rule'], h['chip']) for h in TYPE_HUBS]


def grouped(lst):
    return [(sec, SECTION_LABELS[sec], [f for f in lst if SECTIONS[f['group']] == sec]) for sec in SECTION_ORDER
            if any(SECTIONS[f['group']] == sec for f in lst)]


# ---------------------------------------------------------------- public charging
CALC = json.load(open(ROOT / 'content' / 'data' / 'kalkulator.json', encoding='utf-8'))
_E = CALC['eps']


def all_in(x):
    return (x + _E['oie'] + _E['ee']) * (1 + _E['akciza']) * (1 + _E['pdv'])


KIND_ORDER = ['cpo', 'drzavni', 'host', 'app', 'besplatno']
operators = [o for o in read_json_dir('operateri') if o.get('publish')]
operators.sort(key=lambda o: (KIND_ORDER.index(o['kind']) if o['kind'] in KIND_ORDER else 9, o.get('order', 99)))
for o in operators:
    o['legal'] = o['name']
    o['name'] = o.get('short_name') or o['name']
    o['url'] = f"/javno-punjenje/{o['slug']}/"
    o['app_short'] = (re.split(r' \(| · | — |; ', o.get('app') or '')[0].strip() or '—') if not (o.get('app') or '').startswith('—') else '—'
    o['card_short'] = o.get('card', '')
    o['verified_iso'] = iso(o.get('verified'))
    o['src_items'] = [{'url': s['url'], 'label': clean_src(s.get('label') or s['url']), 'date': s.get('date', '')} for s in o.get('sources', [])]
    prices = []
    for p in o.get('prices', []):
        prices.append(dict(p, source=clean_src(p.get('source', ''))))
    o['now_prices'] = [p for p in prices if not p['what'].startswith('Istorija')]
    o['old_prices'] = [p for p in prices if p['what'].startswith('Istorija')]
    attach_logo(o, 'op-' + o['slug'])

price_index = json.load(open(ROOT / 'content' / 'javno' / 'indeks-cena.json', encoding='utf-8'))


def _r(x):
    return int(x + 0.5)


def kwh_text(row):
    """≈ price per kWh for one index row, as short lines joined with <br>. A start or connection fee (start_rsd) is not
    in the per-kWh figure: it is shown as its own line."""
    st = f'<br>+ {fmt_rsd(row["start_rsd"])} RSD po punjenju' if row.get('start_rsd') else ''
    if row.get('kwh'):
        return f'= {_r(row["rsd_total"] / row["kwh"])} RSD<br>stvarni račun'
    if row.get('unit_rsd'):
        return '„jedinica“ nije kWh'
    if row.get('rsd_kwh'):
        return f'= {fmt_rsd(row["rsd_kwh"][0])} RSD<br>cena po kWh' + st
    if row.get('rsd_hour'):
        return '<br>'.join(f'≈{_r(row["rsd_hour"] / k)} RSD pri {k} kW' for k in row['assume_kw']) + st
    vals, out = row['rsd_min'], []
    for k in row['assume_kw']:
        lo, hi = _r(min(vals) / (k / 60)), _r(max(vals) / (k / 60))
        out.append((f'≈{lo}' if lo == hi else f'≈{lo}–{hi}') + f' RSD pri {k} kW')
    return '<br>'.join(out) + st


for row in price_index['rows']:
    row['source'] = clean_src(row.get('source', ''))
    if not row.get('free'):
        row['kwh_html'] = kwh_text(row)
RECEIPTS = [r['rsd_total'] / r['kwh'] for r in price_index['rows'] if r.get('kwh')]
KWH_RANGE = f'{_r(min(RECEIPTS))}–{_r(max(RECEIPTS))}' if RECEIPTS else ''


def per_min(r):
    if r.get('rsd_min'):
        return r['rsd_min'][0]
    if r.get('rsd_hour'):
        return r['rsd_hour'] / 60
    return None


def price_summary():
    """Compact price cards per network, straight from the price index (content/javno/indeks-cena.json)."""
    ops = {o['slug']: o for o in operators}
    rows = price_index['rows']
    cards = []

    def card(slug, **kw):
        o = ops.get(slug, {'name': slug, 'slug': slug})
        c = {'name': o.get('name'), 'page': o.get('url', ''), 'logo': o.get('logo', ''), 'logo_dark': o.get('logo_dark'), 'items': [], 'sub': '', 'note': '', 'free': False}
        c.update(kw)
        cards.append(c)
    # Charge&GO: one tariff per class of charger power (rows with "sum"); exceptions in the note (rows with "exc")
    cg = [r for r in rows if r['op'] == 'chargego' and r.get('rsd_min') and not r.get('kwh')]
    items = [(r['sum'], r['label']) for r in cg if r.get('sum')] or [(r['charger'], r['label']) for r in cg]
    exc = [r['exc'] for r in cg if r.get('exc')]
    rc = [r['rsd_total'] / r['kwh'] for r in rows if r['op'] == 'chargego' and r.get('kwh')]
    card('chargego', sub='po minutu, prema snazi punjača', items=items,
         note=(f'Izuzeci: {"; ".join(exc)}. ' if exc else '') + (f'Po računima {_r(min(rc))}–{_r(max(rc))} RSD po kWh. ' if rc else '')
         + 'Posle punjenja: 5 RSD/min posle 15 min.')
    # Orion: own chargers, grouped by charger type
    orion = [r for r in rows if r['op'] == 'orion-emobility' and not r.get('where', '').startswith('punjač ') and per_min(r)]
    by = {}
    for r in orion:
        by.setdefault(re.sub(r'\s*\(.*?\)', '', r['charger']), []).append(per_min(r))
    items = []
    for ch in sorted(by, key=lambda c: (c.startswith('DC'), float(re.search(r'(\d+)', c).group(1)))):
        lo, hi = min(by[ch]), max(by[ch])
        items.append((ch, (fmt_rsd(lo) if abs(lo - hi) < 0.01 else f'{fmt_rsd(lo)}–{fmt_rsd(hi)}') + ' RSD/min'))
    card('orion-emobility', sub='+ 50 RSD po punjenju; cena zavisi od lokacije', items=items)
    # eDrive: own chargers per kWh with a start fee
    ed = [r for r in rows if r['op'] == 'edrive' and not r.get('where', '').startswith('punjač ')]
    if ed:
        card('edrive', sub='sopstveni punjači; naknada za pokretanje', items=[(r['charger'], r['label'] + (f' + {fmt_rsd(r["start_rsd"])} RSD' if r.get('start_rsd') else '')) for r in ed],
             note='Na punjačima drugih mreža (roming) eDrive je skuplji od aplikacije te mreže.')
    # Yesla: per kWh
    ye = [r for r in rows if r['op'] == 'yesla']
    if ye:
        ks = sorted({r['rsd_kwh'][0] for r in ye})
        card('yesla', sub='po kWh, plaćanje karticom u aplikaciji', items=[('DC', f'{fmt_rsd(ks[0])}–{fmt_rsd(ks[-1])} RSD/kWh' if len(ks) > 1 else f'{fmt_rsd(ks[0])} RSD/kWh')],
             note=f'{fmt_rsd(ks[0])} RSD/kWh samo na punjaču ZELEZNIK-01 u Železniku.' if len(ks) > 1 else '')
    # Spectra: per "unit" + per minute; a few chargers are free
    sp = [r for r in rows if r['op'] == 'emobility-spectra' and not r.get('free')]
    spf = [r for r in rows if r['op'] == 'emobility-spectra' and r.get('free')]
    if sp or spf:
        items = []
        for cur in ('AC', 'DC'):
            u = [r['unit_rsd'] for r in sp if r['charger'].startswith(cur)]
            if u:
                items.append((cur, (f'{min(u)}–{max(u)}' if min(u) != max(u) else f'{u[0]}') + ' RSD/jed. + 1,20 RSD/min'))
        card('emobility-spectra', sub='„jedinica punjenja“ nije kWh', items=items,
             note=('Besplatno: ' + ', '.join(r['where'] for r in spf) + '.') if spf else '')
    for r in rows:
        if r.get('free') and r['op'] in ('putevi-srbije', 'lidl-echarge'):
            card(r['op'], sub=r.get('who') or '', items=[(r['where'][:1].upper() + r['where'][1:], 'Besplatno')], free=True)
    ps = next((r for r in rows if r['op'] == 'parking-servis-beograd'), None)
    if ps:
        card('parking-servis-beograd', sub='punjenje bez naknade, plaća se parking', items=[(ps['where'][:1].upper() + ps['where'][1:], ps['label'])], note=f"Tarifa iz {ps['date'].split()[-1]}.")
    return cards


PRICE_SUMMARY = price_summary()
PRICE_DATE = price_index['updated']
NT_GREEN = sr_num(all_in(next(z for z in _E['zones'] if z['id'] == 'zelena')['nt']), 2)
NT_BLUE = sr_num(all_in(next(z for z in _E['zones'] if z['id'] == 'plava')['nt']), 2)


# ---------------------------------------------------------------- build start
if DIST.exists():
    shutil.rmtree(DIST)
DIST.mkdir()
shutil.copytree(ROOT / 'static', DIST, dirs_exist_ok=True)

# map data first: counts are used on several pages
MAP = map_data.build(DIST, operators, price_index, {o['slug']: {'logo': o['logo'], 'dark': o['logo_dark']} for o in operators})
MAP_COUNTS = MAP['counts']
CARS_N = map_data.cars(DIST)   # "Moj auto": /assets/map/auta.json

# neighbouring countries on /mapa/: the blokvolt.com sections carry the same open data (OpenStreetMap + Open Charge Map,
# not checked one by one) for the neighbours; /mapa/ draws them as a second, quieter layer (map.js: cfg.region), without
# prices, reports or checks, and links each one to its country's map on blokvolt.com. Kosovo is not part of
# blokvolt.rs (scripts/region_pages.py), so /xk/ is left out. RUNBOOK 3.25.
RG_CC = ('hr', 'ba', 'me', 'al', 'mk')
RG_KEEP = ('id', 'n', 'a', 't', 'lat', 'lon', 'net', 'opn', 'c', 'dc', 'ac', 'acc', 'src', 'v', 'al')
_rg_ids = {_s['id'] for _s in MAP['stations']}
_rg_st, RG_META = [], {}
for _cc in RG_CC:
    _d = ROOT / 'content' / 'com' / 'local' / _cc
    _C = json.load(open(_d / 'country.json', encoding='utf-8'))
    _map_slug = ''
    for _md in sorted(_d.glob('*.md')):
        _fm = re.match(r'---\n(.*?)\n---', _md.read_text(encoding='utf-8'), re.S)
        if _fm and re.search(r'^template:\s*map\s*$', _fm.group(1), re.M):
            _map_slug = re.search(r'^slug:\s*(\S+)\s*$', _fm.group(1), re.M).group(1)
    if not _map_slug:
        raise SystemExit(f'region {_cc}: no map page')
    RG_META[_cc] = {'map': f'https://blokvolt.com/{_cc}/{_map_slug}', 'prices': f"https://blokvolt.com/{_cc}/{_C['slugs']['prices']}", 'n': 0}
    for _s in json.load(open(_d / 'stanice.json', encoding='utf-8'))['stations']:
        if _s['id'] in _rg_ids:
            continue
        _rg_ids.add(_s['id'])
        # map.js reads c, src and v on every station; the other fields only when they are set
        _rs = {k: _s[k] for k in RG_KEEP if k in _s and (k in ('c', 'src', 'v') or _s[k] not in (None, '', []))}
        _rs.setdefault('c', [])
        _rs.setdefault('src', [])
        _rs['cc'] = _cc
        _nn = (_C.get('net_names') or {}).get(_s.get('net') or '')
        if _nn:
            _rs['nn'] = _nn
        _rg_st.append(_rs)
        RG_META[_cc]['n'] += 1
(DIST / 'assets' / 'map' / 'region.json').write_text(json.dumps({
    'about': 'Public chargers in the neighbouring countries (blokvolt.com sections): OpenStreetMap and Open Charge Map, '
             'not checked one by one. Prices and details are on blokvolt.com.',
    'license': 'ODbL 1.0 (OpenStreetMap), CC BY 4.0 (Open Charge Map)',
    'cc': RG_META, 'stations': _rg_st}, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
RG_N = len(_rg_st)
print(f'region layer: {RG_N} stations in ' + ', '.join(f"{k} {v['n']}" for k, v in RG_META.items()))

# state motorway chargers: counts and the per-site status list come from content/mapa/putevi-srbije.json (map_data)
_pv = next((o for o in operators if o['slug'] == 'putevi-srbije'), None)
_PS = MAP.get('ps') or {}
PUTEVI_N = str(_PS.get('total', ''))
PUTEVI_RUN = str(_PS.get('works', ''))
PUTEVI_VERB = 'rade' if _PS and _PS['works'] % 10 in (2, 3, 4) and _PS['works'] % 100 not in (12, 13, 14) else 'radi'
PS_NOTE = {'kw60': 'do 60 kW', 'dc_only': 'samo DC konektor', 'toll': 'do otvaranja naplatne stanice'}
if _PS and _pv:
    _ps_ids = {}
    for _st in MAP['stations']:
        if _st.get('ps'):
            _ps_ids.setdefault(_st['ps']['site'], _st['id'])
    _pv['ps_sites'] = [{'name': s['name'], 'road': s['road'], 'map': _ps_ids.get(s['name']),
                        'lines': [{'dir': c.get('dir') or '', 'power': c['power'], 'st': c['status'],
                                   'note': PS_NOTE.get(c.get('note', ''), ''), 'when': c.get('when', '')} for c in s['chargers']]}
                       for s in _PS['sites']]
    _pv['ps_meta'] = {k: _PS[k] for k in ('total', 'works', 'down', 'connecting', 'planned', 'checked', 'source')}
for _s in SITE_META['home_stats']:  # "auto:putevi" = counts from the official list (content/mapa/putevi-srbije.json)
    if _s['b'] == 'auto:putevi':
        _s['b'] = f'{PUTEVI_RUN} od {PUTEVI_N}'
        _s['short'] = f'državnih punjača na autoputevima {PUTEVI_VERB}, besplatno'
for o in operators:
    o['on_map'] = MAP_COUNTS.get(o['slug'], 0)


def _ver(p):
    return hashlib.sha1(p.read_bytes()).hexdigest()[:10]


MAP_T = {
    'schuko': 'Šuko', 'other': 'Ostalo', 'charger': 'Punjač', 'near': 'okolina: {t}', 'per_min': 'RSD/min', 'free': 'Besplatno',
    'p_unknown': 'Cena nije poznata. Proverite u aplikaciji mreže.', 'p_free': 'Besplatno', 'p_exact': 'Cena na ovom punjaču',
    'p_tier': 'Cena mreže za {c}', 'p_receipt': 'Račun: {l}, {k} RSD po kWh', 'p_range': 'Između cena za {a} i {b}',
    'p_seen': 'Zabeležene cene ove mreže:', 'price': 'Cena', 'count_all': 'Punjača: {n}', 'count': 'Prikazano {n} od {all}',
    'sorted_near': 'najbliži prvi', 'none': 'Nema punjača za ovaj izbor.', 'conn': 'Priključci', 'access': 'Pristup',
    'customers': 'Samo za goste ili kupce', 'navigate': 'Navigacija', 'site': 'Sajt mreže', 'about_net': 'O mreži',
    'nav_in': 'Otvori u:', 'share': 'Podeli', 'copied': 'Link je kopiran',
    'p_old': 'Cena je starija od godinu dana. Proverite u aplikaciji mreže.',
    'report': 'Prijavi grešku', 'mail_subj': 'Greška na mapi', 'mail_body': 'Šta nije tačno:', 'data': 'Podaci',
    'close': 'Zatvori', 'net_known': 'Mreža', 'operator': 'Operater', 'net_unknown': 'Mreža nije poznata',
    'no_location': 'Lokacija nije dostupna.', 'load_err': 'Mapa trenutno ne može da se učita. Pokušajte ponovo.',
    'idle': 'Zauzeće posle punjenja: {x}', 'in_view': 'U ovom delu mape: {n}', 'all_serbia': 'Cela Srbija', 'more': 'Prikaži još ({n})',
    'off': 'Ne radi', 'status': 'Stanje punjača', 'st_ok': 'radi', 'st_off': 'ne radi', 'st_kw60': 'do 60 kW',
    'st_dc_only': 'samo DC konektor', 'st_src': 'Po spisku JP „Putevi Srbije“ od {d}',
    # verification (content/mapa/provera.json, content/mapa/mreze/)
    'v_ok': 'Potvrđeno', 'v_cg': 'na spisku lokacija mreže Charge&GO', 'v_rm': 'na roming mapi Charge&GO',
    'v_te': 'na zvaničnom spisku Tesla', 'v_ps': 'na spisku JP „Putevi Srbije“', 'v_g': 'skorašnje ocene vozača na Google mapama',
    'v_nep': 'Nije potvrđeno', 'v_checked': 'Provereno {d}', 'v_help': 'Šta znači oznaka?',
    'v_none': 'Punjač je samo u otvorenim bazama: nema ga ni na spisku mreža ni na Google mapama. Možda više ne postoji ili nije javan. Proverite pre polaska.',
    'v_old': 'Punjač je u otvorenim bazama i na Google mapama, ali bez skorijih potvrda: nijedna ocena vozača iz poslednjih godinu dana. Proverite pre polaska.',
    'v_prob_t': 'Prijavljen kvar', 'v_prob': 'Vozači u skorašnjim recenzijama pišu da punjač ne radi. Proverite pre polaska.',
    'v_test': 'Po spisku mreže punjač je u probnom radu i još nije otvoren za sve. Proverite u aplikaciji pre polaska.',
    'src_rm': 'Charge&GO roming',
    # drivers' reports (/api)
    'rv_title': 'Iskustva vozača', 'rv_empty': 'Još nema prijava za ovaj punjač.', 'ratings': 'ocena: {n}', 'last_report': 'Poslednja prijava',
    'rv_q': 'Bili ste ovde? Javite kako je.', 'ci_ok': 'Radi', 'ci_problem': 'Radi, uz problem', 'ci_broken': 'Ne radi', 'ci_missing': 'Nema punjača',
    'rv_rate': 'Ocena', 'rv_comment': 'Komentar', 'rv_comment_ph': 'Kako je prošlo punjenje? (nije obavezno)', 'rv_name': 'Ime ili nadimak (nije obavezno)',
    'rv_send': 'Pošalji', 'rv_cancel': 'Otkaži', 'rv_rules': 'Bez ličnih podataka, reklama i uvreda.', 'rv_rules_link': 'Pravila',
    'rv_thanks': 'Hvala! Prijava je sačuvana.', 'rv_thanks_pending': 'Hvala! Prijava je sačuvana, a komentar će biti objavljen posle provere.',
    'rv_err': 'Slanje nije uspelo. Pokušajte ponovo.', 'rv_limit': 'Previše prijava za danas. Pokušajte sutra.',
    'rv_fast': 'Sačekajte nekoliko sekundi pa pošaljite ponovo.', 'rv_off': 'Prijave vozača sada ne mogu da se učitaju. Proverite internet vezu.',
    'photo_queue': 'Za ovaj punjač već mnogo fotografija čeka proveru. Pokušajte ponovo za nekoliko dana.',
    'report_abuse': 'Prijavi neprikladan komentar', 'report_photo': 'Prijavi fotografiju', 'reported': 'Prijavljeno, hvala.',
    'add_photo': 'Dodaj fotografiju', 'photo_alt': 'Fotografija punjača',
    'photo_note': 'Fotografije se objavljuju posle provere. Ne slikajte ljude i tablice izbliza.',
    'photo_wait': 'Šaljem…', 'photo_thanks': 'Hvala! Fotografija će se pojaviti posle provere.', 'photo_bad': 'Ova slika ne može da se pošalje. Probajte JPEG.',
    'today': 'danas', 'yesterday': 'juče', 'days_ago': 'pre {n} dana',
    # favourites (kept only in this browser)
    'fav_add': 'Sačuvaj u omiljene', 'fav_del': 'Ukloni iz omiljenih', 'fav_sr': 'omiljeni',
    'conn_mine': 'vaš auto',   # the fast-charging plug of a signed-in reader's car (Moj BlokVolt)
    'fav_none': 'Još nema omiljenih punjača. Otvorite punjač i dodirnite zvezdicu — lista se čuva u ovom pregledaču.',
    # prices on the pins, Tesla-only chargers, our checked facts (content/mapa/dopune.json)
    'per_kwh': 'RSD/kWh', 'tesla_only': 'Samo Tesla', 'p_tesla_only': 'Samo za Tesla vozila', 'p_tesla_fee': '{t} — {s}.',
    'p_tesla_hint': 'Imate Teslu? Uključite „Imam Teslu“ iznad liste punjača.', 'p_by_receipt': 'Po računima sa ovog punjača ({d})',
    'p_est': '≈ {k} RSD po kWh ako auto puni sa {w} kW', 'v_own': 'na sajtu vlasnika lokacije',
    'where': 'Gde tačno', 'addr_none': 'Adresa nije poznata — koristite koordinate.', 'copy': 'Kopiraj', 'copied_ll': 'Kopirano',
    'q_net': 'Tačka je sa spiska mreže.', 'q_osm': 'Tačka je iz OpenStreetMap-a.',
    'q_ocm': 'Tačka je iz Open Charge Map-a i može odstupati nekoliko desetina metara.',
    'q_site': 'Približna tačka: parking ili objekat, ne sam punjač.', 'q_field': 'Tačka je proverena na licu mesta.',
    # neighbouring countries (cfg.region, /assets/map/region.json)
    'v_src': 'Iz otvorenih baza OpenStreetMap i Open Charge Map. Punjač nije pojedinačno proveren — pre polaska proverite u aplikaciji mreže.',
    'cc_hr': 'Hrvatska', 'cc_ba': 'Bosna i Hercegovina', 'cc_me': 'Crna Gora', 'cc_al': 'Albanija', 'cc_mk': 'Severna Makedonija',
    'rg_count': 'u regionu još {n}', 'rg_open': 'Mapa zemlje na blokvolt.com', 'rg_prices': 'Cene mreža: {c}',
    'rg_note': 'Punjač je van Srbije. Cene su u valuti te zemlje, sa datumom i izvorom.',
    'v_src_short': 'Nije pojedinačno proveren', 'loading': 'Učitavanje…', 'src_cga': 'aplikacija Charge&GO',
    # the network's price of every connector (mreze.json: pr)
    'p_station': 'Cena ovog punjača u aplikaciji mreže · {d} · {s}',
    # "Najbliži punjač"
    'nr_title': 'Najbliži punjači', 'nr_sub': 'Potvrđeni punjači koji rade · udaljenost vazdušnom linijom',
    'nr_sub_all': 'Uključeni su i nepotvrđeni · udaljenost vazdušnom linijom', 'nr_fast': 'Samo brzi (DC)',
    'nr_nav_to': 'Navigacija do {t}, {d}', 'nr_opens': 'Otvara se u: {a}', 'nr_change': 'Promeni', 'nr_nep': 'Prikaži i nepotvrđene',
    'nr_unfilter': 'Ukloni filter', 'nr_wait': 'Tražim vašu lokaciju…',
    'nr_denied': 'Pregledač nema dozvolu za lokaciju. Dozvolite je za ovaj sajt u podešavanjima pregledača, pa pokušajte ponovo.',
    'nr_unavail': 'Lokacija trenutno nije dostupna. Pokušajte ponovo za minut.', 'nr_retry': 'Pokušajte ponovo',
    'nr_privacy': 'Lokacija ostaje na vašem uređaju.', 'nr_far': 'Na mapi su punjači u Srbiji i susednim zemljama.', 'nr_find': 'Pronađi najbliže',
    'nr_ask': 'Za najbliže punjače potrebna je vaša lokacija. Pregledač je traži tek kad pritisnete dugme i ne šalje je sajtu.',
    # hours, cable, parking (mreze.json, dopune.json)
    'oh_open': 'sada radi do {t}', 'oh_closed': 'sada zatvoreno, otvara u {t}', 'closed_now': 'sada zatvoreno',
    'cab_own': 'Ponesite svoj Tip 2 kabl',
    # "Moj auto" and the cost per km
    'car_none': 'izaberite — cena po km', 'car_title': 'Moj auto',
    'car_lead': 'Mapa tada pokazuje cenu po kilometru za vaš auto: koliko snage auto zaista prima na svakom punjaču, potrošnju i naknade.',
    'car_make': 'Marka', 'car_model': 'Model', 'car_choose_make': 'Izaberite marku', 'car_choose_model': 'Izaberite model',
    'car_cons': 'Potrošnja, kWh na 100 km (nije obavezno)', 'car_cons_hint': 'Procena je za mešovitu vožnju; upišite svoju sa putnog računara.',
    'car_opt': 'Auto ima opcioni punjač od {k} kW', 'car_cab': 'Imam svoj Tip 2 kabl', 'car_save': 'Sačuvaj', 'car_del': 'Ukloni auto',
    'car_note': 'Izbor se čuva samo u ovom pregledaču.', 'car_src': 'Podaci o autima: Open EV Data, Chargeprice, P3, ADAC i proizvođači.',
    'car_load_err': 'Spisak automobila trenutno ne može da se učita. Pokušajte ponovo.',
    'per_km': 'RSD/km', 'u_kw': 'kW', 'u_km': 'km', 'u_m': 'm', 'sorted_cheap': 'najjeftinije za vaš auto prvo',
    'cost_pick': 'Izaberite auto — pokazaćemo cenu po kilometru', 'cost_t': 'Za vaš {car}: ≈ {x} RSD/km', 'cost_100': '100 km ≈ {x} RSD',
    'cost_kw': 'auto ovde prima ≈ {w} kW, ≈ {k} RSD po kWh', 'cost_start': 'Uračunata je naknada za pokretanje od {s} RSD.',
    'cost_winter': 'Zimska potrošnja: +{p} %.', 'cost_alt': 'Ovde je za vaš auto jeftiniji {c}: ≈ {x} RSD/km.',
    'cost_near': 'Jeftinije u blizini: {t}, {d} — ≈ {x} RSD/km.', 'cost_near_free': 'Besplatno u blizini: {t}, {d}.', 'cost_cmp': 'Benzin ≈ {b} RSD/km · kod kuće noću ≈ {h} RSD/km',
    'cost_na': 'Za ovu cenu ne može da se izračuna cena po kilometru.', 'cost_no_dc': 'Vaš {car} ne može da puni na DC priključku ovog punjača.',
    # "Izdvojeno": charging at home (Evolako)
    'promo_badge': 'Izdvojeno', 'promo_km': 'Kod kuće noću ≈ {h} RSD/km, punjačem u garaži zgrade.',
    'promo_kwh': 'Kod kuće noću ≈ {h} RSD po kWh, punjačem u garaži zgrade.', 'promo_link': 'Evolako →',
    # "Kako se puni ovde" (cene.json: kako)
    'kako_t': 'Kako se puni ovde — {n}', 'kako_pay': 'Plaćanje:', 'kako_guest': 'Bez registracije:', 'kako_after': 'Posle punjenja:',
    'kako_refund': 'Povraćaj:', 'kako_apps': 'Aplikacija:', 'kako_checked': 'Provereno {d}',
    # drivers' short answers
    'why_q': 'Šta nije bilo u redu? (nije obavezno)', 'why_busy': 'Mesto zauzeto', 'why_broken': 'Punjač ne radi',
    'why_app': 'Aplikacija ili plaćanje', 'why_cable': 'Nisam imao svoj kabl', 'why_closed': 'Zatvoreno', 'why_short': 'Kabl prekratak',
    'f_q': 'Još tri kratka pitanja (nije obavezno):', 'f_cab': 'Kabl', 'f_cab_att': 'na punjaču', 'f_cab_own': 'treba svoj',
    'f_park': 'Parking', 'f_park_free': 'besplatan', 'f_park_paid': 'plaća se', 'f_oh': 'Radno vreme', 'f_oh_24': '0–24', 'f_oh_lim': 'ograničeno',
    'f_by': 'po vozačima, {n}×', 'why_seen': 'Vozači javljaju (60 dana): {x}',
}
# Serbian notes that come with the price data (cene.json) and the idle fees: added as 'tx:<text>' so that the
# translation memory translates them on /en/ and /ru/ (map.js looks them up with tr())
_IDLE = {'chargego': '5 RSD/min posle 15 min', 'orion-emobility': '5 RSD/min posle 15 min', 'emobility-spectra': '10,20 RSD/min posle 10 min (ECO)'}
_tx = set(_IDLE.values())
for _n in MAP['nets'].values():
    _tx.update(x for x in (_n.get('note'), _n.get('free_note')) if x)
    for _t in _n.get('tiers', []) + _n.get('places', []):
        _tx.update(x for x in (_t.get('extra'), _t.get('src')) if x)
    for _rc in _n.get('receipts', []):
        _tx.update(x for x in (_rc.get('label'),) if x and re.search('[a-zčćžšđ]{3}', x.lower()))
    _k = _n.get('kako') or {}
    _tx.update(x for x in _k.get('start', []) + [_k.get(f) for f in ('pay', 'guest', 'after', 'refund')] if x)
    _tx.update(x['l'] for x in _k.get('apps', []) + _k.get('src', []) if re.search('[a-zčćžšđ]{3}', x['l'].lower()))
_tx.update(MAP['extra_texts'])
for _x in sorted(_tx):
    MAP_T['tx:' + _x] = _x
CHIP_NETS = ['chargego', 'orion-emobility', 'putevi-srbije', 'tesla', 'emobility-spectra']
_r0 = MAP['retrieved'].split('-')
M = {
    'n': MAP['n'],
    'ok': sum(1 for _s in MAP['stations'] if (_s.get('v') or {}).get('s') == 'ok'),
    'chips': [(s, map_data.NAMES.get(s, s), MAP_COUNTS[s]) for s in CHIP_NETS if MAP_COUNTS.get(s, 0) >= 4],
    'retrieved_sr': f'{_r0[2]}.{_r0[1]}.{_r0[0]}' if len(_r0) == 3 else MAP['retrieved'],
    'checked': MAP.get('checked', ''),
    'rg_n': RG_N,
    'cfg': json.dumps({
        'style': 'https://tiles.openfreemap.org/styles/positron',
        'font': ['Noto Sans Bold'],
        'stations': '/assets/map/punjaci.json?v=' + _ver(DIST / 'assets' / 'map' / 'punjaci.json'),
        'nets': '/assets/map/mreze.json?v=' + _ver(DIST / 'assets' / 'map' / 'mreze.json'),
        'api': '/api',
        'help': '/pomoc/sta-znaci-potvrdjeno/',
        'prices': '/assets/map/cene.json?v=' + _ver(DIST / 'assets' / 'map' / 'cene.json'),
        'extra': '/assets/map/dopune.json?v=' + _ver(DIST / 'assets' / 'map' / 'dopune.json'),
        'region': '/assets/map/region.json?v=' + _ver(DIST / 'assets' / 'map' / 'region.json'),
        'cities': {c['slug']: list(TOWN_XY[c['name']]) for c in CITY_CFG if c['name'] in TOWN_XY},
        'idle': _IDLE,
        # "Moj auto": the cars, home charging at night (EPS, lower tariff, green and blue zone, all fees) and fuel for the
        # comparison per km (the calculator's numbers: content/data/kalkulator.json)
        'cars': '/assets/map/auta.json?v=' + _ver(DIST / 'assets' / 'map' / 'auta.json'),
        'home': [round(all_in(next(z for z in _E['zones'] if z['id'] == i)['nt']), 2) for i in ('zelena', 'plava')],
        'fuel': {'b': CALC['fuel']['benzin'], 'd': CALC['fuel']['dizel'], 'lb': CALC['defaults']['l100_benzin'],
                 'ld': CALC['defaults']['l100_dizel'], 'date': CALC['fuel']['date']},
        'evo': EVOLAKO + 'proveri-svoju-garazu',
    }, ensure_ascii=False).replace('</', '<\\/'),
    'i18n': json.dumps(MAP_T, ensure_ascii=False),
}


def near_count(lat, lon, km=15):
    return sum(1 for s in MAP['stations'] if map_data.dist_m({'latitude': lat, 'longitude': lon}, {'latitude': s['lat'], 'longitude': s['lon']}) <= km * 1000)


# ---------------------------------------------------------------- navigation and page context
NAV = [('/mapa/', 'Mapa punjača', 'mapa'), ('/firme/', 'Firme', 'firme'), ('/cene/', 'Cene', 'cene'),
       ('/vodici/', 'Vodiči', 'vodici'), ('/vesti/', 'Vesti', 'vesti'), ('/alati/kalkulator-troskova/', 'Kalkulator', 'kalk')]
PRICE_PAGES = ('/podaci/tarife-eps/', '/podaci/wallbox-modeli/', '/podaci/cene-elektricnih-automobila/', '/cena-punjaca-za-elektricni-auto')


def section_of(path):
    if path.startswith('/mapa/'):
        return 'mapa'
    if path.startswith('/vesti/'):
        return 'vesti'
    if path.startswith(('/firme/', '/gradovi/')):
        return 'firme'
    if path.startswith(('/javno-punjenje/', '/cene/')) or path.startswith(PRICE_PAGES):
        return 'cene'
    if path.startswith('/alati/kalkulator-troskova/'):
        return 'kalk'
    if path.startswith(('/podaci/', '/vodici/', '/alati/')) or path.endswith('.html') and 'politika' not in path:
        return 'vodici'
    return ''


CRUMB = {'cene': ('/cene/', 'Cene'), 'vodici': ('/vodici/', 'Vodiči'), 'firme': ('/firme/', 'Firme')}

# usage analytics (docs/RUNBOOK.md 3.16): PostHog only when a project key is set in site.json
_AN = dict(SITE_META.get('analytics') or {})
if os.environ.get('BV_QA_POSTHOG_KEY'):       # QA only: build with a dummy key to see the banner and the PostHog texts
    _AN['posthog_key'] = os.environ['BV_QA_POSTHOG_KEY']
# consent: true = cookieless for everyone until the reader allows the analytics cookie in the banner (then cookies and
# session replay with masked inputs); false = cookieless only, no banner
ANALYTICS_CONSENT = bool(_AN.get('posthog_key')) and bool(_AN.get('consent'))
ANALYTICS = json.dumps({'key': _AN['posthog_key'], 'host': _AN['posthog_host'], 'ui': _AN['posthog_ui'], 'assets': _AN['posthog_assets'],
                        'consent': ANALYTICS_CONSENT}) if _AN.get('posthog_key') else ''
# accounts ("Moj BlokVolt", /nalog/) and the newsletter (Nedeljni pregled, /pregled/), docs/RUNBOOK.md 3.27:
# content/data/site.json → accounts.enabled, pregled.enabled (+ pregled.day). Off, the pages are still built, but noindex,
# out of the sitemap and not linked from anywhere. BV_QA_ACCOUNTS=1 / BV_QA_PREGLED=1 switch them on for a QA build
# (like BV_QA_POSTHOG_KEY; '0' switches them off). "since" (DD.MM.YYYY, the day a feature goes live) dates the change in the
# privacy policy; a real build with a feature on refuses to run without it, a QA build uses today.
def _feature(name, env_var):
    cfg = SITE_META.get(name) or {}
    on, qa = bool(cfg.get('enabled')), os.environ.get(env_var) in ('0', '1')
    if qa:
        on = os.environ[env_var] == '1'
    since = cfg.get('since') or (TODAY if qa else '')
    if on and not re.fullmatch(r'\d{2}\.\d{2}\.\d{4}', since):
        raise SystemExit(f'content/data/site.json: {name}.since (DD.MM.YYYY, the day it goes live) is needed when {name}.enabled is true')
    return on, since


ACCOUNTS, ACCOUNTS_SINCE = _feature('accounts', 'BV_QA_ACCOUNTS')
_PG_ON, PREGLED_SINCE = _feature('pregled', 'BV_QA_PREGLED')
# the newsletter's day in the two Serbian forms the texts need: "stiže petkom" and "stiže u petak"
DAY_FORMS = {'ponedeljak': ('ponedeljkom', 'u ponedeljak'), 'utorak': ('utorkom', 'u utorak'), 'sreda': ('sredom', 'u sredu'),
             'četvrtak': ('četvrtkom', 'u četvrtak'), 'petak': ('petkom', 'u petak'), 'subota': ('subotom', 'u subotu'),
             'nedelja': ('nedeljom', 'u nedelju')}
_PG_DAY = (SITE_META.get('pregled') or {}).get('day') or 'petak'
assert _PG_DAY in DAY_FORMS, f'site.json pregled.day: one of {", ".join(DAY_FORMS)}'
PG = {'on': _PG_ON, 'day': _PG_DAY, 'dayi': DAY_FORMS[_PG_DAY][0], 'dayu': DAY_FORMS[_PG_DAY][1]}
print('features: accounts ' + ('on' if ACCOUNTS else 'off') + ', pregled ' + ('on' if PG['on'] else 'off'))
if ACCOUNTS:   # the map's favourites also go to the account of a signed-in reader
    MAP_T['fav_none'] = 'Još nema omiljenih punjača. Otvorite punjač i dodirnite zvezdicu — lista se čuva u ovom pregledaču, a ako ste prijavljeni — i u nalogu.'
    M['i18n'] = json.dumps(MAP_T, ensure_ascii=False)
base_ctx = dict(SITE=SITE, TODAY=TODAY, ISO_TODAY=ISO_TODAY, FIRMS_CHECKED=FIRMS_CHECKED, SITE_META=SITE_META, NAV=NAV,
                n_firms=len(published), n_map=MAP['n'], ANALYTICS=ANALYTICS, ANALYTICS_CONSENT=ANALYTICS_CONSENT, APP=APP,
                ACCOUNTS=ACCOUNTS, PG=PG)

urls = []


def add_url(path, prio='0.6', lastmod=ISO_TODAY):
    urls.append((SITE + canon_of(path), prio, lastmod))


def render(tpl, path, **ctx):
    c = dict(base_ctx)
    c.update(ctx)
    c['path'] = path
    c['canon'] = canon_of(path)
    c.setdefault('section', section_of(path))
    write(path, env.get_template(tpl).render(**c))


# ---------------------------------------------------------------- articles (Markdown)
PROMO = {'text': 'Evolako ugrađuje punjač u zgradi ili garaži sa MID brojilom, uz mesečni obračun struje po ceni iz računa EPS-a i šablone za skupštinu.',
         'href': EVOLAKO, 'link': 'evolako.rs'}
PROMO_ON = {'/punjenje-elektricnog-auta-u-zgradi.html', '/punjac-u-zgradi-skupstina.html', '/ko-placa-struju-za-punjenje.html',
            '/punjac-u-iznajmljenoj-garazi.html'}
ARTICLES = {}
for mdf in sorted(glob.glob(str(ROOT / 'content' / 'podaci' / '*.md'))) + sorted(glob.glob(str(ROOT / 'content' / 'javno' / '*.md'))) \
        + sorted(glob.glob(str(ROOT / 'content' / 'vodici' / '*.md'))):
    meta, body = front_matter(mdf)
    slug = Path(mdf).stem
    path = meta.get('path') or f'/podaci/{slug}/'
    ARTICLES[path] = {'meta': meta, 'body': body, 'path': path, 'canon': canon_of(path), 'slug': slug,
                      'h1': meta.get('h1') or meta.get('title', '').split(' — ')[0].split(':')[0],
                      'lead': meta.get('lead', ''), 'title': meta.get('title', '')}

# the two hubs; each entry: (href, name, description, icon)
def A(path, name=None, desc=None, icon='doc'):
    a = ARTICLES.get(path)
    href = canon_of(path)
    return {'href': href, 'name': name or (a['h1'] if a else path), 'desc': desc or (clip(a['lead'], 120) if a else ''), 'icon': icon,
            'img': ((a['meta'].get('thumb') or a['meta'].get('image')) if a else None)}


VODICI_GROUPS = [
    ('Punjač u zgradi i garaži', [
        A('/punjenje-elektricnog-auta-u-zgradi.html', icon='building'), A('/punjac-u-zgradi-skupstina.html', icon='doc'),
        A('/ko-placa-struju-za-punjenje.html', icon='coins'),
        {'href': '/alati/racun-u-zgradi/', 'name': 'Ko koliko plaća u zgradi', 'desc': 'Kalkulator: koliko komšije plaćaju tuđe punjenje bez brojila.', 'icon': 'calc', 'img': 'stambena-zgrada-balkoni'},
        A('/bezbednost-punjenja-atest.html', icon='shield'), A('/punjac-u-iznajmljenoj-garazi.html', icon='plug'),
        A('/elektricni-auto-bez-garaze.html', icon='car'), A('/wallbox-cena-srbija.html', icon='plug')]),
    ('Kupovina i vlasništvo', [
        A('/podaci/subvencije-2026/', icon='gift'), A('/podaci/cene-elektricnih-automobila/', 'Cene električnih automobila', icon='car'),
        A('/podaci/registracija-i-porezi/', icon='doc'), A('/podaci/uvoz-i-carina/', icon='doc'),
        A('/podaci/osiguranje-elektricnog-automobila/', icon='shield'), A('/podaci/krediti-i-lizing/', icon='coins'),
        A('/podaci/servisi-za-elektricne-automobile/', icon='car'), A('/podaci/rent-a-car-i-car-sharing/', icon='car'),
        A('/najam-elektricnog-automobila.html', icon='car')]),
    ('Na putu', [
        A('/javno-punjenje/kako-jeftinije-puniti/', icon='coins'), A('/javno-punjenje/plug-in-hibrid-na-javnom-punjacu/', icon='bolt'), A('/podaci/putarina-i-parking/', icon='road'), A('/javno-punjenje/besplatni-punjaci/', icon='gift'),
        A('/javno-punjenje/aplikacije-i-kartice/', icon='phone'), A('/javno-punjenje/region/', icon='globe2')]),
    ('Brojke', [
        A('/podaci/statistika-ev-srbija/', icon='chart'), A('/podaci/tarife-eps/', 'Cena struje kod kuće', icon='bolt'),
        A('/podaci/wallbox-modeli/', 'Wallbox modeli i cene', icon='plug')]),
]
CENE_TILES = [
    {'href': '/javno-punjenje/', 'name': 'Javno punjenje', 'desc': 'Cene po mrežama, po minutu i po kWh, i besplatni punjači.', 'icon': 'bolt'},
    {'href': '/cena-punjaca-za-elektricni-auto', 'name': 'Kućni punjač sa ugradnjom', 'desc': 'Koliko traže firme i šta ulazi u ugradnju.', 'icon': 'plug'},
    {'href': '/podaci/wallbox-modeli/', 'name': 'Wallbox uređaji', 'desc': 'Cene modela kod prodavaca u Srbiji.', 'icon': 'firm'},
    {'href': '/podaci/tarife-eps/', 'name': 'Struja kod kuće', 'desc': 'Zone, tarife i sati jeftinije struje.', 'icon': 'coins'},
    {'href': '/podaci/cene-elektricnih-automobila/', 'name': 'Električni automobili', 'desc': 'Cene modela kod uvoznika i posle subvencije.', 'icon': 'car'},
    {'href': '/alati/kalkulator-troskova/', 'name': 'Kalkulator troškova', 'desc': 'Koliko košta 100 km: kuća, javni punjač, benzin.', 'icon': 'calc'},
]


def related_for(path):
    href = canon_of(path)
    for _, items in VODICI_GROUPS:
        if any(i['href'] == href for i in items):
            rel = [i for i in items if i['href'] != href][:3]
            return [{'path': i['href'], 'h1': i['name'], 'lead': i['desc']} for i in rel]
    return []


AN_BLOCKS = {'posthog': bool(ANALYTICS), 'noposthog': not ANALYTICS, 'consent': ANALYTICS_CONSENT, 'noconsent': not ANALYTICS_CONSENT,
             'cookieless': bool(ANALYTICS) and not ANALYTICS_CONSENT,
             # accounts and the newsletter (RUNBOOK 3.27); posta = either of them (the site sends e-mail)
             'nalog': ACCOUNTS, 'nonalog': not ACCOUNTS, 'pregled': PG['on'], 'nopregled': not PG['on'],
             'posta': ACCOUNTS or PG['on'], 'noposta': not (ACCOUNTS or PG['on'])}


def posthog_blocks(body):
    """Privacy-policy text that depends on the analytics mode: <!--posthog-->…<!--/posthog--> (PostHog on),
    <!--noposthog--> (off), <!--consent--> (on, with the cookie banner), <!--noconsent--> (no banner: off or
    cookieless), <!--cookieless--> (on, no banner). The same for the accounts and the newsletter: <!--nalog-->,
    <!--nonalog-->, <!--pregled-->, <!--nopregled-->, <!--posta--> (either is on), <!--noposta-->. Blocks of different
    kinds may be nested. {{NALOG_OD}} and {{PREGLED_OD}} become the date the feature went live (site.json → since)."""
    for k, on in AN_BLOCKS.items():
        if on:
            body = body.replace(f'<!--{k}-->', '').replace(f'<!--/{k}-->', '')
        else:
            body = re.sub(rf'\n?<!--{k}-->.*?<!--/{k}-->\n?', lambda m: '\n' if m.group(0).startswith('\n') and m.group(0).endswith('\n') else '',
                          body, flags=re.S)
    return body.replace('{{NALOG_OD}}', ACCOUNTS_SINCE).replace('{{PREGLED_OD}}', PREGLED_SINCE)


def _later(a, b):
    """The later of two DD.MM.YYYY dates ('' counts as none)."""
    return max((x for x in (a, b) if x), key=lambda x: x.split('.')[::-1], default='')


for path, a in ARTICLES.items():
    _raw = a['body']
    a['body'] = posthog_blocks(a['body'])
    meta = a['meta']
    # front matter lead_consent / description_consent (cookie banner), lead_nalog / description_nalog (accounts on) and
    # lead_consent_nalog / description_consent_nalog (both) replace the lead and description
    _suffixes = (['_consent_nalog', '_nalog', '_consent'] if ANALYTICS_CONSENT and ACCOUNTS else ['_nalog'] if ACCOUNTS
                 else ['_consent'] if ANALYTICS_CONSENT else [])
    for _k in ('lead', 'description'):
        _v = next((meta[_k + _s] for _s in _suffixes if meta.get(_k + _s)), None)
        if _v:
            meta[_k] = _v
    a['lead'] = meta.get('lead', a['lead'])
    # a page whose text changes when a feature goes live shows that date as its update (e.g. the privacy policy)
    for _tok, _on, _since in (('{{NALOG_OD}}', ACCOUNTS, ACCOUNTS_SINCE), ('{{PREGLED_OD}}', PG['on'], PREGLED_SINCE)):
        if _on and _tok in _raw and meta.get('updated'):
            meta['updated'] = _later(meta['updated'], _since)
            meta['modified'] = max(meta.get('modified') or '', iso(meta['updated']))
    sec = section_of(path)
    if path.startswith('/javno-punjenje/'):
        crumbs = [('/javno-punjenje/', 'Javno punjenje')]
    elif sec in ('cene', 'vodici') and path not in ('/politika-privatnosti.html',):
        crumbs = [CRUMB[sec]]
    else:
        crumbs = []
    meta = dict(meta, h1=a['h1'])
    render('article.html', path, meta=meta, body=md_to_html(a['body']), crumbs=crumbs, section=sec,
           title=meta.get('title', a['h1']) + ' | BlokVolt', description=meta.get('description', ''), sources=sources_of(meta),
           promo_box=PROMO if path in PROMO_ON else None, related=related_for(path), oglas=oglas_za(path))
    add_url(path, meta.get('priority', '0.7'), meta.get('modified', ISO_TODAY))

def _numbered(groups):
    n = 0
    for g in groups:
        for it in g['items']:
            n += 1
            it['pos'] = n
    return groups


render('hub.html', '/vodici/', h1='Vodiči', lead='Kratki odgovori o punjenju, kupovini i troškovima električnog automobila u Srbiji.',
       groups=_numbered([{'title': t, 'tiles': False, 'items': [dict(i) for i in items]} for t, items in VODICI_GROUPS]),
       title='Vodiči za električni automobil u Srbiji: punjač u zgradi, subvencije, troškovi | BlokVolt',
       description='Punjač u zgradi i odluka skupštine, ko plaća struju, subvencije 2026, registracija, osiguranje, putarina, statistika i cene struje. Kratko, sa izvorima.')
add_url('/vodici/', '0.8')
render('hub.html', '/cene/', h1='Cene', lead='Koliko košta punjenje, kućni punjač, struja kod kuće i sam automobil.',
       groups=_numbered([{'title': '', 'tiles': True, 'items': [dict(i) for i in CENE_TILES]}]),
       title='Cene u Srbiji: javno punjenje, kućni punjač, struja, električni automobili | BlokVolt',
       description='Cene javnog punjenja po mrežama, kućnih punjača sa ugradnjom, wallbox uređaja, struje po tarifama EPS-a i električnih automobila kod uvoznika.')
add_url('/cene/', '0.8')

# ---------------------------------------------------------------- help (/pomoc/)
# content/pomoc/<slug>.md, one question per file (docs/RUNBOOK.md 3.24). Front matter: id, title, h1, description, lead,
# kicker, section (one of POMOC_SECTIONS), order, path (/pomoc/<slug>/), updated (DD.MM.YYYY), related (help paths,
# comma-separated), shots (the pictures the text asks for), published, modified. Body: Markdown; a line
# [[shot:<id> | <alt>]] shows static/assets/img/pomoc-<id>-<w>.webp (scripts/pomoc_shots.py) and is left out while the
# picture does not exist. No counts or prices that change with the data: they would go stale here.
POMOC_SECTIONS = [('mapa-i-podaci', 'Mapa i podaci', 'Kako se čita mapa, odakle su podaci i šta znače oznake.', 'map'),
                  ('doprinos', 'Prijave, ocene i fotografije', 'Kako da javite stanje punjača i šta se objavljuje.', 'star'),
                  ('aplikacija', 'Aplikacija i privatnost', 'Android, iPhone i računar, ažuriranja i vaši podaci.', 'phone'),
                  ('firme-i-ispravke', 'Firme, ispravke i kontakt', 'Ispravke, podaci firmi i mreža, ko stoji iza sajta.', 'firm')]
POMOC_TOP = ['/pomoc/kako-radi-mapa/', '/pomoc/sta-znaci-potvrdjeno/', '/pomoc/punjac-ne-radi/', '/pomoc/cene-javnog-punjenja/',
             '/pomoc/android-aplikacija-apk/', '/pomoc/kontakt/']
HELP = {}
for mdf in sorted(glob.glob(str(ROOT / 'content' / 'pomoc' / '*.md'))):
    meta, body = front_matter(mdf)
    hp = meta['path']
    assert re.fullmatch(r'/pomoc/[a-z0-9-]+/', hp) and meta.get('section') in {x[0] for x in POMOC_SECTIONS}, mdf
    assert not re.search(r'\[ODLUKA|\[PROVERITI', body), f'{mdf}: an open decision marker'
    # text that depends on the accounts and the newsletter (RUNBOOK 3.27): the markers of posthog_blocks, lead_nalog and
    # description_nalog; the page then shows the day the feature went live as its update
    _on = {'nalog': ACCOUNTS_SINCE if ACCOUNTS else '', 'pregled': PREGLED_SINCE if PG['on'] else ''}
    _on['posta'] = min((d for d in _on.values() if d), key=lambda x: x.split('.')[::-1], default='')
    _since = [d for k, d in _on.items() if d and re.search(rf'<!--(no)?{k}-->', body)]
    for _k in ('lead', 'description'):
        if ACCOUNTS and meta.get(_k + '_nalog'):
            meta[_k] = meta[_k + '_nalog']
            _since.append(ACCOUNTS_SINCE)
    body = posthog_blocks(body)
    if _since and meta.get('updated'):
        meta['updated'] = _later(meta['updated'], max(_since, key=lambda x: x.split('.')[::-1]))
        meta['modified'] = max(meta.get('modified') or '', iso(meta['updated']))
    HELP[hp] = {'meta': meta, 'body': body, 'path': hp, 'h1': meta.get('h1') or meta['title'], 'lead': meta.get('lead', ''),
                'order': int(meta.get('order', 50))}
_SEC_ICON = {k: icon for k, _, _, icon in POMOC_SECTIONS}


def help_shots(h):
    """[[shot:id | alt]] -> the screenshot at its natural size (saved at double density by scripts/pomoc_shots.py), with
    the alt text as the caption; nothing while the picture is missing."""
    def rep(m):
        name, alt = 'pomoc-' + m.group(1), html.unescape(m.group(2).strip())
        if name not in IMGS:
            return ''
        css = IMG_SIZE[name][0] // 2
        f = str(fig_html(name, alt, caption=alt, sizes=f'(max-width: {css + 40}px) calc(100vw - 40px), {css}px', cls='shot'))
        return f.replace('<figure class="fig shot">', f'<figure class="fig shot" style="max-width:{css}px">', 1)
    return re.sub(r'<p>\[\[shot:([\w-]+)\s*\|\s*(.*?)\]\]</p>', rep, h, flags=re.S)


for hp, a in HELP.items():
    meta = dict(a['meta'], h1=a['h1'])
    rel = [HELP[x.strip()] for x in meta.get('related', '').split(',') if x.strip() in HELP and x.strip() != hp]
    sec_name = next(n for k, n, _, _ in POMOC_SECTIONS if k == meta['section'])
    render('pomoc.html', hp, meta=meta, body=help_shots(md_to_html(a['body'])), related=rel, sec_name=sec_name, section='',
           title=meta['title'] + ' | BlokVolt', description=meta.get('description', ''))
    add_url(hp, '0.5', meta.get('modified', ISO_TODAY))
_groups = [(k, n, d, icon, sorted([a for a in HELP.values() if a['meta']['section'] == k], key=lambda x: x['order']))
           for k, n, d, icon in POMOC_SECTIONS]
render('pomoc_hub.html', '/pomoc/', h1='Pomoć', section='',
       lead='Kako se koristi mapa punjača, šta znače oznake, kako da javite da punjač ne radi, aplikacija i privatnost.',
       sections=POMOC_SECTIONS, groups=_groups, all_items=[a for g in _groups for a in g[4]],
       top=[dict(HELP[x], icon=_SEC_ICON[HELP[x]['meta']['section']]) for x in POMOC_TOP if x in HELP],
       title='Pomoć: mapa punjača, prijave, aplikacija i ispravke | BlokVolt',
       description='Odgovori na pitanja o mapi punjača BlokVolt: šta znači „Potvrđeno“, cene po minutu, kako da javite kvar, Android aplikacija, privatnost i ispravke.')
add_url('/pomoc/', '0.6')

# ---------------------------------------------------------------- news (/vesti/)
# content/vesti/YYYY-MM-DD-<slug>.md, one file per news item (docs/RUNBOOK.md 3.15, docs/NEWS_STYLE.md).
# Front matter: title, lead, description (optional, else the lead), date (DD.MM.YYYY: the day the news happened, shown),
# published (YYYY-MM-DD: the day the item went online; JSON-LD, RSS), modified (optional), tag (key of NEWS_TAGS),
# sources (label :: url | …), related (site paths, " | ").
NEWS_TAGS = {'subvencije': 'Subvencije', 'punjaci': 'Punjači', 'cene': 'Cene', 'modeli': 'Modeli', 'propisi': 'Propisi',
             'struja': 'Struja', 'statistika': 'Statistika', 'region': 'Region'}
PAGE_NAMES = {'/mapa/': ('Mapa punjača', 'Javni punjači u Srbiji, sa cenom i snagom.'),
              '/javno-punjenje/': ('Javno punjenje', 'Cene po mrežama, po minutu i po kWh.'),
              '/javno-punjenje/putevi-srbije/': ('Državni punjači na autoputevima', 'Spisak, snaga i stanje po lokaciji.'),
              '/firme/': ('Firme za kućni punjač', 'Ko prodaje i ugrađuje punjač i po kojoj ceni.'),
              '/alati/kalkulator-troskova/': ('Kalkulator troškova', 'Koliko košta 100 km: kuća, javni punjač, benzin.'),
              '/gradovi/novi-sad/': ('Punjači u Novom Sadu', 'Javni punjači i firme za ugradnju u Novom Sadu.'),
              '/gradovi/nis/': ('Punjači u Nišu', 'Javni punjači i firme za ugradnju u Nišu.')}
NEWS_PER_PAGE = 20


def _iso_date(d):
    p_ = (d or '').split('.')
    return f'{p_[2]}-{p_[1]}-{p_[0]}' if len(p_) >= 3 else ISO_TODAY


def _sr_date(iso_):
    y, m, d = iso_.split('-')
    return f'{d}.{m}.{y}'


def page_link(path):
    """Title and one line for a link to one of our pages (news 'related' and home)."""
    href = canon_of(path)
    a = ARTICLES.get(path) or ARTICLES.get(path.rstrip('/') + '.html')
    if a:
        return {'href': href, 'name': a['h1'], 'desc': clip(a['lead'], 110)}
    name, desc = PAGE_NAMES.get(path, (path, ''))
    return {'href': href, 'name': name, 'desc': desc}


NEWS = []
for _mdf in sorted(glob.glob(str(ROOT / 'content' / 'vesti' / '*.md'))):
    _meta, _body = front_matter(_mdf)
    _slug = re.sub(r'^\d{4}-\d{2}-\d{2}-', '', Path(_mdf).stem)
    _iso = _iso_date(_meta.get('date'))
    _pub = _meta.get('published') or _iso
    NEWS.append({'slug': _slug, 'url': f'/vesti/{_slug}/', 'title': _meta['title'], 'lead': _meta.get('lead', ''),
                 'description': _meta.get('description') or _meta.get('lead', ''), 'date': _meta.get('date', ''), 'iso': _iso,
                 'published': _pub, 'published_sr': _sr_date(_pub), 'modified': _meta.get('modified') or _pub,
                 'tag': _meta.get('tag', ''), 'tag_label': NEWS_TAGS.get(_meta.get('tag', ''), ''),
                 'sources': sources_of(_meta), 'related': [page_link(x.strip()) for x in (_meta.get('related') or '').split(' | ') if x.strip()],
                 'body': md_to_html(_body), 'meta': _meta})
assert len({n['slug'] for n in NEWS}) == len(NEWS), 'two news items share a slug'
# photo: front matter `image:` (a name from content/data/foto.json), else one from the tag's pool. Pool photos are
# handed out oldest item first, skipping the photos of the three items before, so older items keep theirs.
NEWS.sort(key=lambda n: (n['iso'], n['published'], n['slug']))
_recent = []
for _n in NEWS:
    _own = (_n['meta'].get('image') or '').strip()
    if _own:
        assert _own in FOTO['photos'], f"news {_n['slug']}: image {_own} is not in content/data/foto.json"
        _n['img'] = _own
    else:
        _pool = FOTO['pools'].get(_n['tag']) or FOTO['pools']['default']
        _k = int(hashlib.md5(_n['slug'].encode()).hexdigest(), 16) % len(_pool)
        _n['img'] = next((_pool[(_k + j) % len(_pool)] for j in range(len(_pool)) if _pool[(_k + j) % len(_pool)] not in _recent[-3:]), _pool[_k])
    _n['img_alt'] = (_n['meta'].get('image_alt') or '').strip() or FOTO['photos'][_n['img']]['alt']
    _n['img_cap'] = photo_caption(_n['img'])
    _recent.append(_n['img'])
NEWS.sort(key=lambda n: (n['iso'], n['published'], n['slug']), reverse=True)
for _i, _n in enumerate(NEWS):
    others = [x for x in NEWS if x is not _n]
    render('vest.html', _n['url'], n=_n, body=_n['body'], sources=_n['sources'], related=_n['related'], latest=others[:3], section='vesti',
           oglas=oglas_za(_n['url'], ' '.join((_n['title'], _n['lead'], _n['body']))),
           title=f"{_n['title']} | BlokVolt", description=clip(_n['description'], 158))
    add_url(_n['url'], '0.5', _n['modified'])
_pages = [NEWS[i:i + NEWS_PER_PAGE] for i in range(0, len(NEWS), NEWS_PER_PAGE)] or [[]]
for _pi, _items in enumerate(_pages, start=1):
    _url = '/vesti/' if _pi == 1 else f'/vesti/strana/{_pi}/'
    render('vesti_index.html', _url, items=_items, page_no=_pi, pages=len(_pages), section='vesti', oglas=oglas_za(_url, ' '.join(x['title'] + ' ' + x['lead'] for x in _items)),
           prev_url=(None if _pi == 1 else ('/vesti/' if _pi == 2 else f'/vesti/strana/{_pi - 1}/')),
           next_url=(f'/vesti/strana/{_pi + 1}/' if _pi < len(_pages) else None), tags=NEWS_TAGS,
           title=('Vesti o električnim automobilima u Srbiji: subvencije, punjači, cene | BlokVolt' if _pi == 1 else f'Vesti, strana {_pi} | BlokVolt'),
           description='Kratke vesti za vozače i kupce električnih automobila u Srbiji: subvencije, novi punjači, cene punjenja i struje, modeli i propisi. Uz svaku vest izvor.')
    add_url(_url, '0.7' if _pi == 1 else '0.3', NEWS[0]['modified'] if NEWS else ISO_TODAY)


def rss_date(iso_):
    import datetime as _dt
    return _dt.datetime.strptime(iso_, '%Y-%m-%d').strftime('%a, %d %b %Y 09:00:00 +0200')


def _x(s):
    return html.escape(str(s), quote=True)


_rss = ['<?xml version="1.0" encoding="UTF-8"?>', '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">', '<channel>',
        '<title>BlokVolt — vesti o električnim automobilima u Srbiji</title>', f'<link>{SITE}/vesti/</link>',
        f'<atom:link href="{SITE}/vesti/rss.xml" rel="self" type="application/rss+xml"/>',
        '<description>Subvencije, punjači, cene punjenja i struje, modeli i propisi. Uz svaku vest izvor.</description>',
        '<language>sr-Latn</language>']
for _n in NEWS[:30]:
    _rss += ['<item>', f"<title>{_x(_n['title'])}</title>", f"<link>{SITE}{_n['url']}</link>", f"<guid isPermaLink=\"true\">{SITE}{_n['url']}</guid>",
             f"<pubDate>{rss_date(_n['published'] if _n['published'] > _n['iso'] else _n['iso'])}</pubDate>",
             f"<description>{_x(_n['lead'])}</description>"] + ([f"<category>{_x(_n['tag_label'])}</category>"] if _n['tag_label'] else []) \
        + [f"<enclosure url=\"{SITE}/assets/og/foto/{_n['img']}.jpg\" length=\"{(ROOT / 'static' / 'assets' / 'og' / 'foto' / (_n['img'] + '.jpg')).stat().st_size}\" type=\"image/jpeg\"/>", '</item>']
_rss += ['</channel>', '</rss>']
(DIST / 'vesti').mkdir(parents=True, exist_ok=True)
(DIST / 'vesti' / 'rss.xml').write_text('\n'.join(_rss) + '\n', encoding='utf-8')

# ---------------------------------------------------------------- firms
for f in published:
    city = f['city_list'][0] if f['city_list'] else None
    cfg = next((c for c in CITY_CFG if c['name'] == city), None)
    if cfg:
        pool = [x for x in published if x is not f and cfg['slug'] in x['grad'].split()]
        sim_title, sim_href = f"Još firmi za {cfg['acc']}", f"/gradovi/{cfg['slug']}/"
    else:
        hub = f['hubs'][0] if f['hubs'] else None
        pool = [x for x in (hub['firms'] if hub else published) if x is not f]
        sim_title, sim_href = ('Slične firme', hub['url'] if hub else '/firme/')
    pool.sort(key=lambda x: (0 if x.get('is_us') else 1, 0 if x['price_val'] else 1, SECTION_ORDER.index(SECTIONS[x['group']]), x['name'].lower()))
    price = f['price_val'] or 'cena na upit'
    render('firma.html', f['url'], firm=f, similar=pool[:4], similar_title=sim_title, similar_href=sim_href,
           title=f"{f['name']}: punjač za električni auto, cena i ugradnja | BlokVolt",
           description=clip(f"{f['name']} ({f['city']}): {price}. Ugradnja: {f['verdicts'].get('ugradnja', 'ne pominje se').lower()}. Podaci sa sajta firme, provereno {f['verified']}.", 158))
    add_url(f['url'], '0.6', f['verified_iso'])

render('firme_index.html', '/firme/', firms=published, groups=grouped(published), CITY_OPTS=CITY_OPTS, TYPE_CHIPS=TYPE_CHIPS,
       count_tpl='Prikazano: {n} od {all}', EXCLUDED=EXCLUDED, crumbs=[],
       title=f"Firme za kućni punjač u Srbiji: {sr_plural(len(published), 'firma', 'firme', 'firmi')}, cene i ugradnja | BlokVolt",
       description=f"Ko u Srbiji prodaje i ugrađuje kućni punjač za električni auto: {sr_plural(len(published), 'firma', 'firme', 'firmi')} sa javnim cenama, ugradnjom i gradovima. Provereno {FIRMS_CHECKED}.")
add_url('/firme/', '0.9')
_WB = json.load(open(ROOT / 'content' / 'data' / 'wallbox-modeli.json', encoding='utf-8'))
for h in TYPE_HUBS:
    _tctx = dict(n=h['n'], n_firms=len(published), checked=FIRMS_CHECKED, n_brands=len(BRAND_INDEX),
                 wb_rows=len(_WB['rows']), wb_models=len({(r['brand'], r['model']) for r in _WB['rows']}))
    _T = (lambda txt: env.from_string(txt).render(**_tctx) if txt else '')
    render('firme_tip.html', h['url'], hub=h, TYPE_HUBS=TYPE_HUBS, firms=h['firms'], groups=grouped(h['firms']), CITY_OPTS=CITY_OPTS,
           TYPE_CHIPS=None, count_tpl='Prikazano: {n} od {all}', lead=_T(h['lead']), intro=_T(h.get('intro')), brand_intro=_T(h.get('brand_intro')),
           BRANDS=BRAND_INDEX if h['rule'] == 'distributer' else None, title=_T(h['title']), description=_T(h['description']))
    add_url(h['url'], '0.7')

NT_HOURS = {x['region']: x['window'] for x in _E['nt_hours']}
for cfg in CITY_CFG:
    city, slug = cfg['name'], cfg['slug']
    local = [f for f in published if city in f['city_list']]
    local_slugs = {f['slug'] for f in local}
    covering = [f for f in published if f['slug'] not in local_slugs and f['group'] in ('A', 'B', 'E') and covers_city(f, cfg)]
    shops = [f for f in published if f['slug'] not in local_slugs and f['group'] in ('C', 'D') and covers_city(f, cfg)]
    xy = TOWN_XY.get(city)
    near = [s for s in MAP['stations'] if xy and map_data.dist_m({'latitude': xy[0], 'longitude': xy[1]}, {'latitude': s['lat'], 'longitude': s['lon']}) <= 15000]
    n_near = len(near)
    per_net = {}
    for s in near:
        if s['net']:
            per_net[s['net']] = per_net.get(s['net'], 0) + 1
    city_ops = []
    for o in operators:
        if o['slug'] in per_net:
            city_ops.append(dict(o, card_short=sr_plural(per_net[o['slug']], 'punjač', 'punjača', 'punjača') + ' na 15 km od centra'))
    n_all = len(local) + len(covering)
    lead = f"Javni punjači, firme za ugradnju kućnog punjača i sati jeftinije struje u {cfg['loc']}."
    render('grad.html', f'/gradovi/{slug}/', city=city, cfg=cfg, firms=local, covering=covering, shops=shops, city_ops=city_ops,
           n_map=n_near, nt=NT_HOURS.get(cfg['nt_region'], ''), lead=lead,
           title=f"Punjač za električni auto u {cfg['loc']}: javni punjači i firme | BlokVolt",
           description=f"{city}: {sr_plural(n_near, 'javni punjač', 'javna punjača', 'javnih punjača')} na mapi, {sr_plural(n_all, 'firma', 'firme', 'firmi')} za ugradnju kućnog punjača, niža tarifa EPS-a {NT_HOURS.get(cfg['nt_region'], '')}.")
    add_url(f'/gradovi/{slug}/', '0.6')

# price guide for home chargers (neutral: every firm with a published price, same rules)
def price_num(f):
    """Published price as a number for sorting only (EUR at 117,2; '+ PDV' and 'bez PDV' + 20 %)."""
    v = f.get('price_val') or ''
    m_ = re.search(r'\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?', v)
    if not m_:
        return 10 ** 9
    x = float(m_.group(0).replace('.', '').replace(',', '.'))
    if '€' in v:
        x *= 117.2
    if '+ PDV' in v or 'bez PDV' in v:
        x *= 1.2
    return x


_priced = sorted([f for f in published if f['price_val'] and f['group'] in ('A', 'B', 'C', 'E')], key=lambda f: (0 if f.get('is_us') else 1, price_num(f)))
_dev11 = []
for f in published:
    if f['group'] in ('B', 'C') and '11 kW' in (f.get('price_headline') or '') and 'PDV' not in f['price_val'] and 'RSD' in f['price_val']:
        m_ = re.match(r'([\d.]+)', f['price_val'])
        if m_:
            _dev11.append(int(m_.group(1).replace('.', '')))
CENA_STATS = [
    {'b': f"od {sr_num(min(_dev11))} RSD" if _dev11 else '—', 't': 'uređaj od 11 kW u prodavnici, bez ugradnje'},
    {'b': '95.000–130.000 RSD', 't': 'punjač 11 kW sa standardnom ugradnjom, javne cene firmi'},
    {'b': '12.000–35.000 RSD', 't': 'sama ugradnja, kad uređaj kupite posebno'},
]
render('cena_punjaca.html', '/cena-punjaca-za-elektricni-auto.html', h1='Koliko košta kućni punjač',
       lead='Uređaj u prodavnici, punjač sa ugradnjom i sama ugradnja: javne cene firmi u Srbiji, na jednom mestu.',
       stats=CENA_STATS, firms=_priced, groups=grouped(_priced), CITY_OPTS=CITY_OPTS, TYPE_CHIPS=None, count_tpl='Prikazano: {n} od {all}',
       install_note='Električar iz Niša objavljuje 12.000–20.000 RSD za ugradnju. Vodič firme PupinEnergy navodi tipično 15.000–35.000 RSD, a STASANET kabliranje „od 150 €“. Cenu najviše menja dužina kabla do table.',
       src_items=[s for f in published if f['slug'] in ('stasanet', 'evolako', 'elektricar-nis', 'pupinenergy') for s in f['src_items']],
       checked_iso=iso(FIRMS_CHECKED),
       title='Cena punjača za električni auto u Srbiji 2026: uređaj, ugradnja, firme | BlokVolt',
       description=f"Kućni punjač 11 kW: uređaj od {sr_num(min(_dev11)) if _dev11 else '40.000'} RSD, sa ugradnjom 95.000–130.000 RSD, sama ugradnja 12.000–35.000 RSD. Javne cene firmi, provereno {FIRMS_CHECKED}.")
add_url('/cena-punjaca-za-elektricni-auto', '0.9', iso(FIRMS_CHECKED))

# ---------------------------------------------------------------- public charging pages
for o in operators:
    render('operator.html', o['url'], op=o, title=f"{o['name']}: javno punjenje, cene i uslovi | BlokVolt",
           description=clip(f"{o['name']}: {o['lead']} {o['card']}. Provereno {o['verified']}.", 158))
    add_url(o['url'], '0.6', o['verified_iso'])

MONTHS_SR = ['januar', 'februar', 'mart', 'april', 'maj', 'jun', 'jul', 'avgust', 'septembar', 'oktobar', 'novembar', 'decembar']
MONTHS_SR_GEN = ['januara', 'februara', 'marta', 'aprila', 'maja', 'juna', 'jula', 'avgusta', 'septembra', 'oktobra', 'novembra', 'decembra']
ARCHIVE = []
for _p in sorted((ROOT / 'content' / 'javno' / 'indeks-arhiva').glob('*.json')):
    _a = json.load(open(_p, encoding='utf-8'))
    _y, _m = _a['month'].split('-')
    _a['label'] = f'{MONTHS_SR[int(_m) - 1]} {_y}'
    _a['label_gen'] = f"{MONTHS_SR_GEN[int(_m) - 1]} {_y}"
    _a['url'] = f"/javno-punjenje/cene/{_a['month']}/"
    for row in _a['rows']:
        row['source'] = clean_src(row.get('source', ''))
        if not row.get('free'):
            row['kwh_html'] = kwh_text(row)
    ARCHIVE.append(_a)
PRICE_HISTORY = None
if len(ARCHIVE) >= 2:
    ARCHIVE[-1]['url'] = '/javno-punjenje/#cene'

    def _key(r):
        # a row whose place list or charger label was reworded keeps its old key ("where|charger") for the comparison
        if r.get('key'):
            w, c = r['key'].split('|')
            return (r['op'], w, c)
        return (r['op'], r.get('where', ''), r.get('charger', ''))

    def _unit(r):
        if r.get('free'):
            return 'free'
        return next((k for k in ('rsd_min', 'rsd_kwh', 'rsd_hour', 'unit_rsd') if r.get(k)), None)

    def _val(r):
        v = r.get(_unit(r)) if _unit(r) not in (None, 'free') else None
        return float(v[0] if isinstance(v, list) else v) if v else None
    _shown = ARCHIVE[-3:]
    _keys = []
    for _a in _shown:
        for r in _a['rows']:
            if not r.get('rsd_total') and _key(r) not in _keys:
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
    _lines.sort(key=lambda l: {'yes': 0, 'ask': 1, 'no': 2}[l['cls']])
    PRICE_HISTORY = {'shown': _shown, 'lines': _lines, 'n_changed': sum(1 for l in _lines if l['cls'] == 'yes')}
    for i, _a in enumerate(ARCHIVE[:-1]):
        render('javno_snimak.html', _a['url'], snap=_a, newer=ARCHIVE[i + 1], older=ARCHIVE[i - 1] if i else None,
               title=f"Cene javnog punjenja u Srbiji — {_a['label']} (arhiva) | BlokVolt",
               description=f"Arhivski snimak cena javnog punjenja za {_a['label']}: tarife iz aplikacija mreža, računi i besplatni punjači, sa računicom po kWh. Snimljeno {_a['captured']}.")
        add_url(_a['url'], '0.4', iso(_a['captured']))
    render('javno_istorija.html', '/javno-punjenje/cene/', archive=ARCHIVE, hist=PRICE_HISTORY,
           title='Istorija cena javnog punjenja u Srbiji po mesecima | BlokVolt',
           description=f"Kako su se menjale cene javnog punjenja u Srbiji od {ARCHIVE[0]['label_gen']}: mesečni snimci i šta je poskupelo ili pojeftinilo.")
    add_url('/javno-punjenje/cene/', '0.6')

render('javno_index.html', '/javno-punjenje/', ops=operators, index=price_index, hist=PRICE_HISTORY, kwh_range=KWH_RANGE,
       putevi_n=PUTEVI_N, putevi_run=PUTEVI_RUN, putevi_verb=PUTEVI_VERB, nt_green=NT_GREEN, nt_blue=NT_BLUE, PRICE_SUMMARY=PRICE_SUMMARY, PRICE_DATE=PRICE_DATE,
       title='Javno punjenje u Srbiji: cene po mrežama i besplatni punjači | BlokVolt',
       description=f"Koliko košta javno punjenje u Srbiji: Charge&GO, Orion eMobility i druge mreže, cena po minutu i po kWh, besplatni državni punjači na autoputevima. Provereno {price_index['updated']}.")
add_url('/javno-punjenje/', '0.9')

render('mapa.html', '/mapa/', M=M, PRICE_SUMMARY=PRICE_SUMMARY, PRICE_DATE=PRICE_DATE,
       title='Mapa punjača za električne automobile u Srbiji, sa cenama | BlokVolt',
       description=f"{MAP['n']} javnih punjača u Srbiji na mapi: mreža, snaga, priključci i cena punjenja. Charge&GO, Orion eMobility, besplatni punjači na autoputevima.")
add_url('/mapa/', '0.9')

# ---------------------------------------------------------------- calculators
_d = CALC['defaults']
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
render('kalkulator.html', '/alati/kalkulator-troskova/', calc=CALC, eps=_E, fuel=CALC['fuel'], public=CALC['public'], d=_d,
       tariff_rows=tariff_rows, home_default=home_default, public_default=public_default, snaga_brutto=snaga_brutto, ex=_ex,
       calc_json=json.dumps(CALC, ensure_ascii=False).replace('</', '<\\/'), modified_iso=iso(CALC['checked']),
       src_items=[{'url': s['url'], 'label': s['label']} for s in _E['sources']] + [{'url': CALC['fuel']['url'], 'label': f"Cene goriva od {CALC['fuel']['date']}"}],
       title='Kalkulator troškova električnog automobila: struja, javni punjači, benzin | BlokVolt',
       description=f"Koliko košta 100 km na struju u Srbiji: kod kuće noću oko {sr_num(tariff_rows[1]['per100'])} RSD (plava zona), na benzinu oko {sr_num(_ex['ice100'])} RSD. Tarife EPS-a i cene goriva od {CALC['fuel']['date']}.")
add_url('/alati/kalkulator-troskova/', '0.9', iso(CALC['checked']))

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
_zex = dict(real=_zreal, real_y=_zreal * 12, per_flat=_zper, per_flat_y=_zper * 12, others_y=_zper * max(0, _zd['stanovi'] - _zd['auta']) * 12,
            gap=_zgap, gap_note='Ostatak i dalje plaćaju svi stanovi.' if _zgap > 0 else 'Paušal tačno pokriva trošak.',
            payback=_zpay, owner=_zper + _zd['pausal'], owner_fair=_zd['kwh_auto'] * _zd['cena_kwh'])
render('kalkulator_zgrada.html', '/alati/racun-u-zgradi/', z=ZG, d=_zd, ex=_zex, section='vodici',
       z_json=json.dumps(ZG, ensure_ascii=False).replace('</', '<\\/'), modified_iso=iso(ZG['checked']), promo_box=PROMO,
       src_items=[{'url': s['url'], 'label': s['label']} for s in ZG['sources']],
       title='Ko koliko plaća punjenje u zgradi: kalkulator zajedničke struje | BlokVolt',
       description=f"Koliko stanari bez automobila plate tuđe punjenje kad je punjač na zajedničkom brojilu: računica po stanu i za koliko se brojilo vrati. Overeno merenje {sr_num(ZG['meter_cost']['low'])}–{sr_num(ZG['meter_cost']['high'])} RSD.")
add_url('/alati/racun-u-zgradi/', '0.8', iso(ZG['checked']))

# ---------------------------------------------------------------- open data
import open_data  # noqa: E402
EV_DATA = json.load(open(ROOT / 'content' / 'data' / 'ev-modeli.json', encoding='utf-8'))
DATASETS = open_data.export_all(DIST, SITE, published, operators, price_index, EV_DATA, _WB, FIRMS_CHECKED)
DL_META = {
    'blokvolt-firme.csv': ('Firme za kućne punjače', f'{sr_plural(len(published), "firma", "firme", "firmi")}: sedište, pokrivenost, brendovi, javna cena, ugradnja, brojilo, sajt i datum provere.'),
    'blokvolt-cene-elektricnih-automobila.csv': ('Cene električnih automobila', 'Modeli sa cenom koju uvoznik objavljuje, cena posle subvencije i link na cenovnik.'),
    'blokvolt-wallbox-modeli.csv': ('Wallbox modeli i cene', 'Cene uređaja kod prodavaca u Srbiji, po modelu i snazi, sa linkom na proizvod.'),
    'blokvolt-javno-punjenje-cene.csv': ('Cene javnog punjenja', 'Tarife i računi sa javnih punjača: po minutu, satu ili „jedinici“, snaga, datum i izvor.'),
    'blokvolt-mreze-javnog-punjenja.csv': ('Mreže javnog punjenja', 'Mreže, aplikacije i domaćini: pokrivenost, plaćanje, roming i podrška.'),
}
for d in DATASETS:
    d['title'], d['desc'] = DL_META[d['name']]
    d['kb'] = round(d['bytes'] / 1024, 1)
if APP.get('apk'):  # the Android app page (docs/RUNBOOK.md 3.20)
    assert (ROOT / 'static' / 'aplikacija' / APP['apk']).stat().st_size == APP['bytes'], 'app.json bytes differ from the APK file'
    render('aplikacija.html', '/aplikacija/', section='', app_mb=sr_num(APP['bytes'] / 1048576, 1), app_iso=_iso_date(APP['released']),
           title='Aplikacija BlokVolt za Android, iPhone i računar | BlokVolt',
           description='BlokVolt kao aplikacija: APK za Android, dodavanje na početni ekran na iPhone-u i instalacija na računaru. Mapa punjača, cene i vesti, i bez interneta.')
    add_url('/aplikacija/', '0.5')
render('preuzimanje.html', '/preuzimanje/', datasets=DATASETS, section='',
       title='Podaci za preuzimanje: CSV tabele o električnim automobilima u Srbiji | BlokVolt',
       description='CSV tabele sa sajta, besplatno uz navođenje izvora: firme za punjače, cene električnih automobila, wallbox modeli, cene javnog punjenja i mreže.')
add_url('/preuzimanje/', '0.5')

# ---------------------------------------------------------------- accounts (/nalog/) and the newsletter (/pregled/)
# docs/RUNBOOK.md 3.27. /nalog/ is personal: always noindex, never in the sitemap; linked from the header only when
# accounts are on. /pregled/ is indexable and in the sitemap only when the newsletter is on; /pregled/potvrda/ and
# /pregled/odjava/ (confirmation, unsubscribing, topics) are always noindex. The data comes from /api (static/assets/nalog.js).
# Model names for the "Moj auto" list, from ev-modeli.json, without the Serbian words some of them carry there
EV_CLEAN = {'Električna G-Klasa (G 580 sa EQ tehnologijom)': 'G 580', 'EQE limuzina': 'EQE', 'EQS limuzina': 'EQS',
            'Proace City Verso Electric (putnički kombi, M1)': 'Proace City Verso Electric', 'Grande Panda (električni)': 'Grande Panda',
            'Cooper E (električni)': 'Cooper E', 'Countryman (električni)': 'Countryman E', 'iX3 (Neue Klasse)': 'iX3'}


def ev_options():
    """[(brand, [(stored value "Brand Model", label "Model")])] for the grouped model list."""
    out = []
    for b in EV_DATA['brands']:
        first, ms = re.split(r'[\s-]', b['brand'])[0].lower(), []
        for m in b['models']:
            label = EV_CLEAN.get(m['model'], re.sub(r'\s*\(električn[ia]\)$', '', m['model']))
            value = label if label.lower().startswith(first) else f"{b['brand']} {label}"
            if value not in (x[0] for x in ms):
                ms.append((value, label))
        out.append((b['brand'], ms))
    return out


_mcfg = json.loads(M['cfg'])
NL_CFG = json.dumps({'api': '/api', **{k: _mcfg[k] for k in ('stations', 'nets', 'extra', 'region')},
                     'names': {k: v.get('name') for k, v in MAP['nets'].items() if v.get('name')}},
                    ensure_ascii=False).replace('</', '<\\/')
render('nalog.html', '/nalog/', noindex=True, section='', NL_CFG=NL_CFG, EV_OPTS=ev_options(), CITY_OPTS=CITY_OPTS,
       title='Moj BlokVolt: omiljeni punjači, auto i podešavanja | BlokVolt',
       description='Nalog na sajtu BlokVolt: omiljeni punjači sa mape na svim uređajima, vaš auto i grad, vaše prijave sa mape. Bez lozinke, prijava kodom na e-mail.')
# the issues: content/pregled/<YYYY-MM-DD>-<slug>.md (format and checks: scripts/pregled.py, docs/RUNBOOK.md 3.27 "Sending
# the issues"). Every issue is a page /pregled/<slug>/ (its sections are what the e-mail is made of, see after the
# translation below). Public — indexable, in the sitemap and under „Prethodni brojevi“ — only with status approved and
# the newsletter on: a draft or a preview is built (the translation memory needs its text, the team looks at it), but
# noindex and linked from nowhere; a stopped issue too. BV_QA_PREGLED_FIXTURE=1 adds the test issue of
# scripts/qa/fixtures/pregled/ (=<status> builds it with that status; approved takes its own hash) — QA builds only.
import pregled as _pg  # noqa: E402
import i18n as _i18n  # noqa: E402
_PG_FILES = [(f, None) for f in sorted(glob.glob(str(ROOT / 'content' / 'pregled' / '*.md')))]
_PG_QA = os.environ.get('BV_QA_PREGLED_FIXTURE', '')
if _PG_QA not in ('', '0'):
    _PG_FILES += [(f, _PG_QA if _PG_QA in _pg.STATUSES else None) for f in sorted(glob.glob(str(ROOT / 'scripts' / 'qa' / 'fixtures' / 'pregled' / '*.md')))]
PG_ISSUES = []
for _mdf, _qa in _PG_FILES:
    _meta, _body = front_matter(_mdf)
    _x = _pg.parse(_mdf, _meta, _body, ROOT, qa_status=_qa)
    for _s in _x['sections']:
        _s['html'] = md_to_html(_s['md'])
        _pg.check_section(_x, _s, _i18n)
    _x['public'] = PG['on'] and _x['status'] == 'approved'
    PG_ISSUES.append(_x)
assert len({x['slug'] for x in PG_ISSUES}) == len(PG_ISSUES), 'two issues of Nedeljni pregled share a slug'
PG_ISSUES.sort(key=lambda x: (x['iso'], x['slug']), reverse=True)
PG_PUBLIC = [x for x in PG_ISSUES if x['public']]
for _x in PG_ISSUES:
    render('pregled_broj.html', _x['path'], x=_x, others=[o for o in PG_PUBLIC if o is not _x][:5], noindex=not _x['public'], section='',
           title=_x['title'] + ' | BlokVolt', description=_x['description'])
    if _x['public']:
        add_url(_x['path'], '0.4', _x['iso'])
render('pregled.html', '/pregled/', noindex=not PG['on'], section='', issues=PG_PUBLIC, PG_MAIL_T=_pg.MAIL_T,
       title='Nedeljni pregled: vesti, cene javnog punjenja i novi punjači na e-mail | BlokVolt',
       description=f"Jednom nedeljno, {PG['dayi']} ujutru: najvažnije vesti o električnim automobilima u Srbiji, promene cena javnog punjenja i novi punjači na mapi. Besplatno, sa izvorima.")
if PG['on']:
    add_url('/pregled/', '0.5')
for _pp, _mode, _t in (('/pregled/potvrda/', 'potvrda', 'Potvrda prijave'), ('/pregled/odjava/', 'odjava', 'Odjava i podešavanja')):
    render('pregled_link.html', _pp, noindex=True, section='', mode=_mode, title=f'Nedeljni pregled: {_t.lower()} | BlokVolt',
           description='Nedeljni pregled BlokVolt: vesti, cene javnog punjenja i novi punjači na e-mail, jednom nedeljno.')

# ---------------------------------------------------------------- home, search, 404
HOME_GUIDES = [
    {'href': '/punjenje-elektricnog-auta-u-zgradi', 'name': 'Punjenje u zgradi', 'desc': 'Šta je dozvoljeno, kada se pita skupština i koliko se štedi.', 'icon': 'building', 'img': 'garaza-wallbox'},
    {'href': '/punjac-u-zgradi-skupstina', 'name': 'Odluka skupštine', 'desc': 'Kojom većinom se odlučuje, sa šablonom odluke.', 'icon': 'doc', 'img': 'skupstina-stanara'},
    {'href': '/ko-placa-struju-za-punjenje', 'name': 'Ko plaća struju', 'desc': 'Brojilo i obračun po ceni sa računa, bez marže.', 'icon': 'coins', 'img': 'brojilo-ugradnja'},
    {'href': '/podaci/tarife-eps/', 'name': 'Cena struje kod kuće', 'desc': 'Zone, tarife i kada počinje jeftinija struja.', 'icon': 'bolt', 'img': 'stambeni-blokovi-sunce'},
    {'href': '/bezbednost-punjenja-atest', 'name': 'Bezbednost i atest', 'desc': 'Zašto ne produžni kabl i šta proverava atest.', 'icon': 'shield', 'img': 'elektricar-atest'},
]
render('home.html', '/', HOME_GUIDES=HOME_GUIDES, NEWS_HOME=NEWS[:3], section='',
       title='BlokVolt: punjači, cene i firme za električne automobile u Srbiji',
       description=f"Mapa sa {MAP['n']} javnih punjača i cenama, {sr_plural(len(published), 'firma', 'firme', 'firmi')} za kućni punjač, cene struje i javnog punjenja, subvencije i vodiči za električni auto u Srbiji.")
add_url('/', '1.0')
# ---------------------------------------------------------------- advertising: the media kit page (RUNBOOK 3.26)
# The PDFs (static/za-firme/blokvolt-medija-kit-sr.pdf, -en.pdf) are the printed page: scripts/medija_kit_pdf.py after a build.
_MK_FILES = {k: (ROOT / 'static' / 'za-firme' / f).exists()
             for k, f in (('pdf_sr', 'blokvolt-medija-kit-sr.pdf'), ('pdf_en', 'blokvolt-medija-kit-en.pdf'), ('logo', 'blokvolt-logo.svg'))}
render('oglasavanje.html', '/za-firme/oglasavanje/', section='', crumbs=[('/za-firme/', 'Za firme i mreže')],
       OGL=OGL, MK_FILES=_MK_FILES, n_ops=len(operators), n_region=RG_N, n_news=len(NEWS),
       n_rub={k: len(r.get('putanje', [])) for k, r in OGL['rubrike'].items()},
       title='Oglašavanje na BlokVoltu — medija kit, cene i pravila | BlokVolt',
       description='Medija kit BlokVolta: ko čita sajt, gde stoji oglas, cena po rubrici i šta se ne prodaje. Oglasi su označeni i ne utiču na podatke, redosled ni ocene.')
add_url('/za-firme/oglasavanje/', '0.4')
render('pretraga.html', '/pretraga/', section='', title='Pretraga | BlokVolt',
       description='Pretraga sajta: punjači, firme, cene, vodiči i propisi za električne automobile u Srbiji.')
add_url('/pretraga/', '0.3')
render('article.html', '/404.html', crumbs=[], noindex=True, section='',
       meta={'h1': 'Stranica nije pronađena', 'lead': 'Ta stranica ne postoji ili je premeštena.'},
       body='<p>Probajte <a href="/mapa/">mapu punjača</a>, <a href="/firme/">firme</a>, <a href="/cene/">cene</a> ili <a href="/vodici/">vodiče</a>.</p>'
            '<p lang="en" translate="no">Page not found. Try the <a href="/en/">English home page</a>.</p>'
            '<p lang="ru" translate="no">Страница не найдена. Попробуйте <a href="/ru/">главную страницу на русском</a>.</p>',
       title='Stranica nije pronađena | BlokVolt', description='', sources=[])

# ---------------------------------------------------------------- robots, redirects, headers
# the pages stay open to search engines and AI; the data files of the map, the API and the apps' feed are not for crawlers
# (punjaci.json, the open ODbL data set, stays allowed). docs/RUNBOOK.md 3.28
(DIST / 'robots.txt').write_text(f'User-agent: *\nAllow: /\nAllow: /assets/map/punjaci.json\nDisallow: /assets/map/\nDisallow: /api/\n'
                                 f'Disallow: /app/\nSitemap: {SITE}/sitemap.xml\n', encoding='utf-8')
# TDM reservation (W3C TDMRep) for the map data, with the terms as the policy
(DIST / '.well-known').mkdir(exist_ok=True)
(DIST / '.well-known' / 'tdmrep.json').write_text(json.dumps([{'location': '/assets/map/*', 'tdm-reservation': 1, 'tdm-policy': f'{SITE}/politika-privatnosti.html#uslovi'},
                                                              {'location': '/api/*', 'tdm-reservation': 1, 'tdm-policy': f'{SITE}/politika-privatnosti.html#uslovi'}]), encoding='utf-8')
_dir_redirects = ['/vodici', '/firme', '/javno-punjenje', '/mapa', '/cene']
(DIST / '_redirects').write_text('\n'.join([
    '/paketi-i-cene https://www.evolako.rs/paketi-i-cene 301',
    '/proveri-svoju-garazu https://www.evolako.rs/proveri-svoju-garazu 301',
    '/cesta-pitanja https://www.evolako.rs/cesta-pitanja 301',
    '/kontakt https://www.evolako.rs/kontakt 301',
] + [f'{pre}{d} {pre}{d}/ 301' for pre in ('', '/en', '/ru') for d in _dir_redirects]
  + [f'{pre}/podaci {pre}/vodici/ 301' for pre in ('', '/en', '/ru')]
  + [f'{pre}/podaci/ {pre}/vodici/ 301' for pre in ('', '/en', '/ru')] + [
    '/en /en/ 301',
    '/ru /ru/ 301',
    '/alati /alati/kalkulator-troskova/ 302',
    '/alati/ /alati/kalkulator-troskova/ 302',
    '/en/alati /en/alati/kalkulator-troskova/ 302',
    '/en/alati/ /en/alati/kalkulator-troskova/ 302',
    '/ru/alati /ru/alati/kalkulator-troskova/ 302',
    '/ru/alati/ /ru/alati/kalkulator-troskova/ 302',
    '/kalkulator /alati/kalkulator-troskova/ 301',
    '/karta /mapa/ 301',
    '/mapa-punjaca /mapa/ 301',
    'https://blokvolt.rs/* https://www.blokvolt.rs/:splat 301',
]) + '\n', encoding='utf-8')
# _headers (security headers + CSP) is written at the very end, after every HTML file is final (see below)
# API: Cloudflare Pages advanced mode (worker/_worker.js, D1 binding DB); only /api/* invokes it
# the worker's CFG line gets the city slugs (account settings), the newsletter's day and whether it is on (the sender
# works only then) from the content files
_wk, _nw = re.subn(r'^const CFG = \{.*\};$', 'const CFG = ' + json.dumps({'cities': [c['slug'] for c in CITY_CFG], 'day': PG['day'], 'pregled': PG['on']},
                                                                        ensure_ascii=False)
                   + ';   // written by build.py from content/data/gradovi.json and site.json',
                   (ROOT / 'worker' / '_worker.js').read_text(encoding='utf-8'), count=1, flags=re.M)
assert _nw == 1, 'worker/_worker.js: the line "const CFG = {...};" is missing'
(DIST / '_worker.js').write_text(_wk, encoding='utf-8')
(DIST / '_routes.json').write_text(json.dumps({'version': 1, 'include': ['/api/*'], 'exclude': []}), encoding='utf-8')


# ---------------------------------------------------------------- search index
def build_search(prefix=''):
    idx = []
    base = DIST / prefix.strip('/') if prefix else DIST
    for f in sorted(base.rglob('*.html')):
        rel = '/' + str(f.relative_to(DIST)).replace('\\', '/')
        if not prefix and rel.startswith(('/en/', '/ru/')):
            continue
        if rel in (f'{prefix}/404.html', f'{prefix}/pretraga/index.html'):
            continue
        url = rel[:-len('index.html')] if rel.endswith('/index.html') else rel[:-5] if rel.endswith('.html') else rel
        soup = BeautifulSoup(f.read_text(encoding='utf-8'), 'html.parser')
        # pages that search engines must not list are not in the site search either (/nalog/, /admin/, /offline, …)
        if soup.find('meta', attrs={'name': 'robots', 'content': re.compile('noindex')}):
            continue
        t = (soup.title.string or '').split(' | ')[0].strip() if soup.title else ''
        h1 = soup.find('h1')
        d = (soup.find('meta', attrs={'name': 'description'}) or {}).get('content', '')
        crumbs = soup.select('.crumbs a')
        sec = crumbs[-1].get_text(' ', strip=True) if len(crumbs) > 1 else ''
        main = soup.find('main') or soup
        for junk in main.find_all(['script', 'style', 'nav', 'noscript']):
            junk.decompose()
        for junk in main.select('aside.oglas'):          # ads are not page content: never in search
            junk.decompose()
        for junk in main.select('[data-only]'):
            if junk['data-only'] != (prefix.strip('/') or 'sr'):
                junk.decompose()
        h = ' · '.join(x.get_text(' ', strip=True) for x in main.find_all(['h2', 'h3', 'summary'])[:16])
        body = re.sub(r'\s+', ' ', main.get_text(' ', strip=True))
        idx.append({'u': url, 't': h1.get_text(' ', strip=True) if h1 else t, 'd': clip(d, 200), 's': sec, 'h': h[:400], 'b': body[:1200]})
    name = 'search.json' if not prefix else f'search-{prefix.strip("/")}.json'
    p = DIST / 'assets' / name
    p.write_text(json.dumps(idx, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    return len(idx), p.stat().st_size // 1024


_n, _kb = build_search()
print(f'search index: {_n} pages, {_kb} KB')

# ---------------------------------------------------------------- English and Russian (scripts/i18n.py)
import i18n as _i18n  # noqa: E402
import region_pages as _region  # noqa: E402
_i18n.EXTRA_ALTS = _region.rs_alternates()   # the same topic in Croatian, Bosnian and Montenegrin on blokvolt.com
I18N = _i18n.render_all(DIST)


def map_tx():
    """/assets/map/tx.json: English and Russian of the Serbian texts in the map data (notes, labels, hours, how to find
    the charger), from the same translation memory as the map on /en/ and /ru/. The map on evolako.rs reads it through
    files.map.tx of the app feed (RUNBOOK 3.25); without it the notes added after its script was written stay Serbian."""
    texts = set(_tx)
    for n in MAP['nets'].values():
        for t in n.get('tiers', []) + n.get('places', []):
            texts.update(x for x in (t.get('label'),) if x and re.search('[a-zčćžšđ]{3}', x.lower()))
    out = {}
    for lang in _i18n.LANGS:
        tm, d = _i18n.load_tm(lang), {}
        for s in sorted(texts):
            key, nums = _i18n.make_key(html.escape(s, quote=False))
            if tm.get(key) is not None:
                d[s] = html.unescape(_i18n.fill(tm[key], nums))
        out[lang] = d
    (DIST / 'assets' / 'map' / 'tx.json').write_text(json.dumps(out, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    miss = len(texts) - min(len(v) for v in out.values())
    print(f'map tx.json: {len(texts)} texts, ' + ', '.join(f'{k} {len(v)}' for k, v in out.items()) + (f' ({miss} without a translation)' if miss else ''))


map_tx()


def strip_lang_only():
    """<… data-only="ru"> exists only on the Russian page (e.g. links to Russian-language guides); written in the
    Serbian source with translate="no", removed from the Serbian and English pages after translation."""
    n = 0
    for f in DIST.rglob('*.html'):
        t = f.read_text(encoding='utf-8')
        if 'data-only=' not in t:
            continue
        rel = '/' + str(f.relative_to(DIST)).replace('\\', '/')
        lang = rel[1:3] if rel[:4] in ('/en/', '/ru/') else 'sr'
        s = BeautifulSoup(t, 'html.parser')
        for el in s.select('[data-only]'):
            if el['data-only'] != lang:
                el.decompose()
                n += 1
            else:
                del el['data-only']
        f.write_text(str(s), encoding='utf-8')
    return n


print('language-only blocks removed:', strip_lang_only())
for _l in _i18n.LANGS:
    _st = I18N.stats[_l]
    _n, _kb = build_search('/' + _l)
    print(f'i18n {_l}: {_st["hit"]} segments translated, {_st["miss"]} left in Serbian ({len(_st["missing"])} distinct); search {_n} pages, {_kb} KB')
# the issue e-mails, from the finished Serbian, English and Russian issue pages (scripts/pregled.py): dist/pregled-mail/,
# read only by the worker (env.ASSETS); noindex (_headers below), in no sitemap or search
for _line in _pg.build(DIST, SITE, PG_ISSUES, I18N.tm, _i18n):
    print(_line)
print(f'pregled: {len(PG_ISSUES)} issues, {len(PG_PUBLIC)} public')

# ---------------------------------------------------------------- sitemap with language alternates
sm = ['<?xml version="1.0" encoding="UTF-8"?>',
      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
for u, p, lm in urls:
    path = u[len(SITE):]
    langs = ['sr'] + (list(_i18n.LANGS) if I18N.is_page(path) else [])
    alts = ''
    if len(langs) > 1:
        alts = ''.join(f'<xhtml:link rel="alternate" hreflang="{_i18n.HREFLANG[l]}" href="{SITE}{_i18n.lang_url(path, l)}"/>' for l in langs)
        alts += ''.join(f'<xhtml:link rel="alternate" hreflang="{c}" href="{h}"/>' for c, h in _i18n.EXTRA_ALTS.get(path, []))
        alts += f'<xhtml:link rel="alternate" hreflang="x-default" href="{u}"/>'
    for l in langs:
        sm.append(f'<url><loc>{SITE}{_i18n.lang_url(path, l)}</loc><lastmod>{lm}</lastmod><priority>{p}</priority>{alts}</url>')
sm.append('</urlset>')
(DIST / 'sitemap.xml').write_text('\n'.join(sm), encoding='utf-8')

# ---------------------------------------------------------------- cache busting (/assets/* is cached for a year)
_ver_map = {a: _ver(DIST / 'assets' / a) for a in ('bv.css', 'bv.js', 'map.js', 'nalog.js')}
_search = json.dumps({'sr': '/assets/search.json?v=' + _ver(DIST / 'assets' / 'search.json'),
                      **{l: f'/assets/search-{l}.json?v=' + _ver(DIST / 'assets' / f'search-{l}.json') for l in _i18n.LANGS}})
for _f in DIST.rglob('*.html'):
    _t = _f.read_text(encoding='utf-8')
    _n = _t
    for _a, _h in _ver_map.items():
        _n = _n.replace(f'"/assets/{_a}"', f'"/assets/{_a}?v={_h}"')
    _n = _n.replace('__SEARCH_URLS__', _search)
    if _n != _t:
        _f.write_text(_n, encoding='utf-8')


# ---------------------------------------------------------------- security headers (docs/RUNBOOK.md 3.17)
# Content-Security-Policy: scripts only from this site, the hashes of our few inline scripts (computed here from the
# final HTML, so a new inline script is allowed automatically), Cloudflare Web Analytics and, when switched on, PostHog.
import base64  # noqa: E402
_INLINE = re.compile(r'<script(?![^>]*\bsrc=)(?![^>]*type="application/(?:ld\+)?json")[^>]*>(.*?)</script>', re.S)
_hashes = set()
for _f in DIST.rglob('*.html'):
    for _m in _INLINE.finditer(_f.read_text(encoding='utf-8')):
        if _m.group(1).strip():
            _hashes.add("'sha256-" + base64.b64encode(hashlib.sha256(_m.group(1).encode('utf-8')).digest()).decode() + "'")
_ph = [_AN['posthog_assets'], _AN['posthog_host']] if ANALYTICS else []
CSP = '; '.join([
    "default-src 'self'",
    "script-src 'self' " + ' '.join(sorted(_hashes)) + ' https://static.cloudflareinsights.com' + (' ' + _ph[0] if _ph else ''),
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: blob: https://tiles.openfreemap.org",
    "font-src 'self'",
    "connect-src 'self' https://tiles.openfreemap.org https://cloudflareinsights.com" + (' ' + ' '.join(_ph) if _ph else ''),
    "worker-src 'self' blob:",
    "child-src 'self' blob:",
    'frame-src https://www.youtube-nocookie.com',
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
    'upgrade-insecure-requests',
])
(DIST / '_headers').write_text('\n'.join([
    '/assets/*',
    '  Cache-Control: public, max-age=31536000, immutable',
    '/*',
    '  X-Content-Type-Options: nosniff',
    '  Referrer-Policy: strict-origin-when-cross-origin',
    '  Strict-Transport-Security: max-age=31536000; includeSubDomains',
    '  X-Frame-Options: DENY',
    '  Cross-Origin-Opener-Policy: same-origin',
    '  Permissions-Policy: geolocation=(self), camera=(), microphone=(), payment=(), usb=(), browsing-topics=()',
    '  Content-Security-Policy: ' + CSP,
    '/admin/*',
    '  X-Robots-Tag: noindex, nofollow',
    '  Cache-Control: no-store',
    '/sw.js',
    '  Cache-Control: no-cache',
    '/manifest.webmanifest',
    '  Content-Type: application/manifest+json',
    '  Cache-Control: public, max-age=3600',
    '/.well-known/assetlinks.json',
    '  Content-Type: application/json',
    '  Access-Control-Allow-Origin: *',
    '  Cache-Control: public, max-age=3600',
    '/offline',
    '  X-Robots-Tag: noindex',
    '/app/*',
    '  Cache-Control: public, max-age=300',
    '  Access-Control-Allow-Origin: *',
    '  X-Robots-Tag: noindex',
    # the map data: the Evolako charger map on evolako.rs reads it with fetch (same as /app/*); not for search engines,
    # and text and data mining is reserved (TDMRep; the open part, punjaci.json, has its own ODbL licence)
    '/assets/map/*',
    '  Access-Control-Allow-Origin: *',
    '  X-Robots-Tag: noindex',
    '  TDM-Reservation: 1',
    f'  TDM-Policy: {SITE}/politika-privatnosti.html#uslovi',
    # the Evolako map script (evomap, RUNBOOK 3.25): evolako.rs loads it with crossorigin + SRI
    '/assets/embed/*',
    '  Access-Control-Allow-Origin: *',
    # the app feed's files (data.json: the fuel price for "Moj auto" on evolako.rs); the apps do not need CORS
    '/assets/app/*',
    '  Access-Control-Allow-Origin: *',
    '  X-Robots-Tag: noindex',
    '/.well-known/tdmrep.json',
    '  Content-Type: application/json',
    '  Cache-Control: public, max-age=3600',
    # the issue e-mails for the sender (the worker reads them through env.ASSETS; RUNBOOK 3.27): never in a search engine
    '/pregled-mail/*',
    '  X-Robots-Tag: noindex, nofollow',
    '  Cache-Control: no-store',
] + ([f'/aplikacija/{APP["apk"]}', '  Content-Type: application/vnd.android.package-archive', '  Content-Disposition: attachment',
      '  Cache-Control: public, max-age=3600'] if APP.get('apk') else [])) + '\n', encoding='utf-8')
print(f'_headers: CSP with {len(_hashes)} inline-script hashes' + (', PostHog on' if ANALYTICS else ''))
# the apps' content feed (/app/v1/manifest.json + /assets/app/v1/…), made from the finished pages (RUNBOOK 3.22)
import app_feed as _app_feed  # noqa: E402
_app_feed.build(DIST)
print('built', len(urls), 'urls;', len(published), 'firms;', len(operators), 'networks;', MAP['n'], 'stations on the map;', len(ARTICLES), 'articles')
