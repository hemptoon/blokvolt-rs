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
  Order of firms (owner's decision, 06.10.2026): the "Izdvojeno" firm is listed first in every firm list
  (register, type hubs, cities, similar firms, price page); groups A and B are shown as one section, sorted A–Z;
  the price page sorts by price (`list_key`, `SECTIONS`, `grouped` in build.py). /firme/ ("Kako se čita
  spisak"), /metodologija/, /o-sajtu/ and /pomoc/ko-stoji-iza-blokvolta/ say exactly this — change them together.
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
| Advertising: media kit and booked ads | `content/data/oglasavanje.json`, `templates/oglasavanje.html`, `templates/_oglas.html`, `static/za-firme/` | `/za-firme/oglasavanje/` (SR/EN/RU) and its PDFs are made from the JSON; an ad appears only while an entry in `oglasi` is in its dates. See 3.26. |
| Accounts and the newsletter | `content/data/site.json` → `accounts`, `pregled`; `worker/_worker.js` | "Moj BlokVolt" (/nalog/) and "Nedeljni pregled" (/pregled/). Both off until the owner switches them on. See 3.27. |
| Newsletter issues | `content/pregled/<YYYY-MM-DD>-<slug>.md`, `static/assets/pregled/` (covers), `scripts/pregled.py` | One file per issue; the page /pregled/<slug>/ and the e-mail in three languages come from it; the worker sends after the owner approved the preview. See 3.27 "Sending the issues". |
| Display currency (RSD / EUR / USD) | `static/assets/fx.js` (core, shared with evolako.rs), `static/assets/valuta.js`, `scripts/valuta.py`, `/api/kurs` in `worker/_worker.js` | Default RSD; EUR/USD only by the reader's choice. The fallback rate is in three files that must agree (the build checks it). See 3.29. |

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
  `content/data/kalkulator.json` → `public_range`, and the guides `content/vodici/ko-placa-struju-za-punjenje.md`,
  `punjenje-elektricnog-auta-u-zgradi.md` (240 kWh → "10.300–19.000 RSD", lead "6 do 20 puta") and
  `elektricni-auto-bez-garaze.md` (160 kWh → "6.900–12.600 RSD", savings "5.900 / 11.700 RSD", break-even
  "1.000–2.000 km" for a 100 € garage; the slow AC row "oko 91 RSD" = `public` → `ac` in `kalkulator.json`).
- State chargers "36 / radi 24": the home stat and the /javno-punjenje/ stat are computed from
  `content/mapa/putevi-srbije.json`; by hand: `content/operateri/putevi-srbije.json` (`network`, `card`,
  `network_short`), `content/javno/indeks-cena.json` (the putevi-srbije row), `content/javno/besplatni-punjaci.md`,
  `content/podaci/statistika-ev-srbija.md`.
- Fleet and registrations ("7.155" MUP, "1.166" SAUVD): `content/podaci/statistika-ev-srbija.md`, `content/data/site.json` →
  `home_stats`, and the growing fleet estimate `ev_counter` (3.30) — a new MUP or SAUVD figure changes all of them.
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

**Since 05.10.2026 the prices come from the owner's Android phone** (a robot reads the apps; method and routes in the
project doc `claude/BlokVolt_Robot_Cene_Android.md`; raw files on the owner's Mac in `~/dev/android/robot/prices/`).
What the site keeps:
- `content/mapa/mreze/chargego-app.txt` — every connector of the Charge&GO app as it showed it
  (`cid|name|address|kW|price`; `izvori.json` key `cga` = date and source). `map_data.app_layer()` gives each matching
  site of the network's list its per-connector prices, cable, hours and "how to find" notes (3.11e).
- Index rows (`indeks-cena.json`): `key` = "where|charger" when two rows share a charger class (the history page
  compares by it), `sum` and `exc` (the Charge&GO summary card: where the class price applies and the exceptions),
  `rsd_kwh` (per-kWh tariffs: eDrive, Yesla), `start_rsd` (start or connection fee), `place_only` (a per-place price:
  goes to `places`, not to the network's tiers), `free_where` (free only at the places named in `where`).
- Fees and "how to charge here" per network: `kako` in `content/operateri/<slug>.json` (steps, payment, without
  registration, after charging, refund, app links, sources, `checked`); the map card and the network page show it.
- Charge&GO tops the balance up when it falls **below 1.000 RSD** (Google Play listing, 28.08.2026; the T&C PDF still
  says 400 — the site uses 1.000). Registered users pay 20 % less than guests; guests reserve at least 2.000 RSD.

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

Prices marked for the display currency (`<span data-rsd=…>`, 3.29) are not part of a key: `i18n.py` takes the span out
of the key and puts it back around the same price in the translation, and the span's `data-unit` follows the translated
unit ("/min" → "/мин"). Marking a price never makes a sentence untranslated.

Not segments: JavaScript texts live in `<script id="bv-i18n" type="application/json">` blocks in the
templates (calculators, search). Plain strings there are translated like any segment; objects keyed by
`sr`/`en`/`ru` (plural forms, month names, quotation marks) are edited in the template itself. Elements
with `translate="no"` (logo, language menu) are left alone. CSV downloads stay Serbian. Links to
evolako.rs get `?lang=en|ru`.

### 3.10 blokvolt.com — the regional guide: English pages and local-language sections

Since 28.09.2026 blokvolt.com has two layers, both generated by `python3 scripts/gen_com.py` into `dist-com/`
(not committed here; exits 1 on a broken internal link or a broken link to blokvolt.rs, and the CI build runs it):

- **English pages** — home, one page per country (Serbia is a short summary that sends readers to blokvolt.rs/en/;
  Montenegro, Bosnia and Herzegovina, North Macedonia, Croatia, Slovenia, Albania, Kosovo), "For companies and
  suppliers" and a 404. Sources: `content/com/site.json` (country order and slugs, the four short facts per
  country, the Serbia summary, the check date) and `content/com/research/<CODE>.json` (one verified fact file per
  country: `summary`, `stats`, `networks` with `prices`, `electricity`, `subsidies` with `status`
  open / closed / none / unconfirmed / paused, `buildings`, `policy`, `gaps`; every fact with `source`,
  `source_title`, `source_date`, `confidence`). Refresh: one research subagent per country (WebSearch and
  WebFetch only, no workarounds for blocked sites, no ratings, Evolako and BlokVolt excluded).
- **Local sections** — `/hr/` Croatia (10 pages, Croatian), `/ba/` Bosnia and Herzegovina (8, Bosnian), `/me/`
  Montenegro (8, Montenegrin in neutral ijekavian); since 28.09.2026 also `/al/` Albania (8, Albanian, lekë), `/xk/`
  Kosovo (8, Albanian as used in Kosovo — veturë, karikues; €) and `/mk/` North Macedonia (8, Macedonian in
  Cyrillic, ден.). A section exists when `content/com/local/<dir>/country.json` exists. Pages: hub, map, prices, (HR) apps and cards, home vs public charging with the calculator, subsidies,
  travel, (HR) apartment buildings, statistics with a CSV, method.
  - `country.json` holds every number of the section: fleet and new registrations, networks with prices, apps,
    tariffs (all-in price per kWh and its parts), fuel, calculator defaults and chips, subsidies, benefits, road,
    sources. Each price and rule carries its source, `valid from` and the check date; `conf` medium/low shows a note.
  - `NN-<page>.md` — front matter (`key`, `slug`, `template` hub / map / page, `order`, `nav`, `title`,
    `description`, `kicker`, `h1`, `lead`, `card`, `related`) and a body in Jinja + Markdown. Widgets come from
    `templates/com2/_w.html` (`w.stats`, `w.tiles`, `w.price_table`, `w.net_cards`, `w.tariffs`, `w.calc`,
    `w.subsidies`, `w.bars`, `w.sources`, …); numbers through `num()`, `money()` and `pl(n, one, few, many)`
    (the noun form after a number: 1 punjač, 2 punjača, 5 punjača — never write a noun after a data number by hand).
  - `content/com/local/strings.json` — the interface strings of each language, the map included; a section may keep
    its own `content/com/local/<dir>/strings.json` (same keys), which wins (al, xk, mk do).
  - Language: Croatian with Croatian words and dates `28. 9. 2026.`; Bosnian ijekavian, dates `28.09.2026.`;
    Montenegrin as neutral ijekavian (gdje, nisu — not đe, nijesmo). A date that ends a sentence takes no second
    period (the generator removes it). Currency EUR (HR, ME) and KM (BA).
  - Albanian and Macedonian (`LOCALES` in `gen_com.py`): thousands with a non-breaking space (sq) or a dot (mk),
    decimal comma, two noun forms (`plural` sq / mk). Lek and denar prices drop trailing zeros (`trim`: 10,2 lekë,
    28 ден.) and the calculator shows totals in whole lekë/denars. Kosovo: "Kosova" as a place name, nothing about its
    status in the site's own words, schema type `Place`; its pages are not linked from blokvolt.rs and are not in the
    .rs hreflang clusters (`region_pages.rs_alternates`, `gen_com.hreflang`). North Macedonia: "Северна Македонија".
  - North Macedonia home electricity = RKE energy price for the universal supplier (decision each December, valid
    from 1 January) + the transmission and distribution fee per kWh (2,0339 ден. in 2026, from the bill calculator
    that the RKE site links to, "Калкулатор за твојата сметка") + VAT 18 %; the monthly access fee (200 ден.) and
    the municipal lighting fee are not part of the cost of charging. Recheck all three every January.
  - Map: `content/com/local/<cc>/stanice.json` (made by `scripts/region_map.py`, see 3.23) and `cijene.json`
    (made from the networks' prices in `country.json`), shown by the same `map.js` as /mapa/ with the page's
    config (centre, zoom, currency, number format `num` {dec, thou, trim}, the correction e-mail). Stations are
    marked "from open data, not checked". The search box reads Cyrillic as Latin and sh/ch/zh, gj/kj as one letter
    (`sfold` in map.js: "Охрид" finds "Ohrid", "Ниш" finds "Niš"); price matching keeps the plain `fold`.
- **hreflang.** Every local page lists its section siblings and, for the shared topics, the blokvolt.rs page in
  sr / en / ru with `x-default` = the Serbian page; the hub lists the English country page (`x-default`). The list
  of shared topics is `scripts/region_pages.py` (`RS_PAGES`): map, prices, apps, calculator, subsidies, buildings,
  statistics, method. build.py writes the same cluster on the .rs side (head and sitemap), so both sites always
  agree. Codes: `hr-HR`, `bs-BA`, `sr-ME`, `sq-AL`, `sq` (Kosovo), `mk-MK` — never `cnr` or `sq-XK` (Google
ignores them).
- **Design** — the blokvolt.rs design system (`bv.css`, `bv.js`, `map.js`, MapLibre, Onest) plus
  `static/com/com.css`; templates in `templates/com2/`. Share images: `python3 scripts/og_com.py` renders
  `static/com/og-en.png`, `og-hr.png`, `og-ba.png`, `og-me.png`, `og-al.png`, `og-xk.png`, `og-mk.png` (Cyrillic
  font for mk). The English layer and the local sections are impersonal (no "we"/"our" about the site).
- **Rules.** No Evolako offer outside the Serbia page; no live statuses of Charge&GO; nothing from Google Maps;
  companies and operators are not contacted from this work.

Refresh: prices, tariffs, fuel and subsidies monthly (edit `country.json`, keep the dates honest); the map data
monthly by itself (3.23). After any change: build, look at the changed pages at 1440 and 390 px, then publish.

Publish (GitHub Pages, repository `hemptoon/blokvolt-com`, branch `main`, root): commit the sources here first
(section 6), then `python3 scripts/com_payload.py` → upload `/mnt/user-data/outputs/.gh/com-payload.json.gz` at
`https://github.com/hemptoon/blokvolt-com/upload/main` with the same helper input and unpack snippet as in
section 6 (steps 3–6), then run the verification snippet the script prints — it compares every built file with
the repository tree. Files that exist only in the repository are not removed by an upload.
The upload page takes fewer than 100 files ("Yowza, that's a lot of files"), and the payload holds the whole
site (106 files on 29.09.2026). Upload only what differs from the repository: after the helper input holds the
payload, run this instead of the unpack snippet (it compares git blob hashes with the tree of `main`):
```js
const f=document.getElementById('bvpay').files[0];
const obj=JSON.parse(await new Response(f.stream().pipeThrough(new DecompressionStream('gzip'))).text());
const j=await (await fetch('https://api.github.com/repos/hemptoon/blokvolt-com/git/trees/main?recursive=1',{credentials:'omit',cache:'no-store'})).json();
const have=Object.fromEntries(j.tree.filter(x=>x.type==='blob').map(x=>[x.path,x.sha]));
const hex=b=>[...new Uint8Array(b)].map(x=>x.toString(16).padStart(2,'0')).join('');
const dt=new DataTransfer(), changed=[];
for (const [p,v] of Object.entries(obj)) { const bytes=('t' in v)?new TextEncoder().encode(v.t):Uint8Array.from(atob(v.b),c=>c.charCodeAt(0));
  const head=new TextEncoder().encode('blob '+bytes.length+'\0'), all=new Uint8Array(head.length+bytes.length); all.set(head); all.set(bytes,head.length);
  if (have[p]!==hex(await crypto.subtle.digest('SHA-1',all))) { changed.push(p); dt.items.add(new File([bytes],p)); } }
if (changed.length<100) { const inp=document.querySelector('#upload-manifest-files-input'); inp.files=dt.files; inp.dispatchEvent(new Event('change',{bubbles:true})); }
changed.length
```
With 100 or more changed files, upload `changed` in two parts. A change of `bv.css`, `bv.js` or `map.js` changes every
page (the asset version in the links), so expect most pages in the list.

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
fix `ids` then. Note: the page text says "N operational" — that is the row count of the
"u funkciji" table, which also holds rows marked "Trenutno nije u funkciji" / "Nije u funkciji"; count the
working chargers from the table image, never from that line (10.10.2026: text "31", table 24 working + 7 down).
The images' Last-Modified header (same-origin fetch from the image tab) shows whether the tables changed. After the update: the "radi 24 od 36" sync points (2), `izmene.md`, and the EN/RU todo —
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
added stations; not open data). The browser joins them. The build's counts (239 stations, "Potvrđeno: 179"
on 28.09.2026) come from the joined list.

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

- **Contact filter.** `CONTACTY` looks for e-mail addresses and phone-like digit runs after dates and times are
  taken out (`DATEY`: 28.09.2026, 28. 9. 2026., 28/09, 2026-09-28, 15.30, 15h30), so "Punio sam 28.09.2026" is
  published at once. Test cases in the 28.09.2026 commit; keep them passing when the regexes change.
- **IP fingerprint.** `ipHash(request, env)` = the first 12 bytes of HMAC-SHA-256 of the IP with the day's random key
  (one-row table `dk`, created by the worker on first use, overwritten on the first request of each UTC day). A plain
  hash of the address is reversible by trying all IPv4 addresses; an old fingerprint without its key is not. The
  privacy policy and /pravila-objavljivanja/ describe exactly this — change the texts if the scheme changes.
- **Reports.** One report per item and fingerprint per day (`rl` key `rx:<c|f>:<id>:<fp>`), so "three visitors"
  in the rules is three different visitors. A comment is hidden for review at 3, a photo at 2. Approving an item in
  moderation resets its `rep` to 0; rejecting keeps it.
- **Errors shown to drivers** (`map.js` `errText`): 429 `too fast` → "Sačekajte nekoliko sekundi…", `queue full`
  → "Za ovaj punjač već mnogo fotografija čeka proveru…", `limit` → "Previše prijava za danas…", a failed upload
  → "Slanje nije uspelo…", a picture the browser cannot open → "Ova slika ne može da se pošalje…". When `/api` does
  not answer, the card says "Prijave vozača sada ne mogu da se učitaju" instead of "Još nema prijava".

Moderation: `/admin/` (noindex) works only after the **owner** sets the secret `ADMIN_KEY` (≥16 characters)
in Cloudflare Pages → Settings → Variables and Secrets (Production) and redeploys; never type the key
yourself. Without it: D1 console queries — `SELECT * FROM photos WHERE status='pending'`,
`UPDATE photos SET status='ok' WHERE id='…'`, `SELECT * FROM checkins WHERE cs='pending'`,
`SELECT * FROM requests WHERE status='new'`. Requests from companies are **not answered** without the
owner's permission (outreach rule). Old form messages (older than 12 months) are deleted by the owner
(privacy policy promise).

Live test after a deploy: `GET /api/zdravlje` → `{"ok":true,…}`; a POST with `"hp":"x"` returns ok and
stores nothing (use it to test routes without creating data).

#### 3.11d Our checked facts per station (`content/mapa/dopune.json`, since 28.09.2026)

Facts that no open database or network list has, checked by hand with a source and a date: the exact point
and how to find the charger, the address with the house number, hours, access (Tesla only, card at the desk,
60 minutes a day), who charges free (`fee.free`: `all` / `limited` / `tesla`), a verification override (`v.by`
`own` = the location owner's own site: IKEA, OMV, Parking servis) and a note. Keys per station id: `n`, `a`,
`lat`, `lon`, `net`, `opn`, `c`, `dc`, `ac` (as in punjaci.json), `loc {q, venue, find}` (`q` = `net` / `osm` /
`ocm` / `site` / `field`), `oh {t, h24, src}`, `ax {who, how, limit, t}`, `fee {free, t, src, note}`, `v`, `al`
(other names, used for search and to match the price table — "OMV Zemun park"), `note`, `src [{d, l, u, upd}]`.
`map_data.dopune()` checks the ids (a station that left the map is printed) and the keys (an unknown key stops
the build), writes `/assets/map/dopune.json` (not open data) and applies it to the station list the pages count
with; the browser joins it after `mreze.json`. Its texts (`venue`, `find`, `t`, `src`, `note`) are translation
segments (`tx:<text>` in the page strings), so a new or changed text needs the EN/RU todo (3.9).

Rules: only facts with a source; drivers' reports are labelled „po vozačima“ with the year; free for Tesla only
(`fee.free: tesla`) shows as free only when the reader switches on „Imam Teslu“. Keep `tesla.json` (the network
list) and this file in step when Tesla's sites change. Re-check the entries with the monthly map refresh
(3.11): Tesla's price policy, IKEA's hours, the OMV list (the five EasyPark pumps), Ledi MS (2024 data).

Pipeline rules added on 28.09.2026 (`map_data.verify()`): a station without a network is joined to an official
site of another current type only within 40 m (the IKEA chargers, AC, are not part of the Tesla Supercharger
80 m away); the network's address replaces ours when it has the house number and ours does not
(`has_house_no`, road numbers such as "E75 75" do not count); `STREET_FIX` corrects the networks' spelling.

Since 06.10.2026 dopune.json also has `park {t, src}` (parking terms of the host) and `cab {own, src, d}`, and `oh.w`
(the daily open windows in minutes, `[[360, 1560]]` = 06:00–02:00; `h24: true` = always open) for "sada radi /
zatvoreno". Coordinates in dopune.json carry a watermark in the 7th decimal (≤ 0,1 m, 3.28) — edit the 5th or 6th
decimal as usual, the build adds it. Keep the file's hand layout: after a scripted change run
`python3 scripts/fmt_dopune.py` (it rewrites the file in that layout and checks the round trip).

#### 3.11e The networks' app layer and the price data (since 06.10.2026)

- **Charge&GO app → stations.** `app_layer()` groups `chargego-app.txt` by name and address and gives each group to
  the one site of the network's list with the best score (2 × name words + address words, −2 when no power is
  within 8 kW); a tie or a score under 2 attaches nothing (printed). Brands must match (OMV, NIS, BIG, Stop Shop…);
  Skopje/Kocho/Katlanovo are skipped. `app_fields()` writes into `mreze.json`: `pr {d, u: 'min', src, l: [[cur,
  kW, RSD, n]]}` (one line per current, power and price), `cab` when the app says "bez kabla"/"sopstveni kabl",
  `oh {t, h24: false, w, src, d}` from the app's closing notes, `loc.find` (floor, gate; the Futura Park phone number
  is not published — "broj za poziv je u aplikaciji"). The test site Nova Crnja (`cg-74`) is not added.
