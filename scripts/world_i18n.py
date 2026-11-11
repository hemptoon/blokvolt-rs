# -*- coding: utf-8 -*-
"""Languages of the world layer of blokvolt.com (task K8-i18n, pool 3): one registry for N languages.

Registry: content/world/config.json
  "langs":          code -> {hreflang, html, og, code, label, script, dir, dec, thou, pct, intl, date, plural, months,
                              slugs (en/sr/ru only; other languages keep theirs in i18n/<code>/slugs.json)}
  "langs_enabled":  production — ["en", "sr", "ru"] until the owner's „релиз языков“ (LANG_pool); sitemaps/IndexNow only these
  "langs_enabled_preview", "waves", "market_countries", "preview_pages_cap" — LANG0 (docs/WORLD_I18N.md, RUNBOOK 3.48)
A local test build may override the enabled list with BV_WORLD_LANGS=en,sr,ru,de (never in a pushed config) and point
the strings of extra languages to another folder with BV_WORLD_I18N=<dir> (the pseudo-language "xx" of the K8 check).

Strings: en / sr / ru from the combined files content/world/strings_<part>.json ({key: {en, sr, ru}}); every other
language from content/world/i18n/<code>/strings_<part>.json ({key: "text"}, plural keys pl_* as {one, few, …: text},
the contract of the L-tasks). An enabled language without a key stops the build.
Plurals: pl_form(n, forms, lang) — "one|few|many" strings of en/sr/ru keep the old rule (byte-identical builds);
dict forms use the CLDR category of the language (Babel, imported only when such a language is built).
Names: i18n/<code>/countries.csv (cc,name,slug,in_phrase,note) and cities.csv (geonameid,name,in_phrase,decl_ok,note);
a missing country or city name falls back to English and is counted (fallback_report()).
CLI:
  python3 scripts/world_i18n.py selftest
  python3 scripts/world_i18n.py check <code>         # an i18n/<code>/ folder against the EN keys (same checks as L-tasks)
  python3 scripts/world_i18n.py pseudo <dir>          # writes the pseudo-language xx (⟦…⟧, +30 % length) into <dir>/xx/
  python3 scripts/world_i18n.py registry              # prints registry entries made with Babel for the L-task languages
  python3 scripts/world_i18n.py status                # LANG0: keys each language still lacks against EN (all files, texts)
  python3 scripts/world_i18n.py world-paths           # LANG0: rsync excludes of the world folders of every language
"""
import csv
import json
import os
import re
import sys
from collections import Counter
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORLD = ROOT / 'content' / 'world'
BASE = ('en', 'sr', 'ru')                      # languages of the combined string files
PARTS = ('map', 'pages', 'shell', 'prices', 'pay', 'press', 'b2b', 'embed', 'home')   # LANG0: all string files (+ home of HOME2)
SLUG_KEYS = ('home', 'map', 'hub', 'net', 'about', 'download', 'gnet', 'prices', 'shell_about', 'sources', 'methodology')
# LANG0: section paths of G4/G5/G7/G10. en/sr/ru keep them in config.json; another language may name them in its
# slugs.json, otherwise the engine takes its home prefix + the English path (/de/ + how-to-pay/ = /de/how-to-pay/)
SECTION_SLUGS = ('pay', 'routes', 'press', 'b2b', 'embed', 'map_conf', 'developers')
SLUG_PATHS = ('home', 'map', 'hub', 'gnet', 'prices', 'shell_about', 'sources', 'methodology') + SECTION_SLUGS
MARK = '[EN] '                                 # preview only: an English string standing in for a missing translation
MISSING = Counter()                            # (lang, part) -> keys filled with English in a preview build
MISSING_EX = {}
FALLBACK = Counter()                           # (lang, kind) -> count of English fallbacks
FALLBACK_EX = {}


# ------------------------------------------------------------------ registry
@lru_cache(maxsize=None)
def config():
    return json.load(open(WORLD / 'config.json', encoding='utf-8'))


def registry():
    reg = config().get('langs')
    if not isinstance(reg, dict) or not all(l in reg for l in BASE):
        raise SystemExit('content/world/config.json: "langs" must describe at least en, sr, ru (K8-i18n)')
    return reg


def i18n_dir(lang):
    extra = os.environ.get('BV_WORLD_I18N')
    if extra and (Path(extra) / lang).is_dir():
        return Path(extra) / lang
    return WORLD / 'i18n' / lang


def preview():
    """A dev/preview build (preview.yml sets BV_WORLD_PREVIEW=1): langs_enabled_preview, English stand-ins for missing
    strings (marked [EN]) and the page budget of Cloudflare Pages (preview_pages_cap)."""
    return os.environ.get('BV_WORLD_PREVIEW') == '1'


def prod_langs():
    """The languages of production (config "langs_enabled"): the only ones that may enter a sitemap or IndexNow."""
    return tuple(config().get('langs_enabled') or BASE)


