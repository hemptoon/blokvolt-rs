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

# L2-PL — back-translation of the new strings (11.11.2026)

Sample: 60 random strings out of the 280 new ones (5 string files + texts.pay), seed 20261111. A separate agent translated them PL→EN without seeing the EN source. **Meaning: 60 of 60 match, 0 serious mismatches.** Its style notes as a native editor, and what was done with them:

- "zasięg" (coverage of apps) is read as the car's driving range → replaced by "lista krajów / kraje obsługiwane" (strings_pay `d_pay_hub`, `lead_pay_hub`, `apps_note`, `th_cover`, `h_apps_all`, `pay_disc`) and "pokrycie" (strings_b2b `lead`, `what_cov`, `f_w_cov`, `f_w_both`, `title`).
- "bez płatnych miejsc" is read as "no paid parking" → "bez płatnego wyróżniania"; "Klienci danych" → "Odbiorcy danych" (b2b `neutral`).
- Calques fixed: "Ceny od kierowców" → "Ceny zgłaszane przez kierowców" (`ci_paid_ok`); "Linia atrybucji" → "Informacja o źródle" (`cf_rules`); `dv_p_mreza`, `dv_balkan_p`, `dv_desc`, `dv_open_p`, `f_mom_n` ("indeksu DC"), `lead_press` ("pod warunkiem podania źródła i linku"), `pay_disc` ("warto to sprawdzić"), texts.pay `afir.points[2]` (card reader / contactless device).
- Kept on purpose: "Należy…" in hints (impersonal register of the pack, NOTES.md); "raza" in `f_home` — the engine always formats the ratio with one decimal (`num(x, l, 1)` in world_press.py), and "1,8 raza" is the correct form; "odpowiedź" in check-in messages (it is the answer to "Czy działa?"); "e-myto" — generic Polish word for electronic toll.

## FIXL 11.11.2026

- Sprawdzono: nowy `strings_home.json` (71 kluczy), `lang_hint`/`lang_hint_close`, D11 (`dv_p_lang`, `p_hub_na`), 7 nowych slugów,
  49 miast (48 NOBIL + Genewa), D12 w `cities.csv`.
- Tłumaczenie wsteczne PL→EN, fala 1: 20 losowych kluczy `strings_home` (te same co NL/PT) + 4 zmienione ciągi + nazwy miast.
  Rozbieżności znaczeniowych brak; `p_ratio` «{x}× cena w domu» — skrót w etykiecie wykresu, dopuszczalny.
- D12 (nazwy historyczne obcych miast → nazwy urzędowe, 10 wierszy): Litwa — Janów→Jonava, Uciana→Utena, Wiłkomierz→Ukmergė,
  Taurogi→Tauragė, Kiejdany→Kėdainiai, Możejki→Mažeikiai, Mariampol→Marijampolė, Olita→Alytus («w mieście X», decl_ok=0);
  Niemcy — Strzałów→Stralsund («w Stralsundzie»), Gryfia→Greifswald («w Greifswaldzie»).
  Zostawione jako żywe egzonimy (jak «Beč»/«Mníchov»): Wilno, Kowno, Kłajpeda, Szawle, Poniewież, Połąga, Lwów, Kijów, Łuck,
  Brześć, Budziszyn, Chociebuż, Koszyce, Preszów, Pecz, Segedyn, Braszów, Sybin, Kluż-Napoka.
- Wątpliwości: Połąga/Szawle/Poniewież (używane w prasie, ale na Litwie drażliwe) — do decyzji; Pecz/Segedyn (rzadziej niż Pécs/Szeged).
- `near_err`: «Położenie» zamiast «Lokalizacja», bo «lokalizacja» = charging location w tym pakiecie; `map_loading` «Wczytywanie mapy…»
  zamiast «Ładowanie mapy…» (dwuznaczne z ładowaniem auta).
