# BlokVolt — maintenance runbook

How www.blokvolt.rs is kept current: what to check, where each fact lives, how to build, deploy and
commit. Written for the people and the scheduled Claude sessions that run the monthly updates.
Everything below uses only the owner's already signed-in browser; no API tokens or passwords are ever
needed or handled.

## 0. Editorial rules (short version of /metodologija/)

- Publish only public, verifiable facts, each with a source URL and a date. Copy prices literally;
  our own conversions go in parentheses (PDV 20 %, 117,2 RSD/€). If something cannot be verified,
  leave the old value, keep its old date, and mention it in the report — never guess.
- Same columns and the same rules for every firm and network, including Evolako ("naša ponuda").
  No ratings, rankings, logos, affiliate links or paid placements. Missing information is written as
  "Ne pominje se", never as "ne".
- App screenshots and receipts: use only the price, tariff, station name, power, kWh, amount, duration
  and date. Never publish account names, e-mails, phone numbers, card digits, fiscal/receipt numbers,
  car plates or anything that shows where the owner was at what time (use the month, not the exact
  timestamp, for receipts).
- No personal names of the team anywhere in the repo or on the site.
- Site copy is Serbian (Latin script), calm and factual.
- Every public change gets a line in `content/podaci/izmene.md` (newest date section on top). Notable
  changes also get a short item at the top of `news` in `content/data/site.json` (the home page shows
  the first `news_on_home` items).
- Do not delete files (the GitHub web upload cannot delete anyway). Do not touch other sites or projects.

## 1. Setup in a fresh container

