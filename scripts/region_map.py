# -*- coding: utf-8 -*-
"""Station lists for the country maps of blokvolt.com (/hr/karta/, /ba/mapa/, /me/mapa/ …) — docs/RUNBOOK.md 3.23.

Input: the branch `region-data` of this repository (OpenStreetMap + Open Charge Map per country, fetched monthly by
.github/workflows/region-data.yml). `--fetch` downloads it from raw.githubusercontent.com into content/com/region-data/
(not committed; the processed lists below are). Without `--fetch` the cached copy is used.

Output per country: content/com/local/<cc>/stanice.json — one merged list in the station format of /mapa/ on
blokvolt.rs (static/assets/map.js): id, n, a, t, lat, lon, net, opn, c [[type, ac|dc, kW, count]], dc, ac, acc, src, v.
It is an ODbL database (OpenStreetMap) with Open Charge Map records (CC BY 4.0; records of providers with a
non-commercial licence are left out) and is published with both attributions.

Same-site rules follow scripts/map_data.py (Serbia): records of one source closer than 40 m that do not contradict each
other are one site (OSM often has a node per charger); an OSM record and an OCM record are one site within 200 m when both
name the same network, otherwise within 60 m (100 m with the same name) with the same top power or a matching name.
Networks are recognised by country-specific rules on the name, operator, brand and network fields (NETS below).
Nothing here is verified by hand: every station carries v = {'s': 'src'} (from the open databases, not checked one by one).

Usage: python3 scripts/region_map.py [--fetch] [CC ...]      (default: HR BA ME AL XK)"""
import json
import math
import re
import sys
import unicodedata
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / 'content' / 'com' / 'region-data'
LOCAL = ROOT / 'content' / 'com' / 'local'
RAW = 'https://raw.githubusercontent.com/hemptoon/blokvolt-rs/region-data/'
COUNTRIES = ['HR', 'BA', 'ME', 'AL', 'XK']

SAME_SRC_M = 40
DUP_M = 60
DUP_NET_M = 200

# network slug -> pattern on the folded name/operator/brand/network text. Order matters (first match wins).
NETS = {
    'HR': [('ionity', r'ionity'), ('tesla', r'supercharger'), ('elen', r'\belen\b|\bhep\b|hrvatska elektroprivreda'),
           ('petrol', r'\bpetrol\b|onecharge'), ('mol', r'\bmol\b|tifon|plugee'),
           ('ht', r'hrvatski telekom|\bht\b|espots?\b|e-?spot\b'), ('lidl', r'\blidl\b'), ('kaufland', r'kaufland'),
           ('electrip', r'electrip'), ('moon', r'\bmoon\b|porsche'), ('greenway', r'greenway'), ('qelo', r'\bqelo\b'),
           ('eon', r'\be\.?\s?on\b'), ('ina', r'\bina\b'), ('tesla', r'\btesla\b')],
    'BA': [('epbih', r'epbih|elektroprivreda bih|elektroprivreda bosne'), ('moon', r'\bmoon\b|porsche'),
           ('ephzhb', r'ep ?hz ?hb|elektroprivreda hz'), ('ers', r'elektroprivreda republike srpske|\bers\b'),
           ('tesla', r'supercharger|\btesla\b'), ('elen', r'\belen\b'), ('petrol', r'\bpetrol\b')],
    'ME': [('eko', r'\beko\b|jugopetrol|helleniq'), ('epcg', r'epcg|elektroprivreda crne gore'), ('petrol', r'\bpetrol\b'),
           ('tesla', r'supercharger|\btesla\b'), ('greencar', r'greencar')],
    'AL': [('vega', r'\bvega\b'), ('plugo', r'plugo'), ('icharge', r'icharge'), ('oshee', r'oshee'), ('tesla', r'\btesla\b')],
    'XK': [('echarge', r'e-?charge'), ('hib', r'\bhib\b'), ('tesla', r'\btesla\b')],
}
NAMES = {'ionity': 'IONITY', 'tesla': 'Tesla Supercharger', 'elen': 'ELEN (HEP)', 'petrol': 'Petrol', 'mol': 'MOL Plugee',
         'ht': 'Hrvatski Telekom', 'lidl': 'Lidl', 'kaufland': 'Kaufland', 'electrip': 'Electrip', 'moon': 'MOON',
         'greenway': 'GreenWay', 'qelo': 'Qelo', 'eon': 'E.ON', 'ina': 'INA', 'epbih': 'Elektroprivreda BiH',
         'ephzhb': 'EP HZ HB', 'ers': 'Elektroprivreda RS', 'eko': 'EKO (Jugopetrol)', 'epcg': 'EPCG', 'greencar': 'Greencar',
         'vega': 'VEGA', 'plugo': 'PlugoAL', 'icharge': 'iCharge', 'oshee': 'OSHEE', 'echarge': 'ECHARGE', 'hib': 'HIB Petrol'}

