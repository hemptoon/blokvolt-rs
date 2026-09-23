# -*- coding: utf-8 -*-
"""Renders static/com/og-en.png (1200×630 share image for blokvolt.com) with Playwright,
in the layout of the blokvolt.rs image: bolt, wordmark, one line of what the site is, topics, domain."""
import asyncio
import base64
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent
FONT = ROOT / 'static' / 'assets' / 'fonts'


def font(name):
    return base64.b64encode((FONT / name).read_bytes()).decode()


HTML = f"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:Onest;src:url(data:font/woff2;base64,{font('onest-latin-wght-normal.woff2')}) format('woff2');font-weight:100 900}}
@font-face{{font-family:Onest;src:url(data:font/woff2;base64,{font('onest-latin-ext-wght-normal.woff2')}) format('woff2');font-weight:100 900;unicode-range:U+0100-024F}}
html,body{{margin:0;width:1200px;height:630px;background:#0B0F17;font-family:Onest,sans-serif;overflow:hidden}}
.wrap{{position:absolute;left:80px;top:150px;display:flex;gap:26px;align-items:flex-start}}
svg{{flex:none;margin-top:30px}}
.wm{{font-size:64px;line-height:1;color:#F2F1EC;letter-spacing:-.02em}}.wm b{{font-weight:800}}.wm span{{font-weight:350}}
.l1{{margin-top:34px;font-size:33px;font-weight:700;color:#F2F1EC;letter-spacing:-.01em}}
.l2{{margin-top:14px;font-size:33px;font-weight:700;color:#D9F45B;letter-spacing:-.01em}}
.foot{{position:absolute;left:186px;bottom:78px;font-size:25px;font-weight:600;color:rgba(242,241,236,.55)}}
</style></head><body><div class="wrap"><svg width="80" height="126" viewBox="0 0 80 126"><path d="M36 0h21L46 48h34L22 126l14-60H0z" fill="#D9F45B"/></svg>
<div><div class="wm"><span>blok</span><b>volt</b></div><div class="l1">EV charging in Serbia and the Western Balkans</div><div class="l2">home chargers · public charging · prices · subsidies</div></div></div>
<div class="foot">blokvolt.com — every figure with a source and a check date</div></body></html>"""


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={'width': 1200, 'height': 630})
        await pg.set_content(HTML)
        await pg.wait_for_timeout(300)
        await pg.screenshot(path=str(ROOT / 'static' / 'com' / 'og-en.png'))
        await b.close()
    print('static/com/og-en.png')

asyncio.run(main())
