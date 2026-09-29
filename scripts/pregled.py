# -*- coding: utf-8 -*-
"""Nedeljni pregled, the weekly newsletter of www.blokvolt.rs: its issues and their e-mails (docs/RUNBOOK.md 3.27,
"Sending the issues").

An issue is content/pregled/<YYYY-MM-DD>-<slug>.md:

    ---
    title: Charge&GO menja cene, pet novih punjača na autoputu     the page's H1 and the e-mail's subject
    date: 02.10.2026                                              DD.MM.YYYY, the issue's date
    lead: …                                                       under the title; the e-mail's preheader
    cover: /assets/pregled/2026-40.jpg                            JPEG or WebP under static/, >= 600 px wide, < 200 KB
    cover_alt: …
    status: draft                                                 draft | preview | approved | stopped
    send_at: 02.10.2026 08:00                                     Europe/Belgrade; needed from preview on
    approved_hash:                                                empty until the owner approves the preview
    ---
    ## Nedelja u tri rečenice {#uvod}
    …
    ## Vesti {#vesti}
    …

Every section starts with "## <heading> {#<topic>}". The topic is a subscription topic (vesti, cene, punjaci) or uvod,
the intro every reader gets (first, at most once). A second section of one topic takes a suffix: {#vesti-region}.
The topic "moji" (the reader's favourite chargers) is not built yet. Inside a section: paragraphs, ### subheadings,
lists (not nested), quotes, bold, italics, links to https://www.blokvolt.rs/…, https://blokvolt.com/… or a site path
(/mapa/). No pictures: the cover is the only one.

build.py renders every issue as the page /pregled/<slug>/ (templates/pregled_broj.html). After scripts/i18n.py has made
the English and Russian pages, build() reads the three pages back, so every word of the e-mail passes the same
translation memory as the site, and writes dist/pregled-mail/<slug>.json and dist/pregled-mail/index.json. The worker
(POST /api/posta/tick) reads them through env.ASSETS and sends; nothing here sends mail."""
import datetime, hashlib, html, json, re
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString, Tag, Comment

ROOT = Path(__file__).resolve().parent.parent
LANGS = ('sr', 'en', 'ru')
STATUSES = ('draft', 'preview', 'approved', 'stopped')
TOPICS = ('vesti', 'cene', 'punjaci')          # the subscription topics an issue has sections for (the worker's PG_TOPICS)
INTRO = 'uvod'                                 # the intro: every reader gets it
LATER = ('moji',)                              # a subscription topic that issues do not have yet
FIELDS = ('title', 'date', 'lead', 'description', 'cover', 'cover_alt', 'status', 'send_at', 'approved_hash')
REQUIRED = ('title', 'date', 'lead', 'cover', 'cover_alt', 'status')
FILE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}-([a-z0-9](?:[a-z0-9-]{0,58}[a-z0-9])?)\.md$')
HEAD_RE = re.compile(r'^##[ \t]+(.+?)[ \t]+\{#([a-z0-9]+(?:-[a-z0-9]+)*)\}[ \t]*$')
HASH_RE = re.compile(r'^[0-9a-f]{64}$')
COVER_MAX = 200 * 1024        # bytes
COVER_MIN_W = 600             # px: the e-mail shows the cover 600 px wide
MAIL_MAX = 100 * 1024         # bytes of HTML with every section: Gmail clips a message above ~102 KB
# links in an issue: our two sites and site paths; the worker checks the same before it redirects (PG_LINK)
LINK_RE = re.compile(r'^https://(www\.blokvolt\.rs|blokvolt\.com)/[^\s"<>\\]*$')
PATH_RE = re.compile(r'^/(?!/|api/)[^\s"<>\\]*$')
ALLOWED = {'p', 'h3', 'ul', 'ol', 'li', 'a', 'strong', 'b', 'em', 'i', 'br', 'blockquote', 'code', 'sup', 'sub'}
BLOCKS = {'p', 'h3', 'ul', 'ol', 'blockquote'}
OPERATOR = 'BlokVolt · www.blokvolt.rs · hello@blokvolt.com'     # no registered company yet: the site and its address
# the fixed texts of the e-mails: build.py puts them on /pregled/ (<script id="bv-i18n-mail">), so scripts/i18n.py
# translates them like any page text and they are always on the site; {n} and {y}: the ISO week and its year
MAIL_T = {'head': 'Nedeljni pregled · {n}. nedelja {y}', 'web': 'Pročitajte na sajtu',
          'why': 'Primate ovaj mejl jer ste se prijavili na Nedeljni pregled na www.blokvolt.rs.',
          'prefs': 'Teme, učestalost i jezik', 'unsub': 'Odjavite se jednim klikom'}


