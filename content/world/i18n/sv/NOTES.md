# L-SV — svenska (sv), anteckningar

Datum: 2026-11-09. Bas: `g3-prices` cf44fc3. Gren: `l-sv`.

## Tilltal och ton
- Opersonligt som EN: inget ”vi/oss/redaktionen”. Imperativ i UI (”Öppna kartan”, ”Försök igen senare”) och ”du” bara där EN har ”you” (”innan du åker”, ”Vid laddaren betalar du…”). ”Ni” används inte — det är föråldrat i svensk UI-text.
- Citattecken: svenska ”…” (samma tecken på båda sidor).
- Procent med mellanslag: `{x} %` (svensk norm, Språkrådet). Tusental i texten: ”2 500–4 999 kWh”.

## Termer (glossary.csv har ingen sv-kolumn — valda här)
| EN | SV |
|---|---|
| charging location / place | laddplats / plats |
| charging point | laddpunkt |
| charging station | laddstation |
| network | nätverk (pl. nätverk); ”laddnätverk” i adressen |
| operator | operatör |
| reliability (data) | datans tillförlitlighet |
| connector | kontakt |
| power | effekt |
| ad hoc price | ad hoc-pris |
| plan (subscription) | abonnemang |
| household electricity | hushållsel |
| open data | öppna data |
| Community (OSM, OCM) | Användarbidrag (OSM, OCM) |

## Plural
CLDR sv: `one`, `other` (Babel 2.18). Alla `pl_*` är objekt `{one, other}`. ”nätverk” har samma form i singular och plural.

## {country_u}
`{country_u}` = `in_phrase` ur `countries.csv` (”i Tyskland”, ”på Island”). Strängar som `t_country` = ”Laddstationer för elbilar {country_u}” fungerar bara med prepositionen — det är avsikten (samma kontrakt som EN ”in Germany”).
- ”på”: 27 ö-stater/territorier (Island, Cypern, Malta, Kuba, Färöarna, Åland, Aruba …), se kolumnen `note` = ”prep på”.

## Slugs
`/sv/karta/`, `/sv/laddstationer/`, nät i land `natverk`, `om-data`, `ladda-ner`, `/sv/laddnatverk/`, `/sv/laddpriser/`, `/sv/om/`, `/sv/kallor/`, `/sv/metod/`. Länders slugs: å/ä→a, ö→o (”osterrike”, ”nederlanderna”).

## Ortnamn
- Alla 5 605 städer, `in_phrase` = ”i <stad>”, `decl_ok` = 1 (svenska böjer inte ortnamn).
- Exonymer bara där de är etablerade: Bryssel, Haag, Prag, Köpenhamn, Lissabon, Aten, Moskva, Bukarest, Belgrad, Neapel, Venedig, Brygge, Kyiv m.fl. München, Wien, Milano, Warszawa, Köln behåller lokalt namn (så skriver man på svenska).
- Finland: svenska officiella namn i tvåspråkiga kommuner (Helsingfors, Esbo, Vanda, Åbo, Vasa …) och etablerade traditionella (Tammerfors, Uleåborg, Björneborg, Lahtis). Lempäälä, Pirkkala, Iisalmi behåller finska namnet.
- Icke-latinsk skrift (GR, BG, RU, UA, KR …) → `name_en` om ingen svensk exonym finns.

## texts.json
- `about_data` och `download` översatta i sin helhet.
- `sources_pages`: bara beskrivande engelska i `name`/`licence` översatt; alla `attribution` ordagrant (krävs av licenserna). Krediteringsraden ”© OpenStreetMap contributors, BlokVolt” står kvar på engelska i licens- och attributionstexten.

## Kontroll
- `python3 content/world/i18n/sv/check.py` → 0 fel.
- Bakåtöversättning: en separat agent översatte 60 slumpvisa strängar (seed 20261109) tillbaka till EN utan att se originalet. Betydelsen stämde i alla 60. 17 stilanmärkningar; 11 rättade (below_p, report_map, disc, p_hub_na, acc_*_notice_required, src_com, how, about_desc, c_lead, n_places_none, d_net, hpc_note), 6 gällde `{country_u}` utan preposition — avsiktligt, se ovan.

## Öppet
- Inmatning av en infödd svensk talare innan G8 (titlar och priser).
- ”USA” (kort form) vs ”Förenta staterna” — valt ”USA”.
- `p_hub_na` nämner serbiska sidor — kan behöva ny lydelse när sv aktiveras (vilka språk täcker vad).
