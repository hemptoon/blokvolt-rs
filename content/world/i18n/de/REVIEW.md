# R-DE — Lektorat Deutsch (10.11.2026)

Base `origin/l-de` (ba1d6e0), branch `r-de`. Native-editor pass over all 403 strings, texts.json (about_data, download), 150 countries, all 941+DACH cities and the first 500 `stage=month` cities outside DACH plus every exonym in the file (98).

## Changed

**Strings (29 keys)**
- Typography: German spaced en dash ` – ` instead of ` — ` in prose (home_title, home_h1, map_p, rs_card, ch_nav_rs, c_price_note, h1_hub, lead_hub, m1, data_p, pay_note, too_few, serbia_note). The bare “—” used as a table symbol (table_note, cars_note) is unchanged.
- crumbs: Brotkrumennavigation → Brotkrümelnavigation.
- report_map: “auf seiner Karte in der Kartenansicht” (Karte = card/map ambiguity) → “im Infofenster des Standorts auf der Karte”.
- disc: “Prüfen Sie vor der Fahrt beim Betreiber” → “Erkundigen Sie sich …”; second sentence rebuilt.
- p_hub_na: rephrased; “serbische Seiten” → “Seiten auf Serbisch” (not pages about Serbia).
- file_link: “öffentliche Ebene” → “Wöchentliche Datei mit allen öffentlichen Standorten”.
- home_h1: “Wo Sie Ihr Elektroauto laden können …”.
- Chips shortened (EN × 1.4): c_price → Ad-hoc-Preis; r_ne_radi → Geschlossen oder defekt; acc_public_pay_at_location → Öffentlich, vor Ort zahlen.
- Prices: h_profiles → “… – drei Fahrerprofile”; m1 “die ihn nennt” → “die diesen Tarif nennt”; pay_note “Karte” → “Zahlungskarte”; serbia_note rebuilt.

**texts.json (about_data)**
- title: “Ladekarten-Daten” (Ladekarte = RFID charging card in German) → “Daten der Ladestationskarte”; description likewise.
- notes 1, 5: “Punktkarte” → “Infofenster (des Standorts)”.
- note 3: “diese unterstützen diese Karte nicht” → “diese unterstützen oder empfehlen die Karte nicht” (endorse).

**countries.csv (2)**: DO in_phrase “in der Dominikanische Republik” → “… Dominikanischen Republik” (grammar bug); LC “in” → “auf St. Lucia”.

**cities.csv (5)**: Olmütz → Olomouc, Thorn → Toruń, Sathmar → Satu Mare (historic names rare in current German media); Ciudad de México → Mexiko-Stadt; GeoNames district “Stadt Winterthur (Kreis 1)” → “Winterthur (Kreis 1)”.

## Checked, left as is
- Plurals `{one, other}` incl. dative `_in` (Städten, Ländern); `pl_cc` other = “Ländern” is right — only used after “in” (home_lead).
- German “in X” needs no city declension → decl_ok = 1 everywhere is correct.
- Slugs: ASCII, natural, all under `/de/`; `content/com/local/` has no `de` → no collisions.
- Address form: Sie / impersonal throughout; no wir/uns, 24/7, sofort, ratings.
- Kept (current German usage): Breslau, Danzig, Stettin, Posen, Brünn, Budweis, Karlsbad, Hermannstadt, Kyjiw/Lwiw/Charkiw (Auswärtiges Amt), Swiss forms Neuenburg/Sitten/Freiburg im Üechtland.

## Open / disputed
- Length > EN × 1.4 that German cannot avoid: Schließen, Filter zurücksetzen, Daten herunterladen, Wird geladen…, Sonstiges, /Ladevorgang, ft_about “Über BlokVolt” (“Über” alone is not idiomatic), cur_local “Landeswährung” (“Lokal” reads as “pub”). Layout should allow wrapping.
- texts.json still carries `sources_pages` (translated by L-DE before the 23:55 rule). Kept, not deleted; K8 should read only about_data and download.
- Shared `names/cities.csv`: 6295520 “Stadt Winterthur (Kreis 1)” duplicates 2657970 Winterthur — for N/K to drop from the city list.
- Back-translation (blind, 29 changed strings): 11 remarks, 9 applied, 2 left (disc “Verfügbarkeit” = intended, both readings fine; lead_hub dashes = kept, mirrors EN).

---

# L2-de — Delta und Rückübersetzung (11.11.2026)

Branch `l2-de` from `dev` (bb86f74). HOME2 not yet in `dev` → 274 new keys: strings_map 29 (`ci_*`, `emb_open`), strings_pay 93, strings_press 54, strings_b2b 33, strings_embed 65. texts.json: new sections `pay` (6 nodes) and `routes` (59 nodes), `sources_pages.nobil` added (attribution verbatim).

Blind back-translation of 60 random new strings (separate agent, saw German only): 60/60 meaning kept, 0 discrepancies.
Minor, accepted:
- `strings_pay.t_pay_hub` — title rewritten for search („Laden bezahlen in Europa: Karte, App, Ladekarte“), H1 keeps the EN wording.
- `nav_pay`/`kick_pay`/`pay_more` = „Bezahlen“ (shorter than „So bezahlen Sie“ for navigation).
- `ci_n30` „Rückmeldungen“ for check-ins (no English loan word).
Fixed after the check: `pay_disc` „verkauft weder Strom“ → „weder Ladevorgänge“ (EN „charging“; avoid any hint of electricity sales).
