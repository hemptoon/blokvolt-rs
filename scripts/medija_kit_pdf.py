# -*- coding: utf-8 -*-
"""Media kit PDFs for advertisers (docs/RUNBOOK.md 3.26).

Prints the built page /za-firme/oglasavanje/ (Serbian) and /en/za-firme/oglasavanje/ (English) from dist/ to
static/za-firme/blokvolt-medija-kit-sr.pdf and -en.pdf, A4, with the print styles in bv.css (no header, footer,
form or buttons; a line with the address for enquiries at the end). The page is the source: change the text in
templates/oglasavanje.html or the numbers in content/data/oglasavanje.json, build, run this, build again (the build
shows the PDF links only when the files exist).

  python3 build.py && python3 scripts/medija_kit_pdf.py && python3 build.py
"""
import functools
import http.server
import io
import sys
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / 'dist'
OUT = ROOT / 'static' / 'za-firme'
PAGES = {'sr': '/za-firme/oglasavanje/', 'en': '/en/za-firme/oglasavanje/'}


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def shrink(path, quality=82):
    """Chrome embeds the WebP photos losslessly (about 3 MB a PDF); re-encode them as JPEG (about 10x smaller).
    Needs pikepdf (pip install pikepdf); without it the PDF stays as Chrome wrote it."""
    try:
        import pikepdf
    except ImportError:
        print('  pikepdf is not installed: the photos stay lossless (bigger file)')
        return
    pdf = pikepdf.open(path, allow_overwriting_input=True)
    # every image stream, also those inside form XObjects (a photo under a CSS fade); soft masks stay lossless
    imgs = [o for o in pdf.objects if isinstance(o, pikepdf.Stream) and o.get('/Subtype') == pikepdf.Name.Image]
    masks = {o.SMask.objgen for o in imgs if '/SMask' in o}
    done = 0
    for raw in imgs:
        if raw.objgen in masks or raw.get('/Filter') == pikepdf.Name.DCTDecode or raw.get('/ImageMask', False):
            continue
        im = pikepdf.PdfImage(raw).as_pil_image()
        if im.mode not in ('RGB', 'L'):
            im = im.convert('RGB')
        buf = io.BytesIO()
        im.save(buf, 'JPEG', quality=quality, optimize=True)
        raw.write(buf.getvalue(), filter=pikepdf.Name.DCTDecode)
        for k in ('/DecodeParms', '/Decode'):
            if k in raw:
                del raw[k]
        raw.BitsPerComponent = 8
        done += 1
    pdf.save(path)
    print(f'  {done} photos re-encoded as JPEG')


def main():
    if not (DIST / 'za-firme' / 'oglasavanje' / 'index.html').exists():
        sys.exit('dist/za-firme/oglasavanje/ is missing: run build.py first')
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(DIST)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{srv.server_address[1]}'
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            for lang, path in PAGES.items():
                pg = b.new_page(viewport={'width': 1200, 'height': 1600})
                pg.goto(base + path, wait_until='networkidle')
                pg.evaluate("document.querySelectorAll('.consent').forEach(e => e.remove());"
                            "document.querySelectorAll('main details').forEach(d => { d.open = true; })")
                # the photos are lazy: load them all before printing, or the PDF gets empty frames
                pg.evaluate("""async () => {
                    document.querySelectorAll('img[loading=lazy]').forEach(i => { i.loading = 'eager'; });
                    await Promise.all([...document.images].map(i => i.complete ? null
                        : new Promise(r => { i.addEventListener('load', r); i.addEventListener('error', r); })));
                }""")
                pg.emulate_media(media='print')
                out = OUT / f'blokvolt-medija-kit-{lang}.pdf'
                pg.pdf(path=str(out), format='A4', print_background=True, prefer_css_page_size=True)
                pg.close()
                shrink(out)
                print(f'{out.relative_to(ROOT)}: {out.stat().st_size // 1024} KB')
            b.close()
    finally:
        srv.shutdown()


if __name__ == '__main__':
    main()
