# L-DA — dansk (da), mondo-lag, pul 3, 09.11.2026

Status: forberedt, ikke slået til. Danish is turned on only after gate G8.

## Tiltaleform

- Upersonlig stil. Ingen "vi", ingen "redaktionen". Passiv og upersonlige konstruktioner ("kan downloades", "Prisen bør kontrolleres").
- Formelt "De" bruges ikke: det lyder forældet på moderne dansk. Hvor en direkte tiltale ikke kan undgås, bruges "du". I praksis er det kun korte imperativer i grænsefladen ("Prøv igen senere", "Vælg, hvad der er forkert", "Zoom ind") — samme som EN.
- Licensteksten (download.licence_p) er skrevet om til upersonlig form ("Dataene må deles …, forudsat at der krediteres …").

## Terminologi (glossary.csv har ingen da-kolonne)

- charging station (sted) = ladestation; charger (apparat) = ladestander; charging point = ladepunkt
- charging location = ladested / ladesteder (pl_loc, pl_publoc); place = lokation (pl_place)
- network = ladenetværk (ens i ental og flertal); operator = ladeoperatør / operatør
- DC fast charging = DC-ladning / hurtigladning; DC charger = DC-hurtiglader
- data reliability = datapålidelighed; reliability score = pålidelighedsscore
- connector = stik; power = effekt; map = kort; point card = infoboks (ikke "kort", forveksles med landkort)
- VAT = moms (inkl./ekskl. moms); session fee = startgebyr; per-minute = minutpris; idle fee = blokeringsgebyr; plan = abonnement; per session = /opladning
- Forslag: tilføj kolonnen `da` i `names/glossary.csv` med ovenstående, når dansk slås til.

## Flertal (CLDR da: one, other)

- Kun pl_*-nøgler er objekter {one, other}. Dansk har ingen kasus, så `*_in` = grundformen.
- `pl_net`: "ladenetværk" i begge former — korrekt dansk.

## Adresser (slugs.json)

- /da/, /da/kort/, /da/ladestationer/, netvaerk, om-dataene, download, /da/ladenetvaerk/, /da/ladepriser/, /da/om/, /da/kilder/, /da/metode/
- Translitteration: æ → ae, ø → oe, å → aa (dansk standard for ASCII).

## Lande (countries.csv, 150)

- Navne fra CLDR (Babel 2.18, da). Forkortet: HK "Hongkong" (CLDR "SAR Hongkong"), MO "Macao", MM "Myanmar".
- NL = "Nederlandene" (CLDR). I daglig tale ofte "Holland" — bevidst ikke brugt.
- PS = "De palæstinensiske områder" (CLDR), XK = "Kosovo".
- in_phrase: "i X"; øer og øgrupper "på X" (24 stk.: CY, CU, IS, FO, MT, MU, LK, JM, BB, FJ, RE, PH, NC, TO, WS, AX, SJ, LC, MF, KY, GG, JE, IM, AW). Taiwan, Irland, Storbritannien, Puerto Rico, New Zealand, Singapore: "i".

## Byer (cities.csv, alle 5 605)

- Rækkefølge: DK (31) → resten af stage=month → resten.
- decl_ok = 1 overalt: dansk bøjer ikke bynavne efter "i".
- Navn: lokalt navn (5 401), latinsk form fra name_en for ikke-latinske skrifter (168, fx græske, bulgarske, ukrainske byer), danske eksonymer (24): Moskva, Sankt Petersborg, Athen, Thessaloniki, Lissabon, Prag, Bukarest, Venedig, Hamborg, Flensborg, Slesvig, Mexico City, Istanbul, Tirana, Kyiv m.fl.
- Bevidst lokalt navn (dansk praksis): München, Köln, Nürnberg, Wien, Bruxelles, Antwerpen, Milano, Napoli, Torino, Warszawa, Göteborg, Zürich, Beograd.
- Marseille-arrondissementer: "Marseille 13. arrondissement".
- Tosproget: Donostia / San Sebastián → "San Sebastián".

## Åbne punkter

- `pages.p_hub_na`: "USA og Canada dækkes på engelsk og russisk; de serbiske sider dækker Europa." — ordret oversat, passer ikke til en dansk side. Teksten bør skrives om (eller nøglen gøres sprogafhængig), før dansk slås til.
- `{net}-ladesteder` (d_gnet, d_network): bindestregsform; ved netværksnavne med mellemrum ("Allego GmbH-ladesteder") lyder det tungt. Alternativ: "Ladesteder fra {net}".
- `{country_u}` forudsætter, at motoren (K8) indsætter `in_phrase` fra countries.csv ("i Tyskland", "på Island").
- Prisindeksets navn i citatet (prices.data_p) står på engelsk som fast titel.
- Termer til afklaring: "abonnement" vs. "prisplan" (th_plan); "/opladning" vs. "/session".

## Kontrol

- `python3 content/world/i18n/da/check.py` → 0 fejl.
- Blind tilbageoversættelse af 60 tilfældige strenge: se afsnittet nedenfor.

## Tilbageoversættelse (blind, 60 tilfældige strenge)

- 60 af 60 stemmer i betydning. Ingen fejl.
- Rettet efter rapporten: about_data.intro "offentlige åbne data" → "myndigheders åbne data" (EN: government open data).
- Fuld rapport: `backtranslation_report.md`.

## FIXL (11.11.2026)
- `strings_home.json` ny (71 nøgler); `strings_shell` + `lang_hint` «Denne side findes også på dansk», `lang_hint_close` «Luk».
- Slugs: `/da/betaling/`, `/da/ruter/`, `/da/til-medier/`, `/da/data-til-virksomheder/`, `/da/embed/kort/`, `/da/kort-til-hjemmesider/`, `/da/til-udviklere/`.
- `pages.p_hub_na` omskrevet (åbent punkt løst). `embed.dv_p_lang` = «Sprog: bestemmes af widgettens adresse».
- cities.csv: 5 654 rækker (alle i names/cities.csv); check.py kontrollerer nu også, at alle bysider i pages_state har et navn.
- D12: danske eksonymer beholdt (se REVIEW). Ingen `name_nom` (da har ikke D14).
