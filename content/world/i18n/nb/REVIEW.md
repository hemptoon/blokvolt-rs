# R-NB — вычитка норвежского букмола (пул 4, 10.11.2026)

База `origin/l-nb` (`4613a58`), ветка `r-nb`. Перевод L-NB в целом хороший: живой букмол, термины единые, плейсхолдеры целы. Исправлено 23 места, ничего не переписывалось без причины.

## Строки (403 просмотрены, 16 исправлено)

Единство и норма:
- `pages.pct` `{x}%` → `{x} %` — норма Språkrådet (пробел перед %), так же уже было в длинных текстах («10 %», «20–30 %»).
- `pages.report` «Meld fra om en feil» → «Meld fra om feil» — как `map.rep` и `map.ch_report`.
- `pages.skip` «Hopp til innholdet», `map.ch_skip` «Gå til innholdet» → обе «Hopp til hovedinnholdet» (стандартная норвежская ссылка доступности).
- `pages.crumbs` «Navigasjonssti» → «Brødsmulesti» — так называют хлебные крошки норвежские сайты (aria-label).
- «sjåfør» → «bilist» в `prices.lead_hub` и `prices.h_profiles`: «sjåfør» в норвежском — водитель по профессии.
- `map.conf_note` «Dette vurderer dataene…» → «Vurderingen gjelder dataene om punktet, ikke nettverket.» — калька с EN звучала неестественно.

Длина кнопок, чипов и заголовков таблиц (не длиннее EN × 1,4):
- `map.copied` «Lenken er kopiert» → «Lenke kopiert»;
- `map.acc_public_pay_at_location` «Offentlig, betaling på stedet» → «Offentlig, betal på stedet»;
- `map.ch_ft_checked` «kontrollert» → «sjekket»;
- `prices.th_ratio` «DC kontra hjemme» → «DC mot hjemme»;
- `prices.th_net`, `prices.th_nets` «Ladenettverk» → «Nettverk»; `prices.h_nets` → «Nettverk og abonnementer»;
- `prices.h_pay` «Slik betaler du, kort fortalt» → «Betaling, kort fortalt» (короче и без «du»).

Оставлено длиннее EN × 1,4 — короче по-норвежски нет: `map.legend` «Tegnforklaring», `pages.lang_label` «Norsk bokmål», `prices.th_plan` / `plan_sub` «Abonnement», `prices.pay_sub` «Abonnementer: {list}.». Если чип «Abonnement» не влезет на 390 px — в K8 переносить, не сокращать.

Падежи: в букмоле падежей нет, `{country_u}` / `{city_u}` подставляют «i …» / «på …» — сломанных конструкций не найдено.

## texts.json

- Удалён блок `sources_pages`: по уточнению README 23:55 `sources_pages.json` один на все языки и не переводится, а контракт L — `{"about_data", "download"}`. `check.py` поправлен под это.
- `about_data.notes[5]` — повелительное «bruk knappen…» заменено безличным пассивом («Feil kan meldes … med knappen «Meld fra om feil» … eller på e-post til {email}»).
- Остальное в about_data и download — без замечаний.

## Страны (150 просмотрены, 2 исправлено)

- `GI` «i Gibraltar» → «på Gibraltar», `TW` «i Taiwan» → «på Taiwan» — по употреблению Språkrådet / NRK.
- Названия CLDR и ручные правки L-NB (Hongkong, Macao, Myanmar, Palestina) верны. `IM` «Man / på Man» — официальная форма Språkrådet, оставлено (в речи чаще «Isle of Man» — спорное).

## Города (норвежские 34 + крупные города Европы и мира выборочно, 4 исправлено)

- «București» → «Bucuresti», «Tiranë» → «Tirana» — норвежские формы (Språkrådet, NRK).
- «İstanbul» → «Istanbul», «İzmir» → «Izmir» — в норвежском без турецкой İ.
- `decl_ok = 1` у всех верно: падежей нет. У исправленных в `note` — «R-NB: nb form».
- Проверены экзонимы: København, Göteborg, München, Köln, Wien, Praha, Warszawa, Lisboa, Napoli, Venezia, Torino, Antwerpen, Brussel, Haag, Athen, Moskva, St. Petersburg, Kyiv, Hongkong, Mexico by, Beograd — верно. Полная проверка 500 крупнейших по числу мест не делалась — на это не хватило времени пула.

## Слаги

`/nb/…` — естественные (kart, ladestasjoner, ladenettverk, ladepriser, om, kilder, metode; nettverk, om-dataene, nedlasting), ASCII. С `content/com/local/` (al ba hr me mk xk) и мировыми EN/SR/RU не пересекаются. Не менялись.

## Спорное

- `/nb/` или `/no/` — вопрос L-NB остаётся за Андреем.
- «du» в 5 заголовках («Hvor du kan lade elbilen…», «Bare hvis du ønsker svar») — оставлено: обобщённое «du» в норвежском нейтрально, безличный вариант звучит канцелярски.
- В `names/glossary.csv` всё ещё нет колонки `nb` — предложение L-NB в `NOTES.md` поддерживаю.

