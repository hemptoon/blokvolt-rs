# World layer of blokvolt.com in N languages (K8-i18n, 10.11.2026)

The world layer (map, world pages, shell, prices) no longer hard-codes EN / SR / RU. Languages come from one registry;
new languages are prepared in `content/world/i18n/<code>/` (L-tasks) and switched on only after gate G8.

## Registry — `content/world/config.json`

- `langs`: code → `hreflang`, `html` (lang attribute), `og`, `code`, `label` (switcher), `script` (latn/cyrl/grek), `dir`,
  `dec`, `thou`, `pct`, `intl` (JS locale), `date` (CLDR short pattern, reference), `plural` (CLDR categories), `months`,
  optional `babel` (locale for plural rules, e.g. `sr_Latn`), optional `scope` (`europe` default = the pages that have
  Serbian, or `all`). `en`/`sr`/`ru` also hold `slugs`; 24 L-languages are generated from Babel
  (`python3 scripts/world_i18n.py registry`).
- `langs_enabled`: `["en","sr","ru"]`. **The only switch for a new language.** `world_i18n selftest` fails while the
  pushed config enables anything else (remove that check at G8).

## Files of a language (contract of the L-tasks, do not change)

`content/world/i18n/<code>/`: `strings_map.json`, `strings_pages.json`, `strings_shell.json`, `strings_prices.json`
(`{key: "text"}`, plural keys `pl_*` as `{one, few, many, other}`), `texts.json` (`about_data`, `download`),
`slugs.json` (home, map, hub, net, about, download, gnet, prices, shell_about, sources, methodology),
`countries.csv` (`cc,name,slug,in_phrase,note`), `cities.csv` (`geonameid,name,in_phrase,decl_ok,note`).

## Rules of the engine

- An enabled language without a key, file or slug → the build stops.
- Country/city without a name in the language → English (CLDR column of `names/countries.csv` first for countries),
  counted once per name and printed in the build log (`BV_WORLD_I18N_REPORT=<file>` also writes JSON).
- Plurals: `"one|few|many"` strings of en/sr/ru keep the old rule (byte-identical builds); objects use the CLDR category
  (Babel; `world_i18n selftest` checks that Babel and the old rule agree for sr/ru on 0…1999).
- City slugs and network slugs are shared by all languages (P1); country slug, section slugs and names are per language.
- hreflang clusters, the switcher and per-language sitemaps cover the enabled languages only.
- Search index: `search-index.json` stays en/sr/ru (unchanged); each extra language gets `search-index-<code>.json`
  (`langs` = en, sr, ru, <code>; its names go to "other names") and its home page loads that file. One index with all
  24 languages would be 365 KB gzip, over the 300 KB limit.
- An extra language whose path collides with an existing page (regional `/hr/`, `/mk/` …) stops the build.
- Extra languages follow Serbian's coverage (Europe) by default; `"scope": "all"` gives them every page.

## Local test (never push)

```
python3 scripts/world_i18n.py pseudo /tmp/i18n          # pseudo-language xx: ⟦…⟧, +30 % length, half of the cities
BV_WORLD_LANGS=en,sr,ru,xx BV_WORLD_I18N=/tmp/i18n BV_WORLD_PAGES=… python3 scripts/gen_com.py
python3 scripts/world_i18n.py check de [folder]         # an i18n folder against the EN keys
```

## Enabling a language at G8 (checklist)

1. Merge its `l-<code>` folder; `python3 scripts/world_i18n.py check <code>` → OK.
2. Add the code to `langs_enabled`; drop the "exactly en, sr, ru" check in `world_i18n.selftest`.
3. `static/com/world-home.js`: take the URL column from `doc.langs.indexOf(lang)` (today `{en:0, sr:1, ru:2}`, other
   languages get English URLs). `static/com/world-map.js`: read `cfg.intl` for the number/date locale (today it maps sr/ru/en only; other languages
   fall back to en-GB numbers). Changing the JS changes its version hash on every map page — do it with the first language.
4. `pip install babel` in `deploy.yml` (preview already has it).
5. Watch the Cloudflare Pages limit: one extra Europe-scoped language adds ≈3 100 files (dist-com 15 494 → 18 604 with one).
   Above 20 000 files the world pages need another host or fewer pages per language.
6. og image per language (`og-<code>.png`) — today a copy of the English one.