# the biggest towns, for "near …" when a record has no town (lat, lon)
TOWNS = {
    'HR': [('Zagreb', 45.8150, 15.9819), ('Split', 43.5081, 16.4402), ('Rijeka', 45.3271, 14.4422), ('Osijek', 45.5550, 18.6955),
           ('Zadar', 44.1194, 15.2314), ('Pula', 44.8666, 13.8496), ('Slavonski Brod', 45.1603, 18.0156), ('Karlovac', 45.4929, 15.5553),
           ('Varaždin', 46.3057, 16.3366), ('Šibenik', 43.7350, 15.8952), ('Sisak', 45.4658, 16.3782), ('Dubrovnik', 42.6507, 18.0944),
           ('Velika Gorica', 45.7125, 16.0756), ('Bjelovar', 45.8986, 16.8423), ('Vinkovci', 45.2883, 18.8047), ('Koprivnica', 46.1628, 16.8275),
           ('Čakovec', 46.3844, 16.4339), ('Požega', 45.3403, 17.6853), ('Vukovar', 45.3517, 19.0022), ('Gospić', 44.5461, 15.3747),
           ('Makarska', 43.2969, 17.0178), ('Poreč', 45.2269, 13.5947), ('Rovinj', 45.0812, 13.6387), ('Umag', 45.4316, 13.5232),
           ('Krk', 45.0253, 14.5750), ('Knin', 44.0406, 16.1994), ('Senj', 44.9894, 14.9058), ('Otočac', 44.8697, 15.2375)],
    'BA': [('Sarajevo', 43.8563, 18.4131), ('Banja Luka', 44.7722, 17.1910), ('Tuzla', 44.5384, 18.6671), ('Zenica', 44.2034, 17.9077),
           ('Mostar', 43.3438, 17.8078), ('Bihać', 44.8169, 15.8708), ('Bijeljina', 44.7570, 19.2144), ('Brčko', 44.8727, 18.8106),
           ('Doboj', 44.7349, 18.0843), ('Prijedor', 44.9799, 16.7133), ('Trebinje', 42.7119, 18.3437), ('Travnik', 44.2264, 17.6658),
           ('Neum', 42.9236, 17.6156), ('Livno', 43.8269, 17.0075), ('Goražde', 43.6679, 18.9759), ('Cazin', 44.9667, 15.9431)],
    'ME': [('Podgorica', 42.4304, 19.2594), ('Nikšić', 42.7731, 18.9445), ('Bar', 42.0931, 19.1003), ('Budva', 42.2911, 18.8403),
           ('Herceg Novi', 42.4531, 18.5375), ('Kotor', 42.4247, 18.7712), ('Tivat', 42.4350, 18.6961), ('Bijelo Polje', 43.0383, 19.7476),
           ('Pljevlja', 43.3567, 19.3584), ('Cetinje', 42.3906, 18.9142), ('Ulcinj', 41.9294, 19.2244), ('Žabljak', 43.1542, 19.1231)],
    'AL': [('Tirana', 41.3275, 19.8187), ('Durrës', 41.3231, 19.4414), ('Vlorë', 40.4661, 19.4914), ('Shkodër', 42.0683, 19.5126),
           ('Elbasan', 41.1125, 20.0822), ('Fier', 40.7239, 19.5561), ('Korçë', 40.6186, 20.7808), ('Berat', 40.7058, 19.9522),
           ('Sarandë', 39.8756, 20.0053), ('Lushnjë', 40.9419, 19.7050), ('Kukës', 42.0769, 20.4219), ('Gjirokastër', 40.0758, 20.1389)],
    'XK': [('Prishtinë', 42.6629, 21.1655), ('Prizren', 42.2139, 20.7397), ('Pejë', 42.6593, 20.2887), ('Gjakovë', 42.3803, 20.4308),
           ('Ferizaj', 42.3702, 21.1553), ('Gjilan', 42.4635, 21.4694), ('Mitrovicë', 42.8914, 20.8660), ('Podujevë', 42.9106, 21.1932)],
}