def fail(path, msg):
    p = Path(path).resolve()
    raise SystemExit(f'{p.relative_to(ROOT) if ROOT in p.parents else p}: {msg}')


def link_ok(href):
    """True for the links an issue may have: https://www.blokvolt.rs/…, https://blokvolt.com/… or a site path."""
    return bool(LINK_RE.match(href) or PATH_RE.match(href))


def belgrade_to_utc(d):
    """A naive date-time in Europe/Belgrade -> aware UTC (the tz database, or the EU summer-time rule without it)."""
    try:
        from zoneinfo import ZoneInfo
        return d.replace(tzinfo=ZoneInfo('Europe/Belgrade')).astimezone(datetime.timezone.utc)
    except Exception:
        def last_sunday(y, m):
            end = (datetime.date(y, m + 1, 1) if m < 12 else datetime.date(y + 1, 1, 1)) - datetime.timedelta(days=1)
            return end - datetime.timedelta(days=(end.weekday() + 1) % 7)
        u = d - datetime.timedelta(hours=1)       # CET; CEST (+2) from the last Sunday of March to the last of October, 01:00 UTC
        start = datetime.datetime.combine(last_sunday(d.year, 3), datetime.time(1))
        end = datetime.datetime.combine(last_sunday(d.year, 10), datetime.time(1))
        if start <= d - datetime.timedelta(hours=2) < end:
            u = d - datetime.timedelta(hours=2)
        return u.replace(tzinfo=datetime.timezone.utc)


def _cover(path, cover, root):
    if not re.fullmatch(r'/[A-Za-z0-9._/-]+\.(jpg|jpeg|webp)', cover) or '..' in cover:
        fail(path, f'cover "{cover}": a site path to a .jpg or .webp file, e.g. /assets/pregled/<slug>.jpg')
    f = Path(root) / 'static' / cover.lstrip('/')
    if not f.is_file():
        fail(path, f'cover: static{cover} does not exist')
    data = f.read_bytes()
    if len(data) >= COVER_MAX:
        fail(path, f'cover: {len(data) // 1024} KB, it must be under {COVER_MAX // 1024} KB')
    jpeg, webp = data[:3] == b'\xff\xd8\xff', data[:4] == b'RIFF' and data[8:12] == b'WEBP'
    if not (jpeg if cover.endswith(('.jpg', '.jpeg')) else webp):
        fail(path, 'cover: the file is not the JPEG or WebP its name says')
    from PIL import Image
    with Image.open(f) as im:
        w, h = im.size
    if w < COVER_MIN_W:
        fail(path, f'cover: {w} px wide, the e-mail needs at least {COVER_MIN_W} (1200 looks sharp on phones)')
    # /assets/ is cached for a year: the version in the address follows the file (and is part of the approved content)
    return {'url': f'{cover}?v={hashlib.sha1(data).hexdigest()[:10]}', 'w': w, 'h': h, 'kb': round(len(data) / 1024)}


