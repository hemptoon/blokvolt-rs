# -*- coding: utf-8 -*-
"""Price layer of blokvolt.com (task G3 of pool G): the European EV Charging Price Index, country and network price
pages in EN / SR / RU, CSV downloads, and the price line on the world map card.

Data: scripts/world_prices_data.py (tariffs.json, price_weights.json, home_electricity.json, fx.json; RUNBOOK 3.42).
Strings: content/world/strings_prices.json (the build stops on a missing language). Templates: templates/com2/world_prices_*.html.

Pages (noindex and out of the sitemap while content/world/config.json "public" is false — same switch as the world layer):
  /charging-prices/                              /sr/cene-punjenja/                  /ru/tseny-zaryadki/
  /charging-prices/<country>/                    (country slug of K4, per language)
  /charging-prices/<country>/<network>/
  /charging-prices/data/blokvolt-ev-charging-price-index-<YYYY-MM>.csv and …-tariffs-<YYYY-MM>.csv (CC BY-NC 4.0)
  /assets/world/prices-<hash>.json               ad hoc prices per country × network key, for the map card

Hooks in gen_com.py:
  world_prices.prepare(G)          before world_map.build(): writes the map file, sets G.WORLD_PRICES (nav + map config)
  world_prices.run(G, wctx)        after world_pages.run(): the pages (needs the world layer; skipped without it)
CLI:  python3 scripts/world_prices.py selftest
"""
import csv
import datetime as dt
import hashlib
import io
import json
import os
import re
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import world_prices_data as D   # noqa: E402

ROOT = D.ROOT
WORLD = D.WORLD
import world_i18n as I   # noqa: E402  K8-i18n: languages, addresses and formats from the registry
LANGS = I.langs()
HUB = {l: I.slugs(l)['prices'] for l in LANGS}
DATA_DIR = '/charging-prices/data/'
STALE_DAYS = 365
MIN_COVER = 0.10
MONTHS = {
    'en': 'January February March April May June July August September October November December'.split(),
    'sr': 'januar februar mart april maj jun jul avgust septembar oktobar novembar decembar'.split(),
    'ru': 'январь февраль март апрель май июнь июль август сентябрь октябрь ноябрь декабрь'.split(),
}
SYM = {'EUR': '€', 'USD': '$', 'GBP': '£', 'SEK': 'kr', 'NOK': 'kr', 'DKK': 'kr', 'CZK': 'Kč', 'PLN': 'zł', 'HUF': 'Ft',
       'RON': 'lei', 'CHF': 'CHF'}
NUMF = {'en': ('.', ','), 'sr': (',', '.'), 'ru': (',', ' ')}
# three cars of the blokvolt.rs car reference (content/data/ev-specs.json): small, mid, large
CARS = [('Dacia', 'Spring (LFP 24.3 kWh)'), ('Tesla', 'Model Y RWD (Juniper)'), ('Kia', 'EV9 99.8 kWh')]
MID_CAR = 1
# shares of home / public AC / public DC for the three driver profiles (stated on the page)
PROFILES = [('pr_home', 0.8, 0.1, 0.1), ('pr_mixed', 0.5, 0.25, 0.25), ('pr_street', 0.0, 0.6, 0.4)]
DATE_IN_URL = re.compile(r'/(20\d\d)/(\d\d)/(\d\d)/')
FORBIDDEN = [r'\bodmah\b', r'24/7', r'evolako', r'\bredakcij', r'\bmi\s', r'proverili smo', r'popust', r'скидк', r'\batest']


# ------------------------------------------------------------------ strings and formatting
def load_strings():
    raw = I.strings_raw('prices', LANGS)   # K8: other languages from i18n/<code>/strings_prices.json
    bad = [f'{k}:{l}' for k, v in raw.items() for l in LANGS if not (isinstance(v, dict) and str(v.get(l) or '').strip())]
    if bad:
        raise SystemExit('content/world/strings_prices.json: missing translations — ' + ', '.join(bad[:20]))
    for k, v in raw.items():
        for l in LANGS:
            for pat in I.forbidden(FORBIDDEN, l):
                if re.search(pat, v[l], re.I):
                    raise SystemExit(f'strings_prices.json: "{k}" ({l}) has a forbidden word ({pat})')
    for k in ('t_hub', 't_country', 't_net'):
        if any(re.search(r'\d', raw[k][l]) for l in LANGS):
            raise SystemExit(f'strings_prices.json: title "{k}" must not hold a number (RUNBOOK 3.34)')
    return {l: {k: v[l] for k, v in raw.items()} for l in LANGS}


def fnum(x, l, d=2):
    dec, th = NUMF[l] if l in NUMF else (I.reg(l)['dec'], I.reg(l)['thou'])
    s = f'{abs(x):,.{d}f}'.replace(',', '§').replace('.', dec).replace('§', th)
    return ('−' if x < 0 else '') + s


def money(x, cur, l, d=None):
    """0.47 € / €0.47 (en, symbol before for € $ £) — numbers under 0.10 get three decimals."""
    if x is None:
        return '—'
    d = d if d is not None else (3 if abs(x) < 0.1 else 2)
    if cur in ('HUF',) and d == 2 and abs(x) >= 10:
        d = 0
    n = fnum(x, l, d)
    s = SYM.get(cur, cur)
    if l == 'en' and cur in ('EUR', 'USD', 'GBP'):
        return s + n
    return f'{n} {s}'


def month_label(ym, l):
    if l not in MONTHS:   # LANG1 (D3): other languages — stand-alone month in the nominative + year (CLDR "LLLL y")
        return I.month_label(ym, l)
    y, m = int(ym[:4]), int(ym[5:7])
    nm = MONTHS[l][m - 1]
    return f'{nm} {y}.' if l == 'sr' else f'{nm} {y}'


