# -*- coding: utf-8 -*-
"""English and Russian versions of www.blokvolt.rs, made from the built Serbian pages.

The Serbian site is the source of truth. After build.py has written dist/, every Serbian page is cut
into translation units ("segments"): the inner HTML of each element that holds running text, plus
the attributes a reader sees (alt, title, aria-label, placeholder, data-label), <title>, meta
descriptions and the names/descriptions in JSON-LD. Each segment is looked up in a translation
memory — content/i18n/en.json and content/i18n/ru.json, {normalised Serbian: translation} — and the
page is written again under /en/ and /ru/ with translated text, rewritten internal links, lang,
canonical and hreflang. A segment without a translation stays Serbian (and is counted), so a new
Serbian sentence never breaks the build; `python3 scripts/i18n.py todo` lists what to translate.

Numbers that carry a separator (dates 22.09.2026, prices 125.000, decimals 7,4) are replaced by
⟦0⟧, ⟦1⟧… in the key, so a new date or price does not make a sentence untranslated. Plain integers
stay in the key on purpose: Serbian and Russian choose the noun form by the number."""
import json, re, sys, html as _html, hashlib
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString, Tag, Comment

ROOT = Path(__file__).resolve().parent.parent
I18N = ROOT / 'content' / 'i18n'
LANGS = ('en', 'ru')
SITE = 'https://www.blokvolt.rs'

INLINE = {'a', 'b', 'strong', 'i', 'em', 'small', 'span', 'br', 'code', 'sup', 'sub', 'abbr', 'time',
          'mark', 'u', 's', 'del', 'ins', 'wbr', 'q', 'cite', 'kbd', 'var', 'bdi', 'bdo', 'img'}
SKIP = {'script', 'style', 'svg', 'noscript_', 'template', 'head', 'code', 'pre'}
ATTRS = ('alt', 'title', 'aria-label', 'placeholder', 'data-label')
NUM = re.compile(r'(?<![\w.,])\d+(?:[.,]\d+)+(?![\w])')
PH = re.compile(r'⟦(\d+)⟧')
UNITS = {'rsd', 'kw', 'kwh', 'km', 'min', 'h', 'v', 'a', 'ma', 'eur', 'mid', 'ac', 'dc', 'x', 'ocpp', 'rfid'}


def norm_ws(s):
    return re.sub(r'\s+', ' ', s).strip()


def make_key(s):
    """Serbian HTML/text -> (key with ⟦n⟧ placeholders, list of the numbers taken out)."""
    s = norm_ws(s)
    nums = []

    def rep(m):
        nums.append(m.group(0))
        return f'⟦{len(nums) - 1}⟧'
    return NUM.sub(rep, s), nums


def fill(tr, nums):
    return PH.sub(lambda m: nums[int(m.group(1))] if int(m.group(1)) < len(nums) else m.group(0), tr)


def worth(key):
    """False for segments with nothing to translate: numbers, units, domains, e-mails, lone symbols."""
    t = BeautifulSoup(key, 'html.parser').get_text(' ') if '<' in key else _html.unescape(key)
    t = PH.sub(' ', t)
    if re.fullmatch(r'[\s\W\d_]*', t):
        return False
    if re.fullmatch(r'\s*[\w.+-]+@[\w.-]+\s*', t) or re.fullmatch(r'\s*(https?://)?[\w-]+(\.[\w-]+)+(/\S*)?\s*↗?\s*', t):
        return False
    words = [w for w in re.findall(r'[^\W\d_]+', t.lower())]
    return any(w not in UNITS for w in words)


def _direct_text(el):
    return any(isinstance(c, NavigableString) and not isinstance(c, Comment) and c.strip() for c in el.children)


def _has_block(el):
    return any(isinstance(d, Tag) and d.name not in INLINE for d in el.descendants)


def segment_roots(root):
    """Yield elements whose inner HTML is one translation unit (see module docstring)."""
    for el in root.children:
        if not isinstance(el, Tag) or el.name in SKIP or el.get('translate') == 'no':
            continue
        if _direct_text(el) and not _has_block(el):
            yield el
        else:
            yield from segment_roots(el)


