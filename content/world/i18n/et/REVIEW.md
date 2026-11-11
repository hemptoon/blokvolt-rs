# R-ET / L2-et — review of the Estonian package (11.11.2026)

Branch `l2-et` from `dev` (bb86f74). No R-ET session ran before, so the whole package was reviewed like R-IT.

## Strings (403 existing + 274 new)
49 existing strings changed:
- Buttons/chips to 2sg imperative (21): map_btn, open_map, more_map, close, share, r_send, r_cancel, rep, report, ch_report, reset, filters_show, acc_all, net_search, net_remove, download, download_link, osm_fix, skip, ch_skip, search_label.
- Ambiguity: `loading` *Laadimine…* (= also "charging") → *Laaditakse…*; `r_sending` → *Saadetakse…*; `report_map` "kaardil selle kaardi nupuga" (map/card both *kaart*) → "koha infokaardi nupuga".
- ad hoc unified to *lepinguta*: `c_price` (was *ühekordne laadimine*); `lead_hub` tautology removed.
- Cases: `t_city`, `t_city_cc`, `d_city` → `{city_u}` (*… laadimisjaamad Tallinnas (Eesti)*); `t_near` no longer needs a genitive; `p_city_cmp` less bookish.
- Naturalness: *segamini* (= "jumbled") → *kombineeritud*; *mahe ilm* → *mõõdukas ilm*; *Laadijas tasutakse* → *Laadijal*; *viitelised* → *informatiivsed*; `th_month` → *Kuutasu*; `regional_guide` *teejuht* (travel guide) → *juhend*; `about_p` "Ei mingeid …" → plain statement; OSM credit *kaastöötajad* → *kaastöölised* (as in about_data).
- texts.json: *Baashinne* → *Algne hinne*, *Vahemik* → *Piirid*, passive "kinnitatud … poolt" rewritten.

## Countries (150)
Checked, no changes. *Holland* kept (what people search; official short form *Madalmaad*) — question below.

## Cities
- EE: Tallinn (page), Tartu — both correct, `decl_ok=1`. No EE city from pages_state.json is missing.
- 14 fixes: US/CA namesakes no longer get European exonyms (Venice ×2, Athens ×2, Rome, Naples, Florence → English names); *Gent'is* → *Gentis*, *Halifax'is* → *Halifaxis*, *Muttenz'is* → *Muttenzis*, *Roeselare'is* → *Roeselares*; *Nižnii Novgorod* → *Nižni Novgorod*; *Rostov-na-Donu* → *Rostov Doni ääres* (EKI).
- 7 auto rows confirmed (`decl_ok=1`): Jekaterinburg, Rjazan, Tjumen, Espoo, Oulu, Vantaa, Malmö.
- Remaining 5 456 auto rows stay `decl_ok=0`: et builds city pages only for EE (market_countries), so their in_phrase is not used on pages. The apostrophe rule (889 rows, FR/US/CA/BE/GB) has misses where the final consonant is pronounced; fix before et gets city pages outside EE.

## Back-translation
See bottom.
A second agent translated 60 random new strings back to EN blind (seed 20261111): **60/60 match in meaning**, 0 grammar errors. It flagged 17 style points; 11 applied:
"kiirteemaks" (misparses as *kiir+teemaks*) → *kiirtee(de) teemaks*; *Reis, EUR* → *Reisi hind, EUR*; `t_route` "hind" → "reisi hind"; "peatused kuni iga 150 km tagant" → "kuni 150 km vahega" (`d_routes`, `d_route`); `lead_route` "+ võimsusega"; `conn_txt` country moved to the front; `cf_view_help` "nihutage … linnani"; `dv_f_demo` word order; `dv_balkan_rs` *avatud JSON* → *avaandmed JSON-vormingus*; `dv_open_btn` clearer; `ci_privacy` "kui see on sisestatud".
Kept on purpose: *rändlus(rakendus)* (Estonian EV usage), *lepinguta* (one term site-wide), *kodu elektrihind* (consistent with prices pages), *asukohad* link next to the network name in a table, *usaldusväärsus 70+* (scale is explained on the page).

## Questions
1. *Holland* or official *Madalmaad* for NL (slug `holland`)? Kept *Holland*.
2. *Kiiev* (EKI, current Estonian usage) — kept.
3. Buttons now 2sg (*Ava, Sulge*), messages polite plural — OK as the rule for et?
