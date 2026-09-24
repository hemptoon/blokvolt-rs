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

Every station is then checked (verify): against the lists the networks publish themselves (content/mapa/mreze/:
Charge&GO, the Charge&GO roaming map, Tesla) and by hand (content/mapa/provera.json: removals, duplicates, positions,
the Google Maps check). Each station gets v = {'s': 'ok' | 'nep' | 'prob', ...}. Connectors and names from the
networks' lists, and the stations only they have, go to /assets/map/mreze.json (not ODbL); the browser joins it
with punjaci.json. See docs/RUNBOOK.md §3.11b.
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


# ------------------------------------------------------------------ check against the networks' own lists

MREZE = MAPA / 'mreze'
CYR = dict(zip('абвгдђежзијклмнопрстћуфхцчшАБВГДЂЕЖЗИЈКЛМНОПРСТЋУФХЦЧШ', 'abvgdđežzijklmnoprstćufhcčšABVGDĐEŽZIJKLMNOPRSTĆUFHCČŠ'))
CYR.update({'љ': 'lj', 'њ': 'nj', 'џ': 'dž', 'Љ': 'Lj', 'Њ': 'Nj', 'Џ': 'Dž'})
# the networks' place names as they should read on the map (raw name -> name)
NAME_FIX = {
    'Suvoborska180-002': 'Suvoborska', 'Konjarnik180-001': 'Konjarnik', 'PancevackiPut180-001': 'Pančevački put',
    'MIND CHARGHER 120 KW': 'MIND', 'FMC NETS punjac': 'FMC Nets', 'ABB Doo Bulevar Peka Dapcevica 13 Terra': 'ABB',
    'Ehom Auto Severni bulevar 6': 'Ehom Auto', 'Kemoimpex Vizantijski bulevar BB': 'Kemoimpex', 'Hotel Izvor EV2': 'Hotel Izvor',
    'Auto Kuca Mikom doo': 'Auto kuća Mikom', 'Skoda Auto Cacak': 'Škoda Auto Čačak', 'BS EVOIL Preljina': 'Evoil Preljina',
    'AC BRAJIC Sabac': 'AC Brajić', 'Jevtovic Cars': 'Jevtović Cars', 'NIS Sokolici 2': 'NIS Sokolići 2', 'OMV Razanj': 'OMV Ražanj',
    'Delta Planet Nis': 'Delta Planet Niš', 'IDEAL AUTO DOO NIS': 'Ideal Auto', 'SIRIUS eksterno': 'Sirius', 'SIRIUS Interno': 'Sirius',
    'SIRIUS INTERNO': 'Sirius', 'BS NIS Krnješevci, autoput Beograd - Zagreb, sm...': 'NIS Krnješevci, autoput Beograd–Zagreb',
    'EVROBROD DOO ZRENJANIN': 'Evrobrod', 'KPM AUTOMOBILI': 'KPM Automobili', 'DelAsol AC': 'Stop Shop DeLasol Lapovo',
    'Duo-pro inženjering doo Ćuprija': 'Duo-Pro inženjering', 'Svetozarevo promet doo': 'Svetozarevo promet',
    'Hyundai centar „Marić Centar“ d.o.o.': 'Hyundai centar Marić', 'B2 SUN SPORT MOKRIN (KIKINDA)': 'B2 Sun Sport Mokrin',
    'MILKOP DOO RAŠKA': 'Milkop Raška', 'Crowne Plaza Hypercharger': 'Crowne Plaza', 'Shell Batajnica 1': 'Shell Batajnica',
    'Shell Adaševci 1': 'Shell Adaševci', 'BEX Subotica 1': 'BEX Subotica', 'BEX Jagodina 1': 'BEX Jagodina', 'NIS Zmaj 1': 'NIS Zmaj',
    'Delta kongresni centar - Sava Centar': 'Sava Centar (Delta kongresni centar)', 'Opština Bela Palanka': 'Bela Palanka',
}
CITY_FIX = {'belgrade': 'Beograd', 'unknown': '', 'vojvodina': '', 'bajina basta': 'Bajina Bašta', 'loznica 15300': 'Loznica',
            'ub': 'Ub', 'indjija': 'Inđija', 'krusevac': 'Kruševac', 'razanj': 'Ražanj', 'cicevac': 'Ćićevac', 'kosevi': 'Koševi',
            'vrnjacka banja': 'Vrnjačka Banja', 'pecinci': 'Pećinci', 'sokolici': 'Sokolići', 'jagodina 35000': 'Jagodina'}
