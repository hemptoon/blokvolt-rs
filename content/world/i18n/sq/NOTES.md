# SQ — албанский, заметки по локализации мирового слоя (L-SQ, 09.11.2026)

Язык впрок, в проде не включён (включение — после ворот G8).

## Форма обращения
- Вежливое «ju» (2-е лицо мн. ч.): «Kërkoni», «Hapni hartën», «Provoni përsëri», как в разделе /al/ (`content/com/local/al/`).
- Безлично: нет «ne» / «redaksia». Кнопки-действия в карточке ошибки — повелительное ед. ч., как в /al/: «Dërgo», «Anulo», «Mbyll».
- Норма — стандартный албанский (Албания + Косово). Формы городов — официальные неопределённые (Tiranë, Prishtinë, Shkodër), как в названиях общин.

## Термины (glossary.csv, колонка sq + /al/)
- charger / charging station → **karikues** (мн. karikues); «stacion» не используем.
- charging location → **vend karikimi** (мн. vende karikimi); charging point → **pikë karikimi**.
- connector → **prizë** (al). В Косово говорят «lidhës» — для раздела /xk/ можно переопределить.
- access → **aksesi** (al). Косово — «qasja».
- network → **rrjet**, operator → **operator**, VAT → **TVSH**, ECB → **BQE**.
- country → **vend** (как в glossary). Конфликт с «vend» = место: где сталкиваются, место пишется «vend publik karikimi» / «vendndodhje».
- ad hoc остаётся латиницей «ad hoc» (так в EN); в /al/ способ оплаты без регистрации — «Pa regjistrim».

## Формы после чисел
- CLDR sq: `one`, `other`. Все `pl_*` — объекты из двух форм. `_in`-варианты совпадают с обычными (после «në» + число албанский берёт ту же неопределённую форму: «në 3 qytete»).
- Строки с `{n}` без форм — конструкция «burime: {n}», «vende: {n}».

## Падежи и «në …»
- `{country_u}` / `fallback_u` в строках ожидают готовую фразу «në + страна» — её даёт `countries.csv:in_phrase` («në Gjermani», «në Mbretërinë e Bashkuar», «në Mal të Zi»). Мотор K8 должен подставлять `in_phrase`, а не склеивать «në» + `name`.
- Страны: `name` — CLDR (`name_sq`), три правки: US «SHBA» → «Shtetet e Bashkuara» (полное для заголовков), HK «RPA i Hong-Kongut» → «Hong Kong», MO «RPA i Makaos» → «Makao». Составные названия просклонены вручную (12 стран).
- Города: все 5 605. Порядок: AL/XK/MK → stage month → balkan → quarter.
  - 66 устоявшихся экзонимов (Vjenë, Romë, Mynih, Shkup, Ohër, Manastir, Ulqin, Tivar, Selanik, Janinë, Korfuz, Stamboll, Londër…).
  - Латинские названия — местные; кириллица/греческий/CJK — `name_en`.
  - Название на -a (Breda, Sevilla…) — безопасная форма «në qytetin X», `decl_ok = 0` (544 города). Остальные «në X», `decl_ok = 1`.

## Числа
- Числовые форматы в строках оставлены как в EN («2,500–4,999», «10 %»). По-албански принято «2 500» и «10%» — это задача формата чисел в реестре K8 (`langs.sq`), не строк.

## Что осталось / вопросы
- Проверить носителем 66 экзонимов и 544 города с `decl_ok = 0` (можно поднять до «në Bredë» и т. п.).
- Решить, нужен ли косовский вариант (lidhës, qasja) для /xk/ — в мировом слое один `sq`.
- Обратный перевод 60 строк — см. раздел ниже.

## Обратный перевод (60 случайных строк, вслепую)
Итог: 52 OK, 8 мелких, 0 расхождений по смыслу. Исправлено 5:
- `p_hub`: согласование «Faqe të veçanta»; «страна» здесь «shtet», чтобы не путать с «vend» (место);
- `n_places_none`: «Vendet e karikimit të rrjetit … këtij shteti» по той же причине;
- `report_map`: «gabim në të dhënat e një vendi karikimi» — ошибка в данных, а не поломка на месте;
- `acc_unknown`: «Akses i panjohur» (неопределённая форма, как «Rrjet i panjohur»);
- `texts.download.licence_p`: порядок слов «Mund t'i ndani të dhënat…».
Не исправлено, вопрос: «priza» (розетки) для connectors. Проверяющий предлагает «konektorë», потому что кабели DC (CCS, CHAdeMO) — не розетки. Оставлено «prizë», как в glossary.csv и в /al/. Если меняем, то во всём /al/ и в glossary сразу (3 строки здесь: `d_hub`, `r_snaga`, `d_network` + `c_conn`, `description`, texts).
Полный отчёт проверяющего: `~/dev/evdb/work/L-SQ/backtranslation_report.md`.
