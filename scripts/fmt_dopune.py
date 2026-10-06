# -*- coding: utf-8 -*-
"""Writes content/mapa/dopune.json in its hand-kept layout: one line per field of a station, compact values,
lat + lon, net + opn and c + dc + ac (whichever follow each other) on one line. Usage: python3 scripts/fmt_dopune.py (rewrites the file in place)."""
import json
from pathlib import Path

P = Path(__file__).resolve().parent.parent / 'content' / 'mapa' / 'dopune.json'
GROUPS = [('lat', 'lon'), ('net', 'opn'), ('c', 'dc', 'ac'), ('c', 'ac'), ('c', 'dc')]


def dumps(d):
    c = lambda v: json.dumps(v, ensure_ascii=False, separators=(', ', ': '))
    out = ['{', ' "about": ' + c(d['about']) + ',', ' "checked": ' + c(d['checked']) + ',', ' "stations": {']
    ids = list(d['stations'])
    for i, sid in enumerate(ids):
        st = d['stations'][sid]
        out.append('  ' + c(sid) + ': {')
        lines, done = [], set()
        for k in st:
            if k in done:
                continue
            grp = next((g for g in GROUPS if k == g[0] and all(x in st for x in g) and list(st)[list(st).index(k):list(st).index(k) + len(g)] == list(g)), None)
            keys = grp or (k,)
            done.update(keys)
            lines.append('   ' + ', '.join(c(x) + ': ' + c(st[x]) for x in keys))
        out.append(',\n'.join(lines))
        out.append('  }' + (',' if i < len(ids) - 1 else ''))
    out += [' }', '}']
    return '\n'.join(out) + '\n'


if __name__ == '__main__':
    P.write_text(dumps(json.load(open(P, encoding='utf-8'))), encoding='utf-8')
