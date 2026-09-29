# Nedeljni pregled — the build side of the sender (docs/RUNBOOK.md 3.27, "Sending the issues").
# 1. scripts/pregled.py on its own, in a temporary folder: the issue format and every check that stops a build, the
#    e-mail's parts, the link table and the click counter, the hash, the size limit, the translation check.
# 2. Real builds with the QA fixture issue (scripts/qa/fixtures/pregled/, text that is already in the translation memory):
#    the e-mail in sr, en and ru with nothing left in Serbian, the files the worker reads, noindex and unlisted until
#    approved, public once approved, the same hash on every build. Ends with a normal build, so dist/ is ready to pack.
#   python3 scripts/qa/pregled_build_test.py            (about a minute and a half: three builds)
#   python3 scripts/qa/pregled_build_test.py --quick    (part 1 only)
import json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'scripts'))
import markdown  # noqa: E402
from PIL import Image  # noqa: E402
import pregled as pg  # noqa: E402
import i18n  # noqa: E402

SITE = 'https://www.blokvolt.rs'
fails = []


def check(cond, what, detail=None):
    print(('ok   ' if cond else 'FAIL ') + what + ('' if cond or detail is None else f' — {str(detail)[:400]}'))
    if not cond:
        fails.append(what)


def front_matter(txt):
    """The same reading as build.py's front_matter()."""
    m = re.match(r'^---\n(.*?)\n---\n(.*)$', txt, re.S)
    meta = {}
    for line in m.group(1).split('\n'):
        if ':' in line:
            k, v = line.split(':', 1)
            meta[k.strip()] = v.strip().strip('"')
    return meta, m.group(2)


# ---------------------------------------------------------------- 1. the module, in a temporary folder
TMP = Path(tempfile.mkdtemp(prefix='bv-pregled-'))
(TMP / 'static' / 'assets' / 'pregled').mkdir(parents=True)
(TMP / 'content' / 'pregled').mkdir(parents=True)
Image.new('RGB', (1200, 630), (200, 220, 90)).save(TMP / 'static/assets/pregled/c.jpg', quality=80)
Image.new('RGB', (1200, 630), (200, 220, 90)).save(TMP / 'static/assets/pregled/c.webp', quality=80)
Image.new('RGB', (500, 260), (200, 220, 90)).save(TMP / 'static/assets/pregled/mala.jpg', quality=80)
Image.effect_noise((1400, 1400), 90).convert('RGB').save(TMP / 'static/assets/pregled/velika.jpg', quality=98)
Image.new('RGB', (1200, 630)).save(TMP / 'static/assets/pregled/png.jpg', format='PNG')
FM = {'title': 'Probni broj', 'date': '02.10.2026', 'lead': 'Uvod u broj.', 'cover': '/assets/pregled/c.jpg', 'cover_alt': 'Opis slike',
      'status': 'draft', 'send_at': '02.10.2026 08:00', 'approved_hash': ''}
BODY = '## Nedelja u tri rečenice {#uvod}\n\nPrva rečenica.\n\n## Vesti {#vesti}\n\nVest sa [mapom](/mapa/).\n\n## Cene {#cene}\n\n- Jedna cena\n- Druga\n'


def issue_md(fm=None, body=BODY, name='2026-10-02-probni-broj.md', drop=()):
    f = dict(FM, **(fm or {}))
    p = TMP / 'content' / 'pregled' / name
    p.write_text('---\n' + ''.join(f'{k}: {v}\n' for k, v in f.items() if k not in drop) + '---\n' + body, encoding='utf-8')
    return p


def parse(fm=None, body=BODY, name='2026-10-02-probni-broj.md', drop=(), qa=None):
    p = issue_md(fm, body, name, drop)
    meta, b = front_matter(p.read_text(encoding='utf-8'))
    return pg.parse(p, meta, b, TMP, qa_status=qa)


