"""POLISH (12.11.2026): the charger lights inside the word "volt" at the bottom of the world footer (templates/com2/_wfooter.html).

Made from the dark Europe picture of the home (static/com/hero/hero-eu-w.webp, scripts/world_hero.py — the public layer of
the world map): only the single lights are kept (a high-pass takes the dense blur of the big cities away, so the letters stay
readable), with a small glow, as a grey-scale WebP. The footer CSS lays it with background-blend-mode: screen over the lime
gradient of the letters, so the light points shine white on lime. ≤ 40 KB; the page loads it only when the footer comes
near (static/com/bvc.js), without it the letters are solid lime.

    python3 scripts/world_footer_lights.py            → static/com/ft-lights.webp (prints its size)
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'static' / 'com' / 'hero' / 'hero-eu-w.webp'
OUT = ROOT / 'static' / 'com' / 'ft-lights.webp'
LIMIT = 40 * 1024


def make(src=SRC, out=OUT):
    a = np.asarray(Image.open(src).convert('RGB')).astype(float) / 255
    lum = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
    lights = np.clip((lum - 0.10) / 0.70, 0, 1)[360:840, 700:1920]       # a band through central Europe
    blur = np.asarray(Image.fromarray((lights * 255).astype('uint8'), 'L').filter(ImageFilter.GaussianBlur(6))).astype(float) / 255
    points = np.clip(np.clip(lights - blur * 0.9, 0, 1) * 2.2, 0, 1) ** 1.2
    img = Image.fromarray((points * 255).astype('uint8'), 'L').resize((1100, 432), Image.LANCZOS)
    p = np.asarray(img).copy()
    p[p < 55] = 0
    img = Image.fromarray(p)
    glow = np.asarray(img.filter(ImageFilter.GaussianBlur(2.0))).astype(float)
    p = np.clip(np.asarray(img).astype(float) * 0.9 + glow * 1.5, 0, 255)
    p[p < 16] = 0
    img = Image.fromarray(p.astype('uint8')).resize((900, 354), Image.LANCZOS)
    img.save(out, quality=38, method=6)
    n = out.stat().st_size
    if n > LIMIT:
        raise SystemExit(f'world_footer_lights: {n} bytes > {LIMIT}')
    print(f'world_footer_lights: {out.relative_to(ROOT)} {img.size[0]}×{img.size[1]}, {n // 1024} KB')
    return n


if __name__ == '__main__':
    sys.exit(0 if make() else 1)