def parse(path, meta, body, root, qa_status=None):
    """One issue file (front matter + body, as build.py's front_matter() reads it) -> a dict for the page and the
    e-mail. Stops the build on anything the sender could not handle. qa_status: a QA build's status for a fixture."""
    path = Path(path)
    m = FILE_RE.match(path.name)
    if not m:
        fail(path, 'file name: <YYYY-MM-DD>-<slug>.md, the slug in lower-case letters, digits and hyphens (at most 60)')
    slug = m.group(1)
    unknown = sorted(set(meta) - set(FIELDS))
    if unknown:
        fail(path, 'unknown front matter: ' + ', '.join(unknown) + ' (known: ' + ', '.join(FIELDS) + ')')
    missing = [k for k in REQUIRED if not meta.get(k)]
    if missing:
        fail(path, 'front matter without ' + ', '.join(missing))
    status = qa_status or meta['status']
    if status not in STATUSES:
        fail(path, f'status "{status}": one of ' + ', '.join(STATUSES))
    try:
        date = datetime.datetime.strptime(meta['date'], '%d.%m.%Y').date()
    except ValueError:
        fail(path, f'date "{meta["date"]}": DD.MM.YYYY')
    send_at, send_utc = meta.get('send_at') or '', ''
    if send_at:
        try:
            send_utc = belgrade_to_utc(datetime.datetime.strptime(send_at, '%d.%m.%Y %H:%M')).strftime('%Y-%m-%dT%H:%M:%SZ')
        except ValueError:
            fail(path, f'send_at "{send_at}": DD.MM.YYYY HH:MM, Belgrade time')
    elif status != 'draft':
        fail(path, 'send_at (DD.MM.YYYY HH:MM, Belgrade time) is needed from status preview on')
    ah = (meta.get('approved_hash') or '').strip().lower()
    if ah and not HASH_RE.match(ah):
        fail(path, 'approved_hash: the full 64-character hash of the approved preview, or empty')
    if status == 'approved' and not ah and not qa_status:
        fail(path, 'status approved without approved_hash: copy the hash of the preview the owner approved')
    cover = dict(_cover(path, meta['cover'], root), alt=meta['cover_alt'])
    # sections: "## <heading> {#<topic>}" … up to the next one
    secs, before = [], []
    for line in body.split('\n'):
        hm = re.match(r'^(#{1,6})(?!#)', line)            # Markdown needs no space after the hashes either
        if hm and len(hm.group(1)) <= 2:
            sm = HEAD_RE.match(line)
            if len(hm.group(1)) == 1 or not sm:
                fail(path, f'"{line.strip()}": a section starts with "## <heading> {{#<topic>}}", topics '
                     + ', '.join((INTRO,) + TOPICS))
            heading, sid = sm.group(1).strip(), sm.group(2)
            topic = sid.split('-')[0]
            if topic in LATER:
                fail(path, f'{{#{sid}}}: the topic "{topic}" (a reader\'s favourite chargers) is not built yet')
            if topic not in TOPICS and topic != INTRO:
                fail(path, f'{{#{sid}}}: unknown topic, one of ' + ', '.join((INTRO,) + TOPICS))
            if any(s['id'] == sid for s in secs):
                fail(path, f'{{#{sid}}} is used twice: a second section of a topic takes a suffix, e.g. {{#{topic}-2}}')
            if topic == INTRO and (secs or sid != INTRO):
                fail(path, '{#uvod} is the first section, at most once')
            secs.append({'id': sid, 'topic': topic, 'heading': heading, 'md': []})
        elif secs:
            secs[-1]['md'].append(line)
        else:
            before.append(line)
    if any(x.strip() for x in before):
        fail(path, 'text before the first section: start the body with "## <heading> {#uvod}" or another section')
    if not any(s['topic'] != INTRO for s in secs):
        fail(path, 'no section with a topic (vesti, cene, punjaci): a reader would get only the intro')
    for s in secs:
        s['md'] = '\n'.join(s['md']).strip()
        if not s['md']:
            fail(path, f'section {{#{s["id"]}}} is empty')
    iy, iw, _ = date.isocalendar()
    return {'file': path, 'slug': slug, 'path': f'/pregled/{slug}/', 'title': meta['title'], 'lead': meta['lead'],
            'description': meta.get('description') or meta['lead'], 'date': meta['date'], 'iso': date.isoformat(),
            'month': date.strftime('%Y-%m'), 'week': iw, 'wyear': iy, 'status': status, 'send_at': send_utc,
            'send_at_local': send_at, 'approved_hash': ah, 'cover': cover, 'sections': secs,
            'topics': list(dict.fromkeys(s['topic'] for s in secs if s['topic'] != INTRO)), 'qa': bool(qa_status)}


