# -*- coding: utf-8 -*-
"""Builds blokvolt.com — the English regional guide — into dist-com/.

Sources: content/com/site.json (country list, home-page facts, Serbia summary) and
content/com/research/<CODE>.json (one verified fact file per country, schema in docs/RUNBOOK.md 3.10).
Design: the same site.css / agg.css / meganav.js as www.blokvolt.rs plus static/com/com.css.
Publish: dist-com/ is committed to github.com/hemptoon/blokvolt-com (GitHub Pages, custom domain
blokvolt.com) with the same web-upload payload procedure as the main repository (RUNBOOK 6).

Usage: python3 scripts/gen_com.py   (writes dist-com/ and prints a summary; exits 1 on broken links)"""
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import urlparse

from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent.parent
COM = ROOT / 'content' / 'com'
OUT = ROOT / 'dist-com'
RS_DIST = ROOT / 'dist'

cfg = json.load(open(COM / 'site.json', encoding='utf-8'))
SITE = cfg['site']
CHECKED, CHECKED_ISO, EMAIL = cfg['checked'], cfg['checked_iso'], cfg['email']
GLANCE = ('EV fleet', 'Public charging', 'Subsidies', 'Home chargers')

env = Environment(loader=FileSystemLoader(str(ROOT / 'templates' / 'com')),
                  autoescape=select_autoescape(['html']), trim_blocks=True, lstrip_blocks=True)
env.filters['domain'] = lambda u: (urlparse(u).netloc or u).replace('www.', '')

URL_RE = re.compile(r'https?://[^\s<>"\')\]]+')


def linkify(t):
    """Escape a text field and turn raw URLs in it into short links (some notes quote their source URL)."""
    from markupsafe import Markup, escape
    if t is None:
        return ''
    s = str(escape(t))

    def rep(m):
        u = m.group(0).rstrip('.,;:')
        return f'<a href="{u}" rel="noopener nofollow">{env.filters["domain"](u.replace("&amp;", "&"))}</a>' + m.group(0)[len(u):]
    return Markup(URL_RE.sub(rep, s))


env.filters['lk'] = linkify

countries = []
for c in cfg['countries']:
    c = dict(c)
    c['url'] = f"/{c['slug']}/"
    countries.append(c)


def rs_firm_count():
    n = 0
    for p in (ROOT / 'content' / 'firme').glob('*.json'):
        f = json.load(open(p, encoding='utf-8'))
        if f.get('publish') and f.get('group') != 'L':
            n += 1
    return n


def collect_sources(r):
    """Every distinct source of a country file: [{url, title, date}], in order of first use."""
    seen, out = set(), []

    def add(url, title, date):
        if not url or not str(url).startswith('http') or url in seen:
            return
        seen.add(url)
        out.append({'url': url, 'title': title or env.filters['domain'](url), 'date': date or ''})

    def walk(o):
        if isinstance(o, dict):
            if 'source' in o:
                add(o.get('source'), o.get('source_title'), o.get('source_date'))
            for v in o.values():
                if isinstance(v, (dict, list)):
                    walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk({k: v for k, v in r.items() if k != 'home_companies'})
    for h in r.get('home_companies', []):
        add(h.get('url'), f"{h['name']} — company website", h.get('source_date'))
    return out