# OSM socket keys -> (type, current)
SOCKET = {'type2': ('type2', 'ac'), 'type2_cable': ('type2', 'ac'), 'type2_combo': ('ccs2', 'dc'), 'chademo': ('chademo', 'dc'),
          'tesla_supercharger': ('tesla', 'dc'), 'tesla_supercharger_ccs': ('ccs2', 'dc'), 'tesla_destination': ('type2', 'ac'),
          'schuko': ('schuko', 'ac'), 'typee': ('schuko', 'ac'), 'cee_blue': ('cee', 'ac'), 'cee_red_16a': ('cee', 'ac'),
          'cee_red_32a': ('cee', 'ac'), 'cee_red_63a': ('cee', 'ac'), 'type1': ('type1', 'ac'), 'type1_combo': ('ccs1', 'dc'),
          'gb_dc': ('gbt', 'dc'), 'gb_ac': ('gbt', 'ac'), 'type3c': ('other', 'ac')}
# OCM ConnectionTypeID -> type (current comes from CurrentTypeID)
OCM_CONN = {33: 'ccs2', 25: 'type2', 1036: 'type2', 2: 'chademo', 30: 'tesla', 27: 'tesla', 28: 'schuko', 1040: 'gbt',
            17: 'cee', 16: 'cee', 32: 'ccs1', 1: 'type1', 0: 'other'}
OCM_SKIP_STATUS = {150, 200, 210}          # planned, removed, removed duplicate
OCM_PRIVATE_USAGE = {2}                    # private, restricted access
OCM_CUSTOMERS_USAGE = {6}                  # for staff, visitors or customers
OSM_PRIVATE = {'private', 'no'}


def fold(s):
    s = (s or '').lower().replace('đ', 'd')
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


def dist_m(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a['latitude'], a['longitude'], b['latitude'], b['longitude']))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371000 * 2 * math.asin(math.sqrt(h))


def kw(txt):
    """'22 kW', '50', '11kW;22 kW', '3.7 kW' -> the biggest number in kW (None when there is none)."""
    if txt is None:
        return None
    vals = []
    for m in re.finditer(r'(\d+(?:[.,]\d+)?)\s*(kw|w)?', str(txt).lower()):
        v = float(m.group(1).replace(',', '.'))
        if m.group(2) == 'w' and v > 1000:
            v /= 1000
        vals.append(v)
    vals = [v for v in vals if 0 < v <= 1000]
    return max(vals) if vals else None


def network(cc, name, *texts):
    """The network named in the station's own name wins over the operator field: Open Charge Map lists the Qelo sites
    of StopShop parks under the operator "Kaufland eCharge" or "Electrip" (28.09.2026)."""
    for t in (fold(name or ''), fold(' '.join(x for x in texts if x))):
        for slug, pat in NETS.get(cc, []):
            if t and re.search(pat, t):
                return slug
    return ''


def near_town(cc, lat, lon):
    best, dbest = None, 1e9
    for name, la, lo in TOWNS[cc]:
        d = math.hypot(la - lat, (lo - lon) * math.cos(math.radians(lat))) * 111
        if d < dbest:
            best, dbest = name, d
    return best, dbest