## Проверка

`python3 content/world/i18n/nb/check.py` → 0 ошибок. Обратный перевод изменённых строк — см. раздел ниже.

## Обратный перевод (отдельный агент, 23 изменённые строки и формы)

Агент перевёл nb → EN, не видя исходника. Смысл совпал во всех 23. По его замечаниям:
- `prices.h_profiles` → «Hva 100 km koster for tre typer bilister» (запятая звучала резко) — принято;
- `about_data.notes[5]` → «Feil og ønske om retting eller fjerning kan meldes med knappen … eller på e-post til {email}» (двойной пассив звучал тяжело; его вариант с «Du kan…» не взят — безличность) — принято частично;
- `prices.th_ratio` «DC mot hjemmelading» — не взято: заголовок колонки, лимит длины; рядом колонка «Hjemme», смысл ясен;
- `prices.lead_hub` «sammenlignet med» вместо «ved siden av» — не взято: EN «next to», формулировка верна.
- «på Gibraltar», «på Taiwan», «Bucuresti» — агент подтвердил.

---

# L2-NB — дельта ключей, обратный перевод (11.11.2026)

Ветка `l2-nb` от `dev` (`bb86f74`). Новые 274 ключа: map 29 (`ci_*`, `emb_open`), pay 93, press 54, b2b 33, embed 65; `texts.json` → `pay` (6 узлов) и `routes` (59 узлов).

## Обратный перевод 60 случайных новых строк

Отдельный агент, не видевший EN, перевёл nb → EN (`backtranslation_L2_60.json`, значения до правок). Смысл совпал во всех 60. Замечаний 10:

Исправлено (6):
- `pay.th_trip` «Turen, EUR» → «Kostnad for turen, EUR» — без «kostnad» неясно, что это цена.
- `b2b.lic_p` «dens del-på-samme-vilkår-krav» → «kravet om deling på samme vilkår» — калька.
- `press.th_change` «Endring DC» → «DC-endring».
- `map.ci_last_ne_radi` / `ci_last_zauzeto` «Siste melding: …» → «Sist rapportert: …».
- `pay.h_conn` «Kontakter og steder» → «Kontakttyper og ladesteder» — в заголовке без контекста «kontakter» читается как «контакты (люди)».
- `pay.th_gaps` «Hull > 150 km» → «Hull i dekningen > 150 km».

Оставлено (4):
- `map.ci_err` «Svaret ble ikke sendt» — это ответ на вопрос «Virker laderen?», не форма; «svaret» верно.
- `press.issue_note` «vekter fra det offentlige laget» — так же непрозрачно в EN; термин «det offentlige laget» уже принят на всём сайте.
- `pay.th_cover` — заголовок колонки, повторяет EN.
- `b2b.what_cov` «kontakter» — термин глоссария nb для connector, используется во всём интерфейсе карты; в перечне рядом с «effektklasser» однозначен.

## Видимые строки — правки носителя

- `shell.home_title` «i Europa og verden» → «i Europa og resten av verden» (как в `map.description`).
- `pages.below_title` «for lite data nå» → «foreløpig for lite data».
- `prices.pr_home` «Lader hjemme» → «Hjemmelader».

## FIXL 11.11.2026

Kontroll (tilbakeoversettelse nb → EN, bølge 1): 20 strenger fra `strings_home` (title, desc, h1, sub, search_none, near_err, map_alt, map_err, map_more, countries_p, ap_note, below_h, prices_p, p_ratio, p_src, pay_p, routes_p, work_p, trust_p, org_desc) + alle andre endrede strenger (`pay.nav_pay`, `embed.dv_p_lang`, `pages.p_hub_na`, `shell.lang_hint`, `shell.lang_hint_close`) + 3 bynavn.
Resultat: ingen meningsavvik. Bevisste forskjeller:
- `desc`: «what charging costs, how to pay and where to stop» → «priser, betaling og ladestopp på langtur» (lengde ≤ 165).
- `near_err`: «move it to your place» → «flytt det til riktig sted» (upersonlig).
- `org_desc`: «independent» → «nøytralt oppslagsverk».
- `sub` bruker generisk «du» som `shell.home_h1` (se NOTES).

D13: menypunktet `strings_pay.nav_pay` = «Betaling»; `kick_pay`, `t_/h1_pay_*`, `pay_more` og `strings_home.pay_h` beholder «Slik betaler du».
D12: ingen historiske/irredentistiske eksonymer funnet. Funnet og rettet en feil: tre amerikanske byer hadde fått greske eksonymer — 4180386 Athens (GA) og 4505542 Athens (OH) «Athen» → «Athens», 4683317 Corinth «Korint» → «Corinth».
cities.csv: + 46 svenske NOBIL-byer (lokale navn, «i X», decl_ok 1) + Genève (2660646). Kongsberg og Skien var der fra før og er kontrollert.
Åpne spørsmål: ingen nye.
