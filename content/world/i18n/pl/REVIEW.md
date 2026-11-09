# R-PL — proofreading of the Polish pack (pool 4, 10.11.2026)

Base: `origin/l-pl` 6f06498. Branch: `r-pl`. `check.py`: 0 errors, 0 warnings.

## Strings (all 403 read)

The translation is good: impersonal register is consistent ("należy…", "można…", "warto…"), and terms match the glossary. Buttons use the 2nd-person imperative ("Pokaż filtry", "Wyślij"), which is the norm for Polish UI. 10 lines were changed:

- map: `data_err`, `r_err_net` — "Można spróbować ponownie później" (the word "ponownie" was missing).
- map: `r_loc_hint`, `r_need_type` — the instruction text was in "ty" form; changed to the impersonal "należy…", in line with the rest of the hints.
- map: `r_ok` — "poprawka pojawi się po najbliższej aktualizacji" (future tense, more natural). "Dziękujemy" was deliberately not used (no "my").
- map: `how` — question mark added ("Jak jest obliczana?").
- pages: `t_city`, `t_city_cc` — "…{city_u} ({country})" instead of a comma ("w Monachium (Niemcy)").
- pages: `p_multi` — "{pct_recent} lokalizacji" — the noun was missing.
- prices: `prices_checked` — "Ceny sprawdzono {date}", matching `checked`.
- prices: `table_note`, `m3` — "każda sieć liczy się z liczbą…" (a calque) rewritten as "waga każdej sieci to liczba…". Ambiguous "których" clarified as "tych ładowarek…, których sieć jest znana".

Considered and left unchanged:
- `st_*` (stat labels after a number) stay in the nominative: no single case works for every number (22 → "publiczne", 25 → "publicznych").
- `per_session` stays "/sesja", the price-list convention like "zł/szt.".

## Countries (150)

All 150 names and `in_phrase` checked; none changed. Prepositions are correct (na Węgrzech, na Słowacji, we Francji, we Włoszech, na Ukrainie, na Białorusi, na Cyprze, na Malcie, na Islandii).

## Cities

- Checked: all 22 Polish cities (correct) and the first 500 `stage=month` in file order (there are no counts in places.json). The exonyms are correct (Monachium, Kolonia, Akwizgran, Trewir, Hawr, Tuluza, Wilno, Kowno…).
- The previous author was inconsistent: "w Eindhoven" had decl_ok=1, while "w mieście Apeldoorn" had 0. For `month` cities in Latin-script Western Europe (NL DE GB BE FR FI AT LU DK SE NO CH IE IS), "w mieście X" was replaced:
  - 679 lines changed in total;
  - 127 are declined by regular endings: -wijk→-wijku, -ch→-chu, -el→-elu, -ing→-ingu, -stein→-steinie, -heim→-heimie, -burg/-berg→-u, -rd→-rdzie, -hut→-hucie (Landshucie, Sittardzie, Meppelu, Emmerichu…);
  - the rest use the uninflected "w X", which is normal in Polish for less-known foreign names (w Apeldoorn, w Dachau, w Vitré);
  - French towns ending in -ing (Tourcoing, Seraing) stay uninflected;
  - exceptions: Gouda→w Goudzie, Pirna→w Pirnie, Hämeenlinna→w Hämeenlinnie; short or ambiguous names (Best, Hof, Haar, Cham, Elst, Wisch, Leek, Velp, Tiel) and names ending in -a keep "w mieście X".
  - The changed lines carry a note: `R-PL: forma nieodmienna` / `R-PL: odmiana regularna`.

## Slugs

`/pl/mapa/`, `/pl/stacje-ladowania/`, `siec`, `o-danych`, `pobierz`, `/pl/sieci-ladowania/`, `/pl/ceny-ladowania/`, `/pl/o-serwisie/`, `/pl/zrodla/`, `/pl/metodologia/` — natural, ASCII. They do not clash: there is no `content/com/local/pl/`, and the `/pl/` prefix is not taken by EN/SR/RU.

## Back translation

A separate agent back-translated 39 changed lines blind (13 strings and 26 cities).
- Strings: no errors. On its feedback, `r_email_hint` and `per_session` were reverted, and "lokalizacji" was added to `p_multi`.
- Cities: 8 of 26 sounded unnatural uninflected. This is what led to the rule for regular endings above; all 8 are now declined.

## Open questions

- `texts.json` contains `sources_pages` (the L-PL author partly translated the `licence` field). By the 23:55 decision `sources_pages` is not translated; K8 should read only `about_data` and `download` from texts.json.
- OSM attribution: the map uses "© współtwórcy OpenStreetMap", texts use "© OpenStreetMap contributors". Not unified: this needs the official PL wording from osm.org/copyright.
- The remaining ~1,400 `quarter` cities in "w mieście X" form are untouched (decl_ok=0, the safe form).
