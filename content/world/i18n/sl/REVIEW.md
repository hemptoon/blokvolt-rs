# R-SL — вычитка словенского (sl), 10.11.2026

База `origin/l-sl` (e6f4e42), ветка `r-sl`. Редактор — отдельная сессия.

## Исправлено
- **Строки: 20 из 403** (map 8, shell 2, pages 3, prices 7):
  - согласование рода в отчёте об ошибке: `r_ne_radi` «Zaprt ali ne deluje», `r_nije_javni` «Ni javen» (polnilnik — м. р.);
  - склонение бренда: «O BlokVoltu» (`about_title`, `about_h1`);
  - длина кнопок/чипов ≤ EN × 1,4 там, где это возможно: `c_unnamed` «Polnilna postaja», `copied`, `no_prices`, `th_fees` «Drugi stroški», `pay_free` «brez mesečnine»;
  - естественность: `lead_hub` (убраны «za omrežja: {nets}, v državah: {countries}»), `p_city_cmp`, `t_near` «(v bližini: {x})», `net_top`, `moved`, `h_n_compare`, `out_stale` (запятая), `ch_nav_region` «Regija (v angleščini)», `ch_ft_claim` → «Kje napolniti…» как на главной;
  - кавычки: везде словенские »…« (`data_p` и 3 места в `texts.json`; были “…” и ASCII "…").
- **Страны: 150 проверены**, правок нет (CLDR-имена и «v/na» + местный падеж верны).
- **Города:** 5 городов Словении — верно. 500 первых `stage = month` (порядок файла: `places-2026-11-09.json` не содержит счётчиков мест): 117 уже были со склонением и верны; 152 добавлены (`decl_ok` 0 → 1): 142 по правилу для DE/NL/GB/BE/AT (одно слово на согласную → +u; NL на -o → -u; на -a → -i; имена на -e/-en/-el/-er оставлены «v kraju X» из-за беглого e), 10 вручную (Brest, Caen, Le Havre, Le Mans, Oviedo, Reims, Avignon, Oulu, Pori, Kuopio). Итого `decl_ok = 1`: 479 → 631.
- **Слаги:** естественные, ASCII; пересечений с `content/com/local/*` и EN/SR/RU нет (`/sl/` в .com не занят).

## Форма обращения
Предложения и ссылки-призывы — «vi» (Poiščite, Prenesite, Prijavite, Odprite). Короткие системные команды на кнопках — общепринятая форма словенского интерфейса на -i (Pošlji, Prekliči, Zapri, Deli, Ponastavi, Prikaži). Оставлено так сознательно.

## Проверка
- `check.py`: 0 ошибок, 3 известных предупреждения (`{city_u}`, как в SR/RU).
- Слепой обратный перевод 40 строк (20 изменённых строк + 20 падежных форм) отдельным агентом: 40/40 по смыслу. Замечание агента про «na Palestinskem ozemlju» учтено — оставлен строчный вариант L-SL.

## Спорное
- `p_hub_na` говорит, что словенские страницы покрывают Европу (допущение L-SL) — решает K8.
- Голландские города на -e/-en (Zwolle, Leiden, Enschede, Emmen) — «v kraju X»; носитель может заменить на «v Leidnu» и т. п.
- `th_ratio` «DC proti domu» — допустимо, но можно «DC : doma».

## L2-SL (11.11.2026) — обратный перевод 60 новых строк
Слепой обратный перевод отдельным агентом (выборка seed 1111 из 274 новых ключей + texts.pay). Смысл совпал в 60/60, «vi» везде, плейсхолдеры и теги целы.
Исправлено по замечаниям (8): `pay.th_trip` «Pot, EUR» → «Stroški poti, EUR»; `pay.stops_note` «v razdalji 150 km» → «do 150 km», «blizu skupaj»; `pay.sys_vignette` → «Časovna vinjeta za avtoceste.»; `map.ci_last_ne_radi`, `ci_last_zauzeto`, `ci_n30` — «prijava» (двусмысленно: вход/регистрация) → «poročilo»; `press.cite_2` «brez vprašanja» → «brez predhodnega dovoljenja»; `press.th_change` → «Sprememba cene DC»; `embed.dv_p_mreza` → «Oznaka (slug) omrežja». Попутно `shell.about_p` «umestitev» → «uvrstitev» (как в b2b).
Оставлено сознательно: «brez registracije» = ad hoc (glossary `adhoc_payment`); `ci_u_min` «minuto» — вин. падеж после подписи «Cena na»; `cov_no` «Ni navedena» — о državi (ж. р.); `issue_note` «preverjeni do {checked}» = EN «checked up to».

## Спорное (L2)
- `pay.conn_lnk` «Polnilne postaje — {name}» и `afir_eu` «{name} je članica EU»: {name} приходит в именительном, поэтому без падежа. Если движок даст `{cu}` — можно «Polnilne postaje v Nemčiji».
- `press.f_home` «od {lo_r}-kratnika … do {hi_r}-kratnika» — зависит от формата числа (2,1-kratnika — нормально).
- `press.d_issue`, `f_mom`: {month}/{prev} в именительном → «({month})», «z obdobjem {prev}».
- 48 новых городов NO/SE (NOBIL) — «v kraju X», decl_ok 0; их ещё нет в names/cities.csv, check.py допускает id из pages_state.
- Кавычки: в новых строках словенские »…« (apps_note), в старых texts — ASCII. Унифицировать при вычитке.

## FIXL 11.11.2026
Preverjeno: strings_home (71 ključev, nova datoteka), strings_shell `lang_hint`/`lang_hint_close`, D11 (`dv_p_lang`, `p_hub_na`), slugs (+7), cities.csv (48 NOBIL preverjenih + Ženeva), D12, D13 (narekovaji).
Povratni prevod (val 2, naslepo, nato primerjava z EN): 10 nizov home (title, desc, h1, sub, near_err, map_err, prices_p, work_p, trust_p, org_desc) + 4 spremenjeni (dv_p_lang, p_hub_na, lang_hint, lang_hint_close).
- Popravljeno: `work_p` »brez računa« je dvoumno (račun = tudi »bill«) → »brez uporabniškega računa«.
- `desc` brez »za vsako mesto« na koncu (dolžina 168) — smisel ostaja.
- `search_label` »mesto« = city; ob »polnilno mesto« možna dvoumnost, a v paru z »državo« jasno.
D13: narekovaji »…« — pregledani vsi JSON v sl/: ASCII "…" ali „…“ v besedilu ni več (razen HTML atributov). Nove vrstice brez narekovajev.
D12: »Valona« (italijansko ime) → »Vlora«, »v Vlori«. Ostali eksonimi so ustaljeni v slovenščini in nevtralni (Gradec, Celovec, Beljak, Trst, Videm, Bocen, Reka, Pulj, Pečuh, Sombotel, Šopron, Temišvar, Lvov) — ostanejo. Dvom: »Skadar« (Shkodër) — ustaljeno v slovenščini, ostavljeno; odločitev naročnika.
48 krajev NOBIL: imena = name_local, »v kraju X«, decl_ok=0 — pravilno; opomba posodobljena (zdaj so v names/cities.csv).
