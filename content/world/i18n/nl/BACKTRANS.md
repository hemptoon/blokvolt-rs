# L-NL — обратный перевод 60 строк (seed 20261109)

Выборка: 60 листовых строк из strings_map/pages/shell/prices и texts.json (для плюралов форма `other`). 15 из 60 — непереводимые значения (URL, attribution, kind, имена полей CSV, названия лицензий), сверены как идентичные EN.

Итог: ok 58 · minor 1 · mismatch 1.

- strings_map.loading — «Laden…» — back-EN: "Charging…" / "Loading…" (двусмысленно на карте зарядок) — EN: "Loading…" — mismatch — исправлено в файле на «Bezig met laden…».
- strings_pages.home — «home» — back-EN: "home" — EN: "home" — minor — в NL-хлебных крошках принято «Home» с заглавной; оставлено как в EN (строчная, как в исходнике), решить при включении языка.

Без замечаний: обращение на «u», нет je/jij/we, нет обещаний (direct, 24/7), термины laadpaal/laadpunt/laadlocatie/btw последовательны.
