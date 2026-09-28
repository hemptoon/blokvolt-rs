# -*- coding: utf-8 -*-
"""App content feed for the BlokVolt apps (iOS first, Android later): the site's checked texts, numbers and map data
as JSON that the apps render natively, offline, and refresh without a release (docs/RUNBOOK.md 3.22).

build.py calls build(DIST) at the very end, after the /en/ and /ru/ pages exist. Output:

  dist/app/v1/manifest.json                 short cache (5 min): what exists and the version of every file
  dist/assets/app/v1/<lang>/guides.json     the guide groups of /vodici/ and every guide or data page in them
  dist/assets/app/v1/<lang>/news.json       the news (/vesti/), newest first
  dist/assets/app/v1/<lang>/networks.json   public charging networks (/javno-punjenje/<network>/)
  dist/assets/app/v1/<lang>/firms.json      the firm register (/firme/<firm>/): same fields for every firm
  dist/assets/app/v1/<lang>/pages.json      reference pages: public charging, method, about, rules, privacy
  dist/assets/app/v1/data.json              numbers for the native calculators and lists (language-neutral)

Everything under /assets is served with a one-year immutable cache, so the manifest lists every file with ?v=<hash>
(the map files keep their place in /assets/map/ and are listed the same way). The text comes from the finished pages,
so the apps show exactly what the site shows, translations included. A page is cut into blocks:

  h2 · h3 · p · ul · ol · summary (the grey box of key points) · img · table · details (collapsed, with blocks)
  quote · callout (the "Izdvojeno" line) · video (YouTube id) · facts (label/value tiles) · links (rows and tiles)
  doc (a sample document) · note

Inline text is limited Markdown the apps can render directly: **bold**, *italic*, [text](absolute URL), `code`,
and a line break as "\\n". Links stay absolute (https://www.blokvolt.rs/…); the apps open the ones they know
natively (map, guides, networks, firms) and the rest in the browser."""
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag, Comment

ROOT = Path(__file__).resolve().parent.parent
SITE = 'https://www.blokvolt.rs'
LANGS = ('sr', 'en', 'ru')
SCHEMA = 'blokvolt.app/1'
FEED = '/assets/app/v1'
MAP_FILES = ('punjaci', 'mreze', 'cene', 'dopune')
PAGES = ['/javno-punjenje/', '/javno-punjenje/aplikacije-i-kartice/', '/javno-punjenje/besplatni-punjaci/',
         '/javno-punjenje/region/', '/cena-punjaca-za-elektricni-auto', '/metodologija/', '/o-sajtu/',
         '/pravila-objavljivanja/', '/politika-privatnosti']
NEWS_MAX = 40
INLINE_SKIP = {'svg', 'script', 'style', 'button', 'noscript', 'template'}
MD_ESC = re.compile(r'([\\`*_\[\]])')
WS = re.compile(r'[ \t\r\f\v]+')


# ---------------------------------------------------------------- helpers
def _abs(href, page_url):
    if not href:
        return ''
    href = href.strip()
    if href.startswith(('http://', 'https://', 'mailto:', 'tel:')):
        return href
    if href.startswith('//'):
        return 'https:' + href
    if href.startswith('#'):
        return page_url.split('#')[0] + href
    if href.startswith('/'):
        return SITE + href
    return SITE + '/' + href


def _text(el):
    return re.sub(r'\s+', ' ', el.get_text(' ', strip=True)).strip() if el is not None else ''


def _esc(s):
    return MD_ESC.sub(r'\\\1', s)


def md(el, page_url):
    """Inline Markdown of an element: bold, italic, links, code, line breaks; everything else is its text."""
    out = []
    for ch in el.children:
        if isinstance(ch, Comment):
            continue
        if isinstance(ch, NavigableString):
            out.append(_esc(WS.sub(' ', str(ch).replace('\n', ' '))))
            continue
        if not isinstance(ch, Tag) or ch.name in INLINE_SKIP:
            continue
        if ch.name == 'br':
            out.append('\n')
        elif ch.name in ('b', 'strong'):
            inner = md(ch, page_url).strip()
            out.append(f'**{inner}**' if inner else '')
        elif ch.name in ('i', 'em'):
            inner = md(ch, page_url).strip()
            out.append(f'*{inner}*' if inner else '')
        elif ch.name == 'a':
            inner = md(ch, page_url).strip()
            href = _abs(ch.get('href'), page_url)
            out.append(f'[{inner}]({href})' if inner and href else inner)
        elif ch.name == 'code':
            out.append('`' + ch.get_text().replace('`', "'") + '`')
        elif ch.name == 'img':
            continue
        elif ch.name in ('ul', 'ol', 'table', 'figure', 'details'):
            continue  # block content inside inline context is handled by the block walker
        else:
            out.append(md(ch, page_url))
    s = ''.join(out)
    s = re.sub(r' *\n *', '\n', s)
    s = re.sub(r' {2,}', ' ', s)
    s = re.sub(r'\*\*\s*\*\*', '', s)
    return s.strip()