@lru_cache(maxsize=None)
def langs():
    """The enabled languages, English first: BV_WORLD_LANGS (local test) › langs_enabled_preview (preview builds) ›
    langs_enabled (production)."""
    env = os.environ.get('BV_WORLD_LANGS')
    if env:
        ls = [x.strip() for x in env.split(',') if x.strip()]
    elif preview() and config().get('langs_enabled_preview'):
        ls = list(config()['langs_enabled_preview'])
    else:
        ls = list(config().get('langs_enabled') or BASE)
    reg = registry()
    for l in ls:
        if l not in reg and l != 'xx':
            raise SystemExit(f'world_i18n: language {l} is enabled but not in config.json "langs"')
    if ls[:1] != ['en']:
        raise SystemExit('world_i18n: English must be the first enabled language (x-default)')
    return tuple(dict.fromkeys(ls))


def reg(lang):
    r = registry().get(lang)
    if r is None and lang == 'xx':      # pseudo-language: English formats, its own slugs
        r = dict(registry()['en'], hreflang='xx', html='en-XA', og='en_XA', code='XX', label='⟦Pseudo⟧', plural=['one', 'other'])
    if r is None:
        raise SystemExit(f'world_i18n: no registry entry for {lang}')
    return r


@lru_cache(maxsize=None)
def slugs(lang):
    r = reg(lang)
    if lang in BASE:
        s = dict(r['slugs'])
    else:
        p = i18n_dir(lang) / 'slugs.json'
        if not p.exists():
            raise SystemExit(f'world_i18n: {p} is missing (language {lang} is enabled)')
        s = json.load(open(p, encoding='utf-8'))
    bad = [k for k in SLUG_KEYS if not s.get(k)]
    if bad:
        raise SystemExit(f'world_i18n: slugs of {lang} miss {bad}')
    en = registry()['en']['slugs']
    for k in SECTION_SLUGS:   # LANG0: optional in slugs.json — home prefix + the English path
        if not s.get(k):
            s[k] = s['home'].rstrip('/') + en[k]
    return s


def market(lang):
    """Countries whose city and network pages a language gets (config "market_countries"; LANG_pool §0.3).
    en/ru: every country; sr: every country of its bundle scope (Europe)."""
    if lang in BASE:
        return None
    if lang == 'xx':   # pseudo-language of the local check: the first two countries of every wave-1 language
        return set(sum((v[:2] for v in config().get('market_countries', {}).values()), []))
    return set(config().get('market_countries', {}).get(lang) or ())


def pages_cap():
    """Preview builds only: the most city + network pages per language (0 = no cap); production builds everything."""
    if not preview():
        return 0
    env = os.environ.get('BV_WORLD_PAGES_CAP')
    return int(env) if env is not None else int(config().get('preview_pages_cap') or 0)


def waves():
    return {k: list(v) for k, v in (config().get('waves') or {}).items()}


def loc(lang):
    """The LOC dict of world_pages (formats + section paths) for any language."""
    r, s = reg(lang), slugs(lang)
    d = dict(key=lang, html=r['html'], hreflang=r['hreflang'], og=r['og'], code=r['code'], dec=r['dec'], thou=r['thou'],
             pct=r['pct'], hub=s['hub'], net=s['net'], about=s['about'], download=s['download'], gnet=s['gnet'], map=s['map'])
    if r.get('script', 'latn') != 'latn':   # cyrl (preloads the Cyrillic face), grek (world-grek.css)
        d['script'] = r['script']
    return d


def scope(lang):
    """Which pages of the bundle a language gets: "all", or "europe" (the pages that have Serbian, bvcom §0) — default."""
    return reg(lang).get('scope', 'europe')


def page_langs(bundle_langs, ptype=None, cc=None):
    """Languages of one world page (LANG_pool §0.1): en/sr/ru as the bundle names them; an extra language gets the hub,
    every country page and the global networks, but city and network pages only in its market_countries."""
    return tuple(l for l in langs() if page_has(l, bundle_langs, ptype, cc))


def page_has(l, bundle_langs, ptype=None, cc=None):
    """The rule of page_langs for one language, enabled or not (the size forecast uses it for languages not built)."""
    bl = tuple(bundle_langs or BASE)
    if l in BASE:
        return l in bl
    if ptype in ('city', 'network'):
        return cc in market(l)
    if ptype is None:   # legacy callers: follow the registry scope
        return scope(l) == 'all' or 'sr' in bl
    return True


def label(lang):
    return reg(lang)['label']


def latin(lang):
    return reg(lang).get('script', 'latn') == 'latn'


