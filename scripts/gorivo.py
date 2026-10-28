# -*- coding: utf-8 -*-
"""Fuel prices and the page /podaci/cena-goriva-i-struje/ (docs/RUNBOOK.md 3.1 and 3.36).

content/data/gorivo.json is the only place of the fuel prices on the site: one entry per weekly decision of the
Ministarstvo unutrašnje i spoljne trgovine (najviše maloprodajne cene; every Friday, valid from 15.00 for seven days),
newest first, each with its own source. current() gives the newest week in the shape the calculator always used
({date, valid_to, benzin, dizel, label, url}); build.py (the calculator, "Moj auto" on the map), scripts/app_feed.py
(the apps' data.json) and scripts/due.py take the fuel price from here.

page() makes the page — front matter + Markdown — from that file and content/data/kalkulator.json (EPS tariffs, the
calculator's assumptions, the public DC price). build.py calls it at build time: there is no .md file for this page, so
the weekly fuel task changes only the JSON. Every number that changes with the fuel prices stands in a table cell of its
own or carries a separator (dates, 1.298, 236,00), so a new week never leaves a sentence untranslated (scripts/i18n.py
keeps plain integers in its keys).

  python3 scripts/gorivo.py      check the data and print the page (front matter + Markdown)
"""
import datetime as dt
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
import valuta  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PATH = '/podaci/cena-goriva-i-struje/'
HISTORY_ROWS = 26          # weeks in the history table; older ones go under "Starije nedelje"
EV_BAND = (16, 18)         # kWh per 100 km: the range of the assumption (the table uses the calculator's kwh100)


def load():
    return json.load(open(ROOT / 'content' / 'data' / 'gorivo.json', encoding='utf-8'))


def _d(s):
    return dt.datetime.strptime(s, '%d.%m.%Y').date()


def check(g):
    """Stops the build on data that cannot be right: newest first, every week dated, priced and sourced."""
    w = g.get('weeks') or []
    assert w, 'content/data/gorivo.json: no weeks'
    for i, x in enumerate(w):
        where = f"content/data/gorivo.json weeks[{i}] ({x.get('from')})"
        for k in ('from', 'to', 'dizel', 'benzin', 'source', 'url'):
            assert x.get(k) not in (None, ''), f'{where}: "{k}" is missing'
        assert _d(x['from']) < _d(x['to']), f'{where}: "to" must be after "from"'
        for k in ('dizel', 'benzin'):
            assert isinstance(x[k], (int, float)) and 100 <= x[k] <= 400, f'{where}: {k} = {x[k]} RSD per litre?'
        assert x['url'].startswith('https://'), f'{where}: url'
        if i:
            assert _d(x['to']) <= _d(w[i - 1]['from']), f'{where}: the weeks must be newest first and must not overlap'
    gaps = [f"{w[i]['to']}–{w[i - 1]['from']}" for i in range(1, len(w)) if w[i]['to'] != w[i - 1]['from']]
    return gaps


def current(g=None):
    """The newest week in the calculator's old shape."""
    g = g or load()
    w = g['weeks'][0]
    return {'date': w['from'], 'valid_to': w['to'], 'benzin': w['benzin'], 'dizel': w['dizel'], 'label': g['label'], 'url': w['url']}


def sr(x, d=0):
    return valuta.sr_format(x, d)


def iso(s):
    return '-'.join(reversed(s.split('.')))


