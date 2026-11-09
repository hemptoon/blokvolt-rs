# World map reports (K6): the rules of scripts/world_reports.py (spam, Balkan/unknown pids, hide with 2 independent
# reports on weak single-source sites only, moves of ≤150 m with 2 agreeing points, "nije javni" -> access, the rest to
# a human), overrides.csv (latest decision wins, undo, --prev merge, exact header, no reporter text), the card lookup in a
# split geohash prefix and the CLI end to end on scripts/qa/fixtures/svet (offline, --fixture-reports).
# Usage: python3 scripts/qa/world_reports_test.py
import csv
import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import world_reports as wr  # noqa: E402

FIX = ROOT / 'scripts' / 'qa' / 'fixtures' / 'svet'
LAT, LON = 48.85, 2.35
T = 1794225600


def site(conf=40, nsrc=1, gov=False, lat=LAT, lon=LON, cc='FR'):
    return {'conf': conf, 'nsrc': nsrc, 'gov': gov, 'lat': lat, 'lon': lon, 'cc': cc, 'n': 'X', 'net': None}


_id = [0]


def rep(pid, typ, ip, text=None, lat=None, lon=None, **kw):
    _id[0] += 1
    r = {'id': _id[0], 'pid': pid, 'type': typ, 'text': text, 'lat': lat, 'lon': lon, 'lang': 'en',
         'ip_hash': ip, 'created_at': T + _id[0], 'status': 'new'}
    r.update(kw)
    return r


def off(north_m, east_m, lat=LAT, lon=LON):
    return lat + north_m / 111_195, lon + east_m / (111_195 * math.cos(math.radians(lat)))


def by_id(decisions):
    return {d['id']: d for d in decisions}


