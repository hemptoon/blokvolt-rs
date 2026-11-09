# -*- coding: utf-8 -*-
"""World map reports (K6, contract claude/evdb_tasks2/00_README.md §10): drivers report a station on blokvolt.com/map/
("ne postoji", "ne radi", wrong location, wrong power, not public, other) through POST /api/svet/prijava; the rows sit
in the D1 table world_reports. This script is the daily decision step:

  1. fetch every report from GET /api/admin/svet?view=export&since=<unix>  (or --fixture-reports file.json, offline)
  2. take the reports still 'new', look up their sites in the K1 layer (pid -> point, confidence, gov bit) and cards
     (contract §4: number of sources, country, name, network)
  3. apply_rules(): spam -> rejected; Balkan/unknown pids -> left for a human; 2 independent "ne postoji/ne radi" on a
     weak single-source site -> auto_hidden; 2 agreeing points within 150 m -> auto_moved; "nije javni" -> access
     restricted; everything else stays 'new' with a queue reason
  4. POST the automatic decisions to /api/admin/svet {"auto": [...]} (skipped with --dry-run / --fixture-reports;
     only rows still 'new' change server-side, a human decision is never overwritten)
  5. write <out>/overrides.csv (pid,action,lat,lon,access,reason,decided_at — the latest decision per pid, merged with
     --prev), queue.json + queue.md (open pids for the human, with reasons and a map link), stats.json and run.log

  ADMIN_KEY=… python3 scripts/world_reports.py --api https://www.blokvolt.rs \
      --layer out/<date>/public_sites.geojsonseq --data out/<date>/ --out work/K6/run-<date>/ [--prev overrides.csv]
      [--since <unix>] [--dry-run]
  python3 scripts/world_reports.py --fixture-reports scripts/qa/fixtures/svet/reports.json \
      --layer scripts/qa/fixtures/svet/layer.geojsonseq --data scripts/qa/fixtures/svet/data --out /tmp/k6
  python3 scripts/world_reports.py --selftest

--data is the directory (or http(s) base URL) holding latest.json, manifest-<date>.json and the cards directory.
ADMIN_KEY is read from the environment only and never printed. Stdlib only.
"""
import argparse
import csv
import json
import math
import os
import re
import sys
import tempfile
import time
import unicodedata
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

DEFAULTS = {'HIDE_MIN': 2, 'PROTECT_CONF': 70, 'MOVE_MAX_M': 150, 'MOVE_AGREE_M': 50, 'MOVE_MIN': 2,
            'ACCESS_MIN': 1, 'SPAM_REPEAT': 3}
BALKAN_PID = 900_000_000
HIDE_TYPES = ('ne_postoji', 'ne_radi')
TYPES = ('ne_postoji', 'ne_radi', 'lokacija', 'snaga', 'nije_javni', 'drugo')
ACCESS_DEFAULT = 'restricted_reported'
MAP_LINK = 'https://blokvolt.com/map/?id={pid}'
OVR_HEADER = ['pid', 'action', 'lat', 'lon', 'access', 'reason', 'decided_at']
STATE_ACTIONS = ('hide', 'unhide', 'move', 'access')
POST_MAX = 2000
UA = 'blokvolt-world-reports/1'

# queue reasons, Serbian Latin labels for queue.md
REASONS = {
    'balkan': 'Balkan — ručno, kroz /mapa/ proces',
    'unknown_pid': 'Nepoznat pid (nema ga u sloju)',
    'gov_registry': 'Zaštićeno: državni registar ili pouzdanost ≥ 70',
    'multi_source': 'Više izvora — ne skriva se automatski',
    'no_card': 'Nema kartice lokacije — broj izvora nepoznat',
    'waiting': 'Čeka drugu nezavisnu prijavu',
    'move_far': 'Predložena tačka dalje od 150 m',
    'move_waiting': 'Čeka drugu tačku koja se slaže',
    'human': 'Za ručnu proveru',
    'postponed': 'Odloženo',
}
TYPE_LABELS = {'ne_postoji': 'ne postoji', 'ne_radi': 'ne radi', 'lokacija': 'pogrešna lokacija',
               'snaga': 'snaga / priključci', 'nije_javni': 'nije javni', 'drugo': 'drugo'}