- **Roaming layer.** `ROAM_NET`: `RS*ORI` = Orion eMobility, `RS*007` = eDrive (Voltic d.o.o.); `EVSE_NAMES` names
  the eDrive EVSEs (E00040 Ingrap-Omni Valjevo, …) because the roaming map shows only the EVSE id.
- **Open data stays open data.** `punjaci.json` (ODbL) has only the open snapshots, the `v` flags and the state
  chargers' status; the own-cable facts (also JP Putevi Srbije's) travel in `mreze.json`. Check after a change: the
  `?v=` hash of punjaci.json changes only when the snapshots or the checks change.
- **cene.json.** `price_table()`: tiers (one price list for the network, by power class) and `places` (a price
  recorded at a place: Orion, Spectra, eDrive, per-place rows). `guard_exact()` adds `places` copies with
  `guard: true` for older map code (the evolako.rs map until its script is replaced, the apps' first versions), which
  takes the only price recorded at a place even for the other current: DeLasol Lapovo has DC 50 and 75 kW in the app
  and AC 22 kW on the list, so the AC station gets a copy of the AC price. map.js skips `guard` entries and never
  takes a place price of the other current. The build prints every guard it adds.
- **tx.json.** English and Russian of the Serbian texts in the map data, from the translation memory (`map_tx()` in
  build.py, after the i18n pass); listed in the app feed as `files.map.tx`. The evolako.rs map reads it.

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
`fig(name, alt)` (templates) or `[[fig:name|alt]]` (Markdown) makes a responsive `<figure>`. Illustrations get no
caption (the owner dropped the „Ilustracija (AI)“ note on 26.09.2026); `/metodologija/#vesti` says in one line
that the guide illustrations are AI-made. Article front matter `image:` / `image_alt:` puts one under the lead;
`thumb:` sets only the small picture in the lists (`/vodici/`, the home page) without adding a figure to the page. The nine current
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

### 3.15 News (/vesti/) — Monday, Wednesday and Friday, by the scheduled news task

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
- **Our visit counter** (07.10.2026, the owner's „деплой счетчика“) — the last block of `static/assets/bv.js` sends one
  request per page view (`fetch` with `keepalive`, `no-cors`, text/plain — no preflight; not `sendBeacon`: Brave's Shields
  drop cross-site beacons) to `https://evolako-bot.mr-smekhov.workers.dev/s/p`
  — the founders' Telegram bot (Cloudflare Worker `evolako-bot`, source and docs in the project:
  `claude/Evolako_CRM_Source_2026-09-29.md` → `src/counter.js`, `claude/Evolako_Bot_Telegram_2026-09-28.md`). Sent: host,
  path (no query), referrer host, utm_source/medium/campaign, page language, team mark. Not sent on other hosts
  (pages.dev previews) or from automated browsers (`navigator.webdriver` — Playwright QA). The worker keeps no IP:
  a daily-salted SHA-256 of IP + browser (`vid`) and of IP (`iph`), table `hits` in D1 `evolako-crm` (EU), 365 days.
  `?tim=1` on any page marks the browser as the team's own (`localStorage['evo_tim']`; `?tim=0` removes it); the
  morning report in Telegram (topic Stats) then leaves out that browser and everything from the same IP that day.
  Do Not Track / GPC are not checked: no cookies, no profile, nothing that follows a reader — like Cloudflare Web
  Analytics. CSP: the worker host is in `connect-src` (`build.py`, 3.17). evolako.rs sends to the same address from
  its Webflow site code. The privacy policy describes it (#merenje-poseta, second paragraph).
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
  | `ad_click` | a booked ad (`aside.oglas`) | `ad` (the booking id) |
  | `calculator_used` | first change in a calculator | `calculator` |
  | `video_play` | YouTube poster clicked | `video` |
  | `language_switch` | language menu | `to` |
  | `currency_changed` | display currency switcher (3.29) | `from`, `to`, `surface` (`site`) |
  | `consent_choice` | cookie banner | `choice` (`yes` / `no`) |
  | `account_sign_in` / `account_sign_out` / `account_delete` / `account_settings` | /nalog/ (3.27) | `how` (`code` / `link`), `all`, the settings chosen |
  | `newsletter_signup` / `newsletter_confirm` / `newsletter_on` / `newsletter_off` / `newsletter_monthly` | /pregled/, the boxes, /nalog/ | `src` (page path), `where` |

  With PostHog on, page views, page leaves and clicks (autocapture) are recorded as well.

### 3.17 Security headers

`build.py` writes `dist/_headers` at the end of every build: HSTS, `X-Frame-Options: DENY`, COOP, a
Permissions-Policy (geolocation only for the site itself) and a Content-Security-Policy that allows scripts only
from the site, the SHA-256 hashes of the inline scripts found in the final HTML (calculators, search, /admin/),
Cloudflare Web Analytics and — when switched on — PostHog; `connect-src` also allows our visit counter (3.16). Map tiles come from `tiles.openfreemap.org`, videos
only from `youtube-nocookie.com`. A new third-party script, iframe, font or tile host must be added to the lists in
`build.py`, or the browser blocks it. `scripts/qa/cfserve.py` serves `dist/` with these headers, so CSP errors show
up as console errors in `scripts/qa/qa_all.py` and `map_ui_test.py`.

### 3.18 Favourite chargers and the card actions

The star on a charger card saves the station id in the reader's browser only (`localStorage` key `bv:fav`, at most 300
ids); the chip „Omiljeni“ and `/mapa/?f=fav` show them, and the map draws a green ring around them. Without an account
nothing is sent to the server; ids of stations that disappear from the map are dropped quietly. The privacy policy says
so. A reader signed in to "Moj BlokVolt" (cookie `bv_in`, 3.27) also keeps the list and „Imam Teslu“ in the account: the
map asks `/api/nalog/ja` once and, when the browser's list belongs to that account (`bv:fav-owner`), joins both lists
and sends every star as well; localStorage stays the offline copy. Nothing changes for readers without the cookie.

Filters: one-of chips (Svi, Omiljeni, Brzi, AC, CHAdeMO, Besplatni, networks) plus the switch „Potvrđeni“, which
combines with any of them (`?ok=1`; the old `?f=ok` still works). Card actions: „Navigacija“ opens Apple Maps on
Apple devices and Google Maps elsewhere, with the other apps (Google Maps, Waze) linked under it; „Podeli“ uses the
system share sheet or copies the `/mapa/#<id>` link. A price whose date is more than a year old gets the warning
`p_old` (the Evolako app shows the same marker).

Since 28.09.2026 the map also has:
- **Imam Teslu** — a switch like „Potvrđeni“ (`bv:tesla` in localStorage, `?tesla=1` for one view). Off: the
  two Superchargers are grey pins with „T“, „Samo Tesla“ in the list, and not in „Besplatni“. On: free for the
  reader (by drivers' reports, `fee.free: tesla` in dopune.json).
- **Prices next to the pins** from zoom 12 (`pt-pr` layer, ASCII only — the map font has no other glyphs
  everywhere): `0 RSD`; receipts of that very charger younger than 90 days as `56-60 RSD/kWh` (they win over the
  network's tariff for the power, also in the card); otherwise `~68 RSD/kWh` = RSD/min × 60 ÷ the power a car
  really gets on that class (DC 30→30, 50→45, 60→50, 110–120→90, 150–180→100, 240→130 kW, interpolated
  between; AC → 11 kW); `?` when the price is unknown. The card shows the same estimate in words.
- **Gde tačno** in the card: address (or „Adresa nije poznata — koristite koordinate“), venue and how to find
  the charger (dopune.json), coordinates with „Kopiraj“, DMS for car navigation, Plus Code (computed in
  map.js), and where the point comes from (network list, OpenStreetMap, Open Charge Map, only the car park).
- Hours and access as badges under the verification line, a note box under the price, and the owner's link
  (with its label) in the sources line. Names from Open Charge Map lose the "Charge&GO -" prefix on screen.
- `?qa=1` exposes `window.bvMapQa()` (the pin properties) for `scripts/qa/map_extra_test.py`.

Since 06.10.2026 (test: `scripts/qa/map_v2_test.py`, with the three tests above):
- **Najbliži punjač** — a button on the map (computer) and next to „Moj auto“ (phone): the three nearest chargers a
  driver can use (works, not Tesla-only, not closed now, confirmed unless the reader asks for the rest; the chip filter
  counts, the search and the visible part of the map do not), straight-line distance, a big route button for the first.
  The location stays in the browser. `?najblizi=1` / `=brzi` opens it (asks first unless the browser already allows
  the location). Route links: Google `dir/?api=1&destination=…&travelmode=driving&dir_action=navigate`, Apple
  `?daddr=…&dirflg=d`, Waze `ul?ll=…&navigate=yes`; the app the reader used last is remembered (`bv:nav`).
  `?qa=1`: `window.bvNearQa(lat, lon, nep)`.
- **Moj auto** — the reader's car (`bv:car` = {id, cons, cab, opt}; the list is `/assets/map/auta.json` from
  `content/data/ev-specs.json`, open sources with attribution; ev-database.org is not used — its terms forbid it).
  With a car: RSD/km in the list, pins and card, sorting „Najjeftinije za moj auto“, what the car really takes
  (AC: phases × current of the post, DC: the car's 10–80 % average, at most 88 % of the station), charging losses
  (DC 96 %, AC 84–92 %), start fees spread over half the battery, winter consumption (Dec–Feb, half in Nov and Mar),
  a cheaper connector here or a ≥ 40 % cheaper charger within 10 km, petrol (calculator's fuel price) and home at night
  (EPS lower tariff, green/blue zone). A Tesla switches „Imam Teslu“ on. `?qa=1`: `window.bvCostQa(id)`.
- **Card**: per-connector prices from the network's app (`pr`), „Kako se puni ovde“ (the network's `kako`), badges for
  hours with „sada radi do … / zatvoreno, otvara u …“ (Serbian time), „Ponesite svoj Tip 2 kabl“ and parking; closed
  stations are faded on the map and marked in the list. „Izdvojeno“: one line about charging at home at night with one
  link to Evolako (`utm_campaign=kartica`, the page language travels as `lang=`); the map's attribution says „Mapu
  održava tim Evolako“.
- **Drivers' short answers**: after „Radi, uz problem“ / „Ne radi“ a reason chip (`why`); then three optional questions
  (cable on the charger / own, parking free / paid, hours 0–24 / limited) → `POST /api/stanica/<id>/podatak`
  (D1 table `facts`; shown as „Vozači javljaju“ when two different drivers agree within 60 days).

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
  Commons the original file), and `zoom` the region `[0,0,1200·r,675·r]` with `save_to_disk`, where r = screenshot
  frame width ÷ `innerWidth` (0.92 on 25.09, 0.80 on 26.09 — check each time) — about 1455×818 px. Never pass
  `scale` when saving. Look at every capture before using it. A larger image (the home hero) is captured in tiles:
  show it at ~1456 CSS px wide, move it by whole CSS px between four `zoom`s of the same region and stitch them.
- **Not only news.** The list thumbnails (`thumb:`) are in `foto.json` too, outside the pools, so they appear in
  the credits list on `/metodologija/`. The home hero is not (since 06.10.2026): `pocetna-punjenje-v2-*.webp` is an
  AI photo (Higgsfield GPT Image 2.5, 2k; plate reads BLOKVOLT, no real plate, no blur), cropped 2308×1520 from the
  original on the branch `media-raw-2026-09` (`media-raw/pocetna-hero-2026-10-06.png`, crop x 380–2688); the
  `/metodologija/#vesti` sentence about AI illustrations names it. The old Unsplash files `pocetna-punjenje-*` stay
  in `static/` unused. Its frame is set by `.hero2-home` in `bv.css` (aspect 2308/1520, phones 3:2).
- **Files.** `python3 scripts/news_photo.py <capture.png> <name>` writes the three WebP sizes and the OG JPEG.
  Add the entry to `foto.json` (and to a pool if it suits a tag), then the build: the caption+credit and the alt
  text become translation segments (3.9); `/metodologija/#vesti` lists every photo with its credit
  (`[[fotografije]]`), so a pool photo's caption is already translated before an item uses it.

### 3.20 Web app, offline pages and the Android app

The page `/aplikacija/` (26.09.2026): download block with the APK size and version from `content/data/app.json`,
three phone screenshots (`scripts/qa/app_shots.py` renders them from the local build; rerun after a visible
change to the home page, the station card or the prices page), a QR code (`static/assets/app/qr-aplikacija.svg`,
made once with the `qrcode` package — not a build dependency), steps, iPhone and computer, questions and the file
hashes. The footer shows two buttons whenever `app.json` has an `apk` (28.09.2026): „Aplikacija za Android (APK)“ →
`/aplikacija/` and „Web-aplikacija za iPhone i računar“ → `/aplikacija/#iphone`. No App Store or Google Play badges
until there is a store page (the stores' rules allow only their download or pre-order / pre-registration badges,
linked to the listing).

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

### 3.21 Automatic checks (GitHub Actions) and the shared quality system

Since 26.09.2026 `.github/workflows/site-checks.yml` checks the site without anyone in a chat:

- **build** — on every push to `main` (except `android/**`) and by hand: `build.py`, `i18n.py todo` must print
  `en 0` and `ru 0`, `check_links.py`, `gen_com.py` (blokvolt.com builds, no broken link), `lint_sr.py --all-news`. A red build means the last commit broke something
  that the next deploy would publish: fix it before deploying.
- **live** — every night at 02:17 UTC and by hand: `scripts/qa/live_smoke.py` against www.blokvolt.rs and
  blokvolt.com (home, /serbia/, /hr/, /hr/karta/, /ba/, /me/ and the Croatian map data) — key SR/EN/RU pages and their markers, a rotating slice of the sitemap (every page about once in
  two weeks), `/api/zdravlje` and `/api/stanice`, the APK against `app.json` (size, SHA-256), `assetlinks.json`,
  security headers, TLS certificates, the apex redirect, the data date in the footer and the latest news date,
  and DNS through dns.google: name servers of all four domains, SPF/DMARC/MX, the DS of blokvolt.rs. Levels:
  FAIL fails the run (a visitor or a mail server would notice), WARN is shown only (known and pending: no DS yet,
  DMARC `p=none` on the .com domains, no anti-spoofing records on evolako.rs, news older than 21 days, footer
  date older than 40 days). When a pending item is done (DS added, DMARC raised), make its WARN a FAIL.
- Run it by hand in the owner's browser: Actions → Site checks → Run workflow. Locally:
  `python3 scripts/qa/live_smoke.py --base http://127.0.0.1:8787 --local` (pages, APK, headers of `dist/`).
- **Pregled tick** (`.github/workflows/pregled-tick.yml`) is not a check but the newsletter's clock: 12 times a day it posts
  to `/api/posta/tick` (3.27, "Sending the issues"). A red run means the worker did not answer, or answered 503 (`mail_off`:
  `RESEND_API_KEY` is missing while the newsletter is on; `no_index`: the deploy has no `/pregled-mail/index.json`).
- **Status badges** (plain SVG, readable with WebFetch): `…/actions/workflows/site-checks.yml/badge.svg?event=schedule`
  (live) and `…?event=push` (build) under `https://github.com/hemptoon/blokvolt-rs`. GitHub e-mails a failed
  run to the owner.
- **Shared quality system.** These checks are the BlokVolt part of the system of both projects described in the
  project doc `claude/Evolako_BlokVolt_Sistema_Kachestva_2026-09-26.md`: nightly run on the owner's Mac (04:30),
  the morning QA review task (08:10) that writes findings to `claude/QA_Log.md`, and the morning Telegram report
  (Worker `evolako-report`). The morning review reads the two badges and, on red, the run summary. Do not build a
  second report or alerting channel for BlokVolt.

### 3.22 App content feed (/app/v1/manifest.json)

The BlokVolt apps (iOS first, Android later; repository `~/dev/blokvolt-app` on the owner's Mac) render the site's
own texts and numbers natively and offline. `scripts/app_feed.py` makes them at the end of `build.py`, from the
finished Serbian, English and Russian pages:

- `dist/app/v1/manifest.json` — what exists and the version (`?v=<hash>`) of every file; served with a 5-minute cache,
  CORS open, `noindex` (`_headers`, rule `/app/*`).
- `dist/assets/app/v1/<lang>/guides.json`, `news.json`, `networks.json`, `firms.json`, `pages.json` and
  `dist/assets/app/v1/data.json` (calculator numbers, language-neutral); the map files stay in `/assets/map/` and are
  listed in the manifest. Everything under `/assets` has a one-year immutable cache, so the apps always go through the
  manifest.
- A page becomes blocks (`h2`, `h3`, `p`, `ul`, `ol`, `summary`, `img`, `table`, `details`, `quote`, `callout`,
  `video`, `facts`, `links`, `doc`, `note`) with limited Markdown inline (`**bold**`, `*italic*`, `[text](URL)`,
  `` `code` ``). Links stay absolute; the apps open the ones they know natively.

Since 06.10.2026 the manifest's `api` has `kurs` (`/api/kurs`, the NBS rate of the display currency, 3.29) and `data.json`
has `fx`: the fallback rate in the same format (`stale: true`) for an app that has no network yet.

The contract is `Docs/FEED.md` in the app repository; schema `blokvolt.app/1` (both additions are new optional fields,
no new version) — add them to `Docs/FEED.md` there with the next app change. A change that removes or renames a
field, a block type or a file is a new version (`/app/v2/`) — v1 stays until the apps in the stores have moved on.
After a build, `python3 -c "import json;print(json.load(open('dist/app/v1/manifest.json'))['files'].keys())"` is a
quick look; the app's own tests read a snapshot of the feed (`Fixtures/`).

### 3.23 Map data of the region (branch region-data) — monthly, by itself

`.github/workflows/region-data.yml` runs on the 3rd of every month at 03:41 UTC, when the workflow or
`scripts/region_fetch.py` changes on `main`, and by hand (Actions → Region data → Run workflow). For HR, BA, ME, MK,
AL, XK, SI and RS it writes one commit to the branch `region-data` (replaced every run, never edited by hand):

- `<CC>/osm.json` — every `amenity=charging_station` of OpenStreetMap inside the country's own boundary relation:
  first from the Geofabrik country extract (daily) cut with osmium; if that fails, from the public Overpass servers
  (one round over three mirrors; a mirror with a database older than 72 h or an empty answer does not count); if
  both fail, the previous file is kept and `meta.json` says so. Mappers' names and ids are removed. ODbL 1.0.
- `<CC>/ocm.json` and `referencedata.json` — Open Charge Map from its public export (github.com/openchargemap/ocm-export).
- `meta.json` — when, from where (`source` geofabrik / overpass, `server`, `timestamp_osm_base`), how many.

The build containers cannot reach Overpass, Geofabrik or the GitHub API; raw.githubusercontent.com works. Locally:
`python3 scripts/region_map.py --fetch` copies the branch into `content/com/region-data/` (ignored by git) and writes
`content/com/local/<cc>/stanice.json` (committed) for HR, BA, ME, AL, XK, MK; without `--fetch` it reuses the copy.
Merging: records of one source closer than 40 m are one site; an OSM and an OCM record are one site within 200 m when
both name the same network, otherwise within 60 m (100 m with the same name) with the same top power or a matching
name. Networks come from per-country rules on name, operator, brand and network (`NETS`); Tesla Destination
chargers (OCM, AC only) are shown as the host's Type 2 for guests; OCM records of providers with a non-commercial
licence, private and planned or removed points are left out; Cyrillic addresses are shown in Latin on the Latin
pages (North Macedonia stays Cyrillic) and country names are cut from addresses. Town names are written as the local
pages write them (`TOWN_FIX`: Tirana → Tiranë, Skutari → Shkodër, Prishtina → Prishtinë, Skopje → Скопје) and the
other spellings stay searchable as aliases (`al`); a name that only says "charger" ("EV Charging Station",
"Karikues elektrik", "punjač za električna vozila") counts as no name (`GENERIC_NAME`), so the card shows the
network or the street; "Tesla Taxi" chargers in Kosovo are not Tesla's network. Every station is "from open data, not checked one by one".
Then rebuild and publish blokvolt.com (3.10). The station counts in the texts follow the data by themselves.

### 3.24 Help (/pomoc/)

Nineteen short answers for drivers and companies, one Markdown file each in `content/pomoc/` (front matter: id, title,
h1, description, lead, kicker, section — `mapa-i-podaci`, `doprinos`, `aplikacija`, `firme-i-ispravke` — order, path
`/pomoc/<slug>/`, updated, related, shots, published, modified), rendered by `build.py` with `templates/pomoc.html`
and the hub `templates/pomoc_hub.html` (sections, the six most asked questions `POMOC_TOP`, a filter box). Linked from
the footer ("Pomoć"), the text under /mapa/, /aplikacija/ and /ispravka/. Rules:

- The text describes the site as it is. A question the owner has not decided (response times, limits, what to
  announce) is not written as a promise; write the neutral version and list the decision in the report. `build.py`
  refuses a page with `[ODLUKA` or `[PROVERITI` left in it.
- No counts, prices or dates that change with the data (they would go stale here); say where the reader sees the
  current value (the map's footer line, the card). The quoted interface labels must match the site (`MAP_T` in
  `build.py`, the forms): after changing a label, grep `content/pomoc/` for the old one.
- Pictures: a line `[[shot:<id> | <alt>]]` shows `static/assets/img/pomoc-<id>-<w>.webp` at its natural size with the
  alt text as the caption, and is left out while the picture is missing. `scripts/pomoc_shots.py` makes them from
  `dist/` (cfserve on 8787): phone crops at 390 px, desktop crops at 1440 px, double density; `/api` answers with
  invented sample data and forms are filled with invented data — mark such captions "(primer)". Retake the pictures
  when the map card or a form changes (`python3 scripts/pomoc_shots.py <id> …`). Not made yet (need an Android
  emulator, the iOS simulator, a real Chrome or the map tiles): android-*, ios-*, desktop-instaliraj, mapa-pregled,
  mapa-legenda, mapa-cene-pored-tacaka, mapa-prijava-poslato, foto-dobro-lose.
- Diagrams are HTML (`<div class="flow">`, `<div class="conns">` in the Markdown) so that they are translated with the
  page; the connector pictograms are inline SVG without text.
- "Da li vam je ovo pomoglo?": the vote goes to `/api/zahtev` with `kind: pomoc` (no name, no e-mail); votes are
  stored in `requests` with status `vote` (outside the moderation queue), an optional note after "Ne" as a `new`
  request (shown in the admin queue). Totals: `GET /api/admin/pomoc` with the owner's key.
- English and Russian through the translation memory as usual (3.9).

### 3.25 The region on /mapa/ and the map data for other sites

- **Neighbouring countries.** `build.py` writes `/assets/map/region.json` from `content/com/local/<cc>/stanice.json`
  of HR, BA, ME, AL and MK (not XK: blokvolt.rs does not list Kosovo, see 3.10) with the fields map.js reads, the
  country (`cc`), the network's short name from `country.json` (`nn`) and, per country, the links to its map and price
  page on blokvolt.com. A station already on the Serbian map is skipped. `cfg.region` in the /mapa/ config switches the
  layer on; the country maps of blokvolt.com have no `cfg.region` and do not change.
- In map.js a station with `cc` is drawn from its own source (`rg`, grey clusters, white points with a grey ring,
  under Serbia's layers) and never takes a Serbian network's data (`netOf`, `isFree`, `price` return nothing for it).
  The list without zoom, search or "Blizu mene" is Serbia's; the count line adds "u regionu još N" (after the filters).
  Search, the chips "Brzi", "AC", "CHAdeMO" and favourites work across the region; "Potvrđeni", "Besplatni" and the
  network chips are Serbian only. The card: country after the address, the network's short name, the verification box
  "Iz otvorenih baza…", a price box linking to that country's prices on blokvolt.com, connectors, "Gde tačno",
  navigation, "Mapa zemlje na blokvolt.com" (its map with the station open, `#<id>`) and "Podeli"; no reports, photos,
  ratings or "Prijavi grešku" (those are for Serbian chargers). Test: `scripts/qa/map_region_test.py`.
- **Map data for other sites.** `/assets/map/*` is served with `Access-Control-Allow-Origin: *` (like `/app/*`): the
  Evolako charger map on evolako.rs reads it with fetch (licences: punjaci.json ODbL; the rest under the terms of use,
  3.28 — the CORS header stays, nothing that real readers use may break). Read the current file names from
  `/app/v1/manifest.json` (`files.map`, versioned `?v=`; the manifest is cached 5 minutes, the files a year).
  Renaming a map file or changing its format breaks that page: keep the fields its script reads, or tell the
  Evolako side first. **Before a deploy that changes the map data, run the live evolako.rs script against the new
  data**: read the page's footer with the Webflow MCP (`get_page_freeform_code`, page `6abaf73484f6a5d61585b9e5`),
  load it in Playwright on a mock page with `www.blokvolt.rs/**` routed to `dist/` and compare every station's list
  price, pin and card with the current data (the 06.10.2026 harness is described in the project doc
  `claude/BlokVolt_Karta_v2_Spec_2026-10-06.md`). On 06.10.2026 this found the Lapovo price for the other current
  (now `guard`, 3.11e) and Serbian notes on the EN/RU page (now `tx.json`).
- **The Evolako map script** (`scripts/evomap/`): `evomap.src.js` and `evomap.css` are the source of the map on
  evolako.rs/mapa-punjaca (Webflow page `6abaf73484f6a5d61585b9e5`); `page_bvq.js` holds the page's EN/RU texts.
  `python3 scripts/evomap/build.py` (terser 5.51.2 through npx) writes `static/assets/embed/evomap-<10 hex of
  sha256>.js` (the same source always gives the same name), `scripts/evomap/build.json` (file, SRI) and, in
  `/tmp/evomap/`, the footer tag (`<script src=… integrity=… crossorigin="anonymous">`) and the head `<style>` block.
  The page's footer code = the politika loader + that tag; its head code = OG/preconnect + the `<style>` block +
  `<script>` with `page_bvq.js` and `window.EVM_TX` (old fallback; the script prefers `files.map.tx`).
  Since 06.10.2026 the script has the same price engine as /mapa/ (per-connector prices, guard-safe matching), „Moj
  auto“ with RSD/km (the car is kept **in memory only** — evolako.rs's privacy policy names no browser storage but the
  language and the referral code), „Kako se puni ovde“, hours with „sada radi“, own-cable and parking badges, closed
  stations faded and left out of „Najbliži punjač“, a Tesla unlocks the Superchargers. It reads `files.map.auta` and
  `files.data` (fuel price) from the feed; `/assets/app/*` and `/assets/embed/*` carry `Access-Control-Allow-Origin: *`.
  Order of a change: source → build.py → deploy blokvolt.rs (the new file next to the old ones) → read the live
  head/footer (`get_page_freeform_code`) and replace only the `<style>` block and the script tag → check the site's
  `lastUpdated` against `customDomains[].lastPublished` (other people's unpublished work: drafts are not published,
  anything else goes live with a site publish) → staging (`publish_site` with `publishToWebflowSubdomain` only) →
  check evolako.webflow.io → production on the owner's „публикуй“ / „да“. **Never change or delete a file the live
  page loads** (another byte = SRI fails = no map); remove old files only after the new tag is live. Test: the
  Playwright harness in the project doc `claude/BlokVolt_Karta_v2_Spec_2026-10-06.md` (mock page + routes).

### 3.26 Advertising (/za-firme/oglasavanje/): the media kit and booked ads

The media kit is public since 29.09.2026 (owner's decision); an ad appears only when a booking is entered in
`content/data/oglasavanje.json` → `oglasi`. The rules below are printed on the page — change them only with the owner.

- **Where.** Three rubrics (`rubrike`, paths listed there): `vlasnistvo` (7 pages of /podaci/: subsidies,
  registration, import, insurance, loans, servicing, rent-a-car), `na-putu` (tolls and parking, free chargers, apps
  and cards, the region) and `vesti` (every news item and the news list). One advertiser per rubric, one ad per page,
  at the end of the text after the „Ažurirano“ line, labelled „Oglas“. Never on the home page, the map, the register
  of firms and networks, prices, statistics, the guides and calculators about charging at home and in buildings, in
  the apps or on blokvolt.com (no analytics there, nothing to sell yet).
- **Not accepted:** selling or installing home chargers and wallboxes (the site is edited by the team behind Evolako,
  and the page says so), public charging networks in „Na putu“ or next to news about that network, gambling, alcohol
  and tobacco, crypto and financial schemes, political ads, claims that cannot be checked. **Never for sale:** place,
  order and labels in the register, points, statuses and ratings on the map, prices and the price index, paid
  articles or news to order, removing drivers' ratings and reports.
- **Price** (`cena`, owner's decision 29.09.2026): one price for everyone — 5.000 RSD a month per rubric without VAT,
  at least 3 months, paid in advance; the same for every rubric and every advertiser, and a booked period keeps its
  price. No tiers by traffic and no discounts (the earlier tiers and the −50 % for the first three advertisers were
  dropped). The page shows three worked examples (3 and 6 months, all three rubrics); they are computed from `cena`.
  Change the price only with the owner.
- **Enquiries** come by the form on the page (`/api/zahtev`, kind `firma` with the hidden field `vrsta=oglas` and
  `jezik` = the page language) or to hello@blokvolt.com. The bot (evolako-bot) posts every advertising enquiry to the
  founders' group, topic „Запросы“, as „BlokVolt · запрос на рекламу“ (firm, rubric, month, what, contact, page
  language) and puts it into the CRM as form `oglas` (version of 29.09.2026; the version before it posted them hourly
  as an ordinary firm request with „vrsta: oglas“). No reply, offer or invoice
  without the owner's explicit yes (outreach rule, 3.7). Invoices only after the publisher (preduzetnik) is
  registered — then fill in the invoice line on the page (business name, MB, PIB, whether VAT is charged).
- **Booking** (owner said yes, invoice paid, image and text checked against the rules): add to `oglasi`
  `{"id", "oglasivac", "rubrika", "od", "do", "url", "slika", "naslov", "tekst", "alt", "ne_na": [], "ne_uz": [],
  "en": {"naslov", "tekst", "alt"}, "ru": {…}}`. `od`/`do` are YYYY-MM-DD, both days included; the image is
  `static/assets/oglasi/<slika>`, 1200 × 400, WebP/PNG/JPG ≤ 200 KB, no animation (the text on the image follows the
  same rules); headline ≤ 60 characters, text ≤ 120. `ne_na`: paths where the ad must not stand. `ne_uz`: words that
  keep the ad off a news item (and a news list page) that contains them — for a network its brand and company names,
  e.g. `["Charge&GO", "ChargeGo", "MT-KOMEX"]`. Without `en`/`ru` the Serbian text is shown on all three versions.
  Keep the advertising declaration (who advertises, what, period and form — Zakon o oglašavanju čl. 20) and the
  advertiser's details until 30 days after the end (čl. 45) outside the repository (it is public). Build, check a page
  of the rubric at 390 and 1440 px, deploy, commit; remove the entry after `do` (bv.js already hides it that day).
- **How it works.** `oglas_za()` in `build.py` picks the ad (rubric of the path, dates, `ne_na`, `ne_uz`);
  `templates/_oglas.html` draws it: `rel="sponsored noopener"`, link with
  `utm_source=blokvolt&utm_medium=oglas&utm_campaign=<id>`, text `translate="no"`, translated variants as `data-only`
  blocks. Ads are left out of the site search (`build_search`), the app feed (asides are skipped) and print; the apps
  hide them by CSS (`display-mode` standalone) and bv.js (a tab opened with `?src=android` or `?src=pwa` stays
  without ads). The image and link are served by BlokVolt: no advertiser pixels, scripts or cookies, CSP unchanged.
  A click sends `ad_click` (3.16).
- **Report to the advertiser** after each month: page views of the rubric's pages in Cloudflare Web Analytics
  (filter by path); clicks they see in their own analytics by the UTM tag.
- **Monthly, in the first days of the month:** `posecenost` ← Cloudflare Web Analytics of the Pages project, whole
  site, previous calendar month (`mesec` like "oktobar 2026", `posete`, `pregledi`); set `stanje` to today; build;
  `i18n.py todo` (the visits line is new every month) → translate (3.9); `python3 scripts/medija_kit_pdf.py`; build
  again; deploy; commit. The visits are information for advertisers; the price does not follow them.
- **PDFs.** `scripts/medija_kit_pdf.py` prints the Serbian and English page to
  `static/za-firme/blokvolt-medija-kit-sr.pdf` and `-en.pdf` (A4, three pages: cover and audience; rubrics, the ad
  and the price; rules, steps and press files — print styles `body.mk-page` in bv.css). It loads the lazy photos
  first and re-encodes them as JPEG with pikepdf (about 0.7 MB a file instead of 3 MB; without pikepdf the file is
  just bigger). After any change of the page text or numbers: build → PDF → build (the buttons appear only when both
  PDFs exist). Look at all three pages of both files before deploying: a section must start at the top of a page.
- **Photos** (redesign 29.09.2026): six AI-generated photos (Higgsfield, 29.09.2026; the people in them are not real
  persons) — the hero, the audience, one per rubric and the sample ad. Originals (PNG 2048 × 1360, the ad 2688 × 1152)
  are on the side branch `media-raw-2026-09`, folder `media-raw/` (not served); `scripts/medija_kit_img.py` makes
  `static/assets/img/oglasavanje-<name>-<width>.webp`, the 3:1 sample ad (`oglasavanje-primer-600/1200.webp`) and the
  og:image `static/assets/og/oglasavanje.jpg` (1200 × 630, drawn from HTML with the site font; `--og-only` redraws just
  that). `/assets/` is cached for a year: a changed photo gets a new file name, never the old one. The sample ad on
  the page is a mock-up (class `.mk-ad`, not `.oglas`, which print and the apps hide).
- **Files for the media:** `static/za-firme/blokvolt-logo.svg`, `blokvolt-logo-beli.svg` (dark backgrounds),
  `blokvolt-znak.svg`, `blokvolt-logo.png` (1200 × 304, transparent). Same geometry as the site logo: the 64-unit
  tile `#0B0F17` with the lime bolt `#D9F45B`, "blok" 400 + "volt" 800.

### 3.27 Accounts and the newsletter (/nalog/, /pregled/)

Built 29.09.2026, **off** until the owner switches it on. "Moj BlokVolt" (`/nalog/`): sign-in without a password (a
six-digit code and a one-click link by e-mail), the map's favourites on every device, the car, its fast-charging plug,
„Imam Teslu“ and the city, the reader's own reports and photos with their review status, data export and deleting the
account. "Nedeljni pregled" (`/pregled/`): a weekly e-mail — news, public charging prices, new chargers — with double
opt-in. The link in the code mail and the one in the confirmation mail open a page with one button („Prijavite se“,
„Potvrđujem prijavu“) and nothing happens until it is pressed: mail scanners open links, and some run the page's scripts
too. Those pages take the token out of the address bar at once (kept for the tab in sessionStorage, so a reload works).
The six-digit code works only in the browser that asked for it (cookie `bv_n`); the link works anywhere. The issues —
`content/pregled/<date>-<slug>.md`, a page `/pregled/<slug>/` each, sent by the worker after the owner approved a
preview — are described under "Sending the issues" at the end of this section.

**Flags** in `content/data/site.json`: `accounts.enabled`, `pregled.enabled`, `pregled.day` (`ponedeljak` … `nedelja`;
the texts say "stiže petkom", "u petak", and so do the e-mails), and, when switching on, `since` (DD.MM.YYYY, the day it
goes live) in each: the privacy policy dates the change with it (`{{NALOG_OD}}`, `{{PREGLED_OD}}`), and a build with a
feature on and no `since` stops.

- Off: the pages are still built (`/nalog/`, `/pregled/`, `/pregled/potvrda/`, `/pregled/odjava/` and their /en/, /ru/),
  but noindex, not in the sitemap, not in the site search and not linked from anywhere. The privacy policy shows none of
  the new text, and nothing else on the site changes.
- On: `accounts` — a person icon in the header before search (`/nalog/`, "Moj nalog"; a dot while the non-HttpOnly
  cookie `bv_in=1` exists; the page itself stays noindex and out of the sitemap). `pregled` — `/pregled/` indexable and
  in the sitemap, a sign-up box (`templates/_pregled_box.html`) at the end of every news item, on `/vesti/` and on
  `/javno-punjenje/` (topic "cene"), the opt-in checkbox at sign-in and the newsletter section in the account.
- Privacy policy text for either state: markers `<!--nalog-->`, `<!--nonalog-->`, `<!--pregled-->`, `<!--nopregled-->`,
  `<!--posta-->` (either feature on — the site sends e-mail) and `<!--noposta-->`, handled like the PostHog markers
  (3.16); front matter `lead_nalog`, `description_nalog`, `lead_consent_nalog`, `description_consent_nalog`. Put a marker
  pair inside one line or around whole lines only: the removal also eats the line break after a closing marker.
- The same markers (and `lead_nalog`, `description_nalog`) work in `content/pomoc/*.md`: /pomoc/privatnost/,
  /pomoc/brisanje-komentara-i-fotografije/ and /pomoc/kako-radi-mapa/ say "no accounts" / "only in this browser" while
  accounts are off and describe the account when on; such a page then shows `since` as its update. On /mapa/ the „Imam
  Teslu“ tooltip and the empty „Omiljeni“ text (`fav_none`) change the same way (build.py, `templates/mapa.html`). A new
  text that says the site has no accounts or keeps something only in the browser needs the same pair.
- QA builds: `BV_QA_ACCOUNTS=1 BV_QA_PREGLED=1 python3 build.py` (`=0` forces a feature off). The EN/RU texts of all
  four combinations are in the translation memory (0 left in Serbian on 29.09.2026). `i18n.py prune` keeps only the
  texts of the build in `dist/`, so prune from all four: after each QA build save its keys
  (`python3 scripts/i18n.py keys /tmp/k-11.json`, then `k-10`, `k-01` for the builds with `=1 =0` and `=0 =1`), build
  normally and run `python3 scripts/i18n.py prune /tmp/k-*.json`. The same works for the PostHog texts (3.16).

**Backend** — `worker/_worker.js`, section "accounts and the newsletter"; every table is created by the worker on first
use, `worker/schema.sql` documents them: `users`, `auth_codes`, `sessions`, `favs`, `subs`, `consents`, `suppressions`
(and `mail_log` in log mode); `checkins` and `photos` get a `uid` column. The worker counts the schema as ready only
when every statement worked (the one expected error is the `uid` column being there already); otherwise the next request
tries again. An `auth_codes` table of the older shape (one code per address) is replaced: its rows live 15 minutes.
build.py writes the worker's `CFG` line (the city slugs of `gradovi.json`, the newsletter's day).

| Endpoint | What |
|---|---|
| `GET /api/nalog/status` | `{mail}` — can the site send mail (cached 60 s) |
| `POST /api/nalog/kod` | `{email, lang, opt_in?, hp, t}`: code + link by mail, sent after the answer. The code belongs to this browser: cookie `bv_n` (random, HttpOnly, Secure, `Path=/api/nalog`, 15 minutes; the app sends `app: true` and gets `nonce` in the answer instead); asking again from the same browser replaces its code, other browsers keep theirs. Limits: 30 a day per IP fingerprint (mobile networks put many people behind one address); per address from one IP fingerprint 5 an hour and 10 a day; 30 a day per address from everywhere |
| `POST /api/nalog/potvrdi` · `/link` | the code of this browser's `bv_n` (or the app's `nonce`; 5 attempts, then only that code is gone; from one IP fingerprint at most 30 failures a day, then 429) or the link's token → session: cookies `bv_s` (HttpOnly, `Path=/api`) and `bv_in` (hint), 90 days; `{app: true}` returns the token instead, for `Authorization: Bearer` in a native app. `/link` with `{token, peek: true}` only returns the masked address, for the card before the click |
| `GET /api/nalog/ja` | account, favourites, newsletter, `user.owner` (a short hash of the account id for `bv:fav-owner`); renews the session (and cookies) at most once an hour |
| `POST /api/nalog/odjava` · `/podesavanja` · `/omiljeni` · `/pregled` · `/obrisi` | sign out (`all`), car/DC/Tesla/city/language, favourites (`add`, `remove`, `replace`; only ids on /mapa/, at most 300), the newsletter from the account, delete (`confirm: "OBRISI"`) |
| `GET /api/nalog/doprinosi` · `/izvoz` | own reports and photos; everything stored, as a JSON download. A photo waiting for review has no id in either (its id alone opens it) |
| `POST /api/posta/prijava` | newsletter sign-up `{email, lang, topics?, src}` (or `{token}` to sign up again): answered at once; pending + confirmation mail after the answer. `src` is kept only when it is a page path (`^/[a-z0-9/-]{0,79}$`), otherwise `nepoznato`: the sources the server writes itself (`confirm-click`, `nalog`, `one-click`, …) cannot come from a request. 20 a day per IP, 3 a day per address |
| `POST /api/posta/potvrdi` · `GET /api/posta/stanje?t=` · `POST /api/posta/podesavanja` | the button on /pregled/potvrda/ (→ on, consent row `confirm-click`, welcome mail once); state; topics, frequency, language |
| `POST /api/posta/odjava?t=` | one-click unsubscribe (RFC 8058; no origin check, idempotent); `{token}` from the page. A GET goes to `/pregled/odjava/` and changes nothing |
| `POST /api/posta/resend` | Resend's webhook, signed by Svix (below): a hard bounce or a spam complaint → the newsletter of that address off (`bounce`, `complaint`) and the address into `suppressions`; other events are ignored. One Resend team sends for BlokVolt and Evolako and every endpoint of the team gets the events of both: only events whose `data.from` is at the domain of `MAIL_FROM` count, the rest are answered `{ignored, other_sender}` and nothing is stored |
| `GET /api/admin/posta` | owner's key: users, subscribers on / pending / off, subscribers by language, suppressed addresses (runs the cleanup first); `pregled`: the issues with their rows by status, previews and clicks per link, today's sends and the cap |
| `POST /api/admin/posta` | owner's key, `{"stop": "<slug>"}`: the issue's queued rows are cancelled at once and it is never queued or sent again (below) |
| `POST /api/posta/tick` | the sender (below): public, no origin check, idempotent, one at a time and one a minute (`{skipped: "busy"}`); counts only in the answer |
| `GET /api/posta/klik?i=<slug>&l=<n>` | the links in the issues: 302 to link n of the issue's table (www.blokvolt.rs or blokvolt.com only, else /pregled/); counts per issue, link and day |

Answers never tell whether an address has an account or a subscription, not even by their timing: `/nalog/kod` and
`/posta/prijava` answer before any mail work (`ctx.waitUntil`), so a failed send is only logged ("mail not sent: …") and
the reader has „Pošaljite ponovo“. All POSTs except the one-click and the webhook need the site's origin and
`content-type: application/json`; a known path with another method answers 405. On ~2 % of the requests (and on every
`/api/admin/posta`) the worker deletes expired codes and sessions, consent histories 3 years after their last
withdrawal, and unconfirmed sign-ups older than 30 days: their consent rows stay as proof, with a row "isteklo", but
keep only `sha256:` of the address (at most 50 sign-ups a run).

**Mail** goes through Resend (`POST https://api.resend.com/emails`, 8 s timeout, one retry with the same
`Idempotency-Key`). Every send first looks the address up in `suppressions` (SHA-256 only): an address that bounced for
good or marked a mail as spam gets no welcome mail and no issues, and the API answers exactly as if they had been sent;
a sign-in code and a confirmation link, which the reader asks for, still go out. A successful sign-in lifts `bounce`; a
confirmed sign-up and switching the newsletter on in the account (a proved address, an explicit act) lift `bounce` and
`complaint`. Newsletter mail carries `List-Unsubscribe` (the one-click URL and
`mailto:hello@blokvolt.com?subject=odjava`) and `List-Unsubscribe-Post`. Three templates in SR/EN/RU (code,
confirmation, welcome): tables, inline styles, 600 px, no remote images, a text part. A `mailto` unsubscribe lands in
hello@blokvolt.com and is handled by hand in the D1 console:
`UPDATE subs SET status = 'off', off_at = unixepoch(), off_reason = 'mailto' WHERE email = '…';` and
`INSERT INTO consents (email, kind, granted, text_v, src, at) VALUES ('…', 'pregled', 0, 'pregled-v1', 'mailto', unixepoch());`

**Favourites in the browser.** `bv:fav` and `bv:tesla` stay the map's local copy; `bv:fav-owner` says which account the
list belongs to (`user.owner`). On sign-in (and on the map with a session): the same owner → both lists joined; another
owner → the signed-in account's list replaces it, never mixed; no owner and stations the account does not have → /nalog/
asks („U ovom pregledaču ima N omiljenih punjača. Dodati ih u nalog?“ — Dodajte / Ne) and the map leaves the list alone
until then. Signing out („Odjavite se“, „… sa svih uređaja“) and deleting the account remove all three keys from the
browser.

**Secrets and variables** — set by the **owner** in Cloudflare Pages → blokvolt → Settings → Variables and Secrets
(Production), then a redeploy; never type them yourself:

- `RESEND_API_KEY` — **Secret**. Without it every endpoint that must send mail answers 503 `mail_off` and /nalog/ says
  „Prijava trenutno nije dostupna“: this is the backend's real off switch.
- `RESEND_WEBHOOK_SECRET` — **Secret**, for bounces and complaints. In Resend → Webhooks → Add endpoint: URL
  `https://www.blokvolt.rs/api/posta/resend`, events `email.bounced` and `email.complained`; copy the endpoint's signing
  secret (`whsec_…`) into this Pages secret and redeploy. The same Resend team has Evolako's own endpoint (its Supabase
  function `resend-webhook`); each endpoint has its own secret and ignores the other brand's mail. The worker checks the Svix signature (headers `svix-id`,
  `svix-timestamp`, `svix-signature`; HMAC-SHA256 of `id.timestamp.body`, constant-time compare, at most 5 minutes of
  clock difference) and answers 401 to anything else; without the secret it answers 503, and Resend retries later.
  A suppression is lifted by hand in the D1 console: `DELETE FROM suppressions WHERE email_hash = '<hex>';` where the
  hex is `printf '%s' 'adresa@example.com' | sha256sum` (the address trimmed and in lower case).
- Optional: `MAIL_FROM` (default `BlokVolt <obavestenja@mail.blokvolt.com>`), `MAIL_REPLY_TO` (default
  `hello@blokvolt.com`; also the only address the previews and the sender's notices go to), `SITE` (default
  `https://www.blokvolt.rs`), `PREGLED_DAILY_CAP` (newsletter mails per UTC day, default 30; `0` pauses the sending). Never
  set `MAIL_MODE` in production (`log` is for local tests: mail goes to D1 and the cookies lose the Secure flag).
- In Resend (the owner's account): add the domain `mail.blokvolt.com` in the region **Ireland (eu-west-1)** — the privacy
  policy says "EU region" — enter the DNS records Resend shows at Spaceship (blokvolt.com) without touching the
  Spacemail records of the root domain, wait for "Verified", then create an API key with sending access to that domain only.

**Switching on**, in this order: (1) domain verified, key set, redeploy; `GET /api/nalog/status` → `"mail": true`;
(2) one real sign-in by the owner (code and link arrive; a `/pregled/` sign-up, confirmation, one-click unsubscribe;
`/api/admin/posta`); (3) in `site.json` set `"enabled": true` and `"since": "<today>"` for `accounts` and/or `pregled`;
(4) build (0 left in Serbian), look at /nalog/, /pregled/, a news item, the privacy policy and /pomoc/privatnost/ at 390
and 1440 px, add the line to `izmene.md`, deploy, commit. Switching off again: `"enabled": false` (the accounts keep
working for signed-in readers who have the link); to stop everything at once remove `RESEND_API_KEY` (sign-in and
sign-ups stop, sessions stay).

**Tests** (Miniflare is not a site dependency; install it outside the repo):

```bash
npm install --prefix /tmp/mf miniflare@4
MINIFLARE_DIR=/tmp/mf node scripts/qa/nalog_worker_test.mjs            # the worker: 191 checks, in-memory D1
BV_QA_ACCOUNTS=1 BV_QA_PREGLED=1 python3 build.py
MINIFLARE_DIR=/tmp/mf node scripts/qa/nalog_serve.mjs dist 8788 &    # dist like Pages + the worker, MAIL_MODE=log
python3 scripts/qa/nalog_ui_test.py /tmp/bv-nalog                     # browser flows, screenshots, the rendered mails
```

`nalog_serve.mjs` serves `dist/` with `dist/_headers` (the CSP applies) and the real worker with D1; codes and links are
read from its `/__dev/mail` (local only). `BV_SITE=https://www.blokvolt.rs` makes the links in the mails point to the
real site when you only want to look at them. The sender of the issues has its own tests (see "Sending the issues").

**Privacy.** Codes, links and session tokens are stored only as SHA-256; `bv_s` is HttpOnly, `bv_in` only a hint; the
consent log (time, source, text version, the day's IP fingerprint) is append-only; after an account is deleted, and 30
days after a sign-up nobody confirmed, the consent rows keep only `sha256:` of the address; `suppressions` holds only
hashes too; reports and photos stay on the map without the account. The privacy policy (section `#nalog`) says all of
this — change it when the behaviour changes. The query strings `t=` (newsletter token) and `prijava=` (sign-in link)
never reach the analytics: the pages take them out of the address bar, and bv.js gives PostHog (3.16) a `before_send` /
`sanitize_properties` that strips them from every URL property and from the page address in session replay.

#### Sending the issues (since 29.09.2026)

One Markdown file per issue, `content/pregled/<YYYY-MM-DD>-<slug>.md`, read by `scripts/pregled.py`. The slug is the page
`/pregled/<slug>/` and keys the previews, the queue and the clicks: never change it once a preview went out (and files are
never deleted — an issue that will not go out gets `status: stopped`).

```markdown
---
title: Charge&GO menja cene, pet novih punjača na autoputu
date: 02.10.2026
lead: Jedna rečenica o nedelji — preheader mejla i uvod stranice.
cover: /assets/pregled/2026-10-02.jpg
cover_alt: Brzi punjač na odmorištu pored autoputa
status: draft
send_at: 02.10.2026 08:00
approved_hash:
---
## Nedelja u tri rečenice {#uvod}

Tri kratke rečenice o nedelji.

## Vesti {#vesti}

- [Nacrt zakona o punjačima](/vesti/nacrt-zakona-o-punjacima/): cena po kWh na punjačima od 50 kW.

## Cene javnog punjenja {#cene}

…

## Novi punjači na mapi {#punjaci}

…
```

- **Front matter.** `title` (the H1 and the e-mail's subject), `date` (DD.MM.YYYY), `lead` (under the title; the preheader),
  `cover` (a JPEG under `static/` — WebP works too, but Outlook for Windows does not show it — at least 600 px wide, 1200
  looks sharp on phones, under 200 KB; the build puts `?v=<hash>` on it, and a changed picture changes the approved text),
  `cover_alt`, `status`, `send_at` (Belgrade time; needed from `preview` on), `approved_hash` (empty until the approval),
  optional `description` (the page's meta description, default the lead). Any other key stops the build (a typo would
  otherwise pass silently).
- **Sections.** The body is sections only: `## <heading> {#<topic>}`. Topics: `uvod` — the intro, every reader gets it
  (optional; first, at most once) — and the subscription topics `vesti`, `cene`, `punjaci`; a second section of one topic
  takes a suffix (`{#vesti-2}`). A reader gets the intro plus the sections of their topics, and nothing when the issue has
  none of them. `moji` (changes at the reader's favourite chargers, promised on /pregled/ to account holders) is not built
  yet — it needs a different text per reader — and stops the build. Inside a section: paragraphs, `###` subheadings, lists
  (not nested: the translation would lose the outer item), `>` quotes, bold, italics, links. Links only to
  `https://www.blokvolt.rs/…`, `https://blokvolt.com/…` or a site path (`/mapa/`), and site links must lead to a page. No
  pictures (the cover is the only one), tables or raw HTML. `python3 scripts/lint_sr.py content/pregled/<file>.md` checks
  the Serbian as for news.
- **Statuses.**

  | `status` | the page `/pregled/<slug>/` | what the tick does |
  |---|---|---|
  | `draft` | built, noindex, linked from nowhere | nothing |
  | `preview` | the same | once per text: the issue in sr, en and ru to `MAIL_REPLY_TO` (hello@blokvolt.com) only, subject `[PREVIEW <first 8 of the hash>] <title>`, without List-Unsubscribe |
  | `approved` | public — indexable, in the sitemap and under „Prethodni brojevi“ — while the newsletter is on | from `send_at` on: queues every reader once and sends within the budget, but only while `approved_hash` is a previewed hash and still the hash of the file |
  | `stopped` | noindex, unlisted | cancels the rows still queued |

  The safe side for the pages: nothing the owner has not approved is listed or indexable (a draft is still reachable by its
  address, and the repository is public anyway). The build needs the draft's page: the translation memory reads it.
- **The hash.** The build prints `pregled <slug> (<status>): hash <64 hex>; e-mail sr … KB, en … KB, ru … KB; … links` for
  every issue; the same hash is `hash` in `dist/pregled-mail/<slug>.json`. It is the SHA-256 of what is sent — every word in
  the three languages, every link, the cover's address — so any change after the approval makes another one. A preview or
  approved issue with text left in Serbian, a link to a page that does not exist, or an e-mail of 100 KB or more (Gmail
  clips larger ones) stops the build; a draft only warns.

**The run** (the main session, with the owner):
1. Write the issue with `status: draft` and its cover in `static/assets/pregled/`. Build, `python3 scripts/i18n.py todo`,
   translate (3.9), build again: 0 left in Serbian. The fixed texts of the mail (header, footer) are in the memory already
   (the `bv-i18n-mail` block on /pregled/).
2. Set `status: preview` and `send_at`, build (pack), deploy, commit. The next tick sends the three previews to
   hello@blokvolt.com — at most 30 minutes in the morning window, about 10 minutes when the site has traffic, or at once with
   Actions → Pregled tick → Run workflow.
3. The owner reads the three mails and answers «ок» in the chat. Copy the full hash of that preview (the build output, or
   `hash` in `dist/pregled-mail/<slug>.json`; its first 8 characters are in the preview's subject — they must be the same)
   into `approved_hash`, set `status: approved`, build (the output must show the same hash), deploy, commit. Change nothing
   else in this step: a new hash is not sent (the team gets a notice instead).
4. From `send_at` on, the tick queues the readers and sends. With the default cap of 30 a day a larger list takes several
   days, oldest rows first; each mail is made when it goes out, in the reader's language and topics of that moment, and a
   reader who unsubscribed meanwhile is skipped.

A change after the approval (a typo while rows still wait): sending stops and the team gets «Выпуск … не отправлен: текст
изменился после одобрения» once a day. `status: preview` → deploy → a new preview → «ок» → its hash in `approved_hash` +
`status: approved` → deploy; the rows still waiting go out with the new text, nobody gets the issue twice. Once every row
is done, a correction of the page needs no new approval (the build warns that `approved_hash` differs; nothing is sent). An
approved hash that was never previewed: «Выпуск … не отправлен: хэш одобрения не совпадает с превью».

**Stopping.** `status: stopped` + deploy is the lasting way: the queued rows are cancelled and nothing more goes out. At once,
without a deploy, the owner (with the key; never type it yourself): `curl -X POST https://www.blokvolt.rs/api/admin/posta -H
'Authorization: Bearer <ADMIN_KEY>' -H 'content-type: application/json' -d '{"stop":"<slug>"}'` — cancels the queued rows
and marks the issue stopped in D1 (`pg_issues.stopped_at`), so it is never queued or sent again whatever its file says.
Undo in the D1 console: `UPDATE pg_issues SET stopped_at = NULL WHERE slug = '…';` and
`UPDATE pg_queue SET status = 'queued' WHERE slug = '…' AND note = 'admin';`. `PREGLED_DAILY_CAP=0` pauses all sending
(previews and notices still go out); the newsletter switched off in `site.json` makes the tick do nothing; without
`RESEND_API_KEY` no mail goes out at all.

**Budget.** `PREGLED_DAILY_CAP` (Pages variable, optional, default 30) newsletter mails per UTC day; at most 25 per tick
(10 per background tick), about 2 a second (Resend's rate for the whole team — Evolako sends through it too), and within 45
D1 calls and fetches per tick (the free Workers plan allows 50 per request). Resend's own quota (the free plan: 100 a day,
3,000 a month) is shared with the sign-in codes and confirmations: keep the cap well under it. A 429, a 5xx or a timeout ends
the tick and the row waits (failed after 5 attempts); 401 or 403 (the key or the domain) ends it without counting and tells
the team once a day («Рассылка выпуска … остановлена: Resend отвечает 401»); any other refusal fails only that row.

**The tick.** `POST /api/posta/tick` does all of it, from three sources: `.github/workflows/pregled-tick.yml` (every 30
minutes 05:00–09:59 UTC and at 13:23 and 19:23 UTC — 12 runs a day), every normal `/api` request after its answer at most
every 10 minutes, and by hand (`curl -X POST https://www.blokvolt.rs/api/posta/tick`, or Run workflow). The one-row table
`pg_lock` lets one tick run at a time and one a minute; the others answer `{"ok":true,"skipped":"busy"}`. The answer:
`{ok, issues: [{slug, action, queued, sent, cancelled, failed, reason, send_at}], sent, sent_today, cap, stop}` — actions
`none` (draft), `preview_sent`, `previewed`, `preview_failed` or `later` (tried again next tick), `blocked` (`reason`: `not_previewed`,
`hash_changed`), `waiting` (before `send_at`), `enqueued`, `sending`, `done`, `stopped`; `stop` is why sending ended early
(`cap`, `budget`, `time`, `resend_429`, `resend_503`, `resend_timeout`, `resend_401`, …). No address is ever in it. Newsletter
off: `{"ok":true,"skipped":"off"}`; no `RESEND_API_KEY`: 503 `mail_off`; the deploy without `/pregled-mail/index.json`:
503 `no_index`.

**Click counter.** Every link in an issue is `https://www.blokvolt.rs/api/posta/klik?i=<slug>&l=<n>`: n is a line of the
issue's link table (`links` in its file, written by the build; each language's links are their own lines; the settings and
unsubscribe links are not counted). The worker redirects only to www.blokvolt.rs and blokvolt.com (anything else to
/pregled/) and counts per issue, link and day in `pg_clicks` — no IP, no cookie, nothing about the reader. Mail scanners that
open links and the team's clicks in the previews count too.

**After a send**, check: `GET /api/admin/posta` with the owner's key → `pregled.issues[]` — `rows` (queued / sent / failed /
cancelled), `previews`, `enqueued_at`, `clicks` per link with its URL, and `sent_today` against `cap`; the hello@ inbox for
notices; bounces and complaints come through the Resend webhook as before (suppressions); Resend's dashboard (tags `kind`
`pregled` and `issue` = the slug). In the D1 console:
`SELECT status, note, COUNT(*) FROM pg_queue WHERE slug = '…' GROUP BY status, note;` — `note` says why a row was cancelled
(`off` = unsubscribed meanwhile, `suppressed`, `topics`, `stopped`, `admin`, `obrisan` = account deleted) or failed
(`resend <status>`).

**Files and tables.** The build writes `dist/pregled-mail/<slug>.json` — `{slug, date, month, title, send_at (UTC), status,
approved_hash, hash, topics, links, langs: {sr|en|ru: {subject, preheader, head_html, head_text, sections: [{topic, html,
text}], foot_html, foot_text}}}`, the reader's links as `{{PREFS}}` and `{{UNSUB}}` — and `index.json` (the same without
`links` and `langs`), served noindex and no-store (`_headers`), in no sitemap and no search; only the worker reads them
(`env.ASSETS`). Tables (created by the worker; `worker/schema.sql`): `pg_previews`, `pg_issues`, `pg_queue` (one row per
issue and reader; the address is removed 60 days after the row is done and at once when the account is deleted; the
account's export lists the issues sent to it), `pg_clicks`, `pg_lock`. Nothing in `content/podaci/izmene.md` until the
first issue.

**Tests.**

```bash
MINIFLARE_DIR=/tmp/mf node scripts/qa/pregled_sender_test.mjs       # the sender: 80 checks, issue files written by the test
python3 scripts/qa/pregled_build_test.py                             # the build side and three builds (--quick: without builds)
BV_QA_ACCOUNTS=1 BV_QA_PREGLED=1 BV_QA_PREGLED_FIXTURE=1 python3 build.py
MINIFLARE_DIR=/tmp/mf node scripts/qa/nalog_serve.mjs dist 8788 &
python3 scripts/qa/pregled_ui_test.py /tmp/bv-pregled                # end to end: previews, approval, the readers' mails, clicks
```

`BV_QA_PREGLED_FIXTURE=1` adds the test issue `scripts/qa/fixtures/pregled/2026-09-25-qa-probni-broj.md` (made of texts
already in the translation memory) as a preview; `=approved` (or another status) builds it with that status, and approved
takes its own hash — QA builds only. Build again without it before packing.

### 3.28 Protecting the map data from copying (since 06.10.2026)

The owner's rule: **nothing may affect real readers in any scenario** — a measure that could touch a person, a browser
extension, an app or another site we run is not used. Everything shown to a person can be copied (the same way the
robot reads the networks' apps); the aim is to make bulk copying slower, provable and pointless (the data ages).

In use:
1. **Terms of use** — `/politika-privatnosti.html#uslovi`: the database (lists, prices per connector, checks, notes) is
   protected as a database maker's right (ZASP čl. 137–140a, 15 years); systematic extraction and automated collection
   need written consent; text and data mining is reserved for the data files. Open parts and their licences: punjaci.json
   ODbL (OpenStreetMap's condition), the CSV downloads CC BY-NC 4.0 from 06.10.2026 (copies taken before stay CC BY).
2. `robots.txt`: `Disallow: /assets/map/` (with `Allow: /assets/map/punjaci.json`), `/api/`, `/app/`. Pages stay open to
   search engines and AI (llms.txt).
3. Headers on `/assets/map/*`: `X-Robots-Tag: noindex`, `TDM-Reservation: 1`, `TDM-Policy` (the terms);
   `/.well-known/tdmrep.json` says the same. `Access-Control-Allow-Origin: *` stays (evolako.rs reads the data; apps).
4. **Watermark**: dopune.json coordinates get a 7th decimal from `sha1(id|YYYY-MM of checked)` (+1…9 × 1e-7°, ≤ 0,1 m;
   shown rounded to 5 decimals): a copy shows what was taken and when. Texts of "how to find" and notes are our own words.
5. **Trap link**: `/api/zamka` (hidden in /mapa/, `rel=nofollow`, `aria-hidden`, `tabindex=-1`, disallowed in robots)
   only counts visits per day and fingerprint in D1 (`trap`), returns 204 and blocks nobody. Readers never see it.
6. Write limits on `/api/*` as before; reads are not limited for people.

Rejected (could touch people): CAPTCHA/Turnstile on reading, Cloudflare Bot Fight Mode (breaks native apps), blocking by
IP/ASN/VPN (mobile carriers' CGNAT), restricting CORS to our domains (could break the apps or a page we forgot), fake
stations or poisoned data, sign-in for the map, text as images, loading details lazily (poorer offline).

### 3.29 Display currency (RSD / EUR / USD)

Built 06.10.2026 (founders' decision; the shared spec for Evolako and BlokVolt is `VALUTA_SPEC_2026-10-06.md` in the
project docs). The reader can show sums in euros or dollars; **RSD is the default, always** (no guessing by language,
country or locale), and with RSD every page looks exactly as before. EUR and USD are only what the reader chose: the
switcher next to the language menu (on phones under 440 px it is in the burger menu, „Valuta“), or a link with
`?cur=eur|usd|rsd` (sets and remembers it; anything else is ignored). The choice is kept in `localStorage` `bv:cur` and,
for a reader signed in to "Moj BlokVolt" (3.27), in the account (`users.valuta`, `POST /api/nalog/podesavanja {valuta}`);
on sign-in /nalog/ applies the account's choice, and an account that never chose takes the browser's. Other currencies
(ruble, KM, denar, forint) were considered and rejected — do not add them without the owner.

BlokVolt sells nothing, so every converted sum is a reference sum: the chosen currency first, the dinars after it,
quieter — „≈ 0,49 €/kWh · 58 RSD/kWh“; in tight places (list rows, pin labels) only the converted sum, the dinars in the
tooltip and the card. Where a price is the whole content of a cell or a card line (class `fx-1`), the dinars go under it.
Number format as everywhere on the site: Serbian on every language („≈ 1.064 €“, „≈ 8,43 €“, rates „≈ 0,50 €/min“, under
0,10 three decimals „≈ 0,010 €/min“), `≈` always except for 0. A footnote under the page's main content (only with EUR/USD
and only on pages with converted sums): „Iznosi u evrima i dolarima su informativni, po srednjem kursu NBS na {datum}. Na
punjačima i u računima cene su u dinarima.“ (EN/RU from the translation memory, block `bv-fx-i18n` in `base.html`).

**What converts** — only prices marked in the HTML (`data-rsd`, `data-rsd-lo/hi`, `data-unit`, `data-rate`; the core
`static/assets/fx.js` converts them in the browser):
- the price index and its archive (`_indeks_tabela.html`, cards `_price_summary.html` on /javno-punjenje/ and /mapa/, the
  „43–79 RSD“ stat, the network list), the history page, the network pages (price fact, table, earlier prices);
- firm prices: the register lists (`_firm_list.html`, /firme/, the sub-hubs, /cena-punjaca…), the firm page's price fact,
  city pages; a price a firm publishes in euros stays as published;
- data pages `/podaci/*`: the price cells of their tables (`valuta.fx_tables`: a cell with „<number> RSD“, or a number
  under a header with „(RSD)“) — wallbox models, registration, insurance, tolls, rentals; the EPS tariffs table is marked by
  `scripts/gen_tarife_eps.py`. EV prices are published in euros: nothing to convert;
- calculators: their results (the inline scripts write `data-rsd` and call `bvFx.render`), the tariff table of the cost
  calculator. **Input fields stay in RSD** with their „RSD“ labels and presets (they are copied from Serbian bills);
- the map (`map.js`, a small block „display currency“): the card's price and its per-kWh estimate in full, the list and
  the pin labels only converted (pins in ASCII: „~0,58 EUR/kWh“). The neighbouring countries' layer and the country maps
  of blokvolt.com (their own currency, no `window.bvFx`) never change.

**Never converted** (nothing there is marked): the prose of guides, news and data pages (authors' text with quoted
sources), the media kit and the ad price (/za-firme/oglasavanje/, its PDFs), legal pages, /pregled/ and the newsletter
e-mails, /admin/, the account page's texts, blokvolt.com (no switcher there, `valuta.js` is not loaded). In the map card
the receipts, the idle fee and the notes stay in dinars.

**How to mark a new price.** In a template `{{ value|fx }}` (every „<number> RSD[/unit]“ of a data string gets the markup;
`fx(stack=False)` keeps it inline) or `{{ fx_num(v, rate=True, text=…) }}` for one number; in Python `valuta.fx_num`. The
visible text never changes. Never apply it to prose, to quotes from a firm's site, or to anything in the "never" list.

**The rate.** `GET /api/kurs` (worker): `{"base":"RSD","source":"NBS srednji kurs","date":"2026-10-05","rates":{"EUR":117.4948,
"USD":105.0468},"fetchedAt":"…","stale":false}` — the middle rate of the National Bank of Serbia from kurs.resenje.org
(`exchange_middle ÷ parity`, `/api/v1/currencies/eur|usd/rates/today`), checked EUR 100–140 and USD 80–140, kept 6 hours in
the Cloudflare cache and as the last good value in D1 (table `kurs`, created on first use); the source down → the last good
value with `stale: true`; nothing stored → the constants with `stale: true`. CORS `*`, `Cache-Control: public, max-age=3600`;
evolako.rs and the BlokVolt app (manifest `api.kurs`) read it too. The browser keeps a rate 6 hours (`bv:cur:kurs`) and
without one uses the constants. **The fallback constants (05.10.2026) are in three places**: `static/assets/fx.js`
(`FALLBACK`), `worker/_worker.js` (`KURS_FALLBACK`), `scripts/valuta.py` (`FALLBACK`, the app feed) — `build.py` stops when
they differ. Update them with each app release (spec §2).

**The core is shared.** `static/assets/fx.js` is a copy of the core that evolako.rs uses too (`FxCore`, version in its
first line). Its unit tests (`fx.test.js`, jsdom: the spec's table, rounding, formats, parsing, DOM) are kept with the master
copy outside this repository; change the core there, run the tests, and copy the identical file to both sites. The BlokVolt
side lives in `static/assets/valuta.js` (instance with `numLang: 'au'` — only the map scans text, and it mixes the page's number format with Serbian-format price data — switcher, footnote, account) and `scripts/valuta.py`.

**Adding a currency later** (only on the owner's decision): add the code to `CODES`, `SYM`, the texts `TX.names` and the
sanity bounds in `fx.js` (+ the Evolako copy and tests), to `KURS_BOUNDS`, `kursUpstream` and `kursOut` in the worker,
`VALUTE` (account setting), `FALLBACK` in all three files, the option texts in `bv-fx-i18n` (`base.html`, then 3.9), and
the spec. The footnote names euros and dollars — reword it with the owner.

**Tests.**

```bash
node fx.test.js                                                     # the core, next to its master copy (see above)
python3 scripts/qa/valuta_build_test.py                             # the markup and i18n keys (22 checks, no build)
MINIFLARE_DIR=/tmp/mf node scripts/qa/kurs_worker_test.mjs          # /api/kurs: format, cache, D1, stale, constants (25)
MINIFLARE_DIR=/tmp/mf node scripts/qa/nalog_worker_test.mjs         # includes the account's valuta
python3 scripts/qa/cfserve.py dist 8787 &
python3 scripts/qa/fx_test.py /tmp/bv-fx-shots [--before <server of a build without the change>]
```

`fx_test.py`: RSD by default with no conversion (and, with `--before`, the same text as the other build), EUR by the
switcher with the `currency_changed` event, after a reload, `?cur=usd`, the price index, a network page, firm prices, data
tables, both calculators (inputs in RSD, a new input repaints, back to RSD shows the new result), the map card, list and
pins, the never-converted pages, the EN/RU footnote and tooltip, the switcher in the burger menu at 360 px, no horizontal
scroll at 360/768/1440, and screenshots. cfserve has no `/api/kurs` (404): the pages must use the constants silently.

### 3.30 The growing EV fleet estimate (since 10.10.2026)

The owner's decision (10.10.2026): the fleet number on the home page and on /podaci/statistika-ev-srbija/ is an
estimate that grows by itself, not the frozen MUP figure. `content/data/site.json` → `ev_counter`:
`anchor` = the last official fleet (`base`, MUP) + new BEV passenger-car registrations since `base_date` (SAUVD),
valid at the end of `anchor_date`; then `rate_per_day` (average of the period base → anchor), in steps of
`step_hours`, for at most `max_days` (then it stops). `build.py` writes the value at build time; `static/assets/bv.js`
recomputes it from `data-evc` on every page view and every 10 minutes — no rebuild is needed for it to move.
Home tile: `home_stats` entry with `"b": "auto:ev"`; in Markdown: `[[evc]]`.

Update when SAUVD publishes a new period or MUP gives a new fleet figure: recompute `anchor`/`anchor_date`
(e.g. SAUVD full year 2026: base + (BEV 2026 − Q1 2026)), `rate_per_day` = new BEV since `base_date` ÷ days, then
the "Kako se računa procena" block on the statistics page (its numbers), `izmene.md`, EN/RU todo. With a new MUP
figure: new `base`/`base_date`, `new_since_base` = 0 if MUP is newer than the last SAUVD period. Used imports, vans
and deregistrations are not counted — the page says so; keep it that way unless a dated source gives them.

## 4. Build and check

```bash
bash scripts/pack.sh      # build.py + check_links.py + /mnt/user-data/outputs/blokvolt-dist.zip (+ .cf/part-N, section 5)
```

Local checks (the container cannot reach blokvolt.rs or the map tiles) are in `scripts/qa/`:

```bash
python3 scripts/qa/cfserve.py dist 8787 &          # like Cloudflare Pages, with dist/_headers
python3 scripts/qa/qa_all.py sr,en,ru 360,768,1440 # every sitemap URL: JS/CSP errors, overflow, images, footer
python3 scripts/qa/map_ui_test.py /tmp/bv-shots    # map cards, reports, photos, favourites (fake /api)
python3 scripts/qa/map_extra_test.py /tmp/bv-shots # dopune.json facts, „Imam Teslu“, pin prices, „Gde tačno“, EN/RU
python3 scripts/qa/map_v2_test.py                 # per-connector prices, Kako se puni, Moj auto (RSD/km), Najbliži, hours, cable, EN/RU
python3 scripts/qa/map_region_test.py             # the region layer
python3 scripts/qa/vis_shots.py /,/vesti/ /tmp/bv-shots   # full-page screenshots, desktop and phone
python3 scripts/qa/fx_test.py /tmp/bv-fx-shots      # display currency: RSD unchanged, EUR/USD, never-converted pages (3.29)
```

`cfserve.py` reads `dist/_headers` when it starts: restart it after a build that changed an inline script (calculators),
or the browser blocks the script by the old CSP hashes. Stop it by its PID (`kill $!` right after starting it, or save
`$!` to a file) — never with a pattern that could hit other servers.

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
3. Upload the zip. The `file_upload` tool takes at most 10 MB per file and the zip is bigger (12.6 MB on
   25.09.2026, with the news photos and the APK), so `pack.sh` also cuts it into parts of at most 9 MB in
   `/mnt/user-data/outputs/.cf/` and prints "deploy parts: N" and the zip's size and SHA-256 prefix. The browser's
   `file_upload` accepts only files the session may read: if it rejects `/mnt/user-data/outputs/…` (28.09.2026 it
   did), pack into the working area instead — `bash scripts/pack.sh /home/claude/deploy/blokvolt-dist.zip` puts the
   parts in `/home/claude/deploy/.cf/` — and upload from there; the same for the payload of section 6. Add one
   helper input per part (set `n` to N):
   ```js
   const n=2; for(let k=0;k<n;k++){let i=document.getElementById('bvp'+k); if(!i){i=document.createElement('input');i.type='file';i.id='bvp'+k;i.setAttribute('aria-label','bvpart '+k);document.body.appendChild(i);}} 'ok'
   ```
   `find` "bvpart 0" → ref → `file_upload` with `/mnt/user-data/outputs/.cf/part-0`; the same for part-1 and
   so on, one part per call. Then join the parts in the page and hand the zip to Cloudflare's zip input:
   ```js
   await (async()=>{const n=2; const parts=[...Array(n).keys()].map(k=>document.getElementById('bvp'+k)?.files?.[0]);
   if(parts.some(p=>!p)) return 'a part is missing';
   const f=new File(parts,'blokvolt-dist.zip',{type:'application/zip'});
   const h=[...new Uint8Array(await crypto.subtle.digest('SHA-256',await f.arrayBuffer()))].map(x=>x.toString(16).padStart(2,'0')).join('').slice(0,16);
   const z=document.querySelector('input[type=file][accept*="zip"]'); if(!z) return 'no zip input yet';
   const dt=new DataTransfer(); dt.items.add(f); z.files=dt.files; z.dispatchEvent(new Event('change',{bubbles:true}));
   return f.size+' '+h;})()
   ```
   The size and hash must equal the ones `pack.sh` printed; if not, reload the page and upload the parts again.
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

A scheduled run sees the browser only when its scheduled task is linked to the owner's Mac: the task needs
"Require this computer" switched on in Claude Desktop on that Mac (on 25.09.2026 no BlokVolt task had it, and
a run without it found neither the Claude in Chrome tools nor the remote-devices tools). If the tools are
missing, say this in the report too: to deploy from that session the owner opens it in Claude Desktop on the
Mac and links it to the computer before replying 'деплой'.

## 8. Report to the owner

Short, in Russian: what changed (with the numbers), what was checked without changes, what could not be
checked and why, what the owner should do (screenshots, logins). No long documents.
