"""TAILS (13.11.2026) — tests of the four number-and-order rules of blokvolt.com, for every page in every language.

    python3 scripts/qa/tails_rules_test.py                       unit tests only
    python3 scripts/qa/tails_rules_test.py dist-com [pages_dir]  unit tests + the built site (+ the bundle for rule 4)

1. Percentages: a share above 0 that rounds to 0 is "<1%", one below the whole that rounds to 100 is ">99%"; the sign
   and the space follow the language (registry "pct"). In the built pages no table row says 0 % next to a count > 0,
   and the network share of a country is never "0 %" while the network has places.
2. "How to pay": networks by the DC-place number the table shows, largest first.
3. Routes: every stop is named by a place (town) — never "HPC", "DC", "Charging station", "Ladepunkt" or empty.
4. Search: a suggestion shows the first number of its page (n_all: every charging place), not the public count.
"""
import json
import os
import re
import sys
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))

os.environ.setdefault('BV_WORLD_PREVIEW', '1')   # every language of the preview build has its paths
ERR = []


def chk(ok, msg):
    if not ok:
        ERR.append(msg)


def txt(h):
    return ' '.join(unescape(re.sub(r'<[^>]+>', ' ', h)).split())


# ---------------------------------------------------------------- unit tests
def unit():
    import world_i18n as I
    import world_pages as WP
    import world_pay as PY
    sv = WP.share_value
    for part, whole, want in [(91, 55590, '<1'), (0, 100, 0), (1, 200, 1), (1, 201, '<1'), (199, 200, '>99'), (200, 200, 100),
                              (5, 10, 50), (1, 3, 33), (2, 3, 67), (0, 0, 0), (3, 1000, '<1'), (995, 1000, '>99'), (994, 1000, 99)]:
        chk(sv(part, whole) == want, f'rule 1: share_value({part}, {whole}) = {sv(part, whole)!r}, want {want!r}')
    for l in I.langs():
        r = I.reg(l)
        s = WP.fmt_pct('<1', r)
        chk('<1' in s and '%' in s.replace('٪', '%'), f'rule 1: {l} "<1" percentage {s!r}')
        chk(s == r['pct'].format(x='<1'), f'rule 1: {l} pattern not used: {s!r}')
        chk(WP.fmt_pct(0, r) == r['pct'].format(x='0'), f'rule 1: {l} zero')
    # rule 2: the old key (DC + HPC) put Shell Recharge (385 DC) above Pfalzwerke (388 DC)
    nets = {'Shell Recharge': {'dc50': 385, 'hpc': 200}, 'Pfalzwerke': {'dc50': 388, 'hpc': 20}, 'Allego': {'dc50': 453, 'hpc': 100},
            'Zero': {'dc50': 0, 'hpc': 0}, 'b-net': {'dc50': 100}, 'A-net': {'dc50': 100}}
    order = [k for k, _ in PY.pay_order(nets)]
    chk(order == ['Allego', 'Pfalzwerke', 'Shell Recharge', 'A-net', 'b-net'], f'rule 2: order {order}')
    # rule 3: labels are never a name
    for nm in ('HPC', 'DC', 'Charging station', 'Charging Stations', 'Ladepunkt', 'Ladestation', 'EV Charger', '', None, ' - DC',
               'Станица за полнење', 'Stație Încărcare Mașini Electrice'):
        chk(PY.clean_place_name(nm) == '', f'rule 3: label {nm!r} survives as {PY.clean_place_name(nm)!r}')
    chk(PY.clean_place_name('Turmstrom Charging Station') == 'Turmstrom', 'rule 3: brand kept')
    t, n, note = PY.stop_label({'name': None, 'net': None, 'cls': 5, 'cc': 'HR'}, 'Slavonski Brod')
    chk(t == 'Slavonski Brod' and not n and not note, f'rule 3: bare stop → {t, n, note}')
    t, n, note = PY.stop_label({'name': 'Kelag Charging Station', 'net': 'Kelag', 'cls': 5}, 'Villach')
    chk((t, n, note) == ('Villach', 'Kelag', ''), f'rule 3: label name → {t, n, note}')
    R = json.load(open(ROOT / 'content' / 'world' / 'routes.json', encoding='utf-8'))
    for rt in R['routes']:
        for s in rt['stops']:
            for l in I.BASE:
                t, n, note = PY.stop_label(s, (s.get('city') or {}).get(l))
                chk(bool(t) and not LABEL_ONLY.match(t), f"rule 3: {rt['id']} {s['km']} km [{l}] → {t!r}")
    # rule 4
    import world_search as WS
    chk(WS.shown_n({'n': 21, 'data': {'n_all': 30}}) == 30, 'rule 4: n_all first')
    chk(WS.shown_n({'n': 21, 'data': {}}) == 21, 'rule 4: index number without n_all')
    chk(WS.shown_n(None) is None, 'rule 4: no page')


LABEL_ONLY = re.compile(r'(?i)^\s*(hpc|dc|ac|charging stations?|ladepunkt|ladestation|charger|—|-|)\s*$')


