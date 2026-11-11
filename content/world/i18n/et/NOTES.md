# L-ET — eesti keel (Estonian), notes

Branch `l-et` from `g3-prices` (cf44fc3). Everything lives in `content/world/i18n/et/`. Not enabled in prod (gate G8).

## Form of address
- Polite plural imperative everywhere, incl. buttons and chips: *Avage kaart*, *Laadige alla*, *Teatage veast*, *Proovige hiljem uuesti*. No *meie/me*, no *toimetus*.
- Estonian UIs often use the 2nd-person singular on buttons (*Ava*, *Vaata*). Chosen consistency over that convention; R-ET may switch buttons/chips to 2sg if they look too long (EN × 1.4).

## Plurals
- CLDR `et`: `one`, `other`. `one` = nominative singular, `other` = partitive singular (Estonian puts the noun in partitive sg after numbers > 1: *5 linna*, *5 laadimiskohta*).
- `pl_city_in`, `pl_country_in`, shell `pl_cc` = inessive in both forms (*5 linnas*, *150 riigis*): Estonian numeral phrases in inessive keep the noun singular. Used in `p_net_share`, `p_gnet`, `home_lead` ("Üks kaart: {n} {c}" → "… laadimiskohta 150 riigis").

## Case before names
- `{city_u}` / `{country_u}` → `in_phrase` from `cities.csv` / `countries.csv` (inessive *-s* or adessive *-l*).
- Strings that in EN use plain `{city}` after "in" were rebuilt with a colon so the case never breaks: *Elektriautode laadimisjaamad: {city}, {country}*.
- `fallback_u` = "asukohas {x}" (only if a city has no in_phrase; all 5 605 have one).

## Countries (150)
- Names: CLDR `et` (Babel), short forms for HK *Hongkong*, MO *Macau*, MM *Myanmar*, PS *Palestiina*, SZ *Eswatini*.
- in_phrase: -maa → adessive *-maal* (Saksamaal, Prantsusmaal, Venemaal, Iirimaal, Uus-Meremaal); islands and island states → adessive (*Islandil, Küprosel, Maltal, Kuubal, Sri Lankal, Filipiinidel*); plurals (*Ameerika Ühendriikides, Araabia Ühendemiraatides*); irregular genitives by hand (*Egiptuses, Iraagis, Kuveidis, Ühendkuningriigis, Lõuna-Aafrika Vabariigis*); rest inessive by vowel/consonant rule. 45 rows marked `käsitsi`.
- Slugs: ASCII of the Estonian name (õ→o, ä→a, ö→o, ü→u, š→s, ž→z): *saksamaa*, *prantsusmaa*, *uhendkuningriik*.

## Cities (5 605, all stages)
- 135 hand-checked (`decl_ok=1`, note `käsitsi`): Baltic cities, capitals and big exonyms — *Riia, Viin, Varssavi, Rooma, Pariis, Berliin, Kopenhaagen, Brüssel, Haag, Lissabon, Ateena, Belgrad, Bukarest, Genf, Peterburi, Kiiev, Helsingi, Turu*; Lithuanian -as/-us/-is → *-es* (*Kaunases, Vilniuses*).
- 5 470 automatic (`decl_ok=0`, note `auto: -s/-is reegel`): local Latin name (RU/BY: Estonian transliteration of the Russian name; other non-Latin: EN name), inessive by the standard rule for foreign names — vowel → *-s*, consonant → *-is*; French/English silent endings with apostrophe (*Fougères'is, Scunthorpe'is, Bordeaux's*). Chosen over a "linnas X" construction because it reads naturally and the rule is regular; R-ET should confirm the top month cities and set `decl_ok=1`.

## Slugs
`/et/`, `/et/kaart/`, `/et/laadimisjaamad/`, net `vork`, about `andmetest`, download `laadi-alla`, `/et/laadimisvorgud/`, `/et/laadimishinnad/`, `/et/teave/`, `/et/allikad/`, `/et/metoodika/`. No collisions with `content/com/local/` (no `/et/` section there).

## Disputed terms (for R-ET)
- network → *laadimisvõrk* everywhere (long on chips; *võrk* possible).
- ad hoc → *ühekordne laadimine* (map) vs *lepinguta* (prices) — pick one.
- plan/subscription → *pakett*; HPC, DC, AC kept.
- *Vahemik*, *baashinne* in texts.json sound technical.
- `p_city_cmp`: "riigis {country_name}" — grammatical but bookish.

## Glossary
`glossary.csv` has no `et` column; terms chosen: laadimisjaam, laadimiskoht, laadimispunkt, laadimisvõrk, kiirlaadija, operaator, laadimishind, avaandmed, usaldusväärsus.

## Back-translation (60 random strings)
Independent agent translated 60 random ET strings back to EN blind, then compared: **60/60 match in meaning, 0 grammar errors**. Its one "bug" (`pl_loc` shown as an object) is a sampling artefact — plural keys are objects by contract. Worth a look: `t_net` / `d_network` "{net} laadimishinnad {country_u}" reads right only with the inessive in_phrase (which the engine gives).

## L2-et (11.11.2026)
- +274 keys: strings_map 29 (`ci_*`, `emb_open`), new strings_pay 93, strings_press 54, strings_b2b 33, strings_embed 65. HOME2 keys not in `dev` yet — LANGI adds them.
- `texts.json`: sections `pay` (6 AFIR points, `afir.points[i]`) and `routes` (59 stop cities, `routes[i].stops[j].city`), LANG0 format.
- ad hoc → **lepinguta** everywhere (map card, prices, pay, press); first mention on pay pages "lepinguta (ad hoc)".
- Buttons, links and chips → 2nd person singular (*Ava kaart, Sulge, Jaga, Saada, Tühista, Teata veast, Laadi alla*), as Estonian UIs do; sentences and messages stay polite plural (*Proovige uuesti, Kontrollige*).
- "Loading…" → *Laaditakse…* (*Laadimine* also means "charging").
- `{cu}` (pay) = in_phrase of countries.csv; `{name}` (pay) = nominative, so `conn_txt` uses "(…{name})".
- City titles use `{city_u}` (`t_city`, `t_city_cc`, `d_city`) — engine must pass `city_u` for et; `t_near` → " (lähedal: {x})" (x is nominative).
- No "me/meie/toimetus/kohe" (check.py). "toimetuslik" avoided → *ajakirjanduslik sisu*.
- check.py: all 8 files, `texts.pay`/`texts.routes` against the multilingual nodes of pay.json/routes.json, `{city_u}`/`{country_u}` accepted for `{city}`/`{country}`/`{country_name}`.

## FIXL (11.11.2026)
- `strings_home.json` — 71 keys; plurals {one, other} = nominative / partitive sg (*laadimiskoht / laadimiskohta*, *riik / riiki*, *avalik koht / avalikku kohta*).
- Section slugs: /et/kuidas-maksta/, /et/marsruudid/, /et/meediale/, /et/andmed-ettevotetele/, /et/embed/kaart/, /et/kaart-veebilehele/, /et/arendajatele/.
- D13: Kiiev, Holland, 2sg buttons / polite messages — kept. name_nom (D14) not needed for et.
- cities.csv: +48 NOBIL (-s/-is rule, decl_ok=0) + Genf/Genfis.
