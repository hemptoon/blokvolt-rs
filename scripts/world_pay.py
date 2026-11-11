# -*- coding: utf-8 -*-
""""How to pay" and routes of blokvolt.com (task G4 of pool G), EN / SR / RU.

Data:
  content/world/pay.json     AFIR points (EUR-Lex), roaming apps with their OFFICIAL coverage pages (url + checked date,
                             country list exactly as the page names it), motorway tolls per country (official pages)
  content/world/routes.json  fast chargers along 17 routes from the public layer (scripts/world_routes_calc.py on the mac
                             → scripts/world_routes_slim.py); rule: DC >= 50 kW, reliability >= 70, step <= 150 km
  G3 (scripts/world_prices.py): DC index per country for the trip cost and the price block; networks / weights
Strings: content/world/strings_pay.json ({key: {en, sr, ru}}; the build stops on a missing language or a forbidden word);
other languages (LANG0): i18n/<code>/strings_pay.json, the texts of pay.json / routes.json from i18n/<code>/texts.json
("pay" / "routes": path of the node → text), route towns from i18n/<code>/cities.csv, section paths from world_i18n.slugs.
Templates: templates/com2/world_pay_*.html.

Pages (noindex and out of the sitemap while the world layer is not public — same switch as world_pages):
  /how-to-pay/                 /sr/kako-platiti/           /ru/kak-platit/
  /how-to-pay/<country>/       (country slug of K4, per language; SR only for countries with a SR page)
  /routes/                     /sr/rute/                   /ru/marshruty/
  /routes/<route-id>/          (one slug for all languages, like city and network slugs — P1)
Hook in gen_com.py: world_pay.run(G, wctx) after world_prices.run(). Menu entries via world_shell.EXTRA.
CLI:  python3 scripts/world_pay.py selftest | validate
"""
import datetime as dt
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORLD = ROOT / 'content' / 'world'
sys.path.insert(0, str(Path(__file__).resolve().parent))
import world_i18n as I   # noqa: E402  LANG0: languages, section paths and texts of the other languages
LANGS = I.langs()
PAY = {l: I.slugs(l)['pay'] for l in LANGS}          # /how-to-pay/ /sr/kako-platiti/ /ru/kak-platit/ /de/… (config / slugs.json)
ROUTES = {l: I.slugs(l)['routes'] for l in LANGS}    # /routes/ /sr/rute/ /ru/marshruty/ …
EU = set('AT BE BG HR CY CZ DK EE FI FR DE GR HU IE IT LV LT LU MT NL PL PT RO SK SI ES SE'.split())
FORBIDDEN = [r'\bodmah\b', r'24/7', r'evolako', r'\bredakcij', r'\bmi\s', r'popust', r'скидк', r'\batest', r'\bwe\b', r'\bмы\b']
URL = re.compile(r'^https://[^\s]+$')
DATE = re.compile(r'^20\d\d-\d\d-\d\d$')
# towns at the ends of the routes (route titles); any other town is shown as in routes.json
TOWNS = {
    'München': ('Munich', 'Minhen', 'Мюнхен'), 'Wien': ('Vienna', 'Beč', 'Вена'), 'Budapest': ('Budapest', 'Budimpešta', 'Будапешт'),
    'Beograd': ('Belgrade', 'Beograd', 'Белград'), 'Zagreb': ('Zagreb', 'Zagreb', 'Загреб'),
    'Thessaloniki': ('Thessaloniki', 'Solun', 'Салоники'), 'İstanbul': ('Istanbul', 'Istanbul', 'Стамбул'),
    'Budva': ('Budva', 'Budva', 'Будва'), 'Sarajevo': ('Sarajevo', 'Sarajevo', 'Сараево'), 'Ljubljana': ('Ljubljana', 'Ljubljana', 'Любляна'),
    'Split': ('Split', 'Split', 'Сплит'), 'Dubrovnik': ('Dubrovnik', 'Dubrovnik', 'Дубровник'), 'Ohrid': ('Ohrid', 'Ohrid', 'Охрид'),
    'Varna': ('Varna', 'Varna', 'Варна'), 'București': ('Bucharest', 'Bukurešt', 'Бухарест'),
    'Podgorica': ('Podgorica', 'Podgorica', 'Подгорица'), 'Skopje': ('Skopje', 'Skoplje', 'Скопье'), 'Sofia': ('Sofia', 'Sofija', 'София'),
}
# country of each waypoint town (for the per-country split of the trip)
TOWN_CC = {
    'München': 'DE', 'Salzburg': 'AT', 'Villach': 'AT', 'Ljubljana': 'SI', 'Novo mesto': 'SI', 'Maribor': 'SI', 'Wien': 'AT', 'Graz': 'AT',
    'Győr': 'HU', 'Budapest': 'HU', 'Kecskemét': 'HU', 'Szeged': 'HU', 'Siófok': 'HU', 'Nagykanizsa': 'HU',
    'Subotica': 'RS', 'Novi Sad': 'RS', 'Beograd': 'RS', 'Jagodina': 'RS', 'Niš': 'RS', 'Vranje': 'RS', 'Pirot': 'RS', 'Čačak': 'RS',
    'Užice': 'RS', 'Prijepolje': 'RS', 'Šabac': 'RS', 'Loznica': 'RS', 'Vršac': 'RS',
    'Zagreb': 'HR', 'Slavonski Brod': 'HR', 'Karlovac': 'HR', 'Gospić': 'HR', 'Zadar': 'HR', 'Šibenik': 'HR', 'Split': 'HR', 'Varaždin': 'HR',
    'Makarska': 'HR', 'Ploče': 'HR', 'Dubrovnik': 'HR',
    'Kumanovo': 'MK', 'Skopje': 'MK', 'Veles': 'MK', 'Gevgelija': 'MK', 'Tetovo': 'MK', 'Gostivar': 'MK', 'Kičevo': 'MK', 'Ohrid': 'MK',
    'Thessaloniki': 'GR', 'Sofia': 'BG', 'Plovdiv': 'BG', 'Haskovo': 'BG', 'Botevgrad': 'BG', 'Pleven': 'BG', 'Veliko Tarnovo': 'BG',
    'Shumen': 'BG', 'Varna': 'BG', 'Edirne': 'TR', 'Lüleburgaz': 'TR', 'İstanbul': 'TR',
    'Bijelo Polje': 'ME', 'Kolašin': 'ME', 'Podgorica': 'ME', 'Budva': 'ME',
    'Zvornik': 'BA', 'Vlasenica': 'BA', 'Sarajevo': 'BA', 'Doboj': 'BA', 'Zenica': 'BA',
    'Timișoara': 'RO', 'Lugoj': 'RO', 'Deva': 'RO', 'Sibiu': 'RO', 'Pitești': 'RO', 'București': 'RO',
}
CC_NAMES_EXTRA = {   # countries without a row in names/countries.csv fall back to these (none expected)
}


