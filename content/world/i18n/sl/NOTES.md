# sl — slovenščina, мировой слой BlokVolt (L-SL, 09.11.2026)

Язык впрок, в проде не включён (включение — после ворот G8, движок K8).

## Форма обращения
- Вежливое «vi» (vikanje): «Poiščite», «Odprite zemljevid», «Prenesite podatke».
- Безлично о сайте: нет «mi», «naš», «uredništvo», «ekipa».
- Короткие UI-кнопки — повелительное вежливое или отглагольное существительное («Prenos», «Filtri»).

## Плюралы (CLDR sl: one / two / few / other)
- Форма — именительный падеж после числа: 1 lokacija, 2 lokaciji, 3 lokacije, 5 lokacij.
- `pl_city_in`, `pl_country_in` — местный падеж (после «v»): v 1 mestu, v 2/3/5 mestih; v 1 državi, v 2/3/5 državah.
- `strings_shell.pl_cc` используется только в `home_lead` («{n} v {c}») — поэтому записан в местном падеже (državi/državah). Если K8 начнёт использовать `pl_cc` где-то ещё — нужен отдельный ключ.
- Строки с количеством из `pn()` (p_shown, p_dc, p_nonet, p_ac, fast_more) построены через двоеточие, чтобы число с существительным стояло в именительном.
- Строки с `{n}` без существительного — нейтрально: «viri: {n}», «(število virov: {n})».

## Плейсхолдеры, отличные от EN (как в SR/RU)
- `strings_pages.d_city`, `t_city`, `t_city_cc` — `{city_u}` вместо `{city}` (в словенском город после «v» склоняется). `t_city` без `{country}`, как SR. check.py помечает это как предупреждение.
- Нужна ветка `sl` в `country_u` / `city_u` движка (K8): брать `in_phrase` из `i18n/sl/countries.csv` и `cities.csv`; при `decl_ok = 0` — `in_phrase` уже безопасный («v kraju X»).

## Термины (glossary, колонка sl)
- polnilna postaja / polnilnik / polnilno mesto / lokacija; omrežje; zemljevid; priključek; Tip 2; moč; DDV.
- Session fee → «pristojbina za polnjenje», «/polnjenje» (по glossary; переводчик сначала дал «za sejo» — исправлено).
- Idle fee → «pristojbina za zasedenost».
- h1 карты «Zemljevid polnilnic» (glossary charger_map). «Polnilnica» разговорнее; альтернатива — «Zemljevid polnilnih postaj». Решение носителя.
- Тариф с абонплатой → «z naročnino», колонка таблицы `th_plan` → «Tarifa».
- glossary `download_data` = «Prenesi podatke» (форма на «ti») — в строках использовано вежливое «Prenesite podatke». Glossary стоит поправить.
- «attribution» → «navedba avtorstva»; «Freshness» → «Ažurnost»/«svežost».
- Кавычки оставлены ASCII "…", как в EN (словенская норма — »…«).

## Названия
- countries.csv: имена из CLDR (`name_sl`), сокращены HK «Hongkong», MO «Macao», MM «Mjanmar» (в CLDR длинная форма). in_phrase — «v»/«na» по норме: na Hrvaškem, na Nizozemskem, na Japonskem, na Kitajskem, na Islandiji, na Kosovu, na Dunaju (город).
- Слаги стран — ASCII от словенского имени (nemcija, nizozemska, zdruzeno-kraljestvo).
- cities.csv: все 5 605 городов. 297 — с проверенным экзонимом/падежом (`decl_ok = 1`: Dunaj, Gradec, Celovec, Beljak, Trst, Videm, Benetke, Pariz, Bruselj, Varšava, Budimpešta, Reka, Novi Sad → v Novem Sadu и т. д.). Остальные — местное латинское название, кириллица — словенская транслитерация (47), греческое/иное письмо — `name_en` (114), `in_phrase = "v kraju X"`, `decl_ok = 0`.
- Греческие города без экзонима (Ioannina, Chania…) идут по `name_en` — словенская норма передаёт их по-гречески (Hanja и т. п.); на проверку носителю.

## Что осталось
- Вычитка носителем (главное — заголовки, `p_*` страницы стран, цены).
- Расширить `decl_ok = 1` для крупных городов DE/FR/NL/ES/US (сейчас только ~300).
- `p_hub_na`: предполагается, что словенские страницы покрывают Европу (как SR). Если K8 решит иначе — поправить строку.
- Обратный перевод 60 строк — см. раздел ниже.
