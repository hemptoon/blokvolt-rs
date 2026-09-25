# Every URL of the sitemap (Serbian, /en/, /ru/) at several widths: JS errors, CSP violations, HTTP status,
# horizontal overflow, broken images, gap under the footer.
# Usage (server running, see cfserve.py): python3 scripts/qa/qa_all.py sr,en,ru 360,768,1440
import asyncio, re, sys, json
from pathlib import Path
from playwright.async_api import async_playwright

REPO = Path(__file__).resolve().parents[2]
base = re.findall(r'<loc>https://www\.blokvolt\.rs(/[^<]*)</loc>', (REPO / 'dist' / 'sitemap.xml').read_text())
base = sorted({re.sub(r'^/(en|ru)(?=/)', '', u) for u in base})
langs = sys.argv[1].split(',') if len(sys.argv) > 1 else ['sr']
widths = [int(x) for x in (sys.argv[2].split(',') if len(sys.argv) > 2 else ['360', '1440'])]


def lang_url(u, l):
    return u if l == 'sr' else '/' + l + u


urls = [lang_url(u, l) for l in langs for u in base if not (l != 'sr' and u.startswith('/admin'))]
STYLE = {"version": 8, "sources": {}, "layers": [{"id": "bg", "type": "background", "paint": {"background-color": "#e9ecef"}}]}
IGNORE = ('openfreemap', 'ERR_', 'Failed to fetch', '/api/', '404', 'cloudflareinsights')


async def check(b, path, w, sem, out):
    async with sem:
        pg = await b.new_page(viewport={'width': w, 'height': 844 if w < 900 else 900})
        errs = []
        pg.on('pageerror', lambda e: errs.append('JS ' + str(e)[:140]))
        pg.on('console', lambda m: errs.append('CON ' + m.text[:160]) if m.type == 'error' and (not any(x in m.text for x in IGNORE) or 'Content Security Policy' in m.text) else None)

        async def style(route):
            await route.fulfill(status=200, content_type='application/json', body=json.dumps(STYLE))
        await pg.route('https://tiles.openfreemap.org/**', style)
        await pg.route('**/api/**', lambda route: route.fulfill(status=200, content_type='application/json', body='{"ok":true,"st":{},"items":[],"photos":[]}'))
        try:
            r0 = await pg.goto('http://127.0.0.1:8787' + path, wait_until='load', timeout=25000)
            if r0 and r0.status >= 400:
                errs.append(f'HTTP {r0.status}')
            await pg.wait_for_timeout(300)
            r = await pg.evaluate('''() => ({sw: document.documentElement.scrollWidth, iw: innerWidth,
              bad: [...document.images].filter(i => i.complete && i.naturalWidth === 0 && !i.src.includes('openfreemap') && !i.src.includes('/api/')).map(i => i.src.replace(location.origin,'')).slice(0,3),
              wide: [...document.querySelectorAll('main *')].filter(e => e.getBoundingClientRect().right > innerWidth + 1 && getComputedStyle(e).position !== 'fixed' && !e.closest('.tw,.map-app,pre,.scroll-x,.chips')).slice(0,2).map(e => e.tagName + '.' + (e.className||'').toString().slice(0,30)),
              foot: (() => { const f = document.querySelector('footer'); return f ? Math.round(f.getBoundingClientRect().bottom + scrollY) - Math.max(document.documentElement.scrollHeight, innerHeight) : 0 })()})''')
            if r['sw'] > r['iw'] + 1:
                errs.append(f"OVERFLOW {r['sw']} {r['wide']}")
            if r['bad']:
                errs.append('IMG ' + ' '.join(r['bad']))
            if abs(r['foot']) > 2:
                errs.append(f"FOOTER gap {r['foot']}")
        except Exception as e:
            errs.append('GOTO ' + str(e)[:80])
        if errs:
            out.append((path, w, errs[:4]))
        await pg.close()


async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        sem = asyncio.Semaphore(8)
        out = []
        await asyncio.gather(*(check(b, u, w, sem, out) for u in urls for w in widths))
        await b.close()
    print(len(urls), 'pages x', widths, ';', len(out), 'with issues')
    for pth, w, e in sorted(out):
        print(w, pth, e)

asyncio.run(main())