KEEP_UP = {'OMV', 'BIG', 'NIS', 'BEX', 'HBIS', 'NCR', 'BMW', 'ABB', 'KPM', 'MIF', 'OBD2', 'FMC', 'MIND', 'SIRIUS'}
PLUS_CODE = r'\b[23456789CFGHJMPQRVWX]{4}\+[23456789CFGHJMPQRVWX]{2,3}\b'
ROAM_NET = {'RS*ORI': 'orion-emobility'}   # other roaming operators (RS*007, RO*PLG): network not published
MATCH_M = {'same': 250, 'host': 150, 'none': 100}   # official site <-> open-data station, by how well the networks agree
HOST_NETS = {'nis-gazprom', 'omv'}   # hosts whose chargers another network runs


def latin(s):
    return ''.join(CYR.get(c, c) for c in (s or ''))


def smart_case(s):
    """'STOP SHOP Vršac' -> 'Stop Shop Vršac', 'MT-KOMEX' -> 'MT-Komex'; short acronyms stay."""
    s = re.sub(r'[A-ZČĆŽŠĐ]{4,}', lambda m: m.group(0) if m.group(0) in KEEP_UP else m.group(0)[0] + m.group(0)[1:].lower(), s)
    s = re.sub(r'^BS Gazprom\b', 'Gazprom', s)
    return re.sub(r'\s*\b(d\.o\.o\.|doo|Doo|DOO)\b\.?', '', s).strip(' ,-')


def _city(c):
    c = latin(c).strip()
    f = fold(c)
    if f in CITY_FIX:
        return CITY_FIX[f]
    return smart_case(c.title() if c.islower() or c.isupper() else c)


def _street(s, city):
    s = re.sub(PLUS_CODE, '', latin(s or '')).replace(' --', '').strip(' ,-')
    s = smart_case(s)
    if city and fold(s).endswith(fold(city)):
        s = s[:len(s) - len(city)].strip(' ,')
    return s


def _kw(p):
    m = re.match(r'(\d+(?:\.\d+)?)', p)
    return round(float(m.group(1))) if m else None


CG_T = {'CCS': ('ccs2', 'dc'), 'T2': ('type2', 'ac'), 'cha_de_mod': ('chademo', 'dc'), 'type_2_outlet': ('type2', 'ac')}
RM_T = {'CCS': ('ccs2', 'dc'), 'CHA': ('chademo', 'dc'), 'T2c': ('type2', 'ac'), 'T2o': ('type2', 'ac')}


def _cg_conns(s):
    """'CCSd120a,CCSd120a,T2a22a' -> [['ccs2', 'dc', 120, 2], ['type2', 'ac', 22, 1]] (last letter = status then, not kept)."""
    out = {}
    for x in filter(None, s.split(',')):
        m = re.fullmatch(r'(CCS|T2|cha_de_mod|type_2_outlet)[ad](\d+(?:\.\d+)?)[a-z]', x)
        if m:
            t, cur = CG_T[m.group(1)]
            k = (t, cur, round(float(m.group(2))))
            out[k] = out.get(k, 0) + 1
    return [[t, cur, kw, n] for (t, cur, kw), n in out.items()]