def fails_with(what, want, **kw):
    try:
        parse(**kw)
    except SystemExit as e:
        check(want in str(e), f'stops the build: {what}', str(e))
        return
    check(False, f'stops the build: {what}', 'it did not')


print('— the issue file')
x = parse()
check(x['slug'] == 'probni-broj' and x['path'] == '/pregled/probni-broj/' and x['iso'] == '2026-10-02' and x['month'] == '2026-10' and
      (x['wyear'], x['week']) == (2026, 40), 'slug from the file name, date, month, ISO week', {k: x[k] for k in ('slug', 'iso', 'month', 'week')})
check([s['id'] for s in x['sections']] == ['uvod', 'vesti', 'cene'] and x['topics'] == ['vesti', 'cene'] and x['sections'][0]['heading'] == 'Nedelja u tri rečenice',
      'sections with their topics; the intro is not a topic', x['topics'])
check(x['send_at'] == '2026-10-02T06:00:00Z' and parse({'send_at': '10.12.2026 08:00'})['send_at'] == '2026-12-10T07:00:00Z',
      'send_at in Belgrade time → UTC (summer +2, winter +1)', x['send_at'])
import datetime  # noqa: E402
from unittest import mock  # noqa: E402
with mock.patch.dict(sys.modules, {'zoneinfo': None}):
    got = [pg.belgrade_to_utc(datetime.datetime(*d)).strftime('%Y-%m-%dT%H:%M') for d in ((2026, 10, 2, 8, 0), (2026, 12, 10, 8, 0), (2026, 3, 29, 8, 0), (2026, 10, 25, 8, 0))]
check(got == ['2026-10-02T06:00', '2026-12-10T07:00', '2026-03-29T06:00', '2026-10-25T07:00'], 'without the tz database: the EU summer-time rule (last Sundays of March and October)', got)
check(x['cover']['url'].startswith('/assets/pregled/c.jpg?v=') and (x['cover']['w'], x['cover']['h']) == (1200, 630) and x['cover']['alt'] == 'Opis slike',
      'cover: versioned address, size, alt', x['cover'])
