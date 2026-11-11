# L-EL — ελληνικά (Greek), notes

Base `g3-prices` (cf44fc3), branch `l-el`. Language kept off: nothing outside `content/world/i18n/el/`.

## Form of address and tone
- Impersonal or polite plural (εσείς forms: «Ανοίξτε», «Ελέγξτε»). No «εμείς/μας», no «η σύνταξη».
  EN "Thank you." in `r_ok` (map report) → «Η αναφορά στάλθηκε.» — Greek «Ευχαριστούμε» is first-person plural.
- Monotonic Modern Greek, Greek question mark «;», ano teleia «·» where EN joins clauses with ";", quotes «».
- Numbers/dates are left to the code (EL format: decimal comma, thousands dot, `d/M/yyyy`; K8 registry).

## Terms (glossary.csv has no `el` column — proposed set)
| EN | EL |
|---|---|
| charging station / location | σταθμός φόρτισης / τοποθεσία φόρτισης |
| charging point / charger (device) | σημείο φόρτισης / φορτιστής |
| network / operator | δίκτυο / φορέας λειτουργίας |
| connector | βύσμα |
| fast / ultra-fast (HPC) | ταχεία / υπερταχεία φόρτιση |
| electric car / EV | ηλεκτρικό αυτοκίνητο / ηλεκτρικό όχημα |
| open data | ανοιχτά δεδομένα |
| ad hoc | χωρίς συνδρομή (ad hoc) |
| subscription | συνδρομή |
| idle fee | χρέωση αδράνειας |
| VAT | ΦΠΑ |
| price index | δείκτης τιμών |
| median | διάμεσος |
| attribution | αναφορά προέλευσης |
Suggest adding an `el` column to `glossary.csv` with these (not done: outside `i18n/el/`).

## Plurals
CLDR `el`: `one`, `other`. All 11 `pl_*` are `{one, other}`. `_in` forms = same as base (Greek uses accusative after «σε», which equals nominative for these nouns: πόλη/πόλεις, χώρα/χώρες).

## Slugs (ELOT 743)
`/el/chartis/`, `/el/stathmoi-fortisis/`, `diktyo`, `schetika-me-ta-dedomena`, `lipsi`, `/el/diktya-fortisis/`, `/el/times-fortisis/`, `/el/schetika/`, `/el/piges/`, `/el/methodologia/`.
Country slugs: ELOT 743 from the CLDR name (αυ→av/af, ευ→ev/ef, ου→ou, γγ→ng, initial μπ→b, ντ→d). Literal ELOT gives some odd ones: HK `chongk-kongk`, SG `sigkapouri`, UG `ougkanta`, TO `tongka` — kept strict; easy to override if Andrei prefers readability.

## Countries
`name` = CLDR `name_el` from `names/countries.csv`, shortened where CLDR adds qualifiers: HK «Χονγκ Κονγκ» (CLDR «… ΕΔΠ Κίνας»), MO «Μακάο», MM «Μιανμάρ» (no «(Βιρμανία)»), MF «Άγιος Μαρτίνος», BA «Βοσνία-Ερζεγοβίνη».
NL kept as CLDR/official «Κάτω Χώρες» (everyday Greek says «Ολλανδία») — question for Andrei. PS, XK as CLDR.
`in_phrase` = σε + article in accusative by gender/number: «στη Γερμανία», «στην Ελλάδα», «στο Βέλγιο», «στον Καναδά», «στις Ηνωμένες Πολιτείες», «στα Ηνωμένα Αραβικά Εμιράτα», «στις Νήσους Φερόες». στην vs στη by the standard rule (στην before vowels and κ π τ ξ ψ μπ ντ γκ τσ τζ).

## Cities
See RESULT/back-translation for counts. GR cities: Greek names with article (decl_ok=1). Elsewhere: Greek exonym where well established (Μόναχο, Παρίσι…, decl_ok=1), otherwise the Latin local/EN name with «στην πόλη X» (decl_ok=0) — Greek apposition, grammatical for any name.

## Placeholders — for K8 (engine)
- Strings keep EN placeholders (contract). Where EN has `{country_u}` the Greek text expects the full `in_phrase` («στη Γερμανία») — K8 must feed `countries.csv:in_phrase` there.
- `t_city`/`d_city` use «στην πόλη {city}» because EN has bare `{city}`. If K8 allows `{city_u}` for non-EN (as SR/RU already do), switch to `cities.csv:in_phrase` («στο Μόναχο») — nicer.
- Count strings without a pl_* form use «label: {n}» (e.g. «Πηγές: {n}», «δικτύων: {nets}, χωρών: {countries}») — correct but stiff.
- `2,500–4,999` (prices band) left as in EN; Greek format would be 2.500–4.999 — if the code doesn't localise it, fix in K8.

## Open
- Native-speaker review of all strings (agent-written).
- `glossary.csv` el column; NL name choice; strict-ELOT slugs vs readable overrides.

## Back-translation (60 random strings, seed 743)
57 ok, 3 minor, 0 mismatch; no rule violations. Fixed: `prices.th_plan` → «Συνδρομή» (was «Πρόγραμμα»), `prices.d_hub` «ad hoc (χωρίς συνδρομή)», `pages.d_city` «ταχείς φορτιστές DC». Details: `BACKTRANSLATION.md`.

## Cities — result
5 605/5 605 rows. decl_ok=1: 701 (all 90 GR cities with article + 611 established Greek forms); decl_ok=0: 4 904 (Latin name, «στην πόλη X»).
Doubts: Burgas «Μπουργκάς» (not «Πύργος», clash with Greek Pyrgos); Galați, Leeds, Caen, Veles left Latin (clashes/unsure); HU «Pest» → «Πέστη» (may be the district); small Balkan towns transliterated, not established (Ζάγετσαρ, Βρσατς, Πέια, Γκιλάν, Λέζα, Κούκες, Κότσανι, Νεγκότινο, Πλιέβλια) — decl_ok=1 but worth a native look. Attica's Heraklion → «Ηράκλειο Αττικής».

## FIXL (11.11.2026)
- `strings_home.json` new (71 keys). Home h1 «Χάρτης φόρτισης ηλεκτρικών αυτοκινήτων σε Ευρώπη και κόσμο».
- countries.csv: new last column `name_nom` (D4/D14) = article + name («η Ελβετία», «οι Ηνωμένες Πολιτείες», «το Βέλγιο», «ο Καναδάς»). Use `{name_nom}` only where it is not sentence-initial and only with «είναι» (number-neutral).
- D13: Netherlands = «Ολλανδία» (slug `ollandia`).
- D12: small TR/AL/MK/BG towns use official local names in Greek script; big-city exonyms kept (see REVIEW FIXL).
- Slugs (F5, ELOT 743): pay `/el/tropoi-pliromis/` · routes `/el/diadromes/` · press `/el/mesa-enimerosis/` · b2b `/el/dedomena-gia-epicheiriseis/` · embed `/el/embed/chartis/` · map_conf `/el/chartis-gia-istotopo/` · developers `/el/gia-programmatistes/`.
- FIXL2: +821 cities from names/cities_extra.csv (own market 12)
