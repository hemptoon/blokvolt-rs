# R-SQ — review of the Albanian (sq) world layer, 10.11.2026

Base: `l-sq` e029cc8. Branch: `r-sq`. `check.py`: 0 errors.

## What was read
- All 403 strings (map 125, pages 120, shell 41, prices 117), plus the place/country passages of `texts.json` (97 strings).
- All 150 countries: `name`, `slug`, `in_phrase`.
- Cities: all AL/XK/MK rows, every row marked as an exonym (67), the 500 largest `stage = month` cities, and the US/CA towns named like European ones.
- Slugs: `/sq/…` does not overlap with `/al/` and `/xk/` (`content/com/local/`) or with the world EN/SR/RU paths.

## Changed: 23 strings, 15 cities
1. **"vend" = place and country (the main issue).** Where the word meant "country" next to "vend karikimi", it is now "shtet":
   - `pl_country`, `pl_country_in`, `pl_cc` → shtet/shtete. "12 000 vende karikimi në 30 vende" became "… në 30 shtete";
   - `st_countries` (pages, prices), `h_more`, `lead_hub`, `d_gnet`, `p_net_share`, `method_p`;
   - `download.fields` country code.
   Where it meant "place" on its own, it is now "vend karikimi": `home_lead`, `method_p`, `c_price_note`, `disc`, and `download.fields` pid/name/max_kw/power_class.
2. **Case after "në" + country name.** `p_city_cmp` built "në {country_name}" from the nominative, which breaks for names like "Mbretëria e Bashkuar". The engine does not pass `{country_u}` to this string, so the construction is now "mesatarja për {country_name}: {country}".
3. **Wording.**
   - `c_price_kwh`: "çmimi zyrtar i rrjetit" (was "çmimi i listës").
   - `about_p`: "pozicionime të paguara".
   - `ft_checked`: "të dhënat nga".
   - `nav_about`: "Për të dhënat", the same as in the footer and on the map.
   - `m4`: the number is written "2 500–4 999", with an Albanian thousands separator.
4. **Cities.**
   - US/CA towns had been given European exonyms: Venice, Athens, Rome, Naples and Florence in the US, and London in Canada (8 rows). They now use the local name.
   - Bologna is now "Bolonjë", and Saint Petersburg is now "Shën Petërburg".
   - Sevilla, Málaga, Zaragoza, Luxembourg and Strasbourg now use the Albanian exonyms Seviljë, Malagë, Saragosë, Luksemburg and Strasburg.
   - The 500 largest `stage = month` cities (in file order) were all read; 488 have `decl_ok = 1` and the forms are correct.

## Left as is (deliberately)
- Short buttons use the singular imperative that is standard in Albanian UI: Dërgo, Anulo, Mbyll, Shfaq, Hiq. Sentences and links use "ju" (Kërkoni, Hapni). The ju-form would break the EN × 1.4 limit on buttons ("Send" → "Dërgoni").
- "prizë" for connector follows the glossary and /al/. The open question about "konektorë" stays with Andrei.
- The 544 cities with `decl_ok = 0` keep "në qytetin X". "në Breda" would also be acceptable, but the safe form was not changed.
- Countries: "Kenia", "Kamboxhia" and "Surinami" are definite CLDR forms and "në …" reads naturally, so they were not changed.

## Back-translation
A second agent reviewed all 27 changed lines blind: 17 OK, 8 MINOR, 2 ERROR.
- Both ERROR lines were already resolved: `home_lead` had been fixed before the check, and in `p_net_share` `{n_cities}` already carries "qytete" via `pl_city_in`.
- 5 MINOR lines were applied and the other 3 are cosmetic.

# L2-SQ — delta for blokvolt.com languages, 11.11.2026

Base: `dev` bb86f74. Branch: `l2-sq`. `check.py` (now all 8 string files + `texts.json` pay/routes + cities from `pages_state.json`): 0 errors.

