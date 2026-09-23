# -*- coding: utf-8 -*-
"""Data for /mapa/ — the map of public chargers with prices.

Stations come from two open snapshots kept in content/mapa/ (made by Scripts/make_chargers.py in the
Evolako iOS app repository, which has network access; copy both files here when they are refreshed):

    punjaci-ocm.json   Open Charge Map, CC BY 4.0
    punjaci-osm.json   OpenStreetMap, ODbL 1.0

They are merged here into one station list: records of one source closer than 40 m with a matching
name are one site (OSM often has a node per charger); an OSM record is the same site as an OCM record
within 200 m when both name the same network (Orion eMobility = the state chargers of JP "Putevi
Srbije"), otherwise within 60 m with the same top power or name. The merged list is an ODbL database and is published as such, with both attributions, in
/assets/map/punjaci.json. Our own price table is NOT merged into it: it is a separate file,
/assets/map/cene.json, built from content/javno/indeks-cena.json (the monthly screenshots) — the
browser joins the two when it shows a card.

The state motorway chargers get their status (works / does not work now) from the official list of JP "Putevi
Srbije", kept by hand in content/mapa/putevi-srbije.json (see putevi_official); working sites missing from both
open databases are added at their toll plaza / rest area position in OpenStreetMap.
"""
import json
import math
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAPA = ROOT / 'content' / 'mapa'

# operator keys of the app snapshot -> slugs of the network cards on this site
KEY = {'charge-and-go': 'chargego', 'orion': 'orion-emobility', 'nis': 'nis-gazprom', 'lidl': 'lidl-echarge',
       'virta': 'chargego'}   # in Serbia the Virta platform runs the Charge&GO network (BIG centres, "… Charge & GO")
NAME_RULES = [
    ('putevi-srbije', r'putevi srbije|roads of serbia|naplatn\w* stanic|toll (gate|station)'),
    ('chargego', r'charge\s*&?\s*(and\s*)?go|chargego'),
    ('orion-emobility', r'\borion\b'),
    ('emobility-spectra', r'spectra|\bemobility\b'),
    ('tesla', r'tesla'),
    ('lidl-echarge', r'\blidl\b'),
    ('parking-servis-beograd', r'obilicev venac|parking servis'),
]
# English words from Open Charge Map titles and addresses, shown in Serbian
DISPLAY = [(r'\bRoads of Serbia( Charger)?\b', 'Putevi Srbije'), (r'\bHighway near toll gate\b', 'Autoput, kod naplatne stanice'),
           (r'\bToll station\b', 'naplatna stanica'), (r'\bJust after the road toll station direction\b', 'Posle naplatne stanice, pravac'),
           (r'\bUrban Municipality\b', ''), (r'\bMunicipality\b', ''), (r'\bBelgrade\b', 'Beograd'), (r'\bBelgrad\b', 'Beograd'),
           (r'\bGarage\b', 'Garaža'), (r'\bRestaurant\b', 'Restoran'), (r'\bShopping Cent(er|ar)\b', 'Shopping Centar'),
           (r'\bSerbien \(Säule 1\)', 'Punjač'), (r'\s{2,}', ' '), (r',\s*,', ','), (r'[,\s]+$', '')]