# ------------------------------------------------------------------ OpenStreetMap
def osm_records(cc, j):
    out = []
    for e in j.get('elements', []):
        t = e.get('tags') or {}
        lat = e.get('lat') if 'lat' in e else (e.get('center') or {}).get('lat')
        lon = e.get('lon') if 'lon' in e else (e.get('center') or {}).get('lon')
        if lat is None or lon is None:
            continue
        # chargers for bicycles, scooters and motorcycles only
        if t.get('motorcar') == 'no' or (t.get('bicycle') in ('yes', 'designated') and t.get('motorcar') not in ('yes', 'designated')):
            continue
        # not open yet or no longer in use
        if t.get('construction') in ('yes', 'charging_station') or t.get('disused') == 'yes' or re.search(BUILDING, fold(t.get('name') or '')):
            continue
        if t.get('access') in OSM_PRIVATE or t.get('operational_status') in ('closed', 'removed'):
            continue
        conns = []
        for k, v in t.items():
            m = re.fullmatch(r'socket:([a-z0-9_]+)', k)
            if not m or m.group(1) not in SOCKET:
                continue
            typ, cur = SOCKET[m.group(1)]
            try:
                n = int(re.match(r'\d+', v).group(0)) if re.match(r'\d+', v) else 1
            except (AttributeError, ValueError):
                n = 1
            if n <= 0:
                continue
            p = kw(t.get(k + ':output'))
            if typ == 'tesla' and not p:
                p = None
            conns.append({'type': typ, 'current': cur, 'powerKW': p, 'count': n})
        if not conns:
            p = kw(t.get('charging_station:output'))
            if p:
                conns.append({'type': 'other', 'current': 'dc' if p > 22.5 else 'ac', 'powerKW': p, 'count': int(t['capacity']) if str(t.get('capacity', '')).isdigit() else 1})
        street = ' '.join(x for x in (t.get('addr:street') or t.get('addr:place'), t.get('addr:housenumber')) if x)
        city = t.get('addr:city') or ''
        name = t.get('name') or t.get('name:hr') or t.get('name:sr-Latn') or t.get('name:en') or ''
        op = t.get('operator') or t.get('network') or t.get('brand') or ''
        typ = {'node': 'n', 'way': 'w', 'relation': 'r'}[e['type']]
        net = network(cc, name, t.get('operator'), t.get('network'), t.get('brand'))
        dest = net == 'tesla' and (re.search(r'destination', fold(' '.join((name, op)))) or (conns and not any(c['current'] == 'dc' for c in conns)))
        if dest:   # Tesla Destination: the host's AC chargers for guests, not Tesla's network (as for Open Charge Map below)
            net, op = '', 'Tesla Destination'
        out.append({
            'id': f'osm-{typ}{e["id"]}', 'name': name, 'address': ', '.join(x for x in (street, city) if x), 'city': city,
            'latitude': lat, 'longitude': lon, 'operatorName': op,
            '_net': net,
            'connectors': conns, 'access': 'customers' if dest or t.get('access') in ('customers', 'permissive', 'destination') else 'public',
            'fee': t.get('fee'), 'oh': t.get('opening_hours'),
            'url': f'https://www.openstreetmap.org/{e["type"]}/{e["id"]}', 'updated': (e.get('timestamp') or '')[:10] or None,
        })
    return out