def _rm_conns(plugs, power):
    """'T2o;CHA;CCS', '22AC_3_PHASE;50DC;75DC' -> connectors; powers pair with plugs when the lists are as long."""
    pl = [p for p in plugs.split(';') if p in RM_T]
    pw = [p for p in power.split(';') if p]
    out = []
    if len(pl) == len(pw):
        for p, w in zip(pl, pw):
            t, cur = RM_T[p]
            out.append([t, cur, _kw(w), 1])
    else:
        ac = sorted({_kw(w) for w in pw if 'AC' in w and _kw(w)}, reverse=True)
        dc = sorted({_kw(w) for w in pw if 'DC' in w and _kw(w)}, reverse=True)
        for p in dict.fromkeys(pl):
            t, cur = RM_T[p]
            vals = dc if cur == 'dc' else ac
            kw = (min(vals) if t == 'chademo' else max(vals)) if vals else None
            out.append([t, cur, kw, 1])
    uniq = {}
    for c in out:
        k = tuple(c[:3])
        uniq[k] = uniq.get(k, 0) + c[3]
    return [[t, cur, kw, n] for (t, cur, kw), n in uniq.items()]


def official_sites():
    """Locations from the networks' own lists (content/mapa/mreze/), one record per site."""
    meta = json.load(open(MREZE / 'izvori.json', encoding='utf-8'))
    recs = []
    for line in open(MREZE / meta['cg']['file'], encoding='utf-8'):
        f = line.rstrip('\n').split('|')
        if len(f) < 9:
            continue
        cid, lat, lon, name, street, city, acc = f[0], float(f[1]), float(f[2]), f[3], f[4], f[5], f[6]
        if lat < 42.2 or fold(city) == 'skopje':
            continue   # North Macedonia
        c = _city(city)
        recs.append({'k': 'cg', 'id': 'cg-' + cid, 'lat': lat, 'lon': lon, 'net': 'chargego', 'raw': name,
                     'n': smart_case(NAME_FIX.get(name, name)), 'a': ', '.join(x for x in (_street(street, c), c) if x),
                     'c': _cg_conns(f[8]), 'evse': None, 'test': acc == 'test'})   # test = in trial operation, not public yet
    for line in open(MREZE / meta['rm']['file'], encoding='utf-8'):
        f = line.rstrip('\n').split('|')
        if len(f) < 11:
            continue
        lat, lon, op, n, name, street, city = float(f[0]), float(f[1]), f[2], int(f[3]), f[6], f[7], f[8]
        if re.search(r'(?i)\btest\b', name):
            continue
        c = _city(city)
        nm = '' if re.fullmatch(r'E\d{5}', name) else smart_case(NAME_FIX.get(name, name))
        recs.append({'k': 'rm', 'id': 'rm-%d-%d' % (round(lat * 1e5), round(lon * 1e5)), 'lat': lat, 'lon': lon,
                     'net': ROAM_NET.get(op, ''), 'op': op, 'raw': name, 'n': nm,
                     'a': ', '.join(x for x in (_street(street, c), c) if x), 'c': _rm_conns(f[9], f[10]), 'evse': n,
                     'putevi': bool(re.search(r'(?i)putevi|naplatn|odmori', name + ' ' + street))})
    te = json.load(open(MREZE / meta['te']['file'], encoding='utf-8'))
    for s in te['sites']:
        if s.get('lat') is None:
            continue
        recs.append({'k': 'te', 'id': 'te-' + re.sub(r'[^a-z0-9]+', '-', fold(s['name'])).strip('-'), 'lat': s['lat'], 'lon': s['lon'],
                     'net': 'tesla', 'raw': s['name'], 'n': s['name'], 'a': s.get('addr', ''), 'kind': s.get('kind'),
                     'c': [['tesla', 'dc', None, 1]] if s.get('kind') == 'supercharger' else [['type2', 'ac', None, 1]], 'evse': None})
    # one site per network within 80 m (Crowne Plaza 1, 2, 3 and the hypercharger; SIRIUS eksterno / interno)
    sites = []
    for r in recs:
        same = next((x for x in sites if x['k'] == r['k'] and x['net'] == r['net'] and dist_m(_ll(x), _ll(r)) <= 80
                     and _first(x['raw']) == _first(r['raw'])), None)
        if same is None:
            sites.append(dict(r, parts=1))
            continue
        same['parts'] += 1
        conns = {tuple(c[:3]): c[3] for c in same['c']}
        for c in r['c']:
            conns[tuple(c[:3])] = conns.get(tuple(c[:3]), 0) + c[3]
        same['c'] = [[t, cur, kw, n] for (t, cur, kw), n in conns.items()]
        if (r.get('evse') or 0) > (same.get('evse') or 0) and r['n']:
            same['n'] = r['n']
        same['n'] = re.sub(r'\s+\d$', '', same['n'])
        same['putevi'] = same.get('putevi') or r.get('putevi')
    return sites, meta


