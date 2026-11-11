# nb — норвежский букмол, мировой слой (L-NB, пул 3, 09.11.2026)

Язык впрок, в проде не включён (включение — после ворот G8, через реестр K8-i18n).

## Что лежит

| Файл | Что | Объём |
|---|---|---|
| `strings_map.json` | карта | 125 ключей |
| `strings_pages.json` | страницы мира | 120 ключей, 9 плюралов |
| `strings_shell.json` | оболочка | 41 ключ, 2 плюрала |
| `strings_prices.json` | цены | 117 ключей |
| `texts.json` | about_data, download, sources_pages | структура 1:1 с EN |
| `slugs.json` | адреса | 11 ключей, префикс `/nb/` |
| `countries.csv` | страны | 150 из 150 |
| `cities.csv` | города | 5 605 из 5 605 |
| `check.py` | проверка | `python3 content/world/i18n/nb/check.py` → 0 ошибок |

## Форма обращения

Современный букмол обращается на «du»; «De» устарело и звучит странно, поэтому вежливой формы как в DE/FR здесь нет. По правилу BlokVolt тексты безличные: инфинитив, пассив (`kan meldes`, `skal oppgis`), «det/man»-конструкции. «du» оставлено только там, где без него фраза неестественна:
- `strings_shell.home_desc`, `home_h1`, `ch_ft_claim`, `strings_pages.ft_claim` — «Hvor du kan lade elbilen» (обобщённое «ты», стандартно для норвежских заголовков);
- `strings_map.r_email_hint` — «Bare hvis du ønsker svar»;
- `strings_prices.h_pay` — «Slik betaler du»;
- `texts.about_data.notes` — одно повелительное «bruk knappen…».

«vi», «vår», «redaksjonen», «24/7», «umiddelbart», Evolako — нет (проверяет `check.py`).

## Термины (glossary.csv колонки nb нет — выбраны здесь)

- charging station / charger — **ladestasjon** (в живой речи — **lader**: «Laderen finnes ikke», «ved laderen»)
- charging location — **ladested** / ladesteder; charging point — **ladepunkt** / ladepunkter
- network — **nettverk** (в цене и описаниях — **ladenettverk**); operator — **operatør**
- connector — **kontakt**; power — **effekt**; fast/DC charger — **hurtiglader**; HPC — оставлено «HPC»
- reliability — **pålitelighet** (в карточке — datapålitelighet)
- ad-hoc price — **ad hoc-pris** (с объяснением «uten avtale»); subscription/plan — **abonnement**
- VAT — **mva.**; home electricity — **strømpris for husholdninger**
- Report an error — **Meld fra om feil** (кнопка карты; ссылки в about_data и pages сверены)
- Methodology — **Metode**; Legend — **Tegnforklaring**; Directions — **Veibeskrivelse**; breadcrumbs (aria) — **Navigasjonssti**
- `lang_label` — «Norsk bokmål»

Предложение: добавить колонку `nb` в `names/glossary.csv` этими значениями при сведении.

## Адреса (`slugs.json`)

`/nb/`, `/nb/kart/`, `/nb/ladestasjoner/`, `nettverk`, `om-dataene`, `nedlasting`, `/nb/ladenettverk/`, `/nb/ladepriser/`, `/nb/om/`, `/nb/kilder/`, `/nb/metode/`.
Транслит в слагах: æ→ae, ø→o, å→a (так делает большинство норвежских сайтов; `oe`/`aa` — тоже допустимо).

**Вопрос Андрею:** префикс `/nb/` или `/no/`. Взял `/nb/` по правилу README «`/<код>/`»; hreflang в реестре K8 лучше ставить `nb` (Google понимает и `no`). Если нужен `/no/` — меняются только пути в `slugs.json`.

## Страны

- Имена — Babel/CLDR `nb` (колонки `name_nb` в `names/countries.csv` нет). Вручную: HK «Hongkong», MO «Macao» (CLDR даёт «… SAR Kina»), MM «Myanmar» (CLDR «Myanmar (Burma)»), PS «Palestina» (CLDR «Det palestinske området»). IM — CLDR «Man» (официальное норвежское; в речи чаще «Isle of Man» — оставил CLDR).
- `in_phrase`: «i …», для островов — «på …» (по норме Språkrådet): Island, Kypros, Malta, Cuba, Jamaica, Sri Lanka, Filippinene, Færøyene, Åland, Svalbard og Jan Mayen, Réunion, Mauritius, Fiji и др. — 28 стран. Падежей в nb нет, так что форма всегда точная.

## Города

