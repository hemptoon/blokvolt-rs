# Names of countries, cities and networks (K4, contract v1 §7)

Files in this folder: `countries.csv`, `cities.csv`, `networks.csv`, `glossary.csv`, `check_names.py`.
Check after every edit: `python3 content/world/names/check_names.py` (exit 1 on errors).
Built on 09.11.2026 from the snapshot `~/dev/evdb/snapshots/2026-11-09/` (GeoNames cities, `sites`), CLDR 47
(Babel 2.18.0) and the translation memory of blokvolt.rs (`content/i18n/en.json`, `ru.json`).
GeoNames is CC BY 4.0: every page that shows these city names credits "GeoNames".

## Columns

- `countries.csv`: `cc, name_en, name_sr, name_ru, slug_en, slug_sr, slug_ru, sr_u, ru_v`, then CLDR 47 names for
  the next languages `name_hr … name_tr` (hr, bs, sl, mk, sq, de, fr, it, es, pt, nl, pl, cs, sk, hu, ro, bg, el, tr),
  `note`. All 150 countries of the snapshot.
- `cities.csv`: `geonameid, cc, name_local, name_en, name_sr, name_ru, slug, sr_u, ru_v, decl_ok, note` (contract)
  plus `stage` (month / quarter / balkan), `decl_ok_sr`, `decl_ok_ru`. Order: month, quarter, balkan; inside a stage by
  public chargers with confidence ≥ 50, most first.
- `networks.csv`: `network` (exactly `operator_canonical`), `name_display`, `slug`, `note` (contract) plus `kind`.
- `glossary.csv`: `key` and the terms in en, sr, ru, hr, bs, sr_me, sl, mk, sq, de, fr, it, es, pl, `note`.

## Slugs

- ASCII, lower case, words joined by `-` (`^[a-z0-9]+(-[a-z0-9]+)*$`). Diacritics are dropped (München → `munchen`,
  Nemačka → `nemacka`, Łódź → `lodz`), ß → ss, æ → ae, ø → o, đ → dj, apostrophes vanish (`'s-Hertogenbosch` →
  `s-hertogenbosch`). Russian: simple transliteration (ж zh, х h, ц ts, ч ch, ш sh, щ shch, ы y, й y, ю yu, я ya,
  ь ъ dropped): Германия → `germaniya`, о данных → `o-dannyh` (P1 §3.1).
- Country: one slug per language (germany / nemacka / germaniya). City and network: one slug for every language.
- City slug = ASCII of `name_local`; for non-Latin scripts ASCII of `name_en` (Θεσσαλονίκη → `thessaloniki`,
  東京 → `tokyo`). Unique inside the country: when two cities give the same slug, the one with more chargers keeps
  it and the other gets a region suffix (`portland` / `portland-me`; US: state code; elsewhere the region tag the
  agent gave, e.g. `frankfurt-oder`, otherwise the GeoNames admin1 code) — listed in `note`.
- Network slug: ASCII of `name_display`, unique worldwide.
- Slugs are part of URLs: once published, never change one silently — add a redirect.

## Serbian (`name_sr`, `sr_u`)

- Latin script only, ekavian, the site's own norm (CONTENT_STYLE).
- Countries: CLDR 47 `sr_Latn`, with Serbian everyday forms where CLDR is formal or Croatian-coloured:
  Velika Britanija (not "Ujedinjeno Kraljevstvo"), SAD (not "Sjedinjene Države"), Hongkong, Makao, Palestina,
  Esvatini. **Netherlands = Holandija** (Serbian norm; "Nizozemska" is the Croatian form — it stays in `name_hr`).
- Cities: an established Serbian exonym where one really exists (Minhen, Keln, Beč, Pariz, Rim, Đenova, Firenca,
  Napulj, Solun, Atina, Lisabon, Brisel, Hag, Ženeva, Cirih, Njujork, Los Anđeles). Otherwise the original Latin
  spelling unchanged (Göttingen, Bordeaux, Springfield) — Pravopis allows the original form in Latin script and it
  avoids inventing transcriptions. Names from non-Latin scripts are transcribed into Serbian Latin by the rules of
  Pravopis (Ελευσίνα → Elefsina, Харків → Harkiv, 横浜 → Jokohama); such rows say "transkripcija" in `note`.
