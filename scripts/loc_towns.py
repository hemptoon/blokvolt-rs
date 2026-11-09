# -*- coding: utf-8 -*-
"""Town pages of the local sections of blokvolt.com (SEO plan 4.3 b; docs/RUNBOOK.md 3.10 and 3.35).

For every local section with a town list `content/com/local/<dir>/mesta.json`:

- each station of the section's map (`content/com/local/<cc>/stanice.json`, rebuilt monthly by CI — never edited here)
  belongs to the nearest town of the list, up to 25 km (the /gradovi/ rule of blokvolt.rs); the station file's own
  `t` field is not used;
- a town gets `/<dir>/<word>/<slug>/` when at least 3 public stations belong to it, or when the list pins it
  (`"page": true`: a town that once had a page keeps it, as on blokvolt.rs — never unpin without a redirect);
- `/<dir>/<word>/` lists the towns with pages by region, with counts;
- the section's map page learns the towns (`cfg.cities`), so `<map>?grad=<slug>` opens the map on the town.

Words come from the section's strings (`towns` object: same keys in every language, the build fails on a missing key);
nouns after numbers only through the section's pl(). Town pages have no hreflang cluster (other sections and
blokvolt.rs have other towns) and Kosovo's pages link nowhere outside /xk/.

gen_com.py calls build() once, after the local sections and before the assets (its only hook into this module).
Self-check: python3 scripts/loc_towns.py [--csv towns.csv]   (assignment, counts and town lists; exits 1 on an error)"""
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCAL = ROOT / 'content' / 'com' / 'local'
MAX_KM = 25.0
MIN_PUBLIC = 3
NEARBY = 5
KEYS = ('word', 'nav', 'idx_title', 'idx_desc', 'idx_h1', 'idx_lead', 'idx_th_town', 'idx_th_n', 'idx_th_dc', 'idx_rest',
        'title', 'desc', 'h1', 'lead', 'n_forms', 'stat_n', 'stat_dc', 'net_forms', 'h2_list', 'map_link',
        'th_name', 'th_net', 'th_power', 'th_conn', 'unknown', 'customers', 'open_data', 'h2_nets', 'nets_prices',
        'net_no_page', 'h2_home', 'home_line', 'home_more', 'h2_near', 'all_towns', 'btn_map', 'data_date', 'attr',
        'hub_line', 'none_now')
TOWN_FIELDS = ('name', 'slug', 'lat', 'lon', 'loc', 'region', 'aliases', 'page')
SLUG_RE = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
CONN = {'ccs2': 'CCS2', 'ccs1': 'CCS1', 'chademo': 'CHAdeMO', 'type2': 'Type 2', 'type1': 'Type 1', 'tesla': 'Tesla',
        'gbt': 'GB/T', 'cee': 'CEE'}


def hav(la1, lo1, la2, lo2):
    la1, lo1, la2, lo2 = map(math.radians, (la1, lo1, la2, lo2))
    a = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371.0088 * math.asin(math.sqrt(a))


def load_towns(d):
    """The section's town list, checked: fields, slugs (ASCII, unique), coordinates. None when the section has none."""
    p = LOCAL / d / 'mesta.json'
    if not p.exists():
        return None
    towns = json.load(open(p, encoding='utf-8'))['towns']
    errs, seen = [], set()
    for t in towns:
        miss = [k for k in TOWN_FIELDS if k not in t]
        if miss:
            errs.append(f"{d}: {t.get('name')} lacks {miss}")
            continue
        if not SLUG_RE.match(t['slug']):
            errs.append(f"{d}: bad slug {t['slug']!r}")
        if t['slug'] in seen:
            errs.append(f"{d}: duplicate slug {t['slug']!r}")
        seen.add(t['slug'])
        if not (39 <= t['lat'] <= 47 and 13 <= t['lon'] <= 24):
            errs.append(f"{d}: {t['name']} outside the region")
        if not t['loc'].strip() or not t['name'].strip():
            errs.append(f"{d}: {t['slug']} empty name or loc")
    if errs:
        raise SystemExit('mesta.json: ' + '; '.join(errs))
    return towns


