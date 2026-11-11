#!/usr/bin/env bash
# Copies the Onest variable font (latin, latin-ext, cyrillic, cyrillic-ext) and Inter's Greek subset into static/assets/fonts/.
# Fonts are not committed to git; site.css references /assets/fonts/onest-<subset>-wght-normal.woff2.
set -euo pipefail
cd "$(dirname "$0")/.."
npm install --no-audit --no-fund >/dev/null
mkdir -p static/assets/fonts
for s in latin latin-ext cyrillic cyrillic-ext; do
  cp "node_modules/@fontsource-variable/onest/files/onest-${s}-wght-normal.woff2" static/assets/fonts/
done
# Greek (LANG0): Onest has no Greek; world-grek.css maps Inter's Greek subset (OFL) into the 'Onest' family, loaded on Greek pages only
cp node_modules/@fontsource-variable/inter/files/inter-greek-wght-normal.woff2 static/assets/fonts/
ls -la static/assets/fonts/
