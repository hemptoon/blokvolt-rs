# -*- coding: utf-8 -*-
"""One-off (23.09.2026): add a curated `brands` list to every published firm.

Brands are taken only from what the firm's own site names (already copied into `offer`
and into content/data/wallbox-modeli.json). Service-only mentions ("servis ABB i Webasto")
and model names of unclear make are left out on purpose. Re-running is safe: it overwrites
`brands` with the list below and keeps every other key in place."""
import json, glob
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BRANDS = {
    'andreja': ['Growatt', 'Huawei', 'Victron'],
    'bp-echarge': ['KEBA'],
    'chargego': ['Charge&GO', 'Schneider Electric', 'Sungrow'],
    'conseko': ['Fronius'],
    'digital-hajdukovic': ['Digital'],
    'edrive': ['FMT', 'Teltonika'],
    'eko-term': ['Huawei'],
    'elektro-centar-nais': ['Schneider Electric'],
    'elektroleum': ['Schneider Electric'],
    'elektronapon': ['ABB'],
    'elmaks': ['Schneider Electric'],
    'emobility-d-o-o': ['Etrel', 'Iocharger', 'Wallbox'],
    'ep-solutions': ['Schneider Electric'],
    'ev-charging-solutions': ['Alfen', 'Exicom', 'Juice', 'Kempower', 'NRGkick', 'Wallbox', 'Zaptec'],
    'it-home': ['Teltonika'],
    'jakov-sistem': ['ABB', 'Telwin'],
    'mda-e-technology': ['Orbis'],
    'network-shop-bazzar': ['ABB', 'Union (Vestel)'],
    'obd2-evchargers': ['Autel'],
    'orion-emobility': ['ABB'],
    'pmp': ['ETEK'],
    'praktiker-elektrowebshop': ['Noark'],
    'provision': ['Circontrol', 'Teltonika'],
    'pupinenergy': ['PupinEnergy'],
    'qoltec': ['Qoltec'],
    'schrack-technik': ['Schrack'],
    'sirotin': ['Morek'],
    'smit': ['Circontrol'],
    'solar-energy-lazic': ['Wallbox'],
    'solarkraft': ['EcoFlow', 'PupinEnergy'],
    'sp-solar': ['Sungrow'],
    'spark-systems': ['Circontrol'],
    'stamteh': ['Wallbox'],
    'stasanet': ['Livoltek'],
    'tehnoducan': ['ABB'],
    'telefon-inzenjering': ['Alfen', 'Fronius', 'Sigenergy', 'SMA', 'Victron', 'Wallbox'],
    'union-electronics-avtera': ['Union (Vestel)'],
    'veming': ['Enelion'],
    'voltech': ['BENY', 'Voltech'],
    'webasto-srbija': ['Webasto'],
    'wise-smart-home': ['WISE'],
}

changed = 0
for p in sorted(glob.glob(str(ROOT / 'content' / 'firme' / '*.json'))):
    d = json.load(open(p, encoding='utf-8'))
    if not d.get('publish'):
        continue
    new = {}
    for k, v in d.items():
        if k == 'brands':
            continue
        new[k] = v
        if k == 'offer':
            new['brands'] = BRANDS.get(d['slug'], [])
    if new != d:
        Path(p).write_text(json.dumps(new, ensure_ascii=False, indent=1), encoding='utf-8')
        changed += 1
unknown = set(BRANDS) - {Path(p).stem for p in glob.glob(str(ROOT / 'content' / 'firme' / '*.json'))}
print('updated', changed, 'files; unknown slugs:', unknown or 'none')
