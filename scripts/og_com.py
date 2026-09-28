# -*- coding: utf-8 -*-
"""Renders the 1200×630 share images of blokvolt.com with Playwright, in the layout of the blokvolt.rs image:
bolt, wordmark, one line of what the page is, topics, domain.
static/com/og-en.png (English pages) and og-hr.png, og-ba.png, og-me.png (local sections, with the country tag
that the header shows next to the logo)."""
import asyncio
import base64
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent
FONT = ROOT / 'static' / 'assets' / 'fonts'
OUT = ROOT / 'static' / 'com'

IMAGES = {
    'en': dict(tag='', l1='EV charging in Serbia and the Western Balkans',
               l2='home chargers · public charging · prices · subsidies',
               foot='blokvolt.com — every figure with a source and a check date'),
    'hr': dict(tag='HR', l1='Punjenje električnih automobila u Hrvatskoj',
               l2='karta · cijene · kućno punjenje · poticaji',
               foot='blokvolt.com/hr — svaki podatak s izvorom i datumom provjere'),
    'ba': dict(tag='BA', l1='Punjenje električnih automobila u BiH',
               l2='mapa · cijene · punjenje kod kuće · poticaji',
               foot='blokvolt.com/ba — svaki podatak s izvorom i datumom provjere'),
    'me': dict(tag='ME', l1='Punjenje električnih automobila u Crnoj Gori',
               l2='mapa · cijene · punjenje kod kuće · subvencije',
               foot='blokvolt.com/me — svaki podatak s izvorom i datumom provjere'),
}


def font(name):
    return base64.b64encode((FONT / name).read_bytes()).decode()


def html(tag, l1, l2, foot):
    t = f'<i>{tag}</i>' if tag else ''
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:Onest;src:url(data:font/woff2;base64,{font('onest-latin-wght-normal.woff2')}) format('woff2');font-weight:100 900}}
@font-face{{font-family:Onest;src:url(data:font/woff2;base64,{font('onest-latin-ext-wght-normal.woff2')}) format('woff2');font-weight:100 900;unicode-range:U+0100-024F}}
html,body{{margin:0;width:1200px;height:630px;background:#0B0F17;font-family:Onest,sans-serif;overflow:hidden}}
.wrap{{position:absolute;left:80px;top:150px;display:flex;gap:26px;align-items:flex-start}}
svg{{flex:none;margin-top:30px}}
.wm{{display:flex;align-items:center;gap:16px;font-size:64px;line-height:1;color:#F2F1EC;letter-spacing:-.02em}}
.wm b{{font-weight:800}}.wm span{{font-weight:350}}
.wm i{{font-style:normal;font-size:26px;font-weight:750;letter-spacing:.06em;background:#D9F45B;color:#0B0F17;border-radius:9px;padding:7px 11px 6px}}
.l1{{margin-top:34px;font-size:33px;font-weight:700;color:#F2F1EC;letter-spacing:-.01em;white-space:nowrap}}
.l2{{margin-top:14px;font-size:31px;font-weight:700;color:#D9F45B;letter-spacing:-.01em;white-space:nowrap}}
.foot{{position:absolute;left:186px;bottom:78px;font-size:25px;font-weight:600;color:rgba(242,241,236,.55)}}
</style></head><body><div class="wrap"><svg width="80" height="126" viewBox="0 0 80 126"><path d="M36 0h21L46 48h34L22 126l14-60H0z" fill="#D9F45B"/></svg>
<div><div class="wm"><div><span>blok</span><b>volt</b></div>{t}</div><div class="l1">{l1}</div><div class="l2">{l2}</div></div></div>
<div class="foot">{foot}</div></body></html>"""


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={'width': 1200, 'height': 630})
        for key, v in IMAGES.items():
            await pg.set_content(html(**v))
            await pg.wait_for_timeout(300)
            # nothing may run past the right edge (80 px margin)
            right = await pg.evaluate("Math.max(...[...document.querySelectorAll('.l1,.l2,.foot,.wm')].map(e => e.getBoundingClientRect().right))")
            if right > 1120:
                raise SystemExit(f'og-{key}: text reaches {right:.0f}px, shorten it')
            path = OUT / f'og-{key}.png'
            await pg.screenshot(path=str(path))
            print(path.relative_to(ROOT), f'(text to {right:.0f}px)')
        await b.close()

asyncio.run(main())
