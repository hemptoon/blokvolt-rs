# R-SV — вычитка шведского (sv), 10.11.2026 00:15–00:50

База `origin/l-sv` `fcff204`, ветка `r-sv`. Язык не включён.

## Что проверено
- Все 403 строки (map 125, pages 120, shell 41, prices 117) — грамматика, естественность, термины, длина кнопок (EN × 1,4), безличный тон.
- `texts.json` (about_data, download) — целиком.
- 150 стран — `name` и `in_phrase`.
- Города: все 122 города SE/FI/AX; 500 первых `stage = month` по порядку файла (числа мест в `places-*.json` нет); плюс прогон по известным шведским экзонимам по всем 5 605.
- Слаги — ASCII, естественные, `/sv/` не пересекается с `content/com/local/` (там al ba hr me mk xk) и с EN/SR/RU.
- Запрещённые слова (vi/oss/ni, 24/7, Evolako, redaktion) — 0.

## Исправлено — 18 строк, 2 места в texts, 2 страны, 10 городов
Строки:
- `f_conf`, `c_conf`: «Datans tillförlitlighet» → «Tillförlitlighet» (было длиннее EN × 1,4; «datans» — разговорное).
- `how`: «Så beräknas tillförlitligheten» → «Så beräknas den» (длина, внутри карточки рядом со словом «Tillförlitlighet»).
- `copied`: «Länken har kopierats» → «Länk kopierad» (длина).
- `r_ok`: «rättelsen syns» → «en rättelse syns».
- `about`, `nav_about`, `ft_about_data`: «Om data» → «Om uppgifterna» (единый термин «uppgifter» для «data» в тексте); в `texts.download` две ссылки на страницу приведены к тому же названию.
- `h_more`, `no_name`: «i datan» → «i uppgifterna».
- `about_desc`: повтор «BlokVolt … BlokVolt» → «… hur man kontaktar tjänsten».
- `prices.t_net`: «{net} laddpriser {country_u}» (без дефиса — ошибка состава слова) → «Laddpriser för {net} {country_u}».
- `prices.serbia_note`: «blokvolt.rs prisindex» (неверный генитив) → «prisindexet på blokvolt.rs».
- `prices.more_local`: «Lokal sektion» → «Lokala sidor» (естественнее для ссылки на раздел из многих страниц).
- `prices.h_n_compare`: «…och med hemma» → «…och med hemmaladdning».
- `prices.h_c_index`: «Index {country_u}» → «Prisindex {country_u}».
- `shell.sources_p`: «attribution» (англицизм) → «källhänvisningar».
- `map.odbl_note`: «punktdatan är tillgänglig» → «punktdata är tillgängliga».

Страны: `PR` «i» → «på Puerto Rico», `TW` «i» → «på Taiwan» (островы, шведская норма).

Города: València → Valencia, New York City → New York, Rīga → Riga, İstanbul → Istanbul, Tiranë → Tirana, Prishtinë → Pristina, Fushë Kosovë → Fushë Kosova, Suharekë → Suhareka, Pejë → Peja, Podujevë → Podujeva (шведские СМИ пишут так).

Контракт:
- `texts.json`: убран `sources_pages` — по уточнению 23:55 он один на все языки и не переводится; `check.py` поправлен под контракт `{about_data, download}`.

## Не менял (проверено, верно)
- `in_phrase` городов — везде «i <город>», `decl_ok = 1`: в шведском названия мест не склоняются.
- Финляндия: официальные шведские имена двуязычных общин (Helsingfors, Esbo, Åbo, Vasa) и традиционные (Tammerfors, Uleåborg, Björneborg) — так рекомендует Språkrådet; малоизвестные — по-фински.
- `{net}-laddplatser`, `{net}-laddstationer` — дефис с названием бренда, шведская норма.
- «Teckenförklaring», «Abonnemang», «Startsida» длиннее EN × 1,4, но короче вариантов нет; это заголовки/ссылки, не чипы.
- Слаги без изменений.

## Проверка
- `python3 content/world/i18n/sv/check.py` — 0 ошибок.
- Обратный перевод: отдельный агент перевёл 40 строк (18 изменённых + 2 из texts + 20 случайных) обратно в EN, не видя оригинала — 39 совпали по смыслу, 1 мелкое (`more_local`: «страницы» vs «раздел», оставлено сознательно). Два его стилистических замечания приняты (`sources_p`, `odbl_note`).

## Спорное
- `plan_adhoc` «Ad hoc»: в Швеции говорят и «ad hoc-laddning», и «direktbetalning». Оставлено «Ad hoc» — совпадает с методикой индекса.
- «USA» вместо «Förenta staterna» — норма шведских СМИ, оставлено.
- `p_hub_na` говорит, какие страны есть на каких языках; при включении sv фразу нужно обновить (вопрос из L-SV остаётся).
- Города за пределами SE/FI/AX и первых 500 `month` проверены только по списку экзонимов.
