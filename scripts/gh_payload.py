# -*- coding: utf-8 -*-
"""Prepares a GitHub web-upload payload from a git clone of hemptoon/blokvolt-rs.

Usage (inside the clone, after editing files):
    python3 scripts/gh_payload.py /mnt/user-data/outputs/.gh/payload.json.gz

Writes gzip(JSON {path: {"t": text} | {"b": base64}}) with every changed or new file
(git status), prints the file list and the expected tree hash: SHA-256 of the sorted
lines "path:blob_sha" over all files — compare it with the same hash computed from
https://api.github.com/repos/hemptoon/blokvolt-rs/git/trees/main?recursive=1 after the commit.
Deleted files are only listed (GitHub web upload cannot delete; delete them in the web UI)."""
import base64, gzip, hashlib, json, os, subprocess, sys

out = sys.argv[1] if len(sys.argv) > 1 else '/mnt/user-data/outputs/.gh/payload.json.gz'
root = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], text=True).strip()
os.chdir(root)
subprocess.check_call(['git', 'add', '-A', '--dry-run'], stdout=subprocess.DEVNULL)
status = subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=all'], text=True).splitlines()
changed, deleted = [], []
for line in status:
    code, path = line[:2], line[3:].strip().strip('"')
    if ' -> ' in path:
        path = path.split(' -> ', 1)[1]
    (deleted if 'D' in code else changed).append(path)
obj = {}
for p in changed:
    b = open(p, 'rb').read()
    try:
        obj[p] = {'t': b.decode('utf-8')}
    except UnicodeDecodeError:
        obj[p] = {'b': base64.b64encode(b).decode()}
os.makedirs(os.path.dirname(out), exist_ok=True)
gz = gzip.compress(json.dumps(obj, ensure_ascii=False).encode('utf-8'), 9)
open(out, 'wb').write(gz)

def blob_sha(b):
    return hashlib.sha1(b'blob %d\0' % len(b) + b).hexdigest()

subprocess.check_call(['git', 'add', '-A'])  # stage to respect .gitignore when listing
files = subprocess.check_output(['git', 'ls-files'], text=True).splitlines()
subprocess.check_call(['git', 'reset', '-q'])
# sort the finished lines, as the check in RUNBOOK §6 does (android/gradlew vs android/gradlew.bat sort differently)
lines = ''.join(sorted(f'{p}:{blob_sha(open(p, "rb").read())}\n' for p in files if os.path.isfile(p)))
print(f'changed {len(changed)}: {changed}')
if deleted:
    print(f'DELETED (remove manually on github.com): {deleted}')
print(f'payload {out} {len(gz)} bytes; files in tree {len(files)}; expected tree hash {hashlib.sha256(lines.encode()).hexdigest()[:16]}')
