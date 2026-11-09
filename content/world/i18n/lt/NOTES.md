# L-LT — lietuvių kalbos paketas pasaulio sluoksniui (pastabos)

Пул 4, 10.11.2026. База `g3-prices cf44fc3`, ветка `l-lt`. Язык впрок, в проде **не включён** (включение — после ворот G8).

## Форма и стиль

- Безлично или вежливое «jūs» (мн. ч.), без «mes / mūsų / redakcija». Кнопки — инфинитив («Atsisiųsti», «Atidaryti žemėlapį»), как в литовских интерфейсах.
- Запрещённое (24/7, «iš karto», «akimirksniu», Evolako) — нет, проверено скриптом.
- Числа для K8: десятичная запятая, тысячи — неразрывный пробел (`1 234,5`). Дата: `2026-11-10` (литовская норма ISO).

## Термины

įkrovimo stotelė (charging station) · įkroviklis (charger) · įkrovimo vieta (location) · įkrovimo tinklas (network) · operatorius · jungtis (connector) · galia · kaina už kWh · elektromobilis · žemėlapis · duomenys · šaltiniai · metodika. В `glossary.csv` колонки `lt` нет — термины выбраны по VLKK/уzusu литовских сайтов зарядки; при вычитке (R-LT) стоит сверить.

Спорное (из отчётов переводчиков):
- ad hoc → «be sutarties» (альтернатива «vienkartinė kaina»);
- plan → «planas», подписка (только где в EN subscription) → «prenumerata»;
- weighted → «svertinis»; ECB reference rate → «ECB orientacinis kursas»;
- breadcrumbs → «Naršymo kelias»; `lang_label` → «Lietuvių».

## Плюралы (CLDR lt: one, few, many, other)

- one — 1, 21, 31… (miestas); few — 2–9, 22–29… (miestai); many — дробные (miesto); other — 10–20, 30… (miestų).
- `_in`-варианты: one/few — местный падеж (mieste / miestuose, šalyje / šalyse), many/other — родительный.
- В литовском нет предлога «в»: местный падеж сам выражает «в». Поэтому `in_phrase` у стран и городов — одно слово без предлога («Vokietijoje», «Vilniuje»).

## Плейсхолдеры — сознательные отступления от EN (для K8)

- `t_city`, `t_city_cc` (pages), `h_more` (prices) — `{city_u}` / `{country_u}` вместо `{city}` / `{country}`; движок подставит `in_phrase`.
- `c_lead`, `src_ops` (prices), `data_from` (pages) — нейтральная конструкция «Tinklų: {n}», без согласования с числом.
- `p_gnet` — «{net} veikia {n_countries}»: `{n_countries}` должен строиться из `pl_country_in` (местный падеж).

## Страны (`countries.csv`)

- `name` — CLDR (Babel `lt`), проверено глазами; `in_phrase` — местный падеж; несклоняемые (Peru, Kongo…) помечены `indecl`.
- Слаг — ASCII из литовского названия без диакритики.

## Города (`cities.csv`)

- Все 5 605 строк. Порядок: 18 городов Литвы (местный падеж, `decl_ok=1`), затем `month`, `balkan`, `quarter`.
- ~186 городов с устоявшимся литовским экзонимом (Berlynas → Berlyne, Miunchenas → Miunchene, Varšuva → Varšuvoje…) — `decl_ok=1`, `note=exonym`.
- Остальные — оригинальное латинское название (литовская норма для иностранных имён в оригинальной форме), `in_phrase = «mieste X»`, `decl_ok=0`. Для нелатинских названий взято `name_en`, `note=translit_en` — для литовской практической транскрипции нужна вычитка.

## Адреса (`slugs.json`)

`/lt/`, `/lt/zemelapis/`, `/lt/ikrovimo-stoteles/`, `tinklas`, `apie-duomenis`, `atsisiusti`, `/lt/ikrovimo-tinklai/`, `/lt/ikrovimo-kainos/`, `/lt/apie/`, `/lt/saltiniai/`, `/lt/metodika/`. Пересечений с `content/com/local/` нет (там al ba hr me mk xk).

## Что осталось

- Вычитка носителем (R-LT): особенно `in_phrase` экзонимов и транскрипция нелатинских городов.
- Местный падеж для 5 401 города с `decl_ok=0` (сейчас безопасная «mieste X»).
