# -*- coding: utf-8 -*-
"""Languages of the world layer of blokvolt.com (task K8-i18n, pool 3): one registry for N languages.

Registry: content/world/config.json
  "langs":          code -> {hreflang, html, og, code, label, script, dir, dec, thou, pct, intl, date, plural, months,
                              slugs (en/sr/ru only; other languages keep theirs in i18n/<code>/slugs.json)}
  "langs_enabled":  the languages that are built — ["en", "sr", "ru"] until gate G8.
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
PARTS = ('map', 'pages', 'shell', 'prices')
SLUG_KEYS = ('home', 'map', 'hub', 'net', 'about', 'download', 'gnet', 'prices', 'shell_about', 'sources', 'methodology')
SLUG_PATHS = ('home', 'map', 'hub', 'gnet', 'prices', 'shell_about', 'sources', 'methodology')
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


@lru_cache(maxsize=None)
def langs():
    """The enabled languages, English first."""
    env = os.environ.get('BV_WORLD_LANGS')
    ls = [x.strip() for x in env.split(',') if x.strip()] if env else list(config().get('langs_enabled') or BASE)
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
        s = r['slugs']
    else:
        p = i18n_dir(lang) / 'slugs.json'
        if not p.exists():
            raise SystemExit(f'world_i18n: {p} is missing (language {lang} is enabled)')
        s = json.load(open(p, encoding='utf-8'))
    bad = [k for k in SLUG_KEYS if not s.get(k)]
    if bad:
        raise SystemExit(f'world_i18n: slugs of {lang} miss {bad}')
    return s


def loc(lang):
    """The LOC dict of world_pages (formats + section paths) for any language."""
    r, s = reg(lang), slugs(lang)
    d = dict(key=lang, html=r['html'], hreflang=r['hreflang'], og=r['og'], code=r['code'], dec=r['dec'], thou=r['thou'],
             pct=r['pct'], hub=s['hub'], net=s['net'], about=s['about'], download=s['download'], gnet=s['gnet'], map=s['map'])
    if r.get('script') == 'cyrl':
        d['script'] = 'cyrl'
    return d


def scope(lang):
    """Which pages of the bundle a language gets: "all", or "europe" (the pages that have Serbian, bvcom §0) — default."""
    return reg(lang).get('scope', 'europe')


def page_langs(bundle_langs):
    """Languages of one page: en/sr/ru as the bundle names them, extra enabled languages by their scope."""
    bl = tuple(bundle_langs or BASE)
    return tuple(l for l in langs() if (l in bl if l in BASE else (scope(l) == 'all' or 'sr' in bl)))


def label(lang):
    return reg(lang)['label']


def latin(lang):
    return reg(lang).get('script', 'latn') == 'latn'


# ------------------------------------------------------------------ strings
def load(part, langs_=None):
    """{lang: {key: value}} for the enabled languages; stops when an enabled language misses a key."""
    raw = json.load(open(WORLD / f'strings_{part}.json', encoding='utf-8'))
    out = {}
    for l in (langs_ or langs()):
        if l in BASE:
            out[l] = {k: v.get(l) for k, v in raw.items()}
            continue
        p = i18n_dir(l) / f'strings_{part}.json'
        if not p.exists():
            raise SystemExit(f'world_i18n: {p} is missing (language {l} is enabled)')
        tr = json.load(open(p, encoding='utf-8'))
        miss = [k for k in raw if k not in tr or tr[k] in (None, '', {})]
        if miss:
            raise SystemExit(f'world_i18n: {p} misses {len(miss)} keys, e.g. {miss[:5]}')
        out[l] = {k: tr[k] for k in raw}
    return out


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


def fallback(lang, kind, key):
    FALLBACK[(lang, kind)] += 1
    FALLBACK_EX.setdefault((lang, kind), []).append(key) if len(FALLBACK_EX.get((lang, kind), [])) < 5 else None


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


def months(lang):
    return reg(lang)['months']


# ------------------------------------------------------------------ check of an i18n folder (L-task contract)
PH = re.compile(r'\{[^{}]*\}')
TAG = re.compile(r'</?[a-zA-Z][^>]*>|&[a-z#0-9]+;')


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
            if sorted(PH.findall(en)) != sorted(PH.findall(t)):
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
        if set(sl) != set(SLUG_KEYS):
            errs.append(f'slugs.json keys {sorted(sl)} != {sorted(SLUG_KEYS)}')
        for k, v in sl.items():
            if k in SLUG_PATHS and not re.fullmatch(r'/[a-z]{2,3}/([a-z0-9]+(-[a-z0-9]+)*/)*', v or ''):
                errs.append(f'slugs.{k}: "{v}" is not /<lang>/…/ in ASCII lowercase')
            if k not in SLUG_PATHS and not re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', v or ''):
                errs.append(f'slugs.{k}: "{v}" is not one ASCII segment')
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
    json.dump(_pseudo_tree(en_texts), open(d / 'texts.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
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


# ------------------------------------------------------------------ registry entries from Babel
L_CODES = 'de fr es it nl pl pt sv nb da fi cs sk hu ro bg el tr uk sl hr bs mk sq'.split()
OG = {'de': 'de_DE', 'fr': 'fr_FR', 'es': 'es_ES', 'it': 'it_IT', 'nl': 'nl_NL', 'pl': 'pl_PL', 'pt': 'pt_PT', 'sv': 'sv_SE',
      'nb': 'nb_NO', 'da': 'da_DK', 'fi': 'fi_FI', 'cs': 'cs_CZ', 'sk': 'sk_SK', 'hu': 'hu_HU', 'ro': 'ro_RO', 'bg': 'bg_BG',
      'el': 'el_GR', 'tr': 'tr_TR', 'uk': 'uk_UA', 'sl': 'sl_SI', 'hr': 'hr_HR', 'bs': 'bs_BA', 'mk': 'mk_MK', 'sq': 'sq_AL'}


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
        errs.append('pushed config must enable exactly en, sr, ru until G8')
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
    elif cmd == 'registry':
        print(json.dumps({c: babel_entry(c) for c in L_CODES}, ensure_ascii=False, indent=1))
    else:
        raise SystemExit(__doc__)