check(parse({'cover': '/assets/pregled/c.webp'})['cover']['url'].startswith('/assets/pregled/c.webp?v='), 'cover: WebP is fine too')
x2 = parse({'status': 'approved', 'approved_hash': 'A' * 64})
check(x2['approved_hash'] == 'a' * 64 and x2['status'] == 'approved', 'approved_hash is kept in lower case')
check(parse(body=BODY.replace('{#vesti}', '{#vesti-region}'))['sections'][1]['topic'] == 'vesti', 'a suffix keeps the topic: {#vesti-region} is vesti')
check(parse(body=BODY + '\n## Još vesti {#vesti-2}\n\nJoš jedna.\n')['topics'] == ['vesti', 'cene'], 'two sections of one topic')
check(parse(body='## Vesti {#vesti}\n\nSamo vesti.\n')['sections'][0]['topic'] == 'vesti', 'the intro is optional')
check(parse(qa='approved')['status'] == 'approved', 'a QA build may give a fixture another status (approved without a hash)')
fails_with('an unknown front-matter key (a typo)', 'unknown front matter: aproved_hash', fm={'aproved_hash': ''})
fails_with('a missing title', 'front matter without title', drop=('title',))
fails_with('a missing cover_alt', 'without cover_alt', drop=('cover_alt',))
fails_with('an unknown status', 'status "gotovo"', fm={'status': 'gotovo'})
fails_with('a date that is not DD.MM.YYYY', 'date "2026-10-02"', fm={'date': '2026-10-02'})
fails_with('send_at in another format', 'send_at "02.10.2026"', fm={'send_at': '02.10.2026'})
fails_with('a preview without send_at', 'send_at (DD.MM.YYYY HH:MM, Belgrade time) is needed', fm={'status': 'preview'}, drop=('send_at',))
fails_with('approved without approved_hash', 'status approved without approved_hash', fm={'status': 'approved'})
fails_with('a short approved_hash (only the 8 of the subject)', 'approved_hash: the full 64-character hash', fm={'status': 'approved', 'approved_hash': 'abcd1234'})
fails_with('a file name without date or slug', 'file name', name='probni.md')
fails_with('an upper-case slug', 'file name', name='2026-10-02-Probni.md')
fails_with('a section heading without a topic', '"## Vesti": a section starts with', body=BODY.replace(' {#vesti}', ''))
fails_with('"##Vesti" without the space', '"##Vesti {#vesti}"', body=BODY.replace('## Vesti {#vesti}', '##Vesti {#vesti}'))
fails_with('a # heading', 'a section starts with', body='# Naslov\n\n' + BODY)
fails_with('an unknown topic', '{#sport}: unknown topic', body=BODY.replace('{#cene}', '{#sport}'))
fails_with('the topic "moji" (later)', 'is not built yet', body=BODY.replace('{#cene}', '{#moji}'))
fails_with('an id used twice', '{#vesti} is used twice', body=BODY.replace('{#cene}', '{#vesti}'))
fails_with('the intro not first', '{#uvod} is the first section', body='## Vesti {#vesti}\n\nA.\n\n## Uvod {#uvod}\n\nB.\n')
fails_with('text before the first section', 'text before the first section', body='Uvodni pasus.\n\n' + BODY)
fails_with('only the intro', 'no section with a topic', body='## Uvod {#uvod}\n\nSamo uvod.\n')
fails_with('an empty section', 'section {#cene} is empty', body=BODY.split('## Cene')[0] + '## Cene {#cene}\n\n')
fails_with('a cover that does not exist', 'static/assets/pregled/nema.jpg does not exist', fm={'cover': '/assets/pregled/nema.jpg'})
fails_with('a cover of 200 KB or more', 'it must be under 200 KB', fm={'cover': '/assets/pregled/velika.jpg'})
fails_with('a cover under 600 px', '500 px wide', fm={'cover': '/assets/pregled/mala.jpg'})
fails_with('a PNG named .jpg', 'not the JPEG or WebP its name says', fm={'cover': '/assets/pregled/png.jpg'})
fails_with('a cover outside the site', 'a site path to a .jpg or .webp file', fm={'cover': 'https://example.com/a.jpg'})
fails_with('a PNG cover', 'a site path to a .jpg or .webp file', fm={'cover': '/assets/pregled/c.png'})

print('— the sections: what the e-mail can carry')
MD_EXT = ['tables', 'attr_list', 'md_in_html', 'sane_lists']       # as build.py's md_to_html


def section_fails(md, want, what):
    s = {'id': 'vesti', 'html': markdown.markdown(md, extensions=MD_EXT)}
    try:
        pg.check_section(x, s, i18n)
    except SystemExit as e:
        check(want in str(e), f'stops the build: {what}', str(e))
        return
    check(False, f'stops the build: {what}', 'it did not')


ok_md = ('Tekst sa **podebljanim**, *kosim*, `kodom` i [linkom](https://www.blokvolt.rs/mapa/), [.com](https://blokvolt.com/hr/), '
         '[putanjom](/vesti/) i [početnom](/).\n\n### Podnaslov\n\n1. prvi\n2. drugi\n\n> Citat.\n')
try:
    pg.check_section(x, {'id': 'vesti', 'html': markdown.markdown(ok_md, extensions=MD_EXT)}, i18n)
    check(True, 'paragraphs, ### subheadings, lists, quotes, bold, italics, code and links to our sites pass')
except SystemExit as e:
    check(False, 'paragraphs, ### subheadings, lists, quotes, bold, italics, code and links to our sites pass', str(e))