# nearest town for stations without a name or address (approximate centres)
TOWNS = [('Beograd', 44.8125, 20.4612), ('Novi Sad', 45.2671, 19.8335), ('Niš', 43.3209, 21.8958), ('Kragujevac', 44.0128, 20.9114),
         ('Subotica', 46.1003, 19.6658), ('Zrenjanin', 45.3816, 20.3906), ('Pančevo', 44.8708, 20.6403), ('Čačak', 43.8914, 20.3497),
         ('Novi Pazar', 43.1367, 20.5122), ('Kraljevo', 43.7258, 20.6896), ('Smederevo', 44.6628, 20.9300), ('Leskovac', 42.9981, 21.9461),
         ('Valjevo', 44.2751, 19.8982), ('Kruševac', 43.5800, 21.3339), ('Vranje', 42.5514, 21.9003), ('Šabac', 44.7489, 19.6908),
         ('Užice', 43.8586, 19.8488), ('Sombor', 45.7742, 19.1122), ('Požarevac', 44.6194, 21.1869), ('Pirot', 43.1531, 22.5861),
         ('Zaječar', 43.9036, 22.2847), ('Kikinda', 45.8297, 20.4653), ('Sremska Mitrovica', 44.9764, 19.6122), ('Jagodina', 43.9771, 21.2612),
         ('Vršac', 45.1167, 21.3036), ('Bor', 44.0747, 22.0959), ('Ruma', 45.0080, 19.8222), ('Inđija', 45.0482, 20.0816),
         ('Stara Pazova', 44.9853, 20.1608), ('Bačka Palanka', 45.2508, 19.3919), ('Vrbas', 45.5717, 19.6403), ('Paraćin', 43.8600, 21.4078),
         ('Aleksinac', 43.5417, 21.7078), ('Prokuplje', 43.2342, 21.5881), ('Loznica', 44.5339, 19.2247), ('Obrenovac', 44.6550, 20.2000),
         ('Lazarevac', 44.3800, 20.2567), ('Mladenovac', 44.4378, 20.6922), ('Gornji Milanovac', 44.0253, 20.4617), ('Aranđelovac', 44.3069, 20.5600),
         ('Zlatibor', 43.7292, 19.7003), ('Kopaonik', 43.2856, 20.8111), ('Vrnjačka Banja', 43.6231, 20.8931), ('Šid', 45.1283, 19.2264),
         ('Bačka Topola', 45.8150, 19.6350), ('Senta', 45.9275, 20.0772), ('Bečej', 45.6164, 20.0489), ('Ćuprija', 43.9275, 21.3700),
         ('Negotin', 44.2267, 22.5308), ('Knjaževac', 43.5667, 22.2567), ('Preševo', 42.3089, 21.6500), ('Ivanjica', 43.5811, 20.2297),
         ('Prijepolje', 43.3897, 19.6489), ('Kovin', 44.7475, 20.9761), ('Velika Plana', 44.3336, 21.0756), ('Lapovo', 44.1842, 21.1033),
         ('Doljevac', 43.1967, 21.8322), ('Dimitrovgrad', 43.0161, 22.7753), ('Horgoš', 46.1564, 19.9725), ('Batrovci', 45.0517, 19.1047)]
NAMES = {
    'chargego': 'Charge&GO', 'orion-emobility': 'Orion eMobility', 'putevi-srbije': 'Putevi Srbije',
    'tesla': 'Tesla', 'nis-gazprom': 'NIS Petrol', 'omv': 'OMV', 'lidl-echarge': 'Lidl',
    'emobility-spectra': 'Emobility Spectra', 'eps': 'EPS', 'ikea': 'IKEA', 'mol': 'MOL', 'ionity': 'IONITY',
    'parking-servis-beograd': 'Parking servis Beograd',
}
DUP_M = 60          # different or unknown network: same site only when this close
DUP_NET_M = 200     # same network: one site per 200 m
SAME_SRC_M = 40     # duplicates inside one source


def fold(s):
    s = (s or '').lower().replace('đ', 'd')
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


def dist_m(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a['latitude'], a['longitude'], b['latitude'], b['longitude']))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371000 * 2 * math.asin(math.sqrt(h))


def max_kw(r):
    vals = [c['powerKW'] for c in r.get('connectors', []) if c.get('powerKW')]
    return max(vals) if vals else None


def _names_match(a, b):
    na, nb = fold(a.get('name')), fold(b.get('name'))
    return not na or not nb or na == nb or na in nb or nb in na


# Orion eMobility runs the state chargers of JP "Putevi Srbije": the two names are one site
SAME_NET = {frozenset(('orion-emobility', 'putevi-srbije'))}


def _same_net(x, y):
    return bool(x) and (x == y or frozenset((x, y)) in SAME_NET)


def same_place(a, b):
    """An OSM record `b` and an OCM record `a` describe one site: the same network within 200 m,
    or within 60 m (100 m with the same name) with the same top power or a matching name."""
    d = dist_m(a, b)
    if _same_net(a.get('_net'), b.get('_net')):
        return d <= DUP_NET_M
    same_name = fold(a.get('name')) != '' and fold(a.get('name')) == fold(b.get('name'))
    if d > (100 if same_name else DUP_M):
        return False
    if a.get('_net') and b.get('_net'):
        return False
    x, y = max_kw(a), max_kw(b)
    if x is not None and y is not None:
        return abs(x - y) < 1 or same_name
    return bool(fold(a.get('name'))) and _names_match(a, b)