def _ll(x):
    return {'latitude': x['lat'], 'longitude': x['lon']}


def _first(name):
    """First word of a name: records of one site share it (Crowne Plaza 1, Crowne Plaza Hypercharger)."""
    w = re.findall(r'[a-z0-9]+', fold(name))
    return w[0] if w else ''


def _fit(st_net, site_net):
    """How well a station's network agrees with the network of an official site."""
    if not st_net:
        return 'none'
    if _same_net(st_net, site_net) or (st_net == 'orion-emobility' and site_net == 'putevi-srbije'):
        return 'same'
    if st_net in HOST_NETS:
        return 'host'
    return None


def manual_check(stations):
    """content/mapa/provera.json: remove, join duplicates, move to the right position. Returns the notes of the rest."""
    f = MAPA / 'provera.json'
    if not f.exists():
        return {}, ''
    pr = json.load(open(f, encoding='utf-8'))
    by_id = {s['id']: s for s in stations}
    drop = set()
    for sid, v in pr['stations'].items():
        s = by_id.get(sid)
        if s is None:
            print('provera.json: station', sid, 'is not in the open data any more')
            continue
        if v.get('x'):
            drop.add(sid)
        elif v.get('dup') and v['dup'] in by_id:
            _absorb(by_id[v['dup']], s)
            drop.add(sid)
        elif v.get('fix'):
            s['lat'], s['lon'] = v['fix']
    stations[:] = [s for s in stations if s['id'] not in drop]
    return pr['stations'], pr.get('checked', '')


def _absorb(keep, other):
    """Join a duplicate station into `keep` (sources, and what `keep` does not know)."""
    for k in ('n', 'a', 't', 'net', 'opn'):
        if not keep.get(k) and other.get(k):
            keep[k] = other[k]
    if len(other.get('c') or []) > len(keep.get('c') or []) and not keep.get('ps'):
        keep['c'], keep['dc'], keep['ac'] = other['c'], other['dc'], other['ac']
    have = {(x['d'], x.get('u')) for x in keep['src']}
    keep['src'] += [x for x in other['src'] if (x['d'], x.get('u')) not in have]
    if other.get('acc') == 'customers':
        keep['acc'] = 'customers'


