# -*- coding: utf-8 -*-
"""Display currency (RSD / EUR / USD) — the build side. docs/RUNBOOK.md 3.29, VALUTA_SPEC_2026-10-06.

The pages are always built in dinars. Structured prices get the markup of static/assets/fx.js, and the browser converts
them only when the reader chose EUR or USD (with RSD nothing changes on the page):

  <span data-rsd="126.67" data-unit="/min" data-rate="1">126,67 RSD/min</span>
  <span data-rsd-lo="16.67" data-rsd-hi="126.67" data-unit="/min" data-rate="1">16,67–126,67 RSD/min</span>

The visible text stays exactly what it was. BlokVolt sells nothing, so every sum is a reference sum (kind "ref": the
chosen currency first, the dinars after it). What gets the markup is decided here and in the templates — prices from the
data (price index, network and firm prices, wallbox models, EPS tariffs, data-page tables, calculator results); never the
prose of articles, guides and news, the media kit, legal pages or the newsletter.

  fx(text)          Jinja filter: every "<number> RSD[/unit]" in a text or HTML string gets the markup
  fx_num(v, ...)    one number as a span (the text given, or the Serbian format of v)
  fx_tables(html)   data pages: price cells of the tables (a cell that is one price, or a number under a "(RSD)" header)

scripts/i18n.py takes these spans out of the translation keys and puts them back around the same price in the
translation, so marking a price never makes a sentence untranslated.
"""
import html as _html
import re

from markupsafe import Markup, escape

# The fallback rate when no live rate is known (spec §2; the same constants are in static/assets/fx.js and worker/_worker.js
# — build.py checks that all three agree). Update with every app release.
FALLBACK = {'base': 'RSD', 'source': 'NBS srednji kurs', 'date': '2026-10-05',
            'rates': {'EUR': 117.4948, 'USD': 105.0468}, 'fetchedAt': None, 'stale': True}

# a number in the Serbian format: 1.013,36 · 126,67 · 59.000 · 43
NUM = r'\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?'
# units that belong to the price; "per something" units are rates (2 or 3 decimals after conversion)
UNITS = ('kWh', 'min', 'sat', 'h', 'km', 'l', 'mes', 'mesec', 'god', 'jed.', 'mestu')
RATE_UNITS = {'/kWh', '/min', '/sat', '/h', '/km', '/l'}
# "<number>[–<number>] RSD[/unit]"; never an exchange rate ("117,2 RSD/€")
# a "≈" right before the number belongs to the price (the conversion writes its own "≈")
TOKEN = re.compile(r'(?<![\w.,\-–])(?:[≈~]\s?)?(?P<lo>' + NUM + r')(?:\s*[–-]\s*(?P<hi>' + NUM + r'))?\s*RSD(?!\s*/\s*(?:€|\$|EUR|USD))'
                   r'(?P<unit>/(?:' + '|'.join(re.escape(u) for u in UNITS) + r'))?(?![\wčćšđž])')


def to_float(s):
    return float(s.replace('.', '').replace(',', '.'))


def sr_format(v, d=None):
    """Serbian format; decimals: as given, else 2 when the number has a fraction."""
    if d is None:
        d = 0 if abs(v - round(v)) < 0.005 else 2
    s = f'{abs(v):,.{d}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    return ('−' if v < 0 and round(abs(v), d) else '') + s


def _attr_num(v):
    return ('%.4f' % v).rstrip('0').rstrip('.')


def attrs(lo, hi=None, unit='', rate=None, stack=False):
    """The data attributes of fx.js (data-rsd or data-rsd-lo first: scripts/i18n.py finds the spans by that).
    stack: the price is the whole content of its box (a table cell, a card line) — bv.css puts the dinars under the
    converted sum there (class fx-1) instead of after it."""
    a = (f'data-rsd-lo="{_attr_num(lo)}" data-rsd-hi="{_attr_num(hi)}"' if hi is not None and hi != lo
         else f'data-rsd="{_attr_num(lo)}"')
    if unit:
        a += f' data-unit="{escape(unit)}"'
    if rate is None:
        rate = unit in RATE_UNITS
    if rate:
        a += ' data-rate="1"'
    if stack:
        a += ' class="fx-1"'
    return a


_PREFIX = re.compile(r'^(?:od|do|oko|prosečno oko)\s+')


def _whole(text):
    """The text is one price, maybe after "od" / "do" / "oko" ("od 39.800 RSD"): it can be stacked."""
    return bool(TOKEN.fullmatch(_PREFIX.sub('', _html.unescape(text).strip())))