def dedupe(recs):
    """Records of one source that describe one site (OSM often has a node per charger)."""
    out = []
    for r in recs:
        dup = None
        for o in out:
            d = dist_m(o, r)
            named_twice = fold(o.get('name')) != '' and fold(o.get('name')) == fold(r.get('name')) and _same_net(o.get('_net'), r.get('_net'))
            if d > (DUP_NET_M if named_twice else SAME_SRC_M):
                continue
            if o.get('_net') and r.get('_net') and not _same_net(o['_net'], r['_net']):
                continue
            x, y = max_kw(o), max_kw(r)
            if _names_match(o, r) and (x is None or y is None or abs(x - y) < 1 or fold(o.get('name')) == fold(r.get('name')) != ''):
                dup = o
                break
        if dup is None:
            out.append(dict(r))
            continue
        if not dup.get('name') and r.get('name'):
            dup['name'] = r['name']
        if not dup.get('address') and r.get('address'):
            dup['address'] = r['address']
        if r.get('_net') and (not dup.get('_net') or r['_net'] == 'putevi-srbije'):
            dup['_net'] = r['_net']
        if len(r.get('connectors') or []) > len(dup.get('connectors') or []):
            dup['connectors'] = r['connectors']
    return out


def network(rec_names, op_key, op_name):
    """Network that sells the charge: the station name wins (OCM lists the platform, OSM the host),
    then the operator name, then the app's key."""
    text = fold(' '.join(x for x in rec_names if x))
    if op_key == 'putevi-srbije' or re.search(r'putevi srbije', fold(op_name)):
        return 'putevi-srbije'
    for key, pat in NAME_RULES:
        if re.search(pat, text):
            return key
    if op_name and re.search(r'orion', fold(op_name)):
        return 'orion-emobility'
    return KEY.get(op_key, op_key)


def merge(ocm, osm):
    ocm = dedupe([dict(r, _net=network([r.get('name')], r.get('operator'), r.get('operatorName'))) for r in ocm if r.get('access') != 'private'])
    osm = dedupe([dict(r, _net=network([r.get('name')], r.get('operator'), r.get('operatorName'))) for r in osm if r.get('access') != 'private'])
    used, pairs, alone = set(), {}, []
    for r in osm:
        cands = [o for o in ocm if same_place(o, r)]
        free = [o for o in cands if o['id'] not in used]
        if free:
            m = min(free, key=lambda o: dist_m(o, r))
            used.add(m['id'])
            pairs[m['id']] = r
        elif not cands:
            alone.append((None, r))
        # else: a second OSM record of a site that is already paired — dropped as a duplicate
    return [(o, pairs.get(o['id'])) for o in ocm] + alone


def display(t):
    t = t or ''
    for pat, rep in DISPLAY:
        t = re.sub(pat, rep, t)
    return t.strip(' ,')


def near_town(lat, lon):
    best = min(TOWNS, key=lambda t: (t[1] - lat) ** 2 + ((t[2] - lon) * math.cos(math.radians(lat))) ** 2)
    d = math.hypot(best[1] - lat, (best[2] - lon) * math.cos(math.radians(lat))) * 111
    return best[0], d


