# L-NL — Dutch (nl) for the world layer — notes

Built 09.11.2026 (pool 3, task L-NL) on branch `l-nl` from `g3-prices` (cf44fc3). Not enabled anywhere: switching on comes after gate G8 through the K8 language registry.

## Register and voice

- Neutral Dutch, readable in the Netherlands and Flanders (no NL-only or BE-only words where a common one exists).
- Reader addressed with **u / uw** (formal), per the pool rule "polite or impersonal form". Many Dutch EV sites use "je";
  switching would be a global search-and-replace, not a re-translation — question for Andrei below.
- BlokVolt stays impersonal: no "wij/we/ons/onze/redactie" (check.py enforces it), no "24/7", no "direct/meteen" promises,
  no network rankings, no Evolako.
- Numbers in prose: decimal comma, thousands dot; percentages "25%" without a space (Dutch norm; `pct` = `{x}%`).

## Terms (glossary.csv has no nl column — this is the de-facto list; propose adding an `nl` column)

charging station / site → laadstation · charging location → laadlocatie · location → locatie · charger (device) → laadpaal,
DC charger → snellader · charging point → laadpunt · public → openbaar · charging network → laadnetwerk / netwerk ·
operator → exploitant · connector → stekker (types → stekkertypes) · power → vermogen · fast charging → snelladen ·
HPC → ultrasnelladen · start/session fee → starttarief · per-minute fee → minuuttarief · idle fee → blokkeertarief ·
VAT → btw (incl. btw / excl. btw) · charge card → laadpas · subscription → abonnement · reliability/confidence →
betrouwbaarheid · open data → open data · source → bron · licence → licentie · breadcrumbs → kruimelpad.

## Plurals

CLDR nl (Babel 2.18): `one`, `other`. Every `pl_*` key is `{"one": …, "other": …}`. Dutch has no case after numbers,
so `pl_city_in` / `pl_country_in` equal `pl_city` / `pl_country`.

## Slugs (`slugs.json`)

`/nl/`, `/nl/kaart/`, `/nl/laadstations/`, `netwerk`, `over-de-data`, `downloaden`, `/nl/laadnetwerken/`, `/nl/laadprijzen/`,
`/nl/over/`, `/nl/bronnen/`, `/nl/methodologie/`. Country slugs are Dutch (`duitsland`, `verenigd-koninkrijk`,
`ijsland`); city and network slugs stay shared (P1).

## Countries (`countries.csv`, 150)

CLDR 47 `name_nl` from `names/countries.csv`, except short forms like EN: Hongkong, Macau, Myanmar.
`in_phrase`: "in X"; with article: in de Verenigde Staten, in het Verenigd Koninkrijk, in de Verenigde Arabische Emiraten,
in de Filipijnen, in de Dominicaanse Republiek, in de Palestijnse gebieden; islands with "op": op Cyprus, op Malta,
op IJsland, op Mauritius, op Jamaica, op Cuba, op Aruba, op Réunion, op Fiji, op de Kaaimaneilanden, op de Faeröer …
(Sri Lanka and Taiwan: "in").

## Cities (`cities.csv`, all 5,605)

- Dutch has no case: every `in_phrase` is "in X", `decl_ok = 1`.
- Belgium: official Dutch names for Brussels and Walloon towns (Brussel, Luik, Namen, Bergen, Doornik, Hoei, Waver,
  Nijvel, Eigenbrakel, Moeskroen, Aarlen, Aat, Tubeke, Lessen, Wezet, Zinnik, 's-Gravenbrakel, Gembloers).
  Kept as is where Flemish usage keeps the French name (Charleroi, Seraing, Verviers, La Louvière, Louvain-la-Neuve,
  Saint-Nicolas — the Liège one, not Sint-Niklaas).
- Established Dutch exonyms elsewhere (91 in total, `note = exoniem`): Parijs, Rijsel, Duinkerke, Straatsburg, Keulen,
  Aken, Berlijn, Neurenberg, Kleef, Londen, Lissabon, Rome, Milaan, Napels, Turijn, Florence, Venetië, Genua, Padua,
  Wenen, Bazel, Praag, Warschau, Krakau, Boedapest, Boekarest, Kopenhagen, Moskou, Athene, Korfoe, Luxemburg,
  Tokio, Peking, Kaapstad, Teheran …
- Everything else: the local Latin name unchanged (München, Zürich, Genève, Göteborg, Frankfurt am Main).
- Non-Latin scripts (143 rows, `note` says so): the EN form from `name_en`, with Dutch exonyms where they are common
  (Moskou, Sofia, Athene, Hongkong, Nizjni Novgorod, Jekaterinenburg, Boergas, Roese).

## Open / for K8

- `world_prices.py` has hard-coded month names (`MONTHS`) for en/sr/ru; for nl they should come from Babel
  (januari … december), not from these files.
- `strings_pages.p_hub_na` says which languages cover the US/Canada — the sentence is language-specific and must be
  revisited when nl is switched on.
- `strings_shell.about_p` keeps "onafhankelijk" because the EN source has it (the "nezavisni" ban in CONTENT_STYLE is
  Serbian-only) — align if the EN changes.
- Cyrillic/Greek city names other than the exonyms above use English transcription (Ivanovo, Novosibirsk, Volos);
  strict Dutch transliteration (zj, oe, sj) would change ~60 names — low priority, decide with the K8 switch-on.
- Glossary: suggest adding an `nl` column to `names/glossary.csv` from the term list above.

## Back-translation check

See `BACKTRANS.md` (60 random strings, NL → EN by a separate reviewer, compared with the source).

## L2 (11.11.2026)

- Card payment: **betaalkaart** (neutral NL/BE; AFIR covers debit and credit), not "bankpas" (NL) / "bankkaart" (BE).
- Check-in UI: answer → antwoord, check-in (count) → melding, driver → rijder / EV-rijder.
- Press: issue → editie, credit → bronvermelding; B2B: data → gegevens (plural verb).
- `{cu}`, `{lo}`, `{hi}` are expected to be full in-phrases ("in België"); route cities in texts.json use cities.csv names.
- check.py now covers all 8 strings files and texts.json `pay` / `routes`; back-translation in BACKTRANS_L2.md.

## FIXL (11.11.2026)

- D13: the reader is addressed with **je / je eigen** everywhere (was u/uw). check.py now bans «u/uw/uzelf» instead of «je/jij/jouw».
- Slugs (F5): `/nl/betalen/`, `/nl/routes/`, `/nl/pers/`, `/nl/gegevens-voor-bedrijven/`, `/nl/embed/kaart/`,
  `/nl/kaart-voor-je-website/`, `/nl/ontwikkelaars/`.
- Home (F3): "charging place" → laadlocatie; Asia-Pacific → Azië-Pacific; "how to pay" heading → «Zo betaal je» (menu stays «Betalen»).
- Cities: 48 NOBIL towns (local Swedish/Norwegian names, «in X») + Genève (2660646). No name_nom needed (no articles with country names in subject position except «de Verenigde Staten» etc., not used with `{name}`).
- FIXL2: +821 cities from names/cities_extra.csv (own market 34)