def assign(stations, towns):
    """Station id -> index of the nearest town within MAX_KM (ties: the first town in the list)."""
    out = {}
    for s in stations:
        best, bd = None, MAX_KM
        for i, t in enumerate(towns):
            dk = hav(s['lat'], s['lon'], t['lat'], t['lon'])
            if dk <= bd and (best is None or dk < bd):
                best, bd = i, dk
        if best is not None:
            out[s['id']] = best
    return out


def counts(stations, towns):
    """Per town: all stations, public ones, DC >= 50 kW; plus the number of stations without a town."""
    a = assign(stations, towns)
    res = [dict(n=0, pub=0, dc50=0, st=[]) for _ in towns]
    for s in stations:
        i = a.get(s['id'])
        if i is None:
            continue
        r = res[i]
        r['n'] += 1
        r['pub'] += s.get('acc') == 'public'
        r['dc50'] += (s.get('dc') or 0) >= 50
        r['st'].append(s)
    return res, len(stations) - len(a)


def has_page(t, c):
    return bool(t.get('page')) or c['pub'] >= MIN_PUBLIC


def strings_of(S, d):
    T = S.get('towns')
    if not isinstance(T, dict):
        raise SystemExit(f'strings: section {d} has no "towns" object')
    miss = [k for k in KEYS if k not in T]
    if miss:
        raise SystemExit(f'strings: section {d} lacks towns.{miss}')
    for k in ('n_forms', 'net_forms'):
        if not (isinstance(T[k], list) and len(T[k]) == 3):
            raise SystemExit(f'strings: {d} towns.{k} must be [one, few, many]')
    return T


