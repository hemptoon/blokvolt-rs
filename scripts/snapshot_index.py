# -*- coding: utf-8 -*-
"""Archive the public-charging price index for the month of its `updated` date.

    python3 scripts/snapshot_index.py

Writes content/javno/indeks-arhiva/YYYY-MM.json (month, capture date, all rows as they stand).
Run it after every update of content/javno/indeks-cena.json (RUNBOOK 3.3). Running it again in the
same month overwrites that month's file, so the archive keeps the last state of each month.
From the second archived month on, build.py renders /javno-punjenje/cene/ (what changed) and one
frozen page per past month; the current month is always the live table on /javno-punjenje/#cene."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
idx = json.load(open(ROOT / 'content' / 'javno' / 'indeks-cena.json', encoding='utf-8'))
day, month, year = idx['updated'].split('.')
key = f'{year}-{month}'
out = ROOT / 'content' / 'javno' / 'indeks-arhiva' / f'{key}.json'
out.parent.mkdir(exist_ok=True)
existed = out.exists()
out.write_text(json.dumps({'month': key, 'captured': idx['updated'], 'rows': idx['rows']},
                          ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
print(('updated' if existed else 'created'), out.relative_to(ROOT), '-', len(idx['rows']), 'rows')