class Rules(unittest.TestCase):
    def run_rules(self, reports, sites):
        return by_id(wr.apply_rules(reports, sites))

    # --- hide
    def test_two_independent_hide(self):
        a, b = rep(1, 'ne_radi', 'a'), rep(1, 'ne_postoji', 'b')
        d = self.run_rules([a, b], {1: site()})
        for x in (a, b):
            self.assertEqual((d[x['id']]['status'], d[x['id']]['rule'], d[x['id']]['action']),
                             ('auto_hidden', 'hide_2_reports', 'hide'))

    def test_same_ip_twice_waits(self):
        a, b = rep(1, 'ne_radi', 'a'), rep(1, 'ne_radi', 'a')
        d = self.run_rules([a, b], {1: site()})
        self.assertIsNone(d[a['id']]['status'])
        self.assertEqual(d[b['id']]['reason'], 'waiting')

    def test_single_hide_waits(self):
        a = rep(1, 'ne_postoji', 'a')
        self.assertEqual(self.run_rules([a], {1: site()})[a['id']]['reason'], 'waiting')

    def test_conf70_protected(self):
        a, b = rep(1, 'ne_radi', 'a'), rep(1, 'ne_radi', 'b')
        d = self.run_rules([a, b], {1: site(conf=70)})
        self.assertIsNone(d[a['id']]['status'])
        self.assertEqual(d[a['id']]['reason'], 'gov_registry')
        d = self.run_rules([a, b], {1: site(conf=69)})
        self.assertEqual(d[a['id']]['status'], 'auto_hidden')

    def test_gov_bit_protected(self):
        a, b = rep(1, 'ne_radi', 'a'), rep(1, 'ne_postoji', 'b')
        d = self.run_rules([a, b], {1: site(conf=20, gov=True)})
        self.assertEqual((d[a['id']]['status'], d[b['id']]['reason']), (None, 'gov_registry'))

    def test_multi_source_not_hidden(self):
        a, b, c = rep(1, 'ne_radi', 'a'), rep(1, 'ne_radi', 'b'), rep(1, 'ne_postoji', 'c')
        d = self.run_rules([a, b, c], {1: site(nsrc=2)})
        self.assertTrue(all(x['status'] is None and x['reason'] == 'multi_source' for x in d.values()))

    def test_no_card_not_hidden(self):
        a, b = rep(1, 'ne_radi', 'a'), rep(1, 'ne_radi', 'b')
        d = self.run_rules([a, b], {1: site(nsrc=None)})
        self.assertEqual(d[a['id']]['reason'], 'no_card')

    def test_mix_counts_together(self):
        a, b = rep(1, 'ne_postoji', 'a'), rep(1, 'ne_radi', 'b')
        d = self.run_rules([a, b], {1: site()})
        self.assertEqual({x['status'] for x in d.values()}, {'auto_hidden'})

    # --- move
    def test_move_two_agree_mean(self):
        p1, p2 = off(40, 0), off(60, 20)
        a = rep(1, 'lokacija', 'a', lat=p1[0], lon=p1[1])
        b = rep(1, 'lokacija', 'b', lat=p2[0], lon=p2[1])
        d = self.run_rules([a, b], {1: site()})
        x = d[a['id']]
        self.assertEqual((x['status'], x['rule'], x['action']), ('auto_moved', 'move_2_agree', 'move'))
        self.assertAlmostEqual(x['alat'], round((p1[0] + p2[0]) / 2, 6), places=6)
        self.assertAlmostEqual(x['alon'], round((p1[1] + p2[1]) / 2, 6), places=6)
        self.assertEqual(d[b['id']]['alat'], x['alat'])

    def test_move_disagree(self):
        p1, p2 = off(70, 0), off(-70, 0)
        a = rep(1, 'lokacija', 'a', lat=p1[0], lon=p1[1])
        b = rep(1, 'lokacija', 'b', lat=p2[0], lon=p2[1])
        d = self.run_rules([a, b], {1: site()})
        self.assertEqual((d[a['id']]['status'], d[a['id']]['reason']), (None, 'move_waiting'))

    def test_move_same_ip_not_independent(self):
        p1, p2 = off(40, 0), off(45, 0)
        a = rep(1, 'lokacija', 'a', lat=p1[0], lon=p1[1])
        b = rep(1, 'lokacija', 'a', lat=p2[0], lon=p2[1])
        d = self.run_rules([a, b], {1: site()})
        self.assertIsNone(d[a['id']]['status'])

    def test_move_far(self):
        p1, p2 = off(200, 0), off(205, 0)
        a = rep(1, 'lokacija', 'a', lat=p1[0], lon=p1[1])
        b = rep(1, 'lokacija', 'b', lat=p2[0], lon=p2[1])
        d = self.run_rules([a, b], {1: site()})
        self.assertEqual((d[a['id']]['status'], d[b['id']]['reason']), (None, 'move_far'))

    def test_move_agree_plus_far_point(self):
        p1, p2, p3 = off(40, 0), off(45, 5), off(500, 0)
        a = rep(1, 'lokacija', 'a', lat=p1[0], lon=p1[1])
        b = rep(1, 'lokacija', 'b', lat=p2[0], lon=p2[1])
        c = rep(1, 'lokacija', 'c', lat=p3[0], lon=p3[1])
        d = self.run_rules([a, b, c], {1: site()})
        self.assertEqual(d[a['id']]['status'], 'auto_moved')
        self.assertEqual((d[c['id']]['status'], d[c['id']]['reason']), (None, 'move_far'))

    def test_single_move_waits(self):
        p = off(30, 0)
        a = rep(1, 'lokacija', 'a', lat=p[0], lon=p[1])
        self.assertEqual(self.run_rules([a], {1: site()})[a['id']]['reason'], 'move_waiting')

    # --- access, human
    def test_nije_javni_access(self):
        # decision 18 (09.11): two independent reports, one is not enough
        a, b = rep(1, 'nije_javni', 'a'), rep(1, 'nije_javni', 'b')
        d = self.run_rules([a, b], {1: site()})
        self.assertTrue(all((x['status'], x['rule'], x['action'], x['access']) ==
                            ('accepted', 'access_reported', 'access', 'restricted_reported') for x in d.values()))

    def test_nije_javni_single_waits(self):
        a = rep(1, 'nije_javni', 'a')
        x = self.run_rules([a], {1: site()})[a['id']]
        self.assertEqual((x['status'], x['reason']), (None, 'waiting'))
        a2 = rep(1, 'nije_javni', 'a')            # the same fingerprint twice is still one person
        d = self.run_rules([a, a2], {1: site()})
        self.assertTrue(all(x['status'] is None and x['reason'] == 'waiting' for x in d.values()))

    def test_move_protected_never_auto(self):
        # decision 18: state registry or confidence >= 70 -> agreeing points still go to the queue
        p1, p2 = off(40, 0), off(45, 5)
        for s in (site(conf=70), site(gov=True)):
            a, b = rep(1, 'lokacija', 'a', lat=p1[0], lon=p1[1]), rep(1, 'lokacija', 'b', lat=p2[0], lon=p2[1])
            d = self.run_rules([a, b], {1: s})
            self.assertTrue(all(x['status'] is None and x['reason'] == 'gov_registry' for x in d.values()), d)
        # switchable in the config
        a, b = rep(1, 'lokacija', 'a', lat=p1[0], lon=p1[1]), rep(1, 'lokacija', 'b', lat=p2[0], lon=p2[1])
        d = wr.apply_rules([a, b], {1: site(conf=80)}, {'MOVE_PROTECTED': True})
        self.assertTrue(all(x['status'] == 'auto_moved' for x in d))

    def test_config_file(self):
        import tempfile as _t
        with _t.NamedTemporaryFile('w', suffix='.json', delete=False) as f:
            json.dump({'HIDE_MIN': 3, 'ACCESS_MIN': 3}, f)
        cfg = wr.load_config(f.name)
        self.assertEqual((cfg['HIDE_MIN'], cfg['ACCESS_MIN'], cfg['MOVE_PROTECTED']), (3, 3, False))
        self.assertEqual(wr.load_config(None), wr.DEFAULTS)
        for bad in ({'NOPE': 1}, {'HIDE_MIN': 'two'}, {'MOVE_PROTECTED': 1}):
            with open(f.name, 'w') as g:
                json.dump(bad, g)
            with self.assertRaises(SystemExit):
                wr.load_config(f.name)
        a, b = rep(1, 'ne_postoji', 'a'), rep(1, 'ne_radi', 'b')
        d = wr.apply_rules([a, b], {1: site()}, {'HIDE_MIN': 3})
        self.assertTrue(all(x['status'] is None and x['reason'] == 'waiting' for x in d))

    def test_nije_javni_protected(self):
        a = rep(1, 'nije_javni', 'a')
        for s in (site(conf=80), site(gov=True)):
            x = self.run_rules([a], {1: s})[a['id']]
            self.assertEqual((x['status'], x['reason']), (None, 'gov_registry'))

    def test_snaga_drugo_human(self):
        a, b = rep(1, 'snaga', 'a', text='only 11 kW'), rep(1, 'drugo', 'b', text='kabl oštećen')
        d = self.run_rules([a, b], {1: site()})
        self.assertTrue(all(x['status'] is None and x['reason'] == 'human' for x in d.values()))

    # --- spam
    def test_spam_link(self):
        for t in ('see http://x.y', 'www.cheap.example', 'go to cheapcharge.shop', 'visit evpunjaci.rs today'):
            a = rep(1, 'drugo', 'a', text=t)
            x = self.run_rules([a], {1: site()})[a['id']]
            self.assertEqual((x['status'], x['rule'], x['action']), ('rejected', 'spam_link', 'none'), t)

    def test_no_false_link(self):
        a = rep(1, 'drugo', 'a', text='Ul. Kneza Miloša 5, ulaz iz dvorišta. Radi 8-20h.')
        self.assertIsNone(self.run_rules([a], {1: site()})[a['id']]['status'])

    def test_spam_rude_three_languages(self):
        for t in ('jebem ti punjač', 'this shit is broken', 'это пиздец, не работает', 'НИХУЯ не работает'):
            a = rep(1, 'ne_radi', 'a', text=t)
            x = self.run_rules([a], {1: site()})[a['id']]
            self.assertEqual((x['status'], x['rule']), ('rejected', 'spam_rude'), t)

    def test_no_false_rude(self):
        for t in ('Shitake restaurant nearby', 'Ne radi od subote', 'Не работает с утра'):
            a, b = rep(1, 'drugo', 'a', text=t), rep(2, 'drugo', 'b', text=t + ' x')
            self.assertIsNone(self.run_rules([a, b], {1: site(), 2: site()})[a['id']]['status'], t)

    def test_spam_repeat_across_pids(self):
        t = 'Call me for a better offer!'
        rows = [rep(1, 'drugo', 'a', text=t), rep(2, 'drugo', 'b', text=t.upper()), rep(3, 'drugo', 'c', text=t + '  ')]
        d = self.run_rules(rows, {1: site(), 2: site(), 3: site()})
        self.assertTrue(all(x['rule'] == 'spam_repeat' and x['status'] == 'rejected' for x in d.values()))

    def test_repeat_needs_two_pids_or_three(self):
        t = 'Call me for a better offer!'
        rows = [rep(1, 'drugo', 'a', text=t), rep(2, 'drugo', 'b', text=t)]       # 2 reports, 2 ips: not spam
        self.assertTrue(all(x['status'] is None for x in self.run_rules(rows, {1: site(), 2: site()}).values()))
        rows = [rep(1, 'drugo', x, text=t) for x in 'abc']                         # 3 reports, 1 pid: not spam
        self.assertTrue(all(x['status'] is None for x in self.run_rules(rows, {1: site()}).values()))

    def test_spam_same_ip_same_text_two_pids(self):
        rows = [rep(1, 'ne_radi', 'z', text='Ovo je lažna stanica'), rep(2, 'ne_radi', 'z', text='ovo je lažna stanica!')]
        d = self.run_rules(rows, {1: site(), 2: site()})
        self.assertTrue(all(x['rule'] == 'spam_repeat' for x in d.values()))

    def test_spam_excluded_from_counts(self):
        a, b = rep(1, 'ne_radi', 'a', text='fuck this'), rep(1, 'ne_radi', 'b')
        d = self.run_rules([a, b], {1: site()})
        self.assertEqual((d[a['id']]['rule'], d[b['id']]['reason']), ('spam_rude', 'waiting'))

    # --- pid classes
    def test_balkan_pid(self):
        a, b = rep(900000000, 'ne_radi', 'a'), rep(900000000, 'ne_radi', 'b')
        d = self.run_rules([a, b], {900000000: site()})
        self.assertTrue(all(x['status'] is None and x['reason'] == 'balkan' for x in d.values()))
        c = rep(899999999, 'ne_radi', 'a')
        self.assertEqual(self.run_rules([c], {})[c['id']]['reason'], 'unknown_pid')

    def test_unknown_pid(self):
        a, b = rep(5, 'ne_radi', 'a'), rep(5, 'ne_radi', 'b')
        d = self.run_rules([a, b], {1: site()})
        self.assertTrue(all(x['reason'] == 'unknown_pid' for x in d.values()))

    def test_only_new_rows(self):
        a = rep(1, 'nije_javni', 'a', status='postponed')
        self.assertEqual(wr.apply_rules([a], {1: site()}), [])

    def test_auto_items_shape(self):
        p1, p2 = off(40, 0), off(45, 0)
        rows = [rep(1, 'lokacija', 'a', lat=p1[0], lon=p1[1]), rep(1, 'lokacija', 'b', lat=p2[0], lon=p2[1]),
                rep(2, 'nije_javni', 'c'), rep(2, 'nije_javni', 'e'), rep(3, 'drugo', 'd')]
        items = wr.auto_items(wr.apply_rules(rows, {1: site(), 2: site(), 3: site()}))
        self.assertEqual(len(items), 4)
        self.assertEqual(set(items[0]), {'id', 'status', 'rule', 'action', 'alat', 'alon'})
        self.assertEqual((items[2]['access'], items[3]['access']), ('restricted_reported', 'restricted_reported'))


