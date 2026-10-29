# The app layer of guides and news (docs/RUNBOOK.md 3.38): the validator in scripts/app_layer.py must accept a correct
# object and catch an invented number, a stale number, a wrong unit, a wrong icon, a too long line, the wrong item count,
# first person and a firm name. No build needed for the unit cases; with a built dist/ it also checks every page.
# Usage: python3 scripts/qa/app_layer_test.py
import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import app_layer as al  # noqa: E402

fails = oks = 0


def check(cond, what, detail=None):
    global fails, oks
    if cond:
        oks += 1
        print('ok   ' + what)
    else:
        fails += 1
        print('FAIL ' + what + ('' if detail is None else ' — ' + str(detail)[:400]))


PAGE = ('Krediti i lizing Raiffeisen: fiksna kamata 4,99 % u EUR za nova električna vozila. '
        'Erste: EKS 7,40 % u EUR, 8,25 % u RSD. Učešće najmanje 30 %. Subvencija od 5.000 € može biti učešće. '
        'Rok 13–84 meseca. Wallbox od 11 kW. Garancija 8 godina ili 160.000 km.')
GOOD = {
    'hero': {'value': '4,99 %', 'label': 'Raiffeisen, fiksna kamata u EUR'},
    'brief': ['Erste: EKS 7,40 % u EUR, 8,25 % u RSD', 'Subvencija od 5.000 € može biti učešće u lizingu'],
    'keys': [{'value': '30 %', 'label': 'učešće, najmanje', 'icon': 'percent'},
             {'value': '8 god.', 'label': 'ili 160.000 km', 'icon': 'battery'}],
    'bars': {'title': 'Kamate u EUR', 'items': [{'label': 'Raiffeisen', 'value': 4.99, 'display': '4,99 %', 'accent': True},
                                                {'label': 'Erste', 'value': 7.40, 'display': '7,40 %'},
                                                {'label': 'Erste RSD', 'value': 8.25, 'display': '8,25 %'}]},
    'important': 'Rok kredita je 13–84 meseca',
}


def errs(app, kind='data', text=PAGE, lang='sr'):
    return al.validate(app, lang, kind, text)


def mutate(fn):
    a = copy.deepcopy(GOOD)
    fn(a)
    return errs(a)


check(errs(GOOD) == [], 'a correct object passes', errs(GOOD))
e = mutate(lambda a: a['brief'].__setitem__(0, 'Erste: EKS 6,90 % u EUR'))
check(any('6,90' in x for x in e), 'an invented number is caught', e)
stale = PAGE.replace('4,99 %', '5,49 %')
e = errs(GOOD, text=stale)
check(any('4,99' in x for x in e), 'a number that is no longer on the page (stale) is caught', e)
e = mutate(lambda a: a['brief'].__setitem__(1, 'Subvencija od 5.000 RSD može biti učešće'))
check(any('5.000' in x for x in e), 'the right number with the wrong unit is caught', e)
e = mutate(lambda a: a['keys'][0].__setitem__('icon', 'rocket'))
check(any('icon' in x and 'rocket' in x for x in e), 'an icon outside the app set is caught', e)
e = mutate(lambda a: a['brief'].__setitem__(0, 'Erste: EKS 7,40 % u EUR, ' + 'a dugačak tekst bez kraja i bez nove informacije ' * 2))
check(any('chars >' in x for x in e), 'a too long line is caught', e)
e = mutate(lambda a: a['hero'].__setitem__('value', '4,99 % fiksno'))
check(any('hero.value' in x for x in e), 'a too long hero value is caught', e)
e = mutate(lambda a: a.__setitem__('brief', a['brief'][:1]))
check(any('brief' in x and 'items' in x for x in e), 'too few brief lines are caught', e)
e = errs(dict(GOOD, brief=GOOD['brief'] + ['Rok 13–84 meseca']), kind='news')
check(any('brief' in x and 'items' in x for x in e), 'a news brief must have exactly 2 lines', e)
e = mutate(lambda a: a['bars']['items'][1].__setitem__('value', 7.0))
check(any('is not the number of' in x for x in e), 'a bar whose value is not its display number is caught', e)
e = mutate(lambda a: a['bars']['items'][1].__setitem__('display', '7,40 RSD'))
check(any('different units' in x for x in e) or any('7,40' in x for x in e), 'bars in mixed units are caught', e)
e = mutate(lambda a: a.__setitem__('important', 'Mi preporučujemo Raiffeisen'))
check(any('"Mi"' in x or 'preporuč' in x for x in e), 'first person and recommending are caught', e)
e = mutate(lambda a: a.__setitem__('important', 'Evolako ugrađuje wallbox od 11 kW'))
check(any('firm name' in x for x in e), 'the firm behind the site is never in the app layer', e)
e = mutate(lambda a: a.__setitem__('extra', 1))
check(any('unknown field' in x for x in e), 'an unknown field is caught', e)
e = errs({'brief': ['The best price is 4,99 %', 'We like it']}, lang='en', text='4,99 %')
check(any('"best"' in x for x in e) and any('"We"' in x or '"we"' in x for x in e), 'English: "best" and "we" are caught', e)
e = mutate(lambda a: a.__setitem__('paths', [{'title': 'X', 'text': 'Y', 'url': 'https://example.com/'},
                                             {'title': 'X', 'text': 'Y', 'url': 'https://www.blokvolt.rs/en/x/'}]))
check(sum('paths[' in x and 'url' in x for x in e) == 2, 'path links outside the site or in the wrong language are caught', e)
# the number check as such
check(al.on_page('17.990', 'eur', None, 'od 17.990 € sa PDV-om'), 'number + unit on the page')
check(not al.on_page('5', None, None, 'subvencija 5.000 €'), '"5" does not match inside 5.000')
check(al.on_page('8', 'year', None, '8 godina ili 160.000 km'), '"8 god." matches "8 godina" (same unit class)')
check(al._num_value('2,4034 RSD') == 2.4034 and al._num_value('17.990 €') == 17990 and al._num_value('1.641.333') == 1641333,
      'display numbers are read the Serbian way')
# covers
c = {'image': 'punjenje-u-zgradi', 'alt': {'sr': 'Auto u garaži', 'en': 'A car in a garage', 'ru': 'Машина в гараже'}}
check(al.validate_cover(c) == [], 'a cover with existing files passes', al.validate_cover(c))
check(any('missing' in x for x in al.validate_cover(dict(c, image='nema-takve-slike'))), 'a cover without its files is caught')
check(any('alt' in x for x in al.validate_cover(dict(c, alt={'sr': 'x'}))), 'a cover without alt text in every language is caught')

# every page of the last build
dist = ROOT / 'dist'
if (dist / 'assets' / 'app' / 'v1' / 'sr' / 'guides.json').exists():
    errors, stats = al.check_dist(dist)
    check(not errors, f'the built feed: {stats["with_app"]}/{stats["docs"]} pages with an app layer, 0 errors',
          '; '.join(errors[:5]))
else:
    print('skip the built feed (no dist/; run python3 build.py)')

print(f'{oks} ok, {fails} failed')
sys.exit(1 if fails else 0)