```bash
git clone https://github.com/hemptoon/blokvolt-rs && cd blokvolt-rs
pip install --break-system-packages -q jinja2 markdown beautifulsoup4
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
| Home stats and news | `content/data/site.json` → `home_stats`, `news` | Stats mirror /podaci/statistika-ev-srbija/ and the free-charger count. |
| Fuel prices (calculator) | `content/data/kalkulator.json` → `fuel` | `date` = first day the prices apply, `valid_to`, `benzin` (BMB 95), `dizel` (evrodizel), `url`. |
| EPS tariffs, fees, taxes | `content/data/kalkulator.json` → `eps`, `checked` | Zones VT/NT without taxes, `oie`, `ee`, `akciza`, `pdv`, `snaga_rsd_kw`, `sources` (+date). |
| Public charging price for the calculator | `content/data/kalkulator.json` → `public`, `public_checked`, `public_basis`, `public_range` | `dc` = average RSD/kWh of recent DC receipts; `ac` = Charge&GO AC 22 kW per-minute price × 60 ÷ 11 kW; `public_range` = min–max RSD/kWh of the DC receipts. |
| Public charging price index | `content/javno/indeks-cena.json` | `updated`, `next_check` (a month name is fine), `rows` (schema below). |
| Charging networks | `content/operateri/<slug>.json` | Edit these JSON files directly. `scripts/add_operators.py` is a historical import — never re-run it. `prices` is the full dated history shown on the network page; `verified` = last check. |
| Free chargers | `content/javno/besplatni-punjaci.md`, `content/operateri/putevi-srbije.json` | The count (36 installed / 31 working) is repeated elsewhere — see sync points. |
| EPS tariffs page | `content/data/kalkulator.json` (+ `tarife_next_check`) | Then run `python3 scripts/gen_tarife_eps.py` — the page `/podaci/tarife-eps/` is generated, never edited by hand. Night-tariff hours per region and the single-tariff prices live in the same `eps` block. |
| Wallbox model prices | `content/data/wallbox-modeli.json` | The model-level view of the firm register: re-derive it from `content/firme/*.json` at the quarterly revision, then run `python3 scripts/gen_wallbox.py`. |
| Building-billing calculator | `content/data/kalkulator-zgrada.json` | Defaults and the MID meter price range (taken from the register); the page `/alati/racun-u-zgradi/` is a template, no generator. |
| New EV prices | `content/data/ev-modeli.json` | Then run `python3 scripts/gen_ev_modeli.py` (regenerates `/podaci/cene-elektricnih-automobila/`). Update `checked` and `next_check` in the JSON. `subsidy_eur` drives the "after subsidy" column. |
| Rentals, regional charging | `content/data/rent-carsharing.json`, `content/data/region.json` + the pages `content/podaci/rent-a-car-i-car-sharing.md`, `content/javno/region.md` | The pages are hand-written from the JSON; edit both. |
| All other data pages | `content/podaci/*.md`, `content/javno/*.md` | Front matter: `updated`, `next_check`, `modified` (ISO), `sources` (`Label :: URL | Label :: URL`). |
| City pages | `content/data/gradovi.json` | One entry per `/gradovi/<slug>/`: `aliases` matched inside a firm's `city` (a firm can belong to several cities), `regions` matched inside a firm's or operator's `coverage`, `loc`/`acc` the Serbian locative and accusative, `nt_region` one of the regions in `kalkulator.json` → `eps.nt_hours`, `note` one paragraph of local fact (HTML allowed). |
| Firms | `content/firme/<slug>.json` | `verified`, cells/verdicts, `sources`. Leads: `"group": "L", "publish": false` (not shown). |

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
grep -rn "43–79\|36 \|31 u radu\|7\.155\|535\|~220\|4–7 RSD" templates content build.py | cut -c1-160
```

- DC receipt range "43–79 RSD/kWh": `templates/javno_index.html` (stat block), `content/javno/region.md`,
  `content/data/kalkulator.json` → `public_range`.
- State chargers "36 / 31 u radu": `templates/javno_index.html` (stat + sources), `content/javno/besplatni-punjaci.md`,
  `build.py` (javno description), `content/data/site.json` home stat.
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

If no new screenshots arrived, keep the old values and dates; the report tells the owner.

Things that can be checked without the owner: whether the state chargers on motorways are still free
(https://www.putevi-srbije.rs/index.php/en/electric-chargers), network sizes and news on the operators'
sites (chargego.rs, oriontelekom.rs/emobility, emobility.rs, omv.co.rs, nis.rs, tesla.com/findus),
Lidl eCharge, Parking servis Beograd.

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

`content/data/ev-foto.json` maps `"<brand>||<model>"` (the raw keys of `ev-modeli.json`) to a file in
`static/assets/auto/<slug>.png` plus the author, licence name, licence URL and Commons file page.
`scripts/gen_ev_modeli.py` renders the thumbnail in the first table column and the credit list under
`## Fotografije modela`; a model with no entry simply gets no photo (today: JMEV Elight, JMEV EWind).

Rules, non-negotiable: only files from Wikimedia Commons under a free licence (CC0, CC BY, CC BY-SA),
never a press photo, a dealer photo or an image found through a search engine. Copy the author string
and the licence exactly as the file page states them — CC BY-SA requires the author, the licence and
the fact that the picture was changed, all of which the page's credit block carries.

Adding one: open the file page on commons.wikimedia.org, take the 640 px thumbnail, cover-crop to
480x270, then
`Image.resize((240,135), LANCZOS).quantize(colors=128)` and save as PNG (~20 KB) into
`static/assets/auto/`. This container cannot reach wikimedia.org (proxy 403), so the fetch and the
crop happen in the browser on the Commons origin and the bytes come back through the GitHub upload
tab; section 6 describes that transfer. Because `/assets/*` is served `immutable`, a replaced photo
needs a new file name — never overwrite a slug that is already live.

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

### 3.7 Firm register (quarterly revision)

For every published `content/firme/*.json`: open the firm's site and price pages from `sources`,
compare every cell, update values and `verified`. A site that is down twice in a row: note it in the
report, do not unpublish silently. Leads (`group` L, 16 at the time of writing): verify with the same
columns; publish (`publish: true`, proper group) only when the firm's own site confirms what it sells.
After the full pass set `firms_checked` in `content/data/site.json`, log in `izmene.md`, add a news item.

### 3.8 Site search index

`build.py` writes `dist/assets/search.json` from the generated pages (title, description, section,
headings and the first 1.200 characters of body text) and `/pretraga/` searches it in the browser.
Nothing to maintain by hand — but if a page should be findable by a word that is not in its text,
put that word in the page's description.

## 4. Build and check

```bash
bash scripts/pack.sh      # build.py + check_links.py + /mnt/user-data/outputs/blokvolt-dist.zip
```

`build.py` also appends `?v=<hash>` to site.css/agg.css/site.js (they are cached for a year). Look at
the changed pages in `dist/` (grep for the new numbers) before deploying.

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
   (The direct URL `…/deployments/new` does not render the upload form — use the button.)
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
