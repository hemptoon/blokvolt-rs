#!/usr/bin/env python3
"""World map check-ins (G6): weekly rules for the prices drivers report, and candidates for the price index.

The worker stores „Radi / Ne radi / Zauzeto“ and „Koliko ste platili“ in D1 world_checkins (/api/svet/stanje). This script
  1. reads them (GET /api/admin/svet/stanje?view=export, or a fixture file);
  2. compares every new price with the network's published ad hoc tariff (content/world/tariffs.json, G3) and fx.json:
       per kWh within 0.6–1.6 × the list price            → match        (tariff_match)
       per kWh below 0.25 × or above 4 × the list price   → auto_hidden  (tariff_impossible)
       per kWh outside 0.03–3.00 EUR (any network)        → auto_hidden  (impossible)
       anything else per kWh with a known tariff          → off          (tariff_off: the owner decides on /admin/svet/)
       per minute / per session, unknown currency or no tariff → no_ref (kept, not compared)
     and sends the decisions back (POST {auto}); a human decision is never overwritten (the worker checks it);
  3. builds candidates: the same network, country, power class, unit and currency, in the last 6 months, with at least
     two independent drivers (different day fingerprints) whose prices agree within 3 % — the candidate price is the
     median of that group. Candidates go to content/world/checkin_prices.json (status "candidate"); nothing on the site
     uses them until the owner adds them to the index (G3/G7 methodology: „cene vozača“ are shown next to the list price,
     never instead of it).
  4. writes stats.json and queue.md (prices for the owner) to --out.

  ADMIN_KEY=… python3 scripts/world_checkins.py --api https://www.blokvolt.rs --out /tmp/ci [--write-content]
  python3 scripts/world_checkins.py --fixture FILE.json --out /tmp/ci        (no network, implies --dry-run)
  python3 scripts/world_checkins.py --selftest

ADMIN_KEY is read from the environment only and never printed. Stdlib only.
"""
import argparse
import json
import os
import statistics
import sys
import time
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORLD = ROOT / 'content' / 'world'
UA = 'BlokVolt-world-checkins/1.0 (+https://www.blokvolt.rs)'
POST_MAX = 1000
RULES = dict(match_lo=0.6, match_hi=1.6, impossible_lo=0.25, impossible_hi=4.0, eur_min=0.03, eur_max=3.0,
             agree=0.03, window_days=183, min_drivers=2)


# ------------------------------------------------------------------------------------------------ tariffs (G3)
def load_tariffs(path=None):
    """{(cc, network name as in the layer): {'ac': (eur, local), 'dc': …, 'hpc': …, 'cur': 'EUR', 'network': …, 'id': …}}
    — the same choice of rows and columns as the price line of the map card (world_prices.map_payload)."""
    T = json.load(open(path or WORLD / 'tariffs.json', encoding='utf-8'))
    out = {}
    for r in T['rows']:
        if r.get('plan') != 'adhoc' or r.get('unit') != 'kWh' or r.get('exclude'):
            continue
        dc = (r.get('hpc_eur'), r.get('hpc')) if r.get('dc_is_hpc_col') else (r.get('dc_eur'), r.get('dc'))
        e = dict(id=r['id'], network=r['network'], cur=r.get('currency') or 'EUR', ac=(r.get('ac_eur'), r.get('ac')), dc=dc,
                 hpc=(r.get('hpc_eur'), r.get('hpc')) if r.get('hpc_150') else (None, None))
        if all(e[k][0] is None for k in ('ac', 'dc', 'hpc')):
            continue
        for name in [r['network']] + list(r.get('layer') or []):
            out.setdefault((r['cc'], name), e)      # the first row of a network is its base tariff (T1 order)
    return out


def load_fx(path=None):
    fx = json.load(open(path or WORLD / 'fx.json', encoding='utf-8'))
    rates = dict(fx['rates'])
    rates['EUR'] = 1.0
    return rates


def ref_eur(t, cls):
    """list price in EUR per kWh for a power class (hpc falls back to dc, unknown class → dc, then ac)"""
    if not t:
        return None
    order = {'hpc': ('hpc', 'dc'), 'dc': ('dc',), 'ac': ('ac',)}.get(cls, ('dc', 'ac'))
    for k in order:
        if t[k][0] is not None:
            return t[k][0]
    return None


# ------------------------------------------------------------------------------------------------ rules
def classify(ci, tariffs, rates, R=RULES):
    """(price_status, rule, eur per unit or None, list price EUR or None) for one check-in with a price"""
    amt, unit, cur = ci.get('amt'), ci.get('unit'), (ci.get('cur') or '').upper()
    rate = rates.get(cur)
    eur = round(amt / rate, 4) if (amt is not None and rate) else None
    if unit != 'kwh':
        return 'no_ref', 'unit_not_kwh', eur, None
    if eur is None:
        return 'no_ref', 'currency_unknown', None, None
    if eur < R['eur_min'] or eur > R['eur_max']:
        return 'auto_hidden', 'impossible', eur, None
    ref = ref_eur(tariffs.get((ci.get('cc'), ci.get('net'))), ci.get('cls'))
    if ref is None:
        return 'no_ref', 'no_tariff', eur, None
    k = eur / ref
    if R['match_lo'] <= k <= R['match_hi']:
        return 'match', 'tariff_match', eur, ref
    if k < R['impossible_lo'] or k > R['impossible_hi']:
        return 'auto_hidden', 'tariff_impossible', eur, ref
    return 'off', 'tariff_off', eur, ref