def render(tpl, path, **ctx):
    base = dict(SITE=SITE, CHECKED=CHECKED, CHECKED_ISO=CHECKED_ISO, EMAIL=EMAIL, COUNTRIES=countries, path=path)
    base.update(ctx)
    html = env.get_template(tpl).render(**base)
    dest = OUT / (path.strip('/') + '/index.html' if path.endswith('/') and path != '/' else
                  ('index.html' if path == '/' else path.lstrip('/')))
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(html, encoding='utf-8')
    return dest


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    n_rs = rs_firm_count()
    research, all_sources, n_companies = {}, set(), n_rs
    pages = []
    for c in countries:
        if c['code'] == 'RS':
            continue
        r = json.load(open(COM / 'research' / f"{c['code']}.json", encoding='utf-8'))
        research[c['code']] = r
        srcs = collect_sources(r)
        all_sources.update(s['url'] for s in srcs)
        n_companies += len(r.get('home_companies', []))
        glance = list(zip(GLANCE, c['facts']))
        title = f"EV charging in {c['name']}: home chargers, public networks, prices and subsidies | BlokVolt"
        desc = (f"{c['name']}: who sells and installs home chargers, public charging networks and prices, "
                f"electricity at home, subsidies and the rules for apartment buildings — with sources, checked {r['checked']}.")
        render('country.html', c['url'], c=c, r=r, glance=glance, sources=srcs, n_sources=len(srcs), title=title, description=desc)
        pages.append(c['url'])
    render('serbia.html', '/serbia/', RS=cfg['serbia'], n_rs_firms=n_rs,
           title='EV charging in Serbia: installers, prices, public charging and subsidies | BlokVolt',
           description=(f'Serbia in short — {n_rs} installers and sellers of home chargers, public charging networks, '
                        'EPS electricity prices, the €5,000 subsidy and the rules for apartment buildings — with the full guide on blokvolt.rs.'))
    pages.insert(0, '/serbia/')
    render('home.html', '/', n_companies=n_companies, n_sources=len(all_sources), n_rs_firms=n_rs,
           title='EV charging in Serbia and the Western Balkans — independent guide | BlokVolt',
           description=('Home chargers, public charging, electricity prices, subsidies and apartment-building rules in Serbia, '
                        'Montenegro, Bosnia and Herzegovina, North Macedonia, Croatia and Slovenia — every figure with a source and a date.'))
    render('partners.html', '/partners/', title='For companies and suppliers | BlokVolt',
           description='How to get a company listed or corrected on BlokVolt — free and by the same rules for everyone — and where charging-hardware quotations go.')
    render('404.html', '/404.html', title='Page not found | BlokVolt', description='This page does not exist.', noindex=True)

    # assets: the design system of www.blokvolt.rs + com.css
    a = OUT / 'assets'
    for rel in ('site.css', 'agg.css', 'site.js', 'meganav.js', 'favicon.svg', 'apple-touch-icon.png', 'vendor/gsap.min.js'):
        (a / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / 'static' / 'assets' / rel, a / rel)
    fonts = ROOT / 'static' / 'assets' / 'fonts'
    (a / 'fonts').mkdir(parents=True, exist_ok=True)
    for f in ('onest-latin-wght-normal.woff2', 'onest-latin-ext-wght-normal.woff2'):
        shutil.copy2(fonts / f, a / 'fonts' / f)
    # the Cyrillic faces are declared in site.css but never used on the English site; ship them anyway
    for f in ('onest-cyrillic-wght-normal.woff2', 'onest-cyrillic-ext-wght-normal.woff2'):
        if (fonts / f).exists():
            shutil.copy2(fonts / f, a / 'fonts' / f)
    shutil.copy2(ROOT / 'static' / 'com' / 'com.css', a / 'com.css')
    (a / 'og').mkdir(exist_ok=True)
    shutil.copy2(ROOT / 'static' / 'com' / 'og-en.png', a / 'og' / 'og-en.png')

    # cache-busting query for CSS/JS (GitHub Pages caches for 10 minutes; the query makes new files win at once)
    ver = {n: hashlib.sha1((a / n).read_bytes()).hexdigest()[:10] for n in ('site.css', 'agg.css', 'com.css', 'site.js', 'meganav.js')}
    for p in OUT.rglob('*.html'):
        t = p.read_text(encoding='utf-8')
        for n, h in ver.items():
            t = t.replace(f'/assets/{n}"', f'/assets/{n}?v={h}"')
        p.write_text(t, encoding='utf-8')

    (OUT / 'CNAME').write_text('blokvolt.com\n', encoding='utf-8')
    (OUT / 'README.md').write_text(
        '# blokvolt.com\n\nEnglish regional guide to EV charging in Serbia and the Western Balkans, served by GitHub Pages '
        '(custom domain blokvolt.com).\n\nThis repository holds the built site only. Pages are generated by `scripts/gen_com.py` '
        'in [hemptoon/blokvolt-rs](https://github.com/hemptoon/blokvolt-rs) from `content/com/` — edit the data there, rebuild '
        'and upload; do not edit the HTML here by hand. Procedure: `docs/RUNBOOK.md`, section 3.10.\n', encoding='utf-8')
    (OUT / '.nojekyll').write_text('\n', encoding='utf-8')
    (OUT / 'robots.txt').write_text(f'User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n', encoding='utf-8')
    urls = ['/'] + pages + ['/partners/']
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        pr = '1.0' if u == '/' else ('0.3' if u == '/partners/' else '0.8')
        sm.append(f'  <url><loc>{SITE}{u}</loc><lastmod>{CHECKED_ISO}</lastmod><priority>{pr}</priority></url>')
    sm.append('</urlset>')
    (OUT / 'sitemap.xml').write_text('\n'.join(sm) + '\n', encoding='utf-8')

    # link check: internal links must exist; links into blokvolt.rs must exist in its dist/ (when built)
    bad = []
    for p in OUT.rglob('*.html'):
        for href in re.findall(r'href="([^"]+)"', p.read_text(encoding='utf-8')):
            if href.startswith('/') and not href.startswith('//'):
                path = href.split('#')[0].split('?')[0]
                if not path:
                    continue
                t = OUT / path.lstrip('/')
                if not (t.is_file() or (t / 'index.html').is_file()):
                    bad.append((p.relative_to(OUT), href))
            elif href.startswith('https://www.blokvolt.rs/') and RS_DIST.exists():
                path = urlparse(href).path
                t = RS_DIST / path.lstrip('/')
                if not (t.is_file() or (t / 'index.html').is_file() or t.with_suffix('.html').is_file() or path == '/'):
                    bad.append((p.relative_to(OUT), href))
    files = [p for p in OUT.rglob('*') if p.is_file()]
    print(f'blokvolt.com: {len(urls)} pages, {len(files)} files, {n_companies} companies, {len(all_sources)} sources; broken links: {len(bad)}')
    for b in bad:
        print('  broken:', *b)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
