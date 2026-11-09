#!/usr/bin/env python3
"""Accessibility check of www.blokvolt.rs and www.evolako.rs (RUNBOOK 3.40, since 09.11.2026).

axe-core (WCAG 2.2 A/AA rules) on the key pages of both sites in Serbian, English and Russian, plus three checks axe
does not make: a skip link as the first focusable element, a visible focus ring on the first 20 Tab stops, and no
sideways scrolling at 320 px (= 400 % zoom on a 1280 px screen).

  FAIL — a "serious" or "critical" axe violation, a missing skip link, a focus stop without a ring, overflow at 320 px
  WARN — "moderate" / "minor" axe findings (shown, never fail the run)

usage:
  python3 scripts/qa/a11y_check.py                          # both live sites
  python3 scripts/qa/a11y_check.py --site blokvolt --base http://127.0.0.1:8787   # local dist (cfserve.py)
  python3 scripts/qa/a11y_check.py --site evolako  --base http://127.0.0.1:8788   # evolako-web site/dist
needs: pip install playwright && python3 -m playwright install chromium; axe-core from npm
(AXE_JS=path/to/axe.min.js, default node_modules/axe-core/axe.min.js).
"""
import argparse
import json
import os
import sys

from playwright.sync_api import sync_playwright

PAGES = {
    'blokvolt': ('https://www.blokvolt.rs', [
        '/', '/mapa/', '/firme/', '/firme/chargego/', '/vesti/', '/vodici/', '/alati/kalkulator-troskova/',
        '/alati/racun-u-zgradi/', '/javno-punjenje/', '/javno-punjenje/cene/', '/elektricni-automobili/',
        '/gradovi/beograd/', '/pomoc/', '/nalog/', '/pretraga/', '/servisi/', '/za-firme/', '/pristupacnost/',
        '/en/', '/en/mapa/', '/ru/', '/ru/pristupacnost/']),
    'evolako': ('https://www.evolako.rs', [
        '/', '/paketi-i-cene', '/kontakt', '/cesta-pitanja', '/mapa-punjaca', '/kalkulator-cene-punjaca', '/vodici',
        '/novosti', '/proveri-svoju-garazu', '/preporuka', '/prijavi-zgradu', '/punjaci-za-firme',
        '/sabloni-za-skupstinu', '/ugradnja-punjaca', '/pristupacnost', '/karijera', '/en/', '/en/paketi-i-cene',
        '/ru/', '/ru/kontakt']),
}
TAGS = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']
# known and accepted, with the reason (keep this list short and dated)
# entries: 'site:rule-id:css target' — none on 09.11.2026
ALLOW = set()

FOCUS_JS = r"""() => { const a = document.activeElement; if (!a || a === document.body) return null;
  const cs = getComputedStyle(a), after = getComputedStyle(a, '::after');
  const ring = (cs.outlineStyle !== 'none' && parseFloat(cs.outlineWidth) > 0) || cs.boxShadow !== 'none' ||
               (after.outlineStyle !== 'none' && parseFloat(after.outlineWidth) > 0);
  return {ring, what: (a.tagName + ' ' + (a.getAttribute('aria-label') || a.innerText || a.className || '')).trim().slice(0, 60)}; }"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--site', choices=sorted(PAGES), action='append')
    ap.add_argument('--base')
    ap.add_argument('--json')
    a = ap.parse_args()
    axe_js = open(os.environ.get('AXE_JS', 'node_modules/axe-core/axe.min.js'), encoding='utf-8').read()
    sites = a.site or sorted(PAGES)
    fails, warns, out = [], [], {}
    with sync_playwright() as p:
        br = p.chromium.launch()
        ctx = br.new_context(viewport={'width': 1280, 'height': 900}, bypass_csp=True,
                             extra_http_headers={'Cache-Control': 'no-cache'})
        for site in sites:
            base, paths = PAGES[site]
            base = a.base or base
            for path in paths:
                url = base + path + ('&' if '?' in path else '?') + 'a11y=1'
                pg = ctx.new_page()
                where = '%s %s' % (site, path)
                try:
                    r = pg.goto(url, wait_until='load', timeout=45000)
                    if not r or r.status >= 400:
                        fails.append('%s: HTTP %s' % (where, r.status if r else '—'))
                        continue
                    pg.wait_for_timeout(1200)
                    pg.evaluate(axe_js)
                    res = pg.evaluate("""async (tags) => (await axe.run(document, {runOnly: {type: 'tag', values: tags},
                        resultTypes: ['violations']})).violations.map(v => ({id: v.id, impact: v.impact, help: v.help,
                        nodes: v.nodes.map(n => n.target.join(' '))}))""", TAGS)
                    for v in res:
                        nodes = [n for n in v['nodes'] if '%s:%s:%s' % (site, v['id'], n) not in ALLOW]
                        if not nodes:
                            continue
                        line = '%s: %s (%s) ×%d — %s — %s' % (where, v['id'], v['impact'], len(nodes), v['help'],
                                                             ', '.join(nodes[:3]))
                        (fails if v['impact'] in ('serious', 'critical') else warns).append(line)
                    first = pg.evaluate("""() => { const e = document.querySelector('a[href],button,input,select,textarea');
                        return e ? (e.getAttribute('href') || '') : ''; }""")
                    if first not in ('#main', '#sadrzaj', '#content'):
                        fails.append('%s: the first focusable element is not a skip link (%r)' % (where, first))
                    noring = []
                    for _ in range(20):
                        pg.keyboard.press('Tab')
                        f = pg.evaluate(FOCUS_JS)
                        if f and not f['ring']:
                            noring.append(f['what'])
                    if noring:
                        fails.append('%s: %d focus stops without a visible ring: %s' % (where, len(noring), noring[:3]))
                    pg.set_viewport_size({'width': 320, 'height': 640})
                    pg.wait_for_timeout(400)
                    over = pg.evaluate('() => document.documentElement.scrollWidth - document.documentElement.clientWidth')
                    if over > 1:
                        fails.append('%s: %d px of sideways scrolling at 320 px (400 %% zoom)' % (where, over))
                    out[where] = res
                    print('ok  ' if not any(x.startswith(where + ':') for x in fails) else 'FAIL', where, flush=True)
                except Exception as e:                      # noqa: BLE001 — a page that does not load is a failure
                    fails.append('%s: %s' % (where, str(e).splitlines()[0][:160]))
                finally:
                    pg.close()
        br.close()
    if a.json:
        json.dump(out, open(a.json, 'w'), ensure_ascii=False, indent=1)
    for w in warns:
        print('WARN', w)
    for f in fails:
        print('FAIL', f)
    print('accessibility: %d pages, %d FAIL, %d WARN' % (sum(len(PAGES[s][1]) for s in sites), len(fails), len(warns)))
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8') as s:
            s.write('### Accessibility\n\n%d FAIL, %d WARN\n\n' % (len(fails), len(warns)))
            s.writelines('- FAIL %s\n' % f for f in fails)
            s.writelines('- WARN %s\n' % w for w in warns)
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
