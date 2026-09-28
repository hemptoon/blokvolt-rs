# -*- coding: utf-8 -*-
"""One list of the pages that blokvolt.rs and the local sections of blokvolt.com share, so that both builds write the
same hreflang clusters (Google ignores a cluster unless every page lists all the others and itself).

- scripts/gen_com.py uses RS_PAGES for the .com side;
- build.py uses rs_alternates() for the .rs side: the Serbian, English and Russian versions of each shared page
  also point to /hr/…, /ba/…, /me/… on blokvolt.com.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCAL = ROOT / 'content' / 'com' / 'local'
COM = 'https://blokvolt.com'

# local section folder -> hreflang (Montenegrin as sr-ME: Google takes ISO 639-1 codes only, "cnr" is not one)
LOCALES = {'hr': 'hr-HR', 'ba': 'bs-BA', 'me': 'sr-ME'}

# page keys that blokvolt.rs has too, and the Serbian page for each
RS_PAGES = {'map': '/mapa/', 'prices': '/javno-punjenje/', 'apps': '/javno-punjenje/aplikacije-i-kartice/',
            'home': '/alati/kalkulator-troskova/', 'subsidies': '/podaci/subvencije-2026/', 'buildings': '/punjac-u-zgradi-skupstina',
            'stats': '/podaci/statistika-ev-srbija/', 'method': '/metodologija/'}

FM_RE = re.compile(r'\A---\n(.*?)\n---\n', re.S)


def local_paths():
    """{'hr': {'map': '/hr/karta/', …}, …} for the sections that are built (a folder with country.json)."""
    out = {}
    for d, _ in LOCALES.items():
        folder = LOCAL / d
        if not (folder / 'country.json').exists():
            continue
        pages = {}
        for p in sorted(folder.glob('*.md')):
            m = FM_RE.match(p.read_text(encoding='utf-8'))
            if not m:
                continue
            meta = {}
            for line in m.group(1).splitlines():
                k, _, v = line.partition(':')
                meta[k.strip()] = v.strip()
            if meta.get('key'):
                pages[meta['key']] = f"/{d}/{meta['slug']}" if meta.get('slug') else f'/{d}/'
        out[d] = pages
    return out


def rs_alternates():
    """{'/mapa/': [('hr-HR', 'https://blokvolt.com/hr/karta/'), ('bs-BA', …), ('sr-ME', …)], …}"""
    loc = local_paths()
    out = {}
    for key, rp in RS_PAGES.items():
        alts = [(LOCALES[d], COM + pages[key]) for d, pages in loc.items() if key in pages]
        if alts:
            out[rp] = alts
    return out


if __name__ == '__main__':
    for k, v in rs_alternates().items():
        print(k, v)
