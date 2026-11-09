# L-UK — notes on the Ukrainian localisation of the world layer

Language code: `uk` (hreflang `uk`, script Cyrl, LTR). Prefix `/uk/`.

This language is prepared for later and is not switched on in production. It goes live only after gate G8 (K8-i18n engine).

## How readers are addressed

- The site stays impersonal, as in EN: no «ми» and no «редакція».
- Where the reader has to be addressed, the polite «ви» is used: «Відкрийте карту», «уточніть в оператора».
- Buttons use the infinitive: «Відкрити карту», «Завантажити», «Скинути фільтри».

## Terms (no `uk` column in glossary.csv, so the list was fixed for this session)

| EN | UK |
|---|---|
| charging station | зарядна станція |
| charging location / place | місце заряджання / місце |
| charging point | точка заряджання |
| charger | зарядний пристрій (in prose); «станція» in lists of fast/AC chargers |
| network | мережа (заряджання) |
| reliability | достовірність (даних) |
| open data | відкриті дані |
| connector | роз’єм |
| ad hoc price | ціна з разовою оплатою (ad hoc) |
| idle fee / session fee | плата за простій / плата за сесію |
| VAT | ПДВ |
| kWh | кВт·год |

Suggestion: add a `uk` column to glossary.csv from this table.

## Typography

- The apostrophe is unified to `’` (U+2019) in all files. CLDR uses `ʼ` (U+02BC); 3 country names were converted. If K8 needs U+02BC (the Unicode recommendation for Ukrainian), replace it with one sed.
- Number formatting (space as thousands separator, comma for decimals) is for the K8 registry to handle, not the strings.

## Plurals

- CLDR uk categories: one, few, many, other. They are checked with Babel in `check.py`.
- `other` is used for fractions. It is equal to the `few` form (the genitive singular): «1,5 місця заряджання».
- `pl_publoc.other` = «громадського місця заряджання».
- `_in` variants (after «у/в» + a number) are in the locative case:
  - `pl_city_in` — місті / містах;
  - `pl_country_in` — країні / країнах.

## Constructions that differ from EN

- `home_lead` (shell): EN has «{n} in {c}». In Ukrainian «у {c}» would need the locative case after the number, so it is written «{n}, {c} — з відкритих даних».
- `lead_hub` (prices): numbers without agreement are given as «мереж: {nets}, країн: {countries}». A bare number before a noun is wrong for 21, 31 and so on.
- `p_city_cmp`: «{country} в середньому по країні ({country_name})». {country_name} is in the nominative case, and the name in brackets avoids having to decline it.
- `t_city`: «Зарядні станції для електромобілів: {city}, {country}». The colon keeps the city in the nominative case.
- `fallback_u` = «у місті {x}». This is the safe form when a city has no checked locative.
- `regional_guide`: «Регіональний путівник для країни {country}». The noun «країна» keeps {country} in the nominative case.

## Countries (countries.csv)

- Names come from CLDR (Babel `Locale('uk').territories`). Shortened: HK Гонконг, MO Макао, MM М’янма, PS Палестина.
- Island countries and islands take «на»: на Кіпрі, на Мальті, на Кубі and others (27). This is the Ukrainian norm.
- Slugs follow the KMU 2010 transliteration (Resolution No. 55). Note that NL is `niderlandy`, because the rules give і → i.

## Cities (cities.csv)

- Ukrainian cities use their official names. Foreign cities use established exonyms, otherwise a practical transcription under the 2019 orthography: German h → г (Ейндговен, Гамбург).
- `decl_ok = 1` means the locative case was written by hand: «у Мюнхені», «у Гамбурзі». Indeclinable names count as checked: «в Осло».
- `decl_ok = 0` means the safe form «у місті X». It is used mostly for compound names: Bad …, Saint-…, …-sur-…
- All 5,605 cities are covered (month 2,353, quarter 3,119, balkan 133). decl_ok=1: 4,421; decl_ok=0: 1,184. Rare names are marked `транскрипція` in `note`. Small towns from the quarter stage need a native speaker's spot check.

## Back-translation check

A separate agent blind-translated 60 random strings (seed 20261109) back into EN and compared them with the original.

Result: 59 ok, 1 minor, 0 mismatch.

The one minor is `strings_shell.home_lead`: «{n}, {c}» instead of «{n} in {c}». It is deliberate (see «Constructions that differ from EN»).

The report is in `bt_report.md` in the work folder on the Mac.