# ---------------------------------------------------------------------------------------------------------- geometry
_B32 = '0123456789bcdefghjkmnpqrstuvwxyz'


def geohash(lat, lon, precision=9):
    """Standard geohash (base32, even bits = longitude)."""
    lat_r, lon_r = [-90.0, 90.0], [-180.0, 180.0]
    out, bit, ch, even = [], 0, 0, True
    while len(out) < precision:
        rng, val = (lon_r, lon) if even else (lat_r, lat)
        mid = (rng[0] + rng[1]) / 2
        if val >= mid:
            ch = (ch << 1) | 1
            rng[0] = mid
        else:
            ch <<= 1
            rng[1] = mid
        even = not even
        bit += 1
        if bit == 5:
            out.append(_B32[ch])
            bit = ch = 0
    return ''.join(out)


def haversine(lat1, lon1, lat2, lon2):
    """Distance in metres."""
    r = 6371008.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


# -------------------------------------------------------------------------------------------------------------- spam
LINK_RE = re.compile(
    r'https?://|www\.|\b[a-z0-9][a-z0-9-]*\.(?:com|net|org|info|biz|io|co|me|rs|ru|ua|by|de|fr|nl|uk|us|eu|ba|mk|hr|si'
    r'|al|me|xyz|top|online|site|club|shop|app|ly|gl|to|link|click|pro|store|live)\b', re.I)
RUDE_RE = re.compile(
    r'(?<!\w)(?:'
    # SR (Latin, also with č/š written plain)
    r'jeb\w*|kurac\w*|kurc\w*|pičk\w*|pick(?:a|e|i|u|om|ama)\b|govn\w*|sranj\w*'
    # EN
    r'|fuck\w*|shit|shitty|bullshit|bitch\w*|asshole\w*|cunt\w*|motherfuck\w*'
    # RU
    r'|(?:на|ни|по|за|об|о|от|отъ|рас|раз|разъ|вы|до|у|при|под|подъ|с|съ|въ|изъ)?(?:ху[йеёяи]\w*|пизд\w*|еб[аеилнуы]\w*|ёб\w*)'
    r'|бля\w*|сука|суки|мудак\w*|говн\w*'
    r')(?!\w)', re.I)


def norm_text(t):
    """Lowercase, accents kept, punctuation -> space, collapsed whitespace."""
    t = unicodedata.normalize('NFC', (t or '').lower())
    t = re.sub(r'[^\w]+', ' ', t, flags=re.U)
    return re.sub(r'\s+', ' ', t).strip()


def spam_kind(text):
    if not text:
        return None
    if LINK_RE.search(text):
        return 'spam_link'
    if RUDE_RE.search(text) or RUDE_RE.search(norm_text(text)):
        return 'spam_rude'
    return None


# ------------------------------------------------------------------------------------------------------------- rules
def _decision(r, status=None, rule=None, action=None, access=None, alat=None, alon=None, reason=None):
    return {'id': r['id'], 'pid': int(r['pid']), 'type': r.get('type'), 'status': status, 'rule': rule,
            'action': action, 'access': access, 'alat': alat, 'alon': alon, 'reason': reason}


def _distinct_ips(rows):
    return len({r.get('ip_hash') for r in rows})


def _agreeing_points(rows, site, cfg):
    """The largest set of independent reports (one point per ip_hash) whose points lie within MOVE_MAX_M of the site and
    within MOVE_AGREE_M of each other. Returns (members, any_far)."""
    near, any_far = [], False
    seen = set()
    for r in sorted(rows, key=lambda x: (x.get('created_at') or 0, x['id'])):
        if r.get('lat') is None or r.get('lon') is None:
            continue
        d = haversine(site['lat'], site['lon'], float(r['lat']), float(r['lon']))
        if d > cfg['MOVE_MAX_M']:
            any_far = True
            continue
        if r.get('ip_hash') in seen:
            continue
        seen.add(r.get('ip_hash'))
        near.append(r)
    best = []
    for i, a in enumerate(near):
        group = [a]
        for b in near[i + 1:]:
            if all(haversine(float(b['lat']), float(b['lon']), float(g['lat']), float(g['lon'])) <= cfg['MOVE_AGREE_M']
                   for g in group):
                group.append(b)
        if len(group) > len(best):
            best = group
    return best, any_far


