# -*- coding: utf-8 -*-
"""App icons for the web app manifest and the Android app (docs/RUNBOOK.md 3.20).

    python3 scripts/app_icons.py

Writes static/assets/app/: icon-192.png and icon-512.png (the favicon: bolt on a dark rounded square),
icon-maskable-512.png (full-bleed, bolt inside the 80 % safe zone), icon-monochrome-512.png (bolt only,
for Android themed icons and notifications) and the shortcut icons sc-<name>-192.png (the site's line
icons on a volt circle, drawn by Chromium from templates/_icons.html paths)."""
import asyncio
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'static' / 'assets' / 'app'
INK, VOLT = (11, 15, 23, 255), (217, 244, 91, 255)            # #0B0F17, #D9F45B (favicon.svg)
BOLT = [(27, 10), (14, 36), (26, 36), (22, 54), (42, 26), (30, 26), (34, 10)]   # favicon.svg path, 64x64 grid
SS = 4                                                          # supersampling for smooth edges


def bolt(draw, scale, dx, dy, fill):
    draw.polygon([(x * scale + dx, y * scale + dy) for x, y in BOLT], fill=fill)


def rounded(size):
    big = size * SS
    im = Image.new('RGBA', (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, big - 1, big - 1), radius=big * 16 // 64, fill=INK)
    bolt(d, big / 64, 0, 0, VOLT)
    return im.resize((size, size), Image.LANCZOS)


def maskable(size, mono=False):
    big = size * SS
    im = Image.new('RGBA', (big, big), (0, 0, 0, 0) if mono else INK)
    d = ImageDraw.Draw(im)
    scale = big * 0.52 / 44                                     # the bolt is 44 units tall; 52 % of the side
    w, h = 28 * scale, 44 * scale                               # bolt box: x 14..42, y 10..54
    bolt(d, scale, (big - w) / 2 - 14 * scale, (big - h) / 2 - 10 * scale, (0, 0, 0, 255) if mono else VOLT)
    return im.resize((size, size), Image.LANCZOS)


SHORTCUTS = {'mapa': 'map', 'cene': 'bolt', 'vesti': 'news'}


async def shortcut_icons():
    from playwright.async_api import async_playwright
    src = (ROOT / 'templates' / '_icons.html').read_text(encoding='utf-8')
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={'width': 192, 'height': 192})
        for sc, name in SHORTCUTS.items():
            start = src.index(f"name == '{name}' -%}}") + len(f"name == '{name}' -%}}")
            paths = src[start:src.index('{%-', start)]
            svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="104" height="104" fill="none" stroke="#0B0F17" '
                   f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{paths}</svg>')
            await pg.set_content(f'<html><body style="margin:0;background:transparent"><div style="width:192px;height:192px;border-radius:50%;'
                                 f'background:#D9F45B;display:grid;place-items:center">{svg}</div></body></html>')
            await pg.screenshot(path=str(OUT / f'sc-{sc}-192.png'), omit_background=True)
        await b.close()


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    rounded(192).save(OUT / 'icon-192.png', optimize=True)
    rounded(512).save(OUT / 'icon-512.png', optimize=True)
    maskable(512).save(OUT / 'icon-maskable-512.png', optimize=True)
    maskable(512, mono=True).save(OUT / 'icon-monochrome-512.png', optimize=True)
    asyncio.run(shortcut_icons())
    for f in sorted(OUT.glob('*.png')):
        print(f.name, Image.open(f).size, f.stat().st_size // 1024, 'KB')
