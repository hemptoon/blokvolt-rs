"""First screen of the world home of blokvolt.com (task HOME2, 11.11.2026): "night lights" pictures of the public layer.

Draws every place of the public layer (K1 public_sites.geojsonseq) as lime light on a dark ground with thin country
borders and coastlines (Natural Earth 1:50m, public domain — content/world/home/ne_lines.json), in Web Mercator, for
three regions (eu = Europe, na = USA and Canada, ap = Asia-Pacific) and two shapes (w = wide, for screens wider than
720 px; t = tall, for phones). Each picture records its view (centre, MapLibre zoom at 512 px tiles, size), so the live
map of the home page (static/com/world-hero-map.js) opens exactly where the picture is and looks the same: the picture is
swapped for the map in place on the first tap or click.

Output (committed to blokvolt-rs; the weekly world run on the Mac writes it into out/<date>/repo_state/hero/):
    static/com/hero/hero-<region>-<shape>.avif / .webp   (each ≤ 150 KB; AVIF only where Pillow can write it)
    static/com/hero/borders.json                         (coarser lines for the live map, loaded on the first tap)
    content/world/home/hero.json                         (date, number of places drawn, views, file sizes, regions,
                                                          Asia-Pacific countries by size — from stats.json when given)
    static/com/hero/og-world.jpg                         (only with --og: the og:image of the home, 1200×630)

Numbers on the page never come from here except the order of the Asia-Pacific countries: the counts come from the
manifest and the pages bundle at build time (scripts/world_home.py).

    python3 scripts/world_hero.py <public_sites.geojsonseq[.gz]> [--stats stats.json] [--out <repo root>] [--og] [--date D]
    python3 scripts/world_hero.py selftest

Needs numpy and Pillow (WebP; AVIF with Pillow ≥ 11.2 built with libavif). No network.
"""
import argparse
import gzip
import hashlib
import io
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NE = ROOT / 'content' / 'world' / 'home' / 'ne_lines.json'
MAX_BYTES = 150_000

# view of each picture: centre [lon, lat], MapLibre zoom (512 px tiles) at the picture's own pixel size, size [w, h].
# Wide pictures leave the left ~40 % for the text panel of the first screen, so the region sits right of the centre.
VIEWS = {
    'eu': {'w': {'c': [-1.5, 52.0], 'z': 3.80, 'size': [1920, 1080]}, 't': {'c': [14.0, 46.0], 'z': 3.08, 'size': [720, 1000]}},
    'na': {'w': {'c': [-118.0, 42.0], 'z': 3.25, 'size': [1920, 1080]}, 't': {'c': [-96.0, 33.0], 'z': 2.38, 'size': [720, 1000]}},
    'ap': {'w': {'c': [100.0, 12.0], 'z': 2.75, 'size': [1920, 1080]}, 't': {'c': [118.0, 2.0], 'z': 1.95, 'size': [720, 1000]}},
}
# countries per region (ISO 3166-1 alpha-2 as in the layer; XK = Kosovo). Anything not listed is "rest of the world".
EUROPE = set('AD AL AT AX BA BE BG BY CH CY CZ DE DK EE ES FI FO FR GB GG GI GR HR HU IE IM IS IT JE LI LT LU LV MC MD '
             'ME MK MT NL NO PL PT RO RS RU SE SI SK SM UA VA XK'.split())
NAMERICA = {'US', 'CA'}
APAC = set('AU BD BN BT CN FJ HK ID IN JP KH KR LA LK MM MN MO MV MY NC NP NZ PF PG PH PK SB SG TH TL TO TW VN VU WS '
           'KZ KG TJ TM UZ'.split())

BG = (11, 15, 23)          # --night of bv.css (#0B0F17)
LIME = (217, 244, 91)      # --volt (#D9F45B)
OLIVE = (60, 76, 14)
HOT = (246, 255, 210)
LINE = (150, 160, 182)


