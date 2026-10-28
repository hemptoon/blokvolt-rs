#!/usr/bin/env bash
# Build, check and pack www.blokvolt.rs for a Cloudflare Pages direct upload.
# Usage: bash scripts/pack.sh [zip path]   (default: /mnt/user-data/outputs/blokvolt-dist.zip)
# Stops on the first error (including broken internal links).
set -euo pipefail
cd "$(dirname "$0")/.."
OUT="${1:-/mnt/user-data/outputs/blokvolt-dist.zip}"
# A direct upload replaces the whole site. If main moved since this clone (another session committed and deployed),
# packing from here would take that work off the site: stop, pull it in first (RUNBOOK 5, step 0). BV_PACK_FORCE=1 skips.
if [ "${BV_PACK_FORCE:-}" != "1" ] && REMOTE=$(git ls-remote origin main 2>/dev/null | cut -f1) && [ -n "$REMOTE" ]; then
  if ! git cat-file -e "$REMOTE" 2>/dev/null || ! git merge-base --is-ancestor "$REMOTE" HEAD; then
    echo "STOP: origin/main ($REMOTE) is not in this clone. Another session has committed since you cloned." >&2
    echo "      git stash -u; git fetch --depth=50 origin main; git checkout -B main FETCH_HEAD; git stash pop; rebuild; then pack." >&2
    exit 3
  fi
fi
python3 -c "import jinja2, markdown, bs4" 2>/dev/null || pip install --break-system-packages -q jinja2 markdown beautifulsoup4
[ -f static/assets/fonts/onest-latin-wght-normal.woff2 ] || bash scripts/fetch_fonts.sh >/dev/null
python3 build.py
python3 scripts/check_links.py
python3 scripts/app_layer.py --strict   # the app layer of guides and news: every number still on its page (RUNBOOK 3.36)
mkdir -p "$(dirname "$OUT")"
rm -f "$OUT"
python3 - "$OUT" <<'PY'
import hashlib, os, sys, zipfile
out = sys.argv[1]
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    for base, dirs, files in os.walk('dist'):
        dirs.sort()
        for f in sorted(files):
            p = os.path.join(base, f)
            z.write(p, os.path.relpath(p, 'dist'))
data = open(out, 'rb').read()
print(f'zip {out} {len(data)} bytes, sha256 {hashlib.sha256(data).hexdigest()[:16]}')
# The browser's file_upload tool takes at most 10 MB per file, so the deploy uploads the zip in parts
# and joins them in the page (RUNBOOK section 5, step 3). Old parts are replaced.
cf = os.path.join(os.path.dirname(out), '.cf')
os.makedirs(cf, exist_ok=True)
for f in os.listdir(cf):
    if f.startswith('part-'):
        os.remove(os.path.join(cf, f))
PART = 9_000_000
parts = [data[i:i + PART] for i in range(0, len(data), PART)]
for k, p in enumerate(parts):
    with open(os.path.join(cf, f'part-{k}'), 'wb') as fh:
        fh.write(p)
print(f'deploy parts: {len(parts)} ({cf}/part-0 ... part-{len(parts) - 1})')
PY
