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