## Added
- 274 keys: `strings_map` +29 (`ci_*` check-ins, `emb_open`), new `strings_pay` 93, `strings_press` 54, `strings_b2b` 33, `strings_embed` 65. HOME2 keys are not in `dev` yet.
- `texts.json`: `pay` (6 AFIR points) and `routes` (59 stop names, taken from this language's `cities.csv`: Lubjanë, Beograd, Sofje, Ohër, Çair …).
- `cities.csv`: +48 page cities missing from `names/cities.csv` (46 SE incl. NOBIL, 2 NO), local names; 10 ending in -a get "në qytetin X", `decl_ok = 0`.
- Own countries AL, XK: names, slugs and all 22 cities checked — no changes (Balkan countries get no world city pages, rule K3).

## Terms
- How to pay → "Si të paguani"; routes → "itinerare"; tolls → "pagesa rrugore", vignette → "vinjetë"; issue (of the index) → "botim"; check-in → "raportim"; embed → "futje në faqe"; widget stays "widget".
- "Is it working?" → "A punon?" / "Punon" / "Nuk punon", as in glossary `report_not_working`.
- "stacion" avoided (NOTES): AFIR point about existing stations → "vendet ekzistuese të karikimit".
- `{name}` is the indefinite CLDR form ("Gjermani"), so `afir_eu`/`afir_non` use "{name} — shtet anëtar i BE-së: …" instead of a sentence with {name} as subject.

## Back-translation (60 random new strings, blind agent)
43 OK, 17 MINOR, 0 ERROR. All 17 applied. Main pattern again "vend" = place/country → "shtet" where it means country; the same fix was carried to 13 more unsampled strings (apps_note, th_cover, typ_line, cost_note, h_by_country …). Other fixes: "nga 50 kW e lart" instead of clipped "50 kW e lart", `stops_note` rewritten, `ci_thanks` "kartelën e karikuesit" (not "kartë" = payment card), `d_route` "tre modele makinash".
Full table: `~/dev/evdb/work/L2-SQ/bt_result.json`.

## Open
- "prizë" vs "konektorë" for connector (from L-SQ) — still Andrei's call; new strings use "prizë" (`h_conn`, `conn_txt`, `what_cov`).

## FIXL 11.11.2026
Checked: new `strings_home.json` (71 keys), `strings_shell` lang_hint/lang_hint_close, D11 (`dv_p_lang`, `p_hub_na`), D13 connector → «konektor» (14 strings + 3 texts nodes), 7 new slugs, the 48 NOBIL towns (L2) + Geneva.
Back-translation (wave 2, blind): 10 home strings (title, data_as_of, search_none, near_err, map_alt, prices_p, p_ratio, work_p, trust_p, routes_p) + 6 changed (r_snaga, th_conn, conn_txt, d_city, dv_p_lang, p_hub_na).
- Fixed: `home.prices_p` used «pa regjistrim» for pay-as-you-go; the rest of the sq world layer says «ad hoc» (prices, press) → «Çmimi mesatar i publikuar ad hoc …».
- Fixed: `home.desc` shortened («ku të ndaleni në rrugë»), 222 chars vs EN 206.
- D13 resolved the open "prizë vs konektorë" point: connector types (CCS, Type 2, table/filter «Konektorët», `r_snaga` «konektorë të gabuar», download fields «Llojet e konektorëve») now «konektor»; «prizë» stays only for a household socket (none in the sq world layer now).
- NOBIL 48 towns verified: names = Swedish/Norwegian local forms with diacritics, -a names in the safe «në qytetin X» (decl_ok 0), consistent with the file. Geneva added: «Gjenevë», «në Gjenevë».
- D12 fixed (historical Albanian exonyms of towns in countries where Albanian is not official there): 3204509 Tivar → **Bar** («në Bar»), 787595 Pazar i Ri → **Novi Pazar** («në Novi Pazar»).
- D12 kept: North Macedonia and Kosovo towns (Shkup, Ohër, Kumanovë, Prishtinë, Pejë…) — Albanian is an official language there; Albanian spellings of current names (Nish, Budvë, Podgoricë, Nikshiq, Cetinë, Sarajevë); big-city exonyms (Vjenë, Selanik, Janinë, Korfuz, Stamboll, Athinë).
Open: «Kiev» (UA, Kyiv) kept as the established Albanian form — D13 does not cover sq, Andrei may want «Kyiv»; «Janinë»/«Korfuz» are standard, but a native check of the Greek exonyms is welcome.