def region_of(cc):
    return 'eu' if cc in EUROPE else 'na' if cc in NAMERICA else 'ap' if cc in APAC else 'other'


# ------------------------------------------------------------------ projection (MapLibre: 512 px tiles)
def world_px(lon, lat, z):
    import numpy as np
    s = 512 * 2 ** z
    lat = np.clip(lat, -85.0511, 85.0511)
    x = (np.asarray(lon) + 180.0) / 360.0 * s
    r = np.radians(lat)
    y = (1 - np.log(np.tan(r) + 1 / np.cos(r)) / math.pi) / 2 * s
    return x, y


def read_points(path):
    """lon, lat arrays of the public layer (GeoJSON sequence, one Feature per line, optionally gzipped)."""
    import numpy as np
    op = gzip.open if str(path).endswith('.gz') else open
    lon, lat = [], []
    with op(path, 'rt', encoding='utf-8') as f:
        for line in f:
            line = line.strip().lstrip('\x1e')
            if not line:
                continue
            g = json.loads(line)['geometry']['coordinates']
            lon.append(g[0])
            lat.append(g[1])
    return np.array(lon, dtype=np.float64), np.array(lat, dtype=np.float64)


def blur(a, sigma):
    """Separable Gaussian blur with numpy only (no scipy on every machine)."""
    import numpy as np
    r = max(1, int(sigma * 3))
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    k /= k.sum()
    a = np.apply_along_axis(lambda v: np.convolve(v, k, mode='same'), 0, a)
    return np.apply_along_axis(lambda v: np.convolve(v, k, mode='same'), 1, a)


def lines_of(ne, keys=('b', 'c')):
    for k in keys:
        for flat in ne[k]:
            yield k, list(zip(flat[0::2], flat[1::2]))


def render(lon, lat, view, ne, scale=1.0):
    """RGB image (Pillow) of one view; scale > 1 renders a bigger picture of the same area (og image)."""
    import numpy as np
    from PIL import Image, ImageDraw
    w, h = (int(round(v * scale)) for v in view['size'])
    z = view['z'] + math.log2(scale)
    cx, cy = world_px(np.array([view['c'][0]]), np.array([view['c'][1]]), z)
    ox, oy = cx[0] - w / 2, cy[0] - h / 2
    x, y = world_px(lon, lat, z)
    x, y = x - ox, y - oy
    ok = (x >= 0) & (x < w) & (y >= 0) & (y < h)
    xi, yi = x[ok].astype(int), y[ok].astype(int)
    cnt = np.zeros((h, w), dtype=np.float64)
    np.add.at(cnt, (yi, xi), 1.0)
    core = blur(cnt, 0.75)
    glow = blur(cnt, 5.0)
    # tone map: each place is visible on its own, dense cities glow without burning out
    a = np.clip(np.log1p(core * 2.2) / math.log1p(14), 0, 1)
    g = np.clip(np.log1p(glow * 22) / math.log1p(60), 0, 1)
    img = np.empty((h, w, 3), dtype=np.float64)
    img[:] = BG
    glow_col = np.array(OLIVE, dtype=np.float64)
    img += (glow_col - np.array(BG)) * (g[..., None] * 0.95)
    lime = np.array(LIME, dtype=np.float64)
    img = img * (1 - a[..., None]) + lime * a[..., None]
    hot = np.clip((core - 3) / 25, 0, 1) ** 0.7
    img = img * (1 - hot[..., None] * 0.6) + np.array(HOT) * hot[..., None] * 0.6
    base = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), 'RGB')
    # borders and coasts: drawn at 2× on a transparent layer, scaled down (thin, anti-aliased), under the lights
    ss = 2
    lay = Image.new('L', (w * ss, h * ss), 0)
    dr = ImageDraw.Draw(lay)
    for kind, pts in lines_of(ne):
        lo = np.array([p[0] for p in pts])
        la = np.array([p[1] for p in pts])
        px, py = world_px(lo, la, z)
        px, py = (px - ox) * ss, (py - oy) * ss
        if px.max() < 0 or px.min() > w * ss or py.max() < 0 or py.min() > h * ss:
            continue
        dr.line(list(zip(px.tolist(), py.tolist())), fill=255 if kind == 'b' else 200, width=max(1, int(round(1.1 * scale))))
    lay = lay.resize((w, h), Image.LANCZOS)
    m = np.asarray(lay, dtype=np.float64)[..., None] / 255 * 0.40
    arr = np.asarray(base, dtype=np.float64)
    under = 1 - np.clip(a * 1.5, 0, 1)[..., None]          # the lights stay on top of the lines
    arr = arr * (1 - m * under) + np.array(LINE) * m * under
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), 'RGB'), int(ok.sum())