def apply_rules(reports, sites, cfg=None):
    """reports: export rows with status 'new'. sites: pid -> {conf, nsrc, gov, lat, lon, cc, n, net} (missing = unknown).
    Returns one decision per report: status None means it stays 'new' and goes to the queue with `reason`."""
    cfg = dict(DEFAULTS, **(cfg or {}))
    reports = [r for r in reports if (r.get('status') or 'new') == 'new']
    out = {}

    # 1. spam: link, rude word, repeated text
    by_text, by_ip_text = {}, {}
    for r in reports:
        n = norm_text(r.get('text'))
        if len(n) >= 10:
            by_text.setdefault(n, []).append(r)
            by_ip_text.setdefault((r.get('ip_hash'), n), []).append(r)
    repeat_ids = set()
    for rows in by_text.values():
        if len(rows) >= cfg['SPAM_REPEAT'] and len({int(x['pid']) for x in rows}) >= 2:
            repeat_ids.update(x['id'] for x in rows)
    for rows in by_ip_text.values():
        if len({int(x['pid']) for x in rows}) >= 2:
            repeat_ids.update(x['id'] for x in rows)
    rest = []
    for r in reports:
        k = spam_kind(r.get('text')) or ('spam_repeat' if r['id'] in repeat_ids else None)
        if k:
            out[r['id']] = _decision(r, 'rejected', k, 'none')
        else:
            rest.append(r)

    by_pid = {}
    for r in rest:
        by_pid.setdefault(int(r['pid']), []).append(r)

    for pid, rows in by_pid.items():
        # 2. Balkans (BlokVolt's own data) and unknown pids go to a human
        if pid >= BALKAN_PID or pid not in sites:
            why = 'balkan' if pid >= BALKAN_PID else 'unknown_pid'
            for r in rows:
                out[r['id']] = _decision(r, reason=why)
            continue
        s = sites[pid]
        conf = s.get('conf') or 0
        protected = conf >= cfg['PROTECT_CONF'] or bool(s.get('gov'))
        nsrc = s.get('nsrc')

        # 3. ne_postoji + ne_radi together
        hide = [r for r in rows if r.get('type') in HIDE_TYPES]
        if hide:
            n = _distinct_ips(hide)
            if protected:
                why = 'gov_registry'
            elif nsrc is None:
                why = 'no_card'
            elif nsrc >= 2:
                why = 'multi_source'
            elif n < cfg['HIDE_MIN']:
                why = 'waiting'
            else:
                why = None
            for r in hide:
                out[r['id']] = (_decision(r, 'auto_hidden', 'hide_2_reports', 'hide') if why is None
                                else _decision(r, reason=why))

        # 4. lokacija
        loc = [r for r in rows if r.get('type') == 'lokacija']
        if loc:
            members, any_far = ([], False) if s.get('lat') is None else _agreeing_points(loc, s, cfg)
            if len(members) >= cfg['MOVE_MIN']:
                alat = round(sum(float(m['lat']) for m in members) / len(members), 6)
                alon = round(sum(float(m['lon']) for m in members) / len(members), 6)
                ids = {m['id'] for m in members}
                # a second report from the same person near the agreeing points rides along
                ips = {m.get('ip_hash') for m in members}
                for r in loc:
                    if r['id'] not in ids and r.get('ip_hash') in ips and r.get('lat') is not None and \
                            haversine(alat, alon, float(r['lat']), float(r['lon'])) <= cfg['MOVE_AGREE_M']:
                        ids.add(r['id'])
                for r in loc:
                    if r['id'] in ids:
                        out[r['id']] = _decision(r, 'auto_moved', 'move_2_agree', 'move', alat=alat, alon=alon)
                    else:
                        far = r.get('lat') is None or haversine(s['lat'], s['lon'], float(r['lat']),
                                                                float(r['lon'])) > cfg['MOVE_MAX_M']
                        out[r['id']] = _decision(r, reason='move_far' if far else 'move_waiting')
            else:
                why = 'move_far' if any_far else 'move_waiting'
                for r in loc:
                    out[r['id']] = _decision(r, reason=why)

        # 5. nije_javni
        acc = [r for r in rows if r.get('type') == 'nije_javni']
        if acc:
            if protected:
                why = 'gov_registry'
            elif _distinct_ips(acc) < cfg['ACCESS_MIN']:
                why = 'waiting'
            else:
                why = None
            for r in acc:
                out[r['id']] = (_decision(r, 'accepted', 'access_reported', 'access', access=ACCESS_DEFAULT)
                                if why is None else _decision(r, reason=why))

        # 6. snaga, drugo (and anything unknown) -> human
        for r in rows:
            if r['id'] not in out:
                out[r['id']] = _decision(r, reason='human')

    return [out[r['id']] for r in reports]