- `sr_u`: "u" + locative (u Minhenu, u Novom Sadu, u Frankfurtu na Majni). Islands and some regions take "na"
  (na Kipru, na Malti, na Islandu, na Kosovu). Original spellings take the Serbian ending only when the word ends in
  a pronounced consonant written as pronounced (u Hamburgu, u Göttingenu, u Springfieldu). Everything else — vowel
  endings of foreign originals, silent letters (Bordeaux, Lille, Milton Keynes) and any doubt — gets the safe form
  "u gradu X" and `decl_ok_sr = 0`.

## Russian (`name_ru`, `ru_v`)

- Established Russian names (Мюнхен, Кёльн, Франкфурт-на-Майне, Генуя, Салоники, Гаага, Нью-Йорк); otherwise
  practical transcription from the local language. "ё" where it is the norm in the name (Кёльн, Гёттинген).
  Multi-part foreign toponyms with hyphens (Сан-Франциско, Ла-Корунья, Бад-Хомбург).
- Serbian (and other ex-Yugoslav) towns: the hyphenated forms of the blokvolt.rs translation memory (Нови-Сад,
  Сремска-Митровица, Врнячка-Баня), declined in the last part only: "в Нови-Саде", "в Сремска-Митровице"
  (RUNBOOK §3.35). Other foreign multi-part names follow the Russian norm (во Франкфурте-на-Майне,
  в Ростове-на-Дону).
- `ru_v`: "в"/"во"/"на" + prepositional. "во" before в/ф + consonant (во Франкфурте, во Флоренции, во Львове).
  Indeclinable names stay as they are (в Торонто, в Бордо, в Сан-Франциско). Any doubt → "в городе X",
  `decl_ok_ru = 0`.
- Countries: CLDR 47 `ru` with short everyday forms (США, Великобритания, Южная Корея, Гонконг, ЮАР, Палестина);
  "в Украине" (alternative "на Украине" noted); islands with "на" (на Кипре, на Кубе, на Мальте).

## decl_ok

`decl_ok = 1` only when both case forms are checked (`decl_ok_sr = 1` and `decl_ok_ru = 1`). A page can use the
language that is fine: `decl_ok_sr`/`decl_ok_ru` tell them apart; the fallback forms are always correct grammar.

## English (`name_en`)

Established English exonym (Munich, Cologne, Athens, The Hague), otherwise the local Latin form with diacritics,
for other scripts the usual English romanization. Countries: CLDR 47 `en`, without "&", "SAR China" and brackets
(Bosnia and Herzegovina, Hong Kong, Myanmar); Türkiye is written "Turkey" (search form; switch if the owner prefers
the official short name).

## name_local

The official name as the municipality writes it, in its script: München, Ελευσίνα, Скопје, 東京. Bilingual places:
the majority language of the municipality, the other form in `note` (Helsinki / SV Helsingfors; Brussels region →
"Bruxelles", note "Brussel"). Kosovo: the Albanian official form in `name_local`, the Serbian form in `name_sr`,
no words about status anywhere (RUNBOOK §3.10). North Macedonia: Macedonian Cyrillic, country "Северна
Македонија" / "Severna Makedonija" / "North Macedonia".

## Networks

Which networks: every `operator_canonical` with at least 20 public sites (confidence ≥ 50, `map_ok`) in some
country, or at least 100 sites on the map worldwide — 367 on the 09.11.2026 snapshot (all countries, Balkans
included, before the K1 licence filter).

`name_display` is the brand as the network writes it itself (bp pulse, IONITY, Shell Recharge, EnBW); brands are
never translated. Non-Latin brands keep their script, the Latin form is in `note`. `note` flags:
"хост, а не сеть" (fuel stations, shops, hotels, parkings that only host chargers — logic of `OP_HOST_RX` in
build.py), "дубль канона: слить с …", "плейсхолдер, не оператор", "ПО/производитель/роуминг, не оператор",
"велосипеды/двухколёсные", "частное лицо — не показывать имя". The flags are proposals for K1/KI; nothing is
merged or hidden here.

## Glossary

About 60 terms that the map and the pages share. hr, bs, sr_me (Montenegrin, neutral ijekavian), sq and mk are
taken from the strings of the blokvolt.com sections (`content/com/local/…`) so the terms match what the site already
says; terms that are not on the site yet are marked in `note`. Never "24/7", "odmah" or "atest".

## Adding a language later

Countries: the CLDR column is a starting point, check it by hand. Cities: add `name_<lang>` (and a case form if the
templates need one) through the same agent rules; keep the slug untouched.
