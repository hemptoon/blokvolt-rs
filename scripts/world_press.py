"""G7: the European EV Charging Price Index as a monthly issue, and the page for media (/press/).

Builds on the price layer of G3 (scripts/world_prices.py). Each month gets a frozen snapshot of the index in
content/world/index_history/<YYYY-MM>.json (committed); the issue pages, the archive CSV files and the charts are
built from the snapshots, so a past issue never changes when the tariffs change later.

    python3 scripts/world_press.py snapshot [--force]   # freeze the index of the month of tariffs.json `updated`
    python3 scripts/world_press.py facts <YYYY-MM> <en|sr|ru|de|fr>   # the key sentences of an issue (for the press release draft)
    python3 scripts/world_press.py selftest

Pages (with the world layer only, like G3; noindex while content/world/config.json `public` is false):
  /press/ /sr/za-medije/ /ru/dlya-smi/              — latest issue, charts to embed, citation rules, contact, archive
  <press>/<YYYY-MM>/                                 — the issue of a month
  <press>/embed/<chart>/                             — chart for an iframe on other sites (always the latest issue)
  /press/charts/<YYYY-MM>-<chart>-<lang>.svg        — chart files of a month (print, fixed month)
  /charging-prices/data/blokvolt-ev-charging-price-index-<YYYY-MM>.csv — archive of past months (G3 writes the current one)
Driver check-ins (G6) enter the issue when content/world/checkins_month.json exists ({"YYYY-MM": {"confirmed": n}}).
RUNBOOK 3.43.
"""
import csv
import datetime as dt
import html
import io
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import world_prices as WP  # noqa: E402

ROOT = WP.ROOT
WORLD = WP.WORLD
HIST = WORLD / 'index_history'
CHECKINS = WORLD / 'checkins_month.json'
LANGS = WP.LANGS
I = WP.I                                              # LANG0: languages, section paths, names of the other languages
PRESS = {l: I.slugs(l)['press'] for l in LANGS}       # /press/ /sr/za-medije/ /ru/dlya-smi/ /de/… (config / slugs.json)
CHART_DIR = '/press/charts/'
CHARTS = ('dc-vs-home', 'europe')
SITE_URL = 'https://blokvolt.com'
FORBIDDEN = WP.FORBIDDEN + [r'\bmy\s', r'редакци']


def load_strings():
    raw = json.load(open(WORLD / 'strings_press.json', encoding='utf-8'))
    for k, v in raw.items():
        for l in I.BASE:
            if l in LANGS and not v.get(l):
                raise SystemExit(f'world press: strings_press.json: "{k}" has no {l}')
    return I.load('press', LANGS)   # LANG0: other languages from i18n/<code>/strings_press.json (stops on a missing key)


def strings_of(l, S=None):
    """LANG1 (D2): the press strings of one language — the built ones when the language is enabled, otherwise straight
    from i18n/<code>/strings_press.json (the press release drafts of G7 in de, fr … while the site has only en/sr/ru).
    No built-in German or French any more: a language without its f_* keys stops with the name of the file."""
    S = S if S is not None else load_strings()
    if l in S:   # a built language: its own strings (a preview shows "[EN] …" where a translation is missing)
        return S[l]
    p = I.i18n_dir(l) / 'strings_press.json'
    tr = json.load(open(p, encoding='utf-8')) if p.exists() else {}
    raw = json.load(open(WORLD / 'strings_press.json', encoding='utf-8'))
    miss = [k for k in raw if k.startswith('f_') and not str(tr.get(k) or '').strip()]
    if miss:
        raise SystemExit(f'world press: {p} lacks {", ".join(miss)} (the facts of an issue in {l} come from there — LANG_pool D2)')
    return {k: (tr.get(k) if tr.get(k) not in (None, '') else raw[k]['en']) for k in raw}