- Все 5 605 (норвежские 34 первыми, потом month, balkan, quarter). `decl_ok = 1` у всех: в букмоле нет падежей, «i X» всегда правильно.
- Латинские местные названия оставлены как есть — так пишет норвежская пресса (München, Köln, Wien, Praha, Milano, Warszawa, Göteborg, Lisboa).
- Экзонимы nb (28): Brussel, Haag, Athen, Korint, Korfu, Rhodos, Pireus, Moskva, St. Petersburg, Rostov ved Don, Valencia (вместо València), Ibiza (Eivissa), Mahón, San Sebastián, Riga, Baku, Tasjkent, Samarkand, Panama by, Mexico by, Hongkong, Kyiv, Kharkiv, Lviv, St. Pölten.
- Россия (14): норвежская транслитерация с кириллицы (Jekaterinburg, Rjazan, Nizjnij Novgorod, Tjumen, Sjusjary).
- Прочая нелатиница (157: Греция, Болгария, С. Македония, Беларусь, Азия) — из `name_en`; для БГ/МК это совпадает с их официальной латиницей.
- Marseille 03–16 → «Marseille, 9. arrondissement».
- Колонка `note` говорит, откуда имя: пусто = местное, `exonym nb`, `translit nb`, `from name_en`, `arrondissement`.

## Обратный перевод

Отдельный агент, не видевший EN, перевёл 60 случайных строк nb → EN (`backtranslation_60.json`: EN, проверенный nb, обратный EN, замечание). Смысл совпал во всех 60. Замечания у 17:
- 6 — «{country_u} должен нести предлог»: так и задумано, `in_phrase` = «i Norge» / «på Island». Не ошибка.
- исправлено 8: `prices.n_places_none` (выходило «у мест сети нет имени сети» — переписано), `prices.noprice_p` (сломанная параллель глаголов), `prices.n_station_page` («fra {net}» → «Alle {net}-ladestasjoner»), `prices.th_ratio` («kontra»), `prices.more_local` («Lokal side» вместо англицизма), `map.src_com` («Fellesskapsdata»), `map.ch_report` (единое «Meld fra om feil»), `pages.report_map` («på kartet»), плюс `shell.method_p` (ясный перечень факторов).
- оставлено 3 (телеграфный стиль совпадает с EN): `prices.europe_label`, `prices.cars_note`, `prices.m1`.
В файле — значения на момент проверки, до правок.

## Что осталось / для K8

- `pct` оставлен «{x}%» как в EN; по норвежской норме «{x} %». Формат чисел для nb в реестре K8: десятичная запятая, пробел (неразрывный) как разделитель тысяч, `{x} %`.
- Даты: месяцы в `strings_prices` — строчными (januar … desember) там, где они есть; формат даты в реестре — `9. november 2026`.
- Глоссарий: колонка `nb`.

## L2 (11.11.2026)

- Новые файлы: `strings_pay` 93, `strings_press` 54, `strings_b2b` 33, `strings_embed` 65; `strings_map` +29 (`ci_*` чек-ин, `emb_open`).
- `texts.json` → `pay` (AFIR, 6 пунктов) и `routes` (59 названий городов в остановках) в формате LANG0: путь узла → текст. Города — из `cities.csv` nb (Belgrade → Beograd, остальные местной латиницей).
- Термины новых разделов: How to pay — «Slik betaler du» (обобщённое «du», как в заголовках главной); Routes — «Ruter»; roaming app/card — «roamingapp / ladekort»; coverage — «dekning»; tolls — «bompenger», vignette — «vignett»; check-in — «melding / Sist rapportert»; price index — «prisindeks for elbillading»; widget — «widget»; preview — «forhåndsvisning»; credit (citation) — «kildehenvisning».
- Города своих стран (NO): 31 страница в `pages_state.json`; добавлены Kongsberg (3149563) и Skien (3139075) — их нет в `names/cities.csv`, `check.py` принимает geonameid из `pages_state.json` для `MARKET = {'NO'}`.
- `check.py`: все 8 файлов `strings_*`, разделы `texts.pay` / `texts.routes` против многоязычных узлов `pay.json` / `routes.json`, проверка, что у каждой городской страницы NO есть имя.

## FIXL (11.11.2026)
- `strings_home.json` ny (71 nøkler); `strings_shell` + `lang_hint` «Denne siden finnes også på norsk», `lang_hint_close` «Lukk». «du» også i `strings_home.sub` og `pay_h` (samme regel som overskriftene).
- D13: `nav_pay` = «Betaling» (meny); overskrifter/kicker «Slik betaler du».
- Slugs: `/nb/betaling/`, `/nb/ruter/`, `/nb/for-media/`, `/nb/data-for-bedrifter/`, `/nb/embed/kart/`, `/nb/kart-til-nettsiden/`, `/nb/for-utviklere/`.
- cities.csv: alle 5 654 rader i names/cities.csv; check.py krever nå at hver geonameid finnes der og at alle bysider i pages_state (alle land, ikke bare NO) har navn.
- countries.csv: ingen `name_nom` (nb har ikke D14).
- FIXL2: +821 cities from names/cities_extra.csv (own market 3). Kyrillisk: UA norsk translitterasjon (Zjytomyr, Tsjernivtsi, Zaporizjzja), RU/BY som filen (russisk form: Gomel, Mogiljov, Tsjeljabinsk), BG engelsk form som før; GR uten aksenter; RO med ș/ț; Roma, Firenze, Genova. check.py godtar names/cities_extra.csv.
