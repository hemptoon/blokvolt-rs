# Normalises collected logos: trims the flat background, fits into 360x160, writes PNG to static/assets/logos.
# Raw inputs live outside the repo (RAW: files from the logos-raw-2026-09 branch, SHOTS: cropped screenshots); see RUNBOOK.
import json
from pathlib import Path
from PIL import Image, ImageChops

RAW = Path('/tmp/claude-0/logos/raw/logos-raw')
SHOTS = Path('/tmp/claude-0/logos/raw/shots')
OUT = Path('/home/claude/agregator/blokvolt-rs/static/assets/logos')
PICKS = json.load(open('/tmp/claude-0/logos/picks.json'))

CHOICE = {  # slug: (source, dark tile)
 'andreja': ('andreja', 0), 'bp-echarge': ('bp-echarge', 0), 'chargego': ('chargego__3', 0), 'conseko': ('conseko', 0),
 'digital-hajdukovic': ('shot:digital-hajdukovic', 0), 'edrive': ('edrive', 1), 'eko-term': ('eko-term', 0),
 'elektricar-nis': ('elektricar-nis', 0), 'elektricni-automobili-d-o-o': ('elektricni-automobili-d-o-o', 0),
 'elektro-centar-nais': ('elektro-centar-nais', 0), 'elektroleum': ('shot:elektroleum', 1), 'elektromil': ('elektromil', 0),
 'elektronapon': ('elektronapon', 0), 'elmaks': ('elmaks', 0), 'elmik-inzenjering': ('elmik-inzenjering', 0),
 'emobility-d-o-o': ('emobility-d-o-o', 0), 'energy-net': ('energy-net', 0), 'ep-solutions': ('ep-solutions', 0),
 'ev-charging-solutions': ('ev-charging-solutions', 0), 'evolako': ('evolako', 0), 'handyman': ('handyman', 0),  # evolako: a full blue square, not trimmed
 'it-home': ('it-home', 0), 'jakov-sistem': ('jakov-sistem', 0), 'kibost-car': ('kibost-car__2', 0),
 'mda-e-technology': ('mda-e-technology', 0), 'network-shop-bazzar': ('network-shop-bazzar', 1),
 'obd2-evchargers': ('obd2-evchargers__2', 0), 'orion-emobility': ('orion-emobility__2', 1), 'pmp': ('pmp', 0),
 'praktiker-elektrowebshop': ('praktiker-elektrowebshop', 0), 'provision': ('provision', 0), 'pupinenergy': ('pupinenergy', 0),
 'qoltec': ('qoltec', 0), 'schrack-technik': ('shot:schrack-technik', 0), 'sirotin': ('shot:sirotin', 0), 'smit': ('smit', 0),
 'solar-energy-lazic': ('solar-energy-lazic', 0), 'solarkraft': ('solarkraft', 0), 'sp-solar': ('sp-solar', 1),
 'spark-systems': ('spark-systems', 0), 'stamteh': ('stamteh', 0), 'stasanet': ('stasanet', 0), 'tehnoducan': ('tehnoducan', 1),
 'telefon-inzenjering': ('telefon-inzenjering', 0), 'tesla-sistemi-energetika': ('tesla-sistemi-energetika', 0),
 'union-electronics-avtera': ('union-electronics-avtera', 0), 'veming': ('veming', 0), 'voltech': ('voltech', 0),
 'vulovic-electric': ('vulovic-electric', 0), 'webasto-srbija': ('webasto-srbija', 0), 'wise-smart-home': ('wise-smart-home__2', 0),
 # networks (op-<slug>); networks without an entry fall back to the firm with the same slug
 'op-chargego': ('op-chargego', 1), 'op-putevi-srbije': ('op-putevi-srbije', 0), 'op-tesla': ('shot:op-tesla', 0),
 'op-omv': ('op-omv', 0), 'op-nis-gazprom': ('op-nis-gazprom', 0), 'op-emobility-spectra': ('emobility-d-o-o', 0),
 'op-lidl-echarge': ('op-lidl-echarge', 0), 'op-parking-servis-beograd': ('shot:op-parking-servis-beograd', 0),
}
SRC_URL = {'digital-hajdukovic': 'https://digital.co.rs/fajlovi/logo/logo.png', 'elektroleum': 'https://elektroleum.rs/wp-content/uploads/logo-light.webp',
           'schrack-technik': 'https://www.schrack.rs/_assets/e3d6a9be731934855a3322e244edc0c7/Images/rwd/schrack-logo.png',
           'sirotin': 'https://sirotin.rs/logo.webp', 'op-parking-servis-beograd': 'https://www.parking-servis.co.rs/favicons/apple-touch-icon.png',
           'op-tesla': 'https://www.tesla.com/'}


def trim(im):
    im = im.convert('RGBA')
    a = im.split()[-1]
    if a.getextrema()[0] < 250:           # has transparency: trim by alpha
        box = a.point(lambda v: 255 if v > 12 else 0).getbbox()
    else:                                 # flat background: trim by the corner colour
        bg = Image.new('RGBA', im.size, im.getpixel((1, 1)))
        diff = ImageChops.difference(im, bg).convert('L').point(lambda v: 255 if v > 24 else 0)
        box = diff.getbbox()
    if not box:
        return im
    pad = max(2, int(max(box[2] - box[0], box[3] - box[1]) * 0.03))
    box = (max(0, box[0] - pad), max(0, box[1] - pad), min(im.width, box[2] + pad), min(im.height, box[3] + pad))
    return im.crop(box)


meta = {}
for slug, (src, dark) in CHOICE.items():
    p = SHOTS / (src[5:] + '.png') if src.startswith('shot:') else RAW / (src + '.png')
    im = Image.open(p).convert('RGBA') if slug in ('evolako',) else trim(Image.open(p))
    im.thumbnail((360, 160), Image.LANCZOS)
    out = OUT / f'{slug}.png'
    if im.mode == 'RGBA' and im.split()[-1].getextrema()[0] >= 250:
        im = im.convert('RGB')
    q = im.quantize(colors=256, method=Image.Quantize.FASTOCTREE if im.mode == 'RGBA' else Image.Quantize.MEDIANCUT)
    q.save(out, optimize=True)
    key = src[5:] if src.startswith('shot:') else src
    meta[slug] = {'file': f'{slug}.png', 'dark': bool(dark), 'source': SRC_URL.get(key) or PICKS.get(key, '')}
    print(f'{slug:30} {im.size} {out.stat().st_size // 1024} KB {"dark" if dark else ""}')
json.dump({'note': 'Logos of companies and networks, from their own websites (source), trimmed and resized by scripts/logos.py (raw files: branch logos-raw-2026-09 and screenshots, see RUNBOOK). Shown only to identify the company; removed on request. dark = shown on a dark tile.', 'logos': meta},
          open('/home/claude/agregator/blokvolt-rs/content/data/logos.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(meta))