def page_units(soup):
    """All translatable units of one page: ('html', element), ('attr', element, name), ('title', el),
    ('meta', el), ('ld', script)."""
    units = []
    body = soup.body or soup
    for el in segment_roots(body):
        units.append(('html', el))
    for el in body.find_all(True):
        if el.name in SKIP or el.find_parent(lambda t: t.name in SKIP or t.get('translate') == 'no'):
            continue
        for a in ATTRS:
            if el.get(a):
                units.append(('attr', el, a))
    if soup.title and soup.title.string:
        units.append(('title', soup.title))
    for m in soup.find_all('meta'):
        if m.get('name') in ('description',) or m.get('property') in ('og:title', 'og:description'):
            units.append(('meta', m))
    for s in soup.find_all('script', type='application/ld+json'):
        units.append(('ld', s))
    for s in soup.find_all('script', id='bv-i18n'):
        units.append(('ui', s))
    return units


LD_KEYS = {'name', 'headline', 'description', 'alternateName', 'articleSection'}
LD_KEEP_TYPES = {'Organization', 'LocalBusiness', 'City', 'Place', 'PostalAddress', 'Brand', 'Person', 'WebSite'}


def ld_strings(obj, out, parent_type=None):
    if isinstance(obj, dict):
        t = obj.get('@type')
        for k, v in obj.items():
            if isinstance(v, str) and k in LD_KEYS and t not in LD_KEEP_TYPES:
                out.append(v)
            else:
                ld_strings(v, out, t)
    elif isinstance(obj, list):
        for v in obj:
            ld_strings(v, out, parent_type)


def text_key(t):
    """Plain text (title, meta, JSON-LD) -> the same key the HTML segment with this text has."""
    return make_key(_html.escape(t, quote=False))


def iter_page_keys(soup):
    for u in page_units(soup):
        kind = u[0]
        if kind == 'html':
            yield make_key(u[1].decode_contents())[0]
        elif kind == 'attr':
            yield text_key(u[1][u[2]])[0]
        elif kind == 'title':
            yield text_key(u[1].string)[0]
        elif kind == 'meta':
            yield text_key(u[1]['content'])[0]
        elif kind == 'ld':
            try:
                data = json.loads(u[1].string or '')
            except Exception:
                continue
            strs = []
            ld_strings(data, strs)
            for s_ in strs:
                yield text_key(s_)[0]
        elif kind == 'ui':
            for v in json.loads(u[1].string or '{}').values():
                if isinstance(v, str):
                    yield text_key(v)[0]


def source_pages(dist):
    """Serbian pages that get a translation: every HTML page except the 404 and the language trees."""
    for p in sorted(dist.rglob('*.html')):
        rel = '/' + str(p.relative_to(dist)).replace('\\', '/')
        if rel.startswith('/en/') or rel.startswith('/ru/') or rel == '/404.html':
            continue
        yield p, rel


def load_tm(lang):
    p = I18N / f'{lang}.json'
    return json.load(open(p, encoding='utf-8')) if p.exists() else {}


def collect(dist):
    """{key: {'pages': n, 'first': url}} over all Serbian pages, only keys worth translating."""
    seen = {}
    for p, rel in source_pages(dist):
        soup = BeautifulSoup(p.read_text(encoding='utf-8'), 'html.parser')
        for k in iter_page_keys(soup):
            if not k or not worth(k):
                continue
            e = seen.setdefault(k, {'pages': 0, 'first': rel})
            e['pages'] += 1
    return seen


# ---------------------------------------------------------------- rendering
NOTE = {
    'en': 'Translated from Serbian. Prices, quotes from company websites and data are given in English for convenience; where the exact wording matters, the <a href="{sr}" data-bv-lang="sr" hreflang="sr">Serbian original</a> applies.',
    'ru': 'Перевод с сербского. Цены, цитаты с сайтов компаний и данные переведены для удобства; если важна точная формулировка, действует <a href="{sr}" data-bv-lang="sr" hreflang="sr">сербский оригинал</a>.',
}
OG_LOCALE = {'en': 'en_US', 'ru': 'ru_RU'}
HREFLANG = {'sr': 'sr', 'en': 'en', 'ru': 'ru'}


