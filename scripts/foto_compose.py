# -*- coding: utf-8 -*-
"""Model thumbnails for /podaci/cene-elektricnih-automobila/.

Cuts each car out of a Commons photo with IS-Net (rembg 'isnet-general-use'; BiRefNet does not fit
in this container's memory), keeps only the car, and places every one on the same 360x200 canvas:
same width, same baseline, same soft contact shadow. Output goes to static/assets/auto after
quantizing (see RUNBOOK 3.5b).

Usage: python3 scripts/foto_compose.py [slug ...]   (sources in $FOTO_SRC, default /tmp/claude-0/foto2)
Per-photo fixes live in KEEP / CUT / RED / KERNEL below — add one when a neighbour car, a stand or a
pole touches ours, and look at the result before publishing."""
import sys, json, os, time
import numpy as np, cv2
from PIL import Image, ImageFilter, ImageDraw
from rembg import remove, new_session

SRC = os.environ.get('FOTO_SRC', '/tmp/claude-0/foto2'); OUT = os.environ.get('FOTO_OUT', '/tmp/claude-0/v3'); MASKS = os.environ.get('FOTO_MASKS', '/tmp/claude-0/mask2')
W, H = 360, 200            # output canvas (displayed ~150 px wide)
CAR_W, CAR_HMAX, BASE = 0.90, 0.80, 0.905

# per-photo keep boxes (fractions of the frame) where a neighbour car or a stand touches ours
KEEP = {'skoda-enyaq-coupe': (0.05, 0, 1, 1),
        'bmw-i7': (0.12, 0, 1, 1), 'mercedes-benz-g-580': (0.03, 0, 0.93, 1)}

# regions to blank out (x0, y0, x1, y1 as fractions): parts of other cars or stands touching ours
CUT = {}
# a red car behind the silver IONIQ 6: remove red pixels in that corner only
RED = {'hyundai-ioniq-6': (0.70, 0, 1, 0.35)}
KERNEL = {'skoda-enyaq': 17, 'mercedes-benz-eqs': 13}

def car_mask(img, sess, slug=''):
    m = np.array(remove(img, session=sess, only_mask=True)).astype(np.float32) / 255.0
    if slug in KEEP:
        x0, y0, x1, y1 = KEEP[slug]; h, w = m.shape
        box = np.zeros_like(m); box[int(y0*h):int(y1*h), int(x0*w):int(x1*w)] = 1; m *= box
    if slug in RED:
        x0, y0, x1, y1 = RED[slug]; h, w = m.shape
        a_ = np.array(img).astype(int); r_, g_, b_ = a_[..., 0], a_[..., 1], a_[..., 2]
        red = (r_ > g_ + 35) & (r_ > b_ + 35)
        reg = np.zeros_like(red); reg[int(y0*h):int(y1*h), int(x0*w):int(x1*w)] = True
        red = cv2.dilate((red & reg).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
        m[red] = 0
    for (x0, y0, x1, y1) in CUT.get(slug, []):
        h, w = m.shape; m[int(y0*h):int(y1*h), int(x0*w):int(x1*w)] = 0
    hard = (m > 0.5).astype(np.uint8)
    # drop thin things attached to the car (antennas, cables, barrier tape, stand poles)
    k = KERNEL.get(slug, max(5, round(img.width / 150)))
    hard = cv2.morphologyEx(hard, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    n, lab, st, _ = cv2.connectedComponentsWithStats(hard, 8)
    if n <= 1:
        return m
    big = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    keep = (lab == big).astype(np.uint8)
    # holes inside the silhouette (glass seen as background) are filled — a car is solid from outside
    cnts, _ = cv2.findContours(keep, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    solid = np.zeros_like(keep); cv2.drawContours(solid, cnts, -1, 1, thickness=cv2.FILLED)
    solid = cv2.dilate(solid, np.ones((3, 3), np.uint8))
    a = np.where(solid > 0, np.maximum(m, (cv2.erode(solid, np.ones((5, 5), np.uint8)) > 0) * 1.0), 0.0)
    # 1 px edge tighten against halos, then a hair of feather
    a = cv2.erode(a, np.ones((2, 2), np.uint8))
    a = cv2.GaussianBlur(a, (3, 3), 0.6)
    return np.clip(a, 0, 1)

def compose(img, alpha):
    rgba = np.dstack([np.array(img), (alpha * 255).astype(np.uint8)])
    ys, xs = np.where(alpha > 0.1)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    car = Image.fromarray(rgba[y0:y1, x0:x1], 'RGBA')
    sc = min(W * CAR_W / car.width, H * CAR_HMAX / car.height)
    cw, ch = max(1, round(car.width * sc)), max(1, round(car.height * sc))
    car = car.resize((cw, ch), Image.LANCZOS)
    cx, by = (W - cw) // 2, round(H * BASE)
    canvas = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    sh = Image.new('L', (W, H), 0); d = ImageDraw.Draw(sh)
    ew, eh = cw * 0.94, max(7, ch * 0.11)
    d.ellipse([W / 2 - ew / 2, by - eh / 2, W / 2 + ew / 2, by + eh / 2], fill=92)
    sh = sh.filter(ImageFilter.GaussianBlur(7))
    shadow = Image.new('RGBA', (W, H), (17, 21, 30, 0)); shadow.putalpha(sh)
    canvas.alpha_composite(shadow)
    canvas.alpha_composite(car, (cx, by - ch))
    return canvas, (cw, ch)

if __name__ == '__main__':
    slugs = sys.argv[1:] or sorted(f[:-4] for f in os.listdir(SRC) if f.endswith('.jpg'))
    sess = new_session('isnet-general-use')
    info = {}
    for s in slugs:
        t = time.time()
        img = Image.open(f'{SRC}/{s}.jpg').convert('RGB')
        a = car_mask(img, sess, s)
        cv2.imwrite(f'{MASKS}/{s}.png', (a * 255).astype(np.uint8))
        out, size = compose(img, a)
        out.save(f'{OUT}/{s}.png')
        info[s] = {'car': size, 'secs': round(time.time() - t, 1)}
        print(s, size, info[s]['secs'], flush=True)
    os.makedirs(OUT, exist_ok=True)