# ------------------------------------------------------------------ snapshots
def snapshot_of(M):
    """The frozen index of a month from the G3 model."""
    W = M.W
    countries = {}
    for cc, c in sorted(M.countries.items()):
        if not c['indexed']:
            continue
        countries[cc] = dict(
            ac=c['cls']['ac']['value'], dc=c['cls']['dc']['value'], hpc=c['cls']['hpc']['value'],
            m={k: c['cls'][k]['method'] for k in ('ac', 'dc', 'hpc')}, home=c['home'], home_src=c['home_src'],
            ratio=c['ratio'], nets=len(c['nets_priced']), cover_dc=round(c['cls']['dc']['cover'], 4), n_dc=c['cls']['dc']['n'])
    nets_idx = len({(cc, n) for cc in M.countries for k in ('ac', 'dc', 'hpc') for n in M.net_values(cc, k)})
    r6 = lambda x: None if x is None else round(x, 6)
    for c in countries.values():
        for k in ('ac', 'dc', 'hpc', 'home', 'ratio'):
            c[k] = r6(c[k])
    return dict(v=1, month=M.month, tariffs_updated=M.T['updated'], weights_layer=W['date'], fx_date=M.FX['date'],
                home_period=M.H['period'], europe={k: r6(M.europe[k]) for k in ('ac', 'dc', 'hpc')}, europe_n=M.europe_n,
                networks_indexed=nets_idx, countries=countries,
                frozen=dt.date.today().isoformat())


def load_history():
    """{month: snapshot}, oldest first."""
    out = {}
    if HIST.is_dir():
        for p in sorted(HIST.glob('20??-??.json')):
            s = json.load(open(p, encoding='utf-8'))
            if s.get('month') != p.stem:
                raise SystemExit(f'world press: {p.name} holds month {s.get("month")}')
            out[p.stem] = s
    return out


