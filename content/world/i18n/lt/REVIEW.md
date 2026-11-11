# L2-LT — вычитка и обратный перевод (11.11.2026)

## Вычитка всего пакета (et/lt/lv не вычитывались — по образцу R-IT)
Строки: просмотрены все 403 старые строки, исправлено 6:
- `strings_map.c_price_note` «Kaina nuo {d}» (читалось как «цена от») → «Kaina {d} duomenimis».
- `strings_map.ch_ft_data` «OpenStreetMap bendraautoriai» → «autoriai» (как в литовском OSM).
- `strings_pages.p3` «DC iki 50 kW» → «DC mažiau nei 50 kW» (EN: under 50).
- `strings_pages.ft_checked` «duomenys nuo» (= «данные с») → «duomenų data».
- `strings_pages.st_n` «viešos vietos» → «viešosios vietos» (единообразно с остальными).
- `strings_prices.h_pay` «Kaip mokėti trumpai» → «Trumpai: kaip mokėti».

Страны: 150 проверены — правок нет (Samoa/Peru/Makao indecl, Kirgizija, Palestina — по CLDR lt).
Города: экзонимы и 95 `auto_lt` просмотрены — правдоподобны. 7 тёзок в США переведены как европейские города
(Athens ×2 → «Atėnai», Rome → «Roma», Venice ×2 → «Venecija», Naples → «Neapolis», Florence → «Florencija») —
возвращены оригинальные названия, «mieste X», `decl_ok=0`, `note=namesake_orig`. decl_ok=1 стало 292.
Своя страна LT: 18 городов, все 13 городских страниц из `pages_state.json` есть, формы верные.

## Новые 274 ключа + texts.pay (6) + texts.routes (59)
Обратный перевод — отдельный агент вслепую, 60 случайных новых строк (seed 60): 60/60 совпали по смыслу.
Принято 8 стилистических замечаний: `texts.pay.afir.points[4–5]` «stotelė» → «įkrovimo stotelė» (иначе — автобусная остановка),
`th_apps_c`, `th_dc`, `nets_note`, `season`, `dv_p_grad`, `cite_3`, `ch_europe_d`.
Не принято: «viešasis sluoksnis» — термин всего пакета; тире в `h1_route` (— как в EN).

## Решения
- ad hoc → «be sutarties»; roaming → «tarptinklinės programėlės ir kortelės»; widget → «valdiklis».
- `f_home` — нейтральная конструкция «kainų santykis: nuo {lo_r} ({lo}) iki {hi_r} ({hi})» (без согласования «karto/kartų»).
- `f_mom` — «Palyginti su ankstesniu leidiniu ({prev})» — месяц в именительном, без склонения.
- `conn_lnk`, `conn_txt`, `afir_*` — `{name}` в именительном, без падежа.
- Города маршрутов: экзонимы только устоявшиеся (Zalcburgas, Liubliana, Zagrebas, Budapeštas, Belgradas, Sofija, Plovdivas, Gracas, Ochridas), остальные — оригинал, как в cities.csv.

## Для движка (LANG0)
- `f_range` ждёт `names.in_` (местный падеж: «Lietuvoje») — как сейчас в world_press.py.
- `p_net_share` «veikia {n_cities} {country_u}» — при n ≥ 10 даёт «12 miestų» (род. п.), это норма; проверить вживую.

## FIXL 11.11.2026
Проверено: новый `strings_home.json` (71 ключ), `lang_hint`/`lang_hint_close`, D11 (`dv_p_lang`, `p_hub_na`), 7 слагов, 49 городов (48 NOBIL + Женева).
Обратный перевод (волна 2, вслепую): 10 строк home (title, h1, sub, data_as_of, search_none, near_err, prices_p, p_ratio, work_p, routes_p) + 3 изменённых (dv_p_lang, p_hub_na, lang_hint) — по смыслу совпадают, правок нет.
- `data_as_of` = «duomenų data: {date}» (а не «duomenys {date}») — так дата не требует падежа.
- `p_ratio` = «{x}× brangiau nei namuose» — знак «×» вместо «kartus/karto», чтобы не согласовывать с дробным числом.
- `tab_ap` «Azija ir Okeanija» — короче «Azijos ir Ramiojo vandenyno regionas» для вкладки; смысл тот же набор стран.
- `trust_p`: «mokamų įrašų» вместо «mokamų vietų» (в about_p «mokamų vietų» двусмысленно — «платные места [зарядки]»; при вычитке R-LT стоит поправить и shell.about_p).
D13 (lt): имена основателей без литовских окончаний — проверено, в about_p уже «Andrei ir Danila».
D12: чужие города проверены — исторических/ирредентистских экзонимов нет; Balstogė (Białystok), Krokuva, Varšuva — нормативные литовские формы (VLKK), оставлены.
Города NOBIL: шведская/норвежская форма, «mieste X», decl_ok=0 (как у остальных шведских городов файла); Женева = «Ženeva / Ženevoje», decl_ok=1.