def encode(img, fmt):
    """Bytes of the picture in AVIF or WebP, the best quality that stays ≤ MAX_BYTES."""
    for q in ((60, 52, 45, 38, 32, 26) if fmt == 'avif' else (82, 74, 66, 58, 50, 42)):
        b = io.BytesIO()
        if fmt == 'avif':
            img.save(b, 'AVIF', quality=q, speed=4)
        else:
            img.save(b, 'WEBP', quality=q, method=6)
        if b.tell() <= MAX_BYTES:
            return b.getvalue(), q
    raise SystemExit(f'world_hero: {fmt} over {MAX_BYTES} bytes even at the lowest quality')


def can_avif():
    try:
        from PIL import features
        return bool(features.check('avif'))
    except Exception:
        return False


def coarse_lines(ne, tol=0.12, min_len=2.5):
    """GeoJSON (MultiLineString per kind) for the live map: fewer points, small islands dropped."""
    def dp(pts):
        if len(pts) < 3:
            return pts
        keep = [False] * len(pts)
        keep[0] = keep[-1] = True
        st = [(0, len(pts) - 1)]
        while st:
            a, b = st.pop()
            (ax, ay), (bx, by) = pts[a], pts[b]
            dx, dy = bx - ax, by - ay
            L = math.hypot(dx, dy)
            md, mi = -1.0, -1
            for i in range(a + 1, b):
                px, py = pts[i]
                d = abs(dy * (px - ax) - dx * (py - ay)) / L if L else math.hypot(px - ax, py - ay)
                if d > md:
                    md, mi = d, i
            if md > tol:
                keep[mi] = True
                st += [(a, mi), (mi, b)]
        return [p for p, k in zip(pts, keep) if k]
    feats = []
    for kind in ('b', 'c'):
        mls = []
        for _, pts in lines_of(ne, (kind,)):
            if kind == 'c' and sum(math.hypot(x2 - x1, y2 - y1) for (x1, y1), (x2, y2) in zip(pts, pts[1:])) < min_len:
                continue
            s = [[round(x, 1), round(y, 1)] for x, y in dp(pts)]
            if len(s) >= 2:
                mls.append(s)
        feats.append({'type': 'Feature', 'properties': {'k': kind}, 'geometry': {'type': 'MultiLineString', 'coordinates': mls}})
    return {'type': 'FeatureCollection', 'about': 'Natural Earth 1:50m, public domain (simplified)', 'features': feats}