# ------------------------------------------------------------------ strings
def mark(v, plural=False):
    """The English stand-in of a missing translation in a preview build: "[EN] text"; plural "a|b|c" → {one, other}."""
    if plural and isinstance(v, str) and v.count('|') == 2:
        one, few, _ = v.split('|')
        return {'one': MARK + one, 'other': MARK + few}
    return MARK + v if isinstance(v, str) else v


def missing(lang, part, key):
    """Counts a key that a preview build filled with English (printed per language by missing_report())."""
    MISSING[(lang, part)] += 1
    if len(MISSING_EX.setdefault((lang, part), [])) < 5:
        MISSING_EX[(lang, part)].append(key)


def missing_report():
    rows = {}
    for (l, part), n in sorted(MISSING.items()):
        rows.setdefault(l, {})[part] = n
    return rows


@lru_cache(maxsize=None)
def _load(part, l):
    raw = json.load(open(WORLD / f'strings_{part}.json', encoding='utf-8'))
    if l in BASE:
        return {k: v.get(l) for k, v in raw.items()}
    p = i18n_dir(l) / f'strings_{part}.json'
    if not p.exists() and not preview():
        raise SystemExit(f'world_i18n: {p} is missing (language {l} is enabled)')
    tr = json.load(open(p, encoding='utf-8')) if p.exists() else {}
    miss = [k for k in raw if k not in tr or tr[k] in (None, '', {})]
    if miss and not preview():
        raise SystemExit(f'world_i18n: {p} misses {len(miss)} keys, e.g. {miss[:5]}')
    out = {}
    for k, v in raw.items():
        if k in miss:
            missing(l, part, k)
            out[k] = mark(v['en'], k.startswith('pl_'))
        else:
            out[k] = tr[k]
    return out


def load(part, langs_=None):
    """{lang: {key: value}} for the enabled languages; stops when an enabled language misses a key (production) or puts
    the English string with the [EN] mark in its place (preview, counted)."""
    return {l: dict(_load(part, l)) for l in (langs_ or langs())}


def strings_raw(part, langs_=None):
    """{key: {lang: value}} — the shape of the combined files, for modules that validate per key."""
    S = load(part, langs_)
    raw = json.load(open(WORLD / f'strings_{part}.json', encoding='utf-8'))
    return {k: {l: S[l][k] for l in S} for k in raw}


# ------------------------------------------------------------------ plurals
@lru_cache(maxsize=None)
def _plural_rule(lang):
    try:
        from babel import Locale
    except ImportError:
        raise SystemExit('world_i18n: plural forms of extra languages need Babel (pip install babel)')
    return Locale.parse(reg(lang).get('babel') or lang).plural_form


def category(n, lang):
    if lang == 'xx':
        return 'one' if abs(int(round(float(n)))) == 1 else 'other'
    return _plural_rule(lang)(abs(int(round(float(n)))))


def pl_form(n, forms, lang):
    """forms: "one|few|many" (en/sr/ru, the old rule) or {category: text} (CLDR, any language)."""
    if isinstance(forms, dict):
        c = category(n, lang)
        return forms.get(c) or forms.get('other') or next(iter(forms.values()))
    one, few, many = forms.split('|')
    n = abs(int(round(float(n))))
    if lang == 'en':
        return one if n == 1 else few
    if n % 10 == 1 and n % 100 != 11:
        return one
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return few
    return many