def load_json(p):
    return json.load(open(p, encoding='utf-8'))


def load_strings():
    raw = load_json(WORLD / 'strings_pay.json')
    bad = [f'{k}:{l}' for k, v in raw.items() for l in I.BASE if l in LANGS and not (isinstance(v, dict) and str(v.get(l) or '').strip())]
    if bad:
        raise SystemExit('content/world/strings_pay.json: missing translations — ' + ', '.join(bad[:20]))
    raw = I.strings_raw('pay', LANGS)   # LANG0: other languages from i18n/<code>/strings_pay.json (stops on a missing key)
    for k, v in raw.items():
        for l in LANGS:
            for pat in I.forbidden(FORBIDDEN, l):
                if re.search(pat, v[l], re.I):
                    raise SystemExit(f'strings_pay.json: "{k}" ({l}) has a forbidden word ({pat})')
        if k.startswith('t_') and any(re.search(r'\d', v[l]) for l in LANGS):
            raise SystemExit(f'strings_pay.json: title "{k}" must not hold a number (RUNBOOK 3.34)')
    return {l: {k: v[l] for k, v in raw.items()} for l in LANGS}


def validate():
    """Errors of pay.json and routes.json (every coverage fact has an official URL and a date)."""
    errs = []
    P = load_json(WORLD / 'pay.json')
    a = P.get('afir') or {}
    if not URL.match(a.get('url') or '') or not DATE.match(a.get('checked') or ''):
        errs.append('afir: url/checked')
    for i, pt in enumerate(a.get('points') or []):
        if any(not (pt.get(l) or '').strip() for l in I.BASE):
            errs.append(f'afir.points[{i}]: missing language')
    seen = set()
    for app in P.get('apps') or []:
        k = app.get('id')
        if not k or k in seen:
            errs.append(f'apps: bad or duplicate id {k}')
        seen.add(k)
        if not URL.match(app.get('url') or ''):
            errs.append(f'apps.{k}: url')
        if not DATE.match(app.get('checked') or ''):
            errs.append(f'apps.{k}: checked')
        if not isinstance(app.get('countries'), list) or any(not re.match(r'^[A-Z]{2}$', c) for c in app['countries']):
            errs.append(f'apps.{k}: countries must be ISO2')
        if app.get('affiliate'):
            errs.append(f'apps.{k}: affiliate links are not allowed')
    for cc, t in (P.get('tolls') or {}).items():
        if t.get('system') not in ('vignette', 'distance', 'none', 'mixed'):
            errs.append(f'tolls.{cc}: system')
        if not URL.match(t.get('url') or '') or not DATE.match(t.get('checked') or ''):
            errs.append(f'tolls.{cc}: url/checked')
    R = load_json(WORLD / 'routes.json')
    for rt in R['routes']:
        if not re.match(r'^[a-z0-9-]+$', rt['id']):
            errs.append(f"routes.{rt['id']}: slug")
        for w in rt['waypoints']:
            if w[0] not in TOWN_CC:
                errs.append(f"routes.{rt['id']}: town {w[0]} has no country in TOWN_CC")
        last = 0
        for s in rt['stops']:
            if s['cls'] not in (4, 5) or s['conf'] < R['rule']['min_conf']:
                errs.append(f"routes.{rt['id']}: stop {s['pid']} breaks the rule")
            if s['km'] - last > R['rule']['step_km'] + 0.5 and not any(g[0] <= last + 1 and g[1] >= s['km'] - 1 for g in rt['gaps']):
                errs.append(f"routes.{rt['id']}: step {last}->{s['km']} > {R['rule']['step_km']} km without a gap entry")
            last = s['km']
    return errs


