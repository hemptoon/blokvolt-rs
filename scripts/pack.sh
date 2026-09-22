#!/usr/bin/env bash
# Build, check and pack www.blokvolt.rs for a Cloudflare Pages direct upload.
# Usage: bash scripts/pack.sh [zip path]   (default: /mnt/user-data/outputs/blokvolt-dist.zip)
# Stops on the first error (including broken internal links).
set -euo pipefail
cd "$(dirname "$0")/.."
OUT="${1:-/mnt/user-data/outputs/blokvolt-dist.zip}"
python3 -c "import jinja2, markdown, bs4" 2>/dev/null || pip install --break-system-packages -q jinja2 markdown beautifulsoup4
[ -f static/assets/fonts/onest-latin-wght-normal.woff2 ] || bash scripts/fetch_fonts.sh >/dev/null
python3 build.py
python3 scripts/check_links.py
mkdir -p "$(dirname "$OUT")"
rm -f "$OUT"
python3 - "$OUT" <<'PY'
import os, sys, zipfile
out = sys.argv[1]
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    for base, dirs, files in os.walk('dist'):
        dirs.sort()
        for f in sorted(files):
            p = os.path.join(base, f)
            z.write(p, os.path.relpath(p, 'dist'))
print(f'zip {out} {os.path.getsize(out)} bytes')
PY