def page(g=None, calc=None):
    """(meta, markdown body) of /podaci/cena-goriva-i-struje/."""
    g = g or load()
    calc = calc or json.load(open(ROOT / 'content' / 'data' / 'kalkulator.json', encoding='utf-8'))
    check(g)
    W, E, DEF = g['weeks'], calc['eps'], calc['defaults']
    cur = W[0]
    Z = {z['id']: z for z in E['zones']}

    def all_in(x):
        return (x + E['oie'] + E['ee']) * (1 + E['akciza']) * (1 + E['pdv'])

    kwh100, loss = DEF['kwh100'], DEF['loss']
    k_home = kwh100 * (1 + loss / 100)                         # kWh from the meter per 100 km
    nt = {z: all_in(Z[z]['nt']) for z in Z}
    home100 = {z: nt[z] * k_home for z in Z}
    vt100 = {z: all_in(Z[z]['vt']) * k_home for z in Z}
    dc = next(p['rsd_kwh'] for p in calc['public'] if p['id'] == 'dc')
    dc_lo, dc_hi = (float(v) for v in calc['public_range'].replace('–', '-').split('-'))
    dc100 = dc * kwh100
    d100, b100 = cur['dizel'] * DEF['l100_dizel'], cur['benzin'] * DEF['l100_benzin']
    band_home = [nt['plava'] * k * (1 + loss / 100) for k in EV_BAND]
    band_dc = [dc * k for k in EV_BAND]

    def fx(v, d=0, rate=False):
        return str(valuta.fx_num(v, rate=rate, text=sr(v, d), stack=True))

    # since when the fuel prices are what they are now
    j = 0
    while j + 1 < len(W) and (W[j + 1]['dizel'], W[j + 1]['benzin']) == (cur['dizel'], cur['benzin']):
        j += 1
    if j:
        since = ('Cene goriva su iste ' + ('najmanje ' if j + 1 == len(W) else '') + f"od **{W[j]['from']}**, "
                 f"cena struje kod kuće od **{E['valid_from']}**")
    elif len(W) > 1:
        since = (f"Nedelju ranije: evrodizel **{sr(W[1]['dizel'], 2)} RSD**, benzin **{sr(W[1]['benzin'], 2)} RSD**; "
                 f"cena struje kod kuće ista je od **{E['valid_from']}**")
    else:
        since = f"Cena struje kod kuće ista je od **{E['valid_from']}**"
    ratio = dc100 / d100
    dc_cmp = 'manje nego' if ratio < 0.97 else 'više nego' if ratio > 1.03 else 'približno isto kao'
    home_cmp = 'i dalje manje nego na gorivo' if vt100['plava'] < min(d100, b100) else 'više nego na gorivo'

    def hist_row(i, x):
        cells = []
        for k in ('dizel', 'benzin'):
            c = fx(x[k], rate=True)
            if i + 1 < len(W) and x[k] != W[i + 1][k]:
                delta = x[k] - W[i + 1][k]
                c += ' <small>' + ('+' if delta > 0 else '−') + sr(abs(delta), 0 if delta == int(delta) else 2) + '</small>'
            cells.append(c)
        host = urlparse(x['url']).netloc.removeprefix('www.')
        return f"| {x['from']} | {cells[0]} | {cells[1]} | [{host}]({x['url']}) |"

    # on a phone each week is a compact two-line card (bv.css .tw.stack.am: date and source, then the two prices)
    head = '<div class="tw stack am" markdown="1">\n\n| Važi od | Evrodizel (RSD) | Benzin BMB 95 (RSD) | Izvor |\n|---|---|---|---|\n'
    hist = head + '\n'.join(hist_row(i, x) for i, x in enumerate(W[:HISTORY_ROWS])) + '\n\n</div>'
    older = ''
    if len(W) > HISTORY_ROWS:
        older = ('\n\n<details markdown="1">\n<summary>Starije nedelje</summary>\n\n' + head
                 + '\n'.join(hist_row(i, x) for i, x in enumerate(W) if i >= HISTORY_ROWS) + '\n\n</div>\n\n</details>')
    zone_rows = '\n'.join(f"| {Z[z]['name'].replace(' zona', '')} | {fx(nt[z], 2, rate=True)} | {fx(home100[z])} | {fx(vt100[z])} |"
                          for z in ('zelena', 'plava', 'crvena') if z in Z)
    R = g['regime']
    eps_src = E['sources'][0]
    updated = max(cur['from'], '.'.join(reversed(g['published'].split('-'))), key=lambda s: s.split('.')[::-1])
    pct = lambda x: sr(x * 100, 0 if abs(x * 100 - round(x * 100)) < 0.01 else 1)   # noqa: E731

    meta = {
        'thumb': 'vd-gorivo',
        'title': 'Cena goriva danas: koliko košta 100 km na gorivo i struju',
        'h1': f"Cena goriva i struje od {cur['from']}: koliko košta 100 km",
        'description': (f"Cene goriva od {cur['from']}: 100 km na evrodizel {sr(d100)} RSD, na benzin {sr(b100)} RSD, na struju "
                        f"kod kuće noću {sr(home100['plava'])} RSD. Istorija cena po nedeljama, sa izvorima."),
        'kicker': 'Cene goriva i struje',
        'lead': (f"Koliko košta 100 km na evrodizel, benzin i struju kod kuće i na brzom javnom punjaču, po najvišim cenama "
                 f"goriva koje važe do {cur['to']} i tarifama EPS-a. Stranica se ažurira posle svake nove odluke o cenama goriva."),
        'updated': updated,
        'next_check': cur['to'],
        'published': g['published'],
        'modified': iso(updated),
        'priority': '0.8',
        'sources': ' | '.join([f"{R['source']} :: {R['url']}", f"{eps_src['label']} :: {eps_src['url']}"]),
    }
    body = f"""<div class="sum" markdown="1">
- Najviše cene od **{cur['from']}** do **{cur['to']}**: evrodizel **{sr(cur['dizel'], 2)} RSD**, benzin BMB 95 **{sr(cur['benzin'], 2)} RSD** za litar
- **{sr(d100)} RSD** za 100 km na evrodizel, **{sr(b100)} RSD** na benzin
- **{sr(home100['plava'])} RSD** za 100 km strujom kod kuće noću (plava zona), **{sr(dc100)} RSD** na brzom javnom punjaču
- {since}
</div>

## Koliko košta 100 km

| Gorivo ili struja | Cena (RSD) | Potrošnja na 100 km | Za 100 km (RSD) |
|---|---|---|---|
| Evrodizel, litar | {fx(cur['dizel'], rate=True)} | {sr(DEF['l100_dizel'], 1)} l | **{fx(d100)}** |
| Benzin BMB 95, litar | {fx(cur['benzin'], rate=True)} | {sr(DEF['l100_benzin'], 1)} l | **{fx(b100)}** |
| Struja kod kuće noću, kWh | {fx(nt['plava'], 2, rate=True)} | {sr(kwh100)} kWh + {sr(loss)} % gubitaka | **{fx(home100['plava'])}** |
| Javni brzi punjač, kWh | {fx(dc, rate=True)} | {sr(kwh100)} kWh | **{fx(dc100)}** |

Gorivo: najviše maloprodajne cene od {cur['from']} u 15 časova do {cur['to']} u 15 časova. Struja kod kuće: plava zona, niža tarifa, sa svim naknadama, akcizom i PDV-om, uz {sr(loss)} % gubitaka pri punjenju. Javni brzi punjač: prosek računa iz [indeksa cena javnog punjenja](/javno-punjenje/), računi pokazuju {sr(dc_lo)}–{sr(dc_hi)} RSD po kWh. Potrošnja je pretpostavka, ista kao u [kalkulatoru troškova](/alati/kalkulator-troskova/).

## Šta to znači

Kod kuće noću 100 km na struju košta oko {sr(home100['plava'])} RSD, a na evrodizel {sr(d100)} RSD. Danju, po višoj tarifi, isto punjenje kod kuće košta oko {sr(vt100['plava'])} RSD, {home_cmp}. Niža tarifa važi samo uz dvotarifno brojilo, a zona zavisi od ukupne mesečne potrošnje domaćinstva: [cena struje po zonama](/podaci/tarife-eps/).

Na brzom javnom punjaču kWh po računima košta {sr(dc_lo)}–{sr(dc_hi)} RSD, zavisno od mreže i snage koju auto prima, pa 100 km košta {sr(dc_lo * kwh100)}–{sr(dc_hi * kwh100)} RSD. Po proseku računa ({sr(dc)} RSD po kWh) to je oko {sr(dc100)} RSD, {dc_cmp} na evrodizel.

Cene goriva mogu da se promene svakog petka, a cena struje za domaćinstva menja se retko: sadašnja važi od {E['valid_from']}. U iznosima nisu cena auta, kućni punjač, održavanje ni putarina. Za vaš auto, kilometražu i deo punjenja na javnim punjačima: [kalkulator troškova](/alati/kalkulator-troskova/).

<details markdown="1">
<summary>Detalji: pretpostavke i računica</summary>

Potrošnja: evrodizel {sr(DEF['l100_dizel'], 1)} l, benzin {sr(DEF['l100_benzin'], 1)} l i električni auto {sr(kwh100)} kWh na 100 km, kao u kalkulatoru. Za auto koji troši od {EV_BAND[0]} do {EV_BAND[1]} kWh, 100 km kod kuće noću košta {sr(band_home[0])}–{sr(band_home[1])} RSD, a na brzom javnom punjaču {sr(band_dc[0])}–{sr(band_dc[1])} RSD.

Kod kuće se dodaje {sr(loss)} % gubitaka pri punjenju, pa sa brojila ide {sr(k_home, 1)} kWh na 100 km. Cena kWh je cena iz cenovnika EPS-a, uz naknadu za obnovljive izvore ({sr(E['oie'], 3)} RSD) i za energetsku efikasnost ({sr(E['ee'], 3)} RSD), pa akcizu {pct(E['akciza'])} % i PDV {pct(E['pdv'])} %. Na javnom punjaču plaća se kWh koji auto primi.

| Zona | kWh noću (RSD) | 100 km noću (RSD) | 100 km danju (RSD) |
|---|---|---|---|
{zone_rows}

</details>

## Cene goriva po nedeljama

Cene važe od petka u 15 časova sedam dana. Uz cenu je promena u odnosu na prethodnu nedelju, u dinarima.

{hist}{older}

<details markdown="1">
<summary>Detalji: ko određuje cene goriva</summary>

Vlada ograničava cene evrodizela i benzina BMB 95 uredbom koja važi do {R['valid_until']}. Najviša maloprodajna cena, sa PDV-om, jednaka je prosečnoj veleprodajnoj ceni uvećanoj za {R['margin_rsd']} RSD trgovačke marže. Ministarstvo unutrašnje i spoljne trgovine objavljuje nove cene svakog petka, a one važe od 15 časova narednih sedam dana. Na pumpi gorivo ne može biti skuplje od te cene, a može biti jeftinije.

</details>

## Česta pitanja

<details markdown="1">
<summary>Kolika je cena goriva danas?</summary>

Od {cur['from']} u 15 časova do {cur['to']} u 15 časova najviše maloprodajne cene su: evrodizel {sr(cur['dizel'], 2)} RSD i benzin BMB 95 {sr(cur['benzin'], 2)} RSD za litar. Pumpa može da prodaje i jeftinije, ali ne skuplje.

</details>

<details markdown="1">
<summary>Koliko košta 100 km na struju?</summary>

Kod kuće noću oko {sr(home100['plava'])} RSD u plavoj zoni, {sr(home100['zelena'])} RSD u zelenoj i {sr(home100['crvena'])} RSD u crvenoj, za auto koji troši {sr(kwh100)} kWh na 100 km, sa gubicima pri punjenju. Na brzom javnom punjaču oko {sr(dc100)} RSD, po proseku računa od {sr(dc)} RSD po kWh.

</details>

<details markdown="1">
<summary>Kada se menjaju cene goriva?</summary>

Svakog petka. Ministarstvo unutrašnje i spoljne trgovine objavljuje najviše maloprodajne cene evrodizela i benzina BMB 95, koje važe od 15 časova sedam dana. Uredba o ograničenju cena derivata nafte važi do {R['valid_until']}.

</details>
"""
    return meta, body


def text(g=None, calc=None):
    meta, body = page(g, calc)
    return '---\n' + ''.join(f'{k}: {v}\n' for k, v in meta.items()) + '---\n' + body


if __name__ == '__main__':
    _g = load()
    _gaps = check(_g)
    if _gaps:
        print('NOTE: weeks without a decision in content/data/gorivo.json: ' + ', '.join(_gaps), file=sys.stderr)
    print(text(_g))