def station(o, s):
    """One map station from an OCM record `o` and/or an OSM record `s`."""
    recs = [x for x in (o, s) if x]
    # Serbian names are usually in OSM, full addresses in OCM
    osm_name = s.get('name') if s else None
    name = osm_name if osm_name and not re.fullmatch(r'(?i)(charging station|punjač|punjac)', osm_name) else (o.get('name') if o else None)
    name = name or (o.get('name') if o else None) or (s.get('name') if s else None)
    addr = (o.get('address') if o else '') or (s.get('address') if s else '')
    conns = (o.get('connectors') if o and o.get('connectors') else None) or (s.get('connectors') if s else []) or []
    op_key = next((x.get('operator') for x in recs if x.get('operator')), None)
    op_name = next((x.get('operatorName') for x in recs if x.get('operatorName')), None)
    nets = [x.get('_net') for x in recs if x.get('_net')]
    net = ('putevi-srbije' if 'putevi-srbije' in nets else nets[0]) if nets else network([x.get('name') for x in recs], op_key, op_name)
    base = o or s
    town, km = near_town(base['latitude'], base['longitude'])
    name, addr = display(name), display(addr)
    dc = [c for c in conns if c.get('current') == 'dc']
    ac = [c for c in conns if c.get('current') != 'dc']
    kdc = max([c['powerKW'] for c in dc if c.get('powerKW')] or [0]) or None
    kac = max([c['powerKW'] for c in ac if c.get('powerKW')] or [0]) or None
    return {
        'id': base['id'],
        'n': name or '',
        'a': addr or '',
        't': town if km < 25 else '',
        'lat': round(base['latitude'], 5),
        'lon': round(base['longitude'], 5),
        'net': net or '',
        'opn': op_name or '',
        'c': [[c.get('type') or 'other', c.get('current') or 'ac', c.get('powerKW'), c.get('count') or 1] for c in conns],
        'dc': kdc,
        'ac': kac,
        'acc': 'customers' if any(x.get('access') == 'customers' for x in recs) else 'public',
        'src': [{'d': 'ocm' if x is o else 'osm', 'u': x.get('url'), 'upd': x.get('updated')} for x in recs],
    }


# ------------------------------------------------------------------ prices (our table)

def _num(s):
    return float(s.replace('.', '').replace(',', '.'))


def parse_charger(txt):
    """'DC 110–120 kW' -> ('dc', 110, 120); 'AC 22 kW' -> ('ac', 0, 22); 'DC' -> ('dc', None, None)."""
    t = txt or ''
    cur = 'dc' if re.search(r'\bDC\b', t) else 'ac'
    m = re.search(r'(\d+(?:,\d+)?)\s*(?:–|-)\s*(\d+(?:,\d+)?)\s*kW', t)
    if m:
        return cur, _num(m.group(1)), _num(m.group(2))
    m = re.search(r'(\d+(?:,\d+)?)\s*kW', t)
    if m:
        v = _num(m.group(1))
        return cur, (0 if cur == 'ac' else v), v
    return cur, None, None


def places(where):
    """'OMV Kneževac, OMV Borska, BIG Karaburma' -> folded place names to look for in a station."""
    w = re.sub(r'^punjač [^:]+:\s*', '', where or '')
    out = []
    for p in re.split(r',\s*(?![^()]*\))', w):
        p = re.sub(r'\(.*?\)', '', p).strip()
        f = fold(p)
        if f and len(f) > 3 and f not in GENERIC and not re.fullmatch(r'autoput.*|[\d\s]+', f):
            out.append(f)
    return out


# a place name that alone says nothing about which charger it is
GENERIC = {fold(t[0]) for t in TOWNS} | {'novi beograd', 'srbija', 'eksterno'}