def page_url(rel):
    """'/firme/index.html' -> '/firme/', '/cena-punjaca.html' -> '/cena-punjaca', '/index.html' -> '/'."""
    if rel.endswith('/index.html'):
        return rel[:-len('index.html')]
    if rel.endswith('.html'):
        return rel[:-5]
    return rel


def lang_url(url, lang):
    return url if lang == 'sr' else f'/{lang}{url}'


class Renderer:
    def __init__(self, dist):
        self.dist = dist
        self.pages = list(source_pages(dist))
        self.urls = {page_url(rel) for _, rel in self.pages}
        self.tm = {l: load_tm(l) for l in LANGS}
        self.stats = {l: {'hit': 0, 'miss': 0, 'missing': {}} for l in LANGS}

    # -- lookups
    def tr_html(self, lang, inner, where):
        key, nums = make_key(inner)
        if not key or not worth(key):
            return None
        t = self.tm[lang].get(key)
        st = self.stats[lang]
        if t is None:
            st['miss'] += 1
            st['missing'].setdefault(key, where)
            return None
        st['hit'] += 1
        return fill(t, nums)

    def tr_text(self, lang, text, where):
        out = self.tr_html(lang, _html.escape(text, quote=False), where)
        return _html.unescape(out) if out is not None else text

    def is_page(self, path):
        return path in self.urls or (path.endswith('/') and path[:-1] in self.urls) or (path + '/') in self.urls

    def local_href(self, href, lang):
        if not href or not href.startswith('/') or href.startswith('//'):
            if href and href.startswith(SITE + '/'):
                return SITE + self.local_href(href[len(SITE):], lang)
            if href and re.match(r'https://(www\.)?evolako\.rs', href) and 'lang=' not in href:
                base, _, frag = href.partition('#')
                return base + ('&' if '?' in base else '?') + f'lang={lang}' + ('#' + frag if frag else '')
            return href
        path = re.split(r'[?#]', href, 1)[0]
        if path.startswith(('/en/', '/ru/')) or path in ('/en', '/ru'):
            return href
        if self.is_page(path):
            return f'/{lang}{href}'
        return href

    # -- one page
    def translate_page(self, src, url, lang):
        soup = BeautifulSoup(src, 'html.parser')
        where = url
        # 1. running text, from the pristine tree (keys must match `collect`)
        roots = list(segment_roots(soup.body or soup))
        for el in roots:
            t = self.tr_html(lang, el.decode_contents(), where)
            if t is not None:
                el.clear()
                el.append(BeautifulSoup(t, 'html.parser'))
        # 2. attributes the reader sees
        for el in (soup.body or soup).find_all(True):
            if el.name in SKIP or el.find_parent(lambda t: t.name in SKIP or t.get('translate') == 'no'):
                continue
            for a in ATTRS:
                if el.get(a):
                    el[a] = self.tr_text(lang, el[a], where)
        # 3. head
        if soup.title and soup.title.string:
            soup.title.string = self.tr_text(lang, soup.title.string, where)
        for m in soup.find_all('meta'):
            if m.get('name') == 'description' or m.get('property') in ('og:title', 'og:description'):
                m['content'] = self.tr_text(lang, m['content'], where)
            if m.get('property') == 'og:url':
                m['content'] = SITE + lang_url(url, lang)
            if m.get('property') == 'og:locale':
                m['content'] = OG_LOCALE[lang]
        can = soup.find('link', rel='canonical')
        if can:
            can['href'] = SITE + lang_url(url, lang)
        if soup.html:
            soup.html['lang'] = lang
        # 4. JSON-LD and UI strings for scripts
        for sc in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(sc.string or '')
            except Exception:
                continue
            sc.string = json.dumps(self.tr_ld(data, lang, where), ensure_ascii=False, indent=1)
        for sc in soup.find_all('script', id='bv-i18n'):
            data = json.loads(sc.string or '{}')
            for k, v in data.items():
                if isinstance(v, str):
                    data[k] = self.tr_text(lang, v, where)
            sc.string = json.dumps(data, ensure_ascii=False)
        # 5. links
        for a in soup.find_all(['a', 'link', 'area']):
            if a.get('data-bv-lang') is not None or a.name == 'link':
                continue
            if a.get('href'):
                a['href'] = self.local_href(a['href'], lang)
        for f in soup.find_all('form'):
            if f.get('action'):
                f['action'] = self.local_href(f['action'], lang)
        # search chips: the query has to be in the page's language
        for a in soup.find_all('a', href=re.compile(r'^/(en|ru)/pretraga/\?q=')):
            a['href'] = f'/{lang}/pretraga/?q=' + re.sub(r'\s+', '+', a.get_text(' ', strip=True).lower())
        # 6. language switcher and the note on top
        self.fix_switcher(soup, url, lang)
        hero = soup.find('div', class_='v3-ph')
        if hero is not None:
            note = BeautifulSoup('<div class="w3 bv-tr-wrap"><p class="bv-tr-note">' + NOTE[lang].format(sr=url) + '</p></div>', 'html.parser')
            hero.insert_after(note)
        self.add_alternates(soup, url)
        return str(soup)

    def tr_ld(self, obj, lang, where, parent_type=None):
        if isinstance(obj, dict):
            t = obj.get('@type')
            out = {}
            for k, v in obj.items():
                if isinstance(v, str) and k in LD_KEYS and t not in LD_KEEP_TYPES:
                    out[k] = self.tr_text(lang, v, where)
                elif isinstance(v, str) and k in ('url', 'item', '@id') and v.startswith(SITE + '/') and t not in LD_KEEP_TYPES:
                    out[k] = SITE + self.local_href(v[len(SITE):], lang)
                elif k == 'inLanguage':
                    out[k] = lang
                else:
                    out[k] = self.tr_ld(v, lang, where, t)
            return out
        if isinstance(obj, list):
            return [self.tr_ld(v, lang, where, parent_type) for v in obj]
        return obj

    def fix_switcher(self, soup, url, lang):
        for a in soup.find_all('a', attrs={'data-bv-lang': True}):
            if a.find_parent(attrs={'data-lang-menu': True}) is None:
                continue
            l = a['data-bv-lang']
            a['href'] = lang_url(url, l)
            if l == lang:
                a['class'] = ['is--on']
                a['aria-current'] = 'true'
            else:
                if 'class' in a.attrs:
                    del a['class']
                if 'aria-current' in a.attrs:
                    del a['aria-current']
        for sp in soup.find_all(attrs={'data-bv-langcode': True}):
            sp.string = lang.upper()

    def add_alternates(self, soup, url):
        head = soup.head
        if head is None:
            return
        for old in head.find_all('link', rel='alternate'):
            if old.get('hreflang'):
                old.decompose()
        can = head.find('link', rel='canonical')
        anchor = can or head.find('meta')
        for l in ('sr', 'en', 'ru'):
            tag = soup.new_tag('link', rel='alternate', hreflang=HREFLANG[l], href=SITE + lang_url(url, l))
            anchor.insert_after(tag)
            anchor = tag
        xd = soup.new_tag('link', rel='alternate', hreflang='x-default', href=SITE + url)
        anchor.insert_after(xd)

    def run(self):
        for p, rel in self.pages:
            src = p.read_text(encoding='utf-8')
            url = page_url(rel)
            for l in LANGS:
                dst = self.dist / l / rel.lstrip('/')
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_text(self.translate_page(src, url, l), encoding='utf-8')
            soup = BeautifulSoup(src, 'html.parser')
            self.add_alternates(soup, url)
            p.write_text(str(soup), encoding='utf-8')
        return self


