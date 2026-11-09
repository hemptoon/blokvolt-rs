# L-IT — Italian package for the world layer (notes)

Date: 2026-11-09. Base: `g3-prices cf44fc3`, branch `l-it`. Not enabled anywhere (enabling only after the G8 gate).

## Form of address and tone
- Impersonal Italian throughout: infinitive instructions ("Riprovare più tardi", "Verificare il prezzo…"), "si" constructions. No "noi", no "redazione", no Lei/tu forms in running text.
- Buttons and links use the imperative tu form that is standard for Italian UI ("Apri la mappa", "Scarica i dati", "Segnala un errore", "Cerca una rete"), as in the glossary.
- "About" in the footer/shell = "Informazioni" / "Informazioni su BlokVolt" (not "Chi siamo", which is first person plural).

## Plurals
- CLDR (Babel 2.18) for `it`: `one`, `many`, `other`. `many` is the "milione di …" form (e.g. 1.000.000 di siti), so it is written as "di <plural>".
- Keys with plural objects: pages `pl_*` (9), shell `pl_loc`, `pl_cc`. `strings_map.title`, `shell.*_title` contain " | BlokVolt" — plain strings, not plurals.

## Terms (glossary.csv, column `it`)
- charging location / site = "sito di ricarica" (glossary `charging_site`); "sito" alone in tables.
- charger = "colonnina (di ricarica)"; charging station = "stazione di ricarica"; charging point = "punto di ricarica".
- country = "Paese" (capital P, Italian convention for the state); network = "rete"; data reliability = "affidabilità dei dati".
- ad hoc kept as "ad hoc" (Italian usage in AFIR texts); plan = "abbonamento" (table column `th_plan` = "Piano").
- ECB = "BCE"; VAT = "IVA"; "price cap di Ofgem".
- The index name in `data_p` citation stays in English ("European EV Charging Price Index") — it is the product name to cite.

## Placeholders to watch at K8
- `{country_u}` is filled with `countries.csv:in_phrase` ("in Germania", "negli Stati Uniti", "nei Paesi Bassi", "nel Regno Unito", "a Cipro", "nel Principato di Monaco").
- `{city}` in `t_city`, `d_city` is preceded by a hard-coded "a " ("Stazioni di ricarica a {city}"). That is wrong for 3 cities with an Italian article: L'Aia, La Spezia, Pireo (→ "all'Aia", "alla Spezia", "al Pireo"). Their correct form is in `cities.csv:in_phrase`. Suggestion for K8: when a language provides `in_phrase`, substitute it for "a {city}" — or accept the 3 cases.
- `fallback_u` = "a {x}" (city); for countries the engine should use `in_phrase`.
- `p_multi`, `p_net_share` put the article before percentages: "Il {pct_multi} dei siti…" — correct Italian with any number ("il 45%").
- `p_city_cmp`: "{country} in media in {country_name}" — for countries needing an article ("negli Stati Uniti") this gives "in Stati Uniti". Minor; K8 could pass `in_phrase` instead.

## Country names (countries.csv)
- From `names/countries.csv:name_it` (CLDR). Changed: HK "RAS di Hong Kong" → "Hong Kong", MO → "Macao", MM "Myanmar (Birmania)" → "Myanmar", CZ "Cechia" → "Repubblica Ceca" (much more common in Italian; question for Andrei below). Marked in `note`.
- Slugs: ASCII of the Italian name (germania, stati-uniti, paesi-bassi, repubblica-ceca, isole-fr-er for Fær Øer — ugly but ASCII; could be `isole-faroe`).

## Cities (cities.csv) — all 5,605
- Order: IT + CH (Italian is official) first, then `month`, then `balkan`, then `quarter`.
- Name: established Italian exonym where one is in normal use (≈95 entries: Monaco di Baviera, Colonia, Francoforte sul Meno, Parigi, Lione, Londra, Varsavia, Cracovia, Praga, Zurigo, Swiss names — Coira, San Gallo, Friburgo, Berna, Basilea, Lucerna, Losanna, Soletta, Svitto; South Tyrol: Appiano sulla Strada del Vino, Bressanone; Belgrado, Zagabria, Lubiana, Atene, Salonicco, Mosca, Kiev, Smirne…), otherwise the local name; for non-Latin local names the GeoNames English form.
- Croatian/Slovenian coastal cities keep the local name (Rijeka, Split, Koper) — neutral choice, only the capitals use exonyms.
- in_phrase: "a <city>" (Italian uses "a" for every city, so decl_ok = 1 everywhere); article cases: all'Aia, alla Spezia, al Pireo, al Cairo.

## Back-translation check
See section at the end (60 random strings).

## Open / left
- Questions for Andrei: (1) "Repubblica Ceca" vs CLDR "Cechia"; (2) "Kiev" vs "Kyiv" (Italian media are split; kept "Kiev" with a note).
- The `name` fields of sources_pages (e.g. "BlokVolt own check") stay in English by the contract (source names); can be translated later if wanted.