def best_src(img, page_url):
    """The largest srcset candidate up to 1344 px wide (what a phone at 3x needs), else src."""
    cands = []
    for part in (img.get('srcset') or '').split(','):
        bits = part.strip().split()
        if len(bits) == 2 and bits[1].endswith('w'):
            try:
                cands.append((int(bits[1][:-1]), bits[0]))
            except ValueError:
                pass
    if cands:
        cands.sort()
        pick = [c for c in cands if c[0] <= 1344] or cands[:1]
        return _abs(pick[-1][1], page_url)
    return _abs(img.get('src'), page_url)


def img_block(fig, page_url):
    img = fig.find('img')
    if img is None:
        return None
    cap = fig.find('figcaption')
    b = {'t': 'img', 'src': best_src(img, page_url), 'alt': img.get('alt') or ''}
    for k in ('width', 'height'):
        try:
            b['w' if k == 'width' else 'h'] = int(img.get(k))
        except (TypeError, ValueError):
            pass
    if cap is not None:
        c = md(cap, page_url)
        if c:
            b['caption'] = c
    return b


def list_items(ul, page_url):
    items = []
    for li in ul.find_all('li', recursive=False):
        sub = [x for x in li.find_all(['ul', 'ol'], recursive=False)]
        item = {'md': md(li, page_url)}
        if sub:
            item['items'] = [i for s in sub for i in list_items(s, page_url)]
        items.append(item if 'items' in item else item['md'])
    return items


def table_block(t, page_url):
    head, rows = [], []
    thead = t.find('thead')
    trs = t.find_all('tr')
    for i, tr in enumerate(trs):
        cells = tr.find_all(['th', 'td'], recursive=False)
        vals = [md(c, page_url) for c in cells]
        if (thead is not None and tr.find_parent('thead') is thead) or (i == 0 and thead is None and all(c.name == 'th' for c in cells)):
            head = vals
        else:
            rows.append(vals)
    b = {'t': 'table', 'rows': rows}
    if head:
        b['head'] = head
    cap = t.find('caption')
    if cap is not None:
        b['caption'] = md(cap, page_url)
    return b


def facts_block(el, page_url):
    items = []
    for f in el.select('.fact'):
        lab, val, small = f.find('span'), f.find('b'), f.find('small')
        it = {'label': _text(lab), 'value': md(val, page_url) if val is not None else ''}
        if small is not None:
            it['note'] = md(small, page_url)
        tone = [c for c in (val.get('class') or []) if c in ('no', 'ok', 'ask', 'yes', 'warn', 'pr')] if val is not None else []
        if tone:
            it['tone'] = tone[0]
        if 'wide' in (f.get('class') or []):
            it['wide'] = True
        items.append(it)
    return {'t': 'facts', 'items': items} if items else None


def links_block(el, page_url, title=None):
    items = []
    for a in el.select('a.row, a.tile, a.st-row, a.card, a.ncard'):
        h = a.find(['h3', 'h4', 'b', 'strong'])
        sub = a.select_one('.sub, .news-meta, p, small')
        img = a.find('img')
        it = {'title': _text(h) or _text(a), 'url': _abs(a.get('href'), page_url)}
        if sub is not None and _text(sub) and _text(sub) != it['title']:
            it['text'] = _text(sub)
        if img is not None and img.get('src'):
            it['img'] = _abs(img.get('src'), page_url)
        items.append(it)
    if not items:
        return None
    b = {'t': 'links', 'items': items}
    if title:
        b['title'] = title
    return b


def video_block(el):
    btn = el.select_one('[data-yt]')
    if btn is None:
        return None
    b = {'t': 'video', 'youtube': btn.get('data-yt')}
    t = el.select_one('.yt-title, .yt-cap, figcaption, .cap')
    if t is not None and _text(t):
        b['title'] = _text(t)
    return b


