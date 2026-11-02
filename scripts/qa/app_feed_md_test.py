"""app_feed.md(): fields that CSS shows as separate pieces don't glue together in the app feed (app 2.0, round 4a,
bug 6: "Audi Q4 e-tronPricenot publishedimporter's websitechecked 22.09.2026"). Run: python3 scripts/qa/app_feed_md_test.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bs4 import BeautifulSoup  # noqa: E402
import app_feed  # noqa: E402

PAGE = 'https://www.blokvolt.rs/elektricni-automobili/audi/'


def md(html):
    return app_feed.md(BeautifulSoup(html, 'html.parser').find(True), PAGE)


def check(html, want):
    got = md(html)
    assert got == want, f'\n got: {got!r}\nwant: {want!r}'


# a model card (templates/_auto_cards.html model_card)
check('<li class="amc"><span class="amc-b"><b class="amc-n">Audi Q4 e-tron</b>\n'
      '<span class="amc-row"><span class="amc-l">Cena</span><span class="amc-p muted">nije objavljena</span></span>'
      '<span class="amc-src"><a href="https://www.audi.rs/q4">sajt uvoznika</a><small>provereno 22.09.2026</small></span></span></li>',
      '**Audi Q4 e-tron** Cena nije objavljena [sajt uvoznika](https://www.audi.rs/q4) provereno 22.09.2026')
check('<li class="amc"><span class="amc-b"><b>Deepal S05</b><span class="amc-v">RWD Pro, 68,8 kWh</span>'
      '<span class="amc-row"><span class="amc-l">Cena od</span><span class="amc-p">33.490 €</span></span></span></li>',
      '**Deepal S05** RWD Pro, 68,8 kWh Cena od 33.490 €')
# table cells: a link with the date in <small>, a price with a note, a model with its version
check('<td><a href="https://d.rs/p.pdf">cenovnik</a><small>cenovnik 01.09.2026</small></td>',
      '[cenovnik](https://d.rs/p.pdf) cenovnik 01.09.2026')
check('<td>21.000 €<small>akcija; redovna 29.654 €</small></td>', '21.000 € akcija; redovna 29.654 €')
check('<td>Dacia Spring<span class="v">Electric 65</span></td>', 'Dacia Spring Electric 65')
# ordinary text stays as it was
check('<p>Cena je <span class="nb">5.000 €</span>, a udeo <b>3,95 %</b>.</p>', 'Cena je 5.000 €, a udeo **3,95 %**.')
check('<p>Prodavac (<span translate="no">MAXX AUTO</span>) i „<span>Charge&amp;GO</span>“.</p>',
      'Prodavac (MAXX AUTO) i „Charge&GO“.')
check('<p>the line “Checked 24.09.2026”</p>', 'the line “Checked 24.09.2026”')
check('<p><a href="/mapa/">mapa</a>, <small>sitno</small></p>', '[mapa](https://www.blokvolt.rs/mapa/), sitno')
print('app_feed md: ok')
