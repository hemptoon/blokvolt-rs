# BlokVolt — maintenance runbook

How www.blokvolt.rs is kept current: what to check, where each fact lives, how to build, deploy and
commit. Written for the people and the scheduled Claude sessions that run the monthly updates.
Everything below uses only the owner's already signed-in browser; no API tokens or passwords are ever
needed or handled.

## 0. Editorial rules (short version of /metodologija/)

- Publish only public, verifiable facts, each with a source URL and a date. Copy prices literally;
  our own conversions go in parentheses (PDV 20 %, 117,2 RSD/€). If something cannot be verified,
  leave the old value, keep its old date, and mention it in the report — never guess.
- Same columns and the same rules for every firm and network, including Evolako (marked "Izdvojeno";
  who runs the site is said only on /o-sajtu/). No ratings, rankings, affiliate links or paid placements.
  Logos only identify a company: taken from its own website, shown as-is, removed on request (note in
  /metodologija/). Missing information is written as "Ne pominje se", never as "ne".
  The old label "naša ponuda" and the site-wide Evolako mentions are retired (owner's decision, 23.09.2026):
  some scheduled-task prompts still quote «naša ponuda» — follow this runbook, never bring the label back.
- Short texts: one idea per sentence, details and footnotes in `<details>` or on the source/method pages,
  no filler. `docs/CONTENT_STYLE.md` has the rules and examples.
- App screenshots and receipts: use only the price, tariff, station name, power, kWh, amount, duration
  and date. Never publish account names, e-mails, phone numbers, card digits, fiscal/receipt numbers,
  car plates or anything that shows where the owner was at what time (use the month, not the exact
  timestamp, for receipts).
- No personal names of the team anywhere in the repo or on the site.
- Site copy is Serbian (Latin script), calm and factual.
- Every public change gets a line in `content/podaci/izmene.md` (newest date section on top). The home
  page shows the three newest items of /vesti/ (3.15); `news` in `content/data/site.json` is only an old archive of site changes.
- Do not delete files (the GitHub web upload cannot delete anyway). Do not touch other sites or projects.

## 1. Setup in a fresh container

```bash
git clone https://github.com/hemptoon/blokvolt-rs && cd blokvolt-rs
pip install --break-system-packages -q jinja2 markdown beautifulsoup4 pillow playwright   # playwright only for scripts/qa
bash scripts/fetch_fonts.sh >/dev/null      # fonts are not in git
python3 scripts/due.py --ahead 15            # what is overdue / due before the next run
```

The repo is public, so cloning needs no login. Pushing from the container is not possible (no
credentials) — commits go through the owner's browser (section 6).

## 2. Where each fact lives

| Topic | File(s) | Notes |
|---|---|---|
| Last content update date | `content/data/site.json` → `updated` | Set to today (DD.MM.YYYY) on every deploy that changes content. Footer, home, sitemap `lastmod`. |
| Firm register revision date | `content/data/site.json` → `firms_checked` | Only after a full revision of all published firms. Price table, /firme/, city pages. |
| Home stats | `content/data/site.json` → `home_stats` | The first two mirror /podaci/statistika-ev-srbija/; the third (`"b": "auto:putevi"`) is filled in by `build.py` from `content/mapa/putevi-srbije.json`. |
| Fuel prices (calculator) | `content/data/kalkulator.json` → `fuel` | `date` = first day the prices apply, `valid_to`, `benzin` (BMB 95), `dizel` (evrodizel), `url`. |
| EPS tariffs, fees, taxes | `content/data/kalkulator.json` → `eps`, `checked` | Zones VT/NT without taxes, `oie`, `ee`, `akciza`, `pdv`, `snaga_rsd_kw`, `sources` (+date). |
| Public charging price for the calculator | `content/data/kalkulator.json` → `public`, `public_checked`, `public_basis`, `public_range` | `dc` = average RSD/kWh of recent DC receipts; `ac` = Charge&GO AC 22 kW per-minute price × 60 ÷ 11 kW; `public_range` = min–max RSD/kWh of the DC receipts. |
| Public charging price index | `content/javno/indeks-cena.json` | `updated`, `next_check` (a month name is fine), `rows` (schema below). |
| Price index archive | `content/javno/indeks-arhiva/YYYY-MM.json` | Written by `scripts/snapshot_index.py` (step 6 of 3.3), never edited by hand. One file per month = the last state of the index in that month. From the second month on the build adds `/javno-punjenje/cene/` (last three months side by side, changes first) and a frozen page per past month. |
| Charging networks | `content/operateri/<slug>.json` | Edit these JSON files directly. `scripts/add_operators.py` is a historical import — never re-run it. `prices` is the full dated history shown on the network page; `verified` = last check. |
| Free chargers | `content/javno/besplatni-punjaci.md`, `content/operateri/putevi-srbije.json` | The count (36 installed / 24 working) is repeated elsewhere — see sync points. |
| State motorway chargers, per charger | `content/mapa/putevi-srbije.json` | Hand copy of the three tables (images) on putevi-srbije.rs: site, road, direction, power, status (1 works, 0 does not, -1 being connected). Drives the map status, the table on `/javno-punjenje/putevi-srbije/` and the "24 od 36" stats (home, /javno-punjenje/). See 3.11. |
| Map of public chargers | `content/mapa/punjaci-ocm.json`, `punjaci-osm.json` + `scripts/map_data.py` | Open-data snapshots (OCM CC BY 4.0, OSM ODbL) made by `Scripts/make_chargers.py` in the Evolako iOS app repo; merged by `map_data.py` into `/assets/map/punjaci.json` (ODbL); prices from the index go to `/assets/map/cene.json`. See 3.11. |
| Logos | `static/assets/logos/*.png`, `content/data/logos.json`, `scripts/logos.py` | `<slug>.png` for firms, `op-<slug>.png` for networks (a network without one uses the firm logo of the same slug). See 3.12. |
| EPS tariffs page | `content/data/kalkulator.json` (+ `tarife_next_check`) | Then run `python3 scripts/gen_tarife_eps.py` — the page `/podaci/tarife-eps/` is generated, never edited by hand. Night-tariff hours per region and the single-tariff prices live in the same `eps` block. |
| Wallbox model prices | `content/data/wallbox-modeli.json` | The model-level view of the firm register: re-derive it from `content/firme/*.json` at the quarterly revision, then run `python3 scripts/gen_wallbox.py`. |
| Building-billing calculator | `content/data/kalkulator-zgrada.json` | Defaults and the MID meter price range (taken from the register); the page `/alati/racun-u-zgradi/` is a template, no generator. |
| New EV prices | `content/data/ev-modeli.json` | Then run `python3 scripts/gen_ev_modeli.py` (regenerates `/podaci/cene-elektricnih-automobila/`). Update `checked` and `next_check` in the JSON. `subsidy_eur` drives the "after subsidy" column. |
| Rentals, regional charging | `content/data/rent-carsharing.json`, `content/data/region.json` + the pages `content/podaci/rent-a-car-i-car-sharing.md`, `content/javno/region.md` | The pages are hand-written from the JSON; edit both. |
| All other data pages | `content/podaci/*.md`, `content/javno/*.md` | Front matter: `updated`, `next_check`, `modified` (ISO), `sources` (`Label :: URL | Label :: URL`). |
| City pages | `content/data/gradovi.json` | One entry per `/gradovi/<slug>/`: `aliases` matched inside a firm's `city` (a firm can belong to several cities), `regions` matched inside a firm's or operator's `coverage`, `loc`/`acc` the Serbian locative and accusative, `nt_region` one of the regions in `kalkulator.json` → `eps.nt_hours`, `note` one paragraph of local fact (HTML allowed). |
| Firms | `content/firme/<slug>.json` | `verified`, cells/verdicts, `sources`, `brands`. Leads: `"group": "L", "publish": false` (not shown). A checked lead that does not sell home chargers keeps `publish: false` and gets `excluded_reason` (one Serbian sentence) — it is then listed with the reason at the bottom of `/firme/`. |
| Register sub-hubs by type | `content/data/firme-tipovi.json` + `TYPE_RULES` in `build.py` | Texts of `/firme/ugradnja-punjaca/`, `/firme/prodaja-punjaca/`, `/firme/distributeri-punjaca/`, `/firme/solarni-integratori/`, `/firme/elektricari/` (Jinja strings: `n`, `n_firms`, `checked`, `n_price`, `n_d`, `wb_rows`, `wb_models`, `n_brands`, filter `plural`). Who is on which page is decided in `build.py` from the firm's verdicts, group and `kind` — never by hand. |
| News (/vesti/) | `content/vesti/YYYY-MM-DD-<slug>.md` | One file per item; rules and sources in `docs/NEWS_STYLE.md`, procedure 3.15. RSS `/vesti/rss.xml` and the three newest on the home page are built from the same files. |
| News photos | `content/data/foto.json`, `static/assets/img/vest-*`, `static/assets/og/foto/` | Free-licence photos with author, licence, caption, alt; tag pools for items without their own photo. Procedure 3.19. |
| Usage analytics | `content/data/site.json` → `analytics` | Cloudflare Web Analytics is switched on in the Pages project (no code); PostHog only when `posthog_key` is set. See 3.16. |
| Security headers (CSP) | `build.py`, end of file | Written to `dist/_headers` on every build; inline-script hashes are computed automatically. See 3.17. |
| English and Russian pages | `content/i18n/en.json`, `content/i18n/ru.json`, `content/i18n/STYLE.md` | Translation memory {Serbian segment: translation}. `/en/` and `/ru/` are generated from the Serbian pages at build time by `scripts/i18n.py` — never edit `dist/en` or `dist/ru`. See 3.9. |

`indeks-cena.json` row schema (one row per app + station/tariff):

```json
{"op": "chargego", "op_name": "Charge&GO", "date": "22.09.2026", "source": "aplikacija Charge&GO",
 "url": "https://chargego.rs/", "conf": "primarni izvor (aplikacija)", "where": "OMV Zemun park, Beograd",
 "charger": "DC 240 kW", "rsd_min": [126.67], "label": "126,67 RSD/min", "who": "", "assume_kw": [120, 60]}
```

- Per-minute tariff: `rsd_min` (list, one or two values) + `assume_kw` (list of realistic average powers;
  the page converts to RSD/kWh = RSD/min × 60 ÷ kW).
- Receipt: `rsd_total` + `kwh` (+ `label` like "760,02 RSD za 12,74 kWh", `op_name` "… — račun",
  `date` as a month, e.g. "septembar 2026").
- Unit tariff (Emobility Spectra): `unit_rsd` + `rsd_per_min`; it is not converted to kWh.
- When a newer value replaces a row, keep the old value as a dated entry in the network's `prices`
  list (`content/operateri/<slug>.json`) so the history stays visible.

### Sync points (numbers repeated in several places)

After changing any of these, grep and update every occurrence:

```bash
grep -rn "43–79\|36 \|radi 24\|24 od 36\|7\.155\|535\|~220\|4–7 RSD" templates content build.py | cut -c1-160
```

- DC receipt range "43–79 RSD/kWh": `templates/javno_index.html` (stat block), `content/javno/region.md`,
  `content/data/kalkulator.json` → `public_range`.
- State chargers "36 / radi 24": the home stat and the /javno-punjenje/ stat are computed from
  `content/mapa/putevi-srbije.json`; by hand: `content/operateri/putevi-srbije.json` (`network`, `card`,
  `network_short`), `content/javno/indeks-cena.json` (the putevi-srbije row), `content/javno/besplatni-punjaci.md`,
  `content/podaci/statistika-ev-srbija.md`.
- Fleet and registrations "7.155", "535": `content/podaci/statistika-ev-srbija.md`, `content/data/site.json` → `home_stats`.
- Home night tariff "kod kuće noću 4–7 RSD": `templates/javno_index.html` (follows the EPS NT prices with taxes).

## 3. Update procedures

Always start with `python3 scripts/due.py --ahead 15`. For every item it lists: open every URL in the
page's `sources`, search for news since the page's `updated` date, fix what changed, then set
`updated` (DD.MM.YYYY), `modified` (YYYY-MM-DD) and a sensible `next_check`. A page that was fully
re-checked without changes also gets the new `updated`/`next_check` dates (that is the truth: it was
checked). Log real changes in `izmene.md`.

### 3.1 Fuel (every run)

The Ministarstvo unutrašnje i spoljne trgovine publishes new maximum retail prices every Friday.
Find the latest announcement (search "cene goriva od petka" / "najviše maloprodajne cene"; RTS, N1,
Blic, 021.rs, mojnovisad.com all repeat it). Update `fuel.date`, `fuel.valid_to`, `benzin` (BMB 95),
`dizel` (evrodizel), `url`. Keep `label` unless the source changes.

### 3.2 EPS household tariffs (monthly)

Open https://www.eps.rs/cir/snabdevanje/Pages/cene.aspx and https://www.eps.rs/lat/vesti/ (price
news). If the regulated prices changed: update the three zones (VT/NT, without akciza and PDV),
`valid_from`, the source list, and the "4–7 RSD" sync point. In December check the OIE fee for the
next year (Vlada decision), the energy-efficiency fee and whether the "plava zona do 1.200 kWh" rule
(announced until the end of 2026) is extended. Set `checked` to today.