def town(name, l):
    t = TOWNS.get(name)
    if l in I.BASE:
        return t[I.BASE.index(l)] if t else name
    gid = _town_gid().get(name)   # LANG0: the town by its GeoNames id in i18n/<code>/cities.csv, else English (counted)
    x = I.cities(l).get(gid) if gid else None
    if x and x.get('name'):
        return x['name']
    I.fallback(l, 'route_town', name)
    return t[0] if t else name


_TG = {}


def _town_gid():
    """Route towns (TOWNS, TOWN_CC) → geonameid of content/world/names/cities.csv (English or Serbian name in its country)."""
    if not _TG:
        import csv
        rows = list(csv.DictReader(open(WORLD / 'names' / 'cities.csv', encoding='utf-8')))
        # LANGI 11.11.2026: also names/cities_extra.csv (FIXL2) — towns without a city page (Botevgrad, Pitești, Edirne…);
        # names compared case-blind, Romanian cedilla = comma (Piteşti = Pitești). Only languages outside en/sr/ru use this.
        extra = list(csv.DictReader(open(WORLD / 'names' / 'cities_extra.csv', encoding='utf-8')))

        def k(x):
            return (x or '').strip().lower().replace('ş', 'ș').replace('ţ', 'ț')
        for name, cc in TOWN_CC.items():
            want = {k(x) for x in (name, *(TOWNS.get(name) or ()))}
            r = next((r for r in rows if r['cc'] == cc and ({k(r['name_en']), k(r['name_sr']), k(r['name_local'])} & want)), None)
            if not r:
                r = next((r for r in extra if r['cc'] == cc and ({k(r['name_geonames']), k(r['ascii'])} & want)), None)
            if r:
                _TG[name] = int(r['geonameid'])
    return _TG