def render_all(dist):
    """Called by build.py after the Serbian pages exist. Returns the Renderer (urls, stats)."""
    return Renderer(dist).run()


# ---------------------------------------------------------------- translation batches and checks
TAG = re.compile(r'<(/?)([a-zA-Z][a-zA-Z0-9]*)([^>]*)>')
SR_WORDS = {'je', 'i', 'u', 'na', 'za', 'se', 'od', 'sa', 'ili', 'da', 'su', 'po', 'sve', 'koji', 'koja',
            'koje', 'što', 'kao', 'ali', 'nije', 'nema', 'samo', 'kod', 'iz', 'do', 'ako', 'kad', 'jer',
            'firme', 'cena', 'cene', 'punjač', 'punjača', 'ugradnja', 'struje', 'pominje', 'upit', 'stanu'}


def _tags(s):
    opens, closes = [], []
    for m in TAG.finditer(s):
        attrs = re.sub(r'\s+', ' ', m.group(3)).strip().rstrip('/').strip()
        (closes if m.group(1) else opens).append((m.group(2).lower(), attrs) if not m.group(1) else m.group(2).lower())
    return sorted(opens), sorted(closes)


def problems(src, tr, lang):
    """Why a translation cannot be accepted (empty list = fine)."""
    out = []
    if not isinstance(tr, str) or not tr.strip():
        return ['empty']
    if sorted(PH.findall(src)) != sorted(PH.findall(tr)):
        out.append('placeholders ⟦n⟧ differ')
    if sorted(re.findall(r'\{[a-z]+\}', src)) != sorted(re.findall(r'\{[a-z]+\}', tr)):
        out.append('{name} placeholders differ')
    so, sc = _tags(src)
    to, tc = _tags(tr)
    if so != to or sc != tc:
        out.append('tags or attributes differ')
    if '„' in tr and lang in ('en', 'ru'):
        out.append('Serbian quotation mark „ left')
    text = _plain(tr)
    words = _words(text)
    if sum(1 for w in words if w in SR_WORDS) >= 2 and len(words) > 3:
        out.append('looks untranslated (Serbian words)')
    if lang == 'ru' and not re.search('[а-яё]', text.lower()):
        if any(w in SR_WORDS for w in _words(_plain(src))):
            out.append('no Cyrillic in a Russian translation')
    return out