### 3.3 Public charging prices (monthly; screenshots come from the owner)

Prices of Charge&GO, Orion eMobility and Emobility Spectra are visible only inside their apps, so the
owner drops screenshots into a folder on their computer before the monthly run (the folder path and the name of its
archive subfolder are in the scheduled task prompt; new files sit in the folder root and processed
ones are moved into `<archive>/YYYY-MM/` inside it — never deleted).

1. List the folder, stage the new files into the container, look at every image (convert HEIC to PNG
   first if needed: `pip install pillow-heif`).
2. For every price screen: app, station, connector/power, tariff (RSD/min, RSD/kWh, start fee, idle fee,
   "jedinica") and the date (file date). For every receipt: station, kWh, amount, duration, month.
3. Update `indeks-cena.json` rows (same app + station → replace, old value → network `prices` history),
   `updated` = today, `next_check` = next month name. Update the network JSON `prices`, `fees`, `verified`.
4. Calculator: recompute `public` (`dc` = average RSD/kWh of the DC receipts of the last ~3 months,
   rounded; `ac` = Charge&GO AC 22 kW RSD/min × 60 ÷ 11, rounded), `public_checked`, `public_range`,
   and the `note` texts. Then the "43–79" sync points.
5. Move the processed files into `<archive>/YYYY-MM/` (mv -n, inside the same folder — no deletions).
6. `python3 scripts/snapshot_index.py` — archives the updated index as `content/javno/indeks-arhiva/YYYY-MM.json`
   (month of `updated`; a second run in the same month overwrites it). The first archive is September 2026;
   the October file makes `/javno-punjenje/cene/` and `/javno-punjenje/cene/2026-09/` appear — check both
   pages after the build, then add a line to `izmene.md` and a news item the first time. Rows are compared by
   operator + location + charger; a row carried over with the same `date` shows as "nije ponovo provereno",
   so never refresh a row's date without having seen the price again.

