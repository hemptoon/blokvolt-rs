# LV — latviešu valoda (L-LV, пул 4, 10.11.2026)

## Форма обращения
Безлично или «jūs»-формы (Pārbaudiet, Lejupielādējiet). Без «mēs», «redakcija», «24/7», рейтингов сетей.

## Плюралы
CLDR lv: `zero`, `one`, `other`. `zero` у CLDR — это 0, 10–20, 30, 40… (n%10=0 или n%100 в 11–19). Для них в латышском именительный мн. ч. («10 uzlādes vietas»), поэтому `zero` = `other` во всех 11 ключах `pl_*`. Варианты `_in` — местный падеж («3 pilsētās», «1 valstī»).

## Падеж перед названием
- `{city_u}` / `{country_u}` = поле `in_phrase` (местный падеж без предлога: «Rīgā», «Vācijā», «Amerikas Savienotajās Valstīs»). Использованы в `d_city`, `t_city`, `t_city_cc` и в ценах.
- `fallback_u` = «pilsētā {x}» (как ru «в городе {x}»).
- `home_lead` в strings_map переформулирован со скобками: «Viena karte: {n} ({c}), no atvērtajiem datiem.», потому что `{c}` приходит в именительном.
- `p_city_cmp`: «šeit {city}, vidēji valstī ({country_name}) {country}» — без склонения названия страны.

## Термины
uzlādes stacija / vieta / punkts, uzlādes tīkls, operators, elektromobilis, ātrā uzlāde (DC), maiņstrāva (AC), tarifs, abonements, PVN, datu kopa, licence, atsauce. В glossary.csv колонки lv нет — термины выбраны по общему узусу, на вычитку R-LV.

## Слаги
`/lv/`, `/lv/karte/`, `/lv/uzlades-stacijas/`, `tikls`, `par-datiem`, `lejupielade`, `/lv/uzlades-tikli/`, `/lv/uzlades-cenas/`, `/lv/par-vietni/`, `/lv/avoti/`, `/lv/metodologija/`. ASCII без диакритики. Слаг страны — имя без диакритики (`vacija`, `amerikas-savienotas-valstis`).

## Страны
Имена — CLDR lv (Babel), кроме HK «Honkonga», MO «Makao», MM «Mjanma» (короткие формы). Спорно: AX «Olandes salas» (CLDR; встречается «Ālandu salas»), PS «Palestīnas teritorijas», SZ «Svatini». Несклоняемые (Peru, Monako, Fidži, Haiti, Sanmarīno, Puertoriko, Makao, Svatini) — `in_phrase` = имя.

## Города
- LV: Rīga/Rīgā, Cēsis/Cēsīs, Valmiera/Valmierā (в базе только 3 латвийских города).
- `stage=month`: 62 крупнейших — вручную (note `exonym`), остальные экзонимы по правилам латышской адаптации — агентами (note `exonym-auto`, `decl_ok=1`): это транслитерация по правилам, а не справочник — проверить в R-LV.
- Где не уверены — исходное имя и «pilsētā X», `decl_ok=0`. Греческие/кириллические имена в запасном варианте заменены английскими (note `latin-en`).
- Остальные стадии (quarter/balkan): агентами только известные города (298 с `decl_ok=1`), остальные — запасной вариант.
- Итог: 5 605 городов, `decl_ok=1` — 1 128 (3 LV + 57 вручную + 1 068 `exonym-auto`), `decl_ok=0` — 4 477. Небольшие города США/Канады с «большим» именем (Amsterdam NY, Cambridge, Springfield) местами получили латышскую форму — проверить в R-LV.
- Несклоняемые имена на -o/-u/-i (Oslo, Brno, Porto, Bordo): `in_phrase` = имя, `decl_ok=1`.

## Проверка
`python3 content/world/i18n/lv/check.py` — 0 ошибок (скрипт из l-pl; проверка `sources_pages` в texts убрана по уточнению 23:55). Обратный перевод 60 случайных строк: 58 совпало, 2 мелких (zero-форма плюралов → исправлено; «reitingoti» → «ranžēti»).

## Осталось
- Вычитка носителем (R-LV), особенно `exonym-auto` и `decl_ok=0`.
- Длина: `plan_sub` «Abonements» и `h_more` длиннее EN×1.4 (не кнопки).
- Разделитель тысяч: в латышском пробел («2 500»), в строках цен стоит как в EN.

## L2 (11.11.2026)
- Новые файлы: strings_pay, strings_press, strings_b2b, strings_embed (+29 ключей strings_map: `ci_*`, `emb_open`); texts.json: разделы `pay` (6) и `routes` (59, имена городов = cities.csv).
- Термины: roaming → «viesabonēšana» (lietotnes un kartes); check-in → «atzīme»; widget → «logrīks»; embed → «iegult»; toll → «nodeva»; vignette → «vinjete»; reliability → «ticamība» (везде, «uzticamība» убрана).
- Индекс: «Eiropas elektromobiļu uzlādes cenu indekss» (и в ценах, и в прессе, и в цитате).
- Даты: «uz {date}» («Dati uz…», «kursa uz…»). Кавычки: „…”.
- Числа в связке с существительным — через двоеточие («Uzlādes tīkli: {n}»), чтобы не ломалось на 21, 31…
- check.py: все 8 файлов + texts.pay/routes; стоп-слова lv (mēs, mūsu, redakcija, 24/7, nekavējoties, uzreiz).
- Вычитка R-уровня — REVIEW.md.