def fdate(iso):
    if not iso:
        return '—'
    p = iso.split('-')
    return '.'.join(reversed(p)) if len(p) == 3 else f'{p[1]}.{p[0]}'


# ------------------------------------------------------------------ the model
class Model:
    def __init__(self, today=None):
        errs = D.validate()
        if errs:
            raise SystemExit('world prices: tariffs.json / fx.json / home_electricity.json fail the check:\n  ' + '\n  '.join(errs[:30]))
        self.T = D.load_json(D.TARIFFS)
        self.W = D.load_json(D.WEIGHTS)
        self.H = D.load_json(D.HOME)
        self.FX = D.load_json(D.FX)
        self.today = today or self.T['updated']
        self.month = self.T['updated'][:7]
        for r in self.T['rows']:
            r['price_date'] = self.price_date(r)
            r['stale'] = bool(r['price_date']) and (dt.date.fromisoformat(self.today) - dt.date.fromisoformat(r['price_date'])).days > STALE_DAYS
            r['has_price'] = any(r.get(k) is not None for k in ('ac', 'dc', 'hpc'))
            r['out'] = self.out_reason(r)
        self.rows = self.T['rows']
        self.countries = self.compute()

    @staticmethod
    def price_date(r):
        """Date the price is known to hold from: valid_from, else the date in a news URL; '' = unknown (only 'checked')."""
        if r.get('valid_from'):
            v = r['valid_from']
            return v if len(v) == 10 else v + '-01'
        m = DATE_IN_URL.search(r.get('source') or '')
        return '-'.join(m.groups()) if m else ''

    @staticmethod
    def out_reason(r):
        if not r['has_price']:
            return 'none'
        if r['plan'] != 'adhoc':
            return 'plan'
        if r['unit'] != 'kWh':
            return 'unit'
        if r.get('exclude'):
            return 'excl'
        if r['stale']:
            return 'stale'
        return ''

    def weight(self, cc, keys, cls):
        nets = self.W['networks'].get(cc, {})
        k = {'ac': 'ac', 'dc': 'dc50', 'hpc': 'hpc'}[cls]
        return sum(nets.get(x, {}).get(k, 0) for x in keys)

    def net_values(self, cc, cls):
        """{network: (price EUR, weight)} for the index rows of a country; several rows of a network → their mean."""
        acc = {}
        for r in self.rows:
            if r['cc'] != cc or r['out']:
                continue
            v = r.get(cls + '_eur')
            if cls == 'dc' and r.get('dc_is_hpc_col'):      # the dc column is below 50 kW; its top class is DC 50+
                v = r.get('hpc_eur')
            if v is None or (cls == 'hpc' and not r['hpc_150']):
                continue
            acc.setdefault(r['network'], (r['layer'], []))[1].append(v)
        return {n: (sum(vs) / len(vs), self.weight(cc, keys, cls)) for n, (keys, vs) in acc.items()}

    def compute(self):
        out = {}
        pool = {'ac': [], 'dc': [], 'hpc': []}
        for cc in D.SCOPE:
            rows = [r for r in self.rows if r['cc'] == cc]
            home = self.H['values'].get(cc)
            if not rows and not home:
                continue
            c = dict(cc=cc, rows=rows, home=home['eur'] if home else None, home_src=(home or {}).get('src'),
                     nets_priced=sorted({r['network'] for r in rows if r['has_price']}),
                     nets_checked=sorted({r['network'] for r in rows}), cls={})
            tot = self.W['totals'].get(cc, {})
            for cls in ('ac', 'dc', 'hpc'):
                nv = self.net_values(cc, cls)
                wk = {'ac': 'ac', 'dc': 'dc50', 'hpc': 'hpc'}[cls]
                wsum = sum(w for _, w in nv.values())
                withw = [(v, w) for v, w in nv.values() if w > 0]
                known = tot.get(wk, 0) - tot.get('nonet_' + wk, 0)    # places of the class whose network is known
                cover = wsum / known if known > 0 else 0
                res = dict(n=len(nv), cover=cover, value=None, method=None)
                if len(withw) >= 2 and cover >= MIN_COVER:
                    res.update(value=sum(v * w for v, w in withw) / sum(w for _, w in withw), method='w')
                    pool[cls].extend(withw)
                elif len(nv) >= 2:
                    res.update(value=statistics.median(v for v, _ in nv.values()), method='m')
                c['cls'][cls] = res
            c['indexed'] = any(c['cls'][k]['value'] is not None for k in c['cls'])
            dcv = c['cls']['dc']['value']
            c['ratio'] = dcv / c['home'] if dcv and c['home'] else None
            out[cc] = c
        self.europe = {cls: (sum(v * w for v, w in pool[cls]) / sum(w for _, w in pool[cls]) if pool[cls] else None)
                       for cls in pool}
        self.europe_n = {cls: len(pool[cls]) for cls in pool}
        return out

    # cost of 100 km
    def cars(self):
        specs = json.load(open(ROOT / 'content' / 'data' / 'ev-specs.json', encoding='utf-8'))['cars']
        res = []
        for make, model in CARS:
            m = next((c for c in specs if c['make'] == make and c['model'] == model), None)
            if not m or not m.get('cons_kwh_100km'):
                raise SystemExit(f'world prices: car {make} {model} with cons_kwh_100km is missing in content/data/ev-specs.json')
            res.append(dict(name=f'{make} {model}', cons=float(m['cons_kwh_100km'])))
        return res

    def profile_cost(self, c, cons):
        h, a, d = c['home'], c['cls']['ac']['value'], c['cls']['dc']['value']
        out = []
        for key, sh, sa, sd in PROFILES:
            need = [(sh, h), (sa, a), (sd, d)]
            if any(s > 0 and p is None for s, p in need):
                out.append(None)
            else:
                out.append(cons * sum(s * (p or 0) for s, p in need))
        return out


