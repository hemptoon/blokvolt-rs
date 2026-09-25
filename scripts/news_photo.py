# -*- coding: utf-8 -*-
"""News photos: one capture in, the site's sizes out.

    python3 scripts/news_photo.py <capture.png|jpg> <name> [<capture> <name> ...]

Writes static/assets/img/<name>-{480,800,1200}.webp (16:9, what the templates use) and
static/assets/og/foto/<name>.jpg (1200x630, og:image and the RSS enclosure).

The capture is a `zoom` screenshot of the photo shown at 1200x675 CSS px in the owner's Chrome
(about 1455x818 px; see docs/RUNBOOK.md 3.19). It is cropped to 16:9 around the centre, resized
with Lanczos and saved as WebP q80 and JPEG q82. The name must also be in content/data/foto.json
(author, licence, caption), or the build stops."""
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / 'static' / 'assets' / 'img'
OG = ROOT / 'static' / 'assets' / 'og' / 'foto'


def crop_ratio(im, rw, rh):
    w, h = im.size
    if w * rh > h * rw:                      # too wide: trim the sides
        nw = round(h * rw / rh)
        x = (w - nw) // 2
        return im.crop((x, 0, x + nw, h))
    nh = round(w * rh / rw)                  # too tall: trim top and bottom
    y = (h - nh) // 2
    return im.crop((0, y, w, y + nh))


def make(src, name):
    im = Image.open(src).convert('RGB')
    if im.width < 1200:
        sys.exit(f'{src}: {im.width} px wide, need at least 1200')
    wide = crop_ratio(im, 16, 9)
    for w in (480, 800, 1200):
        out = wide.resize((w, round(w * 9 / 16)), Image.LANCZOS)
        out.save(IMG / f'{name}-{w}.webp', 'WEBP', quality=80, method=6)
    OG.mkdir(parents=True, exist_ok=True)
    og = crop_ratio(wide, 1200, 630).resize((1200, 630), Image.LANCZOS)
    og.save(OG / f'{name}.jpg', 'JPEG', quality=82, optimize=True, progressive=True)
    sizes = [(IMG / f'{name}-{w}.webp').stat().st_size // 1024 for w in (480, 800, 1200)]
    print(f'{name}: webp {sizes} KB, og {(OG / f"{name}.jpg").stat().st_size // 1024} KB')


if __name__ == '__main__':
    args = sys.argv[1:]
    if not args or len(args) % 2:
        sys.exit(__doc__)
    for i in range(0, len(args), 2):
        make(args[i], args[i + 1])
