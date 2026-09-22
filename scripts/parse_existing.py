# -*- coding: utf-8 -*-
"""Parse the 20 firms from the existing comparison page into content/firme/*.json (cells kept as HTML)."""
import json, re, os, unicodedata
from bs4 import BeautifulSoup
h = open('content/vodici/cena-punjaca-za-elektricni-auto.html', encoding='utf-8').read()
s = BeautifulSoup(h, 'html.parser')
groups = ['A', 'B', 'C', 'D']
def slugify(t):
    t = unicodedata.normalize('NFKD', t).encode('ascii', 'ignore').decode()
    t = re.sub(r'[^a-zA-Z0-9]+', '-', t).strip('-').lower()
    return t
labels = ['firma', 'cena', 'ugradnja', 'brojilo', 'skupstina', 'usluga']
out = []
for gi, tbl in enumerate(s.select('table.bva-tbl')):
    for tr in tbl.select('tbody tr'):
        tds = tr.find_all('td')
        firm = tds[0]
        name = firm.find('b').get_text(strip=True)
        is_us = 'is-us' in (tr.get('class') or [])
        smalls = firm.find_all('small')
        site_small = smalls[0]
        a = site_small.find('a')
        website = a['href'] if a else ''
        domain = a.get_text(strip=True) if a else ''
        loc = site_small.get_text(' ', strip=True)
        city = loc.split('·')[-1].strip() if '·' in loc else ''
        of = ''
        for sm in smalls:
            if 'of' in (sm.get('class') or []):
                of = sm.decode_contents()
        cells = {}
        for lab, td in zip(labels[1:], tds[1:]):
            cells[lab] = td.decode_contents()
        verdicts = {}
        for lab, td in zip(labels[2:], tds[2:]):
            v = td.find('b', class_='v')
            verdicts[lab] = v.get_text(strip=True) if v else ''
        pr = tds[1].find('b', class_='pr')
        rec = {
            'slug': 'evolako' if is_us else slugify(name.split('(')[0]),
            'name': name, 'group': groups[gi], 'publish': True, 'is_us': is_us,
            'website': website, 'domain': domain, 'city': city, 'coverage': '',
            'offer': of, 'price_headline': pr.get_text(' ', strip=True) if pr else '',
            'cells': cells, 'verdicts': verdicts,
            'contact': {}, 'sources': [], 'verified': '07.09.2026', 'confidence': 'visoko', 'notes': ''
        }
        out.append(rec)
os.makedirs('content/firme', exist_ok=True)
for r in out:
    with open(f"content/firme/{r['slug']}.json", 'w', encoding='utf-8') as f:
        json.dump(r, f, ensure_ascii=False, indent=1)
print(len(out), [r['slug'] for r in out])
print(json.dumps(out[2], ensure_ascii=False, indent=1)[:2500])