def _wrap_text(text, stack=False):
    """Plain text (already HTML-escaped) → the same text with every price token wrapped."""
    def rep(m):
        lo = to_float(m.group('lo'))
        hi = to_float(m.group('hi')) if m.group('hi') else None
        unit = m.group('unit') or ''
        return f'<span {attrs(lo, hi, unit, stack=stack)}>{m.group(0)}</span>'
    return TOKEN.sub(rep, text)


def fx(value, stack=True):
    """Jinja filter: wrap every RSD price in a text (escaped first) or in safe HTML (only the text between tags).
    A value that is one price and nothing else gets class fx-1 (stack=False: never)."""
    if value is None:
        return ''
    if not hasattr(value, '__html__'):
        value = escape(str(value))
    s = str(value)
    if 'RSD' not in s:
        return Markup(s)
    whole = stack and '<' not in s and _whole(s)
    if whole:
        return Markup(_wrap_text(s, True))
    parts = re.split(r'(<[^>]+>)', s)
    inside = 0                                      # never inside an element that already carries the markup
    out = []
    for p in parts:
        if p.startswith('<'):
            if re.match(r'<span data-rsd', p):
                inside += 1
            elif p == '</span>' and inside:
                inside -= 1
            out.append(p)
        else:
            out.append(p if inside else _wrap_text(p))
    return Markup(''.join(out))


def fx_num(v, unit='', rate=None, d=None, text=None, rsd=False, stack=False):
    """One number as a span. `text`: the visible text (default: v in the Serbian format, + ' RSD' with rsd=True, + unit)."""
    if v is None:
        return Markup(escape(text or ''))
    if text is None:
        text = sr_format(v, d) + (' RSD' if rsd else '') + (unit if rsd else '')
    return Markup(f'<span {attrs(v, None, unit, rate, stack)}>{escape(text)}</span>')


def fx_range(lo, hi, unit='', rate=None, text='', stack=False):
    """A range as one span (the visible text as given)."""
    return Markup(f'<span {attrs(lo, hi, unit, rate, stack)}>{escape(text)}</span>')


# ---------------------------------------------------------------- tables of the data pages (/podaci/…)
_CELL = re.compile(r'(<(td|th)\b[^>]*>)(.*?)(</\2>)', re.S)
_ROW = re.compile(r'<tr\b[^>]*>.*?</tr>', re.S)
_TABLE = re.compile(r'<table\b[^>]*>.*?</table>', re.S)
_LEAD = re.compile(r'^(\s*(?:<(?:b|strong)>)?)([^<]*)(?=</(?:b|strong)>|<small|<br|$)')
_BARE = re.compile(r'^(\s*(?:<(?:b|strong)>)?)(' + NUM + r')((?:</(?:b|strong)>)?\s*)$')


def _cells(row):
    return list(_CELL.finditer(row))


def fx_tables(html):
    """Price cells of the tables on a data page: every RSD price token inside a <td>, and in a column whose header says
    "(RSD)" also a cell that is only a number ("1.910", "<strong>15.716</strong>"). Text outside tables is not touched."""
    def table(tm):
        t = tm.group(0)
        rows = _ROW.findall(t)
        if not rows:
            return t
        head = [c.group(3) for c in _cells(rows[0])] if '<th' in rows[0] else []
        rsd_cols = {i for i, h in enumerate(head) if '(RSD)' in h}

        def row(rm):
            r = rm.group(0)
            out, pos, i = [], 0, 0
            for c in _cells(r):
                out.append(r[pos:c.start()])
                inner = c.group(3)
                if c.group(2) == 'td':
                    if 'RSD' in inner:
                        lead = _LEAD.match(inner)                # "38.000 RSD<small>…</small>": the price is the cell's line
                        if lead and _whole(lead.group(2)):
                            inner = lead.group(1) + _wrap_text(lead.group(2), True) + inner[lead.end(2):]
                        else:
                            inner = str(fx(Markup(inner), stack=False))
                    elif i in rsd_cols:
                        m = _BARE.match(inner)
                        if m:
                            inner = m.group(1) + str(fx_num(to_float(m.group(2)), text=m.group(2), stack=True)) + m.group(3)
                out.append(c.group(1) + inner + c.group(4))
                pos = c.end()
                i += 1
            out.append(r[pos:])
            return ''.join(out)
        return _ROW.sub(row, t)
    return _TABLE.sub(table, html)


def text_of(span_html):
    return _html.unescape(re.sub(r'<[^>]+>', '', span_html))