# ------------------------------------------------------------------ Open Charge Map
def ocm_records(cc, pois, ref):
    ops = {o['ID']: o['Title'] for o in ref.get('Operators', [])}
    nc = {d['ID'] for d in ref.get('DataProviders', []) if re.search(r'noncommercial|non-commercial', (d.get('License') or '').replace(' ', '').lower().replace('attribution-', ''))}
    out = []
    for p in pois:
        if p.get('StatusTypeID') in OCM_SKIP_STATUS or p.get('UsageTypeID') in OCM_PRIVATE_USAGE or p.get('DataProviderID') in nc:
            continue
        a = p.get('AddressInfo') or {}
        if a.get('Latitude') is None:
            continue
        conns = []
        for c in p.get('Connections') or []:
            if c.get('StatusTypeID') in OCM_SKIP_STATUS:
                continue
            typ = OCM_CONN.get(c.get('ConnectionTypeID'), 'other')
            cur = 'dc' if c.get('CurrentTypeID') == 30 or typ in ('ccs2', 'chademo', 'ccs1') or (typ == 'gbt' and (c.get('PowerKW') or 0) > 30) else 'ac'
            if typ == 'tesla' and (c.get('PowerKW') or 0) > 22.5:
                cur = 'dc'
            conns.append({'type': typ, 'current': cur, 'powerKW': c.get('PowerKW'), 'count': c.get('Quantity') or 1})
        opname = ops.get(p.get('OperatorID')) or ''
        if opname.startswith('('):          # (Unknown Operator), (Business Owner at Location) …
            opname = ''
        name = a.get('Title') or ''
        if re.search(BUILDING, fold(name)):
            continue
        net = network(cc, name, opname)
        dest = net == 'tesla' and not any(c['current'] == 'dc' for c in conns)
        if dest:
            # Tesla Destination chargers (hotels, campsites): the host's Type 2 wall connectors for guests,
            # not chargers of Tesla's network
            net, opname = '', 'Tesla Destination'
            conns = [dict(c, type='type2') if c['type'] == 'tesla' else c for c in conns]
        upd = (p.get('DateLastStatusUpdate') or p.get('DateLastVerified') or p.get('DateCreated') or '')[:10] or None
        addr = a.get('AddressLine1') or ''
        town = a.get('Town') or ''
        if town and fold(town) not in fold(addr):
            addr = ', '.join(x for x in (addr, town) if x)
        out.append({
            'id': f'ocm-{p["ID"]}', 'name': name, 'address': addr, 'city': town, 'latitude': a['Latitude'], 'longitude': a['Longitude'],
            'operatorName': re.sub(r'\s*\((?:Tesla-only charging|including non-tesla)\)', '', opname), '_net': net,
            'connectors': conns, 'access': 'customers' if dest or p.get('UsageTypeID') in OCM_CUSTOMERS_USAGE else 'public',
            'status': p.get('StatusTypeID'), 'url': f'https://openchargemap.org/site/poi/details/{p["ID"]}', 'updated': upd,
            'provider': p.get('DataProviderID'),
        })
    return out


# ------------------------------------------------------------------ merging
def max_kw(r):
    vals = [c['powerKW'] for c in r.get('connectors', []) if c.get('powerKW')]
    return max(vals) if vals else None


def names_match(a, b):
    na, nb = (re.sub(r'[\s\-_.]+', '', fold(x.get('name'))) for x in (a, b))   # "StopShop" = "Stop Shop"
    return not na or not nb or na == nb or na in nb or nb in na


def dedupe(recs):
    out = []
    for r in recs:
        dup = None
        for o in out:
            d = dist_m(o, r)
            same_named = fold(o.get('name')) != '' and fold(o.get('name')) == fold(r.get('name')) and o.get('_net') == r.get('_net')
            if d > (DUP_NET_M if same_named and o.get('_net') else SAME_SRC_M):
                continue
            if o.get('_net') and r.get('_net') and o['_net'] != r['_net']:
                continue
            x, y = max_kw(o), max_kw(r)
            if names_match(o, r) and (x is None or y is None or abs(x - y) < 1 or same_named):
                dup = o
                break
        if dup is None:
            out.append(dict(r, _also=[]))
            continue
        dup['_also'].append(r['id'])
        for k in ('name', 'address', 'city', 'operatorName', 'fee', 'oh'):
            if not dup.get(k) and r.get(k):
                dup[k] = r[k]
        if r.get('_net') and not dup.get('_net'):
            dup['_net'] = r['_net']
        # one node per charger in OSM: add up the sockets of the nodes of one site
        if r['id'].startswith('osm-') and dup['id'].startswith('osm-') and r.get('connectors'):
            dup['connectors'] = sum_conns(dup.get('connectors') or [], r['connectors'])
        elif len(r.get('connectors') or []) > len(dup.get('connectors') or []):
            dup['connectors'] = r['connectors']
        if (r.get('updated') or '') > (dup.get('updated') or ''):
            dup['updated'] = r['updated']
    return out


def sum_conns(a, b):
    out = {(c['type'], c['current'], c.get('powerKW')): dict(c) for c in a}
    for c in b:
        k = (c['type'], c['current'], c.get('powerKW'))
        if k in out:
            out[k]['count'] = (out[k].get('count') or 1) + (c.get('count') or 1)
        else:
            out[k] = dict(c)
    return list(out.values())


def same_place(o, s):
    d = dist_m(o, s)
    if o.get('_net') and o.get('_net') == s.get('_net'):
        return d <= DUP_NET_M
    same_name = fold(o.get('name')) != '' and fold(o.get('name')) == fold(s.get('name'))
    if d > (100 if same_name else DUP_M):
        return False
    if o.get('_net') and s.get('_net'):
        return False
    x, y = max_kw(o), max_kw(s)
    if x is not None and y is not None:
        return abs(x - y) < 1 or same_name
    return d <= 30 or (bool(fold(o.get('name'))) and names_match(o, s))