for href in ('http://www.blokvolt.rs/mapa/', 'https://evil.example/', 'https://blokvolt.rs/mapa/', 'https://www.blokvolt.rs', 'mailto:hello@blokvolt.com',
             '//evil.example/x', '/api/posta/tick', 'mapa/', '#vesti', 'javascript:alert(1)', 'https://www.blokvolt.rs.evil.example/'):
    section_fails(f'Vidi [ovde]({href}).', f'link "{href}"', f'link {href}')
section_fails('![slika](/assets/x.jpg)', '<img> cannot go into the e-mail', 'a picture in the text')
section_fails('| a | b |\n|---|---|\n| 1 | 2 |', '<table> cannot go into the e-mail', 'a table')
section_fails('<div>blok</div>', '<div> cannot go into the e-mail', 'raw HTML')
section_fails('Linija\n\n---\n\nlinija', '<hr> cannot go into the e-mail', 'a horizontal rule')
section_fails('- spolja\n    - unutra', 'a list inside a list', 'a nested list')
section_fails('    kod u bloku', '<pre> cannot go into the e-mail', 'a code block')

print('— the e-mail from the three pages')
CH = {'sr': 'SR', 'en': 'EN', 'ru': 'RU'}


def page(lang, x, sections):
    """A built issue page as far as the e-mail reads it (the real template: templates/pregled_broj.html)."""
    t = CH[lang]
    return (f'<html><body><div class="ph" data-bv-note><h1 data-pg="title">{t} naslov &amp; više</h1><p class="lead" data-pg="lead">{t} uvod</p></div>'
            f'<figure><img src="{x["cover"]["url"]}" alt="{t} opis" data-pg="cover"></figure><div class="prose">'
            + ''.join(f'<section class="pg-sec" id="{sid}" data-pg-topic="{sid.split("-")[0]}"><h2>{t} {sid}</h2>\n{html}\n</section>' for sid, html in sections)
            + '</div></body></html>')


SECS = [('uvod', '<p>{T} prva rečenica.</p>'),
        ('vesti', '<p>{T} vest sa <a href="{P}/mapa/">mapom</a> i <a href="https://blokvolt.com/hr/">regionom</a>.</p><ul><li>{T} jedan</li><li>{T} <b>dva</b></li></ul>'),
        ('cene', '<ol><li>{T} prvi</li><li>{T} drugi</li></ol><blockquote><p>{T} citat</p></blockquote>')]


def make_dist(x, secs=SECS, tweak=None):
    d = Path(tempfile.mkdtemp(prefix='bv-pregled-dist-'))
    for lang in ('sr', 'en', 'ru'):
        pre = '' if lang == 'sr' else '/' + lang
        base = d / pre.lstrip('/') / 'pregled'
        (base / x['slug']).mkdir(parents=True)
        body = page(lang, x, [(sid, h.replace('{T}', CH[lang]).replace('{P}', pre)) for sid, h in secs])
        (base / x['slug'] / 'index.html').write_text(tweak(lang, body) if tweak else body, encoding='utf-8')
        texts = pg.MAIL_T if lang == 'sr' else {k: CH[lang] + ' ' + v for k, v in pg.MAIL_T.items()}
        (base / 'index.html').write_text(f'<html><body><script id="bv-i18n-mail" type="application/json">{json.dumps(texts)}</script></body></html>', encoding='utf-8')
        for p in ('mapa', 'vesti'):
            (d / pre.lstrip('/') / p).mkdir(parents=True, exist_ok=True)
            (d / pre.lstrip('/') / p / 'index.html').write_text('<html></html>', encoding='utf-8')
    (d / '_redirects').write_text('/karta /mapa/ 301\n', encoding='utf-8')
    return d


def tm_for(d, x, drop=None):
    """A translation memory with every key the e-mail needs (drop: leave out the Russian of the key with this text)."""
    keys = pg.page_keys((d / 'pregled' / x['slug'] / 'index.html').read_text(encoding='utf-8'), i18n) + [i18n.text_key(v)[0] for v in pg.MAIL_T.values()]
    tm = {l: {k: l.upper() + ':' + k for k in keys} for l in ('en', 'ru')}
    if drop:
        tm['ru'].pop(next(k for k in keys if k == drop.replace('RU', 'SR')))
    return tm


