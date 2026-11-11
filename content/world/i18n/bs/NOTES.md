# L-BS — bosanski (bs), mirovoj sloj blokvolt.com

Ветка `l-bs` от `g3-prices` (cf44fc3). Все файлы — только в `content/world/i18n/bs/`. Язык не включён: включение — после ворот G8 (K8-i18n).

## Форма и стиль
- Босанский, латиница, **иекавица** (cijena, mjesto, gdje, provjereno, posljednji, sedmično, dio), лексика BiH: `hiljada`, `historija`, `tačka`, `sedmica`, `mapa` (не `karta`), `cjenovnik` (не `cjenik`), `spisak`, `pregledač/preglednik` → `preglednik`, `filteri`, `poticaji`.
- Обращение — вежливое `vi` (Pokušajte, Provjerite), BlokVolt безличен: без `mi`, `naš`, `redakcija`.
- Термины — колонка `bs` в `names/glossary.csv` и раздел `/ba/` (`content/com/local/ba/`): punjač, mjesto za punjenje, lokacija, konektori (в карточке, как EN Connectors), cijena bez ugovora (ad hoc), uz pretplatu (with a plan), s PDV-om, naknada po punjenju / za zauzeće.
- `s` / `sa`: по дому `/ba/` — `s` перед большинством слов, `sa` перед с-/з-/ш-/ж- и где легче читается.
- Плюралы: CLDR bs = `one`, `few`, `other` (Babel). `_in` — локатив ед. ч. для `one`, родительный после числа для `few`/`other`.

## Адреса (slugs.json) — допущение
Префикс языка **`/bs/`**, а не `/ba/`: `/ba/` уже занят страновым разделом «Bosna i Hercegovina» (gen_com LOCALES `ba`). Мировой слой на боснийском — это язык, а не страна. Если Андрей решит иначе — поменять только `slugs.json`.
`/bs/`, `/bs/mapa/`, `/bs/punjaci/` (+ `mreza`, `o-podacima`, `preuzimanje`), `/bs/mreze-punjaca/`, `/bs/cijene-punjenja/`, `/bs/o-stranici/`, `/bs/izvori/`, `/bs/metodologija/`.

## Страны (countries.csv, 150)
- `name` — CLDR `name_bs` из `names/countries.csv`, проверено глазами. Отступления (в `note`): NL **Holandija** (CLDR Nizozemska; в BiH обиходно Holandija), US **Sjedinjene Američke Države** (CLDR «Sjedinjene Države»), HK `Hong Kong`, MO `Makao` (без «SAR Kina»), PS `Palestina`.
- `in_phrase` — с падежом; острова и островные государства с `na` (na Kipru, na Malti, na Islandu, na Novom Zelandu, na Kosovu — как принято в BiH).
- Слаг — ASCII от боснийского названия (`njemacka`, `svicarska`, `holandija`, `sad`, `ujedinjeno-kraljevstvo`); свой для языка (P1).

## Города (cities.csv, все 5 605)
Порядок: города BiH (19) → stage month → balkan → quarter.
Правило имён (Pravopis bosanskog jezika: имена из латинских письменностей пишутся в оригинале, кроме устоявшихся адаптаций):
- латинская письменность — местное название (`New York City`, `Zürich`, `Lyon`, `Salzburg`), кроме белого списка;
- белый список устоявшихся экзонимов (86 строк): Beč, Pariz, Prag, Minhen, Keln, Brisel, Hag, Lisabon, Varšava, Krakov, Napulj, Venecija, Budimpešta, Bukurešt, Sofija, Atina, Solun, Moskva, Sankt Peterburg, Kopenhagen, Frankfurt na Majni/Odri, Nica, Singapur, Seul, Teheran, Taškent, Temišvar и т. п. — с падежом как в SR;
- кириллица, греческий, азиатские письменности (169) — транслитерация из `name_sr` (те же правила транскрипции), `note = transliteracija kao sr`;
- RS и ME — как в `name_sr` (латиница, местные формы).
- `in_phrase`: если имя совпадает с SR-формой — склонение из `sr_u` (`decl_ok` как `decl_ok_sr`), иначе безопасное «u gradu X», `decl_ok = 0`. Итог: `decl_ok=1` у 2 634 из 5 605.
- Округа Марселя: `Marseille (9. arondisman)`.

