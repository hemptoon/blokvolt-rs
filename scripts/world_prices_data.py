# -*- coding: utf-8 -*-
"""Price layer of blokvolt.com (task G3, pool G) — data side: tariffs, weights, home electricity, exchange rates.

Files (all small, committed):
  content/world/tariffs.json          every published tariff row (network × country × plan), source + dates; source of truth
  content/world/price_weights.json    places per network and power class in each country (public, confidence ≥ 50),
                                      counted from the public layer of evdb (K1 odbl-<date>.csv.gz) — weights of the index
  content/world/home_electricity.json household electricity price per country (Eurostat nrg_pc_204, band DC; UK: Ofgem cap)
  content/world/fx.json               exchange rates per 1 EUR (ECB reference rates of one day; RSD — NBS; BAM fixed)

CLI (RUNBOOK 3.42):
  python3 scripts/world_prices_data.py import-t1 <T1_tariffs.csv> [--force]   # first import / full refresh from a T1 run
  python3 scripts/world_prices_data.py weights <odbl-YYYY-MM-DD.csv.gz>       # after every public layer build (weekly)
  python3 scripts/world_prices_data.py validate                               # the build runs the same check and stops
  python3 scripts/world_prices_data.py selftest
"""
import csv
import datetime as dt
import gzip
import json
import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
WORLD = ROOT / 'content' / 'world'
TARIFFS = WORLD / 'tariffs.json'
WEIGHTS = WORLD / 'price_weights.json'
HOME = WORLD / 'home_electricity.json'
FX = WORLD / 'fx.json'

# Europe of the price layer: countries with world pages (K3: EU, EEA, UK, CH) plus HR and SI, whose prices T1 collected
# with the Balkans. The rest of the Balkans (RS, BA, ME, MK, AL, XK) stays with blokvolt.rs and the local sections.
SCOPE = ['AT', 'BE', 'BG', 'CH', 'CY', 'CZ', 'DE', 'DK', 'EE', 'ES', 'FI', 'FR', 'GB', 'GR', 'HR', 'HU', 'IE', 'IS', 'IT',
         'LI', 'LT', 'LU', 'LV', 'MT', 'NL', 'NO', 'PL', 'PT', 'RO', 'SE', 'SI', 'SK']
CURRENCY = {'GB': 'GBP', 'SE': 'SEK', 'NO': 'NOK', 'DK': 'DKK', 'CZ': 'CZK', 'PL': 'PLN', 'HU': 'HUF', 'RO': 'RON',
            'CH': 'CHF', 'LI': 'CHF', 'IS': 'ISK'}          # every other country of SCOPE pays in EUR (BG since 01.01.2026)
EUROSTAT_GEO = {'GR': 'EL', 'GB': 'UK'}