def stats_block(el):
    items = [{'value': _text(st.find('b')), 'label': _text(st.find('span'))} for st in el.select('.stat')]
    return {'t': 'stats', 'items': items} if items else None


def prices_block(el, page_url):
    """The price cards of /javno-punjenje/: one card per network with its price lines."""
    items = []
    for c in el.select('.pcard'):
        head = c.select_one('.pcard-h')
        a = head.find('a') if head is not None else None
        img = head.find('img') if head is not None else None
        sub = head.find('span', class_=False) if head is not None else None
        subs = [s for s in head.select('div > span')] if head is not None else []
        it = {'name': _text(a) or _text(head.find('b')), 'url': _abs(a.get('href'), page_url) if a is not None else '',
              'rows': [[_text(li.find('span')), _text(li.find('b'))] for li in c.select('ul.pl > li')]}
        if img is not None and img.get('src'):
            it['logo'] = _abs(img.get('src'), page_url)
        if subs:
            it['sub'] = _text(subs[-1])
        note = c.select_one('p.note')
        if note is not None:
            it['note'] = md(note, page_url)
        items.append(it)
    return {'t': 'prices', 'items': items} if items else None


def dl_block(el, page_url):
    items, term = [], None
    for ch in el.children:
        if not isinstance(ch, Tag):
            continue
        if ch.name == 'dt':
            term = _text(ch)
        elif ch.name == 'dd':
            items.append({'term': term or '', 'md': md(ch, page_url)})
            term = None
    return {'t': 'dl', 'items': items} if items else None


def sources_of(det, page_url):
    out = []
    for a in det.select('li a'):
        out.append({'label': _text(a), 'url': _abs(a.get('href'), page_url)})
    for li in det.select('li'):
        if li.find('a') is None and _text(li):
            out.append({'label': _text(li)})
    return out


class Page:
    def __init__(self, soup, url):
        self.soup, self.url = soup, url
        self.sources, self.updated, self.unknown = [], '', []

    def blocks(self, container):
        out = []
        for el in container.children:
            if isinstance(el, Comment):
                continue
            if isinstance(el, NavigableString):
                t = WS.sub(' ', str(el)).strip()
                if t:
                    out.append({'t': 'p', 'md': _esc(t)})
                continue
            if not isinstance(el, Tag) or el.name in INLINE_SKIP:
                continue
            b = self.block(el)
            if b is None:
                continue
            if isinstance(b, list):
                out.extend(b)
            else:
                out.append(b)
        return out

    def block(self, el):
        name, cls = el.name, set(el.get('class') or [])
        if name in ('h2', 'h3', 'h4'):
            t = _text(el)
            if not t:
                return None
            b = {'t': 'h2' if name == 'h2' else 'h3', 'text': t}
            if el.get('id'):
                b['id'] = el.get('id')
            return b
        if name == 'p':
            if 'upd' in cls:
                m = re.search(r'\d{2}\.\d{2}\.\d{4}', _text(el))
                self.updated = m.group(0) if m else _text(el).split('·')[0].strip()
                return None
            if 'claim-min' in cls:
                return {'t': 'note', 'md': md(el, self.url), 'small': True}
            m = md(el, self.url)
            if not m:
                return None
            return {'t': 'note', 'md': m} if 'note' in cls else {'t': 'p', 'md': m}
        if name in ('ul', 'ol'):
            items = list_items(el, self.url)
            return {'t': name, 'items': items} if items else None
        if name == 'blockquote':
            return {'t': 'quote', 'md': md(el, self.url)}
        if name == 'dl':
            return dl_block(el, self.url)
        if name == 'figure':
            if el.select_one('[data-yt]') is not None:
                return video_block(el)
            return img_block(el, self.url)
        if name == 'table':
            return table_block(el, self.url)
        if name == 'details':
            summ = el.find('summary')
            if 'src' in cls:
                self.sources.extend(sources_of(el, self.url))
                return None
            inner = [c for c in el.children if c is not summ]
            wrap = BeautifulSoup('<div></div>', 'html.parser').div
            for c in inner:
                wrap.append(c.__copy__() if isinstance(c, Tag) else NavigableString(str(c)))
            return {'t': 'details', 'summary': _text(summ), 'blocks': self.blocks(wrap)}
        if name == 'div':
            if 'sum' in cls:
                ul = el.find(['ul', 'ol'])
                items = list_items(ul, self.url) if ul is not None else []
                return {'t': 'summary', 'items': items} if items else {'t': 'summary', 'items': [md(el, self.url)]}
            if 'promo' in cls:
                badge = el.select_one('.badge')
                p = el.find('p')
                return {'t': 'callout', 'badge': _text(badge), 'md': md(p if p is not None else el, self.url)}
            if 'facts' in cls:
                return facts_block(el, self.url)
            if 'stats' in cls:
                return stats_block(el)
            if 'pcards' in cls:
                return prices_block(el, self.url)
            if 'ncards' in cls:
                return links_block(el, self.url)
            if cls & {'tw', 'tw2', 'twrap'} or (el.find('table') is not None and len(el.find_all(recursive=False)) == 1):
                t = el.find('table')
                return table_block(t, self.url) if t is not None else None
            if 'yt' in cls or el.select_one('[data-yt]') is not None and not el.find(['p', 'h2', 'h3']):
                return video_block(el)
            if 'bva-doc' in cls:
                return {'t': 'doc', 'blocks': self.blocks(el)}
            if 'sec' in cls:
                return self.section(el)
            if cls & {'rows', 'tiles', 'cards', 'st-list'}:
                return links_block(el, self.url)
            return self.blocks(el)
        if name == 'section':
            return self.section(el) if 'sec' in cls else self.blocks(el)
        if name in ('form', 'nav', 'aside', 'input', 'select', 'label', 'canvas', 'iframe', 'button', 'hr'):
            return None
        m = md(el, self.url)
        if m:
            self.unknown.append(name + '.' + '.'.join(sorted(cls)))
            return {'t': 'p', 'md': m}
        return None

    def section(self, el):
        head = el.select_one('.sec-head h2, .sec-head h3, h2')
        title = _text(head)
        more = el.select_one('.sec-head > a')
        body = []
        for ch in el.children:
            if not isinstance(ch, Tag):
                continue
            if 'sec-head' in (ch.get('class') or []) or ch is head:
                continue
            b = self.block(ch)
            if b is None:
                continue
            body.extend(b if isinstance(b, list) else [b])
        # a related-pages section is a list of links; keep its title on the block
        if len(body) == 1 and body[0].get('t') == 'links':
            body[0]['title'] = title
            if more is not None and more.get('href'):
                body[0]['more'] = {'label': _text(more), 'url': _abs(more.get('href'), self.url)}
            return body[0]
        h = {'t': 'h2', 'text': title}
        if more is not None and more.get('href'):
            h['more'] = {'label': _text(more), 'url': _abs(more.get('href'), self.url)}
        return ([h] if title else []) + body