def date_local(ddmmyyyy, loc):
    """'26.10.2026' -> hr '26. 10. 2026.', ba/me '26.10.2026.', the others as they are (RUNBOOK 3.10)."""
    m = re.match(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', ddmmyyyy or '')
    if not m:
        return ddmmyyyy or ''
    d, mo, y = m.groups()
    if loc['key'] == 'hr':
        return f'{int(d)}. {int(mo)}. {y}.'
    if loc['key'] in ('ba', 'me'):
        return f'{d}.{mo}.{y}.'
    return f'{d}.{mo}.{y}'


def iso(ddmmyyyy):
    m = re.match(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', ddmmyyyy or '')
    return f'{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}' if m else None


def station_row(s, C, S, T, G, loc, map_path, price_nets):
    nets = C.get('net_names', {})
    net = nets.get(s.get('net')) or (price_nets.get(s.get('net')) or {}).get('name') or s.get('opn') or ''
    name = (s.get('n') or '').strip() or net or ((s.get('a') or '').split(',')[0].strip()) or S['map']['charger']
    addr = s.get('a') if (s.get('n') or '').strip() and s.get('a') else ''
    if (s.get('dc') or 0) > 0:
        pw = f"DC {G.num(s['dc'], 0, loc)} kW"
    elif (s.get('ac') or 0) > 0:
        pw = f"AC {G.num(s['ac'], 0, loc)} kW"
    else:
        pw = T['unknown']
    agg = {}
    for c in s.get('c') or []:
        lab = CONN.get(c[0]) or S['map'].get(c[0]) or S['map']['other']
        agg[lab] = agg.get(lab, 0) + (int(c[3]) if len(c) > 3 and c[3] else 1)
    conns = ' · '.join(f'{k} ×{v}' if v > 1 else k for k, v in agg.items())
    return dict(id=s['id'], name=name, addr=addr, net=net, net_slug=s.get('net') or '',
                net_url=f"/{loc['dir']}/{C['slugs']['prices']}#{s['net']}" if s.get('net') in price_nets else '',
                pw=pw, conns=conns, guests=s.get('acc') != 'public', url=f"{map_path}#{s['id']}",
                sort=(-(s.get('dc') or 0), -(s.get('ac') or 0), name.lower()))


def fill(tpl, **kw):
    for k, v in kw.items():
        tpl = tpl.replace('{' + k + '}', str(v))
    return tpl


def home_line(C, T, G, loc, pages):
    """One sentence on charging at home from the section's own tariff (country.json -> power, calc); None without data."""
    try:
        calc = C['calc']
        tar = next(t for t in C['power']['tariffs'] if t['id'] == calc['tariff'])
        allin = float(tar['allin'])
    except (KeyError, StopIteration, TypeError, ValueError):
        return None
    if not allin or 'home' not in pages:
        return None
    d = 3 if loc['cur_sign'] in ('€', 'KM') else 2
    per100 = allin * calc.get('kwh100', 17) * (1 + calc.get('loss', 10) / 100)
    text = fill(T['home_line'], tariff=tar['name'], price=G.money(allin, loc, d), per100=G.money(per100, loc, 0 if loc.get('trim') else 2))   # lekë and denars: whole, as the calculator
    text = re.sub(r'\.\.$', '.', text.strip())   # 'ден.' at the end of the sentence takes no second period
    return dict(text=G.NBSP_RE.sub('\\1\u00a0\\2', text), url=pages['home']['path'])


def patch_map_cities(G, loc, map_page, towns_with_page):
    """Adds cfg.cities {slug: [lat, lon]} to the section's built map page, so ?grad=<slug> centres the map on a town
    (map.js fromUrl; the map page itself stays the generator's)."""
    f = G.OUT / map_page['path'].strip('/') / 'index.html'
    html = f.read_text(encoding='utf-8')
    rx = re.compile(r'(<script id="map-cfg" type="application/json">)(.*?)(</script>)', re.S)
    m = rx.search(html)
    if not m or len(rx.findall(html)) != 1:
        raise SystemExit(f'loc_towns: no single map-cfg in {f}')
    cfg = json.loads(m.group(2).replace('<\\/', '</'))
    cfg['cities'] = {t['slug']: [t['lat'], t['lon']] for t in towns_with_page}
    js = json.dumps(cfg, ensure_ascii=False).replace('</', '<\\/')
    f.write_text(html[:m.start(2)] + js + html[m.end(2):], encoding='utf-8')


def build_section(G, loc, C, st, pages):
    d = loc['dir']
    towns = load_towns(d)
    if towns is None:
        return None
    S = G.STRINGS[loc['key']]
    T = strings_of(S, d)
    pl = G.plural_for(loc)
    by_key = {p['key']: p for p in pages}
    map_page = next(p for p in pages if p.get('template') == 'map')
    map_path = map_page['path']
    price_nets = G.price_file(C, loc)['nets']
    res, n_none = counts(st['stations'], towns)
    idx_path = f"/{d}/{T['word']}/"
    for t, c in zip(towns, res):
        t['url'] = f"{idx_path}{t['slug']}/"
        t['c'] = c
    paged = [t for t, c in zip(towns, res) if has_page(t, c)]
    NAV = [(p['path'], p['nav'], p['key']) for p in pages if p.get('nav')]
    when = date_local(st.get('retrieved'), loc)
    lastmod = iso(st.get('retrieved')) or C.get('checked_iso')
    hl = home_line(C, T, G, loc, by_key)
    ctx0 = dict(LOC=loc, S=S, T=T, C=C, NAV=NAV, SWITCH=G.en_switch(), home=f'/{d}/', PAGES=by_key, pl=pl,
                num=lambda x, dd=0: G.num(x, dd, loc), section='towns', alts=[], idx_path=idx_path, map_path=map_path,
                when=when, fill=fill)
    for t in paged:
        c = t['c']
        rows = sorted((station_row(s, C, S, T, G, loc, map_path, price_nets) for s in c['st']), key=lambda r: r['sort'])
        nets = {}
        for r in rows:
            if r['net_slug'] and r['net']:   # networks only; a host or operator without a network stays in the table
                nets.setdefault(r['net_slug'], dict(name=r['net'], url=r['net_url'], n=0))['n'] += 1
        nets = sorted(nets.values(), key=lambda x: (-x['n'], x['name'].lower()))
        near = sorted((o for o in paged if o is not t), key=lambda o: hav(t['lat'], t['lon'], o['lat'], o['lon']))[:NEARBY]
        G.render('loc_town.html', t['url'], dict(
            ctx0, t=t, rows=rows, nets=nets, near=near, home_line=hl,
            stats=[(G.num(c['n'], 0, loc), pl(c['n'], *T['n_forms']) + ' ' + T['stat_n']),
                   (G.num(c['dc50'], 0, loc), T['stat_dc']),
                   (G.num(len(nets), 0, loc), pl(len(nets), *T['net_forms']))],
            title=fill(T['title'], loc=t['loc'], name=t['name']), description=fill(T['desc'], loc=t['loc'], name=t['name']),
            h1=fill(T['h1'], loc=t['loc'], name=t['name']), lead=fill(T['lead'], loc=t['loc'], name=t['name'])),
            priority='0.6', lastmod=lastmod)
    regions = {}
    for t in paged:
        regions.setdefault(t['region'], []).append(t)
    groups = []
    for r, ts in regions.items():
        ts.sort(key=lambda x: (-x['c']['n'], x['name']))
        groups.append(dict(name=r, towns=ts, n=sum(x['c']['n'] for x in ts)))
    groups.sort(key=lambda g: (-g['n'], g['name']))
    G.render('loc_towns.html', idx_path, dict(ctx0, groups=groups, n_towns=len(paged),
                                              title=T['idx_title'], description=T['idx_desc'], h1=T['idx_h1'], lead=T['idx_lead']),
             priority='0.7', lastmod=lastmod)
    patch_map_cities(G, loc, map_page, paged)
    return dict(dir=d, towns=len(towns), pages=len(paged), stations=len(st['stations']),
                assigned=sum(c['n'] for c in res), none=n_none)


def build(G, loaded):
    """Hook of gen_com.main(): G = the gen_com module, loaded = {key: (C, st, pages)}."""
    out = []
    for key, (C, st, pages) in loaded.items():
        r = build_section(G, G.LOCALES[key], C, st, pages)
        if r:
            out.append(r)
            print(f"/{r['dir']}/ towns: {r['pages']} pages + index ({r['towns']} towns in the list; "
                  f"{r['assigned']} of {r['stations']} stations with a town, {r['none']} farther than 25 km)")
    return out


# ------------------------------------------------------------------ self-check
def selfcheck(csv_path=None):
    """Assignment and counts for every section with a mesta.json; sums against stanice.json; optional towns.csv."""
    import csv
    ok, lines = True, []
    for d in sorted(p.name for p in LOCAL.iterdir() if (p / 'mesta.json').exists()):
        towns = load_towns(d)
        st = json.load(open(LOCAL / d / 'stanice.json', encoding='utf-8'))['stations']
        res, none = counts(st, towns)
        tot = sum(c['n'] for c in res) + none
        pub = sum(c['pub'] for c in res)
        if tot != len(st):
            ok = False
            print(f'{d}: counts {tot} != stanice.json {len(st)}')
        # the tests of the rule itself: the nearest town wins; nothing beyond 25 km
        a = assign(st, towns)
        for s in st:
            dist = sorted((hav(s['lat'], s['lon'], t['lat'], t['lon']), i) for i, t in enumerate(towns))
            exp = dist[0][1] if dist[0][0] <= MAX_KM else None
            if a.get(s['id']) != exp and not (exp is not None and abs(dist[0][0] - dist[1][0]) < 1e-9):
                ok = False
                print(f"{d}: {s['id']} assigned {a.get(s['id'])}, nearest {exp}")
        pages = sum(has_page(t, c) for t, c in zip(towns, res))
        print(f'{d}: {len(towns)} towns, {pages} with a page; {len(st)} stations = {tot - none} with a town + {none} without; public with a town {pub}')
        for t, c in zip(towns, res):
            lines.append([d, t['slug'], t['name'], t['region'], t.get('gid') or '', t['lat'], t['lon'], t.get('pop') or '',
                          c['n'], c['pub'], c['dc50'], int(has_page(t, c)), int(bool(t.get('page'))), t['loc']])
    assert hav(45.815, 15.982, 43.856, 18.413) > 200 and abs(hav(0, 0, 0, 1) - 111.2) < 0.1
    assert date_local('26.10.2026', {'key': 'hr'}) == '26. 10. 2026.' and iso('6.1.2026') == '2026-01-06'
    if csv_path:
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(['section', 'slug', 'name', 'region', 'geonameid', 'lat', 'lon', 'population', 'stations', 'public',
                        'dc50', 'page', 'pinned', 'loc'])
            w.writerows(lines)
        print(f'{csv_path}: {len(lines)} rows')
    return 0 if ok else 1


if __name__ == '__main__':
    a = sys.argv[1:]
    sys.exit(selfcheck(a[a.index('--csv') + 1] if '--csv' in a else None))