# ------------------------------------------------------------------ the map file (before world_map.build)
def map_payload(M, site_urls):
    nets = {}
    for r in M.rows:
        if r['plan'] != 'adhoc' or r['unit'] != 'kWh' or not r['has_price'] or r.get('exclude'):
            continue
        dcv, dcl = (r.get('hpc_eur'), r.get('hpc')) if r.get('dc_is_hpc_col') else (r.get('dc_eur'), r.get('dc'))
        e = dict(n=r['network'], ac=r.get('ac_eur'), dc=dcv, hpc=r.get('hpc_eur') if r['hpc_150'] else None, cur=r['currency'],
                 l=[r.get('ac'), dcl, r.get('hpc') if r['hpc_150'] else None] if r['currency'] != 'EUR' else None,
                 d=r['price_date'] or r['checked'], old=r['stale'], u=site_urls.get((r['cc'], r['network'])))
        for k in r['layer']:
            key = f"{r['cc']}|{k}"
            if key not in nets:      # first row of a network (T1 lists the base tariff first)
                nets[key] = e
    return dict(v=1, date=M.T['updated'], fx=M.FX['date'], rates=M.FX['rates'], nets=nets)


def prepare(G):
    """Called by gen_com before the world map: the map's price file and the URLs the other world pages link to."""
    G.WORLD_PRICES = None
    if not os.environ.get('BV_WORLD_PAGES'):
        return None
    M = Model()
    names = {r['cc']: r for r in D.csv.DictReader(open(WORLD / 'names' / 'countries.csv', encoding='utf-8'))}
    site = Site(M, names)
    payload = json.dumps(map_payload(M, site.net_paths()), ensure_ascii=False, separators=(',', ':'))
    h = hashlib.sha1(payload.encode()).hexdigest()[:10]
    dst = G.OUT / 'assets' / 'world' / f'prices-{h}.json'
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(payload, encoding='utf-8')
    import world_shell   # G0 menu: "Prices" between Charging stations and Open data
    world_shell.PRICES = dict(hub=HUB, nav={l: load_strings()[l]['nav_prices'] for l in LANGS})
    G.WORLD_PRICES = dict(hub=HUB, nav={l: load_strings()[l]['nav_prices'] for l in LANGS}, map_json=f'/assets/world/{dst.name}', model=M, site=site,
                          country_pages={cc: {l: site.country(cc, l) for l in LANGS} for cc in site.countries})
    return G.WORLD_PRICES


# ------------------------------------------------------------------ URLs
class Site:
    def __init__(self, M, names):
        self.M, self.N = M, names
        self.countries = [cc for cc, c in M.countries.items() if c['nets_priced']]
        self.nets = sorted({(r['cc'], r['network']) for r in M.rows if r['has_price']})
        self.slug = {}
        for cc, net in self.nets:
            s = D.slugify(net)
            while (cc, s) in self.slug.values():
                s += '-2'
            self.slug[(cc, net)] = (cc, s)

    def hub(self, l):
        return HUB[l]

    def country(self, cc, l):
        return f"{HUB[l]}{I.country_slug(self.N[cc], l)}/"

    def net(self, cc, net, l):
        return f'{self.country(cc, l)}{self.slug[(cc, net)][1]}/'

    def net_paths(self):
        return {k: {l: self.net(k[0], k[1], l) for l in LANGS} for k in self.nets}


def csv_names(month):
    return (f'blokvolt-ev-charging-price-index-{month}.csv', f'blokvolt-ev-charging-tariffs-{month}.csv')


