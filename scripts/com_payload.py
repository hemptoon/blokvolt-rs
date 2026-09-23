# -*- coding: utf-8 -*-
"""Packs dist-com/ (built by scripts/gen_com.py) into a web-upload payload for github.com/hemptoon/blokvolt-com.

Usage: python3 scripts/com_payload.py [/mnt/user-data/outputs/.gh/com-payload.json.gz]
Writes gzip(JSON {path: {"t": text} | {"b": base64}}) with every file of dist-com/ (the upload overwrites
files with the same path; files that exist only in the repository stay — delete them in the web UI if needed)
and prints a JS snippet that checks, after the commit, that every built file matches the repository tree."""
import base64
import gzip
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / 'dist-com'
out = sys.argv[1] if len(sys.argv) > 1 else '/mnt/user-data/outputs/.gh/com-payload.json.gz'

obj, shas = {}, {}
for p in sorted(DIST.rglob('*')):
    if not p.is_file():
        continue
    rel = str(p.relative_to(DIST)).replace(os.sep, '/')
    b = p.read_bytes()
    shas[rel] = hashlib.sha1(b'blob %d\0' % len(b) + b).hexdigest()
    try:
        obj[rel] = {'t': b.decode('utf-8')}
    except UnicodeDecodeError:
        obj[rel] = {'b': base64.b64encode(b).decode()}
os.makedirs(os.path.dirname(out), exist_ok=True)
gz = gzip.compress(json.dumps(obj, ensure_ascii=False).encode('utf-8'), 9)
open(out, 'wb').write(gz)
print(f'payload {out} {len(gz)} bytes, {len(obj)} files')
digest = hashlib.sha256(''.join(f'{k}:{v}\n' for k, v in sorted(shas.items())).encode()).hexdigest()[:16]
print(f'built-files hash {digest}')
print('verify on github.com after the commit (JS):')
print("const want=" + json.dumps(shas) + ";const j=await (await fetch('https://api.github.com/repos/hemptoon/blokvolt-com/git/trees/main?recursive=1',{credentials:'omit',cache:'no-store'})).json();"
      "const have=Object.fromEntries(j.tree.filter(x=>x.type==='blob').map(x=>[x.path,x.sha]));"
      "const bad=Object.keys(want).filter(k=>have[k]!==want[k]);({checked:Object.keys(want).length, mismatched:bad})")