# ------------------------------------------------------------------ names
def read_csv(p):
    with open(p, encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


@lru_cache(maxsize=None)
def countries(lang):
    p = i18n_dir(lang) / 'countries.csv'
    return {r['cc']: r for r in read_csv(p)} if p.exists() else {}


@lru_cache(maxsize=None)
def cities(lang):
    p = i18n_dir(lang) / 'cities.csv'
    return {int(r['geonameid']): r for r in read_csv(p) if (r.get('geonameid') or '').isdigit()} if p.exists() else {}


_SEEN = set()


def fallback(lang, kind, key):
    """Counts each (language, kind, key) once — a name is looked up many times in one build."""
    if (lang, kind, key) in _SEEN:
        return
    _SEEN.add((lang, kind, key))
    FALLBACK[(lang, kind)] += 1
    if len(FALLBACK_EX.setdefault((lang, kind), [])) < 5:
        FALLBACK_EX[(lang, kind)].append(key)


def fallback_report():
    """Lines for the build log; with BV_WORLD_I18N_REPORT=<file> also a JSON report."""
    rows = {f'{l}:{k}': {'n': n, 'examples': FALLBACK_EX.get((l, k), [])} for (l, k), n in sorted(FALLBACK.items())}
    if os.environ.get('BV_WORLD_I18N_REPORT'):
        json.dump(rows, open(os.environ['BV_WORLD_I18N_REPORT'], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return [f'  {k}: {v["n"]} English fallbacks (e.g. {", ".join(map(str, v["examples"][:3]))})' for k, v in rows.items()]


def country_name(row, lang):
    """Name of a country for any language: row = content/world/names/countries.csv; extra languages read i18n first."""
    if lang in BASE:
        return row[f'name_{lang}']
    x = countries(lang).get(row['cc'])
    if x and x.get('name'):
        return x['name']
    if row.get(f'name_{lang}'):
        return row[f'name_{lang}']
    fallback(lang, 'country_name', row['cc'])
    return row['name_en']


def country_slug(row, lang):
    if lang in BASE:
        return row[f'slug_{lang}']
    x = countries(lang).get(row['cc'])
    if x and x.get('slug'):
        return x['slug']
    fallback(lang, 'country_slug', row['cc'])
    return row['slug_en']


def country_in(row, lang):
    """"in Germany" of an extra language (en/sr/ru keep their own rules in the modules)."""
    x = countries(lang).get(row['cc'])
    if x and x.get('in_phrase'):
        return x['in_phrase']
    fallback(lang, 'country_in', row['cc'])
    return country_name(row, lang)


def check_collisions(out):
    """Stops the build when a page path of an extra language is already taken by another page of blokvolt.com
    (e.g. /hr/ = the Croatian regional section). Called after the regional sections and before the world pages."""
    out = Path(out)
    bad = []
    for l in langs():
        if l in BASE:
            continue
        for k in SLUG_PATHS:
            f = out / slugs(l)[k].strip('/') / 'index.html'
            if f.exists() and not (k == 'map' and 'world-map.js' in f.read_text(encoding='utf-8', errors='ignore')):
                bad.append(f'{l}.{k} = {slugs(l)[k]}')
    if bad:
        raise SystemExit('world_i18n: paths of extra languages collide with existing pages — ' + ', '.join(bad))


UNIVERSAL_FORBIDDEN = (r'24/7', r'evolako')
BCMS = ('sr', 'hr', 'bs', 'sl')   # the Serbian word lists ("mi", "odmah", "redakcija", "popust" …) apply to these only


def forbidden(patterns, lang):
    """The forbidden-word patterns that apply to a language: all of them for en/sr/ru (as before) and the BCMS
    languages; for other languages only the language-neutral ones (Hungarian "Mi a hiba?" is not Serbian "mi")."""
    if lang in BASE or lang in BCMS:
        return patterns
    return [p for p in patterns if p in UNIVERSAL_FORBIDDEN]


def months(lang):
    return reg(lang)['months']


# ------------------------------------------------------------------ check of an i18n folder (L-task contract)
PH = re.compile(r'\{[^{}]*\}')
TAG = re.compile(r'</?[a-zA-Z][^>]*>|&[a-z#0-9]+;')


def _ph_group(ph):
    return re.sub(r'^\{(city|country)_[uv]\}$', r'{\1}', ph)


def check_folder(lang, folder=None):
    folder = Path(folder) if folder else i18n_dir(lang)
    errs = []
    for part in PARTS:
        raw = json.load(open(WORLD / f'strings_{part}.json', encoding='utf-8'))
        p = folder / f'strings_{part}.json'
        if not p.exists():
            errs.append(f'{p.name} missing')
            continue
        tr = json.load(open(p, encoding='utf-8'))
        for k, v in raw.items():
            en, t = v['en'], tr.get(k)
            if t in (None, '', {}):
                errs.append(f'{part}.{k}: missing')
                continue
            if k.startswith('pl_'):
                if not isinstance(t, dict):
                    errs.append(f'{part}.{k}: plural must be an object')
                elif lang != 'xx':
                    try:
                        from babel import Locale
                        cats = set(Locale.parse(reg(lang).get('babel') or lang).plural_form.tags) | {'other'}
                        if set(t) != cats:
                            errs.append(f'{part}.{k}: categories {sorted(t)} != CLDR {sorted(cats)}')
                    except ImportError:
                        pass
                continue
            if not isinstance(t, str):
                errs.append(f'{part}.{k}: must be a string')
                continue
            # placeholders: the same as EN, with the case variants the engine also passes ({city}/{city_u}/{city_v},
            # {country}/{country_u}/{country_v}); a group may be left out only where SR or RU leave it out too
            base_ph = [set(map(_ph_group, PH.findall(str(v.get(x) or '')))) for x in BASE]
            tg = set(map(_ph_group, PH.findall(t)))
            if not tg <= set.union(*base_ph) or not set.intersection(*base_ph) <= tg:
                errs.append(f'{part}.{k}: placeholders {PH.findall(en)} != {PH.findall(t)}')
            if sorted(TAG.findall(en)) != sorted(TAG.findall(t)):
                errs.append(f'{part}.{k}: tags/entities differ')
        extra = set(tr) - set(raw)
        if extra:
            errs.append(f'{part}: unknown keys {sorted(extra)[:5]}')
    s = folder / 'slugs.json'
    if not s.exists():
        errs.append('slugs.json missing')
    else:
        sl = json.load(open(s, encoding='utf-8'))
        if not set(SLUG_KEYS) <= set(sl) <= set(SLUG_KEYS) | set(SECTION_SLUGS):
            errs.append(f'slugs.json keys {sorted(sl)}: need {sorted(SLUG_KEYS)}, may add {sorted(SECTION_SLUGS)}')
        for k, v in sl.items():
            if k in SLUG_PATHS and not re.fullmatch(r'/[a-z]{2,3}/([a-z0-9]+(-[a-z0-9]+)*/)*', v or ''):
                errs.append(f'slugs.{k}: "{v}" is not /<lang>/…/ in ASCII lowercase')
            if k not in SLUG_PATHS and not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', v or ''):
                errs.append(f'slugs.{k}: "{v}" is not one ASCII segment')
    t = json.load(open(folder / 'texts.json', encoding='utf-8')) if (folder / 'texts.json').exists() else {}
    for sec in DATA_TEXTS:   # LANG0: texts.json → pay / routes, key = path of the multilingual node
        have = t.get(sec) or {}
        nodes = data_nodes(sec)
        miss = [k for k in nodes if not str(have.get(k) or '').strip()]
        if miss:
            errs.append(f'texts.{sec}: {len(miss)} of {len(nodes)} missing, e.g. {miss[:3]}')
        extra = [k for k in have if k not in nodes and not re.fullmatch(r'(tolls\.[A-Z]{2}|apps\[\d+\])\.note', k)]
        if extra:
            errs.append(f'texts.{sec}: unknown keys {extra[:3]}')
    for name, cols in (('countries.csv', ['cc', 'name', 'slug', 'in_phrase', 'note']),
                       ('cities.csv', ['geonameid', 'name', 'in_phrase', 'decl_ok', 'note'])):
        p = folder / name
        if p.exists():
            with open(p, encoding='utf-8', newline='') as f:
                hdr = next(csv.reader(f), [])
            if hdr != cols:
                errs.append(f'{name}: header {hdr} != {cols}')
    return errs


# ------------------------------------------------------------------ pseudo-language xx
def pseudo_text(s):
    if not s:
        return s
    parts = re.split(r'(\{[^{}]*\}|<[^>]+>|&[a-z#0-9]+;)', s)
    out = []
    for p in parts:
        if not p or PH.fullmatch(p) or p.startswith('<') or (p.startswith('&') and p.endswith(';')):
            out.append(p)
        else:
            pad = '~' * max(1, round(len(p) * 0.3)) if p.strip() else ''
            out.append(p.replace('a', 'á').replace('e', 'é').replace('o', 'ö') + pad)
    return '⟦' + ''.join(out) + '⟧'


def write_pseudo(dest):
    d = Path(dest) / 'xx'
    d.mkdir(parents=True, exist_ok=True)
    for part in PARTS:
        raw = json.load(open(WORLD / f'strings_{part}.json', encoding='utf-8'))
        tr = {}
        for k, v in raw.items():
            en = v['en']
            if k.startswith('pl_'):
                one, few, _ = en.split('|')
                tr[k] = {'one': pseudo_text(one), 'other': pseudo_text(few)}
            elif en.endswith(' | BlokVolt'):
                tr[k] = pseudo_text(en[:-len(' | BlokVolt')]) + ' | BlokVolt'
            else:
                tr[k] = pseudo_text(en)
        json.dump(tr, open(d / f'strings_{part}.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    sl = {'home': '/xx/', 'map': '/xx/xmap/', 'hub': '/xx/xstations/', 'net': 'xnet', 'about': 'xabout-data',
          'download': 'xdownload', 'gnet': '/xx/xnetworks/', 'prices': '/xx/xprices/', 'shell_about': '/xx/xabout/',
          'sources': '/xx/xsources/', 'methodology': '/xx/xmethodology/'}
    json.dump(sl, open(d / 'slugs.json', 'w', encoding='utf-8'), indent=1)
    names = WORLD / 'names' / 'countries.csv'
    with open(d / 'countries.csv', 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['cc', 'name', 'slug', 'in_phrase', 'note'])
        for r in read_csv(names):
            w.writerow([r['cc'], '⟦' + r['name_en'] + '⟧', 'x' + r['slug_en'], '⟦in ' + r['name_en'] + '⟧', 'pseudo'])
    with open(d / 'cities.csv', 'w', encoding='utf-8', newline='') as f:   # half of the cities: the rest tests the fallback
        w = csv.writer(f)
        w.writerow(['geonameid', 'name', 'in_phrase', 'decl_ok', 'note'])
        for i, r in enumerate(read_csv(WORLD / 'names' / 'cities.csv')):
            if i % 2 == 0:
                w.writerow([r['geonameid'], '⟦' + r['name_en'] + '⟧', '⟦in ' + r['name_en'] + '⟧', '1', 'pseudo'])
    for name in ('about_data.json', 'download.json'):   # texts.json: {"about_data": …, "download": …}
        pass
    en_texts = {'about_data': json.load(open(WORLD / 'about_data.json', encoding='utf-8'))['en'],
                'download': json.load(open(WORLD / 'download.json', encoding='utf-8'))['en']}
    en_texts = _pseudo_tree(en_texts)
    for sec in DATA_TEXTS:   # pay: every text; routes: every second place name (the rest tests the English fallback)
        en_texts[sec] = {k: pseudo_text(v['en']) for i, (k, v) in enumerate(data_nodes(sec).items()) if sec == 'pay' or i % 2 == 0}
    json.dump(en_texts, open(d / 'texts.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return d


def _pseudo_tree(x):
    if isinstance(x, str):
        return pseudo_text(x) if not re.fullmatch(r'(https?://|/)\S*', x) else x
    if isinstance(x, list):
        return [_pseudo_tree(v) for v in x]
    if isinstance(x, dict):
        return {k: _pseudo_tree(v) for k, v in x.items()}
    return x


@lru_cache(maxsize=None)
def texts(lang, name):
    """Long texts (about_data / download) of a language: the combined file for en/sr/ru, i18n/<code>/texts.json else."""
    if lang in BASE:
        return json.load(open(WORLD / f'{name}.json', encoding='utf-8'))[lang]
    p = i18n_dir(lang) / 'texts.json'
    if not p.exists():
        raise SystemExit(f'world_i18n: {p} is missing (language {lang} is enabled)')
    t = json.load(open(p, encoding='utf-8'))
    if name not in t:
        raise SystemExit(f'world_i18n: {p} has no "{name}"')
    return t[name]


# ------------------------------------------------------------------ texts of the data files (LANG0)
DATA_TEXTS = {'pay': 'pay.json', 'routes': 'routes.json'}
NAME_SECTIONS = ('routes',)    # sections that hold place names: a missing one falls back to English and is counted


@lru_cache(maxsize=None)
def data_nodes(section):
    """{path: node} of the multilingual nodes ({en, sr, ru}) of pay.json / routes.json; the path is the key of the
    section in i18n/<code>/texts.json: afir.points[0], routes[3].stops[1].city (LANG_pool, LANG0 step 2)."""
    out = {}

    def walk(x, path):
        if isinstance(x, dict):
            if all(isinstance(x.get(l), str) for l in BASE):
                out[path] = x
                return
            for k, v in x.items():
                walk(v, f'{path}.{k}' if path else k)
        elif isinstance(x, list):
            for i, v in enumerate(x):
                walk(v, f'{path}[{i}]')
    walk(json.load(open(WORLD / DATA_TEXTS[section], encoding='utf-8')), '')
    return out


@lru_cache(maxsize=None)
def _texts_file(lang):
    p = i18n_dir(lang) / 'texts.json'
    return json.load(open(p, encoding='utf-8')) if p.exists() else {}


def data_text(lang, section, path, node=None):
    """The text of a multilingual node of pay.json / routes.json in any language. en/sr/ru: the node itself; others:
    texts.json[section][path]. A missing place name → English (counted); a missing text → build stops (production) or
    English with the [EN] mark (preview, counted)."""
    node = node if node is not None else data_nodes(section)[path]
    if lang in BASE:
        return node[lang]
    v = (_texts_file(lang).get(section) or {}).get(path)
    if isinstance(v, str) and v.strip():
        return v
    if section in NAME_SECTIONS:
        fallback(lang, section + '_name', path)
        return node['en']
    if not preview():
        raise SystemExit(f'world_i18n: {i18n_dir(lang) / "texts.json"} has no "{section}" → "{path}" (language {lang} is enabled)')
    missing(lang, 'texts.' + section, path)
    return MARK + node['en']


def data_note(lang, section, path):
    """Optional short notes of pay.json (note_sr / note_ru of tolls and apps) for another language: texts.json
    [section][path] (path like tolls.HR.note or apps[2].note), '' when not translated — as SR/RU without a note."""
    return ((_texts_file(lang).get(section) or {}).get(path) or '').strip()


# ------------------------------------------------------------------ language menu (LANG0 step 4)
def _fold(s):
    import unicodedata
    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower() or s.lower()


def lang_menu(urls, l, ups=()):
    """Entries of the language menu of a page with more than three languages, or None (en/sr/ru keep the old menu):
    every enabled language by its native name, A–Z (Latin, then Cyrillic and Greek); a language without this page leads to
    the nearest page that has it (ups: {lang: url} dicts, nearest first: country → hub → home), marked up=True.
    The hint strip (world-lang.js) uses `hint`, the sentence of each language about itself."""
    ls = langs()
    if len(ls) <= 3:
        return None
    hints = load('shell')
    out = []
    for x in ls:
        href, up = urls.get(x), False
        if not href:
            up = True
            href = next((u[x] for u in ups if u and u.get(x)), None) or slugs(x)['hub']
        out.append(dict(code=x, href=href, label=label(x), hl=reg(x)['hreflang'], html=reg(x)['html'], on=x == l, up=up,
                        # a preview stand-in ("[EN] This page is also available in English") would mislead: no strip then
                        hint='' if str(hints[x].get('lang_hint') or '').startswith(MARK) else hints[x].get('lang_hint') or '',
                        close=hints[l].get('lang_hint_close') or ''))
    out.sort(key=lambda e: (0 if reg(e['code']).get('script', 'latn') == 'latn' else 1, _fold(e['label'])))
    return out


_ASSETS = {}


def lang_assets(out):
    """LANG0: copies static/com/world-lang.js, world-lang.css and world-grek.css into <out>/assets/world/ once per build and
    returns their versioned URLs {js, css, grek}; None while only en/sr/ru are built (their pages stay as they were)."""
    if len(langs()) <= 3:
        return None
    key = str(out)
    if key not in _ASSETS:
        import hashlib
        import shutil
        a = Path(out) / 'assets' / 'world'
        a.mkdir(parents=True, exist_ok=True)
        v = {}
        for f in ('world-lang.js', 'world-lang.css', 'world-grek.css'):
            shutil.copy2(ROOT / 'static' / 'com' / f, a / f)
            v[f] = hashlib.sha1((a / f).read_bytes()).hexdigest()[:10]
        _ASSETS[key] = {'js': f"/assets/world/world-lang.js?v={v['world-lang.js']}", 'css': f"/assets/world/world-lang.css?v={v['world-lang.css']}",
                        'grek': f"/assets/world/world-grek.css?v={v['world-grek.css']}"}
    return _ASSETS[key]


# ------------------------------------------------------------------ registry entries from Babel
L_CODES = 'de fr es it nl pl pt sv nb da fi cs sk hu ro bg el tr uk sl hr bs mk sq et lt lv'.split()
OG = {'de': 'de_DE', 'fr': 'fr_FR', 'es': 'es_ES', 'it': 'it_IT', 'nl': 'nl_NL', 'pl': 'pl_PL', 'pt': 'pt_PT', 'sv': 'sv_SE',
      'nb': 'nb_NO', 'da': 'da_DK', 'fi': 'fi_FI', 'cs': 'cs_CZ', 'sk': 'sk_SK', 'hu': 'hu_HU', 'ro': 'ro_RO', 'bg': 'bg_BG',
      'el': 'el_GR', 'tr': 'tr_TR', 'uk': 'uk_UA', 'sl': 'sl_SI', 'hr': 'hr_HR', 'bs': 'bs_BA', 'mk': 'mk_MK', 'sq': 'sq_AL',
      'et': 'et_EE', 'lt': 'lt_LT', 'lv': 'lv_LV'}


def babel_entry(code):
    from babel import Locale
    lc = Locale.parse(code)
    from babel.numbers import get_decimal_symbol, get_group_symbol
    pctsym = lc.number_symbols['latn']['percentSign'] if 'latn' in lc.number_symbols else '%'
    script = {'bg': 'cyrl', 'uk': 'cyrl', 'mk': 'cyrl', 'el': 'grek'}.get(code, 'latn')
    pat = lc.percent_formats[None].pattern.replace('#,##0', '{x}').replace('#', '').replace('%', pctsym).replace('\xa0', ' ').strip()
    months = [lc.months['stand-alone']['wide'][i] for i in range(1, 13)]
    t = OG[code].split('_')[1]
    return dict(hreflang=code, html=code, og=OG[code], code=code.upper(), label=lc.get_display_name(code)[:1].upper() + lc.get_display_name(code)[1:],
                script=script, dir='ltr', dec=get_decimal_symbol(code), thou=get_group_symbol(code), pct=pat,
                intl=f'{code}-{t}', date=lc.date_formats['short'].pattern, plural=sorted(set(lc.plural_form.tags) | {'other'}),
                months=months)


# ------------------------------------------------------------------ selftest
def selftest():
    errs = []
    if tuple(config().get('langs_enabled') or ()) != BASE:
        errs.append('pushed config must enable exactly en, sr, ru until "релиз языков" (LANG_pool, LANGI step 6)')
    pv = config().get('langs_enabled_preview') or []
    if pv[:1] != ['en'] or any(x not in registry() for x in pv) or len(set(pv)) != len(pv):
        errs.append('langs_enabled_preview: English first, registry languages only, no repeats')
    mc = config().get('market_countries') or {}
    for code in L_CODES:
        if not mc.get(code) or any(not re.fullmatch(r'[A-Z]{2}', c) for c in mc[code]):
            errs.append(f'market_countries: {code} needs ISO2 countries')
    wv = sum(waves().values(), [])
    if sorted(wv) != sorted(L_CODES):
        errs.append(f'waves must hold every extra language once: {sorted(set(L_CODES) ^ set(wv))}')
    for code in L_CODES:
        if code in registry():
            r = registry()[code]
            if r.get('slugs'):
                errs.append(f'{code}: slugs belong in i18n/{code}/slugs.json')
            if not r.get('label') or not r.get('intl'):
                errs.append(f'{code}: label/intl')
    for l in BASE:
        if set(slugs(l)) < set(SLUG_KEYS):
            errs.append(f'slugs of {l}')
    try:
        from babel import Locale
        for l in ('sr', 'ru'):
            pf = Locale.parse(l).plural_form
            m = {'one': 'a', 'few': 'b', 'many': 'c', 'other': 'c'}
            bad = [n for n in range(0, 2000) if m[pf(n)] != pl_form(n, 'a|b|c', l)]
            if bad:
                errs.append(f'Babel plural of {l} differs from pl_form at {bad[:5]}')
        if [pl_form(n, {'one': 'Stadt', 'other': 'Städte'}, 'de') for n in (1, 2, 21)] != ['Stadt', 'Städte', 'Städte']:
            errs.append('de plural')
        pl = {'one': 'miasto', 'few': 'miasta', 'many': 'miast', 'other': 'miasta'}
        if [pl_form(n, pl, 'pl') for n in (1, 2, 5, 22, 25, 112)] != ['miasto', 'miasta', 'miast', 'miasta', 'miast', 'miast']:
            errs.append('pl plural')
        for code in L_CODES:
            if code not in registry():
                errs.append(f'registry misses {code}')
    except ImportError:
        print('world_i18n selftest: Babel not installed — CLDR checks skipped')
    if pseudo_text('{n} of <b>x</b>').count('{n}') != 1:
        errs.append('pseudo keeps placeholders')
    for l in langs():
        if l not in BASE:
            e = check_folder(l)
            errs += [f'{l}: {x}' for x in e]
    if errs:
        raise SystemExit('world_i18n selftest FAILED:\n  ' + '\n  '.join(errs))
    print(f'world_i18n selftest: OK ({len(registry())} languages in the registry, enabled {", ".join(langs())})')


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'selftest'
    if cmd == 'selftest':
        selftest()
    elif cmd == 'check':
        e = check_folder(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
        print('\n'.join(e) or 'OK')
        sys.exit(1 if e else 0)
    elif cmd == 'pseudo':
        print(write_pseudo(sys.argv[2]))
    elif cmd == 'status':   # LANG0: what each language still lacks against EN (all string files + texts pay/routes)
        rows = []
        for code in L_CODES:
            n, parts = 0, []
            for part in PARTS:
                raw = json.load(open(WORLD / f'strings_{part}.json', encoding='utf-8'))
                pth = i18n_dir(code) / f'strings_{part}.json'
                tr = json.load(open(pth, encoding='utf-8')) if pth.exists() else {}
                m = sum(1 for k in raw if tr.get(k) in (None, '', {}))
                if m:
                    parts.append(f'{part} {m}')
                    n += m
            tx = _texts_file(code)
            for sec in DATA_TEXTS:
                m = sum(1 for k in data_nodes(sec) if not str((tx.get(sec) or {}).get(k) or '').strip())
                if m:
                    parts.append(f'texts.{sec} {m}')
                    n += m * (sec not in NAME_SECTIONS)
            rows.append((code, n, parts))
        for code, n, parts in rows:
            print(f'{code}: {n} keys missing' + (f" ({', '.join(parts)})" if parts else ''))
    elif cmd == 'world-paths':   # LANG0: top folders of the world layer in every registry language (blokvolt-com deploy.yml)
        ps = set()
        for l in registry():
            if l == 'en':
                continue
            sl = slugs(l) if (l in BASE or (WORLD / 'i18n' / l / 'slugs.json').exists()) else {}
            for k in SLUG_PATHS:
                v = sl.get(k)
                if v:
                    seg = v.strip('/').split('/')
                    # a language with its own folder (/de/, /sr/) goes whole; a language that shares a folder with a regional
                    # section (/hr/, /mk/) goes by its world folders only (/hr/svijet/, /hr/karta-svijeta/ …)
                    ps.add('/' + seg[0] + '/' if seg[0] not in ('hr', 'mk', 'ba', 'me', 'al', 'xk', 'si') else '/' + '/'.join(seg[:2]) + '/')
        print(' '.join(f'--exclude={x}' for x in sorted(ps)))
    elif cmd == 'registry':
        print(json.dumps({c: babel_entry(c) for c in L_CODES}, ensure_ascii=False, indent=1))
    else:
        raise SystemExit(__doc__)
