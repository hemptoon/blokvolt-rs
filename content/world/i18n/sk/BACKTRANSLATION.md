# Slovak blind back-translation QA — 60 strings (sk_bt_sample.json)

Method: SK -> EN back-translation written first (/home/claude/sk_bt/bt.py), then compared with EN originals in content/world/*.json.

Counts: ok 56 · minor 4 · mismatch 0

No "my/náš/redakcia", no "okamžite/ihneď", no diacritics or grammar errors found. Register is consistent (vykanie: "Skúste", "overte"). The 4 minor items are about placeholders, not wording: the Slovak text itself is fine, but it depends on placeholder forms that do not exist for SK yet.

## Minor

- strings_prices.h_more — EN: "More {country_u}" — SK: "Viac {country_u}" — BT: "More {country_u}" — issue: {country_u} is the locative with its preposition ("in Germany"; sr_u / ru_v in countries.csv). countries.csv has only name_sk and no sk_u column, and N.country_u() in scripts/world_pages.py has no 'sk' branch, so this either crashes or would produce "Viac Nemecko". — fix: keep "Viac {country_u}" and add an sk_u column ("v Nemecku", "na Slovensku", "v Srbsku", "v Spojených štátoch"…) plus an 'sk' branch in country_u().
- strings_prices.h_c_index — EN: "Index {country_u}" — SK: "Index {country_u}" — BT: "Index {country_u}" — issue: same sk_u dependency; "Index v Nemecku" reads acceptably. — fix: keep it, or use "Cenový index {country_u}" so it reads more naturally.
- strings_pages.p_gnet — EN: "{net} appears in {n_countries}." — SK: "Sieť {net} je prítomná v {n_countries}." — BT: "The {net} network is present in {n_countries}." — issue: the meaning is fine, but {n_countries} comes from the plural key pl_country_in, which has no SK value yet; it must be locative. — fix: add SK pl_country_in = "krajine|krajinách|krajinách" (v 1 krajine / v 3 krajinách / v 5 krajinách).
- strings_pages.t_city — EN: "EV charging stations in {city}, {country}" — SK: "Nabíjacie stanice pre elektromobily: {city}, {country}" — BT: "EV charging stations: {city}, {country}" — issue: "in" became a colon. This avoids declining city names, so it is acceptable for a title; noted only as a structural difference. — fix: keep it (recommended), or if an SK city locative ever exists: "Nabíjacie stanice pre elektromobily {city_u}, {country}".