## Спорное / вопросы
1. Префикс `/bs/` vs `/ba/` (см. выше) — допущение `/bs/`.
2. `Minhen`/`Keln`/`Cirih`: в прессе BiH встречаются и адаптации, и оригинал. Взяты адаптации только для самых частых (Minhen, Keln); Zürich, Strasbourg, Lyon, Graz, Salzburg — в оригинале.
3. `p_hub_na` (pages): переведено как «stranice na bosanskom pokrivaju Evropu» — по аналогии с SR. Если K8 решит выдавать на bs и США/Канаду — поправить строку.
4. `pct` — `{x} %` с пробелом, как SR (так в боснийской норме).
5. `t_city` / `t_city_cc`: EN-плейсхолдер `{city}` не склоняется → «Punjači za električne automobile — {city}, {country}»; `d_city` — «u gradu {city}». Когда K8 начнёт подставлять `in_phrase` города — можно перейти на `{city_u}`-форму.
6. `m4` (prices): «gornja granica cijena Ofgem (price cap)» — английская глосса в скобках оставлена для ясности.
7. Склонение имён источников: «OpenStreetMapa», «BlokVolta» (texts) — нормально для боснийского; если нужно без склонения — заменить.

## Проверка
`python3 content/world/i18n/bs/check.py` — ключи EN, плейсхолдеры, HTML, пустые, категории плюралов против Babel, запрещённые слова (24/7, odmah, Evolako, mi/naš, кириллица), экавизмы/хорватизмы (предупреждения), слаги ASCII и префикс `/bs/`, CSV читаются и покрывают 150 стран / 5 605 городов.
Обратный перевод 60 случайных строк — см. раздел ниже.

## Обратный перевод (60 случайных строк, отдельный агент)
56 совпадают по смыслу, 4 — мелкие нюансы, ошибок смысла нет. Подробно — `BACKCHECK.md`.
Применено: `download.what_p` (team checks → «provjere BlokVolta»), `download.fields[access]` → «(javni, ograničeni i slično)», «zvaničn-» → «služben-» (норма BiH), «fajl» → «datoteka» везде.
Не применено: `prices.t_hub` «Evropski indeks cijena javnog punjenja» — оставлено (короче, смысл тот же).

## L2-bs (11.11.2026)
- +274 ключа: strings_map +29 (28 `ci_*` + `emb_open`), новые strings_pay 93, strings_press 54, strings_b2b 33, strings_embed 65. Плюралов `pl_*` в новых файлах нет.
- `texts.json`: разделы `pay` (6 узлов `afir.points[i]`) и `routes` (59 узлов `routes[i].stops[j].city`) — формат LANG0, путь через точку. Города маршрутов — из `cities.csv` этого языка (Budimpešta, Beograd, Sofija; Salzburg, Graz, Győr — в оригинале по правилу выше).
- «ad hoc» = «bez ugovora» (как в prices), в тексте AFIR — «bez registracije (ad hoc)»; «roaming» (как в `/ba/`), «autocesta» (как в `/ba/`), «dionica», «datoteka», «web-stranica», «e-mail».
- Числа с существительным — только в нейтральной форме «(mreža: {nets})», без «{n} cijena».
- Свои страны: BA — название, слаг `bosna-i-hercegovina`, 19 городов BiH с падежами проверены, все верны. Страниц городов BA в мировом слое нет (K3). 48 новых городов NOBIL (NO/SE) в `pages_state.json` ещё нет в `names/cities.csv` — для bs они не нужны (не свой рынок).
- `check.py` расширен на все 8 файлов и `texts.pay`/`texts.routes` (пути = многоязычные узлы pay.json/routes.json).
