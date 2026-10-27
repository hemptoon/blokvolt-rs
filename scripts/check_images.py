#!/usr/bin/env python3
"""check_images.py — no picture on the built site may be cut badly (RUNBOOK 3.5c, owner's rule 27.10.2026).

Runs after build.py on dist/. For every <img> that CSS shows with object-fit:cover in a fixed-ratio box,
it compares the box ratio with the picture's real ratio and reports how much of the picture is cut off.

  python3 scripts/check_images.py            # fails (exit 1) if any picture loses more than LIMIT
  python3 scripts/check_images.py --list     # every cropped picture, sorted by loss

Article and news photos (.art-fig, .sec-fig), guide thumbnails (.row .th) and the media-kit audience photo keep
their own ratio since 27.10.2026, so they are never cut and are not listed here.
Small thumbnails in lists may trim a thin edge; LIMIT keeps that edge thin. A machine cannot see faces:
whoever publishes a new picture still looks at it on the page (desktop and phone) before saying "done".
"""
import re, sys
from pathlib import Path
from bs4 import BeautifulSoup
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / 'dist'
LIMIT = 0.10  # at most 10 % of the picture may fall outside the box (5 % per side)

# selector -> box width/height, as set in static/assets/bv.css (keep in sync when the CSS changes)
RULES = [
    ('a.ncard > img', 16 / 9),            # news cards
    ('a.ni-img > img', 16 / 9),           # /vesti list
    ('a.tile.pic > img', 3 / 2),          # picture tiles
    ('.amc-ph > img.evm-i', 360 / 200),   # model cards on /elektricni-automobili
    ('.mk-card-img', 16 / 10),
]
_size = {}


def size(src):
    p = DIST / src.split('?')[0].lstrip('/')
    if not p.exists():
        p = ROOT / 'static' / src.split('?')[0].lstrip('/')
    if not p.exists():
        return None
    if p not in _size:
        with Image.open(p) as im:
            _size[p] = im.size
    return _size[p]


def main():
    show_all = '--list' in sys.argv
    seen, bad = {}, []
    for html in sorted(DIST.rglob('*.html')):
        soup = BeautifulSoup(html.read_text(encoding='utf-8'), 'html.parser')
        for sel, box in RULES:
            for img in soup.select(sel):
                src = img.get('src') or ''
                if not src or src.endswith('.svg'):
                    continue
                wh = size(src)
                if not wh:
                    continue
                nat = wh[0] / wh[1]
                lost = 1 - min(nat / box, box / nat)
                key = (src, sel)
                if key not in seen:
                    seen[key] = (lost, str(html.relative_to(DIST)))
    rows = sorted(((v[0], k[0], k[1], v[1]) for k, v in seen.items()), reverse=True)
    for lost, src, sel, page in rows:
        if lost > LIMIT:
            bad.append((lost, src, sel, page))
        if show_all and lost > 0.01:
            print(f'{lost:5.1%}  {sel:22s} {src}  (first on /{page})')
    for lost, src, sel, page in bad:
        print(f'CUT {lost:.0%} > {LIMIT:.0%}: {src} in {sel} (first on /{page}) — use a picture with the box ratio or change the box')
    print(f'check_images: {len(seen)} picture placements, {len(bad)} cut too much')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