# ------------------------------------------------------------------ rendering
class R:
    """Rendering context of one build."""

    def __init__(self, G, wctx, S):
        self.G, self.w, self.S = G, wctx, S
        P = G.WORLD_PRICES
        self.M, self.site = P['model'], P['site']
        self.public = bool(wctx.public)
        self.cars = self.M.cars()
        self.n_written = 0
        self.page_cur = 'EUR'
        self.cur_loc = False   # LANG0: local currency first on the pages of a language's own countries (LANG_pool §0.4)

    def cname(self, cc, l):
        return I.country_name(self.site.N[cc], l)

    def cu(self, cc, l):
        r = self.site.N[cc]
        if l == 'en':
            return 'in ' + ('the ' if cc in ('US', 'GB', 'NL', 'PH', 'AE') else '') + r['name_en']
        if l not in I.BASE:
            return I.country_in(r, l)
        return r['sr_u'] if l == 'sr' else r['ru_v']

    def t(self, l, k, **kw):
        return self.S[l][k].format(**kw)

    def pz(self, eur, l, cur='EUR', loc=None, unit='kWh', cls=''):
        """A price span the currency switch can rewrite: data-e = EUR, data-l = local value, data-c = local currency."""
        if eur is None:
            return '<span class="muted">—</span>'
        u = {'kWh': self.S[l]['per_kwh'], 'min': self.S[l]['per_min'], 'session': self.S[l]['per_session'], '': ''}[unit]
        la = ''
        shown = money(eur, 'EUR', l)
        if loc is not None and cur != 'EUR':
            la = f' data-l="{loc:.4f}" data-c="{cur}"'
            if self.cur_loc:
                shown = money(loc, cur, l)
        elif self.page_cur != 'EUR' and self.page_cur in self.M.FX['rates']:   # EUR figure on a non-euro country page
            la = f' data-l="{eur * self.M.FX["rates"][self.page_cur]:.4f}" data-c="{self.page_cur}" data-a="1"'
            if self.cur_loc:
                shown = '≈ ' + money(eur * self.M.FX['rates'][self.page_cur], self.page_cur, l)
        return f'<span class="pz{(" " + cls) if cls else ""}" data-e="{eur:.4f}"{la} data-u="{u}">{shown}{u}</span>'

    def own_cur(self, cc, l):
        """LANG0 (LANG_pool §0.4): an extra language shows the local currency first on the pages of its own countries
        (SEK, NOK, DKK, PLN, CZK, HUF, RON, BGN, CHF …); everywhere else EUR stays the default."""
        return l not in I.BASE and cc in (I.market(l) or ()) and D.CURRENCY.get(cc, 'EUR') != 'EUR' \
            and D.CURRENCY.get(cc) in self.M.FX['rates']

    def write(self, l, tpl, url, urls, ctx, section='prices'):
        alts = [(I.reg(x)['hreflang'], self.G.SITE + urls[x]) for x in LANGS] + [('x-default', self.G.SITE + urls['en'])]
        Sp = dict(self.w.S[l])
        nav = [(u, n, k) for u, n, k in __import__('world_pages').nav(self.w, l)]
        base = dict(SITE=self.G.SITE, RS=self.G.RS, EMAIL=self.G.EMAIL, CHECKED=fdate(self.M.T['updated']),
                    CHECKED_ISO=self.M.T['updated'], canon=url, path=url, LOC=__import__('world_pages').L[l], S=Sp, P=self.S[l],
                    NAV=nav, SWITCH=[(x, urls[x], self.w.S[x]['lang_label'] if x in I.BASE else I.label(x), I.reg(x)['hreflang']) for x in LANGS], home=self.w.site.hub(l),
                    alts=alts, COUNTRIES=self.G.countries, LOCALS=self.w.local_hubs, C={'checked': fdate(self.M.T['updated'])},
                    robots=None if self.public else 'noindex,nofollow', W=self.w, l=l, section=section, PAGES={},
                    jsonld=None, local_cur=None, WORLD_FT=__import__('world_shell').footer(l), fx_date=fdate(self.M.FX['date']), usd=self.M.FX['rates']['USD'],
                    cur_loc=self.cur_loc, LANGMENU=I.lang_menu(urls, l, [HUB, {x: self.w.site.hub(x) for x in LANGS}]), LANGJS=I.lang_assets(self.G.OUT),
                    FMT={'dec': I.reg(l)['dec'], 'thou': I.reg(l)['thou']} if l not in I.BASE else None)
        base.update(ctx)
        base['title'] = __import__('world_pages').seo_title(base['title'])
        html = self.G.env.get_template(tpl).render(**base)
        for n, h in self.w.ver.items():
            html = html.replace(f'/assets/{n}"', f'/assets/{n}?v={h}"')
        self.G.write(url, html)
        self.w.written.append((l, 'prices', url, self.M.T['updated'], self.public))
        self.n_written += 1

    # ---------------- blocks
    def plan_rows(self, rows, l, cur_c):
        S = self.S[l]
        out = []
        order = sorted(rows, key=lambda r: (r['plan'] != 'adhoc', (r.get('dc_eur') or r.get('hpc_eur') or r.get('ac_eur') or 9), r['network']))
        for r in order:
            if not r['has_price']:
                continue
            unit = r['unit']
            cells = []
            for k in ('ac', 'dc', 'hpc'):
                cells.append(self.pz(r.get(k + '_eur'), l, r['currency'], r.get(k), unit) if r.get(k) is not None else '<span class="muted">—</span>')
            why = {'stale': S['out_stale'], 'unit': S['out_unit'], 'excl': S['out_excl']}.get(r['out'], '')
            fees = '; '.join(x for x in (r.get('session_fee'), r.get('idle_fee')) if x)
            sub = ''
            if r['plan'] == 'subscription':
                sub = S['pay_free'] if not r.get('sub_month') else money(r['sub_month'], r['currency'], l)
            out.append(dict(net=r['network'], plan=S['plan_adhoc'] if r['plan'] == 'adhoc' else S['plan_sub'], cells=cells,
                            sub=sub, fees=fees, src=r.get('source'), kind=S['src_news'] if r['source_kind'] == 'news' else S['src_op'],
                            date=fdate(r['price_date']) if r['price_date'] else '—', checked=fdate(r['checked']), why=why,
                            hpcx=(not r['hpc_150'] and r.get('hpc') is not None), vat=r.get('vat') is False,
                            url=self.site.net(r['cc'], r['network'], l), notes=r.get('notes') if l == 'en' else ''))
        return out

    def car_rows(self, l, home, ac, dc, hpc):
        rows = []
        for car in self.cars:
            cells = [self.pz(None if p is None else p * car['cons'], l, unit='') for p in (home, ac, dc, hpc)]
            rows.append(dict(name=car['name'], cons=fnum(car['cons'], l, 1), cells=cells))
        return rows

    # ---------------- pages
    def page_hub(self, l, csvs):
        M, S = self.M, self.S[l]
        urls = {x: HUB[x] for x in LANGS}
        self.page_cur = 'EUR'
        self.cur_loc = False   # LANG0: local currency first on the pages of a language's own countries (LANG_pool §0.4)
        month = month_label(M.month, l)
        rows, empty = [], []
        for cc, c in sorted(M.countries.items(), key=lambda kv: self.cname(kv[0], l)):
            if c['indexed']:
                rows.append(dict(cc=cc, name=self.cname(cc, l), url=self.site.country(cc, l),
                                 cells=[self.pz(c['cls'][k]['value'], l, cls='med' if c['cls'][k]['method'] == 'm' else '') +
                                        (f' <small class="muted">{S["mark_median"]}</small>' if c['cls'][k]['method'] == 'm' else '')
                                        for k in ('ac', 'dc', 'hpc')],
                                 home=self.pz(c['home'], l), ratio=(fnum(c['ratio'], l, 1) + '×') if c['ratio'] else '—',
                                 nets=len(c['nets_priced']), cover=f"{round(100 * c['cls']['dc']['cover'])} %" if c['cls']['dc']['cover'] else '—',
                                 sort=c['cls']['dc']['value'] or 9))
            elif c['nets_checked']:
                empty.append(dict(name=self.cname(cc, l), url=self.site.country(cc, l) if cc in self.site.countries else None,
                                  home=self.pz(c['home'], l),
                                  text=S['too_few'] if c['nets_priced'] else f"{S['no_prices']} — {self.t(l, 'no_prices_n', n=len(c['nets_checked']))}"))
        rows.sort(key=lambda r: r['sort'])
        chart = self.chart(l, [r for r in rows if M.countries[r['cc']]['cls']['dc']['value'] is not None])
        tiles = [(self.pz(M.europe['ac'], l), S['st_ac']), (self.pz(M.europe['dc'], l), S['st_dc']),
                 (self.pz(M.europe['hpc'], l), S['st_hpc']), (str(len(rows)), S['st_countries'])]
        car = self.cars[MID_CAR]
        prof = []
        for r in rows:
            v = M.profile_cost(M.countries[r['cc']], car['cons'])
            if any(x is not None for x in v):
                prof.append(dict(name=r['name'], url=r['url'], cells=[self.pz(x, l, unit='') for x in v]))
        pct = lambda x: f'{round(100 * x)} %'
        shares = [', '.join(filter(None, [self.t(l, 'share_home', x=pct(h)) if h else '', self.t(l, 'share_ac', x=pct(a)) if a else '',
                                          self.t(l, 'share_dc', x=pct(d)) if d else ''])) for _, h, a, d in PROFILES]
        n_ops = len({r['source'] for r in M.rows if r['has_price'] and r['source_kind'] == 'operator'})
        n_news = len({r['source'] for r in M.rows if r['has_price'] and r['source_kind'] == 'news'})
        nets_idx = len({(cc, n) for cc, c in M.countries.items() for k in ('ac', 'dc', 'hpc') for n in M.net_values(cc, k)})
        h1 = self.t(l, 'h1_hub', month=month)
        ld = {'@context': 'https://schema.org', '@graph': [
            {'@type': 'Dataset', 'name': f'European EV Charging Price Index — {month_label(M.month, "en")}', 'url': self.G.SITE + urls['en'],
             'description': self.S['en']['d_hub'], 'license': 'https://creativecommons.org/licenses/by-nc/4.0/', 'isAccessibleForFree': True,
             'dateModified': M.T['updated'], 'temporalCoverage': M.month, 'creator': {'@type': 'Organization', 'name': 'BlokVolt', 'url': self.G.SITE + '/'},
             'distribution': [{'@type': 'DataDownload', 'encodingFormat': 'text/csv', 'contentUrl': self.G.SITE + DATA_DIR + f} for f in csvs]},
            {'@type': 'BreadcrumbList', 'itemListElement': [{'@type': 'ListItem', 'position': 1, 'name': S['nav_prices'], 'item': self.G.SITE + urls[l]}]}]}
        self.write(l, 'world_prices_hub.html', urls[l], urls, dict(
            title=S['t_hub'], h1=h1, description=S['d_hub'], kick=S['kick_index'],
            lead=self.t(l, 'lead_hub', nets=nets_idx, countries=len(rows)), tiles=tiles, rows=rows, empty=empty, chart=chart,
            prof=prof, prof_note=self.t(l, 'profiles_note', car=car['name'], cons=fnum(car['cons'], l, 1), p1=shares[0], p2=shares[1], p3=shares[2]),
            m3=self.t(l, 'm3', layer=fdate(M.W['date'])), m4=self.t(l, 'm4', period=self.period(l), fx=fdate(M.FX['date'])),
            data_p=self.t(l, 'data_p', month=month_label(M.month, 'en'), email=self.G.EMAIL),
            csvs=[(DATA_DIR + csvs[0], S['dl_index']), (DATA_DIR + csvs[1], S['dl_tariffs'])],
            src_ops=self.t(l, 'src_ops', n=n_ops, m=n_news), home_src=M.H['source'], fx_src=M.FX['source'],
            table_note=self.t(l, 'table_note', u=S['mark_median']), rs_index=self.G.RS + '/javno-punjenje/',
            checked=self.t(l, 'prices_checked', date=fdate(M.T['updated'])),
            jsonld=json.dumps(ld, ensure_ascii=False).replace('</', '<\\/')))

    def period(self, l):
        p = self.M.H['period']   # 2026-S1
        y, s = p.split('-S')
        if l not in I.BASE:   # K8: "Januar–Juni 2026" from the CLDR months of the language
            m = I.months(l)
            return f'{m[0]}–{m[5]} {y}' if s == '1' else f'{m[6]}–{m[11]} {y}'
        return {'en': f'{"first" if s == "1" else "second"} half of {y}', 'sr': f'{s}. polugodište {y}.',
                'ru': f'{"первое" if s == "1" else "второе"} полугодие {y}'}[l]

    def chart(self, l, rows):
        """Horizontal bars, EUR/kWh: DC index and home electricity per country. role=img + a text alternative; the table
        below holds the same numbers."""
        if not rows:
            return None
        M = self.M
        data = [(r['name'], M.countries[r['cc']]['cls']['dc']['value'], M.countries[r['cc']]['home']) for r in rows]
        vmax = max(max(d or 0, h or 0) for _, d, h in data)
        vmax = (int(vmax * 10) + 1) / 10
        lw, bw, rh, top = 150, 470, 30, 26
        W = lw + bw + 60
        Hh = top + rh * len(data) + 26
        sx = lambda v: lw + bw * v / vmax
        p = [f'<svg viewBox="0 0 {W} {Hh}" width="100%" role="img" aria-labelledby="wp-ch-t wp-ch-d" class="wp-chart" '
             f'xmlns="http://www.w3.org/2000/svg" font-family="Onest, system-ui, sans-serif" font-size="13">',
             f'<title id="wp-ch-t">{self.S[l]["h_chart"]}</title><desc id="wp-ch-d">{self.S[l]["chart_desc"]}</desc>']
        for i in range(int(vmax * 10) + 1):
            v = i / 10
            x = sx(v)
            p.append(f'<line x1="{x:.1f}" y1="{top - 6}" x2="{x:.1f}" y2="{Hh - 22}" class="wp-grid"/>'
                     f'<text x="{x:.1f}" y="{Hh - 6}" text-anchor="middle" class="wp-ax">{fnum(v, l, 1)}</text>')
        for i, (nm, d, h) in enumerate(data):
            y = top + i * rh
            p.append(f'<text x="{lw - 8}" y="{y + 15}" text-anchor="end" class="wp-lb">{nm}</text>')
            if d is not None:
                p.append(f'<rect x="{lw}" y="{y + 3}" width="{sx(d) - lw:.1f}" height="11" rx="2" class="wp-dc"/>'
                         f'<text x="{sx(d) + 4:.1f}" y="{y + 13}" class="wp-v">{fnum(d, l)}</text>')
            if h is not None:
                p.append(f'<rect x="{lw}" y="{y + 16}" width="{sx(h) - lw:.1f}" height="8" rx="2" class="wp-home"/>')
        p.append('</svg>')
        return '\n'.join(p)

    def country_blocks(self, cc, l):
        M, S = self.M, self.S[l]
        c = M.countries[cc]
        v = {k: c['cls'][k]['value'] for k in ('ac', 'dc', 'hpc')}
        tiles = [(self.pz(v['ac'], l), S['st_ac']), (self.pz(v['dc'], l), S['st_dc']), (self.pz(v['hpc'], l), S['st_hpc']),
                 (self.pz(c['home'], l), S['st_home'])]
        return c, v, tiles

    def links_more(self, cc, l):
        S, out = self.S[l], []
        if cc in self.w.site.country_pages:
            out.append((self.w.site.country(cc, l), self.t(l, 'more_stations', country_u=self.cu(cc, l))))
        loc = next((h for h in self.w.local_hubs if h['loc']['dir'] == cc.lower()), None)
        if loc:
            out.append((loc['path'], f"{S['more_local']}: /{cc.lower()}/"))
        out.append((self.w.map_url(l, {'zemlja': cc}), S['more_map']))
        out.append((HUB[l], S['more_index']))
        return out

    def page_country(self, cc, l):
        M, S, site = self.M, self.S[l], self.site
        urls = {x: site.country(cc, x) for x in LANGS}
        self.page_cur = D.CURRENCY.get(cc, 'EUR')
        self.cur_loc = self.own_cur(cc, l)
        c, v, tiles = self.country_blocks(cc, l)
        cu = self.cu(cc, l)
        cur = D.CURRENCY.get(cc, 'EUR')
        title = self.t(l, 't_country', country_u=cu)
        plans = self.plan_rows(c['rows'], l, cur)
        adhoc = sorted({r['network'] for r in c['rows'] if r['plan'] == 'adhoc' and r['has_price']})
        subs = []
        for r in c['rows']:
            if r['plan'] == 'subscription' and r['has_price']:
                subs.append(f"{r['network']} ({S['pay_free'] if not r.get('sub_month') else money(r['sub_month'], r['currency'], l)})")
        noprice = [n for n in c['nets_checked'] if n not in c['nets_priced']]
        prof = M.profile_cost(c, self.cars[MID_CAR]['cons'])
        ld = {'@context': 'https://schema.org', '@graph': [
            {'@type': 'WebPage', 'name': title, 'url': self.G.SITE + urls[l], 'inLanguage': __import__('world_pages').L[l]['html'], 'dateModified': M.T['updated']},
            {'@type': 'BreadcrumbList', 'itemListElement': [
                {'@type': 'ListItem', 'position': 1, 'name': S['nav_prices'], 'item': self.G.SITE + HUB[l]},
                {'@type': 'ListItem', 'position': 2, 'name': self.cname(cc, l), 'item': self.G.SITE + urls[l]}]}]}
        self.write(l, 'world_prices_country.html', urls[l], urls, dict(
            title=title, h1=title, description=self.t(l, 'd_country', country_u=cu), kick=S['kick_country'],
            crumbs=[(S['nav_prices'], HUB[l])], last=self.cname(cc, l),
            lead=self.t(l, 'c_lead', n=len(c['nets_priced'])), indexed=c['indexed'], tiles=tiles, plans=plans,
            home=self.pz(c['home'], l),
            home_src=M.H['source'][c['home_src']] if c['home_src'] else None,
            cars=self.car_rows(l, c['home'], v['ac'], v['dc'], v['hpc']),
            prof=[(S[k], self.pz(x, l, unit='')) for (k, *_), x in zip(PROFILES, prof)] if any(x is not None for x in prof) else None,
            pay_adhoc=self.t(l, 'pay_adhoc', list=', '.join(adhoc)) if adhoc else '',
            pay_sub=self.t(l, 'pay_sub', list='; '.join(subs)) if subs else '',
            noprice=self.t(l, 'noprice_p', list=', '.join(noprice)) if noprice else '',
            h_index=self.t(l, 'h_c_index', country_u=cu), more=self.links_more(cc, l), h_more=self.t(l, 'h_more', country_u=cu),
            checked=self.t(l, 'prices_checked', date=fdate(M.T['updated'])), local_cur=cur,
            jsonld=json.dumps(ld, ensure_ascii=False).replace('</', '<\\/')))

    def page_net(self, cc, net, l):
        M, S, site = self.M, self.S[l], self.site
        urls = {x: site.net(cc, net, x) for x in LANGS}
        self.page_cur = D.CURRENCY.get(cc, 'EUR')
        self.cur_loc = self.own_cur(cc, l)
        c = M.countries[cc]
        cu = self.cu(cc, l)
        rows = [r for r in c['rows'] if r['network'] == net]
        title = self.t(l, 't_net', net=net, country_u=cu)
        base = next((r for r in rows if r['plan'] == 'adhoc' and r['unit'] == 'kWh' and r['has_price'] and not r.get('exclude')), None)
        bv = {k: (base.get(k + '_eur') if base else None) for k in ('ac', 'dc', 'hpc')}
        if base and base.get('dc_is_hpc_col'):
            bv['dc'] = base.get('hpc_eur')
        if base and not base['hpc_150']:
            bv['hpc'] = None
        cmp = [(S['th_ac'], self.pz(bv['ac'], l), self.pz(c['cls']['ac']['value'], l)),
               (S['th_dc'], self.pz(bv['dc'], l), self.pz(c['cls']['dc']['value'], l)),
               (S['th_hpc'], self.pz(bv['hpc'], l), self.pz(c['cls']['hpc']['value'], l)),
               (S['th_home'], self.pz(None, l), self.pz(c['home'], l))]
        keys = rows[0]['layer']
        wn = M.W['networks'].get(cc, {})
        pl = {k: sum(wn.get(x, {}).get(k, 0) for x in keys) for k in ('all', 'dc50', 'hpc')}
        station = None
        for k in keys:
            if self.w.site.has_net(cc, k, l):
                station = (self.w.site.net(cc, k, l), self.t(l, 'n_station_page', net=net, country_u=cu))
                break
        ld = {'@context': 'https://schema.org', '@graph': [
            {'@type': 'WebPage', 'name': title, 'url': self.G.SITE + urls[l], 'inLanguage': __import__('world_pages').L[l]['html'], 'dateModified': M.T['updated']},
            {'@type': 'BreadcrumbList', 'itemListElement': [
                {'@type': 'ListItem', 'position': 1, 'name': S['nav_prices'], 'item': self.G.SITE + HUB[l]},
                {'@type': 'ListItem', 'position': 2, 'name': self.cname(cc, l), 'item': self.G.SITE + site.country(cc, l)},
                {'@type': 'ListItem', 'position': 3, 'name': net, 'item': self.G.SITE + urls[l]}]}]}
        n = __import__('world_pages').fmt_num
        L = __import__('world_pages').L[l]
        self.write(l, 'world_prices_network.html', urls[l], urls, dict(
            title=title, h1=title, description=self.t(l, 'd_net', net=net, country_u=cu), kick=S['kick_country'],
            crumbs=[(S['nav_prices'], HUB[l]), (self.cname(cc, l), site.country(cc, l))], last=net, net=net,
            plans=self.plan_rows(rows, l, D.CURRENCY.get(cc, 'EUR')), cmp=cmp, th_this=self.t(l, 'th_this', net=net),
            cars=self.car_rows(l, c['home'], bv['ac'], bv['dc'], bv['hpc']) if base else None,
            places=self.t(l, 'n_places', all=n(pl['all'], L), dc=n(pl['dc50'], L), hpc=n(pl['hpc'], L)) if pl['all'] else S['n_places_none'],
            h_places=self.t(l, 'h_n_places', country_u=cu), station=station,
            map_link=self.w.map_url(l, {'zemlja': cc}), country_url=site.country(cc, l), cname=self.cname(cc, l),
            notes=[r['notes'] for r in rows if r.get('notes')] if l == 'en' else [], local_cur=self.page_cur,
            checked=self.t(l, 'prices_checked', date=fdate(M.T['updated'])),
            jsonld=json.dumps(ld, ensure_ascii=False).replace('</', '<\\/')))