def price_table(index, operators, logos):
    """{net: {...}} for the browser. Only what the price index says, with its date; nothing invented."""
    nets = {}
    ops = {o['slug']: o for o in operators}

    def base(slug):
        o = ops.get(slug, {})
        lg = logos.get(slug) or {}
        return {'name': NAMES.get(slug, o.get('name', slug)), 'page': f'/javno-punjenje/{slug}/' if slug in ops else '',
                'site': o.get('website', ''), 'logo': lg.get('logo', ''), 'logo_dark': bool(lg.get('dark')), 'tiers': [], 'places': [], 'receipts': []}

    for r in index['rows']:
        slug = {'lidl-echarge': 'lidl-echarge'}.get(r['op'], r['op'])
        n = nets.setdefault(slug, base(slug))
        if r.get('free'):
            n['free'] = True
            n['free_note'] = r.get('who') or ''
            n['date'] = r.get('date', '')
            continue
        if r.get('rsd_total'):
            n['receipts'].append({'where': places(r.get('where')), 'label': r['label'], 'kwh': round(r['rsd_total'] / r['kwh']), 'date': r.get('date', '')})
            continue
        if r.get('where', '').startswith('punjač '):
            continue   # roaming price of one app on another network's charger: shown on the network page, not on the map
        cur, lo, hi = parse_charger(r.get('charger'))
        item = {'cur': cur, 'lo': lo, 'hi': hi, 'charger': r.get('charger', ''), 'label': r['label'],
                'v': (r.get('rsd_min') or [None])[0], 'extra': r.get('who') or '', 'date': r.get('date', ''),
                'src': r.get('source', ''), 'where': places(r.get('where'))}
        if r.get('unit_rsd'):
            n['places'].append(item)       # per-station tariffs (Spectra): only where they were recorded
        else:
            n['tiers'].append(item)
    for slug in ('putevi-srbije', 'lidl-echarge'):
        if slug in nets:
            nets[slug]['free'] = True
    # free only where it was confirmed: Lidl on Liman, Novi Sad (other Lidl chargers: price unknown)
    if 'lidl-echarge' in nets:
        nets['lidl-echarge']['free_where'] = ['liman', 'novi sad', 'ive andrica']
        nets['lidl-echarge']['note'] = 'Besplatno je potvrđeno samo za Lidl na Limanu u Novom Sadu.'
    # networks without a published price: say where the price is
    for slug, note in (('tesla', 'Cena je u aplikaciji Tesla.'),
                       ('omv', 'Punjač na OMV stanici vodi Charge&GO, Orion ili EasyPark — cena je u njihovoj aplikaciji.'),
                       ('nis-gazprom', 'Punjače na NIS stanicama vodi Charge&GO — cena je u aplikaciji Charge&GO.'),
                       ('emobility-spectra', 'Cena je u aplikaciji Emobility Spectra.'),
                       ('orion-emobility', 'Tačna cena je u aplikaciji Orion eMobility; zavisi od lokacije.'),
                       ('chargego', 'Cena zavisi od snage punjača; tačna cena je u aplikaciji Charge&GO.')):
        nets.setdefault(slug, base(slug))['note'] = note
    nets['nis-gazprom']['via'] = 'chargego'
    return nets


def is_free(s, nets):
    if s.get('ps') and not any(l[2] == 1 for l in s['ps']['l']):
        return False   # a state charger that does not work now
    n = nets.get(s['net']) or {}
    if not n.get('free'):
        return False
    hay = fold(' '.join((s['n'], s['a'], s['t'])))
    return not n.get('free_where') or any(w in hay for w in n['free_where'])


def _ps_kw(power, cur):
    m = re.search(cur + r'\s*(\d+)\s*kW', power or '')
    return float(m.group(1)) if m else None


