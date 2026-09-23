# -*- coding: utf-8 -*-
"""Open-data exports for /preuzimanje/.

Called from build.py with the already-loaded data, writes CSV (semicolon-separated,
UTF-8 with BOM so Serbian Excel opens it without an import wizard) into dist/preuzimanje/.
Every file carries the same columns the site shows, plus the source URL and the check date —
so a number can always be traced back to the page it was copied from."""
import csv, io


def _cell(v):
    """Serbian locale: comma as the decimal mark — which is why the delimiter is a semicolon."""
    if isinstance(v, float):
        return f'{v:.2f}'.rstrip('0').rstrip('.').replace('.', ',')
    return v


def _list(vals):
    return ' / '.join(str(_cell(float(x) if isinstance(x, float) else x)) for x in (vals or []))


def _write(dist, name, header, rows):
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=';', quoting=csv.QUOTE_MINIMAL, lineterminator='\r\n')
    w.writerow(header)
    w.writerows([[_cell(c) for c in r] for r in rows])
    p = dist / 'preuzimanje' / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text('﻿' + buf.getvalue(), encoding='utf-8')
    return {'name': name, 'rows': len(rows), 'bytes': p.stat().st_size}


def export_all(dist, site, published, operators, price_index, ev_data, wallbox, firms_checked):
    out = []

    # 1. firm register
    rows = []
    for f in published:
        v = f.get('verdicts', {})
        rows.append([f['name'], f.get('city', ''), f.get('coverage', ''), f['group'], f['group_label'],
                     f.get('kind_label', ''), f.get('price_headline', ''), v.get('ugradnja', ''),
                     v.get('brojilo', ''), v.get('skupstina', ''), v.get('usluga', ''),
                     f.get('website', ''), f['verified'], f.get('confidence', ''), site + f['url'],
                     ', '.join(f.get('brands', []))])
    out.append(_write(dist, 'blokvolt-firme.csv',
                      ['naziv', 'sediste', 'pokrivenost', 'grupa', 'grupa_opis', 'tip', 'javna_cena',
                       'ugradnja', 'brojilo', 'skupstina', 'usluga_i_garancija', 'sajt', 'provereno',
                       'pouzdanost', 'stranica_blokvolt', 'brendovi'], rows))

    # 2. EV models with a published price
    sub = ev_data.get('subsidy_eur', 5000)
    rows = []
    for b in ev_data['brands']:
        for m in b.get('models', []):
            if m.get('source_type') not in ('official', 'pricelist_pdf'):
                continue
            reg, promo = m.get('price_regular'), m.get('price_promo')
            if not reg and not promo:
                continue
            base = reg or promo
            if m.get('price_includes_subsidy') is True:
                base = (promo or reg) + sub
            elif promo and reg and promo < reg:
                base = promo if b['brand'] not in ('Ford', 'Toyota') else reg
            rows.append([b['brand'], m['model'], m.get('version', ''), base, base - sub,
                         reg or '', promo or '', 'da' if m.get('price_includes_subsidy') else 'ne',
                         m.get('vat', ''), m.get('source_type', ''), m.get('url', ''), ev_data['checked']])
    out.append(_write(dist, 'blokvolt-cene-elektricnih-automobila.csv',
                      ['marka', 'model', 'verzija', 'cena_od_eur', 'posle_subvencije_eur',
                       'redovna_eur', 'akcijska_eur', 'cena_sadrzi_subvenciju', 'pdv',
                       'tip_izvora', 'izvor_url', 'provereno'], rows))

    # 3. wallbox models
    rows = [[r['brand'], r['model'], r['kw'], r['price_rsd'], r['vat'], r['seller'],
             r.get('note', ''), r.get('stock', ''), r.get('url', ''), r.get('date', wallbox['checked'])]
            for r in wallbox['rows']]
    out.append(_write(dist, 'blokvolt-wallbox-modeli.csv',
                      ['marka', 'model', 'snaga_kw', 'cena_rsd', 'pdv', 'prodavac', 'napomena',
                       'zalihe', 'izvor_url', 'provereno'], rows))

    # 4. public charging price index
    rows = []
    for r in price_index['rows']:
        per_kwh = ''
        if r.get('kwh') and r.get('rsd_total'):
            per_kwh = round(r['rsd_total'] / r['kwh'], 2)
        rows.append([r.get('op_name', r.get('op', '')), r.get('where', ''), r.get('charger', ''),
                     r.get('label', ''), _list(r.get('rsd_min')),
                     r.get('rsd_hour', ''), r.get('unit_rsd', ''), r.get('rsd_total', ''),
                     r.get('kwh', ''), per_kwh, _list(r.get('assume_kw')),
                     r.get('date', ''), r.get('source', ''), r.get('conf', ''), r.get('url', '')])
    out.append(_write(dist, 'blokvolt-javno-punjenje-cene.csv',
                      ['mreza', 'lokacija', 'punjac', 'tarifa', 'rsd_po_minutu', 'rsd_po_satu',
                       'rsd_po_jedinici', 'racun_rsd', 'racun_kwh', 'rsd_po_kwh_racun',
                       'pretpostavljena_snaga_kw', 'datum', 'izvor', 'pouzdanost', 'izvor_url'], rows))

    # 5. charging networks
    rows = [[o.get('legal', o['name']), o.get('kind_label', ''), o.get('coverage', ''), o.get('network', ''),
             o.get('payment', ''), o.get('card', ''), o.get('roaming', ''), o.get('support', ''),
             o.get('website', ''), o['verified']] for o in operators]
    out.append(_write(dist, 'blokvolt-mreze-javnog-punjenja.csv',
                      ['mreza', 'tip', 'pokrivenost', 'velicina_mreze', 'placanje', 'kartica',
                       'roming', 'podrska', 'sajt', 'provereno'], rows))
    return out
