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

## FIXL 11.11.2026

Geprüft (Rückübersetzung DE → EN, Welle 1): 20 Strings aus `strings_home` (title, desc, h1, sub, search_none, near_err, map_alt, map_err, map_more, countries_p, ap_note, below_h, prices_p, p_ratio, p_src, pay_p, routes_p, work_p, trust_p, org_desc) und alle übrigen geänderten Strings (`pay.afir_eu`, `pay.afir_non`, `pay.conn_txt`, `embed.dv_p_lang`, `pages.p_hub_na`, `shell.lang_hint`, `shell.lang_hint_close`, `texts.routes[15].stops[2].city`) sowie die 9 D12-Städtenamen.
Ergebnis: keine Sinnabweichung. Bewusste Unterschiede:
- `desc`: „für jeden Standort“ am Ende gestrichen (Länge ≤ 160); `title` als Suchphrase „E-Auto laden in Europa und weltweit – Karte, Preise, Bezahlen“ (72 Zeichen).
- `org_desc`: EN „independent reference“ → „Neutrales Nachschlagewerk“ (Regel aus NOTES).
- `p_ratio`: „{x}× so teuer wie zu Hause“ statt wörtlich „{x}× der Hauspreis“.
- `map_alt`: „lime“ → „hellgrün“.

D14: `countries.csv` + Spalte `name_nom` (Artikel: die Schweiz, die Niederlande, das Vereinigte Königreich, die Vereinigten Staaten, der Irak, das Kosovo …). Umgeschrieben:
- `afir_eu` „Für {name_nom} als EU-Mitglied gilt bei öffentlichen Ladesäulen die … (AFIR).“
- `afir_non` „Die AFIR ist EU-Recht; für {name_nom} als Nicht-EU-Land greifen die Regeln unten womöglich nicht. …“
- `conn_txt` „Zahlen zu Steckern, Schnellladern und Ladenetzen für {name_nom} finden Sie auf der Länderseite.“
Bewusst „für {name_nom}“ und nicht „{name_nom} gehört …“: Ein Subjekt bräuchte Verb-Kongruenz („die Niederlande gehören“), die der Motor nicht kennt. Nach „für“ ist Akkusativ = Nominativ für Femininum, Neutrum und Plural; falsch wäre es nur bei maskulinen Ländern (der Irak, der Iran, der Libanon, der Sudan) — keines davon hat eine Länder- oder Bezahlseite. `{name_nom}` steht nie am Satzanfang.

D12 (neutrale Ortsnamen anderer Länder), `cities.csv` + `texts.routes`:
Breslau → Wrocław, Danzig → Gdańsk, Stettin → Szczecin, Posen → Poznań, Hermannstadt → Sibiu (auch Routenhalt routes[15]), Brünn → Brno, Budweis → České Budějovice, Karlsbad → Karlovy Vary, Pilsen → Plzeň. Pressburg kam nicht vor (Bratislava war schon lokal); Olmütz/Thorn/Sathmar waren schon lokal.
Bleiben (übliche neutrale Exonyme bzw. Amtssprache vor Ort): Prag, Warschau, Krakau, Bukarest, Belgrad, Kopenhagen, Brüssel, Lüttich, Brügge, Ostende, Ypern, Mailand, Turin, Neapel, Venedig, Padua, Mantua, Straßburg, Nizza, Dünkirchen, Lissabon, Saragossa; Bozen/Meran (amtlich zweisprachig); Luxemburg/Schweiz (Deutsch Amtssprache).
D13: „Kyjiw“ war schon gesetzt, „Kiew“ kommt nirgends vor.

Offene Zweifel:
- Pilsen/Brünn sind im heutigen Deutsch neutraler als Breslau/Danzig; wegen einheitlicher Regel (CZ/PL/RO: lokal außer Hauptstädten und Krakau) trotzdem lokal. Bei Bedarf Pilsen zurück.
- Trient (Trento) gelassen — geläufig, aber historisch österreichisch; Kandidat für „lokal“, falls die Regel strenger sein soll.