# T1 network label → (shown name, network keys of the public layer it covers). A label not listed here is shown as it
# is and matched to the layer key of the same name. Keys that are ambiguous in the layer (e.g. "ALDI" = Nord + Süd in
# DE) are left out on purpose: a wrong weight is worse than none.
NETMAP = {
    'Vattenfall InCharge': ('Vattenfall InCharge', ['Vattenfall', 'InCharge']),
    'Tesla Supercharger': ('Tesla Supercharger', ['Tesla', 'Tesla Supercharger']),
    'Enel X Way (Enel)': ('Enel X Way', ['Enel X Way']),
    'Pod Point (Pod)': ('Pod Point', ['Pod Point']),
    'Iberdrola | bp pulse': ('Iberdrola | bp pulse', ['Iberdrola bp pulse']),
    'Innogy -> E.ON Drive': ('E.ON Drive (ex innogy)', ['Innogy']),
    'E.ON (E.ON Drive)': ('E.ON Drive', ['E.ON', 'drivE.ON']),
    'bp pulse (Aral pulse)': ('Aral pulse (bp pulse)', ['Aral pulse']),
    'Repsol (Ibil)': ('Repsol (Ibil)', ['Repsol Ibil']),
    'Endesa (Endesa X Way)': ('Endesa X Way', ['Endesa']),
    'ALDI Sued': ('ALDI SÜD', ['ALDI SÜD']),
    'Be Charge (Plenitude On The Road)': ('Plenitude On The Road (ex Be Charge)', ['Be Charge', 'BeCharged']),
    'EnBW (SMATRICS EnBW)': ('SMATRICS EnBW', ['SMATRICS Netz']),
    'Ionity': ('Ionity', ['Ionity', 'IONITY']),
    'Mer': ('Mer', ['MER']),
    'Greenway': ('Greenway', ['Greenway', 'GreenWay', 'Greenway Polska']),
    'Stromnetz Hamburg': ('Hamburger Energiewerke (ex Stromnetz Hamburg)', ['Stromnetz Hamburg']),
    'SureCharge': ('SureCharge → Shell Recharge', ['SureCharge']),
    'ChargePlace Scotland': ('ChargePlace Scotland', ['Chargeplace Scotland']),
    'ELEN (HEP ELEN)': ('ELEN (HEP)', ['ELEN (HEP)', 'ELEN', 'Elen']),
    'Petrol (Petrol Hrvatska)': ('Petrol', ['Petrol', 'Petrol OneCharge']),
    'Hrvatski Telekom (HT punionice)': ('Hrvatski Telekom', ['Hrvatski Telekom (espoTs)']),
    'Greenway (Greenway Croatia)': ('Greenway', ['Greenway', 'GreenWay']),
    'Gremo na elektriko (Elektro Ljubljana)': ('Gremo na elektriko', ['Gremo na elektriko', 'Gremonaelektriko.si', 'Elektro Ljubljana']),
    'Porsche (MOON charge)': ('MOON charge', ['MOON', 'Moon']),
    'Elevat / MasterCharge': ('Elevat / MasterCharge', ['Elevat', 'Elevat/MasterCharge', 'Elevat/Imperla']),
    'SODO (motorway fast chargers)': ('SODO (motorway fast chargers)', ['SODO']),
    'EM (Elektro Maribor?)': ('EM (Elektro Maribor)', []),
    'MOBI.E (EGME tariff reference)': ('MOBI.E — EGME fee', []),
    'EDP': ('EDP', ['EDP', 'EDP Smart']),
    'ESB ecars': ('ESB ecars', ['ESB ecars']),
    'MOL Plugee': ('MOL Plugee', ['MOL Plugee']),
}
# Sources that are news articles quoting the operator (dated, but not the operator's own page)
NEWS = ('electrive.', 'ecomento.', 'mobiflip.', 'testcoches.', 'motorbox.', 'actu-automobile.', 'rouleur-electrique.',
        'bevolt.', 'fdrive.', 'eldebate.', 'eco.sapo.', 'mobilityenergy.', 'biznis.rs')
# Rows that stay out of the index (shown on the pages with the reason). Keys: (cc, T1 label, plan).
LOW = {
    ('ES', 'Mercadona', 'adhoc'): 'price from a news report, not attributed to the operator',
    ('BE', 'Electra', 'adhoc'): 'price blocks on the operator page carry no country label',
    ('IT', 'Electra', 'adhoc'): 'flat price from an app banner; card price not labelled',
    ('ES', 'Repsol (Ibil)', 'subscription'): 'bundle of kWh, no price per kWh',
}
# the hpc column of these rows is a class above 50 / 60 kW, not ≥ 150 kW (T1 notes)
HPC_NOT_150 = {('HR', 'ELEN (HEP ELEN)'), ('HR', 'Petrol (Petrol Hrvatska)'), ('SI', 'SODO (motorway fast chargers)'),
               ('FR', 'MObiVE'), ('FR', 'eborn'), ('PL', 'Greenway'), ('SI', 'Porsche (MOON charge)'),
               ('SI', 'MOL Plugee'), ('CZ', 'Innogy -> E.ON Drive'), ('FR', 'TotalEnergies'), ('HR', 'Electrip')}
# … and for these the "dc" column is a class below 50 kW, so the DC 50–149 kW price of the index is their "hpc" column
DC_IS_HPC_COL = {('HR', 'ELEN (HEP ELEN)'), ('HR', 'Petrol (Petrol Hrvatska)'), ('FR', 'MObiVE'), ('FR', 'eborn'),
                 ('FR', 'TotalEnergies'), ('SI', 'Porsche (MOON charge)')}
UNITS = ('kWh', 'min', 'session')
PLANS = ('adhoc', 'subscription')


def slugify(s):
    s = (s or '').replace('ß', 'ss').replace('đ', 'dj').replace('ø', 'o').replace('æ', 'ae').replace('ł', 'l').replace('&', ' and ')
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')


def num(x):
    x = (x or '').strip()
    if not x:
        return None
    try:
        return float(x)
    except ValueError:
        return None


def load_json(p):
    return json.load(open(p, encoding='utf-8'))