If no new screenshots arrived, keep the old values and dates; the report tells the owner.

Things that can be checked without the owner: whether the state chargers on motorways are still free
and which of them work (https://www.putevi-srbije.rs/index.php/en/electric-chargers — see 3.11), network
sizes and news on the operators' sites (chargego.rs, oriontelekom.rs/emobility, emobility.rs, omv.co.rs,
nis.rs, tesla.com/findus), Lidl eCharge, Parking servis Beograd.

### 3.4 Subsidies (every run until the programme closes)

`content/podaci/subvencije-2026.md`: application deadline (01.12.2026 at the time of writing), budget
used/remaining, changes to the Uredba (Sl. glasnik), list of approved dealers. Official sources first
(the ministry, paragraf.rs for the Uredba text), then media. If the amount changes, also update
`subsidy_eur` in `content/data/ev-modeli.json` and re-run `scripts/gen_ev_modeli.py`.

### 3.5 New EV prices (monthly or when `next_check` is due)

Go brand by brand through `content/data/ev-modeli.json` (importer site, price list PDF, salon page).
Change only what the importer publishes; keep promotions as separate fields as they are now. Update
`checked`, `next_check` (+~2 months), run `python3 scripts/gen_ev_modeli.py`, and check the generated
page's stat block (cheapest model, count under 30.000 €).

### 3.5b Model photos (only when a model is added or a photo is wrong)

`content/data/ev-foto.json` maps `"<brand>||<model>"` (the raw keys of `ev-modeli.json`) to
`static/assets/auto/<slug>.png` plus author, licence, licence URL, Commons file page and `v` (first 8
hex of the PNG's SHA-1 — `/assets/*` is served `immutable`, so the `src` carries `?v=` and must change
whenever the file does). `scripts/gen_ev_modeli.py` renders the thumbnail in the first table column
(a grey silhouette when a model has no photo — today JMEV Elight and EWind) and the credit list under
`## Fotografije modela`.

Rules, non-negotiable: only files from Wikimedia Commons under a free licence (CC0, CC BY, CC BY-SA),
never a press photo, a dealer photo or an image found through a search engine. Copy author and licence
exactly as the file page states them. The photo must show the model and generation in the table — the
facelift if the price list is for the facelift, the EV and not the petrol or PHEV twin, not a concept,
not an N Line when the table says N. A front three-quarter view with the whole car in frame; no rear
views, no open doors, nothing standing in front of the car.

How it was done (23.09.2026), and how to add one:
1. Choose on commons.wikimedia.org in the browser: the Commons API (`generator=search`,
   `gsrsearch=intitle:"<model>" filetype:bitmap`, `iiprop=url|size|extmetadata`) gives candidates;
   render them as a grid of 320 px thumbnails with index numbers on a blank Commons page and pick by
   eye from a screenshot. The container cannot reach wikimedia.org (proxy 403).
2. Transfer: re-encode the chosen files to 1024 px JPEG in the browser, open
   `github.com/hemptoon/blokvolt-rs/upload/<branch>` from the Commons tab through a clicked
   `<a target="_blank" rel="opener">`, and `postMessage` the blobs to it; commit to a throwaway
   branch (`hemptoon-patch-2` holds the current sources and `sources*.json`), then `git archive` it here.
3. Cut out and compose: `python3 scripts/foto_compose.py <slug>` (IS-Net). Add a `KEEP` box, `CUT`
   region, `RED` colour cut or a larger opening `KERNEL` for that slug when something else sticks to
   the car, and look at the result at display size before publishing.
4. Quantize to 256 colours with dithering and write to `static/assets/auto/<slug>.png` (~16 KB),
   recompute `v`, update the entry in `ev-foto.json`, run `gen_ev_modeli.py`.

### 3.6 Statistics (quarterly, after SAUVD/ABS figures appear)

`content/podaci/statistika-ev-srbija.md` + `home_stats` in `content/data/site.json`. MUP fleet figures
usually appear via media (RTS, 021.rs); SAUVD quarterly registration figures 3–6 weeks after a quarter.

### 3.6b Wallbox model prices (with the firm register)

Prices in `content/data/wallbox-modeli.json` are the same numbers the register carries per firm, only
organised by model. After the quarterly firm revision, walk the register's price cells again, update
the rows (brand, model, kW, price, VAT status, seller slug, note, product URL), keep `checked` and
`next_check` current and run `scripts/gen_wallbox.py`. Only add a row when the seller publishes the
price itself; "na upit" stays out of the table.

### 3.6c Adding a city page

Add an entry to `content/data/gradovi.json` — nothing else is needed: the page, the menu column
"Po gradu", the line on `/firme/` and the sitemap all come from that file. Fill `aliases` with every
spelling that appears in a firm's `city` field (a suburb that officially belongs to the city counts:
Futog and Veternik are Novi Sad), `regions` with the words firms actually use for the area
("vojvodina", "zapadna srbija") — matching is whole-word, so short ones are safe — and write `note`
as one paragraph of something true about that city only. A city with no firm of its own is fine; the
page then says so and lists the firms that cover it from elsewhere. Do not add a city just to have
the page: without a local firm, a local operator or a local fact, it repeats the neighbour's page.

### 3.6d Open data (/preuzimanje/)

Nothing to maintain: `scripts/open_data.py` rebuilds the five CSV files from the same objects the
pages use, on every build. When a dataset gains a column, add it there and to `DL_META` in `build.py`
(title, description, update cadence) — the page, the JSON-LD `Dataset` blocks and the sitemap follow.
Keep the promise the page makes: every row carries its source URL and check date, an unpublished
value stays empty rather than estimated, and numbers are written with a comma decimal mark because
the delimiter is a semicolon (Serbian Excel opens that without an import wizard).

### 3.6e Register sub-hubs by type (/firme/<tip>/)

Five pages cut the same register by what the reader needs: firms that say they install
(`verdicts.ugradnja` is "Da…" or "Na upit"), firms that publish a device price (groups A–C),
distributors (`kind` distributer), solar integrators (`kind` solar) and electricians (`kind`
elektricar). Membership follows the data on every build, so a firm edited at the revision moves by
itself. The distributors page also carries the brand index — every value of `brands` across the
register, with the firms that name it. A new hub needs an entry in `firme-tipovi.json`, a rule in
`TYPE_RULES` and at least three firms; a slug must not collide with a firm slug (the build stops if
it does). Numbers in the texts go through `plural` (1 firma / 2 firme / 5 firmi — and 51 is "51 firma").

`brands` lists only the makes the firm's own site names for sale or installation — not "servis ABB",
not a model name whose make is unclear, not the generic word "wallbox". Keep it in step with `offer`
and with the seller rows in `wallbox-modeli.json` (same spelling: "Schneider Electric", "Union (Vestel)").

### 3.7 Firm register (quarterly revision)

For every published `content/firme/*.json`: open the firm's site and price pages from `sources`,
compare every cell, update values and `verified`. A site that is down twice in a row: note it in the
report, do not unpublish silently. Update `brands` together with `offer`. Leads (`group` L, none open
since 23.09.2026): verify with the same columns in a real browser; publish (`publish: true`, proper
group) only when the firm's own site confirms what it sells, otherwise set `excluded_reason`. Never
contact firms to verify — no calls, e-mails or forms to firms or operators without a separate,
explicit go-ahead from the owner (decision of 23.09.2026).
After the full pass set `firms_checked` in `content/data/site.json`, log in `izmene.md`, add a news item.
In the same quarterly run refresh blokvolt.com (section 3.10): the five country files, the four facts per country and the check date, then build and publish it.