def auto_items(decisions):
    """The POST /api/admin/svet {"auto": [...]} items for the decisions that change a row."""
    items = []
    for d in decisions:
        if not d['status']:
            continue
        it = {'id': d['id'], 'status': d['status'], 'rule': d['rule'], 'action': d['action']}
        if d['action'] == 'access':
            it['access'] = d['access']
        if d['action'] == 'move':
            it['alat'], it['alon'] = d['alat'], d['alon']
        items.append(it)
    return items


def merge_decisions(rows, decisions, now):
    """Apply this run's decisions to the export rows locally (only rows still 'new', like the server)."""
    by_id = {d['id']: d for d in decisions if d['status']}
    out = []
    for r in rows:
        d = by_id.get(r['id'])
        if d and (r.get('status') or 'new') == 'new':
            r = dict(r, status=d['status'], decided_at=now, decided_by='auto', rule=d['rule'], action=d['action'],
                     access=d['access'], alat=d['alat'], alon=d['alon'])
        out.append(r)
    return out


# --------------------------------------------------------------------------------------------------------- overrides
def _iso_date(ts):
    return datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime('%Y-%m-%d')


def _fmt(x):
    return '' if x is None or x == '' else f'{float(x):.6f}'


def build_overrides(export_rows, prev_rows=None):
    """One row per pid: the latest decision with an effect on the map. An undo of a move/access (action none, rule undo)
    drops the pid; pids not touched by the export keep their --prev row. Returns sorted list of dicts (OVR_HEADER)."""
    decided = [r for r in export_rows if r.get('decided_at') and (r.get('status') or 'new') not in ('new', 'postponed')]
    decided.sort(key=lambda r: (int(r['decided_at']), int(r['id'])))
    state = {}   # pid -> row dict, or None = explicitly dropped
    for r in decided:
        pid = int(r['pid'])
        action = r.get('action') or 'none'
        if action in STATE_ACTIONS:
            n = sum(1 for x in decided if int(x['pid']) == pid and x.get('rule') == r.get('rule')
                    and (x.get('action') or 'none') == action and int(x['decided_at']) == int(r['decided_at']))
            reason = re.sub(r'[^A-Za-z0-9_ ()-]', '', f"{r.get('rule') or 'admin'} ({n})")
            state[pid] = {'pid': str(pid), 'action': action,
                          'lat': _fmt(r.get('alat')) if action == 'move' else '',
                          'lon': _fmt(r.get('alon')) if action == 'move' else '',
                          'access': (r.get('access') or ACCESS_DEFAULT) if action == 'access' else '',
                          'reason': reason, 'decided_at': _iso_date(r['decided_at'])}
        elif r.get('rule') == 'undo':
            state[pid] = None
    merged = {}
    for p in prev_rows or []:
        merged[int(p['pid'])] = {k: p.get(k, '') or '' for k in OVR_HEADER}
    for pid, row in state.items():
        if row is None:
            merged.pop(pid, None)
        else:
            merged[pid] = row
    return [merged[k] for k in sorted(merged)]