# ---------------------------------------------------------------- built site
def site(dist, pages=None):
    dist = Path(dist)
    n_files = n_rows = 0
    for f in dist.rglob('index.html'):
        rel = f.relative_to(dist).as_posix()
        if rel.startswith(('hr/', 'ba/', 'me/', 'mk/', 'al/', 'xk/', 'serbia/', 'croatia/', 'bosnia', 'montenegro/', 'north-macedonia/',
                           'albania/', 'kosovo/', 'si/')) and 'svijet' not in rel and '/svet' not in rel:
            continue
        h = f.read_text(encoding='utf-8', errors='replace')
        if '%' not in h and 'wpay-t' not in h:
            continue
        n_files += 1
        # rule 1: a row with a count above 0 and "0 %" beside it
        for row in re.findall(r'<tr[^>]*>(.*?)</tr>', h, re.S):
            cells = [txt(c) for c in re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', row, re.S)]
            for a, b in zip(cells, cells[1:]):
                if re.fullmatch(r'0\s?%|%\s?0', b) and re.fullmatch(r'[\d\s.,  ’\']+', a or '') and re.sub(r'\D', '', a) not in ('', '0'):
                    ERR.append(f'rule 1: {rel}: "{a} | {b}"')
            n_rows += 1
        # rule 2: how to pay — the first table, DC column non-increasing
        if 'wpay' in h and re.search(r'/(how-to-pay|[a-z]{2}/[^/]+)/[^/]+/index\.html$', '/' + rel):
            m = re.search(r'<table[^>]*>(.*?)</table>', h, re.S)
            if m and m.group(1).count('<tr') > 2 and 'th scope="col" class="num"' in m.group(1)[:600]:
                nums = []
                for row in re.findall(r'<tr[^>]*>(.*?)</tr>', m.group(1), re.S)[1:]:
                    cells = [txt(c) for c in re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', row, re.S)]
                    if len(cells) > 1 and re.fullmatch(r'[\d\s.,  ’\']+', cells[1]):
                        nums.append(int(re.sub(r'\D', '', cells[1])))
                if len(nums) > 1 and 'th_stop_km' not in h:
                    chk(nums == sorted(nums, reverse=True), f'rule 2: {rel}: {nums}')
        # rule 3: route pages — the first cell after km
        if 'id="stops"' in h:
            for row in re.findall(r'<tr><td class="num">[^<]*</td><th scope="row"[^>]*>(.*?)</th>', h, re.S):
                first = txt(row.split('<small')[0])
                chk(bool(first) and not LABEL_ONLY.match(first), f'rule 3: {rel}: stop "{first}"')
    chk(n_files > 100, f'site: only {n_files} pages with percentages or pay tables')
    # rule 1 on the network pages: the share sentence of IONITY in Germany (any language built)
    ion = list(dist.glob('**/ionity*/index.html'))
    de = [f for f in ion if re.search(r'(germany|deutschland|allemagne|alemania|germania|niemcy|nemecko|německo|tyskland|saksa|duitsland|alemanha|германия|немачка|nemačka)', str(f), re.I)]
    import world_i18n as I
    price = tuple(I.slugs(l)['prices'].strip('/') for l in I.langs())
    de = [f for f in de if not f.relative_to(dist).as_posix().startswith(price)]
    chk(len(de) >= 1, f'rule 1: no IONITY Germany network page built')
    for f in de:
        h = unescape(f.read_text(encoding='utf-8'))
        chk('<1' in h, f'rule 1: {f.relative_to(dist)} — IONITY share is not "<1%"')
    # rule 4: the search items against the bundle
    if pages:
        pages = Path(pages)
        idx = json.load(open(pages / 'index.json', encoding='utf-8'))
        nall = {}
        for e in idx['pages']:
            if e['type'] in ('city', 'country'):
                d = json.load(open(pages / e['file'], encoding='utf-8'))
                nall[(e['type'][0], str(e.get('gid') or e['cc']))] = d.get('n_all') or e.get('n')
        bad = n = 0
        for f in sorted(dist.glob('assets/world/search-*.json')):
            if not re.fullmatch(r'search-[a-z]{2}\.json', f.name):
                continue
            for it in json.load(open(f, encoding='utf-8')).get('items') or []:
                k = (it[0], str(it[1]))
                if k in nall and it[4] is not None:
                    n += 1
                    if it[4] != nall[k]:
                        bad += 1
                        if bad <= 5:
                            ERR.append(f'rule 4: {f.name} {k} shows {it[4]}, page {nall[k]}')
        chk(n > 100, f'rule 4: only {n} search items checked')
        print(f'rule 4: {n} search suggestions checked against the pages')
    # P3.10: search regions of France are the 13 current ones (the old 22 are aliases)
    FR13 = {'Grand Est', 'Nouvelle-Aquitaine', 'Auvergne-Rhône-Alpes', 'Bourgogne-Franche-Comté', 'Brittany', 'Centre-Val de Loire', 'Corsica',
            'Normandy', 'Île-de-France', 'Occitania', 'Hauts-de-France', 'Pays de la Loire', "Provence-Alpes-Côte d'Azur"}
    fr = set()
    for f in dist.glob('assets/world/search-en*.json'):
        d = json.load(open(f, encoding='utf-8'))
        fr |= {str(i[1])[3:] for i in d.get('items') or [] if i[0] == 'r' and str(i[1]).startswith('FR:')}
        fr |= {str(i)[3:] for k, i in zip(d.get('k') or '', d.get('id') or []) if k == 'r' and str(i).startswith('FR:')}
    chk(fr and fr <= FR13, f'P3.10: French regions in the search: {sorted(fr - FR13)}')
    print(f'site: {n_files} pages, {n_rows} table rows checked; French regions {len(fr)}')


if __name__ == '__main__':
    unit()
    if len(sys.argv) > 1:
        site(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    for e in ERR[:60]:
        print('FAIL', e)
    print('TAILS rules:', 'PASS' if not ERR else f'{len(ERR)} errors')
    sys.exit(1 if ERR else 0)