def cmd_snapshot(force=False):
    M = WP.Model()
    s = snapshot_of(M)
    HIST.mkdir(parents=True, exist_ok=True)
    p = HIST / f"{s['month']}.json"
    if p.exists() and not force:
        old = json.load(open(p, encoding='utf-8'))
        same = {k: v for k, v in old.items() if k != 'frozen'} == {k: v for k, v in s.items() if k != 'frozen'}
        print(f'{p.name} exists ({"unchanged" if same else "DIFFERENT from the current tariffs — use --force to refreeze"})')
        return 0 if same else 1
    p.write_text(json.dumps(s, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f"{p.relative_to(ROOT)}: {len(s['countries'])} countries, Europe DC {s['europe']['dc']:.3f} EUR/kWh")
    return 0


# ------------------------------------------------------------------ facts of an issue
def prev_month(hist, month):
    ms = [m for m in hist if m < month]
    return ms[-1] if ms else None


def month_name(ym, l):
    """D3: "November 2026", "novembar 2026.", "ноябрь 2026" (en/sr/ru as before); every other language the stand-alone
    month in the nominative and the year (Babel "LLLL y": "listopad 2026", "листопад 2026")."""
    return WP.month_label(ym, l)


def eur(x, l):
    return WP.money(x, 'EUR', l)


def cents(x, l):
    v = x * 100
    s = f'{v:+.1f}'
    if l != 'en':
        s = s.replace('.', I.reg(l)['dec'] if l not in ('sr', 'ru') else ',')
    return {'en': f'{s} ct', 'sr': f'{s} c', 'ru': f'{s} ц.'}.get(l, f'{s} ct')   # euro cent: "ct" outside sr/ru


def checkins_of(month):
    if not CHECKINS.exists():
        return None
    return (json.load(open(CHECKINS, encoding='utf-8')).get(month) or {}).get('confirmed')


class Names:
    def __init__(self):
        self.N = {r['cc']: r for r in csv.DictReader(open(WORLD / 'names' / 'countries.csv', encoding='utf-8'))}

    def name(self, cc, l):
        r = self.N[cc]
        if l not in I.BASE:   # i18n/<code>/countries.csv of any language, built or not (press release drafts)
            return I.country_name(r, l)
        return r.get(f'name_{l}') or r['name_en']

    def in_(self, cc, l):
        """D1: "in Germany" / "u Nemačkoj" / "в Германии"; every other language its in_phrase of i18n/<code>/countries.csv
        ("in den Niederlanden", "aux Pays-Bas", "w Niemczech") — no built-in German or French list any more."""
        r = self.N[cc]
        if l == 'en':
            return 'in ' + ('the ' if cc in ('US', 'GB', 'NL', 'PH', 'AE') else '') + r['name_en']
        if l == 'sr':
            return r['sr_u']
        if l == 'ru':
            return r['ru_v']
        return I.country_in(r, l)


def num(x, l, d=1):
    s = f'{x:.{d}f}'
    return s if l == 'en' else s.replace('.', ',' if l in ('sr', 'ru') else I.reg(l)['dec'])


def facts(hist, month, l, names=None):
    """Key sentences of an issue: Europe, range of DC, DC vs home, month on month, check-ins. Only numbers of the snapshot."""
    SL = strings_of(l)
    names = names or Names()

    def T(k, **kw):   # D2: f_* of the language's own strings_press (built, or i18n/<code>/ for a draft)
        return SL[k].format(**kw)
    s = hist[month]
    E = s['europe']
    out = [T('f_europe', dc=eur(E['dc'], l), hpc=eur(E['hpc'], l), ac=eur(E['ac'], l))]
    dc = sorted(((c['dc'], cc) for cc, c in s['countries'].items() if c['dc'] is not None))
    if len(dc) >= 2:
        out.append(T('f_range', lo=names.in_(dc[0][1], l), lo_v=eur(dc[0][0], l), hi=names.in_(dc[-1][1], l), hi_v=eur(dc[-1][0], l)))
    rt = sorted(((c['ratio'], cc) for cc, c in s['countries'].items() if c['ratio']))
    if len(rt) >= 2:
        out.append(T('f_home', lo_r=num(rt[0][0], l), lo=names.name(rt[0][1], l), hi_r=num(rt[-1][0], l), hi=names.name(rt[-1][1], l)))
    pm = prev_month(hist, month)
    if pm:
        P = hist[pm]
        if E['dc'] and P['europe']['dc']:
            d = E['dc'] - P['europe']['dc']
            out.append(T('f_mom', prev=month_name(pm, l), d=cents(d, l), p=num(100 * d / P['europe']['dc'], l) + ' %'))
        ch = []
        for cc, c in s['countries'].items():
            pc = P['countries'].get(cc)
            if pc and c['dc'] is not None and pc['dc'] is not None and abs(c['dc'] - pc['dc']) >= 0.005:
                ch.append((abs(c['dc'] - pc['dc']), cc, c['dc'] - pc['dc']))
        ch.sort(reverse=True)
        if ch:
            out.append(T('f_mom_n', list=', '.join(f'{names.name(cc, l)} {cents(d, l)}' for _, cc, d in ch[:3])))
    else:
        out.append(T('f_first'))
    n = checkins_of(month)
    if n:
        out.append(T('f_checkins', n=n))
    return out


# ------------------------------------------------------------------ charts (standalone SVG: inline styles, no page CSS)
DC_COL, HOME_COL, GRID, INK, MUTED = '#2E6BFF', '#9AA3AF', '#dfe3ea', '#0B1220', '#5b6472'


def svg_dc_home(s, l, names, title, desc, legend, credit):
    rows = sorted(((names.name(cc, l), c['dc'], c['home']) for cc, c in s['countries'].items() if c['dc'] is not None), key=lambda r: r[1])
    vmax = max(max(d or 0, h or 0) for _, d, h in rows)
    vmax = (int(vmax * 10) + 1) / 10
    lw, bw, rh, top = 140, 440, 30, 40
    W = lw + bw + 70
    H = top + rh * len(rows) + 70
    sx = lambda v: lw + bw * v / vmax
    e = html.escape
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" role="img" aria-labelledby="t d" '
         f'font-family="Onest, system-ui, -apple-system, Segoe UI, sans-serif" font-size="13">',
         f'<title id="t">{e(title)}</title><desc id="d">{e(desc)}</desc><rect width="{W}" height="{H}" fill="#fff"/>',
         f'<text x="12" y="22" font-size="15" font-weight="600" fill="{INK}">{e(title)}</text>']
    for i in range(int(vmax * 10) + 1):
        x = sx(i / 10)
        p.append(f'<line x1="{x:.1f}" y1="{top - 6}" x2="{x:.1f}" y2="{H - 64}" stroke="{GRID}"/>'
                 f'<text x="{x:.1f}" y="{H - 50}" text-anchor="middle" font-size="11" fill="{MUTED}">{num(i / 10, l)}</text>')
    for i, (nm, d, h) in enumerate(rows):
        y = top + i * rh
        p.append(f'<text x="{lw - 8}" y="{y + 15}" text-anchor="end" fill="{INK}">{e(nm)}</text>')
        p.append(f'<rect x="{lw}" y="{y + 3}" width="{sx(d) - lw:.1f}" height="11" rx="2" fill="{DC_COL}"/>'
                 f'<text x="{sx(d) + 4:.1f}" y="{y + 13}" font-size="11" fill="{MUTED}">{num(d, l, 2)}</text>')
        if h is not None:
            p.append(f'<rect x="{lw}" y="{y + 16}" width="{sx(h) - lw:.1f}" height="8" rx="2" fill="{HOME_COL}"/>'
                     f'<text x="{sx(h) + 4:.1f}" y="{y + 24}" font-size="10" fill="{MUTED}">{num(h, l, 2)}</text>')
    yl = H - 30
    p.append(f'<rect x="12" y="{yl - 9}" width="10" height="10" fill="{DC_COL}"/><text x="27" y="{yl}" font-size="11" fill="{INK}">{e(legend[0])}</text>'
             f'<rect x="140" y="{yl - 9}" width="10" height="10" fill="{HOME_COL}"/><text x="155" y="{yl}" font-size="11" fill="{INK}">{e(legend[1])}</text>'
             f'<text x="12" y="{H - 10}" font-size="11" fill="{MUTED}">{e(credit)}</text></svg>')
    return ''.join(p)


