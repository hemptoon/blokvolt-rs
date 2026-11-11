# R-HU — вычитка венгерского мирового слоя (10.11.2026)

База `origin/l-hu` (2fc8940), ветка `r-hu`. Перевод L-HU в целом хороший: форма обращения Ön выдержана везде, плейсхолдеры целы, плюралы `{one, other}` верны (в HU после числа — единственное число).

## Строки — 403 вычитано, 23 исправлено
- Безличность: «Hogyan számítódik / vonódnak össze / gyűlnek» (неестественный медиопассив) → номинальные заголовки: `conf_link`, `disc`, `about_more`, `method_desc`, `method_p`.
- Падежи и проценты: `p_net_share`, `p_multi` («{pct} részét» → «… aránya: {pct}»), `p_city_cmp` («{country_name} átlagában» → «az országos átlag ({country_name})»), `c_price_note` («Ár {d} szerint» → «Az ár dátuma: {d}»).
- Естественность: `acc_all`, `copied`, `acc_restricted_customers_staff`, `c_price` («Eseti ár»), `th_from` («Kezdőár»), `h_more` цен (было слабое «Továbbiak»).
- Длина кнопок/чипов (≤ EN×1,4): `filters_show`, `map_btn`, `more_map`, `t_unk`/`lg_unk` («Ismeretlen kW»), `lg_home` («Otthoni áram»), `out_excl` («indexen kívül»), `th_ratio` («DC/otthoni»).
- Однословные метки длиннее EN×1,4 оставлены (Térkép, Hozzáférés, Megosztás, Teljesítmény) — короче слов нет.

## Страны — 150 проверено, 2 исправлено
FJ → «a Fidzsi-szigeteken»; MF → «Saint Martinon» (единый вид с name).

## Города
- Все 32 города Венгрии — верно (Pécsett, Győrben, Egerben…), отмечены `rev: ok`.
- 500 первых `stage=month` по порядку файла (AT…DE/Hilden; файл мест — bbox, без счёта мест): 84 исправлено. Бельгия/Швейцария: безопасное «X városában» заменено на точную форму с дефисом после немой буквы (Tournai-ben, Montreux-ben, Verviers-ben, Wavre-ban), неверные авто-формы (Renensben → Renens-ben, Morgesben → Morges-ban, Říčanyben → Říčanyban); Ruse → Rusze/Ruszéban; Güstrow, Eltville, Blankenfelde-Mahlow. Остальные верные помечены `rev: ok`.
- `decl_ok=1`: 2305 → 2386. Названия с уточнением в скобках («Halle (Saale)») оставлены в безопасной форме.

## Слаги
Естественные, ASCII, с /hu/ местного раздела нет — пересечений нет.

## Спорное
- Венгерские исторические названия соседних стран (Pozsony, Kolozsvár, Újvidék) — решение Андрея из L-HU не принято, не трогал.
- Гармония гласных во французских названиях (Tournai, Namur) — средняя уверенность.

## Проверка
`check.py` — OK. Обратный перевод изменённых строк отдельным агентом: смысл совпадает, 2 его замечания приняты (`p_multi`, `h_more`).

## L2-HU — обратный перевод (11.11.2026)
60 случайных новых строк, независимый агент без доступа к EN: смысл совпал 60/60. Его стилистические замечания — 8; принято 6:
`b2b.lic_p` («készlet» → «adatkészlet», «soronkénti» → «rekordszintű»), `b2b.what_price` («nagy teljesítményű ár» → «HPC-ár»), `pay.th_gaps` («Hézagok» → «Töltő nélkül > 150 km»), `press.read_issue` (+«elolvasása»), `press.th_change` → «A DC-ár változása», `embed.dv_p_lang` («cím» двусмысленно: адрес/заголовок → «URL-je»).
Не приняты: `pay.checked` «Adatok: {date}» — так же, как `data_date` на карте; `embed.cf_more` «API-kérések» — в контексте ссылки однозначно.
