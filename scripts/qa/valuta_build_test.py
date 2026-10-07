# Display currency — the build side (docs/RUNBOOK.md 3.29): the price markup of scripts/valuta.py and how
# scripts/i18n.py keeps it out of the translation keys and puts it back into the translations. No build needed.
# Usage: python3 scripts/qa/valuta_build_test.py
import re, sys
from pathlib import Path
from markupsafe import Markup
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import valuta as v  # noqa: E402
import i18n  # noqa: E402

fails = oks = 0


def check(cond, what, detail=None):
    global fails, oks
    if cond:
        oks += 1
        print('ok   ' + what)
    else:
        fails += 1
        print('FAIL ' + what + ('' if detail is None else ' — ' + str(detail)[:400]))


def spans(html):
    return re.findall(r'<span ([^>]*)>([^<]*)</span>', str(html))


# ---------------------------------------------------------------- tokens
r = v.fx('126,67 RSD/min')
check(str(r) == '<span data-rsd="126.67" data-unit="/min" data-rate="1" class="fx-1">126,67 RSD/min</span>', 'one price: markup, rate, stacked', r)
r = v.fx('16,67 RSD/min (1.000 RSD/sat)')
check([s[1] for s in spans(r)] == ['16,67 RSD/min', '1.000 RSD/sat'] and 'fx-1' not in str(r), 'two prices in one text, inline', r)
r = v.fx('87 lokacija · 16,67–126,67 RSD/min')
check('data-rsd-lo="16.67" data-rsd-hi="126.67"' in str(r) and str(r).startswith('87 lokacija · <span'), 'range', r)
r = v.fx('760,02 RSD za 12,74 kWh ≈ 60 RSD/kWh')
check([s[1] for s in spans(r)] == ['760,02 RSD', '≈ 60 RSD/kWh'], 'a "≈" before the number belongs to the price', r)
check(str(v.fx('preračun po 117,2 RSD/€')) == 'preračun po 117,2 RSD/€', 'an exchange rate is not a price')
check(str(v.fx('570 € + PDV')) == '570 € + PDV', 'a price published in euros stays as it is')
check(str(v.fx('Wallbox 7 kW (EVD02-07RD): 43.191 RSD')).endswith('<span data-rsd="43191">43.191 RSD</span>'), 'no number taken from a model code')
r = v.fx('100 RSD/započeti sat')
check(str(r) == '<span data-rsd="100">100 RSD</span>/započeti sat', 'unknown unit stays outside the price', r)
check(str(v.fx('od 39.800 RSD')) == 'od <span data-rsd="39800" class="fx-1">39.800 RSD</span>', '"od" outside, still stacked')
check(str(v.fx(v.fx('59.000 RSD'))) == str(v.fx('59.000 RSD')), 'marking twice changes nothing')
check(str(v.fx('A & B: 5 RSD')) == 'A &amp; B: <span data-rsd="5">5 RSD</span>', 'text is escaped')
r = v.fx(Markup('<b class="pr">Growatt THOR 22 kW: 72.000 RSD</b> (bilo 118.800)'))
check(str(r) == '<b class="pr">Growatt THOR 22 kW: <span data-rsd="72000">72.000 RSD</span></b> (bilo 118.800)', 'safe HTML: only the text between tags', r)
check(str(v.fx('Besplatno')) == 'Besplatno' and v.fx(None) == '', 'no price, no markup')
check(str(v.fx_num(4.153, rate=True, text='4,15', stack=True)) == '<span data-rsd="4.153" data-rate="1" class="fx-1">4,15</span>', 'fx_num keeps the full value')

# ---------------------------------------------------------------- data-page tables
t = ('<table><thead><tr><th>Stavka</th><th>Premija (RSD)</th><th>Okvirno</th></tr></thead><tbody>'
     '<tr><td>A</td><td><strong>15.716</strong></td><td>38.000 RSD<small>PDV nije naznačen</small></td></tr>'
     '<tr><td>B 2026</td><td>1.910</td><td>prosečno oko 12.000 RSD; po kW</td></tr></tbody></table><p>9.000 RSD u tekstu</p>')
r = v.fx_tables(t)
check('<strong><span data-rsd="15716" class="fx-1">15.716</span></strong>' in r and '<span data-rsd="1910" class="fx-1">1.910</span>' in r,
      'tables: numbers under an "(RSD)" header', r)
check('<span data-rsd="38000" class="fx-1">38.000 RSD</span><small>' in r and 'oko <span data-rsd="12000">12.000 RSD</span>; po kW' in r,
      'tables: prices in cells (stacked when the price is the line)', r)
check('<p>9.000 RSD u tekstu</p>' in r and '<td>B 2026</td>' in r, 'tables: text outside the cells and other cells untouched', r)

# ---------------------------------------------------------------- i18n keys and translations
sr = '87 lokacija · <span class="fx-1" data-rate="1" data-rsd-hi="126.67" data-rsd-lo="16.67" data-unit="/min">16,67–126,67 RSD/min</span>'
key, nums = i18n.make_key(sr)
check(key == '87 lokacija · ⟦0⟧–⟦1⟧ RSD/min' and nums == ['16,67', '126,67'], 'key without the markup (attributes in any order)', key)
tr = i18n.fill('87 локаций · ⟦0⟧–⟦1⟧ RSD/мин', nums)
out = i18n.fx_rewrap(tr, i18n.fx_split(sr)[1])
check(out == '87 локаций · <span class="fx-1" data-rate="1" data-rsd-hi="126.67" data-rsd-lo="16.67" data-unit="/min">16,67–126,67 RSD/мин</span>',
      'translation: the span back around the same price, unit written differently', out)
out = i18n.fx_rewrap('760,02 RSD за 12,74 кВт·ч ≈ 60 RSD/кВт·ч', [('data-rsd="760.02"', '760,02 RSD'), ('data-rate="1" data-rsd="60" data-unit="/kWh"', '≈ 60 RSD/kWh')])
check(out == '<span data-rsd="760.02">760,02 RSD</span> за 12,74 кВт·ч <span data-rate="1" data-rsd="60" data-unit="/kWh">≈ 60 RSD/кВт·ч</span>',
      'translation: a "≈" in front of a price whose unit is written differently goes into the span (no "≈ ≈ €")', out)
out = i18n.fx_rewrap('Free', [('data-rsd="0"', '0 RSD')])
check(out == 'Free', 'a price the translation does not have: nothing breaks', out)
soup = BeautifulSoup('<p><b><span data-rsd="990" data-unit="/mes">990 RSD/мес</span></b><span data-rsd="5" data-unit="/min">5 RSD</span></p>', 'html.parser')
i18n.fx_units(soup)
u = [s.get('data-unit') for s in soup.find_all('span')]
check(u == ['/мес', None], 'data-unit follows the translated text', u)
soup = BeautifulSoup('<div class="val"><span class="fx-1" data-rsd="72000">72.000 RSD</span><small>Growatt</small></div>', 'html.parser')
roots = list(i18n.segment_roots(soup))
check(len(roots) == 1 and roots[0].name == 'div' and i18n.make_key(i18n.seg_html(roots[0]))[0] == '⟦0⟧ RSD<small>Growatt</small>',
      'a marked price keeps its element one segment (same key as before)', [r.name for r in roots])

print(f'\n{oks} passed, {fails} failed')
sys.exit(1 if fails else 0)