def drow(id_, pid, action, rule, decided_at, status='accepted', **kw):
    r = {'id': id_, 'pid': pid, 'type': 'ne_radi', 'text': 'reporter text, secret', 'status': status,
         'decided_at': decided_at, 'decided_by': 'auto', 'rule': rule, 'action': action, 'access': None,
         'alat': None, 'alon': None}
    r.update(kw)
    return r


class Overrides(unittest.TestCase):
    def test_latest_wins(self):
        rows = [drow(1, 10, 'hide', 'hide_2_reports', T, 'auto_hidden'),
                drow(2, 10, 'hide', 'hide_2_reports', T, 'auto_hidden'),
                drow(3, 10, 'move', 'admin', T + 100, alat=1.5, alon=2.25)]
        o = wr.build_overrides(rows)
        self.assertEqual(len(o), 1)
        self.assertEqual((o[0]['action'], o[0]['lat'], o[0]['lon'], o[0]['reason']),
                         ('move', '1.500000', '2.250000', 'admin (1)'))
        o = wr.build_overrides(rows[:2])
        self.assertEqual((o[0]['action'], o[0]['reason'], o[0]['lat']), ('hide', 'hide_2_reports (2)', ''))

    def test_same_time_id_order(self):
        rows = [drow(5, 10, 'access', 'access_reported', T, access='restricted_reported'),
                drow(4, 10, 'hide', 'admin', T)]
        self.assertEqual(wr.build_overrides(rows)[0]['action'], 'access')

    def test_undo_after_hide_unhide(self):
        rows = [drow(1, 10, 'unhide', 'undo', T, 'rejected'), drow(2, 10, 'unhide', 'undo', T, 'rejected')]
        prev = [{'pid': '10', 'action': 'hide', 'lat': '', 'lon': '', 'access': '', 'reason': 'hide_2_reports (2)',
                 'decided_at': '2026-11-01'}]
        o = wr.build_overrides(rows, prev)
        self.assertEqual((o[0]['action'], o[0]['reason']), ('unhide', 'undo (2)'))

    def test_undo_move_drops(self):
        rows = [drow(1, 10, 'move', 'move_2_agree', T, 'auto_moved', alat=1, alon=2),
                drow(2, 10, 'none', 'undo', T + 10, 'rejected')]
        self.assertEqual(wr.build_overrides(rows), [])
        prev = [{'pid': '10', 'action': 'access', 'lat': '', 'lon': '', 'access': 'restricted_reported',
                 'reason': 'access_reported (1)', 'decided_at': '2026-11-01'}]
        self.assertEqual(wr.build_overrides([drow(2, 10, 'none', 'undo', T, 'rejected')], prev), [])

    def test_action_none_keeps_prev(self):
        prev = [{'pid': '10', 'action': 'hide', 'lat': '', 'lon': '', 'access': '', 'reason': 'x (2)',
                 'decided_at': '2026-11-01'}]
        o = wr.build_overrides([drow(1, 10, 'none', 'admin', T, 'rejected'),
                                drow(2, 11, 'none', 'spam_link', T, 'rejected')], prev)
        self.assertEqual([r['pid'] for r in o], ['10'])

    def test_new_rows_ignored(self):
        self.assertEqual(wr.build_overrides([drow(1, 10, None, None, None, 'new')]), [])

    def test_prev_merge_sorted(self):
        prev = [{'pid': '300', 'action': 'hide', 'lat': '', 'lon': '', 'access': '', 'reason': 'a (2)',
                 'decided_at': '2026-11-01'},
                {'pid': '20', 'action': 'hide', 'lat': '', 'lon': '', 'access': '', 'reason': 'b (2)',
                 'decided_at': '2026-11-01'}]
        o = wr.build_overrides([drow(1, 100, 'access', 'access_reported', T)], prev)
        self.assertEqual([r['pid'] for r in o], ['20', '100', '300'])
        self.assertEqual(o[1]['access'], 'restricted_reported')

    def test_csv_header_and_no_text(self):
        rows = [drow(1, 10, 'hide', 'hide_2_reports', T, 'auto_hidden'),
                drow(2, 11, 'access', 'admin', T, access='restricted_reported')]
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'o.csv'
            wr.write_overrides(wr.build_overrides(rows), p)
            txt = p.read_text(encoding='utf-8')
            self.assertEqual(txt.splitlines()[0], 'pid,action,lat,lon,access,reason,decided_at')
            self.assertNotIn('secret', txt)
            self.assertTrue(txt.isascii())
            self.assertEqual(wr.read_overrides(p)[0]['decided_at'], '2026-11-09')

    def test_reason_ascii_even_with_odd_rule(self):
        o = wr.build_overrides([drow(1, 10, 'hide', 'čudno pravilo', T)])
        self.assertTrue(o[0]['reason'].isascii())