def parse(path, lang, dist):
    """(soup, url) of a built page in a language, or (None, url) when the page does not exist."""
    rel = path.lstrip('/')
    cands = []
    base = dist if lang == 'sr' else dist / lang
    if rel.endswith('.html'):
        cands = [base / rel]
    elif rel.endswith('/') or rel == '':
        cands = [base / rel / 'index.html']
    else:
        cands = [base / (rel + '.html'), base / rel / 'index.html']
    url = SITE + ('' if lang == 'sr' else '/' + lang) + '/' + re.sub(r'\.html$', '', rel)
    for f in cands:
        if f.exists():
            return BeautifulSoup(f.read_text(encoding='utf-8'), 'html.parser'), url
    return None, url


def page_doc(path, lang, dist, kind):
    soup, url = parse(path, lang, dist)
    if soup is None:
        return None
    can = soup.find('link', rel='canonical')
    if can is not None and can.get('href'):
        url = can.get('href')
    ph = soup.select_one('main .ph')
    main = soup.select_one('main .wrap.main') or soup.select_one('main')
    pg = Page(soup, url)
    doc = {'id': path, 'kind': kind, 'url': url, 'title': _text(ph.find('h1')) if ph is not None else _text(soup.find('h1'))}
    if ph is not None:
        lead = ph.select_one('p.lead')
        if lead is not None:
            doc['lead'] = md(lead, url)
        meta = ph.select_one('.news-meta')
        if meta is not None:
            tm = meta.find('time')
            if tm is not None:
                doc['date'] = tm.get('datetime') or _text(tm)
            spans = [s for s in meta.find_all('span') if not s.get('aria-hidden')]
            if spans:
                doc['tag'] = _text(spans[-1])
        ent = ph.select_one('.ent img')
        if ent is not None and ent.get('src'):
            doc['logo'] = _abs(ent.get('src'), url)
            if 'dark' in (ent.find_parent('span').get('class') or []):
                doc['logoDark'] = True
        acts = []
        for a in ph.select('.ph-actions a'):
            acts.append({'label': _text(a), 'url': _abs(a.get('href'), url)})
        if acts:
            doc['actions'] = acts
    desc = soup.find('meta', attrs={'name': 'description'})
    if desc is not None and desc.get('content'):
        doc['description'] = desc.get('content').strip()
    blocks = []
    if main is not None:
        prose = main.select_one('.prose')
        if prose is not None and prose.parent is main:
            for ch in main.children:
                if not isinstance(ch, Tag):
                    continue
                if ch is prose:
                    blocks.extend(pg.blocks(prose))
                else:
                    b = pg.block(ch)
                    if b is not None:
                        blocks.extend(b if isinstance(b, list) else [b])
        else:
            blocks = pg.blocks(main)
    # the hero image of a guide or a news item comes first in the prose; lift it to the document
    if blocks and blocks[0].get('t') == 'img':
        doc['image'] = blocks.pop(0)
    doc['blocks'] = blocks
    if pg.sources:
        doc['sources'] = pg.sources
    if pg.updated:
        doc['updated'] = pg.updated
    if pg.unknown:
        doc['_unknown'] = sorted(set(pg.unknown))
    return doc