def run(x, d, tm):
    rep = pg.build(d, SITE, [x], tm, i18n)
    return rep, json.loads((d / 'pregled-mail' / f'{x["slug"]}.json').read_text(encoding='utf-8'))


xp = parse({'status': 'preview'})
for s, (sid, _) in zip(xp['sections'], SECS):
    s['id'] = sid
d0 = make_dist(xp)
rep, j = run(xp, d0, tm_for(d0, xp))
L = j['langs']
check(set(L) == {'sr', 'en', 'ru'} and j['status'] == 'preview' and j['send_at'] == '2026-10-02T06:00:00Z' and j['topics'] == ['vesti', 'cene'] and
      re.fullmatch(r'[0-9a-f]{64}', j['hash']) and j['approved_hash'] == '', 'issue file: three languages, status, send_at (UTC), topics, hash', {k: j[k] for k in ('status', 'send_at', 'topics')})
check(L['en']['subject'] == 'EN naslov & više' and L['ru']['preheader'] == 'RU uvod' and [s['topic'] for s in L['sr']['sections']] == ['uvod', 'vesti', 'cene'],
      'subject and preheader from each page (plain text); sections tagged by topic', L['en']['subject'])
check(j['links'] == {'1': SITE + '/pregled/probni-broj/', '2': SITE + '/mapa/', '3': 'https://blokvolt.com/hr/', '4': SITE + '/en/pregled/probni-broj/',
                     '5': SITE + '/en/mapa/', '6': SITE + '/ru/pregled/probni-broj/', '7': SITE + '/ru/mapa/'},
      'link table: every link once, Serbian first; blokvolt.com shared by the languages', j['links'])
allh = {l: p['head_html'] + ''.join(s['html'] for s in p['sections']) + p['foot_html'] for l, p in L.items()}
hrefs = {l: re.findall(r'href="([^"]*)"', h) for l, h in allh.items()}
check(all(all(h.startswith(SITE + '/api/posta/klik?i=probni-broj&amp;l=') or h in ('{{PREFS}}', '{{UNSUB}}') for h in hs) for hs in hrefs.values()),
      'every link in the HTML goes through the click counter, except the reader\'s settings and unsubscribe', hrefs['en'])
check('klik?i=probni-broj&amp;l=5' in allh['en'] and 'klik?i=probni-broj&l=5' in ''.join(s['text'] for s in L['en']['sections']),
      'the English mail counts the English links; the text part has the same counter URLs', None)
check(all(f'src="{SITE}{xp["cover"]["url"]}"' in h and 'width="600" height="315"' in h for h in allh.values()) and 'alt="RU opis"' in allh['ru'],
      'cover: absolute versioned URL, 600 px wide, height to scale, translated alt text', None)
check('<html lang="ru">' in allh['ru'] and 'RU Nedeljni pregled · 40. nedelja 2026' in allh['ru'] and 'RU Pročitajte na sajtu' in allh['ru'],
      'the head: language, the week label ({n}, {y} filled) and the web-page link in that language', None)
check('BlokVolt · www.blokvolt.rs · hello@blokvolt.com' in L['sr']['foot_html'] and '{{PREFS}}' in L['sr']['foot_html'] and '{{UNSUB}}' in L['sr']['foot_text'] and
      pg.MAIL_T['why'] in L['sr']['foot_html'], 'the foot: why, settings and unsubscribe placeholders, the operator line', L['sr']['foot_text'])
check('<table role="presentation"' in L['sr']['sections'][1]['html'] and '&#9679;' in L['sr']['sections'][1]['html'] and '>1.</td>' in L['sr']['sections'][2]['html'] and
      'border-left:3px solid' in L['sr']['sections'][2]['html'], 'lists as tables with bullets or numbers, the quote with a rule (e-mail-safe)', None)