def check_section(x, sec, i18n):
    """sec['html'] (the section's Markdown as build.py renders it) -> stops the build on what the e-mail cannot carry:
    another tag, a link outside our sites, a nested list, or text that the translation memory would never see (i18n
    translates whole blocks; words outside one would stay Serbian in the English and Russian e-mail)."""
    soup = BeautifulSoup(sec['html'], 'html.parser')
    where = f'section {{#{sec["id"]}}}'
    for el in soup.find_all(True):
        if el.name not in ALLOWED:
            fail(x['file'], f'{where}: <{el.name}> cannot go into the e-mail — paragraphs, ### subheadings, lists, quotes, '
                 'bold, italics and links only; the cover is the only picture')
        if el.name == 'a':
            href = (el.get('href') or '').strip()
            if not link_ok(href):
                fail(x['file'], f'{where}: link "{href}" — only https://www.blokvolt.rs/…, https://blokvolt.com/… and site paths such as /mapa/')
        if el.name == 'li' and el.find(['ul', 'ol']):
            fail(x['file'], f'{where}: a list inside a list — the translation would lose the outer item\'s text')
    roots = {id(r) for r in i18n.segment_roots(soup)}
    for t in soup.find_all(string=True):
        if isinstance(t, Comment) or not t.strip():
            continue
        if not any(id(p) in roots for p in t.parents):
            fail(x['file'], f'{where}: "{t.strip()[:60]}" is outside a paragraph, heading or list item')


# ---------------------------------------------------------------- the e-mail (the style of the worker's mails)
FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"
S = {
    'h1': f'margin:0 0 10px;font:700 26px/1.25 {FONT};color:#0D111A;letter-spacing:-.4px',
    'lead': f'margin:0 0 22px;font:17px/1.55 {FONT};color:#5C6270',
    'h2': f'margin:0 0 12px;font:700 20px/1.3 {FONT};color:#0D111A;letter-spacing:-.2px',
    'h3': f'margin:18px 0 8px;font:700 17px/1.35 {FONT};color:#0D111A',
    'p': f'margin:0 0 14px;font:16px/1.6 {FONT};color:#2A2F3A',
    'a': 'color:#0D111A;font-weight:600;text-decoration:underline',
    'dot': f'padding:2px 10px 2px 0;font:16px/1.6 {FONT};color:#6E8A12',
    'num': f'padding:2px 10px 2px 0;font:700 15px/1.7 {FONT};color:#6E8A12',
    'li': f'padding:2px 0;font:16px/1.6 {FONT};color:#2A2F3A',
    'quote': 'border-left:3px solid #D9D8CF;padding:2px 0 2px 14px',
    'code': 'font:14px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;background:#F4F3EE;border-radius:4px;padding:1px 4px',
    'sec': 'border-top:1px solid #ECEBE3;padding:22px 0 8px',
    'foot': f'padding:18px 8px 0;font:13px/1.55 {FONT};color:#5C6270',
}
esc = html.escape
TABLE = '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"'


