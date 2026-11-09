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