def svg_europe(s, l, labels, title, desc, credit):
    vals = [(labels[k], s['europe'][k]) for k in ('ac', 'dc', 'hpc') if s['europe'][k] is not None]
    vmax = (int(max(v for _, v in vals) * 10) + 1) / 10
    lw, bw, rh, top = 130, 450, 40, 44
    W = lw + bw + 70
    H = top + rh * len(vals) + 40
    sx = lambda v: lw + bw * v / vmax
    e = html.escape
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="100%" role="img" aria-labelledby="t d" '
         f'font-family="Onest, system-ui, -apple-system, Segoe UI, sans-serif" font-size="13">',
         f'<title id="t">{e(title)}</title><desc id="d">{e(desc)}</desc><rect width="{W}" height="{H}" fill="#fff"/>',
         f'<text x="12" y="22" font-size="15" font-weight="600" fill="{INK}">{e(title)}</text>']
    for i, (nm, v) in enumerate(vals):
        y = top + i * rh
        p.append(f'<text x="{lw - 8}" y="{y + 18}" text-anchor="end" fill="{INK}">{e(nm)}</text>'
                 f'<rect x="{lw}" y="{y + 4}" width="{sx(v) - lw:.1f}" height="20" rx="3" fill="{DC_COL}"/>'
                 f'<text x="{sx(v) + 6:.1f}" y="{y + 19}" font-weight="600" fill="{INK}">{eur(v, l)}</text>')
    p.append(f'<text x="{W - 10}" y="{H - 12}" text-anchor="end" font-size="11" fill="{MUTED}">{e(credit)}</text></svg>')
    return ''.join(p)