class _Mail:
    """One language of one issue. Every link goes through the click counter, numbered in the issue's link table
    (`links`: absolute URL -> n, shared by the three languages)."""

    def __init__(self, site, slug, links):
        self.site, self.slug, self.links = site, slug, links

    def url(self, href):
        u = self.site + href if href.startswith('/') else href
        if not LINK_RE.match(u):
            raise SystemExit(f'pregled {self.slug}: link "{href}" is not on www.blokvolt.rs or blokvolt.com')
        n = self.links.setdefault(u, str(len(self.links) + 1))
        return f'{self.site}/api/posta/klik?i={self.slug}&l={n}'

    def inline(self, node):
        """(html, text) of inline content."""
        if isinstance(node, Comment):
            return '', ''
        if isinstance(node, NavigableString):
            s = re.sub(r'\s+', ' ', str(node))
            return esc(s, quote=False), s
        parts = [self.inline(c) for c in node.children]
        h, t = ''.join(p[0] for p in parts), ''.join(p[1] for p in parts)
        n = node.name
        if n == 'a':
            u = self.url(node['href'].strip())
            return f'<a href="{esc(u)}" style="{S["a"]}">{h}</a>', f'{t} ({u})'
        if n in ('strong', 'b'):
            return f'<b>{h}</b>', t
        if n in ('em', 'i'):
            return f'<i>{h}</i>', t
        if n == 'br':
            return '<br>', '\n'
        if n == 'code':
            return f'<code style="{S["code"]}">{h}</code>', t
        if n in ('sup', 'sub'):
            return f'<{n}>{h}</{n}>', t
        if n in ('h2', 'h3', 'p', 'li'):                          # the content of a block element
            return h.strip(), t.strip()
        raise SystemExit(f'pregled {self.slug}: <{n}> cannot go into the e-mail')

    def blocks(self, nodes):
        """(html, text) of block elements: a section's body, a quote, the paragraphs of a list item."""
        hs, ts = [], []
        for c in nodes:
            if isinstance(c, Comment) or (isinstance(c, NavigableString) and not c.strip()):
                continue
            if not isinstance(c, Tag) or c.name not in BLOCKS:
                raise SystemExit(f'pregled {self.slug}: text outside a paragraph cannot go into the e-mail')
            h, t = self.block(c)
            hs.append(h)
            ts.append(t)
        return ''.join(hs), ''.join(ts)

    def block(self, el):
        n = el.name
        if n in ('p', 'h3'):
            h, t = self.inline(el)
            return f'<{n} style="{S[n]}">{h}</{n}>', t + '\n\n'
        if n in ('ul', 'ol'):
            rows, txt = [], []
            for i, li in enumerate(el.find_all('li', recursive=False), 1):
                h, t = self.blocks(li.children) if any(isinstance(c, Tag) and c.name in BLOCKS for c in li.children) else self.inline(li)
                mark = ('&#9679;', 'dot', '• ') if n == 'ul' else (f'{i}.', 'num', f'{i}. ')
                rows.append(f'<tr><td valign="top" style="{S[mark[1]]}">{mark[0]}</td><td style="{S["li"]}">{h}</td></tr>')
                txt.append(mark[2] + ' '.join(t.split()))
            return (f'<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:0 0 14px">{"".join(rows)}</table>',
                    '\n'.join(txt) + '\n\n')
        if n == 'blockquote':
            h, t = self.blocks(el.children)
            return (f'{TABLE} style="margin:0 0 14px"><tr><td style="{S["quote"]}">{h}</td></tr></table>',
                    ''.join('> ' + line + '\n' for line in t.strip().split('\n')) + '\n')
        raise SystemExit(f'pregled {self.slug}: <{n}> cannot go into the e-mail')

    def render(self, lang, x, page, t):
        """page: the issue's page in `lang` (extract()), t: the fixed texts in `lang` -> the e-mail's parts."""
        pre = '' if lang == 'sr' else '/' + lang
        label = t['head'].replace('{n}', str(x['week'])).replace('{y}', str(x['wyear']))
        web = self.url(f'{pre}/pregled/{x["slug"]}/')
        c = x['cover']
        head = ('<!DOCTYPE html><html lang="' + lang + '"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
                '<meta name="color-scheme" content="light"><meta name="supported-color-schemes" content="light"><title>' + esc(page['title']) + '</title></head>'
                '<body style="margin:0;padding:0;background:#F4F3EE">'
                '<div style="display:none;max-height:0;overflow:hidden;opacity:0;color:#F4F3EE">' + esc(page['lead']) + '&#8199;&#65279;&#847;' * 12 + '</div>'
                f'{TABLE} style="background:#F4F3EE"><tr><td align="center" style="padding:28px 12px 32px">'
                '<table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="width:100%;max-width:600px">'
                # the wordmark (as in the worker's mails), the issue's week and the link to its page
                f'<tr><td style="padding:0 6px 16px">{TABLE}><tr>'
                f'<td valign="top"><span style="font:22px/1 {FONT};letter-spacing:-.6px;color:#0D111A">blok<b style="font-weight:800">volt</b></span>'
                '<div style="width:34px;height:5px;margin-top:7px;border-radius:3px;background:#D9F45B;font-size:0;line-height:0">&nbsp;</div></td>'
                f'<td valign="top" align="right" style="font:13px/1.45 {FONT};color:#5C6270">{esc(label)}<br>'
                f'<a href="{esc(web)}" style="color:#5C6270">{esc(t["web"])}</a></td></tr></table></td></tr>'
                # the cover, 600 px wide
                f'<tr><td style="padding:0 0 14px"><img src="{esc(self.site + c["url"])}" width="600" height="{round(600 * c["h"] / c["w"])}" '
                f'alt="{esc(page["alt"])}" style="display:block;width:100%;max-width:600px;height:auto;border:0;border-radius:18px;background:#E6E5DC"></td></tr>'
                # the card: title and lead, then one row per section, closed by the foot
                f'<tr><td style="background:#FFFFFF;border:1px solid #E6E5DC;border-radius:18px">{TABLE}>'
                f'<tr><td style="padding:30px 30px 4px"><h1 style="{S["h1"]}">{esc(page["title"])}</h1>'
                f'<p style="{S["lead"]}">{esc(page["lead"])}</p></td></tr>')
        sections = []
        for s in page['sections']:
            hh, ht = self.inline(s['h2'])
            bh, bt = self.blocks(s['body'])
            sections.append({'topic': s['topic'],
                             'html': f'<tr><td style="padding:0 30px">{TABLE}><tr><td style="{S["sec"]}"><h2 style="{S["h2"]}">{hh}</h2>{bh}</td></tr></table></td></tr>',
                             'text': f'———\n{ht}\n\n{bt}'})
        foot = ('<tr><td style="padding:0 0 10px;font-size:0;line-height:0">&nbsp;</td></tr></table></td></tr>'
                f'<tr><td style="{S["foot"]}">{esc(OPERATOR)}<br>{esc(t["why"])} '
                '<a href="{{PREFS}}" style="color:#5C6270">' + esc(t['prefs']) + '</a> · '
                '<a href="{{UNSUB}}" style="color:#5C6270">' + esc(t['unsub']) + '</a></td></tr>'
                '</table></td></tr></table></body></html>')
        return {'subject': page['title'], 'preheader': page['lead'], 'head_html': head,
                'head_text': f'{label}\n{t["web"]}: {web}\n\n{page["title"]}\n\n{page["lead"]}\n\n',
                'sections': sections, 'foot_html': foot,
                'foot_text': f'—\n{OPERATOR}\n{t["why"]}\n{t["prefs"]}: {{{{PREFS}}}}\n{t["unsub"]}: {{{{UNSUB}}}}\n'}


