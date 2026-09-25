#!/usr/bin/env python3
"""Lint for Serbian site texts (Latin script, ekavica, "vi"), tuned for www.blokvolt.rs news items.

Checks: Croatian/ijekavian forms, machine-writing clichés, first person ("mi", "redakcija" — the site is impersonal),
typography (quotes, decimal comma, spaces before units), sentence length, paragraphs without a single fact,
and — for news items (content/vesti/*.md) — the front matter and the shape of the item (docs/NEWS_STYLE.md).

Usage:  python3 scripts/lint_sr.py content/vesti/2026-09-25-slug.md [more files]      (exit code 1 = errors)
        python3 scripts/lint_sr.py --all-news
Errors must be fixed before publishing; warnings are read and judged."""
import re, sys, html, glob, statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NEWS_TAGS = {'subvencije', 'punjaci', 'cene', 'modeli', 'propisi', 'struja', 'statistika', 'region'}

# Croatian / ijekavian word -> Serbian (whole words, lower case)
HR2SR = {
    'cijena': 'cena', 'cijene': 'cene', 'cijenu': 'cenu', 'vrijeme': 'vreme', 'mjesto': 'mesto', 'mjesta': 'mesta',
    'mjesec': 'mesec', 'mjesečno': 'mesečno', 'mjera': 'mera', 'mjere': 'mere', 'primjer': 'primer', 'rješenje': 'rešenje',
    'prijedlog': 'predlog', 'prijevoz': 'prevoz', 'vrijednost': 'vrednost', 'dvije': 'dve', 'prije': 'pre', 'poslije': 'posle',
    'uvjet': 'uslov', 'uvjeti': 'uslovi', 'savjet': 'savet', 'zahtjev': 'zahtev', 'zahtjevi': 'zahtevi', 'cijeli': 'ceo',
    'dio': 'deo', 'dijela': 'dela', 'riječ': 'reč', 'svijet': 'svet', 'uvijek': 'uvek', 'gdje': 'gde', 'ovdje': 'ovde',
    'tjedan': 'nedelja', 'sljedeći': 'sledeći', 'sljedeće': 'sledeće', 'posljednji': 'poslednji', 'vjerojatno': 'verovatno',
    'također': 'takođe', 'tijekom': 'tokom', 'unatoč': 'uprkos', 'ovlašten': 'ovlašćen', 'ovlašteni': 'ovlašćeni',
    'tisuća': 'hiljada', 'tisuće': 'hiljade', 'točka': 'tačka', 'točno': 'tačno', 'zrak': 'vazduh', 'tvrtka': 'firma',
    'tvrtke': 'firme', 'poduzeće': 'preduzeće', 'sustav': 'sistem', 'sustava': 'sistema', 'zaslon': 'ekran',
    'tvornica': 'fabrika', 'kat': 'sprat', 'susjed': 'komšija', 'postotak': 'procenat', 'povijest': 'istorija',
    'europski': 'evropski', 'europske': 'evropske', 'europa': 'evropa', 'općina': 'opština', 'općine': 'opštine',
    'kabel': 'kabl', 'kabela': 'kabla', 'punionica': 'stanica za punjenje', 'punionice': 'stanice za punjenje',
    'cesta': 'put', 'ceste': 'puta', 'autocesta': 'autoput', 'promet': 'saobraćaj', 'osobni': 'putnički',
    'vlastiti': 'sopstveni', 'kvaliteta': 'kvalitet', 'tko': 'ko', 'netko': 'neko', 'nitko': 'niko',
    'rujan': 'septembar', 'rujna': 'septembra', 'listopad': 'oktobar', 'listopada': 'oktobra', 'studeni': 'novembar',
    'prosinac': 'decembar', 'siječanj': 'januar', 'veljača': 'februar', 'ožujak': 'mart', 'travanj': 'april',
    'svibanj': 'maj', 'lipanj': 'jun', 'srpanj': 'jul', 'kolovoza': 'avgusta', 'trenutačno': 'trenutno',
    'redovito': 'redovno', 'plin': 'gas', 'mirovina': 'penzija', 'čimbenik': 'faktor', 'sigurnosni': 'bezbednosni',
}

