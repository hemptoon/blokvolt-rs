"""Fetch the world data of a dev build from the tiles host (hemptoon/blokvolt-tiles on GitHub Pages) and prepare it:
pages bundle (K3), cards, manifest and the country/city frames `places` (K1). The manifest gets absolute URLs for the tiles and the ODbL dump (they stay on
the tiles host: GitHub Pages answers Range requests, Cloudflare Pages does not), the cards are served next to the site.

    python3 scripts/dev_world_data.py <tiles base URL> <work dir>   → prints shell lines: D=…, PAGES=…, MANIFEST=…, CARDS=…
"""
import json
import os
import subprocess
import sys
import tarfile
import urllib.request
from pathlib import Path


def get(url, dest=None):
    with urllib.request.urlopen(url, timeout=120) as r:
        data = r.read()
    if dest:
        Path(dest).write_bytes(data)
    return data


def main(base, work):
    base = base.rstrip('/')
    work = Path(work)
    work.mkdir(parents=True, exist_ok=True)
    latest = json.loads(get(f'{base}/latest.json'))
    d = latest['date']
    dd = f"{base}/{latest.get('data', f'data/{d}/')}".rstrip('/')
    for name in (f'pages-{d}.tar.gz', f'cards-{d}.tar.gz', f'manifest-{d}.json'):
        get(f'{dd}/{name}', work / name)
    for name in (f'pages-{d}.tar.gz', f'cards-{d}.tar.gz'):
        with tarfile.open(work / name) as t:
            t.extractall(work, filter='data')
    m = json.load(open(work / f'manifest-{d}.json', encoding='utf-8'))
    # BV_TILES_PATH: a task branch may point its own preview at another tiles folder of the host (K7: world/2026-11-09-k7/)
    # without touching latest.json, so the previews of dev and the other branches stay as they are
    m['tiles'] = f"{base}/{os.environ.get('BV_TILES_PATH') or latest['tiles']}"
    if m.get('odbl_dump') and not str(m['odbl_dump']).startswith('http'):
        m['odbl_dump'] = f"{dd}/{m['odbl_dump']}"
    m['dev_note'] = 'dev build: tiles and ODbL dump on the tiles host, cards next to the site'
    json.dump(m, open(work / f'manifest-{d}.json', 'w', encoding='utf-8'), ensure_ascii=False)
    if m.get('places'):
        get(f"{dd}/{m['places']}", work / m['places'])
    pages = next(work.glob('pages-*/index.json')).parent
    print(f'D={d}')
    print(f'PAGES={pages}')
    print(f'MANIFEST={work}/manifest-{d}.json')
    print(f'CARDS={work}/{m["cards_base"].rstrip("/")}')
    print(f"PLACES={work}/{m['places']}" if m.get('places') else 'PLACES=')


if __name__ == '__main__':
    main(*sys.argv[1:3])