def decide(rows, tariffs, rates, R=RULES):
    """decisions for the rows whose price is still „new“ → [{id, price_status, rule}]"""
    out = []
    for r in rows:
        if r.get('amt') is None or r.get('price_status') != 'new' or r.get('status') != 'ok':
            continue
        st, rule, _, _ = classify(r, tariffs, rates, R)
        out.append(dict(id=r['id'], price_status=st, rule=rule))
    return out


def candidates(rows, tariffs, rates, now, R=RULES):
    """two or more independent drivers with the same price → one candidate per (cc, network, class, unit, currency)"""
    usable = {'match', 'no_ref', 'accepted'}
    groups = defaultdict(list)
    for r in rows:
        if r.get('amt') is None or r.get('status') != 'ok' or r.get('price_status') not in usable:
            continue
        if not r.get('cc') or not r.get('net') or r['created_at'] < now - R['window_days'] * 86400:
            continue
        groups[(r['cc'], r['net'], r.get('cls') or '', r['unit'], (r['cur'] or '').upper())].append(r)
    out = []
    for (cc, net, cls, unit, cur), rs in sorted(groups.items()):
        rs = sorted(rs, key=lambda x: x['amt'])
        best = []
        for i, a in enumerate(rs):      # the largest group of prices within ±agree of its lowest price
            grp = [b for b in rs[i:] if b['amt'] <= a['amt'] * (1 + R['agree'])]
            if len({b['ip_hash'] for b in grp}) > len({b['ip_hash'] for b in best}):
                best = grp
        drivers = {b['ip_hash'] for b in best}
        if len(drivers) < R['min_drivers']:
            continue
        price = round(statistics.median(b['amt'] for b in best), 4)
        rate = rates.get(cur)
        eur = round(price / rate, 4) if rate else None
        ref = ref_eur(tariffs.get((cc, net)), cls or None) if unit == 'kwh' else None
        out.append(dict(cc=cc, network=net, cls=cls or None, unit=unit, cur=cur, price=price, eur=eur, drivers=len(drivers),
                        n=len(best), first=min(b['ym'] for b in best), last=max(b['ym'] for b in best),
                        last_at=max(b['created_at'] for b in best), list_eur=ref,
                        vs_list=round(eur / ref, 3) if (eur and ref) else None, status='candidate'))
    return out


def stats(rows, decisions, cands, now):
    week = [r for r in rows if r['created_at'] >= now - 7 * 86400]
    by = lambda it, k: dict(sorted(((x, sum(1 for r in it if (r.get(k) or '—') == x)) for x in {(r.get(k) or '—') for r in it})))
    return dict(now=now, total=len(rows), week=len(week), week_by_state=by(week, 's'), week_by_country=by(week, 'cc'),
                week_prices=sum(1 for r in week if r.get('amt') is not None),
                decisions=by(decisions, 'price_status'), candidates=len(cands),
                places_confirmed_30d=len({r['pid'] for r in rows if r.get('s') == 'radi' and r['status'] == 'ok'
                                          and r['created_at'] >= now - 30 * 86400}))


def queue_md(rows, decisions, tariffs, rates):
    ids = {d['id'] for d in decisions if d['price_status'] == 'off'}
    lines = ['# Cene vozača — za pregled (tariff_off)', '', 'Odluka na /admin/svet/ (Prihvati / Odbij).', '']
    for r in rows:
        if r['id'] in ids or (r.get('price_status') == 'off' and r.get('status') == 'ok'):
            _, _, eur, ref = classify(r, tariffs, rates)
            lines.append(f"- #{r['id']} pid {r['pid']} · {r.get('cc')} · {r.get('net') or '?'} · {r.get('cls') or '?'} · "
                         f"{r['amt']} {r['cur']}/{r['unit']} ({r['ym']}) ≈ {eur} EUR, cenovnik {ref} EUR")
    if len(lines) == 4:
        lines.append('Nema cena za pregled.')
    return '\n'.join(lines) + '\n'


