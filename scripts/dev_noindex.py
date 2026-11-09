"""Make a built site safe as a dev preview (RUNBOOK "Dev previews"): robots.txt Disallow: /, an X-Robots-Tag header for
every path in _headers (Cloudflare Pages) and <meta name="robots" content="noindex,nofollow"> in every HTML page that
does not carry one. Cloudflare already sends X-Robots-Tag: noindex on *.pages.dev previews; this is the second lock.
Never run it on a production build.

    python3 scripts/dev_noindex.py dist dist-com
"""
import re
import sys
from pathlib import Path

META = '<meta name="robots" content="noindex,nofollow">'


def run(root):
    root = Path(root)
    (root / 'robots.txt').write_text('User-agent: *\nDisallow: /\n', encoding='utf-8')
    h = root / '_headers'
    old = h.read_text(encoding='utf-8') if h.exists() else ''
    if 'X-Robots-Tag: noindex, nofollow\n# dev' not in old:
        h.write_text(old.rstrip('\n') + ('\n' if old else '') + '/*\n  X-Robots-Tag: noindex, nofollow\n# dev preview\n', encoding='utf-8')
    n = 0
    for p in root.rglob('*.html'):
        t = p.read_text(encoding='utf-8', errors='replace')
        if re.search(r'<meta name="robots" content="[^"]*noindex', t):
            continue
        t2 = re.sub(r'<meta name="robots" content="[^"]*">\s*', '', t)
        t2 = t2.replace('<head>', '<head>\n' + META, 1)
        if t2 != t:
            p.write_text(t2, encoding='utf-8')
            n += 1
    print(f'{root}: robots.txt Disallow, _headers X-Robots-Tag, meta noindex added to {n} pages')


if __name__ == '__main__':
    for d in sys.argv[1:]:
        run(d)