def charts_of(s, l, S, names):
    m = month_name(s['month'], l)
    credit = S[l]['credit'].format(month=m) + ' · blokvolt.com'
    return {'dc-vs-home': svg_dc_home(s, l, names, S[l]['ch_dc_home'], S[l]['ch_dc_home_d'], (S[l]['lg_dc'], S[l]['lg_home']), credit),
            'europe': svg_europe(s, l, {k: S[l]['cls_' + k] for k in ('ac', 'dc', 'hpc')}, S[l]['ch_europe'], S[l]['ch_europe_d'], credit)}


# ------------------------------------------------------------------ archive CSV (same columns as G3's index CSV)
def archive_csv(s):
    f = io.StringIO()
    w = csv.writer(f, lineterminator='\n')
    w.writerow(['month', 'country', 'ac_eur_kwh', 'ac_method', 'dc_eur_kwh', 'dc_method', 'hpc_eur_kwh', 'hpc_method',
                'dc_networks', 'dc_chargers_covered_pct', 'home_eur_kwh', 'home_source', 'dc_vs_home', 'prices_checked',
                'weights_layer', 'licence', 'source'])
    meth = {'w': 'weighted', 'm': 'median', None: ''}
    r4 = lambda x: '' if x is None else f'{x:.4f}'
    src = 'BlokVolt, European EV Charging Price Index, https://blokvolt.com/charging-prices/'
    for cc, c in sorted(s['countries'].items()):
        w.writerow([s['month'], cc, r4(c['ac']), meth[c['m']['ac']], r4(c['dc']), meth[c['m']['dc']], r4(c['hpc']), meth[c['m']['hpc']],
                    c['n_dc'], round(100 * c['cover_dc'], 1), r4(c['home']), c['home_src'] or '',
                    '' if c['ratio'] is None else f"{c['ratio']:.2f}", s['tariffs_updated'], s['weights_layer'], 'CC BY-NC 4.0', src])
    E = s['europe']
    w.writerow([s['month'], 'EUROPE', r4(E['ac']), 'weighted', r4(E['dc']), 'weighted', r4(E['hpc']), 'weighted',
                s['europe_n']['dc'], '', '', '', '', s['tariffs_updated'], s['weights_layer'], 'CC BY-NC 4.0', src])
    return f.getvalue()


# ------------------------------------------------------------------ build
def prepare(G):
    """Before the world pages: the footer link (world_shell) and the link on the price hub. Only with the price layer."""
    if not getattr(G, 'WORLD_PRICES', None) or not load_history():
        return
    S = load_strings()
    import world_shell
    world_shell.PRESS = {l: (PRESS[l], S[l]['ft_press']) for l in LANGS}
    G.env.globals['PRESS_LINK'] = {l: (PRESS[l], S[l]['for_media_link']) for l in LANGS}


