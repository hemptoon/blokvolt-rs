# -*- coding: utf-8 -*-
"""The Evolako charger map (www.evolako.rs/mapa-punjaca): minify evomap.src.js and evomap.css.

    python3 scripts/evomap/build.py

Writes static/assets/embed/evomap-<first 10 hex of the file's SHA-256>.js (the same source always gives the same name)
and, for the Webflow page code (page 6abaf73484f6a5d61585b9e5, RUNBOOK 3.25):
  /tmp/evomap/footer_tag.html — the <script src=… integrity=… crossorigin> tag for the page's footer code;
  /tmp/evomap/head_style.html — the same styles as a <style> block, for the page's head code if it is ever rewritten (the
                                script injects them itself, so the head's older block can stay until then);
  scripts/evomap/build.json  — file name, SRI and size of the current build (what the page should load).
A file the live page loads is never changed or deleted: a different byte breaks its SRI and the map disappears.
Remove an old file only after the page has been published with the new tag."""
import base64, hashlib, json, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
EMBED = ROOT / 'static' / 'assets' / 'embed'
TMP = Path('/tmp/evomap')
TERSER = 'terser@5.51.2'


def mini_css(css):
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    css = re.sub(r'\s+', ' ', css)
    # no spaces around { } ; , > and after :, but keep calc(a + b) and similar
    css = re.sub(r'\s*([{};,>])\s*', r'\1', css)
    css = re.sub(r':\s+', ':', css)
    css = css.replace(';}', '}')
    return css.strip()


def main():
    src = (HERE / 'evomap.src.js').read_text(encoding='utf-8')
    r = subprocess.run(['npx', '-y', TERSER, '-c', 'passes=2', '-m', '--comments', 'false'], input=src, capture_output=True, text=True)
    if r.returncode:
        sys.exit('terser failed: ' + r.stderr[:500])
    banner = '/*! Evolako — mapa javnih punjača (evomap). Izvor: github.com/hemptoon/blokvolt-rs, scripts/evomap/evomap.src.js */\n'
    css = mini_css((HERE / 'evomap.css').read_text(encoding='utf-8'))
    # the script brings its own styles (<style id="evm-css">, added once, after the page's head code), so a change of the
    # map never needs the page's head code: the footer tag is the only thing to replace in Webflow
    inject = ('!function(){if(!document.getElementById("evm-css")){var s=document.createElement("style");s.id="evm-css";'
              's.textContent=' + json.dumps(css, ensure_ascii=False) + ';document.head.appendChild(s)}}();\n')
    js = (banner + inject + r.stdout.strip() + '\n').encode('utf-8')
    name = 'evomap-' + hashlib.sha256(js).hexdigest()[:10] + '.js'
    EMBED.mkdir(parents=True, exist_ok=True)
    f = EMBED / name
    if f.exists() and f.read_bytes() != js:
        sys.exit(f'{f} exists with other bytes')
    f.write_bytes(js)
    sri = 'sha384-' + base64.b64encode(hashlib.sha384(js).digest()).decode()
    TMP.mkdir(parents=True, exist_ok=True)
    tag = (f'<!-- Evolako — mapa javnih punjača (evomap): skripta je na blokvolt.rs. Izvor: github.com/hemptoon/blokvolt-rs, '
           f'scripts/evomap/evomap.src.js -->\n<script src="https://www.blokvolt.rs/assets/embed/{name}" integrity="{sri}" crossorigin="anonymous"></script>')
    (TMP / 'footer_tag.html').write_text(tag, encoding='utf-8')
    (TMP / 'head_style.html').write_text('<style>/* Mapa punjača — izgled (evomap) */\n' + css + '\n</style>', encoding='utf-8')
    (HERE / 'build.json').write_text(json.dumps({'file': '/assets/embed/' + name, 'sri': sri, 'bytes': len(js), 'css_chars': len(css)},
                                                ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f'{name}: {len(js)} bytes, {sri}; css {len(css)} chars -> {TMP}')


if __name__ == '__main__':
    main()