def merge(ocm, osm):
    ocm, osm = dedupe(ocm), dedupe(osm)
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
    return [(o, pairs.get(o['id'])) for o in ocm] + alone


# Serbian Cyrillic in the open data (addr:city = Беране) is shown in Latin on the Latin-script local pages
CYR = dict(zip('АБВГДЂЕЖЗИЈКЛМНОПРСТЋУФХЦЧШабвгдђежзијклмнопрстћуфхцчш',
               ['A', 'B', 'V', 'G', 'D', 'Đ', 'E', 'Ž', 'Z', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'R', 'S', 'T', 'Ć', 'U', 'F', 'H', 'C', 'Č', 'Š',
                'a', 'b', 'v', 'g', 'd', 'đ', 'e', 'ž', 'z', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'r', 's', 't', 'ć', 'u', 'f', 'h', 'c', 'č', 'š']))
CYR.update({'Љ': 'Lj', 'Њ': 'Nj', 'Џ': 'Dž', 'љ': 'lj', 'њ': 'nj', 'џ': 'dž'})
LATIN_CC = ('HR', 'BA', 'ME')
COUNTRY_WORDS = {'montenegro', 'crna gora', 'bosnia and herzegovina', 'bosnia & herzegovina', 'bosna i hercegovina', 'bih',
                 'croatia', 'hrvatska', 'republika hrvatska', 'republic of croatia'}


def latin(cc, t):
    if not t or cc not in LATIN_CC or not re.search('[\u0400-\u04FF]', t):
        return t
    return ''.join(CYR.get(ch, ch) for ch in t)


def clean_addr(cc, a):
    """Latin script, and no country name at the end of an address ("…, 81000, Montenegro, Podgorica")."""
    parts = [x.strip() for x in latin(cc, a or '').split(',')]
    return ', '.join(x for x in parts if x and fold(x) not in COUNTRY_WORDS)


BUILDING = r'under construction|u izgradnji|\bu gradnji\b|coming soon|\bplanned\b|planirano'
GENERIC_NAME = r'(?i)(charging station|punionica|punjač|punjac|elektri[cč]na punionica|ev charger|charger|e-?punionica|polnilnica|stacion karikimi)'


def station(cc, o, s, when):
    recs = [x for x in (o, s) if x]
    osm_name = s.get('name') if s else ''
    name = osm_name if osm_name and not re.fullmatch(GENERIC_NAME, osm_name.strip()) else (o.get('name') if o else '')
    if name and re.fullmatch(GENERIC_NAME, name.strip()):
        name = ''
    addr = (s.get('address') if s and s.get('address') and re.search(r'\d', s.get('address')) else '') or (o.get('address') if o else '') or (s.get('address') if s else '')
    conns = (o.get('connectors') if o and o.get('connectors') else None) or (s.get('connectors') if s else []) or []
    nets = [x.get('_net') for x in recs if x.get('_net')]
    net = nets[0] if nets else ''
    opn = next((x.get('operatorName') for x in recs if x.get('operatorName')), '')
    base = s if s else o
    city = next((x.get('city') for x in recs if x.get('city') and re.search(r'[^\W\d_]{2}', x.get('city'))
                 and not re.search(r'(?i)county|županij|zupanij|kanton|municipality|opština|opstina|općina|region|qark', x.get('city'))), '')
    town, km = near_town(cc, base['latitude'], base['longitude'])
    dc = [c for c in conns if c.get('current') == 'dc']
    ac = [c for c in conns if c.get('current') != 'dc']
    kdc = max([c['powerKW'] for c in dc if c.get('powerKW')] or [0]) or None
    kac = max([c['powerKW'] for c in ac if c.get('powerKW')] or [0]) or None
    if dc and not kdc:
        kdc = 50.0 if any(c['type'] in ('ccs2', 'chademo') for c in dc) else None
    st = {
        'id': (o or s)['id'],
        'n': latin(cc, (name or '').strip()),
        'a': clean_addr(cc, addr).strip(' ,'),
        't': latin(cc, city) or (town if km < 25 else ''),
        'lat': round(base['latitude'], 5),
        'lon': round(base['longitude'], 5),
        'net': net,
        'opn': opn if not net else '',
        'c': [[c.get('type') or 'other', c.get('current') or 'ac', c.get('powerKW'), c.get('count') or 1] for c in conns],
        'dc': kdc,
        'ac': kac,
        'acc': 'customers' if any(x.get('access') == 'customers' for x in recs) else 'public',
        'src': [{'d': 'ocm' if x is o else 'osm', 'u': x.get('url'), 'upd': fmt_date(x.get('updated'))} for x in recs],
        'v': {'s': 'src', 'd': when},
    }
    fee = next((x.get('fee') for x in recs if x.get('fee')), None)
    if fee == 'no':
        st['fee_osm'] = 'no'
    oh = next((x.get('oh') for x in recs if x.get('oh')), None)
    if oh:
        st['oh_osm'] = oh
    if o and o.get('status') in (30, 100):
        st['ocm_status'] = o['status']
    return st


