# R-IT — вычитка итальянского пакета (10.11.2026, 00:15–00:50)

База `origin/l-it` (78af4a2), ветка `r-it`. Редактор независимый, перевод L-IT в целом чистый: термины совпадают с `glossary.csv` (it), тон безличный (инфинитив в инструкциях, повелительное 2 л. только на кнопках — норма итальянского UI), без «noi», «redazione», «24/7», «subito».

## Строки — просмотрены все 403, исправлено 16

Падежи и предлоги (по уточнению пула 4 о `{city_u}`/`{country_u}`):
- `t_city`, `t_city_cc`, `d_city`: «a {city}» → `{city_u}`; теперь L'Aia, La Spezia, Pireo и ad-формы получают правильный предлог из `cities.csv`.
- `p_city_cmp`: «in media in {country_name}» → «in media {country_u}» (было бы «in Stati Uniti», «in Paesi Bassi»).

Естественность и точность:
- `c_price_note`: «in questo sito» (читалось как «на этом сайте») → «in questa stazione».
- `odbl_note`: «dati uniti» → «dati aggregati».
- `osm_fix`: «Correggere anche in OpenStreetMap» → «Correggi anche su OpenStreetMap» (ссылка-действие как остальные кнопки; «su» для платформы).
- `below_p`: «solo finché» → «solo quando».
- `dataset_desc`: «Siti delle stazioni… uniti da fonti» → «Siti di ricarica pubblici… ricavati dall'unione di fonti».
- `moved`: «spostata in» → «trasferita a».
- `method_p`: «aggiornamento» (freshness) → «data dell'ultima conferma».
- `lead_hub`, `h_profiles`: «conducente» → «automobilista»; заголовок «Quanto costano 100 km: tre profili di automobilista».
- `m4`: «il price cap di Ofgem» → «il tetto ai prezzi di Ofgem (price cap)».
- `h_more`: «Altro {country_u}» → «Ancora {country_u}».
- `home_title`: добавлено «per auto elettriche» — как во всех остальных заголовках (SEO).

Длина кнопок и чипов: все в пределах EN × 1,4.

## Страны — все 150 проверены, исправлено 2
- AW «a Aruba» → «ad Aruba».
- FO слаг `isole-fr-er` → `isole-faer-oer` (æ→ae, ø→oe).
- Остальные `in_phrase` верны: «negli Stati Uniti», «nei Paesi Bassi», «nella Repubblica Ceca», «a Cipro», «alle Barbados», «sull'Isola di Man», «alla Riunione».

## Города — проверены IT/CH/SM, ~110 экзонимов и крупные города month; исправлено 301
- 296 городов на A-: «a Amburgo» → «ad Amburgo», «ad Aosta», «ad Anversa», «ad Atene» (норма «ad» перед a-).
- Тёзки в США/Канаде получили итальянский экзоним европейского города: London (CA), Dublin (US) ×2, Athens (US) ×2 → английское название.
- Rīga → Riga, Prishtinë → Pristina (устоявшиеся итальянские формы).
- Экзонимы проверены: Monaco di Baviera, Francoforte sul Meno, Friburgo in Brisgovia, Colonia, Aquisgrana, Ratisbona, Augusta, Treviri, Coblenza, Passavia, Lione, Marsiglia, Tolosa, Lilla, Digione, Avignone, Tolone, Anversa, Gand, Lovanio, Liegi, L'Aia, Leida, Varsavia, Cracovia, Breslavia, Danzica, Salonicco, Leopoli, Smirne, Siviglia, Saragozza, Cordova, Zurigo, Coira, Losanna, Lubiana, Zagabria, Belgrado — верно.
- Французские артикли в названиях оставлены как есть («a Le Havre», «a La Rochelle») — норма итальянского.
- `decl_ok` = 1 сохранён: исправленные формы верны.

## Слаги
- `prices`: `/it/prezzi-ricarica/` → `/it/prezzi-di-ricarica/` — в одном стиле с `stazioni-di-ricarica`, `reti-di-ricarica`.
- Пересечений с EN/SR/RU и местными разделами нет (префикс `/it/` свой, местного раздела `content/com/local/it/` нет).

