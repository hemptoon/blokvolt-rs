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
