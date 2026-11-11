# World layer of blokvolt.com in N languages (K8-i18n 10.11.2026, LANG0 11.11.2026)

The world layer (map, world pages, shell, prices) no longer hard-codes EN / SR / RU. Languages come from one registry;
new languages are prepared in `content/world/i18n/<code>/` (L-tasks) and switched on only after gate G8.

## Registry — `content/world/config.json`

- `langs`: code → `hreflang`, `html` (lang attribute), `og`, `code`, `label` (switcher), `script` (latn/cyrl/grek), `dir`,
  `dec`, `thou`, `pct`, `intl` (JS locale), `date` (CLDR short pattern, reference), `plural` (CLDR categories), `months`,
  optional `babel` (locale for plural rules, e.g. `sr_Latn`). `en`/`sr`/`ru` also hold `slugs`; 24 L-languages are generated from Babel
  (`python3 scripts/world_i18n.py registry`).
- `langs_enabled`: `["en","sr","ru"]` — **production**, the only languages of the sitemaps and IndexNow. `world_i18n
  selftest` fails while the pushed config enables anything else (drop that check at „релиз языков“, LANGI step 6).
- `langs_enabled_preview` (LANG0): the languages of dev previews (`BV_WORLD_PREVIEW=1`, set by `preview.yml`): en, sr, ru +
  all 27. In a preview a missing key shows the English string with `[EN] ` (counted: `world pages: …` log and
  `world_i18n.missing_report()`); a production build stops instead.
- `waves` (LANG_pool §0.2), `market_countries` (§0.3): a language gets city and network pages only for these countries.
- `preview_pages_cap` (1000): at most this many city + network pages per language in a preview (the largest first, by
  places), so the preview of all 30 languages stays under 19 000 files (Cloudflare Pages Free: 20 000). `BV_WORLD_PAGES_CAP`
  overrides it for a test; production never caps.
- 27 extra languages: the 24 of K8 + `et`, `lt`, `lv` (LANG0, Babel entries).

## Files of a language (contract of the L-tasks)

`content/world/i18n/<code>/`: `strings_map.json`, `strings_pages.json`, `strings_shell.json`, `strings_prices.json`,
`strings_pay.json`, `strings_press.json`, `strings_b2b.json`, `strings_embed.json` (all eight since LANG0; `{key: "text"}`,
plural keys `pl_*` as `{one, few, many, other}`), `texts.json` (`about_data`, `download`, and since LANG0 `pay` / `routes`:
path of the multilingual node of `pay.json` / `routes.json` → text, e.g. `afir.points[0]`, `routes[3].stops[1].city`;
optional notes `tolls.<CC>.note`, `apps[<i>].note`), `slugs.json` (home, map, hub, net, about, download, gnet, prices,
shell_about, sources, methodology; optional since LANG0: pay, routes, press, b2b, embed, map_conf, developers — without them
the path is the home prefix + the English path, `/de/how-to-pay/`), `countries.csv` (`cc,name,slug,in_phrase,note`),
`cities.csv` (`geonameid,name,in_phrase,decl_ok,note`; also names the route towns by their GeoNames id).

## Placeholders and names of the LANG_pool decisions (LANG1, 11.11.2026)

- **D1 `{cu}`, `{lo}`/`{hi}`, "in <country>"** — every language other than en/sr/ru takes `in_phrase` of its
  `i18n/<code>/countries.csv` (How to pay, prices, pages, press facts). No built-in German or French lists remain.
- **D2 press facts** — `f_*` of the language's own `strings_press.json`, also for a press-release draft of a language that is
  not built (`world_press.py facts 2026-11 de` reads `i18n/de/strings_press.json` and stops when an `f_*` is missing).
- **D3 `{month}`** — en/sr/ru as before; every other language the stand-alone nominative month and the year (Babel
  `LLLL y`: "studeni 2026", "листопад 2026"), `world_i18n.month_label()`.
- **D4 `{name_nom}`** — optional column `name_nom` of `countries.csv` (after the five columns): the country in the middle of a
  sentence with its article ("die Schweiz", "les Pays-Bas", "η Ελβετία"); empty → the name. May stand wherever English has
  `{name}` (How to pay: `afir_eu`, `afir_non`, `conn_txt`, `conn_lnk`). A string that opens with `{name_nom}` gets its capital
  ("Die Schweiz ist kein EU-Mitglied"). French: write no "de {name_nom}" (it would read "de les Pays-Bas").
