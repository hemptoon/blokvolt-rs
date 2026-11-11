# R-EL — Greek review (10.11.2026)

Reviewer: an independent session acting as a native-level editor. Base: `origin/l-el` d8a29e9. Branch: `r-el`.

## Scope covered
- Strings: all 403 keys (map 125, pages 120, shell 41, prices 117) were read against EN. `texts.json` (97) was read too: no changes needed.
- Countries: all 150 `name` + `in_phrase` checked. The article/ν rule (στην before κ π τ ξ ψ γκ μπ ντ τσ τζ and vowels, στη otherwise) was checked by script on all countries and cities: 0 violations.
- Cities: all 90 GR cities and the first 500 `stage=month` cities outside GR, in file order. `places-2026-11-09.json` has bboxes only, no counts, so file order was used.
- Slugs: ELOT 743 is correct; there is no `/el/` local section in `content/com/local/`, so there are no collisions.

## Changes (21 edits)
Strings (13):
- `map.nav` «Οδηγίες διαδρομής» → «Διαδρομή». The old text was too long for a button (17 > 10×1.4).
- `map.c_price` → «Τιμή χωρίς συνδρομή». The old text was 29 characters against a limit of 21.
- `shell.map_btn`, `prices.more_map` «Ανοίξτε τον χάρτη» → «Άνοιγμα χάρτη», so they match the other noun-style buttons (Αποστολή, Λήψη).
- `pages.t_city`, `t_city_cc`, `d_city`: «στην πόλη {city}» → `{city_u}`. This is the pool 4 decision, so the engine now fills `cities.csv:in_phrase` («στο Μόναχο»).
- `pages.p_gnet` «{net}: παρουσία σε …» → «Το δίκτυο {net} είναι παρόν σε {n_countries}.»
- `pages.mini_alt` «ισχύς που δεν αναφέρεται» → «χωρίς δηλωμένη ισχύ».
- `pages.regional_guide` «Περιφερειακός» → «Τοπικός», consistent with `shell.region_p` «Τοπικοί οδηγοί».
- `prices.lead_hub` «δικτύων: {nets}, χωρών: {countries}» → «{nets} δικτύων σε {countries} χώρες». These numbers are always > 1.
- `prices.m4`: «2,500–4,999» → «2.500–4.999», using the Greek thousands separator. Also removed the repeated «Ισοτιμίες: ισοτιμίες».
- `prices.h_nets` «Δίκτυα και προγράμματα» → «Δίκτυα και συνδρομές», to match `th_plan` «Συνδρομή».

Countries (2): FJ «στο Φίτζι» → «στα Φίτζι» (neuter plural). MM «στο» → «στη Μιανμάρ».

Cities (4, decl_ok → 1): Groningen «Χρόνινγκεν» → «Γκρόνινγκεν». Nijmegen «Νάιμεχεν» → «Ναϊμέγκεν». Caen Latin → «Καν / στην Καν». Vitoria-Gasteiz «στο» → «στη Βιτόρια».

`check.py`: placeholders now treat `{city_u}`/`{country_u}` as equivalent to `{city}`/`{country}`, following pool 4 decision 00:12. Result: OK.

## Back-translation
A separate agent back-translated all 20 changed items: 0 meaning mismatches. Its suggestions were applied (VC kept as one name without «τις»; m4 repetition removed). Two were declined:
- d_city «φορτιστές ταχείας φόρτισης DC» kept, for consistency with d_country/d_hub.
- regional_guide «Τοπικός» kept, consistent with the local sections.

## Open / disputed
- NL «Κάτω Χώρες» (official) vs «Ολλανδία» (what Greeks actually say and search for). For SEO «Ολλανδία» is stronger. Left unchanged; this is for Andrei to decide.
- `share` «Κοινοποίηση» is 11 characters against a limit of 7. There is no shorter natural Greek word, so it was kept.
- About 4 900 cities stay in Latin script with «στην πόλη X», decl_ok=0. This is grammatically safe. Exonyms beyond the top 500 were not reviewed.
- `{fx}`/`{d}`/`{date}` after «της» assume the engine renders a date (for example «9 Νοεμβρίου 2026» or «09.11.2026»). That reads fine either way.

## L2-EL — 11.11.2026 (delta to 8 files, LANG pool)
- Added 274 keys: strings_map +29 (28 `ci_*` check-ins + `emb_open`), new strings_pay (93), strings_press (54), strings_b2b (33), strings_embed (65). HOME2 keys: not in `dev` yet — none.
- texts.json: new sections `pay` (6 AFIR points) and `routes` (59 stop-city nodes; Greek names taken from `cities.csv` — 23 Greek exonyms, 9 kept Latin where cities.csv has decl_ok=0).
- Tone: «Thank you» in `ci_thanks`, `ci_paid_ok`, `m_ok` rendered without «Ευχαριστούμε» (first-person plural), as in L-EL `r_ok`. Country-name slots without article: `afir_eu`/`afir_non` «{name}: …», `conn_txt` «για τη χώρα {name}», `f_range` «στη χώρα {lo}».
- check.py now covers all 8 strings files, texts.json `pay`/`routes` (all paths, no extras, placeholders) and forbidden wording (24/7, εμείς, ευχαριστούμε). Result: OK, 0 errors.
- Blind back-translation of 60 random new strings (seed 274) by a separate agent: 0 meaning mismatches; 10 notes, 5 applied (m_demo, sys_mixed, lead_issue, dv_p_grad, season «απόθεμα μπαταρίας»), 5 declined (ci_unit fragment is a form label as in EN; `tamna`/`nepoznato` are literal parameter values; {month}/{name} slots depend on engine format).
- Own countries GR, CY: names/slugs OK (Ελλάδα/ellada, Κύπρος/kypros); all 58 GR city pages in pages_state have Greek name + in_phrase, decl_ok=1; CY has no city pages; nothing to add.
- Open: slugs for pay/routes/press/b2b/developers are not in the `slugs.json` contract (LANG0 decides); NL «Κάτω Χώρες» vs «Ολλανδία» still Andrei's call.