# ---------------------------------------------------------------- collections
def guide_groups(dist, lang):
    soup, url = parse('/vodici/', lang, dist)
    groups = []
    if soup is None:
        return groups
    for sec in soup.select('main .sec'):
        h = sec.select_one('.sec-head h2, h2')
        items = []
        for a in sec.select('a.row, a.tile'):
            href = a.get('href') or ''
            path = re.sub(r'^/(en|ru)(?=/)', '', href)
            it = {'path': path, 'title': _text(a.find('h3')), 'text': _text(a.select_one('.sub'))}
            img = a.find('img')
            if img is not None and img.get('src'):
                it['img'] = _abs(img.get('src'), url)
            items.append(it)
        if items:
            groups.append({'title': _text(h), 'items': items})
    return groups


def guides(dist, lang, paths_sr):
    groups = guide_groups(dist, lang)
    docs = []
    for p in paths_sr:
        kind = 'tool' if p.startswith('/alati/') else ('data' if p.startswith('/podaci/') else 'guide')
        if kind == 'tool':
            soup, url = parse(p, lang, dist)
            docs.append({'id': p, 'kind': 'tool', 'url': url, 'title': _text(soup.find('h1')) if soup is not None else p})
            continue
        d = page_doc(p, lang, dist, kind)
        if d is not None:
            docs.append(d)
    return {'groups': groups, 'items': docs}


def news(dist, lang):
    items = []
    for f in sorted((ROOT / 'content' / 'vesti').glob('*.md'), reverse=True)[:NEWS_MAX]:
        slug = re.sub(r'^\d{4}-\d{2}-\d{2}-', '', f.stem)
        d = page_doc(f'/vesti/{slug}/', lang, dist, 'news')
        if d is not None:
            d['slug'] = slug
            items.append(d)
    items.sort(key=lambda d: d.get('date', ''), reverse=True)
    return {'items': items}


def networks(dist, lang):
    out = []
    for f in sorted((ROOT / 'content' / 'operateri').glob('*.json')):
        o = json.loads(f.read_text(encoding='utf-8'))
        if not o.get('publish', True):
            continue
        d = page_doc(f'/javno-punjenje/{o["slug"]}/', lang, dist, 'network')
        if d is None:
            continue
        d.update({'slug': o['slug'], 'order': o.get('order', 99), 'kindCode': o.get('kind'), 'website': o.get('website') or '',
                  'mapFilter': o['slug']})
        out.append(d)
    out.sort(key=lambda d: (d['order'], d['slug']))
    return {'items': out}


def firms(dist, lang):
    tipovi = json.loads((ROOT / 'content' / 'data' / 'firme-tipovi.json').read_text(encoding='utf-8'))
    out = []
    for f in sorted((ROOT / 'content' / 'firme').glob('*.json')):
        o = json.loads(f.read_text(encoding='utf-8'))
        if not o.get('publish'):
            continue
        d = page_doc(f'/firme/{o["slug"]}/', lang, dist, 'firm')
        if d is None:
            continue
        d.update({'slug': o['slug'], 'featured': bool(o.get('is_us')), 'website': o.get('website') or '',
                  'domain': o.get('domain') or '', 'city': o.get('city') or '', 'coverage': o.get('coverage') or '',
                  'brands': o.get('brands') or [], 'verified': o.get('verified') or '', 'group': o.get('group') or ''})
        kinds = o.get('kind') or []
        d['types'] = kinds if isinstance(kinds, list) else [kinds]
        out.append(d)
    out.sort(key=lambda d: (not d['featured'], d['title'].lower()))
    return {'items': out, 'types': tipovi}


