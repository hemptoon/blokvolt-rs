#!/usr/bin/env python3
"""Photos of the media kit page (/za-firme/oglasavanje/, templates/oglasavanje.html; docs/RUNBOOK.md 3.26).

The originals (PNG, 2048 x 1360 and one 2688 x 1152, generated in Higgsfield on 29.09.2026) are kept on the side branch
media-raw-2026-09, folder media-raw/ — not served. This script makes the web copies in static/assets/img/:
WebP in several widths, the sample ad as a 3:1 banner (1200 x 400, the real ad size) and the page's og:image
(static/assets/og/oglasavanje.jpg, drawn with Playwright).

Files under /assets/ are cached for a year: never overwrite a published image, give a changed one a new name.

Usage:  git fetch origin media-raw-2026-09 && python3 scripts/medija_kit_img.py
        python3 scripts/medija_kit_img.py --src <folder with the PNGs>
"""
import argparse
import io
import subprocess
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'static' / 'assets' / 'img'
BRANCH = 'origin/media-raw-2026-09'

# source PNG -> (web name, widths)
JOBS = {
    'mk-hero-tesla-vojvodina.png': ('oglasavanje-hero', (800, 1200, 1600, 2048)),
    'mk-publika-par-u-autu.png': ('oglasavanje-publika', (480, 800, 1200)),
    'mk-vlasnistvo-predaja-kljuceva.png': ('oglasavanje-vlasnistvo', (480, 800, 1200)),
    'mk-na-putu-zlatibor.png': ('oglasavanje-na-putu', (480, 800, 1200)),
    'mk-vesti-predstavljanje.png': ('oglasavanje-vesti', (480, 800, 1200)),
}
AD = ('mk-primer-oglasa-porodica.png', 'oglasavanje-primer', (600, 1200), 40)   # 3:1 crop from y = 40 px


def load(name, src):
    if src:
        return Image.open(Path(src) / name).convert('RGB')
    data = subprocess.run(['git', 'show', f'{BRANCH}:media-raw/{name}'], cwd=ROOT, capture_output=True, check=True).stdout
    return Image.open(io.BytesIO(data)).convert('RGB')


def save(im, name, widths, q=80):
    for w in widths:
        r = im if w == im.width else im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
        p = OUT / f'{name}-{w}.webp'
        r.save(p, 'WEBP', quality=q, method=6)
        print(f'{p.relative_to(ROOT)}  {r.width}x{r.height}  {p.stat().st_size // 1024} KB')


OG_HTML = """<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{font-family:Onest;font-weight:100 900;src:url(%(fonts)s/onest-latin-wght-normal.woff2) format('woff2');unicode-range:U+0000-00FF,U+2000-206F}
@font-face{font-family:Onest;font-weight:100 900;src:url(%(fonts)s/onest-latin-ext-wght-normal.woff2) format('woff2');unicode-range:U+0100-02BA,U+1E00-1E9F}
html,body{margin:0;width:1200px;height:630px;overflow:hidden;background:#0B0F17;font-family:Onest,sans-serif;color:#fff}
.ph{position:absolute;top:0;right:0;width:760px;height:630px;background:url(%(img)s) 60%% 50%%/cover;
 -webkit-mask-image:linear-gradient(90deg,transparent 0,#000 42%%);mask-image:linear-gradient(90deg,transparent 0,#000 42%%)}
.tx{position:absolute;left:72px;top:0;bottom:0;width:560px;display:flex;flex-direction:column;justify-content:center}
.logo{height:44px;margin:0 0 56px;align-self:flex-start}
.k{margin:0 0 16px;font-size:20px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:#D9F45B}
h1{margin:0 0 20px;font-size:68px;line-height:1.02;font-weight:760;letter-spacing:-.035em}
p{margin:0;font-size:25px;line-height:1.4;color:rgba(255,255,255,.78)}
</style></head><body><div class="ph"></div><div class="tx"><img class="logo" src="%(logo)s" alt="">
<p class="k">Medija kit</p><h1>Oglašavanje na BlokVoltu</h1><p>Vodič za vozače električnih automobila u Srbiji</p></div></body></html>"""


def og():
    """static/assets/og/oglasavanje.jpg (1200 x 630): the page's og:image, rendered from HTML with the site font."""
    from playwright.sync_api import sync_playwright
    html = OG_HTML % {'fonts': (ROOT / 'static' / 'assets' / 'fonts').as_uri(),
                      'img': (OUT / 'oglasavanje-hero-1600.webp').as_uri(),
                      'logo': (ROOT / 'static' / 'za-firme' / 'blokvolt-logo-beli.svg').as_uri()}
    tmp = OUT.parent / 'og' / '_og_tmp.html'
    tmp.write_text(html, encoding='utf-8')
    png = OUT.parent / 'og' / '_og_tmp.png'
    out = ROOT / 'static' / 'assets' / 'og' / 'oglasavanje.jpg'
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={'width': 1200, 'height': 630})
        pg.goto(tmp.as_uri(), wait_until='networkidle')
        pg.evaluate('document.fonts.ready')
        pg.screenshot(path=str(png))
        b.close()
    tmp.unlink()
    Image.open(png).convert('RGB').save(out, 'JPEG', quality=86, optimize=True, progressive=True)
    png.unlink()
    print(f'{out.relative_to(ROOT)}  {out.stat().st_size // 1024} KB')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--src', help='folder with the original PNGs (default: the branch media-raw-2026-09)')
    ap.add_argument('--og-only', action='store_true', help='only redraw the og:image from the existing WebP')
    a = ap.parse_args()
    if not a.og_only:
        for src, (name, widths) in JOBS.items():
            save(load(src, a.src), name, widths)
        src, name, widths, y0 = AD
        im = load(src, a.src)
        h = round(im.width / 3)
        save(im.crop((0, y0, im.width, y0 + h)), name, widths, q=82)
    og()


if __name__ == '__main__':
    sys.exit(main())