# ------------------------------------------------------------------ CSV
def write_csvs(G, M, site):
    idx_name, tar_name = csv_names(M.month)
    d = G.OUT / DATA_DIR.strip('/')
    d.mkdir(parents=True, exist_ok=True)
    f = io.StringIO()
    w = csv.writer(f, lineterminator='\n')
    w.writerow(['month', 'country', 'ac_eur_kwh', 'ac_method', 'dc_eur_kwh', 'dc_method', 'hpc_eur_kwh', 'hpc_method',
                'dc_networks', 'dc_chargers_covered_pct', 'home_eur_kwh', 'home_source', 'dc_vs_home', 'prices_checked',
                'weights_layer', 'licence', 'source'])
    meth = {'w': 'weighted', 'm': 'median', None: ''}
    r4 = lambda x: '' if x is None else f'{x:.4f}'
    for cc, c in sorted(M.countries.items()):
        if not c['indexed']:
            continue
        k = c['cls']
        w.writerow([M.month, cc, r4(k['ac']['value']), meth[k['ac']['method']], r4(k['dc']['value']), meth[k['dc']['method']],
                    r4(k['hpc']['value']), meth[k['hpc']['method']], k['dc']['n'], round(100 * k['dc']['cover'], 1),
                    r4(c['home']), c['home_src'] or '', '' if c['ratio'] is None else f"{c['ratio']:.2f}", M.T['updated'],
                    M.W['date'], 'CC BY-NC 4.0', 'BlokVolt, European EV Charging Price Index, https://blokvolt.com/charging-prices/'])
    w.writerow([M.month, 'EUROPE', r4(M.europe['ac']), 'weighted', r4(M.europe['dc']), 'weighted', r4(M.europe['hpc']), 'weighted',
                M.europe_n['dc'], '', '', '', '', M.T['updated'], M.W['date'], 'CC BY-NC 4.0',
                'BlokVolt, European EV Charging Price Index, https://blokvolt.com/charging-prices/'])
    (d / idx_name).write_text(f.getvalue(), encoding='utf-8')
    f = io.StringIO()
    w = csv.writer(f, lineterminator='\n')
    cols = ['country', 'network', 'plan', 'ac', 'dc', 'hpc', 'unit', 'currency', 'ac_eur', 'dc_eur', 'hpc_eur', 'hpc_is_150kw',
            'session_fee', 'idle_fee', 'subscription_month', 'vat_included', 'price_from', 'source_url', 'source_kind', 'checked_on',
            'in_index', 'not_in_index_reason', 'licence']
    w.writerow(cols)
    for r in sorted(M.rows, key=lambda r: (r['cc'], r['network'], r['plan'])):
        if not r['has_price']:
            continue
        w.writerow([r['cc'], r['network'], r['plan'], r['ac'] if r['ac'] is not None else '', r['dc'] if r['dc'] is not None else '',
                    r['hpc'] if r['hpc'] is not None else '', r['unit'], r['currency'], r4(r['ac_eur']), r4(r['dc_eur']), r4(r['hpc_eur']),
                    'yes' if r['hpc_150'] else 'no', r.get('session_fee') or '', r.get('idle_fee') or '',
                    '' if r.get('sub_month') is None else r['sub_month'], {True: 'yes', False: 'no', None: ''}[r.get('vat')],
                    r['price_date'], r.get('source') or '', r['source_kind'], r['checked'], 'no' if r['out'] else 'yes',
                    {'plan': 'subscription plan', 'unit': 'not per kWh', 'excl': r.get('exclude') or '', 'stale': 'older than 12 months', '': ''}[r['out']],
                    'CC BY-NC 4.0'])
    (d / tar_name).write_text(f.getvalue(), encoding='utf-8')
    for p in (d / idx_name, d / tar_name):     # the CSV must read back
        list(csv.reader(open(p, encoding='utf-8')))
    return idx_name, tar_name


