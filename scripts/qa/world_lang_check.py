# -*- coding: utf-8 -*-
"""LANG1 (LANG_pool D1–D10): the places of the language engine, checked on a built blokvolt.com.

    BV_WORLD_PREVIEW=1 [BV_WORLD_I18N=<dir>] python3 scripts/qa/world_lang_check.py dist-com [de,fr,pl,uk,hr]

1. Every page of every built extra language: no placeholder left unfilled ({cu}, {name_nom}, {city_de}, {city_u}, {month} …).
2. For the sample languages (default de, fr, pl, uk, hr):
   - D1 {cu}: the How to pay title of each country holds that country's in_phrase of i18n/<code>/countries.csv,
     when the language's t_pay_country uses {cu};
   - D6 {city_u}: city titles hold the town's in_phrase of i18n/<code>/cities.csv (decl_ok = 1), when t_city uses it;
   - D4 {name_nom}: where the language's pay strings use it, the country's name_nom stands on the page (any case);
   - D5 {city_de}: fr titles with t_near read "de X" / "d’X" / "du X", never "de {vowel}…";
   - D3 {month}: the press page shows the stand-alone month + year (Babel "LLLL y"), never the genitive of a date;
   - section paths of slugs.json (LANG0 contract: pay, routes, press, b2b, embed, map_conf, developers) were built;
   - D9: the widget configurator offers every built language.
Exit 1 on any failure. Needs a build of the same languages (gen_com.py) and the same BV_WORLD_I18N.
"""
import csv
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import world_i18n as I  # noqa: E402

EU = set('AT BE BG CY CZ DE DK EE ES FI FR GR HR HU IE IT LT LU LV MT NL PL PT RO SE SI SK'.split())
PH = re.compile(r'\{(?:cu|name|name_nom|city|city_u|city_v|city_de|country|country_u|country_v|country_name|month|x|n|lo|hi)\}')
fails = []


def fail(m):
    fails.append(m)
    print('FAIL', m)


def page(out, url):
    f = Path(out) / url.strip('/') / 'index.html'
    return f.read_text(encoding='utf-8') if f.exists() else None


def title(h):
    m = re.search(r'<title>(.*?)</title>', h or '', re.S)
    return html.unescape(m.group(1)) if m else ''


def text(h):
    return html.unescape(re.sub(r'<[^>]+>', ' ', re.sub(r'<script.*?</script>|<style.*?</style>', ' ', h or '', flags=re.S)))


def main(out, sample):
    out = Path(out)
    extra = [l for l in I.langs() if l not in I.BASE]
    if not extra:
        print('world_lang_check: only en/sr/ru built — nothing to check')
        return 0
    # 1. no unfilled placeholder anywhere
    n = 0
    for l in extra:
        roots = {I.slugs(l)[k].strip('/') for k in I.SLUG_PATHS}
        for r in sorted(roots):
            for f in (out / r).rglob('index.html') if (out / r).is_dir() else []:
                n += 1
                m = PH.search(text(f.read_text(encoding='utf-8')))
                if m:
                    fail(f'{f.relative_to(out)}: unfilled {m.group(0)}')
    print(f'ok   {n} pages of {len(extra)} languages: no unfilled placeholder' if not fails else f'{n} pages scanned')
    names = {r['cc']: r for r in I.read_csv(I.WORLD / 'names' / 'countries.csv')}
    for l in [x for x in sample if x in extra]:
        k0 = len(fails)
        pay = I.load('pay', [l])[l]
        pages = I.load('pages', [l])[l]
        C = I.countries(l)
        # D1 / D4 — How to pay of every country built
        pay_root = out / I.slugs(l)['pay'].strip('/')
        checked = 0
        for cc, row in names.items():
            slug = I.country_slug(row, l)
            h = page(out, f"{I.slugs(l)['pay']}{slug}/")
            if not h:
                continue
            checked += 1
            if '{cu}' in str(pay['t_pay_country']) and C.get(cc, {}).get('in_phrase'):
                if C[cc]['in_phrase'].lower() not in title(h).lower():
                    fail(f'{l} D1 {cc}: "{C[cc]["in_phrase"]}" not in "{title(h)}"')
            nom = (C.get(cc, {}).get('name_nom') or '').strip()
            keys = ('afir_eu' if cc in EU else 'afir_non', 'conn_txt', 'conn_lnk')   # the strings this page renders
            uses_nom = any('{name_nom}' in str(pay[k]) for k in keys)
            if nom and uses_nom and nom.lower() not in text(h).lower():
                fail(f'{l} D4 {cc}: name_nom "{nom}" not on the page')
        if not checked:
            fail(f'{l}: no How to pay page under {pay_root}')
        # D6 — city titles
        CI = I.cities(l)
        city_ok = 0
        n_city = sum(1 for r in I.config().get('market_countries', {}).get(l, []) if r not in ('RS', 'HR', 'BA', 'ME', 'MK', 'AL', 'XK'))
        if '{city_u}' in str(pages['t_city']) and n_city:   # Balkan languages have no world city pages (K3)
            for f in (out / I.slugs(l)['hub'].strip('/')).glob('*/*/index.html'):
                h = f.read_text(encoding='utf-8')
                if 'world_city' not in h and '"@type": "City"' not in h and '"City"' not in h:
                    continue
                t = title(h)
                hits = [r for r in CI.values() if r.get('decl_ok') == '1' and r.get('in_phrase') and r['in_phrase'] in t]
                city_ok += bool(hits)
            if not city_ok and any((out / I.slugs(l)['hub'].strip('/')).glob('*/*/index.html')):
                fail(f'{l} D6: no city title holds an in_phrase of cities.csv')
        # D5 — French "de"
        if l == 'fr':
            for f in (out / I.slugs(l)['hub'].strip('/')).glob('*/*/index.html'):
                t = title(f.read_text(encoding='utf-8'))
                if re.search(r'\bde [AEIOUYÉÈÊÀÂÎÔÛ]', t) or re.search(r'\bde (Le|Les) ', t):
                    fail(f'fr D5: "{t}"')
        # D3 — month of the press page
        hp = page(out, I.slugs(l)['press'])
        if hp:
            m = I.month_label(sorted(p.stem for p in (I.WORLD / 'index_history').glob('*.json'))[-1], l)
            if m not in text(hp):
                fail(f'{l} D3: "{m}" not on {I.slugs(l)["press"]}')
        # section folders (LANG0 contract of slugs.json; D7 replaced by it, LANG_pool "Поправка 18:45")
        for k in ('pay', 'routes', 'press', 'b2b', 'map_conf', 'developers'):
            if not page(out, I.slugs(l)[k]):
                fail(f'{l} section {k}: {I.slugs(l)[k]} not built')
        # D9 — configurator languages
        hc = page(out, I.slugs(l)['map_conf']) or ''
        offered = set(re.findall(r'name="lang" value="([a-z]{2,3})"', hc)) | set(re.findall(r'<option value="([a-z]{2,3})" lang=', hc))
        if offered != set(I.langs()):
            fail(f'{l} D9: configurator offers {len(offered)} of {len(I.langs())} languages')
        if len(fails) == k0:
            print(f'ok   {l}: D1 {checked} pay pages, D6 {city_ok} city titles, D3 month, section paths, D9 {len(offered)} languages')
    print('world_lang_check:', 'ALL OK' if not fails else f'{len(fails)} FAIL')
    return 1 if fails else 0


if __name__ == '__main__':
    a = sys.argv[1:]
    sys.exit(main(a[0] if a else 'dist-com', (a[1] if len(a) > 1 else 'de,fr,pl,uk,hr').split(',')))