check('• SR jedan\n• SR dva' in L['sr']['sections'][1]['text'] and '1. SR prvi\n2. SR drugi' in L['sr']['sections'][2]['text'] and '> SR citat' in L['sr']['sections'][2]['text']
      and 'mapom (https://www.blokvolt.rs/api/posta/klik?i=probni-broj&l=2)' in L['sr']['sections'][1]['text'], 'text part: bullets, numbers, quote, link targets', L['sr']['sections'][1]['text'])
check(not re.search(r'<(script|link|style|iframe|form)\b', ''.join(allh.values())) and 'SR naslov &amp; više' in allh['sr'], 'no scripts, styles or forms; text escaped', None)
check(any(r.startswith('pregled probni-broj (preview): hash ' + j['hash']) for r in rep), 'the build prints the full hash (what the owner approves)', rep)
idx = json.loads((d0 / 'pregled-mail' / 'index.json').read_text(encoding='utf-8'))
check([i['slug'] for i in idx['issues']] == ['probni-broj'] and set(idx['issues'][0]) == {'slug', 'date', 'month', 'title', 'send_at', 'status', 'approved_hash', 'hash', 'topics'}
      and 'langs' not in idx['issues'][0], 'index.json: the issue without its text', idx['issues'][0])
check(j['hash'] == pg.content_hash(L, j['links']), 'hash = sha256 of the canonical JSON of the languages and links')
_, j2 = run(xp, d0, tm_for(d0, xp))
check(j2['hash'] == j['hash'], 'the same text: the same hash (stable)')
xs = dict(xp, status='approved', approved_hash='0' * 64)
rep_s, j3 = run(xs, d0, tm_for(d0, xp))
check(j3['hash'] == j['hash'] and any(r.startswith('WARNING pregled probni-broj: approved_hash 00000000') for r in rep_s),
      'status and approved_hash are not content (same hash); an approved_hash that differs is reported', rep_s)
d1 = make_dist(xp, tweak=lambda lang, b: b.replace('RU drugi', 'RU drugi!') if lang == 'ru' else b)
_, j4 = run(xp, d1, tm_for(d1, xp))
check(j4['hash'] != j['hash'], 'one character changed in the Russian text: another hash')
d2 = make_dist(xp, secs=[SECS[0], (SECS[1][0], SECS[1][1].replace('/mapa/', '/vesti/')), SECS[2]])
_, j5 = run(xp, d2, tm_for(d2, xp))
check(j5['hash'] != j['hash'], 'a link changed: another hash')
xq = parse({'status': 'approved'}, qa='approved')
for s, (sid, _) in zip(xq['sections'], SECS):
    s['id'] = sid
_, j6 = run(xq, d0, tm_for(d0, xq))
check(j6['approved_hash'] == j6['hash'], 'QA fixture with status approved: approved as built')
try:
    run(xp, d0, tm_for(d0, xp, drop='RU prvi'))
    check(False, 'a preview with a Russian text missing from the translation memory stops the build', 'it did not')
except SystemExit as e:
    check('ru 1' in str(e) and 'without a translation' in str(e), 'a preview with a Russian text missing from the translation memory stops the build', str(e))
xd = dict(xp, status='draft')
rep_d, _ = run(xd, d0, tm_for(d0, xp, drop='RU prvi'))
check(any(r.startswith('WARNING pregled probni-broj: the e-mail has text without a translation (en 0, ru 1)') for r in rep_d), 'a draft: only a warning', rep_d)
d3 = make_dist(xp, secs=SECS + [('punjaci', '<p>{T} ' + 'reč ' * 30000 + '</p>')])
try:
    run(xp, d3, tm_for(d3, xp))
    check(False, 'an e-mail of 100 KB or more stops the build', 'it did not')
