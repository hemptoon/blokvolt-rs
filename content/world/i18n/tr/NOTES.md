# L-TR — Turkish (tr), notes — 09.11.2026

## Form of address
- Polite "siz" forms (imperatives "açın", "kontrol edin", "deneyin") and impersonal passives ("gösterilir", "güncellenir"). No "biz"/"bizim", no "editörler".
- Buttons are short polite imperatives ("Haritayı açın") or short infinitive-like labels ("Gönder", "Kapat", "Paylaş"), as Turkish UIs usually do.

## Grammar decisions
- Plurals: CLDR tr = one/other. A Turkish noun after a number stays singular, so one == other everywhere ("3 şehir", "12 ülke").
  `pl_city_in`/`pl_country_in` = the locative after the number ("12 ülkede", "5 şehirde"); the templates (`p_gnet`, `p_net_share`) have the verb at the end ("… {n_countries} bulunuyor").
- `{country_u}` (EN "in Germany") = `in_phrase` from countries.csv, already in the locative ("Almanya'da"). The templates are written around that: "{country_u} elektrikli araç şarj istasyonları" → "Almanya'da elektrikli araç şarj istasyonları".
  **Contract for K8:** for tr, `country_u` must be filled from `i18n/tr/countries.csv:in_phrase`.
- No suffixes are attached to `{city}`, `{country}`, `{net}` placeholders (Turkish suffixes depend on pronunciation). Where a case is needed: "{x} şehrinde" (fallback_u), "{city}, {country}: …" (titles), "Endeks …" etc.
- Percent: Turkish puts the sign first — `pct` = "%{x}" ("%12"). Other strings with a literal % ("%10'undan", "%20–30") follow that too.
- Locative suffix rule (countries.csv, cities.csv): last vowel back (a ı o u) → -da/-ta, front (e i ö ü) → -de/-te; -ta/-te after f s t k ç ş h p; apostrophe after proper names; a compound name ending in a possessive suffix takes -nda/-nde ("Amerika Birleşik Devletleri'nde", "Man Adası'nda").

## Countries (150)
- `name` = CLDR tr (names/countries.csv `name_tr` = Babel), except: HK "Hong Kong" and MO "Makao" (CLDR "Çin Hong Kong ÖİB" is too long for navigation), MM "Myanmar" (without "(Burma)"), RE "Réunion". Noted in the `note` column.
- Exceptions to the harmony rule: Nepal'de, Liechtenstein'da (pronunciation). All 150 checked by eye.
- Slug: Turkish letters transliterated (ç→c, ğ→g, ı→i, ö→o, ş→s, ü→u): almanya, turkiye, birlesik-krallik, amerika-birlesik-devletleri.

## Cities (5,605 of 5,605; decl_ok=1 for 1,538)
- Order: Turkey (28) → month/balkan → quarter.
- `name`: established Turkish exonym for about 70 well-known cities (Münih, Viyana, Prag, Varşova, Atina, Selanik, Belgrad, Üsküp, Saraybosna, Bükreş, Budapeşte, Londra, Brüksel, Lahey, Lizbon, Kopenhag, Cenevre, Zürih, Moskova, Lefkoşa, Tiflis, Pekin…, see note "egzonim"). Otherwise the local name in Latin script; for non-Latin scripts — name_en.
  Greek islands and cities with a historical Turkish name (Kandiye, İstanköy, Filibe, Eğriboz) get the local name in brackets.
- `in_phrase`, decl_ok=1: TR (Turkish spelling) + exonyms (by hand) + the rule for languages where spelling ≈ pronunciation: DE AT (diphthongs ei/ai/ey→a, eu/äu→o, ie→i), IT ES HR RS BA SI ME FI CZ SK HU (diacritics normalised; c/cs/sz → hard).
- decl_ok=0 = the safe construction "X şehrinde" (FR, GB, US, NL, BE, PT, etc. — pronunciation does not follow spelling, and multi-word names or names with brackets/slashes).
- Doubtful: Catalan names with final -x/-tx (Felanitx), Spanish final -z (rule by spelling). Few, decl_ok=1 left; worth checking.

## Terms (glossary.csv has no tr column — my choices)
- charging station = şarj istasyonu; charger/charging point = şarj noktası; charging location = şarj lokasyonu; network = şarj ağı; operator = operatör;
  connector = konnektör; ad hoc = abonelik olmadan (ad-hoc); plan/subscription = abonelik/tarife; idle fee = bekleme ücreti; VAT = KDV; reliability = güvenilirlik.
- "lokasyon" vs "konum/yer": "lokasyon" is the common term in the Turkish EV sector (charging companies' and EPDK texts); "konum" is used for the location on the map (r_lokacija "Yanlış konum").
- Suggestion: add a `tr` column to glossary.csv from this list (not done — files only in i18n/tr).

## What is left
- `sources_pages.json` is not translated (by rule).
- Native-speaker read before the language is enabled (G8): the long texts (texts.json, m1–m4, profiles_note).
- decl_ok=0 cities (4,067) — can be improved by hand or with pronunciation data.

## FIXL (11.11.2026)
- `strings_home.json` (HOME2) — 71 ключ; pl_* = {one, other}, обе формы одинаковы. Нет «EV» (ev = дом).
- D13: driver check-in = «durum bildirimi», error report = «hata bildirimi».
- D12: османские названия греческих/болгарских/албанских городов заменены местными (Heraklion, Chalkida, Kos, Rethymno, Ioannina, Preveza, Plovdiv, Shkodër); Selanik, Üsküp, Sofya, Burgaz и др. крупные — оставлены.
- Слаги разделов: /tr/nasil-odenir/, /tr/guzergahlar/, /tr/medya-icin/, /tr/isletmeler-icin-veri/, /tr/embed/harita/, /tr/siteniz-icin-harita/, /tr/gelistiriciler-icin/.
- Cities: Cenevre (Cenevre'de); 48 NOBIL проверены. name_nom (D14) для tr не нужен (нет артиклей).