def extract(page_html):
    """The parts of a built issue page (any language) the e-mail is made of."""
    soup = BeautifulSoup(page_html, 'html.parser')
    secs = []
    for s in soup.select('section[data-pg-topic]'):
        h2 = s.find('h2', recursive=False)
        secs.append({'topic': s['data-pg-topic'], 'h2': h2, 'body': [c for c in s.children if c is not h2]})
    return {'title': soup.select_one('[data-pg=title]').get_text(' ', strip=True),
            'lead': soup.select_one('[data-pg=lead]').get_text(' ', strip=True),
            'alt': soup.select_one('img[data-pg=cover]').get('alt', ''), 'sections': secs}


def page_keys(page_html, i18n):
    """The translation-memory keys of everything the e-mail takes from the Serbian page: title, lead, the cover's alt
    text and every block and visible attribute of the sections."""
    soup = BeautifulSoup(page_html, 'html.parser')
    keys = []
    for el in soup.select('[data-pg=title], [data-pg=lead], section[data-pg-topic]'):
        for r in ([el] if el.name != 'section' else i18n.segment_roots(el)):
            keys.append(i18n.make_key(i18n.seg_html(r))[0])
        for a_el in [el] + el.find_all(True):
            keys += [i18n.text_key(a_el[a])[0] for a in i18n.ATTRS if a_el.get(a)]
    keys.append(i18n.text_key(soup.select_one('img[data-pg=cover]').get('alt', ''))[0])
    return [k for k in dict.fromkeys(keys) if k and i18n.worth(k)]


def content_hash(langs, links):
    """sha256 of the canonical JSON of what is sent: any change of a word, a link or the cover changes it."""
    canon = json.dumps({'langs': langs, 'links': links}, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canon.encode('utf-8')).hexdigest()


def mail_size(parts):
    """Bytes of the HTML with every section and a reader's links (Gmail clips above ~102 KB)."""
    u = 'https://www.blokvolt.rs/ru/pregled/odjava/?t=' + '0' * 32 + '&amp;teme=1'
    whole = parts['head_html'] + ''.join(s['html'] for s in parts['sections']) + parts['foot_html']
    return len(whole.replace('{{PREFS}}', u).replace('{{UNSUB}}', u).encode('utf-8'))


def _texts(page_file):
    s = BeautifulSoup(Path(page_file).read_text(encoding='utf-8'), 'html.parser').find('script', id='bv-i18n-mail')
    return json.loads(s.string)


def _broken(dist, site, links):
    """The links to www.blokvolt.rs that lead nowhere in dist/ (as scripts/check_links.py resolves site paths; it cannot
    see the absolute ones, and a mail cannot be corrected once sent)."""
    red = dist / '_redirects'
    redirects = {line.split()[0] for line in red.read_text(encoding='utf-8').splitlines() if len(line.split()) >= 2} if red.exists() else set()
    out = []
    for u in links:
        if not u.startswith(site + '/'):
            continue
        p = re.split(r'[?#]', u[len(site):], 1)[0]
        if p in redirects or p.rstrip('/') in redirects:
            continue
        rel = p.lstrip('/')
        cand = ['index.html'] if p == '/' else [rel + 'index.html'] if p.endswith('/') else [rel, rel + '.html', rel + '/index.html']
        if not any((dist / c).is_file() for c in cand):
            out.append(u)
    return out