def pages(dist, lang):
    out = []
    for p in PAGES:
        d = page_doc(p, lang, dist, 'page')
        if d is not None:
            out.append(d)
    return {'items': out}


def data_json():
    data = ROOT / 'content' / 'data'
    load = lambda n: json.loads((data / n).read_text(encoding='utf-8'))
    out = {'calculator': load('kalkulator.json'), 'building': load('kalkulator-zgrada.json'),
           'evModels': load('ev-modeli.json'), 'cities': load('gradovi.json')}
    try:
        out['app'] = {k: v for k, v in load('app.json').items() if k in ('version', 'apk', 'size', 'sha256', 'package')}
    except Exception:
        pass
    return out


# ---------------------------------------------------------------- writer
def _write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(obj, ensure_ascii=False, separators=(',', ':'))
    path.write_text(raw, encoding='utf-8')
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()[:10], len(raw.encode('utf-8'))


def build(dist, strict=False):
    dist = Path(dist)
    now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    files, counts, unknown = {}, {}, {}
    sr_groups = guide_groups(dist, 'sr')
    guide_paths = [it['path'] for g in sr_groups for it in g['items']]
    for lang in LANGS:
        colls = {'guides': guides(dist, lang, guide_paths), 'news': news(dist, lang), 'networks': networks(dist, lang),
                 'firms': firms(dist, lang), 'pages': pages(dist, lang)}
        for kind, obj in colls.items():
            for d in obj.get('items', []):
                if '_unknown' in d:
                    unknown.setdefault(d['id'], d.pop('_unknown'))
            obj.update({'schema': SCHEMA, 'lang': lang, 'generated': now})
            h, n = _write(dist / 'assets' / 'app' / 'v1' / lang / f'{kind}.json', obj)
            files.setdefault(kind, {})[lang] = f'{FEED}/{lang}/{kind}.json?v={h}'
            counts.setdefault(kind, len(obj.get('items', [])))
    h, n = _write(dist / 'assets' / 'app' / 'v1' / 'data.json', dict(data_json(), schema=SCHEMA, generated=now))
    files['data'] = f'{FEED}/data.json?v={h}'
    mp = {}
    for m in MAP_FILES:
        f = dist / 'assets' / 'map' / f'{m}.json'
        if f.exists():
            mp[m] = f'/assets/map/{m}.json?v=' + hashlib.sha256(f.read_bytes()).hexdigest()[:10]
    files['map'] = mp
    manifest = {'schema': SCHEMA, 'generated': now, 'site': SITE, 'langs': list(LANGS), 'minApp': {'ios': '1.0', 'android': '1.0'},
                'files': files, 'counts': counts,
                'api': {'stations': '/api/stanice', 'station': '/api/stanica/{id}', 'checkin': '/api/stanica/{id}/prijava',
                        'photo': '/api/stanica/{id}/foto', 'photoFile': '/api/foto/{photo}.jpg', 'report': '/api/prijavi',
                        'request': '/api/zahtev'},
                'links': {'privacy': SITE + '/politika-privatnosti', 'rules': SITE + '/pravila-objavljivanja/',
                          'correction': SITE + '/ispravka/', 'contact': 'mailto:hello@blokvolt.com'}}
    _write(dist / 'app' / 'v1' / 'manifest.json', manifest)
    msg = (f'app feed: {counts.get("guides", 0)} guides, {counts.get("news", 0)} news, {counts.get("networks", 0)} networks, '
           f'{counts.get("firms", 0)} firms, {counts.get("pages", 0)} pages × {len(LANGS)} languages')
    if unknown:
        msg += f'; {len(unknown)} pages with unmapped elements (as text): ' + ', '.join(f'{k} {v}' for k, v in list(unknown.items())[:6])
    print(msg)
    if strict and unknown:
        raise SystemExit('app feed: unmapped elements')
    return manifest


if __name__ == '__main__':
    build(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'dist', strict='--strict' in sys.argv)
