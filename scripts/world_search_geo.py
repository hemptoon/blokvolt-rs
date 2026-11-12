"""SEARCH (12.11.2026): one-time preparation of the place names the search of blokvolt.com needs for every city with
charging places, not only the ~3 200 with a page of their own.

Input (not in the repository; both are copies of GeoNames, CC BY 4.0):
  - geonamescache 3.0.2 `cities15000.json` (PyPI geonamescache, MIT) — the list evdb normalises the places to
    (~/dev/evdb/product/geo/geonamescache_3.0.2_cities15000.json): geonameid, name, country, population, admin1 code and
    alternate names;
  - reverse_geocoder 1.5.1 `rg_cities1000.csv` (PyPI) — the English name of the first-level region (admin1) of a place.
Output: content/world/search/cities15000.tsv.gz — one line per city: geonameid, cc, population, region (admin1, English),
name, other names (|). Other names are cut to what the 30 languages of the site can type: Latin, Cyrillic and Greek script,
no codes or digits, one spelling per folded form, at most 6–40 by population.

    python3 scripts/world_search_geo.py <cities15000.json> <rg_cities1000.csv>
The search index itself is built at every build by scripts/world_search.py."""
import csv
import gzip
import json
import math
import re
import sys
import unicodedata
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / 'content' / 'world' / 'search' / 'cities15000.tsv.gz'
OK_SCRIPT = re.compile(r"^[ -ɏḀ-ỿͰ-Ͽἀ-῿Ѐ-ӿ'’.\-–()]+$")


def fold(s):
    s = unicodedata.normalize('NFD', s.lower())
    return re.sub(r'[^0-9a-zа-яёєіїґђјљњћџα-ω ]', '', ''.join(c for c in s if not unicodedata.combining(c)))


def cap(pop):
    return 40 if pop >= 1_000_000 else 25 if pop >= 300_000 else 12 if pop >= 100_000 else 6


def main(gc, rgf):
    G = json.load(open(gc, encoding='utf-8'))
    exact, grid = {}, {}
    for r in csv.DictReader(open(rgf, encoding='utf-8')):
        la, lo = float(r['lat']), float(r['lon'])
        exact[(r['cc'], round(la, 3), round(lo, 3))] = r['admin1']
        grid.setdefault((r['cc'], int(la * 4), int(lo * 4)), []).append((la, lo, r['admin1']))

    def region(c):
        la, lo, cc = c['latitude'], c['longitude'], c['countrycode']
        a = exact.get((cc, round(la, 3), round(lo, 3)))
        if a is not None:
            return a
        best, bd = '', 1e9
        for i in (-1, 0, 1):
            for j in (-1, 0, 1):
                for x in grid.get((cc, int(la * 4) + i, int(lo * 4) + j), ()):
                    dd = (x[0] - la) ** 2 + ((x[1] - lo) * math.cos(math.radians(la))) ** 2
                    if dd < bd and x[2]:
                        best, bd = x[2], dd
        return best if bd < 0.04 else ''   # ≈ 22 km
    rows = []
    for gid, c in G.items():
        pop = int(c.get('population') or 0)
        seen = {fold(c['name'])}
        alt = []
        for a in c.get('alternatenames') or []:
            a = a.strip()
            if not (2 <= len(a) <= 40) or not OK_SCRIPT.match(a) or re.search(r'\d', a) or (a.isupper() and len(a) <= 4):
                continue
            if "'" in a or '’' in a:   # romanisations of other scripts (Ehskal'des…) — the real elisions are in the main name
                continue
            f = fold(a)
            if not f or f in seen:
                continue
            seen.add(f)
            alt.append(a)
        # Cyrillic and Greek first (few, and the only way a Cyrillic or Greek query finds a place without a page), then Latin
        nl = [a for a in alt if re.search(r'[\u0370-\u03FF\u1F00-\u1FFF\u0400-\u04FF]', a)][:8]
        alt = (nl + [a for a in alt if a not in nl])[:cap(pop)]
        rows.append((int(gid), c['countrycode'], pop, region(c), c['name'], '|'.join(alt)))
    rows.sort()
    with gzip.open(OUT, 'wt', encoding='utf-8', compresslevel=9) as f:
        f.write('gid\tcc\tpop\tregion\tname\tother\n')
        for r in rows:
            f.write('\t'.join(str(x).replace('\t', ' ') for x in r) + '\n')
    print(f'{OUT.relative_to(OUT.parents[3])}: {len(rows)} cities, {OUT.stat().st_size // 1024} KB, '
          f'{sum(1 for r in rows if r[3])} with a region')


if __name__ == '__main__':
    main(*sys.argv[1:3])