## Спорное (оставлено, решает Андрей)
1. «Kiev» (оставлено; так пишут Treccani и большинство СМИ) vs «Kyiv».
2. «Repubblica Ceca» (оставлено) vs CLDR «Cechia».
3. «Malines» для Mechelen (итальянская традиция) — можно «Mechelen».
4. «Sito»/«siti» для location — из глоссария; в одиночку («Siti», «Siti pubblici») может читаться как «сайты». Альтернатива — «punti di ricarica» нельзя (это charging point). Оставлено по глоссарию.

## Проверка
`python3 content/world/i18n/it/check.py` — 0 ошибок, 3 предупреждения. check.py обновлён: `{city_u}`/`{country_u}` засчитываются вместо `{city}`/`{country}`/`{country_name}` (уточнение пула 4).

## L2-IT back-translation (11.11.2026)
Blind back-translation by a separate agent of 60 random new strings (seed 1111: strings_map ci_*, pay, press, b2b, embed, texts.pay). Meaning: 60 of 60 equivalent, 0 major. Wording notes (7) — all fixed:
- `map.ci_thanks`, `ci_err_limit` (and for consistency `ci_once`, `ci_err`, `ci_demo_note`, `ci_rules`, `ci_privacy`): "risposta" → "segnalazione" (a user check-in reads as a report, matches `ci_n30`).
- `pay.th_apps_c`: "che indicano il Paese" → "con il Paese in elenco" (= listed in coverage).
- `pay.th_place`: "Sito" → "Luogo" (in the route table "sito" read as website).
- `pay.gap_line`: word order made natural, "nel livello pubblico dei dati" at the end.
- `b2b.lic_p`: share-alike = clausola «condividi allo stesso modo» (official CC/ODbL Italian wording).
- `embed.cf_country_any`: "(oppure l'area della mappa qui sotto)".
Not changed: `pay.h_stops` has "150 km" written in, as in EN; `kick_pay` = `pay_more` = "Come pagare", as in EN.

## FIXL 11.11.2026
Scope: new `strings_home.json` (71 keys), shell `lang_hint`/`lang_hint_close`, D11 (`embed.dv_p_lang`, `pages.p_hub_na`), D14 (`pay.afir_eu`, `afir_non`, `conn_txt` with `{name_nom}`), countries.csv `name_nom`, 49 FIXL cities, 7 section slugs.
Back-translation (wave 1, blind, done by the FIXL agent itself): 20 home strings (title, desc, h1, sub, search_none, near_err, map_alt, map_err, countries_h, dc_line, ap_note, below_h, prices_p, p_ratio, p_src, routes_h, routes_p, work_p, trust_p, org_desc) + all 7 other changed strings. Meaning equivalent in all; fixes:
- `pay.afir_eu`: "there" was lost → "alle colonnine pubbliche **del Paese**".
- home `title` shortened to 71 chars ("Colonnine in Europa e nel mondo: mappa, prezzi e come pagare | BlokVolt"); "EV" is implied by "colonnine".
Accepted divergences: `routes_h` "Viaggi in auto" (= car trips, EN "Road trips"); `below_h` "Meno siti: da vedere sulla mappa"; `countries_h` "La ricarica Paese per Paese".
D12: no Fiume/Pola/Zara in the file (Croatian/Slovenian coast already local: Rijeka, Pula, Zadar, Koper). Grep of other exonyms of foreign towns: Nizza, Mentone, Breslavia, Danzica, Stettino, Leopoli, Smirne, Salonicco, Corfù, Scutari, Valona — all are the current it.wikipedia/Treccani titles, not irredentist forms → kept. Doubt for Andrei: Mentone (ex-Sardinian town, like Fiume/Pola/Zara a "lost" town) and Breslavia/Stettino (old-fashioned; "Wrocław"/"Szczecin" also common) — switch if the D12 rule should be read strictly.
Open: `pages.p_city_cmp` uses `{country_u}` where EN has `{country_name}` (pool 4 decision; allowed by check.py, flagged by `world_i18n.py check`). `pay.conn_lnk` keeps `{name}` ("Stazioni di ricarica: {name}").