class Cards(unittest.TestCase):
    def test_split_prefix_lookup(self):
        with tempfile.TemporaryDirectory() as td:
            a, b = (52.52, 13.405), (52.53, 13.30)      # both in geohash-3 'u33'
            ga, gb = wr.geohash(*a, 5), wr.geohash(*b, 5)
            self.assertEqual(ga[:3], gb[:3])
            far = (48.85, 2.35)
            Path(td, 'latest.json').write_text(json.dumps({'date': '2026-11-09'}))
            Path(td, 'manifest-2026-11-09.json').write_text(json.dumps(
                {'cards_base': 'c', 'cards_split': [ga[:3]], 'sources': [{'k': 'bnetza', 'gov': True}]}))
            Path(td, 'c').mkdir()
            for g, pid in ((ga[:4], 1), (gb[:4], 2), (wr.geohash(*far, 3), 3)):
                f = Path(td, 'c', g + '.json')
                cur = json.loads(f.read_text()) if f.exists() else {'v': 1, 'sites': {}}
                cur['sites'][str(pid)] = {'n': f'S{pid}', 'src': [{'k': 'osm'}, {'k': 'bnetza'}] if pid == 2
                                          else [{'k': 'osm'}], 'cc': 'DE', 'conf': 30}
                f.write_text(json.dumps(cur))
            cards = wr.Cards(td)
            got = wr.load_cards(cards, {1: a, 2: b, 3: far, 4: a})
            self.assertEqual({k: v['n'] for k, v in got.items()}, {1: 'S1', 2: 'S2', 3: 'S3'})
            layer = {1: {'lat': a[0], 'lon': a[1], 'conf': 30, 'gov': False},
                     2: {'lat': b[0], 'lon': b[1], 'conf': 30, 'gov': False}}
            s = wr.site_info(layer, got, cards.gov_sources)
            self.assertEqual((s[1]['nsrc'], s[1]['gov'], s[2]['nsrc'], s[2]['gov']), (1, False, 2, True))

    def test_geohash_haversine(self):
        self.assertEqual(wr.geohash(57.64911, 10.40744, 11), 'u4pruydqqvj')
        self.assertLess(abs(wr.haversine(*off(100, 0), LAT, LON) - 100), 0.5)


