# -*- coding: utf-8 -*-
"""The app layer of guides, data pages and news (docs/RUNBOOK.md 3.38): the short, visual top of a page in the BlokVolt
apps — one key figure, two or three "Ukratko" lines, number tiles, steps, a bar chart, one "Važno" line, path cards —
written by hand from the page itself, in Serbian, English and Russian. The full page stays below it as "Detaljno".

Where it lives: one file per page, content/app/<page path>.json, with the keys "sr", "en" and "ru":

  /podaci/krediti-i-lizing/          → content/app/podaci/krediti-i-lizing.json
  /punjenje-elektricnog-auta-u-zgradi → content/app/punjenje-elektricnog-auta-u-zgradi.json
  /vesti/<slug>/                     → content/app/vesti/<slug>.json

scripts/app_feed.py puts each language's object into that page's document as `app` (guides.json, news.json) and calls
check() below: every object is checked for its shape, lengths, icons and counts, and every number in it (with its
unit: %, €, RSD, km, kW, kWh, years) must be on the built page of that language. A number that is no longer on the page
means the page changed and the app layer did not: update both in the same commit. A guide, data page or news item
without an app layer is an error too.

  python3 build.py                        warns (the build goes on)
  python3 scripts/app_layer.py --strict   checks the last build (dist/) and exits 1 on any error — CI and pack.sh
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP_DIR = ROOT / 'content' / 'app'
IMG_DIR = ROOT / 'static' / 'assets' / 'img'
# the cover photo of a guide or data page (app only): static/assets/img/cover-<image>-1200.webp and -640.webp, 16:9
COVER_SIZES = {'src': 1200, 'thumb': 640}
COVER_CREDIT = {'sr': 'Ilustracija: BlokVolt (AI)', 'en': 'Illustration: BlokVolt (AI)', 'ru': 'Иллюстрация: BlokVolt (ИИ)'}
COVER_ALT = 100
SITE = 'https://www.blokvolt.rs'
LANGS = ('sr', 'en', 'ru')

ICONS = {'bolt', 'plug', 'building', 'users', 'doc', 'coins', 'percent', 'shield', 'wrench', 'battery', 'car', 'road',
         'map', 'clock', 'calendar', 'alert', 'check', 'info', 'phone', 'globe', 'leaf', 'card', 'parking', 'receipt'}
KEYS = ('hero', 'brief', 'keys', 'steps', 'bars', 'important', 'paths')
# (min, max) item counts and character limits
LIM = {'hero.value': 10, 'hero.label': 48, 'brief': 95, 'keys.value': 12, 'keys.label': 40, 'steps.title': 48,
       'steps.item.title': 36, 'steps.item.text': 90, 'bars.title': 48, 'bars.note': 120, 'bars.label': 28,
       'bars.display': 12, 'important': 160, 'paths.title': 36, 'paths.text': 90}
COUNT = {'brief': (2, 3), 'brief.news': (2, 2), 'keys': (2, 4), 'steps': (3, 5), 'bars': (3, 6), 'paths': (2, 4)}

# words the app layer never uses: first person, the site's own voice, rankings, the firm behind the site (RUNBOOK §0)
FORBIDDEN = {
    'sr': re.compile(r'\b(mi|nas|naš\w*|redakcij\w*|najbolj\w*|preporuču\w*)\b', re.I),
    'en': re.compile(r'\b(we|our|ours|best|recommend\w*)\b', re.I),
    'ru': re.compile(r'(?<![\w])(мы|нас|наш\w*|редакци\w*|лучш(ий|ая|ее|ие|его|ую|их)|рекоменду\w*)(?![\w])', re.I),
}
ANY_FORBIDDEN = re.compile(r'evolako', re.I)

# a number: digits with decimal/thousand separators (17.990 · 4,99 · 1 166 · 01.10.2026)
NUM = re.compile(r'(?<![\w.,])\d+(?:[.,]\d+|[   ]\d{3}(?!\d))*')
# units after a number, by class: the same class must follow the number on the page
UNITS = [
    ('pct', r'%'), ('eur', r'€'), ('usd', r'\$'),
    ('rsd', r'RSD|din\.?|дин\.?|динар\w*'),
    ('kwh', r'kWh|кВт·ч|кВт\s?ч|кВтч'), ('kw', r'kW|кВт'),
    ('km', r'km|км'),
    ('year', r'god\.|godin\w*|godine|years?|год\w*|лет'),
    ('month', r'mes\.|mesec\w*|meseci|months?|мес\.|месяц\w*'),
]
UNIT_AFTER = re.compile(r'^[   ]?(' + '|'.join(f'(?P<{c}>{r})' for c, r in UNITS) + r')(?![A-Za-zА-Яа-я])')
UNIT_RX = dict(UNITS)


def norm(s):
    return re.sub(r'[ \t\r\n   ]+', ' ', s or '').strip()


def file_for(doc_id):
    """content/app/<path>.json for a page id ('/podaci/x/', '/vesti/slug/', '/x')."""
    return APP_DIR / (doc_id.strip('/') + '.json')


def load(doc_id):
    f = file_for(doc_id)
    if not f.exists():
        return None
    return json.loads(f.read_text(encoding='utf-8'))


def cover_files(image):
    return {k: IMG_DIR / f'cover-{image}-{w}.webp' for k, w in COVER_SIZES.items()}


def cover(data, lang):
    """The `cover` object of the app layer in a language, from the file's top-level "cover": {"image", "alt": {lang}}:
    absolute versioned URLs (sha1 of the file, like every other /assets file of the build), size, alt text, credit."""
    c = (data or {}).get('cover')
    if not isinstance(c, dict) or not c.get('image'):
        return None
    files = cover_files(c['image'])
    if not all(f.exists() for f in files.values()):
        return None
    import hashlib
    out = {}
    for k, f in files.items():
        out[k] = f'{SITE}/assets/img/{f.name}?v=' + hashlib.sha1(f.read_bytes()).hexdigest()[:10]
    try:
        from PIL import Image
        with Image.open(files['src']) as im:
            out['w'], out['h'] = im.size
    except Exception:
        out['w'], out['h'] = 1200, 675
    out['alt'] = (c.get('alt') or {}).get(lang, '')
    out['credit'] = COVER_CREDIT[lang]
    return out


def validate_cover(c):
    err = []
    if not isinstance(c, dict) or set(c) != {'image', 'alt'}:
        return ['cover: needs exactly image and alt {sr, en, ru}']
    if not isinstance(c['image'], str) or not re.fullmatch(r'[a-z0-9-]+', c['image']):
        return [f'cover.image: a name like "punjenje-u-zgradi": {c["image"]}']
    for k, f in cover_files(c['image']).items():
        if not f.exists():
            err.append(f'cover: {f.relative_to(ROOT)} is missing')
    alt = c['alt']
    if not isinstance(alt, dict) or set(alt) != set(LANGS):
        err.append('cover.alt: needs sr, en and ru')
    else:
        for lang, a in alt.items():
            if not isinstance(a, str) or not a.strip() or len(a) > COVER_ALT:
                err.append(f'cover.alt {lang}: empty or longer than {COVER_ALT} chars')
            elif ANY_FORBIDDEN.search(a):
                err.append(f'cover.alt {lang}: firm name')
    return err


def strings(obj):
    """Every text of an app object (not URLs, icons or numbers), for the word and number checks."""
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, list):
        for x in obj:
            yield from strings(x)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if k in ('url', 'icon', 'value') and not isinstance(v, str):
                continue
            if k in ('url', 'icon', 'accent'):
                continue
            yield from strings(v)


def number_tokens(s):
    """[(number, unit class or None, currency before or None)] of a text."""
    out = []
    for m in NUM.finditer(s):
        tok = norm(m.group(0))
        after = UNIT_AFTER.match(s[m.end():])
        unit = next((c for c, _ in UNITS if after and after.group(c)), None) if after else None
        before = s[:m.start()].rstrip('   ')[-1:]
        cur = {'€': 'eur', '$': 'usd'}.get(before)
        out.append((tok, unit, cur))
    return out


def on_page(tok, unit, cur, text):
    """Is the number (with its unit or currency sign) on the page text?"""
    t = re.escape(tok).replace(r'\ ', r'[   ]')
    rx = r'(?<![\d.,])' + t + r'(?![\d]|[.,]\d)'
    if unit:
        rx += r'[   ]?(?:' + UNIT_RX[unit] + ')'
    if cur:
        rx = (r'€' if cur == 'eur' else r'\$') + r'[   ]?' + rx
    return re.search(rx, text) is not None


def page_text(soup):
    """The visible text of a built page: <main>, the title and the description."""
    if soup is None:
        return ''
    parts = []
    t = soup.find('title')
    if t is not None:
        parts.append(t.get_text(' '))
    d = soup.find('meta', attrs={'name': 'description'})
    if d is not None and d.get('content'):
        parts.append(d.get('content'))
    main = soup.find('main') or soup
    main = main.__copy__()
    for x in main.find_all(['script', 'style', 'template', 'svg', 'noscript']):
        x.decompose()
    parts.append(main.get_text(' '))
    return norm(' '.join(parts))


def _num_value(display):
    m = NUM.search(display or '')
    if not m:
        return None
    s = norm(m.group(0)).replace(' ', '')
    # the site writes numbers the Serbian way in every language (17.990 · 4,99): a comma is the decimal sign, a point
    # followed by three digits groups thousands; a point followed by other than three digits is a decimal point (4.99)
    s = re.sub(r'\.(?=\d{3}(?:\D|$))', '', s)
    s = s.replace(',', '.')
    try:
        return float(s)
    except ValueError:
        return None


def validate(app, lang, kind, text, exists=None):
    """Errors of one language's app object. kind: guide, data, tool or news; text: the page's visible text;
    exists(url) → bool tells whether a link of a path card is a built page."""
    err = []

    def ln(path, s, lim):
        if not isinstance(s, str) or not s.strip():
            err.append(f'{path}: empty or not text')
        elif len(s) > lim:
            err.append(f'{path}: {len(s)} chars > {lim}: "{s}"')
        elif s != s.strip() or '  ' in s:
            err.append(f'{path}: extra spaces: "{s}"')

    def cnt(path, items, key):
        lo, hi = COUNT[key]
        if not isinstance(items, list) or not lo <= len(items) <= hi:
            err.append(f'{path}: {len(items) if isinstance(items, list) else "no"} items, needs {lo}–{hi}')
            return False
        return True

    if not isinstance(app, dict):
        return ['not an object']
    for k in app:
        if k not in KEYS:
            err.append(f'unknown field "{k}"')
    if kind != 'tool' and 'brief' not in app:
        err.append('brief is required')
    if 'hero' in app:
        h = app['hero']
        if not isinstance(h, dict) or set(h) != {'value', 'label'}:
            err.append('hero: needs exactly value and label')
        else:
            ln('hero.value', h['value'], LIM['hero.value'])
            ln('hero.label', h['label'], LIM['hero.label'])
            if not NUM.search(h.get('value') or ''):
                err.append(f'hero.value: no number in "{h.get("value")}"')
    if 'brief' in app:
        if cnt('brief', app['brief'], 'brief.news' if kind == 'news' else 'brief'):
            for i, s in enumerate(app['brief']):
                ln(f'brief[{i}]', s, LIM['brief'])
                if isinstance(s, str) and s.endswith('.') and not re.search(r'(god|mes|itd|tj|br|str|г|ч|руб)\.$', s):
                    err.append(f'brief[{i}]: no full stop at the end: "{s}"')
    if 'keys' in app:
        if cnt('keys', app['keys'], 'keys'):
            for i, it in enumerate(app['keys']):
                if not isinstance(it, dict) or set(it) != {'value', 'label', 'icon'}:
                    err.append(f'keys[{i}]: needs exactly value, label and icon')
                    continue
                ln(f'keys[{i}].value', it['value'], LIM['keys.value'])
                ln(f'keys[{i}].label', it['label'], LIM['keys.label'])
                if it['icon'] not in ICONS:
                    err.append(f'keys[{i}].icon: "{it["icon"]}" is not one of the app icons')
    if 'steps' in app:
        st = app['steps']
        if not isinstance(st, dict) or set(st) - {'title', 'items'} or 'items' not in st:
            err.append('steps: needs items (and a title)')
        else:
            if 'title' in st:
                ln('steps.title', st['title'], LIM['steps.title'])
            if cnt('steps', st['items'], 'steps'):
                for i, it in enumerate(st['items']):
                    if not isinstance(it, dict) or set(it) != {'title', 'text'}:
                        err.append(f'steps.items[{i}]: needs exactly title and text')
                        continue
                    ln(f'steps.items[{i}].title', it['title'], LIM['steps.item.title'])
                    ln(f'steps.items[{i}].text', it['text'], LIM['steps.item.text'])
    if 'bars' in app:
        b = app['bars']
        if not isinstance(b, dict) or set(b) - {'title', 'note', 'items'} or 'items' not in b or 'title' not in b:
            err.append('bars: needs title and items (and a note)')
        else:
            ln('bars.title', b['title'], LIM['bars.title'])
            if 'note' in b:
                ln('bars.note', b['note'], LIM['bars.note'])
            if cnt('bars', b['items'], 'bars'):
                units = set()
                for i, it in enumerate(b['items']):
                    if not isinstance(it, dict) or set(it) - {'label', 'value', 'display', 'accent'} or \
                            not {'label', 'value', 'display'} <= set(it):
                        err.append(f'bars.items[{i}]: needs label, value, display (and accent)')
                        continue
                    ln(f'bars.items[{i}].label', it['label'], LIM['bars.label'])
                    ln(f'bars.items[{i}].display', it['display'], LIM['bars.display'])
                    if not isinstance(it['value'], (int, float)) or isinstance(it['value'], bool) or it['value'] < 0:
                        err.append(f'bars.items[{i}].value: not a number ≥ 0')
                    elif _num_value(it['display']) is None or abs(_num_value(it['display']) - it['value']) > 1e-6:
                        err.append(f'bars.items[{i}]: value {it["value"]} is not the number of "{it["display"]}"')
                    if 'accent' in it and not isinstance(it['accent'], bool):
                        err.append(f'bars.items[{i}].accent: true or false')
                    units.add(norm(NUM.sub('', it['display'])) if isinstance(it['display'], str) else '')
                if len(units) > 1:
                    err.append(f'bars: items in different units {sorted(units)}')
    if 'important' in app:
        ln('important', app['important'], LIM['important'])
    if 'paths' in app:
        if cnt('paths', app['paths'], 'paths'):
            pre = SITE + ('' if lang == 'sr' else '/' + lang) + '/'
            for i, it in enumerate(app['paths']):
                if not isinstance(it, dict) or set(it) != {'title', 'text', 'url'}:
                    err.append(f'paths[{i}]: needs exactly title, text and url')
                    continue
                ln(f'paths[{i}].title', it['title'], LIM['paths.title'])
                ln(f'paths[{i}].text', it['text'], LIM['paths.text'])
                u = it['url']
                if not isinstance(u, str) or not u.startswith(pre) or (lang == 'sr' and re.match(SITE + r'/(en|ru)/', u)):
                    err.append(f'paths[{i}].url: must start with {pre}: {u}')
                elif exists is not None and not exists(u):
                    err.append(f'paths[{i}].url: no such page: {u}')
    # words and numbers
    for s in strings(app):
        if ANY_FORBIDDEN.search(s):
            err.append(f'firm name in the app layer (neutrality, RUNBOOK §0): "{s}"')
        m = FORBIDDEN[lang].search(s)
        if m:
            err.append(f'word "{m.group(0)}" is not used in the app layer (impersonal, no rankings): "{s}"')
        for tok, unit, cur in number_tokens(s):
            if not on_page(tok, unit, cur, text):
                shown = ('€' if cur == 'eur' else '$' if cur == 'usd' else '') + tok + (f' [{unit}]' if unit else '')
                err.append(f'number {shown} is not on the page: "{s}"')
    return err


def shape(app):
    """The structure of an app object without its texts, to compare the languages."""
    if not isinstance(app, dict):
        return None
    out = {}
    for k, v in app.items():
        if k in ('brief', 'keys', 'paths'):
            out[k] = len(v) if isinstance(v, list) else None
            if k == 'keys' and isinstance(v, list):
                out['icons'] = [x.get('icon') for x in v if isinstance(x, dict)]
        elif k in ('steps', 'bars'):
            items = v.get('items') if isinstance(v, dict) else None
            out[k] = len(items) if isinstance(items, list) else None
            if k == 'bars' and isinstance(items, list):
                out['barvals'] = [x.get('value') for x in items if isinstance(x, dict)]
                out['accent'] = [bool(x.get('accent')) for x in items if isinstance(x, dict)]
        else:
            out[k] = True
    return out


def check(docs, page_text_of, exists=None):
    """docs: {lang: [doc, ...]} of guides.json and news.json; page_text_of(doc_id, lang) → the page text.
    Returns (errors, stats): errors as 'id lang: message'."""
    errors, stats = [], {'docs': 0, 'with_app': 0, 'cover': 0}
    for k in KEYS:
        stats[k] = 0
    ids = {}
    for lang, items in docs.items():
        for d in items:
            ids.setdefault(d['id'], d.get('kind'))
    for doc_id, kind in ids.items():
        stats['docs'] += 1
        data = load(doc_id)
        rel = file_for(doc_id).relative_to(ROOT)
        if data is None:
            if kind != 'tool':
                errors.append(f'{doc_id}: no app layer ({rel})')
            continue
        bad = set(data) - set(LANGS) - {'cover'}
        if bad:
            errors.append(f'{doc_id}: unknown keys {sorted(bad)} in {rel} (only sr, en, ru and cover)')
        if 'cover' in data:
            if kind == 'news':
                errors.append(f'{doc_id}: news keep their own photo, no cover')
            for e in validate_cover(data['cover']):
                errors.append(f'{doc_id}: {e}')
            stats['cover'] += 1
        shapes = {}
        for lang in LANGS:
            if lang not in data:
                errors.append(f'{doc_id} {lang}: missing in {rel}')
                continue
            for e in validate(data[lang], lang, kind, page_text_of(doc_id, lang), exists):
                errors.append(f'{doc_id} {lang}: {e}')
            shapes[lang] = shape(data[lang])
        if len({json.dumps(s, sort_keys=True) for s in shapes.values()}) > 1:
            errors.append(f'{doc_id}: the languages differ in structure: ' +
                          '; '.join(f'{k} {json.dumps(v, sort_keys=True)}' for k, v in shapes.items()))
        if 'sr' in data and isinstance(data['sr'], dict):
            stats['with_app'] += 1
            for k in KEYS:
                if k in data['sr']:
                    stats[k] += 1
    # files that belong to no page of the feed
    known = {file_for(i) for i in ids}
    for f in sorted(APP_DIR.rglob('*.json')) if APP_DIR.exists() else []:
        if f not in known:
            errors.append(f'{f.relative_to(ROOT)}: no guide, data page or news item in the feed has this path')
    return errors, stats


def report(errors, stats, strict, out=print):
    head = (f'app layer: {stats["with_app"]}/{stats["docs"]} pages; ' +
            ', '.join(f'{k} {stats[k]}' for k in KEYS + ('cover',)))
    if not errors:
        out(head + '; 0 errors')
        return True
    out(head + f'; {len(errors)} errors (docs/RUNBOOK.md 3.38)' + ('' if strict else ' — warning only; CI and pack.sh fail on them'))
    for e in errors[:60 if strict else 12]:
        out('  ' + e)
    if len(errors) > (60 if strict else 12):
        out(f'  … and {len(errors) - (60 if strict else 12)} more (python3 scripts/app_layer.py --strict)')
    return False


def check_dist(dist):
    """Checks the app layer against a finished build (dist/ with the feed and the pages)."""
    sys.path.insert(0, str(ROOT / 'scripts'))
    import app_feed  # noqa: E402
    dist = Path(dist)
    docs = {}
    for lang in LANGS:
        items = []
        for coll in ('guides', 'news'):
            f = dist / 'assets' / 'app' / 'v1' / lang / f'{coll}.json'
            if not f.exists():
                raise SystemExit(f'app layer: {f} is missing — run python3 build.py first')
            items += json.loads(f.read_text(encoding='utf-8'))['items']
        docs[lang] = items
    cache = {}

    def text_of(doc_id, lang):
        if (doc_id, lang) not in cache:
            soup, _ = app_feed.parse(doc_id, lang, dist)
            cache[(doc_id, lang)] = page_text(soup)
        return cache[(doc_id, lang)]

    return check(docs, text_of, page_exists(dist))


def page_exists(dist):
    sys.path.insert(0, str(ROOT / 'scripts'))
    import app_feed  # noqa: E402

    def exists(url):
        m = re.match(re.escape(SITE) + r'(?:/(en|ru))?(/.*)$', url.split('#')[0].split('?')[0])
        if not m:
            return False
        soup, _ = app_feed.parse(m.group(2), m.group(1) or 'sr', Path(dist))
        return soup is not None
    return exists


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    strict = '--strict' in sys.argv
    errs, st = check_dist(Path(args[0]) if args else ROOT / 'dist')
    ok = report(errs, st, strict=True)
    sys.exit(0 if ok or not strict else 1)