# phrases typical of machine-written or PR text (substring, lower case)
CLICHES = [
    'u današnjem svetu', 'u današnje vreme', 'u ovom članku', 'u ovom tekstu', 'hajde da', 'zaronimo',
    'važno je napomenuti', 'važno je istaći', 'važno je naglasiti', 'treba napomenuti', 'vredi napomenuti',
    'imajte na umu', 'igra ključnu ulogu', 'ključnu ulogu', 'ključna uloga', 'ključni korak', 'značajan korak',
    'veliki korak', 'sveobuhvatn', 'bez sumnje', 'nesumnjivo', 'na kraju dana', 'u zaključku', 'zaključno',
    'kao što smo videli', 'kao što je pomenuto', 'u svetu električnih', 'revoluci', 'od suštinskog značaja',
    'od vitalnog značaja', 'pogledajmo', 'razmotrimo', 'istražimo', 'u nastavku', 'nadamo se', 'uživajte',
    'besprekor', 'bez napora', 'budućnost mobilnosti', 'budućnost je', 'zelena budućnost', 'eko-friendly',
    'prelazak na električn', 'sve što treba da znate', 'ultimativn', 'kompletan vodič', 'dakle,', 'stoga,',
    'izuzetno važno', 'veoma važno', 'ne zaboravite', 'zapamtite', 'naravno,', 'ostaje da se vidi',
    'vreme će pokazati', 'sve popularnij', 'sve veći broj', 'ne treba zaboraviti', 'pravi izazov',
    'otvara vrata', 'nova era', 'novo poglavlje', 'prekretnic', 'uzbudljiv', 'fascinantn', 'impresivn',
]
PATTERNS = [
    (r'\bne samo\b.{0,80}\b(već|nego) i\b', 'warn', '"ne samo … već i" — at most once, better not at all'),
    (r'\bbilo da\b.{0,60}\bili\b', 'warn', '"bilo da … ili" — cliché'),
    (r'[\U0001F300-\U0001FAFF☀-➿]', 'error', 'emoji'),
    (r'!', 'error', 'exclamation mark'),
    (r'\?(\s|$)', 'warn', 'question in the text — rhetorical questions are not used'),
    (r'\b(mi|nas|nama|naš|naša|naše|našim|redakcija|redakcije|proverili smo|pišemo|objavljujemo)\b', 'error',
     'first person / "redakcija" — the site is impersonal (docs/CONTENT_STYLE.md)'),
    (r'\bEvolako\b', 'error', 'Evolako in a news item — neutrality rule (only on /o-sajtu/ and in the marked promo box)'),
    (r'\bnezavisn\w*', 'error', 'the word "nezavisni" is not used about the site'),
]
TYPO = [
    (r'"[^"\n]{2,}"', 'straight quotes "…" — Serbian „…“'),
    (r'(?<![\d.])\d{1,3},\d{3}(?![\d,])(?!\s*(kWh|kW|%|RSD|€|km|t\b))', 'comma as thousands separator — Serbian uses a dot (125.000)'),
    (r'\b\d+\.(?!\d{3}\b)\d+\s*(kW|kWh|%|km|RSD|€)', 'decimal point — Serbian uses a comma (7,4 kW)'),
    (r'\b\d+(kW|kWh|km|RSD)\b', 'no space between number and unit (11 kW)'),
    (r'\bkwh\b|\bKWH\b|\bKwh\b', 'the unit is written kWh'),
    (r'\b(ti|tvoj\w*|tebi|tebe)\b', 'addressing with "ti" — the site uses "vi"'),
    (r'(?<=[a-zčćđšž,] )(Vi|Vaš\w*|Vam)\b', 'capital Vi/Vaš inside a sentence — lower case "vi"'),
    (r' - ', 'hyphen used as a dash — use "–" or rewrite'),
]


def front_matter(txt):
    m = re.match(r'^---\n(.*?)\n---\n(.*)$', txt, re.S)
    meta = {}
    if not m:
        return meta, txt
    for line in m.group(1).split('\n'):
        if ':' in line:
            k, v = line.split(':', 1)
            meta[k.strip()] = v.strip()
    return meta, m.group(2)


def plain_text(md):
    t = re.sub(r'<[^>]+>', ' ', md)
    t = html.unescape(t)
    t = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', t)
    t = re.sub(r'https?://\S+', ' ', t)
    t = re.sub(r'^#+\s.*$', ' ', t, flags=re.M)
    t = re.sub(r'[*_`>|]+', ' ', t)
    return t