def copy_assets(G):
    for n in ('world-prices.js', 'world-prices.css'):
        src = ROOT / 'static' / 'com' / n
        dst = G.OUT / 'assets' / 'world' / n
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())


def run(G, wctx):
    P = getattr(G, 'WORLD_PRICES', None)
    if not P or wctx is None:
        print('world prices: skipped (no world layer in this build)')
        return None
    S = load_strings()
    copy_assets(G)
    r = R(G, wctx, S)
    ver = {n: hashlib.sha1((G.OUT / 'assets' / 'world' / n).read_bytes()).hexdigest()[:10] for n in ('world-prices.js', 'world-prices.css')}
    G.env.globals['WP_VER'] = ver
    csvs = write_csvs(G, r.M, r.site)
    for l in LANGS:
        r.page_hub(l, csvs)
        for cc in r.site.countries:
            r.page_country(cc, l)
        for cc, net in r.site.nets:
            r.page_net(cc, net, l)
    M = r.M
    print(f"world prices: {r.n_written} HTML ({len(r.site.countries)} countries, {len(r.site.nets)} networks × {len(LANGS)} languages), "
          f"index {sum(1 for c in M.countries.values() if c['indexed'])} countries; Europe AC {M.europe['ac']:.3f} / DC {M.europe['dc']:.3f} / "
          f"HPC {M.europe['hpc']:.3f} EUR/kWh; public={r.public}")
    return r


