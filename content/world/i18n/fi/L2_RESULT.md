# L2-fi — результат (11.11.2026)

Ветка `l2-fi` от `dev` (bb86f74). Файлы — только `content/world/i18n/fi/`. HOME2 в `dev` ещё нет → ключи главной HOME2 не переводились (добор — LANGI).

## Сделано
- **Ключи: 274 новых** — strings_map +29 (28 `ci_*` + `emb_open`), новые файлы strings_pay 93, strings_press 54, strings_b2b 33, strings_embed 65. Порядок ключей как в EN.
- **texts.json:** разделы `pay` (6 узлов `afir.points[i]`) и `routes` (59 узлов `routes[i].stops[j].city`; финские названия = местные латинские, Belgrade → Belgrad) в формате LANG0; добавлен источник `sources_pages.nobil` (появился в REL3, без него check падал).
- **Свои страны (FI):** название/слаг `Suomi`/`suomi`; все 80 городов FI в `cities.csv`, из них 62 со страницами (pages_state) — все есть, все `decl_ok = 1`, локативы проверены. Новых городов FI нет. 48 городов NOBIL (SE 46, NO 2) отсутствуют в `names/cities.csv` — это рынки sv/nb, для fi страниц не строится.
- **Видимые строки:** карта/оболочка/title уже вычитаны R-FI; поправлено `noscript` («Kartta vaatii JavaScriptin.») и `c_price` → «Kertahinta» (термин как в ценах).
- **check.py** — все 8 файлов + `texts.pay`/`texts.routes` (пути узлов, плейсхолдеры) → 0 ошибок.
- **Обратный перевод** 60 случайных новых строк отдельным агентом: 15 замечаний, 14 приняты (см. REVIEW.md).

## Решения/допущения
- `{cu}` (pay) и `{lo}`/`{hi}` в `f_range` (press) — локатив страны (`in_phrase`: «Saksassa»); `{name}`, `{lo}`/`{hi}` в `f_home` — номинатив. LANG0 должен подать `in_phrase` для fi в `cu()`/`Names.in_()` (сейчас там только en/sr/ru/de/fr).
- Сплошной текст безличный («kannattaa tarkistaa…»), кнопки — повелительное ед. ч., как в NOTES.md.
- Слаги новых разделов (pay, routes, press, b2b, developers) не добавлял: в реестре EN их нет, это зона LANG0.

## Проверка
`python3 content/world/i18n/fi/check.py`