# ------------------------------------------------------------------------------------------------ API
def _api(url, key, body=None):
    data = None if body is None else json.dumps(body).encode('utf-8')
    req = urllib.request.Request(url, data=data, method='GET' if body is None else 'POST',
                                 headers={'Authorization': 'Bearer ' + key, 'User-Agent': UA, 'content-type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode('utf-8'))


def run(args, env=os.environ):
    now = int(time.time())
    if args.fixture:
        rows = json.load(open(args.fixture, encoding='utf-8'))['checkins']
        args.dry_run = True
        now = int(json.load(open(args.fixture, encoding='utf-8')).get('now') or now)
    else:
        key = env.get('ADMIN_KEY')
        if not key:
            raise SystemExit('world_checkins: ADMIN_KEY is not set in the environment; refusing to call the API')
        j = _api(f"{args.api.rstrip('/')}/api/admin/svet/stanje?view=export&since={int(args.since)}", key)
        if not j.get('ok'):
            raise SystemExit('world_checkins: export not ok')
        rows, now = j['checkins'], int(j.get('now') or now)
    tariffs, rates = load_tariffs(), load_fx()
    dec = decide(rows, tariffs, rates)
    sent = 0
    if dec and not args.dry_run:
        for i in range(0, len(dec), POST_MAX):
            sent += int(_api(f"{args.api.rstrip('/')}/api/admin/svet/stanje", env['ADMIN_KEY'], {'auto': dec[i:i + POST_MAX]}).get('n') or 0)
    by_id = {d['id']: d['price_status'] for d in dec}
    rows2 = [dict(r, price_status=by_id.get(r['id'], r.get('price_status'))) for r in rows]
    cands = candidates(rows2, tariffs, rates, now)
    payload = dict(v=1, about='Prices reported by drivers on the world map (G6). Candidates only: two or more independent drivers, '
                   'the same price within 3 %, last 6 months. Not part of the price index until the owner adds them (RUNBOOK 3.43).',
                   date=time.strftime('%Y-%m-%d', time.gmtime(now)), fx=json.load(open(WORLD / 'fx.json', encoding='utf-8'))['date'],
                   rows=cands)
    out = Path(args.out) if args.out else None
    if out:
        out.mkdir(parents=True, exist_ok=True)
        (out / 'decisions.json').write_text(json.dumps(dec, ensure_ascii=False, indent=1), encoding='utf-8')
        (out / 'checkin_prices.json').write_text(json.dumps(payload, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        (out / 'stats.json').write_text(json.dumps(stats(rows2, dec, cands, now), ensure_ascii=False, indent=1), encoding='utf-8')
        (out / 'queue.md').write_text(queue_md(rows2, dec, tariffs, rates), encoding='utf-8')
    if args.write_content:
        (WORLD / 'checkin_prices.json').write_text(json.dumps(payload, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f"world_checkins: {len(rows)} check-ins, {len(dec)} new prices decided "
          f"({', '.join(f'{k} {v}' for k, v in sorted(stats(rows2, dec, cands, now)['decisions'].items())) or 'none'}), "
          f"{'dry run' if args.dry_run else f'{sent} stored'}, {len(cands)} candidate(s)")
    return dict(decisions=dec, candidates=cands)


def selftest():
    """the rules on the real tariffs.json, without the network"""
    T, X = load_tariffs(), load_fx()
    errs = []
    k = next(((cc, n) for (cc, n), e in T.items() if e['cur'] == 'EUR' and e['dc'][0]), None)
    if not k:
        return print('world_checkins selftest: no EUR tariff with DC') or 1
    ref = T[k]['dc'][0]
    base = dict(id=1, pid=10, cc=k[0], net=k[1], cls='dc', unit='kwh', cur='EUR', ym='2026-11', status='ok', price_status='new')
    for amt, want in ((ref, 'match'), (ref * 1.3, 'match'), (ref * 2.5, 'off'), (ref * 5, 'auto_hidden'), (0.01, 'auto_hidden'),
                      (ref * 0.3, 'off'), (ref * 0.2, 'auto_hidden')):
        got = classify(dict(base, amt=amt), T, X)[0]
        if got != want:
            errs.append(f'{amt:.3f} EUR vs list {ref}: {got}, expected {want}')
    if classify(dict(base, amt=0.5, net='No Such Network'), T, X)[1] != 'no_tariff':
        errs.append('unknown network is not no_tariff')
    if classify(dict(base, amt=0.5, unit='min'), T, X)[0] != 'no_ref':
        errs.append('per minute is compared')
    for e in errs:
        print('FAIL', e)
    print(f'world_checkins selftest ({len(T)} tariff keys, {k[1]} {k[0]} DC {ref} EUR):', 'OK' if not errs else f'{len(errs)} problem(s)')
    return 1 if errs else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description='World map check-ins: price rules and index candidates (G6).')
    ap.add_argument('--api', help='site base URL, e.g. https://www.blokvolt.rs (ADMIN_KEY from env)')
    ap.add_argument('--fixture', help='export JSON {"now": …, "checkins": [...]} instead of the API (implies --dry-run)')
    ap.add_argument('--out', help='output directory: decisions.json, checkin_prices.json, stats.json, queue.md')
    ap.add_argument('--since', type=int, default=0)
    ap.add_argument('--dry-run', action='store_true', help='compute and write files, do not POST')
    ap.add_argument('--write-content', action='store_true', help='also write content/world/checkin_prices.json')
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if not a.api and not a.fixture:
        ap.error('--api or --fixture is required')
    run(a)
    return 0


if __name__ == '__main__':
    sys.exit(main())