def _plain(s):
    # <code> holds identifiers (column names like cena_rsd), not language
    s = re.sub(r'<code\b[^>]*>.*?</code>', ' ', s, flags=re.S)
    t = BeautifulSoup(s, 'html.parser').get_text(' ') if '<' in s else _html.unescape(s)
    # displayed URLs and domains are not language
    return re.sub(r'(https?://\S+|\b[\w.-]+\.(rs|com|net|org|ba|me|mk|hr|eu|info|io)(/\S*)?)', ' ', t)


def _words(t):
    # "i-CHARGE" or "Plug-in" is one token, so the Serbian "i" inside a name does not count;
    # tokens with digits are model names (BMW i4, ID.3), not words
    return [w for w in re.findall(r'[^\W_]+(?:-[^\W_]+)*', t.lower()) if not re.search(r'\d', w)]


def make_batches(size=28000):
    """Split todo-en.json into content/i18n/work/batch-NN.json, keeping each page's segments together."""
    work = I18N / 'work'
    work.mkdir(exist_ok=True)
    todo = json.load(open(I18N / 'todo-en.json', encoding='utf-8'))
    ru = json.load(open(I18N / 'todo-ru.json', encoding='utf-8'))
    keys = list(dict.fromkeys(list(todo) + list(ru)))
    en_tm = load_tm('en')
    batches, cur, n = [], [], 0
    for i, k in enumerate(keys):
        item = {'id': i, 'page': todo.get(k) or ru.get(k), 'sr': k}
        if k in en_tm:                      # English, when already done, is a reference for the Russian pass
            item['en'] = en_tm[k]
        if cur and n + len(k) > size and (item['page'] != cur[-1]['page'] or n > size * 1.25):
            batches.append(cur)
            cur, n = [], 0
        cur.append(item)
        n += len(k)
    if cur:
        batches.append(cur)
    for j, b in enumerate(batches):
        (work / f'batch-{j:02d}.json').write_text(json.dumps(b, ensure_ascii=False, indent=1), encoding='utf-8')
    return [(j, len(b), sum(len(x['sr']) for x in b)) for j, b in enumerate(batches)]