def og_image(lon, lat, ne):
    """1200×630 og:image: the Europe view, wordmark-free (the page title travels with the link)."""
    v = {'c': [12.0, 50.5], 'z': 3.55, 'size': [1200, 630]}
    img, _ = render(lon, lat, v, ne)
    return img


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('sites')
    ap.add_argument('--stats')
    ap.add_argument('--out', default=str(ROOT))
    ap.add_argument('--date')
    ap.add_argument('--og', action='store_true')
    a = ap.parse_args(argv)
    out = Path(a.out)
    hero_dir = out / 'static' / 'com' / 'hero'
    meta_p = out / 'content' / 'world' / 'home' / 'hero.json'
    hero_dir.mkdir(parents=True, exist_ok=True)
    meta_p.parent.mkdir(parents=True, exist_ok=True)
    ne = json.load(open(NE, encoding='utf-8'))
    lon, lat = read_points(a.sites)
    stats = json.load(open(a.stats, encoding='utf-8')) if a.stats else None
    date = a.date or (stats or {}).get('date') or ''
    fmts = ['avif', 'webp'] if can_avif() else ['webp']
    views, files = {}, {}
    for reg, shapes in VIEWS.items():
        views[reg] = {}
        for shp, v in shapes.items():
            img, n = render(lon, lat, v, ne)
            views[reg][shp] = {'c': v['c'], 'z': v['z'], 'w': v['size'][0], 'h': v['size'][1], 'n': n}
            for fmt in fmts:
                data, q = encode(img, fmt)
                name = f'hero-{reg}-{shp}.{fmt}'
                (hero_dir / name).write_bytes(data)
                files[name] = {'bytes': len(data), 'q': q, 'v': hashlib.sha1(data).hexdigest()[:10]}
    live = json.dumps(coarse_lines(ne), separators=(',', ':'))
    (hero_dir / 'borders.json').write_text(live, encoding='utf-8')
    files['borders.json'] = {'bytes': len(live), 'v': hashlib.sha1(live.encode()).hexdigest()[:10]}
    if a.og:
        b = io.BytesIO()
        og_image(lon, lat, ne).save(b, 'JPEG', quality=84, optimize=True, progressive=True)
        (hero_dir / 'og-world.jpg').write_bytes(b.getvalue())
    if (hero_dir / 'og-world.jpg').exists():
        d = (hero_dir / 'og-world.jpg').read_bytes()
        files['og-world.jpg'] = {'bytes': len(d), 'v': hashlib.sha1(d).hexdigest()[:10]}
    meta = {'about': 'Pictures of the first screen of the world home (scripts/world_hero.py, HOME2). Views: centre [lon, lat], '
                     'MapLibre zoom at 512 px tiles for the picture size w×h; n = places inside the picture.',
            'date': date, 'places': int(len(lon)), 'formats': fmts, 'views': views, 'files': files}
    if stats and stats.get('by_country'):
        bc = stats['by_country']
        reg = {}
        for cc, n in bc.items():
            r = region_of(cc)
            reg[r] = reg.get(r, 0) + n
        meta['regions'] = reg
        meta['apac'] = [cc for cc, _ in sorted(((cc, n) for cc, n in bc.items() if cc in APAC), key=lambda x: -x[1])]
    elif meta_p.exists():   # keep the order from the last run with stats
        old = json.load(open(meta_p, encoding='utf-8'))
        for k in ('regions', 'apac'):
            if k in old:
                meta[k] = old[k]
    json.dump(meta, open(meta_p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    tot = sum(f['bytes'] for n, f in files.items() if n.startswith('hero-'))
    print(f"world hero: {len(lon)} places, {len(files)} files ({', '.join(fmts)}), pictures {tot // 1024} KB in all, "
          f"largest {max(f['bytes'] for n, f in files.items() if n.startswith('hero-')) // 1024} KB; date {date or '?'}")
    return 0


def selftest():
    import numpy as np
    ok = True
    x, y = world_px(np.array([0.0]), np.array([0.0]), 0)
    ok &= abs(x[0] - 256) < 1e-6 and abs(y[0] - 256) < 1e-6
    for reg, shapes in VIEWS.items():
        for shp, v in shapes.items():
            ok &= v['size'][0] <= 1920 and v['size'][1] <= 1080 and 1 <= v['z'] <= 6
    ok &= region_of('DE') == 'eu' and region_of('US') == 'na' and region_of('JP') == 'ap' and region_of('BR') == 'other'
    ne = json.load(open(NE, encoding='utf-8'))
    ok &= len(ne['b']) > 100 and len(ne['c']) > 100
    print('world_hero selftest:', 'OK' if ok else 'FAIL')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(selftest() if sys.argv[1:] == ['selftest'] else main(sys.argv[1:]))