def fmt_date(iso):
    if not iso or len(iso) < 10:
        return None
    return f'{iso[8:10]}.{iso[5:7]}.{iso[:4]}'


def fetch(cc):
    d = CACHE / cc
    d.mkdir(parents=True, exist_ok=True)
    for name in ('osm.json', 'ocm.json'):
        with urllib.request.urlopen(RAW + f'{cc}/{name}', timeout=120) as r:
            (d / name).write_bytes(r.read())
    for name in ('referencedata.json', 'meta.json'):
        with urllib.request.urlopen(RAW + name, timeout=120) as r:
            (CACHE / name).write_bytes(r.read())


def build(cc):
    meta = json.loads((CACHE / 'meta.json').read_text(encoding='utf-8'))
    ref = json.loads((CACHE / 'referencedata.json').read_text(encoding='utf-8'))
    osm_j = json.loads((CACHE / cc / 'osm.json').read_text(encoding='utf-8'))
    ocm_j = json.loads((CACHE / cc / 'ocm.json').read_text(encoding='utf-8'))
    cm = meta['countries'][cc]
    osm_base = (cm['osm'].get('timestamp_osm_base') or '')[:10]
    when = fmt_date((cm['osm'].get('fetched') or meta.get('finished') or '')[:10])
    osm, ocm = osm_records(cc, osm_j), ocm_records(cc, ocm_j, ref)
    pairs = merge(ocm, osm)
    stations = [station(cc, o, s, when) for o, s in pairs]
    stations.sort(key=lambda x: (fold(x['t']), fold(x['n']), x['id']))
    out = {
        'about': f'Public EV chargers in {cc}: OpenStreetMap and Open Charge Map merged by BlokVolt (scripts/region_map.py). '
                 'Not checked one by one.',
        'license': 'ODbL 1.0 (https://opendatacommons.org/licenses/odbl/1-0/)',
        'attribution': '© OpenStreetMap contributors (ODbL 1.0); Open Charge Map (CC BY 4.0, per data provider)',
        'retrieved': when, 'osm_base': fmt_date(osm_base), 'ocm_export': fmt_date((meta.get('ocm_export') or {}).get('date', '')[:10]),
        'counts': {'osm_records': len(osm), 'ocm_records': len(ocm), 'stations': len(stations)},
        'stations': stations,
    }
    dest = LOCAL / cc.lower()
    dest.mkdir(parents=True, exist_ok=True)
    (dest / 'stanice.json').write_text(json.dumps(out, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    by_net = {}
    for s in stations:
        by_net[s['net'] or '-'] = by_net.get(s['net'] or '-', 0) + 1
    fast = sum(1 for s in stations if (s['dc'] or 0) >= 50)
    print(f'{cc}: {len(stations)} stations (OSM {len(osm)}, OCM {len(ocm)}; DC ≥ 50 kW {fast}); networks {dict(sorted(by_net.items(), key=lambda x: -x[1]))}')
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    countries = [a.upper() for a in args] or COUNTRIES
    if '--fetch' in sys.argv:
        for cc in countries:
            fetch(cc)
    for cc in countries:
        build(cc)


if __name__ == '__main__':
    main()