except SystemExit as e:
    check('too big' in str(e) and 'Gmail' in str(e), 'an e-mail of 100 KB or more stops the build', str(e))
d4 = make_dist(xp, secs=[SECS[0], (SECS[1][0], SECS[1][1].replace('/mapa/', '/nema-je/')), SECS[2]])
try:
    run(xp, d4, tm_for(d4, xp))
    check(False, 'a link to a page that does not exist stops a preview', 'it did not')
except SystemExit as e:
    check('links to pages that do not exist: https://www.blokvolt.rs/nema-je/' in str(e), 'a link to a page that does not exist stops a preview', str(e))
check(pg.mail_size(L['ru']) < pg.MAIL_MAX and pg.mail_size(L['ru']) > len(L['ru']['head_html']), 'mail_size: the whole HTML with a reader\'s links')
shutil.rmtree(TMP, ignore_errors=True)
for dd in (d0, d1, d2, d3, d4):
    shutil.rmtree(dd, ignore_errors=True)
if '--quick' in sys.argv:
    print(f'\n{len(fails)} failed' if fails else '\nALL OK')
    sys.exit(1 if fails else 0)

# ---------------------------------------------------------------- 2. real builds with the QA fixture
DIST = REPO / 'dist'
FIX = 'qa-probni-broj'


def build(**envs):
    env = dict(os.environ, **{k: v for k, v in envs.items() if v is not None})
    for k, v in envs.items():
        if v is None:
            env.pop(k, None)
    r = subprocess.run([sys.executable, 'build.py'], cwd=REPO, env=env, capture_output=True, text=True)
    if r.returncode:
        print(r.stdout[-2000:], r.stderr[-3000:])
        raise SystemExit('build failed')
    return r.stdout


def left(out):
    return {m.group(1): int(m.group(2)) for m in re.finditer(r'^i18n (en|ru): \d+ segments translated, (\d+) left in Serbian', out, re.M)}


print('— a build with the fixture as a preview')
out = build(BV_QA_PREGLED_FIXTURE='1', BV_QA_PREGLED='1')
fj = json.loads((DIST / 'pregled-mail' / f'{FIX}.json').read_text(encoding='utf-8'))
check(left(out) == {'en': 0, 'ru': 0}, 'the whole site: 0 left in Serbian (en, ru)', left(out))
check(f'pregled {FIX} (preview): hash {fj["hash"]}' in out and 'pregled: 1 issues, 0 public' in out, 'the build prints the issue with its hash', None)
check(fj['status'] == 'preview' and fj['send_at'] == '2026-09-25T06:00:00Z' and fj['topics'] == ['vesti', 'cene', 'punjaci'], 'fixture file: status, send_at, topics', {k: fj[k] for k in ('status', 'send_at', 'topics')})
srt = ''.join(s['text'] for s in fj['langs']['sr']['sections'])
for lang, words in (('en', ('What it means', 'News', 'Public charging prices')), ('ru', ('Что это значит', 'Новости', 'Цены на публичную зарядку'))):
    p = fj['langs'][lang]
    t = p['head_text'] + ''.join(s['text'] for s in p['sections']) + p['foot_text']
    check(all(w in t for w in words) and not any(w in t for w in ('rečenic', 'punjač', 'Primate ovaj', 'Pročitajte', 'Odjavite')),
          f'{lang}: the e-mail is translated through the translation memory, no Serbian left', t[:300])
check('„Imam Teslu“' in srt and 'Weekly Digest · Week 39, 2026' in fj['langs']['en']['head_html'], 'sr text as written; the week label in English', None)
pg_html = (DIST / 'pregled' / FIX / 'index.html').read_text(encoding='utf-8')
check('content="noindex"' in pg_html and 'ld+json' not in pg_html, 'preview page: noindex, no structured data', None)
check(FIX not in (DIST / 'sitemap.xml').read_text() and FIX not in (DIST / 'assets' / 'search.json').read_text() and FIX not in (DIST / 'pregled' / 'index.html').read_text(),
      'preview page: not in the sitemap, the site search or „Prethodni brojevi“', None)