class Cli(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.td = tempfile.TemporaryDirectory()
        cls.out = Path(cls.td.name) / 'out'
        prev = Path(cls.td.name) / 'prev.csv'
        cls.fx = json.loads((FIX / 'reports.json').read_text(encoding='utf-8'))
        roles = cls.fx['fixture']['roles']
        prev.write_text('pid,action,lat,lon,access,reason,decided_at\n'
                        '5,hide,,,,hide_2_reports (2),2026-10-01\n'
                        f"{roles['undo_access']},access,,,restricted_reported,access_reported (1),2026-10-01\n",
                        encoding='utf-8')
        cls.p = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'world_reports.py'),
                                '--fixture-reports', str(FIX / 'reports.json'), '--layer', str(FIX / 'layer.geojsonseq'),
                                '--data', str(FIX / 'data'), '--out', str(cls.out), '--prev', str(prev)],
                               capture_output=True, text=True, env={'PATH': '/usr/bin:/bin'})

    @classmethod
    def tearDownClass(cls):
        cls.td.cleanup()

    def test_runs_and_writes(self):
        self.assertEqual(self.p.returncode, 0, self.p.stderr)
        self.assertTrue(self.p.stdout.startswith('world_reports: ') and '[dry-run]' in self.p.stdout)
        for f in ('overrides.csv', 'queue.json', 'queue.md', 'stats.json', 'run.log'):
            self.assertTrue((self.out / f).stat().st_size > 0, f)

    def test_overrides(self):
        roles = self.fx['fixture']['roles']
        with open(self.out / 'overrides.csv', newline='') as f:
            o = {int(r['pid']): r for r in csv.DictReader(f)}
        self.assertEqual(o[roles['hide']]['action'], 'hide')
        self.assertEqual(o[roles['move']]['action'], 'move')
        self.assertEqual(o[roles['admin_move']]['action'], 'move')
        self.assertEqual(o[roles['access']]['access'], 'restricted_reported')
        self.assertEqual(o[roles['undo_hide']]['action'], 'unhide')
        self.assertNotIn(roles['undo_access'], o)        # undone access drops the --prev row
        self.assertEqual(o[5]['action'], 'hide')         # untouched --prev row kept
        self.assertEqual(list(o), sorted(o))

    def test_queue_and_stats(self):
        roles = self.fx['fixture']['roles']
        q = json.loads((self.out / 'queue.json').read_text(encoding='utf-8'))
        reasons = {g['pid']: g['reasons'] for g in q['groups']}
        expect = {'same_ip': 'waiting', 'conf70': 'gov_registry', 'gov': 'gov_registry', 'multi': 'multi_source',
                  'move_disagree': 'move_waiting', 'move_far': 'move_far', 'move_single': 'move_waiting',
                  'access_protected': 'gov_registry', 'snaga': 'human', 'balkan': 'balkan', 'unknown': 'unknown_pid'}
        for role, why in expect.items():
            self.assertIn(why, reasons.get(roles[role], []), role)
        self.assertIn('postponed', reasons[roles['drugo']])
        self.assertIn('waiting', reasons[roles['snaga']])            # one "nije javni" waits (decision 18)
        ov = {int(r['pid']): r for r in csv.DictReader((self.out / 'overrides.csv').open(encoding='utf-8'))}
        self.assertNotIn(roles['conf70'], ov)                         # no automatic move of a protected place
        for role in ('hide', 'move', 'access', 'spam_link', 'spam_rude_sr', 'spam_rude_ru', 'spam_rude_en',
                     'repeat_a', 'repeat_b', 'repeat_c', 'ip_text_a', 'ip_text_b'):
            self.assertNotIn(roles[role], reasons, role)
        g = next(g for g in q['groups'] if g['pid'] == roles['gov'])
        self.assertEqual(g['link'], f"https://blokvolt.com/map/?id={roles['gov']}")
        self.assertTrue(g['site']['gov'])
        st = json.loads((self.out / 'stats.json').read_text(encoding='utf-8'))
        self.assertEqual(st['by_status']['auto_hidden'], 2)
        self.assertEqual(st['by_status']['auto_moved'], 2)
        self.assertEqual(st['by_status']['accepted'], 2)   # two independent "nije javni" (decision 18)
        self.assertEqual(sum(v for k, v in st['by_rule'].items() if k.startswith('spam_')), 9)
        self.assertEqual([x['pid'] for x in st['auto_hidden']], [roles['hide']])
        self.assertTrue({'DE', 'FR', 'NL', 'US'} <= set(st['by_country']))
        md = (self.out / 'queue.md').read_text(encoding='utf-8')
        self.assertIn('Razlog', md)
        self.assertIn('Zaštićeno', md)

    def test_api_needs_key(self):
        p = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'world_reports.py'), '--api', 'https://example.invalid',
                            '--layer', str(FIX / 'layer.geojsonseq'), '--data', str(FIX / 'data'),
                            '--out', str(Path(self.td.name) / 'nokey')],
                           capture_output=True, text=True, env={'PATH': '/usr/bin:/bin'})
        self.assertNotEqual(p.returncode, 0)
        self.assertIn('ADMIN_KEY', p.stderr)

    def test_fixture_small(self):
        self.assertLess(sum(f.stat().st_size for f in FIX.rglob('*') if f.is_file() and '__pycache__' not in f.parts),
                        200 * 1024)

    def test_selftest(self):
        p = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'world_reports.py'), '--selftest'],
                           capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stdout)


if __name__ == '__main__':
    res = unittest.TextTestRunner(verbosity=1, stream=sys.stdout).run(
        unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    bad = len(res.failures) + len(res.errors)
    print(f'{res.testsRun - bad} ok, {bad} FAIL')
    sys.exit(1 if bad else 0)
