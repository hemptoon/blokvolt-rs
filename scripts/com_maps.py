# -*- coding: utf-8 -*-
"""Fresh station lists of the neighbouring countries for the automatic build of blokvolt.com (RUNBOOK 3.10 and 3.23).

Runs `scripts/region_map.py --fetch` (the branch region-data, refreshed by .github/workflows/region-data.yml on the 3rd of
every month) and then guards the result country by country: a list that could not be made, cannot be read or has fewer
than 80 % of the stations of the committed list is put back to the committed version (git checkout), so a broken
download never empties a map. Prints one line per country.

Used by the workflow of hemptoon/blokvolt-com (.github/workflows/deploy.yml) before scripts/gen_com.py; locally it does
the same as `python3 scripts/region_map.py --fetch` plus the guard.

Usage: python3 scripts/com_maps.py            exit code 0 (the guard never fails the build)
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCAL = ROOT / 'content' / 'com' / 'local'
COUNTRIES = ('hr', 'ba', 'me', 'al', 'xk', 'mk')
MIN_SHARE = 0.8


def count_file(path):
    try:
        return len(json.load(open(path, encoding='utf-8'))['stations'])
    except Exception:
        return None


def count_committed(rel):
    try:
        raw = subprocess.run(['git', 'show', 'HEAD:' + rel], cwd=ROOT, capture_output=True, check=True).stdout
        return len(json.loads(raw.decode('utf-8'))['stations'])
    except Exception:
        return None


def restore(rel):
    subprocess.run(['git', 'checkout', '--', rel], cwd=ROOT, check=False)


def main():
    rels = {cc: f'content/com/local/{cc}/stanice.json' for cc in COUNTRIES}
    before = {cc: count_committed(rel) for cc, rel in rels.items()}
    run = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'region_map.py'), '--fetch'], cwd=ROOT)
    for cc, rel in rels.items():
        old, new = before[cc], count_file(ROOT / rel)
        if run.returncode != 0:
            restore(rel)
            print(f'{cc}: region_map.py failed — committed list kept ({old} stations)')
        elif new is None:
            restore(rel)
            print(f'{cc}: new list unreadable — committed list kept ({old} stations)')
        elif old and new < old * MIN_SHARE:
            restore(rel)
            print(f'{cc}: {new} stations is under {int(MIN_SHARE * 100)} % of the committed {old} — committed list kept')
        else:
            print(f'{cc}: {old} → {new} stations')
    return 0


if __name__ == '__main__':
    sys.exit(main())