def read_overrides(path):
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def write_overrides(rows, path):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=OVR_HEADER, lineterminator='\n')
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, '') for k in OVR_HEADER})


# -------------------------------------------------------------------------------------------------------- site info
def _is_url(s):
    return str(s).startswith(('http://', 'https://'))


def _read_text(src):
    if _is_url(src):
        req = urllib.request.Request(src, headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.read().decode('utf-8')
    return Path(src).read_text(encoding='utf-8')


def _join(base, name):
    if _is_url(name) or (not _is_url(base) and os.path.isabs(name)):
        return name
    if _is_url(base):
        return base.rstrip('/') + '/' + name.lstrip('/')
    return str(Path(base) / name)


def load_layer(path, pids=None):
    """K1 public layer (geojsonseq): pid -> {lat, lon, conf, gov}. With `pids`, keep only those."""
    want = None if pids is None else {int(p) for p in pids}
    out = {}
    for line in _read_text(path).splitlines():
        line = line.strip().lstrip('\x1e')
        if not line:
            continue
        f = json.loads(line)
        p = f.get('properties') or {}
        pid = int(p['i'])
        if want is not None and pid not in want:
            continue
        lon, lat = f['geometry']['coordinates'][:2]
        out[pid] = {'lat': float(lat), 'lon': float(lon), 'conf': p.get('c'), 'gov': bool(int(p.get('s') or 0) & 1)}
    return out


class Cards:
    """Manifest + card files (contract §4/§5) from a local directory or an http(s) base URL; card files are cached."""

    def __init__(self, base):
        self.base = str(base)
        latest = json.loads(_read_text(_join(self.base, 'latest.json')))
        name = latest.get('manifest') or f"manifest-{latest['date']}.json"
        self.manifest = json.loads(_read_text(_join(self.base, name)))
        self.split = set(self.manifest.get('cards_split') or [])
        self.cards_base = _join(self.base, self.manifest.get('cards_base') or f"cards-{self.manifest.get('date')}")
        srcs = self.manifest.get('sources') or []
        if isinstance(srcs, dict):
            srcs = [dict(v, k=k) for k, v in srcs.items()]
        self.gov_sources = {s.get('k') for s in srcs if s.get('gov')}
        self.cache = {}

    def prefix(self, lat, lon):
        g = geohash(lat, lon, 5)
        n = 3
        while g[:n] in self.split and n < len(g):
            n += 1
        return g[:n]

    def file(self, prefix):
        if prefix not in self.cache:
            try:
                self.cache[prefix] = json.loads(_read_text(_join(self.cards_base, prefix + '.json')))
            except (OSError, ValueError):
                self.cache[prefix] = None
        return self.cache[prefix]

    def card(self, pid, lat, lon):
        f = self.file(self.prefix(lat, lon))
        return ((f or {}).get('sites') or {}).get(str(pid))


def load_cards(data, pids_with_coords):
    """pid -> card for the given {pid: (lat, lon)}; pids whose card is missing are left out."""
    cards = data if isinstance(data, Cards) else Cards(data)
    out = {}
    for pid, (lat, lon) in pids_with_coords.items():
        c = cards.card(pid, lat, lon)
        if c is not None:
            out[int(pid)] = c
    return out


def site_info(layer, cards, gov_sources=()):
    """Join layer points and cards into the `sites` shape apply_rules wants."""
    sites = {}
    for pid, l in layer.items():
        c = cards.get(pid)
        s = {'lat': l['lat'], 'lon': l['lon'], 'conf': l.get('conf'), 'gov': l.get('gov', False),
             'nsrc': None, 'cc': None, 'n': None, 'net': None}
        if c:
            keys = {x.get('k') if isinstance(x, dict) else x for x in (c.get('src') or [])}
            s.update(nsrc=len(keys), cc=c.get('cc'), n=c.get('n'), net=c.get('net'))
            if c.get('conf') is not None:
                s['conf'] = c['conf']
            if keys & set(gov_sources):
                s['gov'] = True
        sites[pid] = s
    return sites


# ------------------------------------------------------------------------------------------------------------- API
def _api_request(url, key, body=None):
    data = None if body is None else json.dumps(body).encode('utf-8')
    req = urllib.request.Request(url, data=data, method='GET' if body is None else 'POST',
                                 headers={'Authorization': 'Bearer ' + key, 'User-Agent': UA,
                                          'content-type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode('utf-8'))


def fetch_export(api, key, since=0):
    j = _api_request(f"{api.rstrip('/')}/api/admin/svet?view=export&since={int(since)}", key)
    if not j.get('ok'):
        raise RuntimeError('export: not ok')
    return j


def post_auto(api, key, items):
    n = 0
    for i in range(0, len(items), POST_MAX):
        j = _api_request(f"{api.rstrip('/')}/api/admin/svet", key, {'auto': items[i:i + POST_MAX]})
        if not j.get('ok'):
            raise RuntimeError('post auto: not ok')
        n += int(j.get('n') or 0)
    return n


# ----------------------------------------------------------------------------------------------------------- outputs
def build_queue(rows, decisions, sites):
    reason_of = {d['id']: d['reason'] for d in decisions if not d['status']}
    groups = {}
    for r in rows:
        st = r.get('status') or 'new'
        if st not in ('new', 'postponed'):
            continue
        pid = int(r['pid'])
        g = groups.setdefault(pid, {'pid': pid, 'link': MAP_LINK.format(pid=pid), 'n': 0, 'types': {}, 'reasons': [],
                                    'first': None, 'last': None, 'site': sites.get(pid), 'reports': []})
        why = 'postponed' if st == 'postponed' else reason_of.get(r['id'], 'human')
        g['n'] += 1
        g['types'][r['type']] = g['types'].get(r['type'], 0) + 1
        if why not in g['reasons']:
            g['reasons'].append(why)
        ts = r.get('created_at') or 0
        g['first'] = ts if g['first'] is None else min(g['first'], ts)
        g['last'] = ts if g['last'] is None else max(g['last'], ts)
        g['reports'].append({k: r.get(k) for k in ('id', 'type', 'text', 'lat', 'lon', 'lang', 'created_at', 'status')}
                            | {'reason': why, 'ip': (r.get('ip_hash') or '')[:6]})
    return sorted(groups.values(), key=lambda g: (-g['n'], -(g['last'] or 0), g['pid']))


def queue_md(queue, stamp):
    out = [f'# Prijave sa svetske mape — red za proveru ({stamp})', '',
           f'Otvoreno: {len(queue)} lokacija, {sum(g["n"] for g in queue)} prijava.', '']
    for g in queue:
        s = g['site'] or {}
        name = s.get('n') or '?'
        meta = ', '.join(x for x in (s.get('cc'), s.get('net'), f"pouzdanost {s['conf']}" if s.get('conf') is not None
                                     else None, f"izvora {s['nsrc']}" if s.get('nsrc') is not None else None,
                                     'državni registar' if s.get('gov') else None) if x)
        out.append(f"## {g['pid']} — {name}" + (f' ({meta})' if meta else ''))
        out.append(f"- Razlog: {'; '.join(REASONS.get(x, x) for x in g['reasons'])}")
        out.append('- Prijave: ' + ', '.join(f'{TYPE_LABELS.get(t, t)} ×{n}' for t, n in sorted(g['types'].items())))
        for r in g['reports']:
            pt = f" → {r['lat']:.6f}, {r['lon']:.6f}" if r.get('lat') is not None else ''
            txt = (r.get('text') or '').replace('\n', ' ')[:140]
            out.append(f"  - #{r['id']} {TYPE_LABELS.get(r['type'], r['type'])}{pt}" + (f' — „{txt}“' if txt else ''))
        out.append(f"- Mapa: {g['link']}")
        out.append('')
    return '\n'.join(out)


def build_stats(new_rows, decisions, sites, rows_after):
    st = {'reports_new': len(new_rows), 'by_type': {}, 'by_status': {}, 'by_rule': {}, 'by_country': {},
          'auto_hidden': [], 'open_pids': 0}
    dec = {d['id']: d for d in decisions}
    hidden = {}
    for r in new_rows:
        st['by_type'][r['type']] = st['by_type'].get(r['type'], 0) + 1
        d = dec.get(r['id'])
        status = (d and d['status']) or 'new'
        st['by_status'][status] = st['by_status'].get(status, 0) + 1
        key = d['rule'] if d and d['status'] else 'queue:' + (d['reason'] if d else 'human')
        st['by_rule'][key] = st['by_rule'].get(key, 0) + 1
        pid = int(r['pid'])
        cc = (sites.get(pid) or {}).get('cc') or r.get('cc') or '??'
        st['by_country'][cc] = st['by_country'].get(cc, 0) + 1
        if status == 'auto_hidden':
            hidden.setdefault(pid, {'pid': pid, 'cc': cc, 'n': 0})['n'] += 1
    st['auto_hidden'] = [hidden[k] for k in sorted(hidden)]
    st['open_pids'] = len({int(r['pid']) for r in rows_after if (r.get('status') or 'new') in ('new', 'postponed')})
    for k in ('by_type', 'by_status', 'by_rule', 'by_country'):
        st[k] = dict(sorted(st[k].items()))
    return st


# -------------------------------------------------------------------------------------------------------------- main
def run(args, env=None):
    env = os.environ if env is None else env
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    log_lines = []

    def log(msg):
        log_lines.append(time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()) + ' ' + msg)

    dry = bool(args.dry_run or args.fixture_reports)
    key = None
    if args.fixture_reports:
        export = json.loads(Path(args.fixture_reports).read_text(encoding='utf-8'))
        log(f'fixture reports: {args.fixture_reports} (dry-run)')
    else:
        if not args.api:
            raise SystemExit('world_reports: --api or --fixture-reports is required')
        key = env.get('ADMIN_KEY')
        if not key:
            raise SystemExit('world_reports: ADMIN_KEY is not set in the environment; refusing to call the API')
        export = fetch_export(args.api, key, args.since)
        log(f'export from {args.api} since={args.since}: {len(export.get("reports") or [])} rows')
    rows = sorted(export.get('reports') or [], key=lambda r: int(r['id']))
    now = int(export.get('now') or time.time()) if args.fixture_reports else int(time.time())
    new_rows = [r for r in rows if (r.get('status') or 'new') == 'new']

    pids = {int(r['pid']) for r in new_rows if int(r['pid']) < BALKAN_PID}
    layer = load_layer(args.layer, pids) if pids else {}
    cards_obj = Cards(args.data) if layer else None
    cards = load_cards(cards_obj, {p: (v['lat'], v['lon']) for p, v in layer.items()}) if cards_obj else {}
    sites = site_info(layer, cards, cards_obj.gov_sources if cards_obj else ())
    log(f'new reports: {len(new_rows)} on {len(pids)} pids; in layer {len(layer)}, with card {len(cards)}')

    decisions = apply_rules(new_rows, sites, None)
    items = auto_items(decisions)
    if items and not dry:
        n = post_auto(args.api, key, items)
        log(f'POST auto: {len(items)} items, server changed {n}')
        if n != len(items):
            log(f'warning: {len(items) - n} items were not new any more on the server')
    else:
        log(f'auto decisions: {len(items)} (not posted{", dry-run" if dry else ""})')

    rows_after = merge_decisions(rows, decisions, now)
    prev = read_overrides(args.prev) if args.prev else None
    ovr = build_overrides(rows_after, prev)
    write_overrides(ovr, out / 'overrides.csv')

    queue = build_queue(rows_after, decisions, sites)
    stamp = _iso_date(now)
    (out / 'queue.json').write_text(json.dumps({'date': stamp, 'open': len(queue), 'groups': queue},
                                               ensure_ascii=False, indent=1), encoding='utf-8')
    (out / 'queue.md').write_text(queue_md(queue, stamp), encoding='utf-8')
    stats = build_stats(new_rows, decisions, sites, rows_after)
    stats.update(date=stamp, dry_run=dry, overrides=len(ovr))
    (out / 'stats.json').write_text(json.dumps(stats, ensure_ascii=False, indent=1), encoding='utf-8')

    bs = stats['by_status']
    spam = sum(v for k, v in stats['by_rule'].items() if k.startswith('spam_'))
    summary = (f"world_reports: {len(new_rows)} new, {len(items)} auto (hidden {bs.get('auto_hidden', 0)}, "
               f"moved {bs.get('auto_moved', 0)}, access {bs.get('accepted', 0)}, spam {spam}), "
               f"{len(queue)} pids in queue, {len(ovr)} overrides{' [dry-run]' if dry else ''} -> {out}")
    log(summary)
    (out / 'run.log').write_text('\n'.join(log_lines) + '\n', encoding='utf-8')
    return summary


def selftest():
    fails, oks = [], []

    def check(cond, what):
        print(('ok   ' if cond else 'FAIL ') + what)
        (oks if cond else fails).append(what)

    check(geohash(57.64911, 10.40744, 11) == 'u4pruydqqvj', 'geohash of (57.64911, 10.40744) is u4pruydqqvj')
    check(geohash(44.81, 20.46, 5) == 'srywc', 'geohash of Belgrade is srywc')
    d = haversine(44.8125, 20.4612, 45.2671, 19.8335)
    check(70_000 < d < 72_000, f'haversine Belgrade–Novi Sad ≈ 71 km ({d:.0f} m)')
    check(abs(haversine(0, 0, 0, 0.001) - 111.2) < 0.5, 'haversine 0.001° of longitude at the equator ≈ 111 m')
    with tempfile.TemporaryDirectory() as td:
        lat, lon = 52.52, 13.405
        g = geohash(lat, lon, 5)
        Path(td, 'latest.json').write_text(json.dumps({'date': '2026-01-01'}))
        Path(td, 'manifest-2026-01-01.json').write_text(json.dumps(
            {'date': '2026-01-01', 'cards_base': 'cards-2026-01-01', 'cards_split': [g[:3]]}))
        Path(td, 'cards-2026-01-01').mkdir()
        Path(td, 'cards-2026-01-01', g[:4] + '.json').write_text(json.dumps(
            {'v': 1, 'sites': {'42': {'n': 'Test', 'src': [{'k': 'osm'}], 'cc': 'DE', 'conf': 50}}}))
        c = load_cards(td, {42: (lat, lon), 43: (lat, lon)})
        check(c.get(42, {}).get('n') == 'Test' and 43 not in c, f'card lookup in a split prefix ({g[:4]}.json)')
    print(f'{len(oks)} ok, {len(fails)} FAIL')
    return not fails


def main(argv=None):
    ap = argparse.ArgumentParser(description='World map reports: auto rules, queue and overrides.csv (K6).')
    ap.add_argument('--api', help='site base URL, e.g. https://www.blokvolt.rs (ADMIN_KEY from env)')
    ap.add_argument('--layer', help='K1 public_sites.geojsonseq (path or URL)')
    ap.add_argument('--data', help='directory or URL base with latest.json, manifest and cards')
    ap.add_argument('--out', help='output directory')
    ap.add_argument('--prev', help='previous overrides.csv to merge')
    ap.add_argument('--since', type=int, default=0, help='export rows created or decided since this unix time')
    ap.add_argument('--dry-run', action='store_true', help='compute and write files, do not POST')
    ap.add_argument('--fixture-reports', help='export JSON {"reports": [...]} instead of the API (implies --dry-run)')
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args(argv)
    if a.selftest:
        return 0 if selftest() else 1
    for need in ('layer', 'data', 'out'):
        if not getattr(a, need):
            ap.error(f'--{need} is required')
    print(run(a))
    return 0


if __name__ == '__main__':
    sys.exit(main())
