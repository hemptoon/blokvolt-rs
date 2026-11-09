import csv, sys, re, unicodedata
sys.path.insert(0, '/home/claude/blokvolt-rs/scripts')
from world_pages import slugify
SRC = '/home/claude/blokvolt-rs/content/world/names/countries.csv'
NAME_FIX = {'HK': ('Hong Kong', 'CLDR : « R.A.S. chinoise de Hong Kong » — forme courte usuelle'),
            'MO': ('Macao', 'CLDR : « R.A.S. chinoise de Macao » — forme courte usuelle'),
            'MM': ('Myanmar', 'CLDR : « Myanmar (Birmanie) » — forme courte'),
            'VC': ('Saint-Vincent-et-les-Grenadines', 'trait d’union officiel (CLDR sans trait)')}
SPECIAL = {
    'AE': 'aux Émirats arabes unis', 'NL': 'aux Pays-Bas', 'US': 'aux États-Unis', 'PH': 'aux Philippines',
    'AX': 'aux îles Åland', 'FO': 'aux îles Féroé', 'KY': 'aux îles Caïmans', 'FJ': 'aux Fidji', 'TO': 'aux Tonga',
    'WS': 'aux Samoa', 'PS': 'dans les Territoires palestiniens', 'IM': 'sur l’île de Man',
    'SJ': 'au Svalbard et à Jan Mayen', 'RE': 'à La Réunion', 'BB': 'à la Barbade', 'MU': 'à Maurice',
    'IL': 'en Israël', 'OM': 'à Oman', 'BH': 'à Bahreïn', 'AD': 'en Andorre', 'HT': 'en Haïti',
    'SV': 'au Salvador', 'TT': 'à Trinité-et-Tobago', 'VC': 'à Saint-Vincent-et-les-Grenadines',
}
A = {'AW', 'CU', 'CY', 'GG', 'GI', 'HK', 'JE', 'LC', 'MC', 'MF', 'MO', 'MT', 'SG', 'SM', 'TW', 'PR'}
MASC_E = {'MX', 'KH', 'BZ', 'SR'}  # le Mexique, le Cambodge, le Belize
VOW = 'AEIOUYÉÈÊÎÏÔÖÛÜH'
rows = []
for x in csv.DictReader(open(SRC)):
    cc = x['cc']
    name, note = NAME_FIX.get(cc, (x['name_fr'], ''))
    if cc in SPECIAL:
        ip = SPECIAL[cc]
    elif cc in A:
        ip = 'à ' + name
    else:
        fem = name.split()[0].endswith('e') and cc not in MASC_E
        if fem or name[0].upper() in VOW:
            ip = 'en ' + name
        else:
            ip = 'au ' + name
    rows.append([cc, name, slugify(name), ip, note])
slugs = [r[2] for r in rows]
assert len(set(slugs)) == len(slugs), 'dup slugs'
with open('/home/claude/work/out/countries.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['cc', 'name', 'slug', 'in_phrase', 'note']); w.writerows(rows)
for r in rows: print(r[0], r[2], '|', r[3])