- **D5 `{city_de}`** (French only) — "de Lyon", "d’Ulm", "du Havre", "des Herbiers"; h counts as aspirated except a short
  list of towns with a mute h (`FR_H_MUET`). Stands for `{city}` on city pages and for `{x}` in `t_near` (" (près {city_de})").
- **D6 `{city_u}`** — available on `t_city`, `t_city_cc`, `d_city` (and every other string of a city page) in every language:
  `in_phrase` of `cities.csv`, or the safe `fallback_u` construction when there is none.
- **`{country_u}` for `{country_name}`** — where English has a number in `{country}` and the name in `{country_name}`
  (`p_city_cmp`), a language may write "in Italia" in the name's slot.
- **Section paths** — LANG0's contract (D7 replaced by it, LANG_pool "Поправка 18:45"): optional `slugs.json` keys `pay`,
  `routes`, `press`, `b2b`, `embed`, `map_conf`, `developers`; without one, home prefix + the English path (`/de/how-to-pay/`).
- **D8** — Romanian percent `{x}%` (registry; `world_i18n.py registry` keeps it, `PCT_FIXED`).
- **D9** — the widget configurator lists every built language; above three, one `<select>` by native name.
- **D10** — `strings_home.json` of every language through the common loader (LANG0); `world-home.js` and the hero map take
  the page's own strings and `intl`.
- Check on a built site: `BV_WORLD_PREVIEW=1 python3 scripts/qa/world_lang_check.py dist-com [de,fr,pl,uk,hr]` (preview.yml).

## Rules of the engine

- An enabled language without a key, file or slug → the build stops.
- Country/city without a name in the language → English (CLDR column of `names/countries.csv` first for countries),
  counted once per name and printed in the build log (`BV_WORLD_I18N_REPORT=<file>` also writes JSON).
- Plurals: `"one|few|many"` strings of en/sr/ru keep the old rule (byte-identical builds); objects use the CLDR category
  (Babel; `world_i18n selftest` checks that Babel and the old rule agree for sr/ru on 0…1999).
- City slugs and network slugs are shared by all languages (P1); country slug, section slugs and names are per language.
- Coverage (LANG0): an extra language gets the hub, every country, prices, How to pay, routes and the shell pages; city and
  network pages only in its `market_countries`. A link to a page a language lacks goes to the map with the filter.
- hreflang clusters cover the languages that have the page; x-default = English. The sitemaps take only `langs_enabled`.
- Language menu (more than three languages): native names A–Z, browser languages first (`static/com/world-lang.js`), a
  language without the page leads to the nearest page above (country → hub). Hint strip once per browser, no redirect.
- JS: each page carries its own language only (map: `wm-i18n` in the page; `cfg.intl`, `cfg.dec`, `cfg.thou` for the
  other languages; prices: `WP_FX.dec/thou/def`; home search: `search-index-<code>.json` with the name in item[8]).
- Currency: price pages of a language's own non-euro countries open in the local currency (`WP_FX.def = "loc"`).
- Greek pages: `world-grek.css` (Inter's Greek subset in the 'Onest' family). `html lang` = the registry `html`.
- Size: every build prints the production forecast (prod / wave 1 / all 27) and stops above 800 MB for production.
- Search index: `search-index.json` stays en/sr/ru (unchanged); each extra language gets `search-index-<code>.json`
  (`langs` = en, sr, ru, <code>; its names go to "other names") and its home page loads that file. One index with all
  24 languages would be 365 KB gzip, over the 300 KB limit.
- An extra language whose path collides with an existing page (regional `/hr/`, `/mk/` …) stops the build.

## Local test (never push)

```
python3 scripts/world_i18n.py pseudo /tmp/i18n          # pseudo-language xx: ⟦…⟧, +30 % length, half of the cities
BV_WORLD_LANGS=en,sr,ru,xx BV_WORLD_I18N=/tmp/i18n BV_WORLD_PAGES=… python3 scripts/gen_com.py
python3 scripts/world_i18n.py check de [folder]         # an i18n folder against the EN keys
```

## Enabling languages — „релиз языков“ (LANGI step 6)

1. All `l2-<code>` folders merged; `python3 scripts/world_i18n.py check <code>` → OK for each.
2. Add the codes to `langs_enabled`; drop the "exactly en, sr, ru" check in `world_i18n.selftest`.
3. Merge `lang0-com` in `hemptoon/blokvolt-com` (world folders of every language stay out of that repository).
4. Watch the forecast line of the build (≤ 800 MB) and the IndexNow lines (one request per language).
5. og image per language (`og-<code>.png`) — today a copy of the English one.

`python3 scripts/world_i18n.py world-paths` prints the rsync excludes of all world folders (blokvolt-com deploy.yml).
