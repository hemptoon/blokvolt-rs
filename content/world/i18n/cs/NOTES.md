# L-CS — čeština (cs), poznámky

Ветка `l-cs` от `g3-prices cf44fc3`, 09.11.2026. Язык впрок, в проде не включать (ворота G8).

## Обращение
Безличные конструкции везде, где можно («je vhodné ověřit», «Data je možné…»). Где нужен императив — вежливая форма на vy: «Zkuste to později», «Vyberte, co je špatně», «Přetáhněte značku». Без «my»/«redakce», без «24/7», без «okamžitě».

## Плюралы
CLDR cs: `one` (1), `few` (2–4), `many` (дробные: 1,5 → род. п. ед. ч.), `other` (0, 5+). Babel даёт tags {one, few, many}, `other` неявный — в файлах все четыре.
- `pl_*` (без `_in`) — именительный: místo / místa / místa(many → «místa», для pl_loc «nabíjecího místa») / míst.
- `pl_city_in`, `pl_country_in` — **винительный**, не местный: шаблоны переписаны на глагол «pokrývá» («Síť v Německu pokrývá 12 měst», «Síť X pokrývá 5 zemí»). Причина: локатив после «v» + число требует выбора v/ve по произношению числа (ve 2, ve 3, ve 4, ve 7, v 5…) — генератор этого не умеет.
- Строки с `{n}` без форм: «zdroje: {n}», «(počet: {n})».

## Названия и падежи
- `{country_u}` = `in_phrase` из `countries.csv` (v/ve/na + lokál, все 150 вручную, запасной «v zemi X» не понадобился). CZ = «Česko», слаг `cesko`.
- Города: в заголовках `{city}` стоит в именительном («Nabíjecí stanice pro elektromobily – Praha, Česko»), потому что плейсхолдеры как в EN.
- `fallback_u` = «ve městě {x}» — безопасная форма для городов с `decl_ok=0`.
- `cities.csv`: 5 605 из 5 605; `decl_ok=1` у 218 (все 63 города Чехии + ~155 экзонимов: Mnichov, Vídeň, Drážďany, Řezno, Cáchy, Linec, Lutych, Vratislav, Bělehrad…). Несклоняемые на практике (Marseille, Nice, Malmö, Los Angeles…) — «ve městě X».

## Спорные термины
- site/location → «místo» (не «lokalita»); charging point → «nabíjecí bod»; charger → «nabíječka»; fast charger → «rychlonabíječka»; session → «relace»; idle fee → «poplatek za blokování»; VAT → «DPH».
- Plan ad hoc оставлен «Ad hoc» (альтернатива «Jednorázově»).
- Атрибуция OSM в тексте — «© přispěvatelé OpenStreetMap» (официальная чешская формулировка OSM). Если нужна дословная EN — вернуть в `texts.json`.
- «Brunšvik» (Braunschweig) — исторический экзоним, в живом чешском чаще Braunschweig. Проверить.
- Районы, записанные городами в исходнике (Brooklyn, Manhattan, Earlsfield) — «ve městě X», по смыслу неточно; правится в `names/cities.csv`, не здесь.
- Глянуть локатив: SJ «na Špicberkách», TO «na Tonze», WS «na Samoi», CZ «v Hranicích».
- `st_*` (подписи под числами) стоят в род. мн. («veřejných míst») — верно для 5+, для 2–4 звучит неидеально; цифры на этих плашках всегда большие.

## Обратный перевод (60 случайных строк, слепой агент)
Смысл сохранён во всех 60. Флагов 9, исправлено 8: `h_more`, `net_none`, `lead_hub`, `ch_nav_region`, `sources_note`, `method_desc`, `no_prices_n`, `r_ne_postoji`. `p_dc` оставлен (агент не видел, что в `{dc}` уже стоит «N míst»).

## Что осталось
- Прогон с мотором K8 (`langs_enabled` + `cs`), посмотреть живые заголовки с `{country_u}`.
- Носитель языка — пробежать карту и цены глазами.
