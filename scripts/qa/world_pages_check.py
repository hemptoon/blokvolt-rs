# -*- coding: utf-8 -*-
"""Checks of the world pages of blokvolt.com (task K3) on a built dist-com/.

  python3 scripts/qa/world_pages_check.py <dist-com> <pages-YYYY-MM-DD dir> [--report out.json] [--seed 7]

Checks: counts and sizes; robots / sitemap / no links from existing pages while config.public is false; JSON-LD
parses (BreadcrumbList everywhere, Dataset with licence and download on country pages); canonical = self; hreflang
en/sr/ru + x-default, absolute and reciprocal; unique titles; no digits in titles beyond those of the names; every
page above its threshold and none for the Balkan countries; SR text without "mi", "odmah", "24/7", Cyrillic; no
ratings or Evolako anywhere; 100 random numbers of the page JSON found on their pages. Exit 1 on any failure.
"""
import json
import random
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import world_pages as W  # noqa: E402

SITE = 'https://blokvolt.com'
BALKAN = W.BALKAN
RATING = re.compile(r'\b(rating|ratings|best|top-rated|najbolj\w*|ocena mreže|рейтинг\w*|лучш\w*)\b', re.I)


class P(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title, self.canon, self.alts, self.robots, self.ld, self.links, self.text = '', None, [], None, [], [], []
        self._t = self._ld = self._skip = False

    def handle_starttag(self, tag, a):
        a = dict(a)
        if tag == 'title':
            self._t = True
        elif tag == 'link' and a.get('rel') == 'canonical':
            self.canon = a.get('href')
        elif tag == 'link' and a.get('rel') == 'alternate' and a.get('hreflang'):
            self.alts.append((a['hreflang'], a['href']))
        elif tag == 'meta' and a.get('name') == 'robots':
            self.robots = a.get('content')
        elif tag == 'script' and a.get('type') == 'application/ld+json':
            self._ld = True
            self.ld.append('')
        elif tag in ('script', 'style'):
            self._skip = True
        elif tag == 'a' and a.get('href'):
            self.links.append(a['href'])

    def handle_endtag(self, tag):
        if tag == 'title':
            self._t = False
        if tag == 'script':
            self._ld = self._skip = False
        if tag == 'style':
            self._skip = False

    def handle_data(self, d):
        if self._t:
            self.title += d
        elif self._ld:
            self.ld[-1] += d
        elif not self._skip:
            self.text.append(d)


def parse(p):
    html = p.read_text(encoding='utf-8')
    x = P()
    x.feed(html)
    x.body = re.sub(r'[ \t\r\n]+', ' ', ' '.join(x.text))       # keeps the no-break spaces of the numbers
    # words written by the site, without data (names of places and networks carry translate="no")
    y = P()
    y.feed(re.sub(r'<(a|td|span|li|p)\b[^>]*translate="no"[^>]*>.*?</\1>', ' ', html, flags=re.S))
    x.own = re.sub(r'[ \t\r\n]+', ' ', ' '.join(y.text))
    return x


def main():
    dist, bdir = Path(sys.argv[1]), Path(sys.argv[2])
    rep_path = sys.argv[sys.argv.index('--report') + 1] if '--report' in sys.argv else None
    seed = int(sys.argv[sys.argv.index('--seed') + 1]) if '--seed' in sys.argv else 7
    cfg = json.load(open(W.WORLD / 'config.json', encoding='utf-8'))
    idx, pages = W.load_bundle(bdir)
    names = W.Names(bdir)
    site = W.Site(names, idx, pages)
    th = W.thresholds(idx)
    fails, R = [], {}

    def fail(m):
        fails.append(m)

    # every world URL
    urls = {}
    for p in pages:
        for l in site.langs(p):
            urls[site.url(p, l)] = (p, l)
        for l in set(W.LANGS) - set(site.langs(p)):   # v2: no SR page outside Europe
            if (dist / site.url(p, l).strip('/') / 'index.html').exists():
                fail(f'page in a language it should not have: {site.url(p, l)}')
    extra = {site.about(l): (None, l) for l in W.LANGS}
    extra.update({site.download(l): (None, l) for l in W.LANGS})
    files = {}
    for u in list(urls) + list(extra):
        f = dist / u.strip('/') / 'index.html'
        if not f.exists():
            fail(f'missing {u}')
        else:
            files[u] = f
    sizes = sorted(f.stat().st_size for f in files.values())
    by = {}
    for u, (p, l) in list(urls.items()) + list(extra.items()):
        t = p['type'] if p else ('about' if 'about' in u or 'podacima' in u or 'dannyh' in u else 'download')
        by.setdefault(t, {}).setdefault(l, 0)
        by[t][l] += 1
    R['counts'] = by
    R['html_files'] = len(files)
    R['size_total_mb'] = round(sum(sizes) / 1e6, 1)
    R['size_median_kb'] = round(sizes[len(sizes) // 2] / 1024, 1)
    R['size_p95_kb'] = round(sizes[int(len(sizes) * .95)] / 1024, 1)
    R['size_max_kb'] = round(sizes[-1] / 1024, 1)
    R['over_30kb'] = sum(1 for s in sizes if s > 30 * 1024)
    mini = list((dist / 'assets' / 'world' / 'mini').glob('*.svg'))
    R['mini_svg'] = dict(files=len(mini), total_mb=round(sum(m.stat().st_size for m in mini) / 1e6, 1))

    # thresholds and Balkans
    for p in pages:
        if p.get('cc') in BALKAN:
            fail(f"Balkan page {p['key']}")
        if p['type'] in ('country', 'city', 'network') and (p['n50'] or 0) < th[p['type']]:
            fail(f"below threshold {p['key']} n50={p['n50']}")

    parsed = {u: parse(f) for u, f in files.items()}
    titles = {}
    ld_n = 0
    for u, x in parsed.items():
        p, l = urls.get(u) or extra.get(u)
        if x.canon != SITE + u:
            fail(f'canonical {u} -> {x.canon}')
        if not cfg.get('public') and x.robots != 'noindex,nofollow':
            fail(f'robots {u}: {x.robots}')
        a = dict(x.alts)
        want = set(site.langs(p)) if p else set(W.LANGS)
        if set(a) != want | {'x-default'} or a.get('x-default') != a.get('en'):
            fail(f'hreflang set {u}: {sorted(a)}')
        for code, href in x.alts:
            if not href.startswith(SITE + '/'):
                fail(f'hreflang not absolute {u}')
            back = parsed.get(href[len(SITE):])
            if back is None:
                fail(f'hreflang target missing {u} -> {href}')
            elif SITE + u not in dict(back.alts).values():
                fail(f'hreflang not reciprocal {u} -> {href}')
        try:
            graph = [json.loads(s) for s in x.ld]
            ld_n += 1
            types = {g['@type'] for d in graph for g in d.get('@graph', [d])}
            if 'BreadcrumbList' not in types:
                fail(f'no BreadcrumbList {u}')
            if p and p['type'] == 'country':
                ds = [g for d in graph for g in d['@graph'] if g['@type'] == 'Dataset']
                if not ds or not ds[0].get('license') or not ds[0].get('distribution') or len(ds[0].get('description', '')) < 50:
                    fail(f'Dataset incomplete {u}')
            for d in graph:
                for g in d.get('@graph', []):
                    if g['@type'] == 'BreadcrumbList':
                        for i, it in enumerate(g['itemListElement']):
                            if it['position'] != i + 1 or not it['item'].startswith(SITE + '/'):
                                fail(f'breadcrumb item {u}')
        except Exception as e:  # noqa: BLE001
            fail(f'JSON-LD {u}: {e}')
        titles.setdefault((l, x.title), []).append(u)
        # digits in the title are allowed only inside the names of the page
        nm = ''
        if p and p['type'] == 'city':
            nm = names.city_name(p['data']['city'], l) + names.country(p['cc'], l)
        elif p and p['type'] in ('network', 'network_global'):
            nm = names.net_name(p['net'], l) + (names.country(p['cc'], l) if p.get('cc') else '')
        if re.sub(r'\d', '', x.title) != x.title and not set(re.findall(r'\d', x.title)) <= set(re.findall(r'\d', nm)):
            fail(f'digits in title {u}: {x.title}')
        body = x.title + ' ' + x.own
        if l == 'sr':
            if re.search(r'\b(mi|naš|naša|naše|naši|odmah|redakcija)\b', body, re.I) or '24/7' in body:
                fail(f'sr words {u}')
            if p:
                txt = body.replace('Русский', '').replace('Северна Македонија', '')   # language menu and footer link (lang=, translate="no")
                if p['type'] == 'city':
                    txt = txt.replace(names.city_name(p['data']['city'], 'sr'), '')
                if re.search(r'[А-Яа-яЁё]', txt):
                    fail(f'Cyrillic in sr {u}')
        if re.search(r'\bodmah\b|24/7|сразу же', body, re.I):
            fail(f'odmah/24-7 {u}')
        if 'Evolako' in body or 'evolako' in ' '.join(x.links):
            fail(f'Evolako on {u}')
        for w in (nm, names.net_name(p['net'], l) if p and p.get('net') else '', names.city_name(p['data']['city'], l) if p and p['type'] == 'city' else ''):
            body = body.replace(w, ' ') if w else body
        m = RATING.search(body) if p else None   # the about page explains the formula ("best source type")
        if m:
            fail(f'rating word "{m.group(0)}" on {u}')
    dup = {k: v for k, v in titles.items() if len(v) > 1}
    for (l, t), v in list(dup.items())[:20]:
        fail(f'duplicate title [{l}] {t}: {v[:3]}')
    R['duplicate_titles'] = len(dup)
    R['jsonld_pages'] = ld_n

    # not public: no sitemap entry, no link from the existing site
    world_prefixes = tuple({W.L[l]['hub'] for l in W.LANGS} | {W.L[l]['gnet'] for l in W.LANGS})
    sm = (dist / 'sitemap.xml').read_text(encoding='utf-8') if (dist / 'sitemap.xml').exists() else ''
    if not cfg.get('public'):
        if any(SITE + w in sm for w in world_prefixes) or (dist / 'sitemap-world.xml').exists():
            fail('world URL in a sitemap while not public')
        n_old = 0
        for f in dist.rglob('*.html'):
            rel = '/' + str(f.parent.relative_to(dist)).strip('.') + '/'
            if rel.startswith(world_prefixes) or rel.replace('//', '/').startswith(world_prefixes):
                continue
            t = f.read_text(encoding='utf-8')
            if 'class="ft-world"' in t:   # a page of the world layer itself (map, G0 shell pages, dev home)
                continue
            n_old += 1
            for w in world_prefixes:
                if f'href="{w}' in t or f'href="{SITE}{w}' in t:
                    fail(f'existing page links to the world layer: {f.relative_to(dist)}')
        R['existing_pages_checked'] = n_old

    # search index (bvcom G0/G2)
    import gzip
    si = dist / 'assets' / 'world' / 'search-index.json'
    if not si.exists():
        fail('no search index')
    else:
        raw = si.read_bytes()
        R['search_index'] = dict(entries=len(json.loads(raw)['items']), kb=round(len(raw) / 1024), kb_gzip=round(len(gzip.compress(raw, 9)) / 1024))
        for it in json.loads(raw)['items']:
            for u in it[6]:
                if u and u.startswith('/') and not (dist / u.strip('/') / 'index.html').exists():
                    fail(f'search index URL missing: {u}')
        if R['search_index']['kb_gzip'] > 300:
            fail('search index > 300 KB gzip')

    # 100 random numbers from the page JSON on their page
    rnd = random.Random(seed)
    checked, missed = 0, []
    cand = [p for p in pages if p['type'] in ('country', 'city', 'network')]
    for _ in range(100):
        p = rnd.choice(cand)
        l = rnd.choice(site.langs(p))
        loc = W.L[l]
        st = p['data']['stats']
        opts = [('stats.n', st['n']), ('stats.dc50', st['dc50']), ('stats.hpc', st['hpc']), ('stats.n_nets', st['n_nets']),
                ('stats.pct_multi', st['pct_multi']), ('stats.pct_recent', st['pct_recent'])]
        opts += [(f'stats.power.{k}', v) for k, v in st['power'].items() if v]
        opts += [(f'stats.conn.{t}', v) for t, v in st['conn']]
        opts += [(f'stats.sources.{k}', v) for k, v in st['sources']]
        if p['type'] == 'city' and p['data']['fast']:
            r = rnd.choice(p['data']['fast'])
            if r[3]:
                opts.append(('fast.kw', r[3]))
        if p['type'] == 'country' and p['data']['city_pages']:
            opts.append(('city_pages.n', rnd.choice(p['data']['city_pages'])[1]))
        field, v = rnd.choice(opts)
        s = W.fmt_num(v, loc)
        u = site.url(p, l)
        body = parsed[u].body
        hit = re.search(r'(?<![\d., ])' + re.escape(s) + r'(?![\d]|[.,]\d)', body)
        checked += 1
        if not hit:
            missed.append((u, field, s))
    for m in missed:
        fail(f'number not on page: {m}')
    R['numbers_checked'] = checked
    R['numbers_missed'] = len(missed)
    R['fails'] = fails[:2000]
    R['n_fails'] = len(fails)
    print(json.dumps({k: v for k, v in R.items() if k != 'fails'}, ensure_ascii=False, indent=1))
    for f in fails[:40]:
        print('FAIL', f)
    if rep_path:
        Path(rep_path).write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding='utf-8')
    print('world pages check:', 'PASS' if not fails else f'FAIL ({len(fails)})')
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