def dump_json(p, obj):
    Path(p).write_text(json.dumps(obj, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')


# ------------------------------------------------------------------ T1 → tariffs.json
def kind_of(url):
    host = urlparse(url or '').netloc.lower()
    if not host:
        return 'none'
    return 'news' if any(n in host for n in NEWS) else 'operator'


def import_t1(path, force=False):
    if TARIFFS.exists() and not force:
        raise SystemExit(f'{TARIFFS.relative_to(ROOT)} exists; it is edited by hand from now on (RUNBOOK 3.42). '
                         'Use --force only for a full refresh from a new T1 run.')
    fx = load_json(FX)
    rows, ids = [], {}
    for r in csv.DictReader(open(path, encoding='utf-8')):
        cc = r['country'].strip()
        if cc not in SCOPE:
            continue
        label = r['network'].strip()
        name, layer = NETMAP.get(label, (label, [label]))
        plan = r['plan'].strip()
        base = f"{cc.lower()}-{slugify(name)}-{'adhoc' if plan == 'adhoc' else 'sub'}"
        ids[base] = ids.get(base, 0) + 1
        rid = base if ids[base] == 1 else f'{base}-{ids[base]}'
        cur = r['currency'].strip()
        row = dict(id=rid, cc=cc, network=name, t1_label=label, layer=layer, plan=plan,
                   ac=num(r['ac_price']), dc=num(r['dc_price']), hpc=num(r['hpc_price']), unit=r['unit'].strip(), currency=cur,
                   session_fee=r['session_fee'].strip() or None, idle_fee=r['idle_fee'].strip() or None,
                   sub_month=num(r['subscription_month']), vat={'yes': True, 'no': False}.get(r['vat_included'].strip()),
                   valid_from=r['valid_from'].strip() or None, source=r['source_url'].strip() or None,
                   source_kind=kind_of(r['source_url']), checked=r['checked_on'].strip(), notes=r['notes'].strip(),
                   hpc_150=(cc, label) not in HPC_NOT_150, dc_is_hpc_col=(cc, label) in DC_IS_HPC_COL,
                   exclude=LOW.get((cc, label, plan)))
        rate = fx['rates'].get(cur) if cur != 'EUR' else 1.0
        for k in ('ac', 'dc', 'hpc'):
            row[k + '_eur'] = round(row[k] / rate, 4) if row[k] is not None and rate else None
        rows.append(row)
    out = dict(v=1, about='Published public charging tariffs (task T1 of the evdb pool, 09.11.2026, then edited by hand). '
                         'Prices with VAT where vat=true; *_eur = price / fx.json rate. RUNBOOK 3.42.',
               updated=max(r['checked'] for r in rows), fx_date=fx['date'], rows=rows)
    dump_json(TARIFFS, out)
    print(f'tariffs.json: {len(rows)} rows, {len({(r["cc"], r["network"]) for r in rows})} networks × countries')


# ------------------------------------------------------------------ weights from the public layer
def power_class_key(pc):
    if pc in ('dc_fast_50_149', 'hpc_150plus'):
        return 'dc50'
    if pc.startswith('ac'):
        return 'ac'
    return 'other'


def weights(odbl_path):
    T = load_json(TARIFFS)
    want = {(r['cc'], k) for r in T['rows'] for k in r['layer']}
    tot, nets = {}, {}
    date = re.search(r'(\d{4}-\d{2}-\d{2})', Path(odbl_path).name)
    with gzip.open(odbl_path, 'rt', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            cc = r['country']
            if cc not in SCOPE or not r['access_class'].startswith('public'):
                continue
            if int(r['confidence'] or 70) < 50:      # Balkan places of BlokVolt carry no number: 70 (decision 2 of 09.11)
                continue
            k = power_class_key(r['power_class'])
            t = tot.setdefault(cc, {'all': 0, 'ac': 0, 'dc50': 0, 'hpc': 0, 'nonet_ac': 0, 'nonet_dc50': 0, 'nonet_hpc': 0})
            t['all'] += 1
            t[k] = t.get(k, 0) + 1
            hpc = r['power_class'] == 'hpc_150plus'
            t['hpc'] += hpc
            if not r['network']:                   # places without a network name: outside the coverage base
                if k in ('ac', 'dc50'):
                    t['nonet_' + k] += 1
                t['nonet_hpc'] += hpc
            if (cc, r['network']) in want:
                n = nets.setdefault(cc, {}).setdefault(r['network'], {'all': 0, 'ac': 0, 'dc50': 0, 'hpc': 0})
                n['all'] += 1
                n[k] = n.get(k, 0) + 1
                n['hpc'] += hpc
    for t in list(tot.values()) + [n for d in nets.values() for n in d.values()]:
        t.pop('other', None)
    out = dict(v=1, about='Public places (access public*, confidence ≥ 50) per country and per network key of the public '
                         'layer, by power class: ac, dc50 (DC ≥ 50 kW), hpc (≥ 150 kW). Weights of the price index.',
               layer=Path(odbl_path).name, date=date.group(1) if date else None, totals=tot, networks=nets)
    dump_json(WEIGHTS, out)
    print(f'price_weights.json: {len(tot)} countries, {sum(len(v) for v in nets.values())} network keys; layer {out["date"]}')


# ------------------------------------------------------------------ validation
ISO = re.compile(r'^\d{4}-\d{2}(-\d{2})?$')


def validate(today=None):
    """Returns a list of problems; the build stops when it is not empty."""
    today = today or dt.date.today().isoformat()
    err = []
    T, fx, H = load_json(TARIFFS), load_json(FX), load_json(HOME)
    for k in ('date', 'source', 'rates'):
        if k not in fx:
            err.append(f'fx.json: no {k}')
    for k in ('period', 'source', 'values'):
        if k not in H:
            err.append(f'home_electricity.json: no {k}')
    seen = set()
    for r in T['rows']:
        w = r.get('id', '?')
        if w in seen:
            err.append(f'{w}: duplicate id')
        seen.add(w)
        if r['cc'] not in SCOPE:
            err.append(f'{w}: country {r["cc"]} outside the price layer')
        if r['plan'] not in PLANS:
            err.append(f'{w}: plan {r["plan"]}')
        if r['unit'] not in UNITS:
            err.append(f'{w}: unit {r["unit"]}')
        if r['currency'] != 'EUR' and r['currency'] not in fx['rates']:
            err.append(f'{w}: no rate for {r["currency"]} in fx.json')
        if not r.get('checked') or not ISO.match(r['checked']) or r['checked'] > today:
            err.append(f'{w}: checked date "{r.get("checked")}"')
        if r.get('valid_from') and (not ISO.match(r['valid_from']) or r['valid_from'] > today):
            err.append(f'{w}: valid_from "{r["valid_from"]}"')
        has = [k for k in ('ac', 'dc', 'hpc') if r.get(k) is not None]
        if has and not r.get('source'):
            err.append(f'{w}: a price without a source')
        if r.get('source') and not r['source'].startswith('https://'):
            err.append(f'{w}: source is not https')
        rate = 1.0 if r['currency'] == 'EUR' else fx['rates'].get(r['currency'])
        for k in has:
            v = r[k]
            if v < 0:
                err.append(f'{w}: {k} < 0')
            if rate:
                e = v / rate
                if r['unit'] == 'kWh' and not 0.05 <= e <= 2.0:
                    err.append(f'{w}: {k} = {e:.3f} EUR/kWh is not plausible')
                if r.get(k + '_eur') is not None and abs(r[k + '_eur'] - e) > 0.01 * max(e, 0.01):
                    err.append(f'{w}: {k}_eur {r[k + "_eur"]} ≠ {k} / rate {e:.4f}')
        if r['plan'] == 'subscription' and r.get('sub_month') is None and has:
            err.append(f'{w}: subscription without a monthly fee')
        if not r.get('layer') and r['network'] not in ('MOBI.E — EGME fee', 'EM (Elektro Maribor)'):
            err.append(f'{w}: no layer key (weights)')
    for cc, v in H['values'].items():
        if cc not in SCOPE:
            continue
        if not 0.03 <= v['eur'] <= 0.8:
            err.append(f'home_electricity {cc}: {v["eur"]} EUR/kWh')
    return err


# ------------------------------------------------------------------ self test
def selftest():
    ok = True

    def chk(c, m):
        nonlocal ok
        if not c:
            ok = False
            print('FAIL', m)
    chk(slugify('ALDI SÜD') == 'aldi-sud', 'slugify umlaut')
    chk(slugify('Iberdrola | bp pulse') == 'iberdrola-bp-pulse', 'slugify pipe')
    chk(kind_of('https://www.electrive.net/x') == 'news', 'news host')
    chk(kind_of('https://www.ionity.eu/subscriptions') == 'operator', 'operator host')
    chk(power_class_key('hpc_150plus') == 'dc50' and power_class_key('ac_11_22') == 'ac', 'power classes')
    errs = validate()
    chk(not errs, 'validate: ' + '; '.join(errs[:5]))
    print('world_prices_data selftest:', 'OK' if ok else 'FAILED')
    return 0 if ok else 1


if __name__ == '__main__':
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        sys.exit(2)
    if a[0] == 'import-t1':
        import_t1(a[1], force='--force' in a)
    elif a[0] == 'weights':
        weights(a[1])
    elif a[0] == 'validate':
        e = validate()
        print('\n'.join(e) or 'tariffs: OK')
        sys.exit(1 if e else 0)
    elif a[0] == 'selftest':
        sys.exit(selftest())
    else:
        print(__doc__)
        sys.exit(2)
