#!/usr/bin/env bash
# Copies the Onest variable font (latin, latin-ext, cyrillic, cyrillic-ext) into static/assets/fonts/.
# Fonts are not committed to git; site.css references /assets/fonts/onest-<subset>-wght-normal.woff2.
set -euo pipefail
cd "$(dirname "$0")/.."
npm install --no-audit --no-fund >/dev/null
mkdir -p static/assets/fonts
for s in latin latin-ext cyrillic cyrillic-ext; do
  cp "node_modules/@fontsource-variable/onest/files/onest-${s}-wght-normal.woff2" static/assets/fonts/
done
ls -la static/assets/fonts/