check(all((DIST / l / 'pregled' / FIX / 'index.html').exists() for l in ('en', 'ru')), 'preview page: also in English and Russian (the translation memory needs them)')
hd = (DIST / '_headers').read_text()
check(re.search(r'^/pregled-mail/\*\n  X-Robots-Tag: noindex, nofollow\n  Cache-Control: no-store$', hd, re.M) is not None, '_headers: /pregled-mail/* noindex, no-store', None)
check('pregled-mail' not in (DIST / 'sitemap.xml').read_text() and 'pregled-mail' not in (DIST / 'robots.txt').read_text(), 'the mail files are in no sitemap', None)
check(re.search(r'^const CFG = \{.*"pregled": true\};', (DIST / '_worker.js').read_text(), re.M) is not None, 'the worker knows the newsletter is on (CFG)', None)
for l in ('sr', 'en', 'ru'):
    size = pg.mail_size(fj['langs'][l])
    check(size < pg.MAIL_MAX, f'{l}: the whole e-mail {size // 1024} KB, under {pg.MAIL_MAX // 1024} KB')
check(all(u.startswith((SITE + '/', 'https://blokvolt.com/')) for u in fj['links'].values()), 'link table: only our two sites', fj['links'])
h1 = fj['hash']

print('— the same fixture approved')
out = build(BV_QA_PREGLED_FIXTURE='approved', BV_QA_PREGLED='1')
fj2 = json.loads((DIST / 'pregled-mail' / f'{FIX}.json').read_text(encoding='utf-8'))
check(fj2['hash'] == h1, 'another build of the same text: the same hash', [h1[:12], fj2['hash'][:12]])
check(fj2['status'] == 'approved' and fj2['approved_hash'] == fj2['hash'] and 'pregled: 1 issues, 1 public' in out, 'approved (QA: approved as built)', None)
pg_html = (DIST / 'pregled' / FIX / 'index.html').read_text(encoding='utf-8')
check('content="noindex"' not in pg_html and '"@type": "Article"' in pg_html and f'/pregled/{FIX}/' in (DIST / 'pregled' / 'index.html').read_text()
      and f'{SITE}/pregled/{FIX}/' in (DIST / 'sitemap.xml').read_text() and f'/en/pregled/{FIX}/' in (DIST / 'sitemap.xml').read_text(),
      'approved page: indexable, structured data, under „Prethodni brojevi“, in the sitemap with /en/ and /ru/', None)
check(left(out) == {'en': 0, 'ru': 0}, 'approved build: 0 left in Serbian', left(out))
out = build(BV_QA_PREGLED_FIXTURE='approved', BV_QA_PREGLED='0')
check('pregled: 1 issues, 0 public' in out and 'content="noindex"' in (DIST / 'pregled' / FIX / 'index.html').read_text(encoding='utf-8')
      and re.search(r'^const CFG = \{.*"pregled": false\};', (DIST / '_worker.js').read_text(), re.M) is not None,
      'newsletter off: even an approved issue stays noindex and unlisted; the worker knows it is off', None)

print('— a normal build')
out = build(BV_QA_PREGLED_FIXTURE=None, BV_QA_PREGLED=None)
real = sorted(p.stem[11:] for p in (REPO / 'content' / 'pregled').glob('*.md'))
check(not (DIST / 'pregled' / FIX).exists() and [i['slug'] for i in json.loads((DIST / 'pregled-mail' / 'index.json').read_text())['issues']] == real,
      'without the QA flag the fixture is not built: only the real issues (dist/ is ready to pack)', real)
check(left(out) == {'en': 0, 'ru': 0}, 'normal build: 0 left in Serbian', left(out))
print(f'\n{len(fails)} failed' if fails else '\nALL OK')
sys.exit(1 if fails else 0)
