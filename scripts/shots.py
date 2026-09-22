import asyncio, sys
from playwright.async_api import async_playwright
PAGES = [('home','/'),('firme','/firme/'),('firma','/firme/orion-emobility/'),('cena','/cena-punjaca-za-elektricni-auto.html#tabela'),('subv','/podaci/subvencije-2026/'),('grad','/gradovi/novi-sad/'),('vodici','/vodici/')]
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for name, path in PAGES:
            for w, tag in ((1440, 'd'), (390, 'm')):
                pg = await b.new_page(viewport={'width': w, 'height': 900}, device_scale_factor=1)
                errs = []
                pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
                pg.on('requestfailed', lambda r: errs.append('FAIL ' + r.url))
                await pg.goto('http://127.0.0.1:8787' + path, wait_until='networkidle')
                h = await pg.evaluate('document.body.scrollHeight')
                for y in range(0, h, 500):
                    await pg.evaluate(f'window.scrollTo(0,{y})'); await pg.wait_for_timeout(60)
                await pg.evaluate('window.scrollTo(0,0)'); await pg.wait_for_timeout(300)
                await pg.screenshot(path=f'/tmp/shot_{name}_{tag}.png', full_page=(tag == 'd'))
                if errs: print(name, tag, errs[:5])
                await pg.close()
        await b.close()
asyncio.run(main())
print('done')