def verify(stations, notes, checked):
    """Mark every station as confirmed or not, against the networks' own lists; join duplicates that are one listed site;
    return the network data for the map layer /assets/map/mreze.json: {'upd': {id: …}, 'add': [stations]}."""
    sites, meta = official_sites()
    iso = lambda d: '-'.join(reversed(d.split('.')))
    # roaming records of the state chargers (Orion runs them): known by name, or by a state charger next to them
    ps_at = [s for s in stations if s.get('ps')]
    for site in sites:
        if site['k'] == 'rm' and not site.get('putevi'):
            site['putevi'] = any(dist_m(_ll(site), _ll(s)) <= 500 for s in ps_at)
    # each open-data station goes to its nearest official site that fits
    claim = {}
    for s in stations:
        best = None
        for site in sites:
            fit = _fit(s.get('net'), site['net'])
            if fit is None and not (s.get('ps') and site.get('putevi')):
                continue
            lim = MATCH_M['same'] if s.get('ps') and site.get('putevi') else MATCH_M.get(fit, 0)
            d = dist_m(_ll(s), _ll(site))
            if d <= lim and (best is None or d < best[0]):
                best = (d, site)
        if best:
            claim.setdefault(id(best[1]), (best[1], []))[1].append(s)
    upd, add, gone = {}, [], set()
    for site, sts in claim.values():
        # open-data duplicates of one listed site become one station (the one with the most sources)
        sts.sort(key=lambda x: (-bool(x.get('ps')), -len(x['src']), -len(x.get('c') or []), x['id']))
        keep = sts[0]
        for other in sts[1:]:
            if dist_m(_ll(keep), _ll(other)) <= 250 and not other.get('ps'):
                _absorb(keep, other)
                gone.add(other['id'])
        if site.get('test'):
            keep['v'] = {'s': 'nep', 'g': 'test', 'd': meta[site['k']]['date']}   # the network lists it as in trial operation
            continue
        by = sorted(set((keep.get('v') or {}).get('by', [])) | {site['k']})
        keep['v'] = {'s': 'ok', 'by': by, 'd': meta[site['k']]['date']}
        if site.get('putevi') or keep.get('ps'):
            continue   # the state chargers keep the official list of JP "Putevi Srbije"
        u = {'src': [{'d': site['k'], 'u': meta[site['k']]['url'], 'upd': iso(meta[site['k']]['date'])}]}
        if site['c'] and site['k'] != 'te':
            dc = [c[2] for c in site['c'] if c[1] == 'dc' and c[2]]
            ac = [c[2] for c in site['c'] if c[1] == 'ac' and c[2]]
            u.update(c=site['c'], dc=max(dc) if dc else None, ac=max(ac) if ac else None)
        if not keep.get('net') and site['net']:
            u['net'] = site['net']
        # the network's own name of the place, unless the open data says more (Sirius Office Building > Sirius)
        if site['k'] != 'te' and site['n'] and fold(site['n']) not in fold(keep.get('n')):
            u['n'] = site['n']
            if site['a']:
                u['a'] = site['a']
        upd[keep['id']] = u
    stations[:] = [s for s in stations if s['id'] not in gone]
    claimed = {id(site) for site, _ in claim.values()}
    for site in sites:
        if id(site) in claimed or site.get('putevi') or site.get('test'):
            continue   # the state chargers come from the list of JP "Putevi Srbije" only; chargers in trial are not added
        dc = [c[2] for c in site['c'] if c[1] == 'dc' and c[2]]
        ac = [c[2] for c in site['c'] if c[1] == 'ac' and c[2]]
        town, km = near_town(site['lat'], site['lon'])
        add.append({'id': site['id'], 'n': site['n'], 'a': site['a'], 't': town if km < 25 else '',
                    'lat': round(site['lat'], 5), 'lon': round(site['lon'], 5), 'net': site['net'], 'opn': '',
                    'c': site['c'], 'dc': max(dc) if dc else None, 'ac': max(ac) if ac else None, 'acc': 'public',
                    'src': [{'d': site['k'], 'u': meta[site['k']]['url'], 'upd': iso(meta[site['k']]['date'])}],
                    'v': {'s': 'ok', 'by': [site['k']], 'd': meta[site['k']]['date']}})
    for s in stations:
        if s.get('ps') and not s.get('v'):
            s['v'] = {'s': 'ok', 'by': ['ps'], 'd': s['ps']['d']}
        elif s.get('ps'):
            s['v']['by'] = sorted(set(s['v']['by']) | {'ps'})
        if s.get('v'):
            continue
        n = notes.get(s['id']) or {}
        g = n.get('g', '')
        if g == 'g':
            s['v'] = {'s': 'ok', 'by': ['g'], 'd': checked}
        else:
            s['v'] = {'s': 'prob' if g == 'prob' else 'nep', 'g': g or 'g_none', 'd': checked}
            if n.get('note'):
                s['v']['note'] = n['note']
    return {'upd': upd, 'add': add}