def lint_text(text):
    errors, warns = [], []
    low = text.lower()
    words = re.findall(r"[A-Za-zČĆĐŠŽčćđšž][A-Za-zČĆĐŠŽčćđšž'\-]*", text)
    for w in words:
        if w.lower() in HR2SR:
            errors.append(f'Croatian/ijekavian "{w}" → "{HR2SR[w.lower()]}"')
    for c in CLICHES:
        if c in low:
            errors.append(f'cliché: "{c}"')
    for pat, level, note in PATTERNS:
        for m in re.finditer(pat, text, flags=re.I if level == 'warn' else 0):
            (errors if level == 'error' else warns).append(f'{note}: «{text[max(0, m.start() - 30):m.end() + 30].strip()}»')
    for pat, note in TYPO:
        for m in re.finditer(pat, text):
            warns.append(f'{note}: «{text[max(0, m.start() - 25):m.end() + 25].strip()}»')
    paras = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    for p in paras:
        if len(p) > 140 and not re.search(r'\d', p) and len(re.findall(r'(?<!^)(?<![.!?]\s)\b[A-ZČĆĐŠŽ][a-zčćđšž]{2,}', p)) == 0:
            warns.append('paragraph without a number or a name — is there a fact in it? «' + p[:80] + '…»')
    sents = [s for s in re.split(r'(?<=[.!?;:])\s+|\n+', '\n'.join(paras)) if len(s.split()) > 2]
    lens = [len(s.split()) for s in sents]
    for s in sents:
        if len(s.split()) > 28:
            warns.append(f'long sentence ({len(s.split())} words): «{s[:90]}…»')
    stats = {'words': len(words), 'sentences': len(lens), 'avg_words': round(statistics.mean(lens), 1) if lens else 0,
             'stdev': round(statistics.pstdev(lens), 1) if lens else 0}
    if lens and len(lens) >= 5 and stats['stdev'] < 3:
        warns.append(f"sentences are all about the same length (stdev {stats['stdev']}) — vary them")
    return errors, warns, stats


def lint_news(path):
    txt = Path(path).read_text(encoding='utf-8')
    meta, body = front_matter(txt)
    errors, warns = [], []
    name = Path(path).name
    if not re.match(r'^\d{4}-\d{2}-\d{2}-[a-z0-9-]+\.md$', name):
        errors.append('file name must be YYYY-MM-DD-slug.md (ASCII, lower case)')
    for k in ('title', 'lead', 'date', 'published', 'tag', 'sources'):
        if not meta.get(k):
            errors.append(f'front matter: "{k}" is missing')
    if meta.get('date') and not re.fullmatch(r'\d{2}\.\d{2}\.\d{4}', meta['date']):
        errors.append('date must be DD.MM.YYYY')
    if meta.get('published') and not re.fullmatch(r'\d{4}-\d{2}-\d{2}', meta['published']):
        errors.append('published must be YYYY-MM-DD')
    if meta.get('date') and name[:10] != '-'.join(reversed(meta['date'].split('.'))):
        warns.append('the file name date differs from "date" (the day of the news)')
    if meta.get('tag') and meta['tag'] not in NEWS_TAGS:
        errors.append(f'tag must be one of {sorted(NEWS_TAGS)}')
    if len(meta.get('title', '')) > 90:
        warns.append(f"title is long ({len(meta['title'])} chars; aim for ≤ 75)")
    if len(meta.get('lead', '').split()) > 30:
        warns.append(f"lead is long ({len(meta['lead'].split())} words; aim for ≤ 25)")
    if meta.get('description') and len(meta['description']) > 160:
        warns.append('description is longer than 160 characters')
    srcs = [s for s in (meta.get('sources') or '').split(' | ') if s.strip()]
    for s in srcs:
        if ' :: http' not in s:
            errors.append(f'source without "label :: url": {s[:60]}')
    if '## Šta to znači' not in body:
        errors.append('the section "## Šta to znači" is missing')
    e2, w2, stats = lint_text(plain_text(meta.get('title', '') + '.\n\n' + meta.get('lead', '') + '\n\n' + body))
    errors += e2
    warns += w2
    if stats['words'] < 70:
        warns.append(f"very short item ({stats['words']} words)")
    if stats['words'] > 380:
        warns.append(f"long item ({stats['words']} words; news items are 120–300 words)")
    return errors, warns, stats


def main(argv):
    files = sorted(glob.glob(str(ROOT / 'content' / 'vesti' / '*.md'))) if '--all-news' in argv else [a for a in argv if not a.startswith('--')]
    bad = 0
    for f in files:
        if '/vesti/' in f.replace('\\', '/'):
            e, w, s = lint_news(f)
        else:
            e, w, s = lint_text(plain_text(front_matter(Path(f).read_text(encoding='utf-8'))[1]))
        print(f'== {Path(f).name}: {len(e)} errors, {len(w)} warnings · {s}')
        for x in e:
            print('  ERROR', x)
        for x in w:
            print('  warn ', x)
        bad += bool(e)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
