#!/usr/bin/env python3
"""G6: scripts/world_checkins.py — price rules and index candidates on the real tariffs.json and fx.json, a fixture
export, no network.  python3 scripts/qa/world_checkins_test.py"""
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import world_checkins as W  # noqa: E402

fails = oks = 0


def check(cond, what, detail=None):
    global fails, oks
    if cond:
        oks += 1
        print('ok  ', what)
    else:
        fails += 1
        print('FAIL', what, '' if detail is None else '— ' + json.dumps(detail, ensure_ascii=False, default=str)[:400])


T, X = W.load_tariffs(), W.load_fx()
key_eur = next((k for k, e in T.items() if e['cur'] == 'EUR' and e['dc'][0] and e['ac'][0]), None)
key_loc = next((k for k, e in T.items() if e['cur'] not in ('EUR',) and e['cur'] in X and e['dc'][1]), None)
check(key_eur is not None, 'a EUR tariff with AC and DC exists', key_eur)
NOW = 1794225600   # 09.11.2026 12:00 UTC
cc, net = key_eur
dc, ac = T[key_eur]['dc'][0], T[key_eur]['ac'][0]
row = lambda i, **o: dict(dict(id=i, pid=100 + i, s=None, cls='dc', amt=dc, unit='kwh', cur='EUR', ym='2026-11', net=net, cc=cc,
                               lang='en', ip_hash=f'h{i:02d}', created_at=NOW - 86400, status='ok', price_status='new'), **o)

# classify
check(W.classify(row(1), T, X)[:2] == ('match', 'tariff_match'), 'list price → match')
check(W.classify(row(1, cls='ac', amt=ac), T, X)[0] == 'match', 'AC class compares with the AC price')
check(W.classify(row(1, amt=dc * 2.2), T, X)[:2] == ('off', 'tariff_off'), '2.2 × list → off (owner)')
check(W.classify(row(1, amt=dc * 4.5), T, X)[1] in ('tariff_impossible', 'impossible'), '4.5 × list → hidden')
check(W.classify(row(1, amt=5.0), T, X)[:2] == ('auto_hidden', 'impossible'), '5 EUR/kWh → impossible')
check(W.classify(row(1, unit='session', amt=12), T, X)[:2] == ('no_ref', 'unit_not_kwh'), 'per session → not compared')
check(W.classify(row(1, cur='XYZ'), T, X)[:2] == ('no_ref', 'currency_unknown'), 'unknown currency → not compared')
check(W.classify(row(1, net='Nobody Charge'), T, X)[:2] == ('no_ref', 'no_tariff'), 'network without tariff → no_ref')
if key_loc:
    lc, ln = key_loc
    e = T[key_loc]
    r = row(1, cc=lc, net=ln, cur=e['cur'], amt=e['dc'][1])
    check(W.classify(r, T, X)[0] == 'match', f'local currency price ({e["cur"]}) → match via fx', W.classify(r, T, X))

# decide: only new prices of visible rows
rows = [row(1), row(2, price_status='accepted'), row(3, status='hidden'), row(4, amt=None, s='radi', price_status=None), row(5, amt=dc * 2.5)]
d = W.decide(rows, T, X)
check([x['id'] for x in d] == [1, 5] and d[1]['price_status'] == 'off', 'decide touches only new, visible prices', d)

# candidates: two independent drivers agreeing within 3 %
rs = [row(1, price_status='match'), row(2, price_status='match', amt=round(dc * 1.02, 4)), row(3, price_status='match', amt=dc * 1.3)]
c = W.candidates(rs, T, X, NOW)
check(len(c) == 1 and c[0]['drivers'] == 2 and c[0]['network'] == net and c[0]['status'] == 'candidate' and c[0]['vs_list'] is not None,
      'two matching drivers → one candidate', c)
c = W.candidates([row(1, price_status='match'), row(2, price_status='match', ip_hash='h01')], T, X, NOW)
check(c == [], 'the same fingerprint twice is one driver → no candidate', c)
c = W.candidates([row(1, price_status='match'), row(2, price_status='match', amt=dc * 1.1)], T, X, NOW)
check(c == [], 'prices 10 % apart do not agree → no candidate', c)
c = W.candidates([row(1, price_status='match'), row(2, price_status='off')], T, X, NOW)
check(c == [], 'a price waiting for the owner does not count', c)
c = W.candidates([row(1, price_status='match', created_at=NOW - 300 * 86400), row(2, price_status='match')], T, X, NOW)
check(c == [], 'older than 6 months does not count', c)
c = W.candidates([row(1, net='Nobody Charge', price_status='no_ref', amt=0.5), row(2, net='Nobody Charge', price_status='no_ref', amt=0.5)], T, X, NOW)
check(len(c) == 1 and c[0]['list_eur'] is None, 'a network without tariff can get a candidate (no list price to compare)', c)

# the CLI on a fixture: files, no network
with tempfile.TemporaryDirectory() as tmp:
    fx = Path(tmp) / 'export.json'
    fx.write_text(json.dumps({'now': NOW, 'checkins': [row(1), row(2, amt=round(dc * 1.01, 4)), row(3, amt=dc * 2.4), row(4, amt=9.0),
                                                        row(5, s='radi', amt=None, price_status=None)]}))
    out = Path(tmp) / 'out'
    res = W.run(W.argparse.Namespace(fixture=str(fx), out=str(out), api=None, since=0, dry_run=False, write_content=False))
    files = sorted(p.name for p in out.iterdir())
    check(files == ['checkin_prices.json', 'decisions.json', 'queue.md', 'stats.json'], 'CLI writes its four files', files)
    cp = json.loads((out / 'checkin_prices.json').read_text())
    st = json.loads((out / 'stats.json').read_text())
    check(len(cp['rows']) == 1 and cp['rows'][0]['drivers'] == 2, 'fixture: one candidate', cp)
    check(st['decisions'] == {'auto_hidden': 1, 'match': 2, 'off': 1} and st['places_confirmed_30d'] == 1, 'fixture: stats', st)
    check('#3' in (out / 'queue.md').read_text(), 'fixture: the price far from the list is in queue.md')

check(W.selftest() == 0, 'selftest')
print(f'\n{oks} ok, {fails} failed')
sys.exit(1 if fails else 0)