def country_km(rt):
    """km of the route per country: a segment between towns of two countries is split in half (estimate)."""
    from math import asin, cos, radians, sin, sqrt
    f = rt['km'] / max(rt['km_straight'], 1)
    out = {}
    for a, b in zip(rt['waypoints'], rt['waypoints'][1:]):
        la1, lo1, la2, lo2 = map(radians, (a[1], a[2], b[1], b[2]))
        d = 2 * 6371 * asin(sqrt(sin((la2 - la1) / 2) ** 2 + cos(la1) * cos(la2) * sin((lo2 - lo1) / 2) ** 2)) * f
        ca, cb = TOWN_CC[a[0]], TOWN_CC[b[0]]
        out[ca] = out.get(ca, 0) + (d if ca == cb else d / 2)
        if ca != cb:
            out[cb] = out.get(cb, 0) + d / 2
    return out


class R:
    def __init__(self, G, w, S):
        import world_pages as W
        import world_prices as WP
        self.G, self.w, self.S, self.W = G, w, S, W
        self.P = load_json(WORLD / 'pay.json')
        self.RT = load_json(WORLD / 'routes.json')
        PR = getattr(G, 'WORLD_PRICES', None)
        self.M = PR['model'] if PR else WP.Model()
        self.psite = PR['site'] if PR else None
        self.WP = WP
        self.public = bool(w.public)
        self.n = 0
        self.names = {r['cc']: r for r in __import__('csv').DictReader(open(WORLD / 'names' / 'countries.csv', encoding='utf-8'))}
        self.countries = sorted(cc for cc in w.site.country_pages if cc in set(self.WP.D.SCOPE))

    # ---------------- helpers
    def cname(self, cc, l):
        r = self.names.get(cc)
        return (r[f'name_{l}'] if l in I.BASE else I.country_name(r, l)) if r else cc

    def cu(self, cc, l):
        r = self.names[cc]
        if l == 'en':
            return 'in ' + ('the ' if cc in ('US', 'GB', 'NL', 'CZ') else '') + r['name_en']
        if l not in I.BASE:
            return I.country_in(r, l)
        return r['sr_u'] if l == 'sr' else r['ru_v']

    def langs(self, cc):
        return tuple(x for x in LANGS if x in self.w.site.cc_langs.get(cc, LANGS))

    def pay_url(self, cc, l):
        return f"{PAY[l]}{I.country_slug(self.names[cc], l)}/"

    def eur(self, v, l):
        return self.WP.money(v, 'EUR', l) if v is not None else '—'

    def date(self, iso):
        return self.W.fmt_date(iso)

    def toll(self, cc, l):
        t = (self.P.get('tolls') or {}).get(cc)
        if not t:
            return None
        note = (t.get('note_' + l) or '') if l in I.BASE else I.data_note(l, 'pay', f'tolls.{cc}.note')
        return dict(text=self.S[l]['sys_' + t['system']], url=t['url'], op=t.get('operator') or '', checked=self.date(t['checked']),
                    note=note)

    def apps_in(self, cc):
        return [a for a in self.P['apps'] if cc in a['countries']]

    def write(self, l, tpl, url, urls, ctx, ptype, ups=None):
        ctx = dict(ctx, T=self.S[l], PAYH=PAY, ROUTESH=ROUTES)
        self.W.write_page(self.w, l, tpl, url, urls, ctx, ptype, ups=ups)
        self.n += 1

    def afir_points(self, l):
        return [I.data_text(l, 'pay', f'afir.points[{i}]', p) for i, p in enumerate(self.P['afir']['points'])]

    def app_note(self, i, a, l):
        if l in I.BASE:
            return a.get('note_' + l) or (a.get('note') if l == 'en' else '')
        return I.data_note(l, 'pay', f'apps[{i}].note')

    # ---------------- how to pay
    def nets_of(self, cc, l):
        nets = self.M.W['networks'].get(cc, {})
        rows = sorted(nets.items(), key=lambda kv: -((kv[1].get('dc50') or 0) + (kv[1].get('hpc') or 0)))
        out = []
        priced = {r['network']: r for r in self.M.rows if r['cc'] == cc and r['has_price']}
        by_layer = {}
        for r in priced.values():
            for k in r['layer']:
                by_layer[k] = r['network']
        for key, v in rows[:10]:
            n_dc = (v.get('dc50') or 0)
            if n_dc <= 0:
                continue
            pnet = by_layer.get(key)
            purl = self.psite.net(cc, pnet, l) if (self.psite and pnet and (cc, pnet) in self.psite.slug) else None
            page = self.w.site.net(cc, key, l) if self.w.site.has_net(cc, key, l) else None
            out.append(dict(name=key, dc=self.W.fmt_num(n_dc, self.W.L[l]), purl=purl, page=page))
        return out

    def page_pay_country(self, cc, l, urls):
        S = self.S[l]
        c = self.M.countries.get(cc) or {}
        cls = c.get('cls') or {}
        v = {k: (cls.get(k) or {}).get('value') for k in ('ac', 'dc', 'hpc')}
        typ = S['typ_line'].format(ac=self.eur(v['ac'], l), dc=self.eur(v['dc'], l), hpc=self.eur(v['hpc'], l)) if any(v.values()) else S['typ_none']
        price_url = self.psite.country(cc, l) if (self.psite and cc in self.psite.countries) else None
        apps = [dict(name=a['name'], maker=a.get('maker') or '', yes=cc in a['countries'], unk=not a.get('list_complete'), url=a['url'],
                     checked=self.date(a['checked']))
                for a in self.P['apps']]
        A = self.P['afir']
        name = self.cname(cc, l)
        # D4: {name_nom} — the country with its article in the middle of a sentence ("Die Schweiz ist …"); en/sr/ru = name
        nom = I.country_nom(self.names[cc], l) if (l not in I.BASE and cc in self.names) else name
        self.write(l, 'world_pay_country.html', urls[l], urls, dict(
            title=S['t_pay_country'].format(cu=self.cu(cc, l)), h1=S['t_pay_country'].format(cu=self.cu(cc, l)),
            description=S['d_pay_country'].format(cu=self.cu(cc, l)), kick=None, jsonld=None, last=name,
            crumbs=[(S['nav_pay'], PAY[l])], checked=S['checked'].format(date=self.date(self.P['updated'])),
            afir_head=I.fmt_nom(S['afir_eu'] if cc in EU else S['afir_non'], name=name, name_nom=nom),
            afir_points=self.afir_points(l) if cc in EU else [], afir_src=S['afir_src'].format(date=self.date(A['checked'])), afir_url=A['url'],
            nets=self.nets_of(cc, l), apps=apps, typ=typ, price_url=price_url, road=self.toll(cc, l),
            conn_txt=I.fmt_nom(S['conn_txt'], name=name, name_nom=nom), conn_url=self.w.site.country(cc, l),
            conn_lnk=I.fmt_nom(S['conn_lnk'], name=name, name_nom=nom),
            routes=[(self.route_title(rt, l), self.route_url(rt, l)) for rt in self.RT['routes'] if cc in {x['cc'] for x in rt['countries']}][:8]),
            'pay', ups=[PAY])

    def page_pay_hub(self, l):
        S = self.S[l]
        rows = [dict(name=self.cname(cc, l), url=self.pay_url(cc, l), apps=len(self.apps_in(cc)), eu=cc in EU)
                for cc in self.countries if l in self.langs(cc)]
        rows.sort(key=lambda r: r['name'])
        apps = [dict(name=a['name'], maker=a.get('maker') or '', url=a['url'], checked=self.date(a['checked']),
                     n=S['apps_n'].format(n=len(a['countries'])) if a.get('list_complete') else S['apps_unk'], note=self.app_note(i, a, l))
                for i, a in enumerate(self.P['apps'])]
        A = self.P['afir']
        self.write(l, 'world_pay_hub.html', PAY[l], PAY, dict(
            title=S['t_pay_hub'], h1=S['h1_pay_hub'], description=S['d_pay_hub'], kick=S['kick_pay'], crumbs=None, jsonld=None,
            lead=S['lead_pay_hub'], checked=S['checked'].format(date=self.date(self.P['updated'])), rows=rows, apps=apps,
            afir_points=self.afir_points(l), afir_src=S['afir_src'].format(date=self.date(A['checked'])), afir_url=A['url'],
            routes_url=ROUTES[l]), 'pay')

    # ---------------- routes
    def route_title(self, rt, l):
        return f"{town(rt['waypoints'][0][0], l)} — {town(rt['waypoints'][-1][0], l)}"

    def route_url(self, rt, l):
        return f"{ROUTES[l]}{rt['id']}/"

    def trip_costs(self, rt, l):
        eu = self.M.europe['dc']
        km = country_km(rt)
        miss = []
        price = {}
        for cc in km:
            v = ((self.M.countries.get(cc) or {}).get('cls') or {}).get('dc', {}).get('value')
            if v is None:
                miss.append(self.cname(cc, l))
                v = eu
            price[cc] = v
        cars = []
        for car in self.M.cars():
            cost = sum(km[cc] * car['cons'] / 100 * price[cc] for cc in km)
            cars.append(dict(name=car['name'], cons=self.W.fmt_num(car['cons'], self.W.L[l], 1), cost=self.WP.money(cost, 'EUR', l, 0)))
        note = self.S[l]['cost_note'].format(eu=self.WP.money(eu, 'EUR', l), miss=', '.join(miss) if miss else self.S[l]['cost_all'])
        return cars, note

    def page_route(self, rt, l, urls):
        S = self.S[l]
        rule = self.RT['rule']
        a, b = town(rt['waypoints'][0][0], l), town(rt['waypoints'][-1][0], l)
        via = S['via'].join(town(w[0], l) for w in rt['waypoints'][1:-1])
        stops = []
        ri = self.RT['routes'].index(rt)
        for si, s in enumerate(rt['stops']):
            city = I.data_text(l, 'routes', f'routes[{ri}].stops[{si}].city', s['city']) if isinstance(s.get('city'), dict) else ''
            stops.append(dict(km=self.W.fmt_num(s['km'], self.W.L[l]), name=s.get('name') or s.get('net') or ('HPC' if s['cls'] == 5 else 'DC'), net=s.get('net') or '',
                              city=city, cc=self.cname(s['cc'], l) if s.get('cc') else '', kw=self.W.fmt_num(s['kw'], self.W.L[l]) if s.get('kw') else '—',
                              pts=s.get('pts') or '—', map=self.w.map_url(l, None, (s['lat'], s['lon']), 16)))
        gaps = [S['gap_line'].format(a=self.W.fmt_num(g[0], self.W.L[l]), b=self.W.fmt_num(g[1], self.W.L[l]), c=self.W.fmt_num(rule['corridor_km'], self.W.L[l]))
                for g in rt['gaps']]
        byc = []
        for x in rt['countries']:
            cc = x['cc']
            byc.append(dict(name=self.cname(cc, l), n=x['n'], nets=', '.join(n for n, _ in x['nets'][:4]),
                            apps=', '.join(ap['name'] for ap in self.apps_in(cc)) or '—', road=self.toll(cc, l),
                            pay=self.pay_url(cc, l) if (cc in self.countries and l in self.langs(cc)) else None))
        cars, cost_note = self.trip_costs(rt, l)
        L = self.W.L[l]
        self.write(l, 'world_pay_route.html', urls[l], urls, dict(
            title=S['t_route'].format(a=a, b=b), h1=S['h1_route'].format(a=a, b=b), description=S['d_route'].format(a=a, b=b),
            kick=None, jsonld=None, last=f'{a} — {b}', crumbs=[(S['nav_routes'], ROUTES[l])],
            checked=S['checked'].format(date=self.date(self.RT['layer_date'])),
            lead=S['lead_route'].format(km=self.W.fmt_num(rt['km'], L), via=via, c=self.W.fmt_num(rule['corridor_km'], L), n=rt['n_fast'], h=rt['n_hpc']),
            stops=stops, gaps=gaps, byc=byc, cars=cars, cost_note=cost_note,
            method=S['method'].format(f=round((rule['road_factor'] - 1) * 100), date=self.date(self.RT['layer_date']), c=self.W.fmt_num(rule['corridor_km'], L))),
            'routes', ups=[ROUTES])

    def page_routes_hub(self, l):
        S = self.S[l]
        L = self.W.L[l]
        rule = self.RT['rule']
        rows = [dict(name=self.route_title(rt, l), url=self.route_url(rt, l), km=self.W.fmt_num(rt['km'], L), n=rt['n_fast'],
                     gaps=len(rt['gaps'])) for rt in self.RT['routes']]
        self.write(l, 'world_pay_routes.html', ROUTES[l], ROUTES, dict(
            title=S['t_routes'], h1=S['h1_routes'], description=S['d_routes'], kick=S['kick_routes'], crumbs=None, jsonld=None,
            lead=S['lead_routes'].format(c=self.W.fmt_num(rule['corridor_km'], L), s=self.W.fmt_num(rule['step_km'], L)),
            checked=S['checked'].format(date=self.date(self.RT['layer_date'])), rows=rows,
            method=S['method'].format(f=round((rule['road_factor'] - 1) * 100), date=self.date(self.RT['layer_date']), c=self.W.fmt_num(rule['corridor_km'], L)),
            pay_url=PAY[l]), 'routes')