class Press(WP.R):
    def __init__(self, G, wctx):
        super().__init__(G, wctx, WP.load_strings())
        self.SP = load_strings()
        for l in LANGS:              # one namespace P for the templates: price strings + press strings
            self.S[l] = dict(self.S[l], **self.SP[l])
        self.names = Names()

    def issue_url(self, month, l):
        return f'{PRESS[l]}{month}/'

    def embed_url(self, chart, l):
        return f'{PRESS[l]}embed/{chart}/'

    def svg_url(self, month, chart, l):
        return f'{CHART_DIR}{month}-{chart}-{l}.svg'

    def rows(self, s, prev, l):
        out = []
        for cc, c in sorted(s['countries'].items(), key=lambda kv: (kv[1]['dc'] is None, kv[1]['dc'] or 9)):
            pc = (prev or {}).get('countries', {}).get(cc) if prev else None
            ch = '—'
            if pc and c['dc'] is not None and pc['dc'] is not None:
                ch = cents(c['dc'] - pc['dc'], l)
            cells = [self.pz(c[k], l) + (f' <small class="muted">{self.S[l]["mark_median"]}</small>' if c['m'][k] == 'm' else '')
                     for k in ('ac', 'dc', 'hpc')]
            url = self.site.country(cc, l) if cc in self.site.countries else None
            out.append(dict(name=self.names.name(cc, l), url=url, cells=cells, home=self.pz(c['home'], l),
                            ratio=(num(c['ratio'], l) + '×') if c['ratio'] else '—', change=ch))
        return out

    def run(self):
        hist = load_history()
        if not hist:
            print('world press: no snapshot in content/world/index_history/ — skipped')
            return 0
        months = list(hist)
        last = months[-1]
        n = 0
        # chart files and archive CSV
        d = self.G.OUT / CHART_DIR.strip('/')
        d.mkdir(parents=True, exist_ok=True)
        for m, s in hist.items():
            for l in LANGS:
                for k, svg in charts_of(s, l, self.SP, self.names).items():
                    (d / f'{m}-{k}-{l}.svg').write_text(svg, encoding='utf-8')
                    n += 1
            p = self.G.OUT / WP.DATA_DIR.strip('/') / WP.csv_names(m)[0]
            if not p.exists():      # G3 writes the current month from the live model
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(archive_csv(s), encoding='utf-8')
                n += 1
        for m in months:
            self.page_issue(hist, m)
        self.page_press(hist, last)
        for k in CHARTS:
            for l in LANGS:
                self.page_embed(hist[last], k, l)
        print(f'world press: {len(months)} issue(s), latest {last}; {self.n_written} HTML, {n} chart/CSV files')
        return self.n_written + n

    def common(self, s, l):
        S = self.S[l]
        m = month_name(s['month'], l)
        csv_name = WP.csv_names(s['month'])[0]
        return dict(month=m, credit=S['credit'].format(month=m), csv=(WP.DATA_DIR + csv_name, S['data_csv'] + ' · ' + m),
                    hub_url=WP.HUB[l], method_url=WP.HUB[l] + '#method')

    def page_issue(self, hist, month):
        s = hist[month]
        pm = prev_month(hist, month)
        prev = hist[pm] if pm else None
        urls = {x: self.issue_url(month, x) for x in LANGS}
        for l in LANGS:
            S = self.S[l]
            c = self.common(s, l)
            charts = charts_of(s, l, self.SP, self.names)
            note = S['issue_note'].format(fx=WP.fdate(s['fx_date']), checked=WP.fdate(s['tariffs_updated']), layer=WP.fdate(s['weights_layer']),
                                          home=self.period_of(s['home_period'], l))
            ld = {'@context': 'https://schema.org', '@graph': [
                {'@type': 'Dataset', 'name': f"European EV Charging Price Index — {month_name(month, 'en')}",
                 'url': self.G.SITE + urls['en'], 'description': self.SP['en']['d_issue'].format(month=month_name(month, 'en')),
                 'license': 'https://creativecommons.org/licenses/by-nc/4.0/', 'isAccessibleForFree': True, 'temporalCoverage': month,
                 'dateModified': s['tariffs_updated'], 'creator': {'@type': 'Organization', 'name': 'BlokVolt', 'url': self.G.SITE + '/'},
                 'distribution': [{'@type': 'DataDownload', 'encodingFormat': 'text/csv', 'contentUrl': self.G.SITE + c['csv'][0]}]},
                {'@type': 'BreadcrumbList', 'itemListElement': [
                    {'@type': 'ListItem', 'position': 1, 'name': S['nav_press'], 'item': self.G.SITE + PRESS[l]},
                    {'@type': 'ListItem', 'position': 2, 'name': c['month'], 'item': self.G.SITE + urls[l]}]}]}
            self.write(l, 'world_press_issue.html', urls[l], urls, dict(
                c, title=S['t_issue'].format(month=c['month']), h1=S['h1_issue'].format(month=c['month']),
                description=S['d_issue'].format(month=c['month']), kick=S['kick_issue'],
                lead=S['lead_issue'].format(nets=s['networks_indexed'], countries=len(s['countries'])),
                crumbs=[(S['nav_press'], PRESS[l])], last=c['month'],
                checked=S['issue_of'].format(date=WP.fdate(s['tariffs_updated'])),
                facts=facts(hist, month, l, self.names), tiles=[(self.pz(s['europe'][k], l), S['cls_' + k]) for k in ('ac', 'dc', 'hpc')],
                rows=self.rows(s, prev, l), has_prev=bool(prev), chart=charts['dc-vs-home'], note=note,
                svgs=[(self.svg_url(month, k, l), S['ch_dc_home'] if k == 'dc-vs-home' else S['ch_europe']) for k in CHARTS],
                press_url=PRESS[l], jsonld=json.dumps(ld, ensure_ascii=False).replace('</', '<\\/')), section='press')

    def period_of(self, p, l):
        y, h = p.split('-S')
        return {'en': f'Eurostat, {"first" if h == "1" else "second"} half of {y}', 'sr': f'Eurostat, {h}. polugodište {y}.',
                'ru': f'Eurostat, {"первое" if h == "1" else "второе"} полугодие {y}'}.get(l, f'Eurostat {y}-S{h}')   # LANG0: Eurostat's own notation

    def page_press(self, hist, last):
        s = hist[last]
        urls = dict(PRESS)
        for l in LANGS:
            S = self.S[l]
            c = self.common(s, l)
            charts = charts_of(s, l, self.SP, self.names)
            emb = []
            for k in CHARTS:
                src = self.G.SITE + self.embed_url(k, l)
                hgt = 600 if k == 'dc-vs-home' else 240
                ttl = S['ch_dc_home'] if k == 'dc-vs-home' else S['ch_europe']
                code = (f'<iframe src="{src}" title="{html.escape(ttl)}" width="100%" height="{hgt}" style="border:0;max-width:720px" '
                        f'loading="lazy"></iframe>')
                emb.append(dict(title=ttl, svg=charts[k], code=code, file=(self.svg_url(last, k, l), S['svg_file'].format(month=c['month']))))
            cite = S['credit'].format(month=c['month']) + f', {self.G.SITE}{WP.HUB[l]}'
            archive = [(self.issue_url(m, l), month_name(m, l)) for m in reversed(list(hist))]
            self.write(l, 'world_press.html', urls[l], urls, dict(
                c, title=S['t_press'], h1=S['h1_press'], description=S['d_press'], kick=S['kick_press'], lead=S['lead_press'],
                checked=S['issue_of'].format(date=WP.fdate(s['tariffs_updated'])),
                h_latest=S['h_latest'].format(month=c['month']), issue_url=self.issue_url(last, l), facts=facts(hist, last, l, self.names),
                emb=emb, cite=cite, contact=S['contact_p'].format(email=f'<a href="mailto:{self.G.EMAIL}">{self.G.EMAIL}</a>'),
                archive=archive), section='press')

    def page_embed(self, s, k, l):
        S = self.S[l]
        svg = charts_of(s, l, self.SP, self.names)[k]
        url = self.embed_url(k, l)
        page = ('<!doctype html><html lang="{l}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
                '<meta name="robots" content="noindex"><title>{t}</title><link rel="canonical" href="{canon}">'
                '<style>html,body{{margin:0;background:#fff}}body{{font:13px system-ui,sans-serif;color:#0B1220}}'
                'a{{color:#5b6472}}p{{margin:4px 10px}}</style></head><body>{svg}'
                '<p><a href="{hub}" target="_blank" rel="noopener">{credit} · blokvolt.com</a></p></body></html>').format(
            l=l, t=html.escape(S['embed_title'] + ' — ' + (S['ch_dc_home'] if k == 'dc-vs-home' else S['ch_europe'])),
            canon=self.G.SITE + self.issue_url(s['month'], l), svg=svg, hub=self.G.SITE + WP.HUB[l],
            credit=html.escape(S['credit'].format(month=month_name(s['month'], l))))
        self.G.write(url, page)
        self.n_written += 1