def putevi_official(stations):
    """The official list of the state motorway chargers (content/mapa/putevi-srbije.json).

    Each listed site gets 'ps' = {'d': date, 'site', 'road', 'l': [[direction, power, 1|0, note], ...]} on its stations
    (1 = works, 0 = does not work now; chargers still being connected are left out). Working sites that the open
    data does not have are added at the position of their toll plaza / rest area in OpenStreetMap."""
    f = MAPA / 'putevi-srbije.json'
    if not f.exists():
        return None
    ps = json.load(open(f, encoding='utf-8'))
    by_id = {s['id']: s for s in stations}
    for site in ps['sites']:
        lines = [[c.get('dir', ''), c.get('power', ''), c['status'], c.get('note', '')] for c in site['chargers'] if c['status'] >= 0]
        if not lines:
            continue
        info = {'d': ps['checked'], 'site': site['name'], 'road': site['road'], 'l': lines}
        found = [by_id[i] for i in site.get('ids', []) if i in by_id]
        for i in site.get('ids', []):
            if i not in by_id:
                print('putevi-srbije.json: station', i, 'is not in the open data any more —', site['name'])
        dirs = sorted({l[0] for l in lines if l[0]})
        dc = max([_ps_kw(l[1], 'DC') or 0 for l in lines]) or None
        ac = max([_ps_kw(l[1], 'AC') or 0 for l in lines]) or None
        for st in found:   # the official name, road and power instead of the mixed (and older) open data
            st['ps'] = info
            st['net'] = 'putevi-srbije'
            st['n'] = site['name']
            st['a'] = ' · '.join([site['road']] + dirs)
            st['dc'], st['ac'] = dc, ac
            st['c'] = [[c[0], c[1], None, c[3]] for c in st['c']]   # connector types stay, their old kW do not
            st['src'].append({'d': 'ps', 'u': ps['source'], 'upd': '-'.join(reversed(ps['checked'].split('.')))})
        if not found and site.get('lat') and any(l[2] == 1 for l in lines):
            stations.append({
                'id': 'ps-' + re.sub(r'[^a-z0-9]+', '-', fold(site['name'])).strip('-'),
                'n': site['name'], 'a': ' · '.join([site['road']] + dirs), 't': site.get('place', ''),
                'lat': site['lat'], 'lon': site['lon'], 'net': 'putevi-srbije', 'opn': 'JP Putevi Srbije',
                'c': [], 'dc': dc, 'ac': ac, 'acc': 'public',
                'src': [{'d': 'ps', 'u': ps['source'], 'upd': '-'.join(reversed(ps['checked'].split('.')))},
                        {'d': 'osm', 'u': site.get('pos', ''), 'upd': ''}],
                'ps': info,
            })
    ch = [c for site in ps['sites'] for c in site['chargers']]
    return {'total': len(ch), 'works': sum(1 for c in ch if c['status'] == 1), 'down': sum(1 for c in ch if c['status'] == 0),
            'connecting': sum(1 for c in ch if c['status'] == -1), 'planned': ps.get('planned', 0), 'checked': ps['checked'],
            'source': ps['source'], 'sites': ps['sites']}


def build(dist, operators, index, logos):
    ocm = json.load(open(MAPA / 'punjaci-ocm.json', encoding='utf-8'))
    osm = json.load(open(MAPA / 'punjaci-osm.json', encoding='utf-8'))
    stations = [station(o, s) for o, s in merge(ocm['chargers'], osm['chargers'])]
    # bicycle and scooter chargers are not for cars
    stations = [s for s in stations if not re.search(r'(?i)bikeep|bicikl|\bbike\b|e-bike|trotinet|scooter', s['n'] + ' ' + s['opn'])]
    ps = putevi_official(stations)
    stations.sort(key=lambda x: (fold(x['n']) or 'zzz', x['id']))
    out = dist / 'assets' / 'map'
    out.mkdir(parents=True, exist_ok=True)
    head = {
        'about': 'Javni punjači u Srbiji za mapu na www.blokvolt.rs: spoj Open Charge Map i OpenStreetMap snimka.',
        'license': 'ODbL 1.0 — https://opendatacommons.org/licenses/odbl/1-0/',
        'attribution': ['© OpenStreetMap contributors (ODbL 1.0) — https://www.openstreetmap.org/copyright',
                        'Open Charge Map contributors (CC BY 4.0) — https://openchargemap.org',
                        'Status i spisak državnih punjača na autoputevima: JP „Putevi Srbije“ — https://www.putevi-srbije.rs/index.php/en/electric-chargers'],
        'ocm_updated': ocm.get('dataUpdated'), 'osm_updated': osm.get('dataUpdated'),
        'retrieved': max(ocm.get('retrieved', ''), osm.get('retrieved', '')),
    }
    (out / 'punjaci.json').write_text(json.dumps(dict(head, stations=stations), ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    nets = price_table(index, operators, logos)
    prices = {'about': 'Cene javnog punjenja po mrežama sa www.blokvolt.rs (aplikacije mreža i računi, sa datumom). CC BY 4.0.',
              'updated': index.get('updated', ''), 'nets': nets}
    (out / 'cene.json').write_text(json.dumps(prices, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    counts = {}
    for s in stations:
        counts[s['net'] or ''] = counts.get(s['net'] or '', 0) + 1
    fast = sum(1 for s in stations if (s['dc'] or 0) >= 50)
    free = sum(1 for s in stations if is_free(s, nets))
    return {'n': len(stations), 'fast': fast, 'free': free, 'counts': counts, 'retrieved': head['retrieved'],
            'ocm_updated': head['ocm_updated'], 'osm_updated': head['osm_updated'], 'nets': nets, 'stations': stations, 'ps': ps}