# ------------------------------------------------------------------ self test
def selftest():
    ok = True

    def chk(c, m):
        nonlocal ok
        if not c:
            ok = False
            print('FAIL', m)
    chk(money(0.47, 'EUR', 'en') == '€0.47', 'money en')
    chk(money(0.47, 'EUR', 'sr') == '0,47 €', 'money sr')
    chk(money(0.055, 'EUR', 'ru') == '0,055 €', 'money 3 decimals')
    chk(month_label('2026-11', 'sr') == 'novembar 2026.', 'month sr')
    chk(fdate('2026-11-09') == '09.11.2026', 'date')
    chk(Model.price_date({'valid_from': '', 'source': 'https://www.electrive.net/2026/07/01/x/'}) == '2026-07-01', 'date from URL')
    load_strings()
    M = Model()
    chk(M.europe['dc'] and 0.3 < M.europe['dc'] < 1.0, f'Europe DC {M.europe["dc"]}')
    chk(all(r['out'] in ('', 'none', 'plan', 'unit', 'excl', 'stale') for r in M.rows), 'out reasons')
    for cc, c in M.countries.items():
        for k, v in c['cls'].items():
            if v['method'] == 'w':
                chk(v['cover'] >= MIN_COVER, f'{cc} {k} cover')
    chk(M.countries['DE']['cls']['dc']['value'] is not None, 'DE has a DC index')
    stale = [r['id'] for r in M.rows if r['stale']]
    chk('de-tesla-supercharger-adhoc' in stale, 'Tesla DE 2024 is stale')
    M.cars()
    print('world_prices selftest:', 'OK' if ok else 'FAILED')
    return 0 if ok else 1


if __name__ == '__main__':
    if sys.argv[1:] == ['selftest']:
        sys.exit(selftest())
    print(__doc__)