def check(lang, batch_file, out_file, verbose=True):
    batch = json.load(open(batch_file, encoding='utf-8'))
    out = json.load(open(out_file, encoding='utf-8'))
    bad = {}
    for item in batch:
        tr = out.get(str(item['id']))
        pr = problems(item['sr'], tr, lang) if tr is not None else ['missing']
        if pr:
            bad[item['id']] = pr
    if verbose:
        if bad:
            for i, pr in list(bad.items())[:60]:
                src = next(x['sr'] for x in batch if x['id'] == i)
                print(f'id {i}: {"; ".join(pr)}\n   sr: {src[:160]}\n   tr: {str(out.get(str(i)))[:160]}')
            print(f'{len(bad)} of {len(batch)} need fixing')
        else:
            print(f'OK: all {len(batch)} segments pass')
    return bad


def merge(lang, pairs):
    """pairs: [(batch_file, out_file)]. Accepts passing translations into content/i18n/<lang>.json."""
    tm = load_tm(lang)
    added, rejected = 0, 0
    for bf, of in pairs:
        batch = json.load(open(bf, encoding='utf-8'))
        out = json.load(open(of, encoding='utf-8'))
        for item in batch:
            tr = out.get(str(item['id']))
            if tr is not None and not problems(item['sr'], tr, lang):
                tm[item['sr']] = tr
                added += 1
            else:
                rejected += 1
    (I18N / f'{lang}.json').write_text(json.dumps(dict(sorted(tm.items())), ensure_ascii=False, indent=1), encoding='utf-8')
    return added, rejected


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'stats'
    dist = ROOT / 'dist'
    keys = collect(dist)
    if cmd == 'stats':
        chars = sum(len(k) for k in keys)
        print(f'{len(keys)} unique segments, {chars} chars; translated: ' +
              ', '.join(f'{l} {sum(1 for k in keys if k in load_tm(l))}' for l in LANGS))
    elif cmd == 'batches':
        for j, n, c in make_batches(int(sys.argv[2]) if len(sys.argv) > 2 else 28000):
            print(f'batch-{j:02d}: {n} segments, {c} chars')
    elif cmd == 'check':
        sys.exit(1 if check(sys.argv[2], sys.argv[3], sys.argv[4]) else 0)
    elif cmd == 'merge':
        lang = sys.argv[2]
        work = I18N / 'work'
        pairs = [(work / f'batch-{p.stem.split("-")[1]}.json', p) for p in sorted(work.glob(f'out-*-{lang}.json'))]
        print(lang, 'added %d, rejected %d' % merge(lang, pairs))
    elif cmd == 'add':
        # add translations from a {serbian key: translation} file (keys copied from todo-<lang>.json)
        lang, path = sys.argv[2], sys.argv[3]
        tm = load_tm(lang)
        ok = bad = 0
        for k, v in json.load(open(path, encoding='utf-8')).items():
            pr = ['key is not on the site'] if k not in keys else problems(k, v, lang)
            if pr:
                print('rejected:', k[:90], '->', '; '.join(pr))
                bad += 1
            else:
                tm[k] = v
                ok += 1
        (I18N / f'{lang}.json').write_text(json.dumps(dict(sorted(tm.items())), ensure_ascii=False, indent=1), encoding='utf-8')
        print(lang, f'added {ok}, rejected {bad}')
    elif cmd == 'prune':
        # drop translations of Serbian text that is no longer on the site
        for l in LANGS:
            tm = load_tm(l)
            keep = {k: v for k, v in tm.items() if k in keys}
            (I18N / f'{l}.json').write_text(json.dumps(dict(sorted(keep.items())), ensure_ascii=False, indent=1), encoding='utf-8')
            print(l, 'removed', len(tm) - len(keep), 'kept', len(keep))
    elif cmd == 'todo':
        # write content/i18n/todo-<lang>.json with every untranslated key (value = first page it appears on)
        for l in LANGS:
            tm = load_tm(l)
            todo = {k: v['first'] for k, v in keys.items() if k not in tm}
            (I18N / f'todo-{l}.json').write_text(json.dumps(todo, ensure_ascii=False, indent=1), encoding='utf-8')
            print(l, len(todo), 'to translate')
