# Full-page screenshots of chosen pages, desktop (1440) and phone (390).
# Usage (server running): python3 scripts/qa/vis_shots.py /,/vesti/,/firme/elektronapon/ [shots-dir]
import asyncio, sys, json
from pathlib import Path
from playwright.async_api import async_playwright

PAGES = sys.argv[1].split(',')
SHOTS = Path(sys.argv[2] if len(sys.argv) > 2 else '/tmp/bv-shots')
SHOTS.mkdir(parents=True, exist_ok=True)
STYLE = {"version": 8, "sources": {}, "layers": [{"id": "bg", "type": "background", "paint": {"background-color": "#e9ecef"}}]}


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'])
        for w, h, tag in ((1440, 900, 'd'), (390, 844, 'm')):
            pg = await b.new_page(viewport={'width': w, 'height': h}, device_scale_factor=1)
            errs = []
            pg.on('pageerror', lambda e: errs.append(str(e)[:150]))
            pg.on('console', lambda m: errs.append(m.text[:160]) if m.type == 'error' and 'openfreemap' not in m.text else None)

            async def style(route):
                await route.fulfill(status=200, content_type='application/json', body=json.dumps(STYLE))
            await pg.route('https://tiles.openfreemap.org/**', style)
            await pg.route('**/api/**', lambda route: route.fulfill(status=200, content_type='application/json', body='{"ok":true,"st":{},"items":[],"photos":[]}'))
            for u in PAGES:
                await pg.goto('about:blank')
                await pg.goto('http://127.0.0.1:8787' + u, wait_until='load')
                await pg.wait_for_timeout(800)
                name = u.strip('/').replace('/', '_').replace('.html', '').replace('?', '_').replace('=', '-') or 'home'
                await pg.screenshot(path=str(SHOTS / f'v_{name}_{tag}.png'), full_page=True)
            print(tag, 'errors', errs[:6])
            await pg.close()
        await b.close()

asyncio.run(main())