### 3.8 Site search index

`build.py` writes `dist/assets/search.json` from the generated pages (title, description, section,
headings and the first 1.200 characters of body text) and `/pretraga/` searches it in the browser.
Nothing to maintain by hand — but if a page should be findable by a word that is not in its text,
put that word in the page's description.

### 3.9 English and Russian versions (every run that changes text)

`/en/` and `/ru/` are made by `build.py` from the finished Serbian pages (`scripts/i18n.py`). Every piece
of running text, every visible attribute (alt, title, aria-label, placeholder), the title, the
descriptions and the JSON-LD names are looked up in the translation memory `content/i18n/en.json` /
`ru.json` ({Serbian: translation}). Numbers with separators (dates, prices, decimals) become
placeholders `⟦0⟧`, so a new price or date needs no new translation; a changed sentence does. Text
without a translation stays Serbian on the EN/RU page — nothing breaks — and the build prints it:

```
i18n en: 27147 segments translated, 0 left in Serbian (0 distinct)
```

After every content change:

1. `python3 scripts/i18n.py todo` — writes `content/i18n/todo-en.json` and `todo-ru.json` (key = the
   Serbian segment, value = the first page it is on) and prints the counts.
2. Up to ~150 segments: translate them yourself, following `content/i18n/STYLE.md` (same tags and
   attributes, keep `⟦n⟧` and `{name}` placeholders and entities, numbers as written, proper names
   unchanged, the terminology table, the offer's package names). Write `{key: translation}` with the
   keys copied exactly from the todo file to a scratch JSON per language, then
   `python3 scripts/i18n.py add en <file>` and `python3 scripts/i18n.py add ru <file>`. Rejected lines
   are printed with the reason — fix them and add again.
3. More than that (a new section, many new pages): `python3 scripts/i18n.py batches 28000` writes
   `content/i18n/work/batch-NN.json` ({id, page, sr, en}); translate each batch into
   `content/i18n/work/out-NN-<lang>.json` ({id: translation}) — parallel subagents, one batch each,
   English first so the Russian pass gets `en` as a reference — check each with
   `python3 scripts/i18n.py check <lang> <batch> <out>` and merge with `python3 scripts/i18n.py merge <lang>`.
   `content/i18n/work/` is scratch and not committed.
4. Rebuild (`bash scripts/pack.sh`). Both "left in Serbian" counts should be 0 before deploying. If a run
   has no time for translation, deploy anyway and list the leftovers in the report — those pages show
   the Serbian sentence until the next run.
5. Now and then `python3 scripts/i18n.py prune` drops translations of Serbian text that is gone.

An element whose text sits next to an inline SVG icon (buttons, chips: `<a class="btn"><svg…>Mapa punjača</a>`)
is one segment without the icon; the icon is put back before (or after) the translated text.

A block that exists in one language only (for example links to a Russian-language guide for newcomers on three
/ru/ pages) is written in the Serbian source as `<aside … data-only="ru" lang="ru" translate="no">…</aside>` in the
target language; after translation `build.py` removes it from the other languages (`strip_lang_only`).

Not segments: JavaScript texts live in `<script id="bv-i18n" type="application/json">` blocks in the
templates (calculators, search). Plain strings there are translated like any segment; objects keyed by
`sr`/`en`/`ru` (plural forms, month names, quotation marks) are edited in the template itself. Elements
with `translate="no"` (logo, language menu) are left alone. CSV downloads stay Serbian. Links to
evolako.rs get `?lang=en|ru`.

### 3.10 blokvolt.com — the English regional guide (quarterly, or when a country's facts change)

blokvolt.com has eight pages: home, Serbia (a short summary that links to blokvolt.rs/en/), Montenegro,
Bosnia and Herzegovina, North Macedonia, Croatia, Slovenia, "For companies and suppliers" and a 404.
They are generated by `python3 scripts/gen_com.py` into `dist-com/` (not committed here) from:

- `content/com/site.json` — country order and slugs, the four short facts per country (home cards and the
  "at a glance" row, in the order fleet · public charging · subsidies · home chargers), the Serbia summary
  and its links, the check date.
- `content/com/research/<CODE>.json` — one verified fact file per country (ME, BA, MK, HR, SI): `summary`,
  `stats`, `home_companies`, `home_price_ranges`, `public_count`, `networks` (with `prices`), `electricity`,
  `subsidies` (`status` open / closed / none / unconfirmed), `buildings`, `policy`, `gaps`. Every fact carries
  `source`, `source_title`, `source_date` and `confidence` (high = primary source, medium = media quoting one,
  low = estimate or dealer opinion). Texts are plain English; prices exactly as published.

Refresh: one research subagent per country, told to verify and extend the existing file (same schema, WebSearch
and WebFetch only, no workarounds for blocked sites, no ratings, Evolako and BlokVolt excluded). Then update the
four facts in `site.json` and `checked`/`checked_iso`, build, and look at the pages (desktop and phone).
The design is the old one of blokvolt.rs (`static/assets/site.css`, `agg.css`, `site.js`, `meganav.js` —
kept only for blokvolt.com; blokvolt.rs uses `bv.css`/`bv.js`) plus `static/com/com.css`;
`scripts/og_com.py` renders the share image `static/com/og-en.png`.

Publish (GitHub Pages, repository `hemptoon/blokvolt-com`, branch `main`, root):
`python3 scripts/com_payload.py` → upload `/mnt/user-data/outputs/.gh/com-payload.json.gz` at
`https://github.com/hemptoon/blokvolt-com/upload/main` with the same helper input and unpack snippet as in
section 6 (steps 3–6), then run the verification snippet the script prints — it compares every built file with
the repository tree. Files that exist only in the repository are not removed by an upload.

DNS (Spaceship, blokvolt.com): four A records `@` → 185.199.108.153 / 109 / 110 / 111, CNAME `www` →
`hemptoon.github.io`, TXT `_github-pages-challenge-hemptoon` (GitHub domain verification) and TXT `@`
`google-site-verification=…` (Search Console, property `sc-domain:blokvolt.com`) — keep all of them; the Spacemail
records (MX, SPF, DKIM, SRV, `_dmarc`) belong to the mailbox and are never touched.

### 3.11 Map of public chargers (/mapa/) and the state motorway chargers (monthly)

Stations: two open snapshots in `content/mapa/` — `punjaci-ocm.json` (Open Charge Map) and
`punjaci-osm.json` (OpenStreetMap). They are made by `Scripts/make_chargers.py` in the Evolako iOS app
repository (it has the network access and the OCM key); that repository is read-only for BlokVolt runs —
ask the owner for fresh copies, or keep the old ones and say so in the report. `scripts/map_data.py`
merges them (docstring: same-site rules, network names, Lidl free only on Liman, bicycle chargers dropped)
into `dist/assets/map/punjaci.json`; the page loads it with `?v=<hash>`.

State chargers (monthly): open the source page, read the three tables (they are images:
`elektro-punjaci-u-funkciji-lat.png`, `…-u-postupku-prikljucenja-lat.png`, `planirani-elektropunjaci-lat.png`
under `/images/putarine/`) and update `content/mapa/putevi-srbije.json`: status per charger, new chargers,
`checked`. A site listed in `ids` takes its name, road, power and status from this file; a working site
missing from both snapshots is added at `lat`/`lon` = the toll plaza or rest area in OpenStreetMap (`pos`
= that OSM element — find it with Overpass/Nominatim from the browser, never guess). The build prints
`putevi-srbije.json: station … is not in the open data any more` when a snapshot dropped a listed id —
fix `ids` then. After the update: the "radi 24 od 36" sync points (2), `izmene.md`, and the EN/RU todo —
counts are part of some segments ("185 javnih punjača…", "Na mapi (22)", "24 od 36"), so a new number
means a new translation.

Checks after the build: `/mapa/` list count, `/mapa/?mreza=putevi-srbije`, a card with status
(`/mapa/#<id>`), `/javno-punjenje/putevi-srbije/` table. MapLibre does not render in a hidden browser tab;
to test the layers in the container, run Playwright with the style and glyph URLs of tiles.openfreemap.org
routed to a tiny local style (the container cannot reach OpenFreeMap).

#### 3.11b Checking every charger (monthly, with the snapshots)

Rule: a charger is **confirmed** only when a network's own list has it at that place, or when it exists on
Google Maps with a driver rating from the last 12 months. Everything else is shown as „Nije potvrđeno“
(or „Prijavljen kvar“ when recent reviews say it does not work). Nothing is copied from Google (no text,
summary, photo or rating) — only our conclusion and the date.

Inputs in `content/mapa/mreze/` (dates in `izvori.json`, change them when a list is refreshed):
- `chargego-raw.txt` — Charge&GO's public map (client.chargego.rs, the `data-locations` attribute),
  `id|lat|lon|name|street|city|access|icon|connectors`; `access=test` and Skopje are skipped.
- `roaming-raw.txt` — the roaming layer of the same portal (Hubject: RS*ORI = Orion eMobility, also the
  state chargers; RS*007/RO*PLG = network not published), `lat|lon|op|n|statuses|date|name|street|city|plugs|power`.
- `tesla.json` — Tesla's own lists of Superchargers and Destination chargers (tesla.com/sl_SI/findus/list/…).
- `content/mapa/provera.json` — the hand check: `x` (remove, with the reason), `dup` (join into another
  station), `fix` ([lat, lon] from a network's list), `g` = `g` / `g_old` / `g_none` / `prob` for stations
  on no list (Google check). Stations missing from this file and from the lists count as `g_none`.

`map_data.verify()` matches every open-data station to the nearest official site of a compatible network
(250 m same network, 150 m host network such as OMV/NIS, 100 m unknown network), joins open-data duplicates
of one site, adds official sites the open data lacks (ids `cg-…`, `rm-…`, `te-…`; state-charger roaming
records are never added — they come from `putevi-srbije.json`), and writes two files: `punjaci.json`
(ODbL, open data + `v` flags) and `mreze.json` (the networks' connectors/names for matched stations and the
added stations; not open data). The browser joins them. The build's counts (240 stations, "Potvrđeno: 176")
come from the joined list.

Refresh (browser): open client.chargego.rs, read the element with `data-locations` (Charge&GO) and the
response of the roaming POST `api/public/locations/locations-update` (needs the page's csrf `_token`) into a
page variable, then copy it out in 900-character slices with `javascript_tool` (its output is cut at about
1,000 characters, and `?`, `=` must be replaced before returning). Rewrite the two raw files, update the dates.
Google check for the `g_*` stations: search "EV charging station" at the station's coordinates (zoom 18),
open the nearest place within ~100 m, sort reviews by newest; a review younger than 12 months = `g`.
Do not batch more than two places per browser call; Google rate-limits fast loops.

#### 3.11c Drivers' reports, ratings, photos (backend)

`worker/_worker.js` (copied to `dist/_worker.js`; `dist/_routes.json` sends only `/api/*` to it) with the
D1 database `blokvolt` (binding `DB`, schema `worker/schema.sql`). Endpoints: `GET /api/stanice`,
`GET /api/stanica/<id>`, `GET /api/foto/<id>.jpg[?v=t]`, `POST /api/stanica/<id>/prijava`,
`POST /api/stanica/<id>/foto`, `POST /api/prijavi`, `POST /api/zahtev` (forms of /ispravka/ and /za-firme/),
`GET /api/zdravlje`. Comments with links/contacts/rude words and every photo wait for moderation.

Moderation: `/admin/` (noindex) works only after the **owner** sets the secret `ADMIN_KEY` (≥16 characters)
in Cloudflare Pages → Settings → Variables and Secrets (Production) and redeploys; never type the key
yourself. Without it: D1 console queries — `SELECT * FROM photos WHERE status='pending'`,
`UPDATE photos SET status='ok' WHERE id='…'`, `SELECT * FROM checkins WHERE cs='pending'`,
`SELECT * FROM requests WHERE status='new'`. Requests from companies are **not answered** without the
owner's permission (outreach rule). Old form messages (older than 12 months) are deleted by the owner
(privacy policy promise).

Live test after a deploy: `GET /api/zdravlje` → `{"ok":true,…}`; a POST with `"hp":"x"` returns ok and
stores nothing (use it to test routes without creating data).

### 3.12 Logos (when a firm or network is added, or on request)

`static/assets/logos/<slug>.png` (firms) and `op-<slug>.png` (networks), max 360×160, trimmed. Source: the
company's own website (its header logo or apple-touch icon), never a logo site. The container cannot reach
most firm sites: fetch the image in the owner's browser (through `https://images.weserv.nl/?url=…` when the
site sends no CORS header, or a `zoom` screenshot with `save_to_disk` when nothing else works), bring the
raw file into the container, add the slug to `CHOICE` in `scripts/logos.py` (`dark` = shown on a dark tile)
and run it — it trims, resizes and rewrites `content/data/logos.json`. A company that asks for removal:
delete its entry from `CHOICE`, rerun, rebuild (the file itself can stay; nothing links to it).

### 3.13 Illustrations and video

Illustrations: `static/assets/img/<name>-<width>.webp` (480/800/1200/full); the build reads the sizes and
`fig(name, alt)` (templates) or `[[fig:name|alt]]` (Markdown) makes a responsive `<figure>` with the caption
„Ilustracija (AI)“. Article front matter `image:` / `image_alt:` puts one under the lead. The nine current
ones were generated in Higgsfield (gpt_image_2_5, high, 2k; about 2.75 credits each) and brought into the
container as full-size `zoom` screenshots of the image opened in the owner's Chrome (the container cannot
reach the CDN). A few images need no confirmation; a batch of many does (ask the owner first), and every
generation is reported with the credit count. News items use real photos, not illustrations (3.19).

Video: `content/data/video.json` (id, title, channel, poster = an illustration name; check titles with
YouTube oEmbed through WebFetch). `yt(id)` / `[[yt:ID]]` renders a poster; `bv.js` creates the
youtube-nocookie iframe only after a click (privacy policy promise — never embed a live iframe).

### 3.14 Company updates (/za-firme/) and corrections (/ispravka/)

Both forms post to `/api/zahtev` (stored in D1 `requests`). Readers come first and companies last (owner's decision,
25.09.2026): a firm page ends — after the similar firms — with one quiet line „Predstavljate ovu firmu? Ažurirajte
podatke“, a network page with „Vodite ovu mrežu? Pošaljite podatke“, and the footer has „Za firme i mreže“. No
company prompts in page heads, summary boxes or next to the facts. Publishing company-supplied
data: verify first (reply to the company-domain e-mail or call the number on its site — only with the
owner's permission while the outreach rule holds), then mark the data „prema podacima firme“ with the date
and log it in `izmene.md`. Ratings are never removed on a company's request unless they break the rules.

### 3.15 News (/vesti/) — twice a week, by the scheduled news task

Everything about content is in `docs/NEWS_STYLE.md` (what counts as news, sources with RSS, checking, writing,
file format). The run:

1. Setup (§1), then `ls content/vesti/` — the newest file date is where to start looking.
2. Scan the sources of NEWS_STYLE §2 for news since then; choose at most three items; open the primary source of each.
3. Write the files; `python3 scripts/lint_sr.py content/vesti/<new>.md` must show 0 errors. Photo: leave `image:`
   out (the tag pool gives one) unless a photo in `content/data/foto.json` fits the item better (3.19).
4. If a news item changes a fact stated elsewhere on the site, update that page too (the procedures above) and add
   a line to `izmene.md`.
5. `python3 scripts/i18n.py todo` → translate (3.9) → `bash scripts/pack.sh` with 0 segments left in Serbian.
6. Check the new pages in `dist/` (and `scripts/qa/` at 390 and 1440 px), deploy (§5), commit (§6).
7. Report: one line per published item. Nothing new → say so, do not build or deploy.

No messages, comments or forms to anyone — the outreach rule of 3.7 applies to news work as well.

### 3.16 Usage analytics

- **Cloudflare Web Analytics** — switched on 25.09.2026 in Pages → blokvolt → Metrics → Web Analytics. Cloudflare
  adds its beacon (`static.cloudflareinsights.com`) to every deployment; no cookies, no storage in the browser.
  Numbers: Cloudflare dashboard → Analytics → Web analytics. Page views, referrers, countries, devices, Core Web Vitals.
- **PostHog** (EU cloud) — prepared in the code, off while `analytics.posthog_key` in `content/data/site.json` is
  empty. `analytics.consent` (true since 25.09.2026, the owner's choice) picks the mode:
  - `consent: true` — every reader is measured **without cookies** (`cookieless_mode: 'always'`, nothing written to
    the browser) and sees a small banner „Odbij / Dozvoli“ (equal buttons, bottom right; `base.html`, `bv.js`).
    „Dozvoli“ stores `bv:consent=yes` in localStorage; from the next page PostHog runs with its cookie
    (`localStorage+cookie`, `person_profiles: 'identified_only'`) and **session replay** (`maskAllInputs: true`).
    „Odbij“ stores `no`. The privacy policy has „Promeni izbor o kolačiću“ (`data-bv-consent-reset`): it removes the
    choice and every `ph_*` cookie and storage key, reloads, and the banner shows again.
  - `consent: false` — cookieless only, no banner.
  Do Not Track or Global Privacy Control: PostHog is not loaded and no banner is shown. Automated browsers
  (`navigator.webdriver`) are not counted either. The privacy policy follows the mode: text between
  `<!--posthog-->`, `<!--noposthog-->`, `<!--consent-->`, `<!--noconsent-->`, `<!--cookieless-->` markers, and
  front matter `lead_consent` / `description_consent`; it promises replays are kept 30 days at most (PostHog free
  plan) — change that sentence if the plan changes.
  To switch on (the owner creates the account; never sign up or log in yourself):
  1. eu.posthog.com → new project; Project settings → Web analytics: turn on **Cookieless server hash mode**;
     Project settings → General: turn on **Discard client IP data**; Session replay: on (the site masks inputs
     itself); sign the DPA in the organisation settings.
  2. Copy the project API key (`phc_…`, public by design) into `analytics.posthog_key`, build, deploy, commit.
  3. The build then adds `<script id="bv-an">` (and the banner) to every page, the PostHog hosts to the CSP (3.17)
     and the PostHog texts of the privacy policy. Their EN/RU translations are already in the memory (added
     25.09.2026 from a QA build): `BV_QA_POSTHOG_KEY=phc_dummy python3 build.py` builds with a dummy key to look at
     the banner or translate new consent texts; build again without it before packing. Run `i18n.py prune` only
     after such a QA build, or it drops those translations while PostHog is off.
  QA with the banner: Playwright sets `navigator.webdriver`, so override it in an init script
  (`Object.defineProperty(navigator,'webdriver',{get:()=>false})`) and route the PostHog hosts to empty responses.
- **Events** — one entry point, `window.bvTrack(name, props)`; the same names are meant for the future apps.
  Every event carries `lang` and, on firm and network pages, `page` (`firm:<slug>`, `network:<slug>`).

  | Event | Where | Properties |
  |---|---|---|
  | `map_card_open` | map, a charger card opens | `station`, `network`, `verified`, `favourite` |
  | `map_filter` | map chip clicked | `filter`, `favourites` |
  | `map_search` | map search, 1,5 s after typing stops | `query` (≤ 60 chars), `results` |
  | `map_near_me` | „Blizu mene“ | `ok` |
  | `map_navigate` / `map_network_link` / `map_report_error` | card buttons | `station`, `network` |
  | `favourite_add` / `favourite_remove` | star on a card | `station`, `network`, `total` |
  | `checkin_sent` / `photo_sent` | drivers' reports | `station`, `network`, `status`, `rating`, `comment` |
  | `outbound_click` / `contact_phone` / `contact_email` | any link out, tel:, mailto: | `host`, `url` / — / `to` |
  | `form_sent` | /ispravka/, /za-firme/ | `form` |
  | `calculator_used` | first change in a calculator | `calculator` |
  | `video_play` | YouTube poster clicked | `video` |
  | `language_switch` | language menu | `to` |
  | `consent_choice` | cookie banner | `choice` (`yes` / `no`) |

  With PostHog on, page views, page leaves and clicks (autocapture) are recorded as well.

### 3.17 Security headers

`build.py` writes `dist/_headers` at the end of every build: HSTS, `X-Frame-Options: DENY`, COOP, a
Permissions-Policy (geolocation only for the site itself) and a Content-Security-Policy that allows scripts only
from the site, the SHA-256 hashes of the inline scripts found in the final HTML (calculators, search, /admin/),
Cloudflare Web Analytics and — when switched on — PostHog. Map tiles come from `tiles.openfreemap.org`, videos
only from `youtube-nocookie.com`. A new third-party script, iframe, font or tile host must be added to the lists in
`build.py`, or the browser blocks it. `scripts/qa/cfserve.py` serves `dist/` with these headers, so CSP errors show
up as console errors in `scripts/qa/qa_all.py` and `map_ui_test.py`.

### 3.18 Favourite chargers and the card actions

The star on a charger card saves the station id in the reader's browser only (`localStorage` key `bv:fav`, at most
300 ids); the chip „Omiljeni“ and `/mapa/?f=fav` show them, and the map draws a green ring around them. Nothing is
sent to the server; ids of stations that disappear from the map are dropped quietly. The privacy policy says so.
When user accounts exist, the list can be synced to the account.

Filters: one-of chips (Svi, Omiljeni, Brzi, AC, CHAdeMO, Besplatni, networks) plus the switch „Potvrđeni“, which
combines with any of them (`?ok=1`; the old `?f=ok` still works). Card actions: „Navigacija“ opens Apple Maps on
Apple devices and Google Maps elsewhere, with the other apps (Google Maps, Waze) linked under it; „Podeli“ uses the
system share sheet or copies the `/mapa/#<id>` link. A price whose date is more than a year old gets the warning
`p_old` (the Evolako app shows the same marker).

### 3.19 News photos (only in a run with the owner's browser)

Every news item shows a real photo: on `/vesti/` (thumbnail), under the lead of the item (with caption and credit),
on the home page, in „Najnovije vesti“, as `og:image` (1200×630 JPEG) and as the RSS enclosure. No AI images for
news. Files: `static/assets/img/<name>-{480,800,1200}.webp` and `static/assets/og/foto/<name>.jpg`; credits in
`content/data/foto.json` (`src`, `au`, `page`, `lic`, `licurl`, `cap`, `alt`, `file` for Commons). The build stops
when a photo has no credit or a news item names an unknown photo.

- **Which photo.** Front matter `image: <name>` picks one; without it the build takes a photo from the tag's pool
  (`pools` in `foto.json`), oldest item first, never the photo of one of the three items before, so older items
  keep theirs when new ones arrive. The scheduled news task only uses photos already in `foto.json` (it has no
  browser): `image:` only when a listed photo fits the item better than the pool (a BYD item → `vest-byd-atto-3`).
- **Sources.** Unsplash — free photos only, never Unsplash+ (the search API marks them `premium`/`plus`; brand
  accounts such as charger makers are skipped for neutrality); Wikimedia Commons — CC0, CC BY, CC BY-SA. Never
  media, press or dealer photos, never a search-engine find. Author and licence exactly as on the photo page.
- **Honest captions.** `cap` says what the photo shows and where, only as far as the photo page or the picture
  proves it („Brzi punjači u Innerbrazu, Vorarlberg, Austrija“, „Gradska kuća u Novom Sadu“). It never claims to be
  the place, charger or car from the news. Unknown place → no place. CC BY / BY-SA get „isečeno“ (the crop is a
  change the licence asks to mark). No readable number plates or recognisable faces in the frame.
- **How (25.09.2026).** The container cannot reach Unsplash or Commons. In the owner's Chrome: on unsplash.com,
  `fetch('/napi/search/photos?query=…&per_page=20')` (drop `premium`, `plus`, `sponsorship`); on
  commons.wikimedia.org, the API (`generator=search&gsrnamespace=6&prop=imageinfo&iiprop=url|size|extmetadata`).
  Show candidates as a grid of thumbnails over the page and pick from a screenshot. Then show the chosen one at
  exactly 1200×675 CSS px (`object-fit:cover`, `object-position` to choose the crop; Unsplash `?w=2400&q=90`,
  Commons the original file), and `zoom` the region `[0,0,1105,621]` with `save_to_disk` (the screenshot frame is
  0.92 of CSS px) — about 1455×818 px. Look at every capture before using it.
- **Files.** `python3 scripts/news_photo.py <capture.png> <name>` writes the three WebP sizes and the OG JPEG.
  Add the entry to `foto.json` (and to a pool if it suits a tag), then the build: the caption+credit and the alt
  text become translation segments (3.9); `/metodologija/#vesti` lists every photo with its credit
  (`[[fotografije]]`), so a pool photo's caption is already translated before an item uses it.

### 3.20 Web app, offline pages and the Android app

- **Web app.** `static/manifest.webmanifest` (name, colours, icons in `static/assets/app/` drawn by
  `scripts/app_icons.py` from the favicon, three shortcuts) and `static/sw.js`, registered by `bv.js` on https. The
  service worker is network-first: when online nothing is served from its cache. It keeps the last 40 pages and the
  assets they used, so they open without a connection; any other page gets `/offline` (`static/offline.html`, SR/EN/RU
  in one file, not translated by `i18n.py`; always the URL without `.html` — Pages redirects `.html`, and a redirected
  response cannot answer a navigation). It never touches `/api/`, `/admin/` or other sites. `_headers`: `sw.js` no-cache.
  Change the cache names (`bv-core-2` …) only when `CORE_FILES` or the offline page change. Kill switch: replace
  `sw.js` with one that calls `self.registration.unregister()`.
- **Android app** — a Trusted Web Activity, package `rs.blokvolt.app`: it opens `https://www.blokvolt.rs/?src=android`
  full screen in Chrome (or another browser with TWA support; otherwise a Custom Tab). No permissions, no data of its
  own; content and updates come from the site. The Android project is `android/`, generated 25.09.2026 with
  `@bubblewrap/core` 1.25 from `android/twa-manifest.json`, plus a themed-icon layer (`ic_monochrome`) and
  `mavenCentral()` instead of jcenter. Icons come from `static/assets/app/`.
- **Build.** The container cannot reach Google Maven or Gradle (proxy), so the app is built by GitHub Actions:
  `.github/workflows/android.yml` runs on every push that changes `android/**` and puts the **unsigned** APK and App
  Bundle into branch `android-build`, folder `<versionName>-<versionCode>/` with `SHA256SUMS`.
- **Sign** (in the container): `apt-get install -y apksigner zipalign`;
  `git fetch origin android-build && git show origin/android-build:<v>/app-release-unsigned.apk > in.apk`;
  `zipalign -p -f 4 in.apk aligned.apk`;
  `apksigner sign --ks <jks> --ks-key-alias blokvolt --ks-pass file:<pw> --key-pass file:<pw> --out blokvolt.apk aligned.apk`;
  `apksigner verify --print-certs blokvolt.apk`. App Bundle for Google Play:
  `jarsigner -keystore <jks> -storepass:file <pw> app-release.aab blokvolt`.
- **Key.** `blokvolt-android.jks` (PKCS12, alias `blokvolt`, RSA 2048, valid until 2056), certificate SHA-256
  `AA:62:B4:08:E9:FA:69:4E:FB:89:57:99:8E:29:FF:93:4C:6F:DF:CA:71:CA:32:75:F8:B0:0D:82:EE:6A:17:21`. The owner keeps
  the file and its password (handed over 25.09.2026); they never go into the repo, the project docs or a chat log.
  Every update of the APK from the site must be signed with this key, or phones refuse to update. On Google Play
  it is the upload key (Play App Signing); add Play's app-signing certificate to `assetlinks.json` then.
- **On the site.** `static/.well-known/assetlinks.json` (the certificate fingerprints; without it the app shows a URL
  bar), the APK at `/aplikacija/blokvolt.apk` (`static/aplikacija/`), its data in `content/data/app.json`
  (version, code, size, SHA-256, certificate, date) and the page `/aplikacija/` (Android download, iPhone and
  computer instructions). `_headers` serves the APK as `application/vnd.android.package-archive`, attachment.
- **New version.** Raise `versionCode` and `versionName` in `android/app/build.gradle` and `android/twa-manifest.json`,
  commit (§6), wait for the workflow (~5 min, green check on the commit), sign, replace the APK and `app.json`,
  build, deploy, commit. Android developer verification for apps installed outside Google Play becomes mandatory
  worldwide in 2027: before then the owner registers as a developer, or the APK on the site stops installing on
  certified phones.

## 4. Build and check

```bash
bash scripts/pack.sh      # build.py + check_links.py + /mnt/user-data/outputs/blokvolt-dist.zip
```

Local checks (the container cannot reach blokvolt.rs or the map tiles) are in `scripts/qa/`:

```bash
python3 scripts/qa/cfserve.py dist 8787 &          # like Cloudflare Pages, with dist/_headers
python3 scripts/qa/qa_all.py sr,en,ru 360,768,1440 # every sitemap URL: JS/CSP errors, overflow, images, footer
python3 scripts/qa/map_ui_test.py /tmp/bv-shots    # map cards, reports, photos, favourites (fake /api)
python3 scripts/qa/vis_shots.py /,/vesti/ /tmp/bv-shots   # full-page screenshots, desktop and phone
```

`build.py` also appends `?v=<hash>` to bv.css, bv.js, map.js, the search indexes, the map data and the
logos (everything under `/assets/` is cached for a year; the MapLibre files sit in a versioned folder). Look at
the changed pages in `dist/` (grep for the new numbers) before deploying, and check the two
`i18n` lines of the build output (3.9).

## 5. Deploy — Cloudflare Pages, project `blokvolt`, direct upload (owner's browser)

Use the Claude in Chrome tools (the owner's Brave, already signed in to Cloudflare). If Cloudflare asks
to sign in, stop and tell the owner — never type credentials.

1. `tabs_context_mcp`, then open a new tab with
   `https://dash.cloudflare.com/?to=/:account/pages/view/blokvolt` (no account id needed). The dashboard
   is slow in a background tab: wait 15–30 s.
2. Click "Create deployment" (JS):
   ```js
   const b=[...document.querySelectorAll('button,a')].find(e=>/^\s*Create deployment\s*$/i.test(e.textContent)); b?(b.click(),'clicked'):'not found yet — wait and retry'
   ```
   (On 23.09.2026 the direct URL `https://dash.cloudflare.com/?to=/:account/pages/view/blokvolt/deployments/new`
   rendered the upload form, with "Production" preselected; if it does not, use the button.)
3. Label the zip input, then find it and upload the zip:
   ```js
   const i=document.querySelector('input[type=file][accept*="zip"]'); i?(i.setAttribute('aria-label','bvzip upload'),'ok'):'no zip input yet'
   ```
   `find` "bvzip upload" → ref → `file_upload` with `/mnt/user-data/outputs/blokvolt-dist.zip`.
4. Wait. The status goes "Preparing upload" → "Unzipped N files." → "N/N files uploaded" and takes
   1–3 minutes for ~100 files; the "Save and deploy" button stays disabled until the end. A background
   tab is throttled, so `innerText` can lag behind the screen — poll every 10–15 s (a single JS call
   that sleeps longer than ~40 s times out), and take a screenshot if the numbers look frozen.
   Then deploy:
   ```js
   const b=[...document.querySelectorAll('button')].find(b=>/Save and deploy/i.test(b.textContent)); b&&!b.disabled?(b.click(),'clicked'):'not ready'
   ```
5. Wait for "Success". If a call times out, look at the deployments list before retrying — the deploy
   may already be live.
6. Verify live: navigate the tab to `https://www.blokvolt.rs/?nc=1` and, on that origin, run
   ```js
   const t=await (await fetch('/alati/kalkulator-troskova/?nc=1',{cache:'no-store'})).text(); t.includes('EXPECTED TEXT')
   ```
   (The cloud container cannot reach blokvolt.rs; cross-origin fetches are blocked, so fetch same-origin.)
   Always add a query string: the browser still holds an old permanent redirect from the days when
   www.blokvolt.rs pointed at evolako.rs, and without it a plain navigation can land on the old target.
   That is only the local browser cache — it says nothing about what the site serves.

## 6. Commit — GitHub `hemptoon/blokvolt-rs` via the web upload page (owner's browser)

1. In the clone: `python3 scripts/gh_payload.py /mnt/user-data/outputs/.gh/payload.json.gz` — prints the
   changed files and the expected tree hash. (Deleted files cannot be committed this way; avoid deletions.)
   GitHub takes fewer than 100 files per upload ("Yowza, that's a lot of files"): with more, commit in parts —
   unpack the same payload twice with a filter in step 4 (e.g. everything except `static/assets/logos/`, then
   only those) and verify the tree hash after the last part.
2. Open `https://github.com/hemptoon/blokvolt-rs/upload/main` (the owner is signed in; if not, stop and
   tell the owner).
3. Add a helper file input, then `find` "bvpay payload" → `file_upload` the payload:
   ```js
   let i=document.getElementById('bvpay'); if(!i){i=document.createElement('input');i.type='file';i.id='bvpay';i.setAttribute('aria-label','bvpay payload');document.body.appendChild(i);} 'ok'
   ```
4. Unpack the payload into GitHub's uploader:
   ```js
   const f=document.getElementById('bvpay').files[0];
   const obj=JSON.parse(await new Response(f.stream().pipeThrough(new DecompressionStream('gzip'))).text());
   const dt=new DataTransfer();
   for (const [p,v] of Object.entries(obj)) dt.items.add(new File([('t' in v)?v.t:Uint8Array.from(atob(v.b),c=>c.charCodeAt(0))], p));
   const inp=document.querySelector('#upload-manifest-files-input'); inp.files=dt.files; inp.dispatchEvent(new Event('change',{bubbles:true}));
   Object.keys(obj)
   ```
5. Wait until the page no longer shows "Uploading N of M files" — the commit button goes live before
   the attachments finish, and committing early silently loses the commit (the page lands on a browser
   error and the branch is unchanged). Poll until it reads "done":
   ```js
   (document.body.innerText.match(/Uploading \d+ of \d+ files/)||['done'])[0]
   ```
6. Commit message and commit (edit SUMMARY/DESCRIPTION; end the description with the attribution lines
   your session instructions require, if any):
   ```js
   const setv=(el,v)=>{Object.getOwnPropertyDescriptor(el.tagName==='TEXTAREA'?HTMLTextAreaElement.prototype:HTMLInputElement.prototype,'value').set.call(el,v);el.dispatchEvent(new Event('input',{bubbles:true}));el.dispatchEvent(new Event('change',{bubbles:true}));};
   setv(document.querySelector('#commit-summary-input'),'SUMMARY');
   setv(document.querySelector('#commit-description-textarea'),'DESCRIPTION');
   const r=document.querySelector('input[type=radio][value=direct]'); if(r){r.checked=true;r.dispatchEvent(new Event('change',{bubbles:true}));}
   const btn=[...document.querySelector('input[name=manifest_id]').closest('form').querySelectorAll('button')].find(b=>/Commit changes/.test(b.textContent));
   btn&&!btn.disabled?(btn.click(),'committed'):'button not ready'
   ```
7. Verify (on github.com; retry after 30–60 s if the API still shows the old tree):
   ```js
   const j=await (await fetch('https://api.github.com/repos/hemptoon/blokvolt-rs/git/trees/main?recursive=1',{credentials:'omit',cache:'no-store'})).json();
   const b=j.tree.filter(x=>x.type==='blob'); const lines=b.map(x=>x.path+':'+x.sha).sort().join('\n')+'\n';
   ({files:b.length, hash:[...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(lines)))].map(x=>x.toString(16).padStart(2,'0')).join('').slice(0,16)})
   ```
   The hash must equal the one printed by `gh_payload.py`. If it still shows the previous commit,
   the commit did not go through — redo section 6 from step 2 rather than assuming a caching delay.

If a browser call answers "Browser extension is not connected", retry the same call once — the link
to Brave drops for a few seconds now and then. If it fails again, go to section 7.

## 7. If the browser is not available

Build anyway, leave `/mnt/user-data/outputs/blokvolt-dist.zip` and the payload in outputs, and tell the
owner in the report: "open Brave (with the Claude extension) and reply 'деплой' in this session".
Do not try other deploy routes.

## 8. Report to the owner

Short, in Russian: what changed (with the numbers), what was checked without changes, what could not be
checked and why, what the owner should do (screenshots, logins). No long documents.
