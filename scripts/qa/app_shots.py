# -*- coding: utf-8 -*-
"""Phone screenshots for /aplikacija/ (docs/RUNBOOK.md 3.20).

    python3 scripts/qa/cfserve.py dist 8787 &
    python3 scripts/qa/app_shots.py

Renders three pages of the local build at 390x844 CSS px, DPR 3, as an Android phone, and writes
static/assets/img/app-ekran-{pocetna,punjac,cene}-{390,780}.webp. The container cannot load the map tiles,
so the map screenshot is the station card (it does not need tiles), not the bare map."""
import asyncio
from pathlib import Path
from PIL import Image
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[2]
IMG = ROOT / 'static' / 'assets' / 'img'
BASE = 'http://localhost:8787'
SHOTS = {'app-ekran-pocetna': '/', 'app-ekran-punjac': '/mapa/?grad=novi-sad#cg-80', 'app-ekran-cene': '/javno-punjenje/'}
UA = 'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Mobile Safari/537.36'


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for name, path in SHOTS.items():
            ctx = await b.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=3, is_mobile=True,
                                      has_touch=True, reduced_motion='reduce', user_agent=UA)
            pg = await ctx.new_page()
            await pg.goto(BASE + path, wait_until='networkidle')
            await pg.wait_for_timeout(1500)
            png = f'/tmp/{name}.png'
            await pg.screenshot(path=png)
            await ctx.close()
            im = Image.open(png).convert('RGB')
            for w in (390, 780):
                im.resize((w, round(w * im.height / im.width)), Image.LANCZOS).save(IMG / f'{name}-{w}.webp', 'WEBP', quality=82, method=6)
            print(name, 'ok')
        await b.close()

asyncio.run(main())