def build(dist, site, issues, tm, i18n):
    """Writes dist/pregled-mail/<slug>.json for every issue and dist/pregled-mail/index.json; returns the lines for the
    build output. tm: {lang: translation memory} of the i18n renderer (the check that nothing stays Serbian)."""
    dist = Path(dist)
    out = dist / 'pregled-mail'
    out.mkdir(parents=True, exist_ok=True)
    texts = {l: (MAIL_T if l == 'sr' else _texts(dist / l / 'pregled' / 'index.html')) for l in LANGS}
    tkeys = [i18n.text_key(v)[0] for v in MAIL_T.values()]
    index, report = [], []
    for x in issues:
        pages = {l: (dist / ('' if l == 'sr' else l) / 'pregled' / x['slug'] / 'index.html').read_text(encoding='utf-8') for l in LANGS}
        keys = page_keys(pages['sr'], i18n) + tkeys
        left = {l: [k for k in keys if i18n.worth(k) and k not in tm[l]] for l in LANGS if l != 'sr'}
        if any(left.values()):
            msg = (f'pregled {x["slug"]}: the e-mail has text without a translation (' +
                   ', '.join(f'{l} {len(v)}' for l, v in left.items()) + '): ' + ' | '.join(next(v for v in left.values() if v)[:3])[:300])
            if x['status'] in ('preview', 'approved'):
                raise SystemExit(msg + ' — run python3 scripts/i18n.py todo and translate before a preview (docs/RUNBOOK.md 3.9)')
            report.append('WARNING ' + msg + ' (draft: translate before the preview)')
        links, langs = {}, {}
        for l in LANGS:
            langs[l] = _Mail(site, x['slug'], links).render(l, x, extract(pages[l]), texts[l])
        table = {n: u for u, n in links.items()}
        broken = _broken(dist, site, links)
        if broken:
            msg = f'pregled {x["slug"]}: links to pages that do not exist: ' + ', '.join(broken[:5])
            if x['status'] in ('preview', 'approved'):
                raise SystemExit(msg)
            report.append('WARNING ' + msg)
        h = content_hash(langs, table)
        sizes = {l: mail_size(p) for l, p in langs.items()}
        big = [f'{l} {v // 1024} KB' for l, v in sizes.items() if v >= MAIL_MAX]
        if big:
            raise SystemExit(f'pregled {x["slug"]}: the e-mail with every section is too big ({", ".join(big)}; at most '
                             f'{MAIL_MAX // 1024} KB, Gmail clips larger ones) — shorten the issue')
        ah = h if x['qa'] and x['status'] == 'approved' else x['approved_hash']     # QA fixture only: approved as built
        data = {'slug': x['slug'], 'date': x['iso'], 'month': x['month'], 'title': x['title'], 'send_at': x['send_at'],
                'status': x['status'], 'approved_hash': ah, 'hash': h, 'topics': x['topics'], 'links': table, 'langs': langs}
        (out / f'{x["slug"]}.json').write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
        index.append({k: data[k] for k in ('slug', 'date', 'month', 'title', 'send_at', 'status', 'approved_hash', 'hash', 'topics')})
        report.append(f'pregled {x["slug"]} ({x["status"]}): hash {h}; e-mail ' + ', '.join(f'{l} {v // 1024} KB' for l, v in sizes.items())
                      + f'; {len(table)} links; sections ' + ' '.join(s['id'] for s in x['sections']))
        if x['status'] == 'approved' and ah != h:
            report.append(f'WARNING pregled {x["slug"]}: approved_hash {ah[:8]}… is not the hash of this text ({h[:8]}…): the e-mail '
                          'will not be sent — a changed issue needs a new preview and approval (docs/RUNBOOK.md 3.27)')
    index.sort(key=lambda i: (i['date'], i['slug']))
    (out / 'index.json').write_text(json.dumps({'about': 'Nedeljni pregled: the issues for the sender (worker, POST /api/posta/tick). '
                                                'Not for readers; docs/RUNBOOK.md 3.27.', 'issues': index},
                                               ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    return report