def prepare():
    """Menu entries (called by gen_com before the world pages, so every world page shows them)."""
    import world_shell
    S = load_strings()
    world_shell.EXTRA = [(PAY, {l: S[l]['nav_pay'] for l in LANGS}, 'pay'), (ROUTES, {l: S[l]['nav_routes'] for l in LANGS}, 'routes')]


def run(G, wctx):
    if wctx is None:
        print('world pay/routes: skipped (no world layer in this build)')
        return None
    errs = validate()
    if errs:
        raise SystemExit('world pay: pay.json / routes.json fail the check:\n  ' + '\n  '.join(errs[:30]))
    S = load_strings()
    r = R(G, wctx, S)
    for l in LANGS:
        r.page_pay_hub(l)
        r.page_routes_hub(l)
    for cc in r.countries:
        ls = r.langs(cc)
        urls = {l: r.pay_url(cc, l) for l in ls}
        for l in ls:
            r.page_pay_country(cc, l, urls)
    for rt in r.RT['routes']:
        urls = {l: r.route_url(rt, l) for l in LANGS}
        for l in LANGS:
            r.page_route(rt, l, urls)
    print(f"world pay/routes: {r.n} HTML ({len(r.countries)} pay countries, {len(r.RT['routes'])} routes; "
          f"{len(r.P['apps'])} apps); public={r.public}")
    return r


def selftest():
    errs = validate()
    load_strings()
    assert not errs, errs
    R_ = load_json(WORLD / 'routes.json')
    for rt in R_['routes']:
        km = country_km(rt)
        assert abs(sum(km.values()) - rt['km']) < 5, (rt['id'], sum(km.values()), rt['km'])
    assert town('Beograd', 'en') == 'Belgrade' and town('Beograd', 'ru') == 'Белград'
    print(f"world_pay selftest ok: {len(R_['routes'])} routes, {len(load_json(WORLD / 'pay.json')['apps'])} apps")


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'selftest'
    if cmd == 'validate':
        e = validate()
        print('\n'.join(e) or 'ok')
        sys.exit(1 if e else 0)
    selftest()