def run(G, wctx):
    if not getattr(G, 'WORLD_PRICES', None) or wctx is None:
        print('world press: skipped (no price layer in this build)')
        return None
    return Press(G, wctx).run()


# ------------------------------------------------------------------ self test
def selftest():
    import re
    ok = True

    def chk(c, m):
        nonlocal ok
        if not c:
            ok = False
            print('FAIL', m)
    S = load_strings()
    for l in LANGS:
        for k, v in S[l].items():
            for pat in FORBIDDEN:
                if re.search(pat, v, re.I):
                    chk(False, f'forbidden "{pat}" in {k}/{l}')
    en_keys = {k: set(re.findall(r'{(\w+)}', v)) for k, v in S['en'].items()}
    for l in LANGS:
        for k, v in S[l].items():
            chk(set(re.findall(r'{(\w+)}', v)) == en_keys[k], f'placeholders {k}/{l}')
    hist = load_history()
    chk(hist, 'at least one snapshot in content/world/index_history/')
    if hist:
        M = WP.Model()
        cur = snapshot_of(M)
        if cur['month'] in hist:
            a = {k: v for k, v in hist[cur['month']].items() if k != 'frozen'}
            b = {k: v for k, v in cur.items() if k != 'frozen'}
            if a != b:
                print(f"NOTE: tariffs.json differs from the frozen {cur['month']} snapshot — the issue keeps the frozen numbers "
                      f"(refreeze with `snapshot --force` only before the issue is announced)")
        names = Names()
        for m in hist:
            drafts = tuple(x for x in ('de', 'fr') if x not in LANGS and (I.i18n_dir(x) / 'strings_press.json').exists())
            for l in LANGS + drafts:   # D2: de/fr drafts only once their strings_press.json is merged (L2 → FIXL → LANGI)
                fs = facts(hist, m, l, names)
                chk(len(fs) >= 3, f'facts {m} {l}')
                chk(all('{' not in f for f in fs), f'facts unfilled {m} {l}')
            for l in LANGS:
                for k, svg in charts_of(hist[m], l, S, names).items():
                    chk(svg.startswith('<svg') and svg.endswith('</svg>') and '<title' in svg, f'svg {m} {k} {l}')
            rows = list(csv.reader(io.StringIO(archive_csv(hist[m]))))
            chk(rows[-1][1] == 'EUROPE' and len(rows) == len(hist[m]['countries']) + 2, f'csv {m}')
        # month on month: a fake next month moves Germany by +2 ct
        last = list(hist)[-1]
        y, mo = map(int, last.split('-'))
        nxt = f'{y + mo // 12}-{mo % 12 + 1:02d}'
        fake = json.loads(json.dumps(hist[last]))
        fake['month'] = nxt
        if 'DE' in fake['countries'] and fake['countries']['DE']['dc']:
            fake['countries']['DE']['dc'] += 0.02
        fake['europe']['dc'] += 0.01
        h2 = dict(hist, **{nxt: fake})
        fs = facts(h2, nxt, 'en', names)
        chk(any('+1.0 ct' in f for f in fs), 'month on month Europe')
        chk(any('Germany +2.0 ct' in f for f in fs), 'month on month countries')
        chk(month_name('2026-11', 'de') == 'November 2026' and month_name('2026-11', 'fr') == 'novembre 2026', 'month de/fr')
        chk(month_name('2026-11', 'hr') == 'studeni 2026' and month_name('2026-11', 'uk') == 'листопад 2026', 'month hr/uk (D3)')
        chk(month_name('2026-11', 'en') == 'November 2026' and month_name('2026-11', 'sr') == 'novembar 2026.', 'month en/sr')
        chk(names.in_('NL', 'fr') == I.country_in(names.N['NL'], 'fr'), 'in_ fr from countries.csv (D1)')
    print('world_press selftest:', 'OK' if ok else 'FAILED')
    return 0 if ok else 1


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[:1] == ['selftest']:
        sys.exit(selftest())
    if a[:1] == ['snapshot']:
        sys.exit(cmd_snapshot('--force' in a))
    if a[:1] == ['facts'] and len(a) == 3:
        h = load_history()
        if a[1] not in h:
            sys.exit(f'no snapshot {a[1]}')
        for f in facts(h, a[1], a[2]):
            print('-', f)
        sys.exit(0)
    print(__doc__)