def build(dist, operators, index, logos):
    ocm = json.load(open(MAPA / 'punjaci-ocm.json', encoding='utf-8'))
    osm = json.load(open(MAPA / 'punjaci-osm.json', encoding='utf-8'))
    stations = [station(o, s) for o, s in merge(ocm['chargers'], osm['chargers'])]
    # bicycle and scooter chargers are not for cars
    stations = [s for s in stations if not re.search(r'(?i)bikeep|bicikl|\bbike\b|e-bike|trotinet|scooter', s['n'] + ' ' + s['opn'])]
    notes, checked = manual_check(stations)
    ps = putevi_official(stations)
    nets_layer = verify(stations, notes, checked)
    stations.sort(key=lambda x: (fold(x['n']) or 'zzz', x['id']))
    out = dist / 'assets' / 'map'
    out.mkdir(parents=True, exist_ok=True)
    head = {
        'about': 'Javni punjači u Srbiji za mapu na www.blokvolt.rs: spoj Open Charge Map i OpenStreetMap snimka, sa proverom '
                 '(v: ok = potvrđeno na spisku mreže ili ručno; nep = nije potvrđeno; prob = skorašnje prijave da ne radi).',
        'license': 'ODbL 1.0 — https://opendatacommons.org/licenses/odbl/1-0/',
        'attribution': ['© OpenStreetMap contributors (ODbL 1.0) — https://www.openstreetmap.org/copyright',
                        'Open Charge Map contributors (CC BY 4.0) — https://openchargemap.org',
                        'Status i spisak državnih punjača na autoputevima: JP „Putevi Srbije“ — https://www.putevi-srbije.rs/index.php/en/electric-chargers'],
        'ocm_updated': ocm.get('dataUpdated'), 'osm_updated': osm.get('dataUpdated'),
        'retrieved': max(ocm.get('retrieved', ''), osm.get('retrieved', '')), 'checked': checked,
    }
    (out / 'punjaci.json').write_text(json.dumps(dict(head, stations=stations), ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    layer = {'about': 'Lokacije i priključci sa javnih mapa mreža (Charge&GO, roming mapa Charge&GO, Tesla), za dopunu mape na '
                      'www.blokvolt.rs. Nije deo otvorenog skupa podataka punjaci.json; podaci pripadaju mrežama.',
             'upd': nets_layer['upd'], 'add': nets_layer['add']}
    (out / 'mreze.json').write_text(json.dumps(layer, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    # the full list the pages count with: open data + the networks' own locations and connectors
    for s in stations:
        u = nets_layer['upd'].get(s['id'])
        if u:
            s.update({k: v for k, v in u.items() if k != 'src'})
            s['src'] = s['src'] + u['src']
    stations = stations + nets_layer['add']
    stations.sort(key=lambda x: (fold(x['n']) or 'zzz', x['id']))
    nets = price_table(index, operators, logos)
    prices = {'about': 'Cene javnog punjenja po mrežama sa www.blokvolt.rs (aplikacije mreža i računi, sa datumom). CC BY 4.0.',
              'updated': index.get('updated', ''), 'nets': nets}
    (out / 'cene.json').write_text(json.dumps(prices, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    counts = {}
    for s in stations:
        counts[s['net'] or ''] = counts.get(s['net'] or '', 0) + 1
    fast = sum(1 for s in stations if (s['dc'] or 0) >= 50)
    free = sum(1 for s in stations if is_free(s, nets))
    return {'n': len(stations), 'fast': fast, 'free': free, 'counts': counts, 'retrieved': head['retrieved'], 'checked': checked,
            'ocm_updated': head['ocm_updated'], 'osm_updated': head['osm_updated'], 'nets': nets, 'stations': stations, 'ps': ps}
