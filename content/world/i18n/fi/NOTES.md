# L-FI — suomi (finnish) — заметки переводчика

Ветка `l-fi` от `g3-prices` (cf44fc3). Язык впрок, в прод не включён (включение — после ворот G8, через K8-i18n).

## Форма обращения
- Сплошной текст — безличный: пассив и безличные конструкции («Tiedot kootaan…», «Virheestä voi ilmoittaa…», «Tarkista hinta…» только в кнопках/коротких советах). Без «me/meidän/toimitus», без «heti», без «24/7».
- Кнопки и короткие подписи — повелительное наклонение ед. ч. («Lataa», «Avaa kartta», «Hae maata…»): это стандарт финских интерфейсов и не читается как фамильярное «ты». Формы на «te» (Lataakaa) в финских UI выглядят устаревше, поэтому не использованы.
- Глоссария для `fi` в `names/glossary.csv` нет — термины выбраны по финской практике: latausasema (charging station), latauspiste (charging point), latauspaikka (charging location / place), laturi (charger), latausverkko (network), operaattori, liitin, teho, kertahinta (ad hoc), sopimus (plan), suurteholataus/HPC, avoin data, lisenssi, lähde, tietojen luotettavuus (data reliability).

## Падежи и плейсхолдеры
- `{country_u}` = инессив/адессив из `countries.csv` (`Saksassa`, `Venäjällä`, `Maltalla`, `Filippiineillä`). Островные территории и Россия/Беларусь — адессив, по финской норме.
- `fallback_u` = `kaupungissa {x}` («в городе X») — безопасная конструкция для городов с `decl_ok = 0`.
- Формы после чисел — CLDR fi: только `one` / `other` (Babel 2.18). После числа финский ставит партитив ед. ч.: `5 latauspaikkaa`. Для `_in`-ключей (`pl_city_in`, `pl_country_in`) и `pl_cc` — инессив, одинаковый в обеих категориях: `12 kaupungissa`, `150 maassa`.
- Названия сетей `{net}` не склоняются: везде конструкция с тире или двоеточием (`{net} – latausasemat Saksassa`, `{net}: kaikki laturit …`), чтобы не делать «Tesla Supercharger-laturit» / генитив от бренда с пробелом.
- `{city}` в заголовках — тоже без склонения (`Sähköautojen latausasemat – Tampere, Suomi`). Склоняемая форма города (`city_u`) сейчас в шаблонах EN не используется; она лежит в `cities.csv` для K8.
- `p_city_cmp`: «maassa {country_name} keskimäärin {country}» — имя страны в номинативе после «maassa» (аппозиция); допустимо, но если K8 даст `{country_u}` в этот ключ, лучше «…, {country_u} keskimäärin …».

## Слаги
`/fi/`, `/fi/kartta/`, `/fi/latausasemat/`, сеть `verkko`, `tietoa-datasta`, `lataa-data`, `/fi/latausverkot/`, `/fi/lataushinnat/`, `/fi/tietoa/`, `/fi/lahteet/`, `/fi/menetelmat/`. ä→a, ö→o (финская практика URL). `download` = `lataa-data`, а не `lataus`: «lataus» по-фински одновременно «зарядка» и «загрузка», на сайте про зарядку это путает.
Слаги стран — ASCII от финского названия (`saksa`, `alankomaat`, `tsekki`, `itavalta`).

## Названия
- Страны — CLDR fi через Babel (колонки `name_fi` в `names/countries.csv` нет). Сокращены: HK «Hongkong» (CLDR: «Hongkong – Kiinan erityishallintoalue»), MO «Macao», MM «Myanmar» (CLDR «Myanmar (Burma)»), PS «Palestiinalaisalueet» (CLDR ед. ч. «Palestiinalaisalue»). GB = «Iso-Britannia» (как в CLDR fi).
- Города Финляндии (80) — вручную, финские имена для шведскоязычных форм GeoNames: Raseborg → Raasepori, Korsholm → Mustasaari, Jakobstad → Pietarsaari, Pargas → Parainen. Местные финские локативы с адессивом: Tampereella, Vantaalla, Rovaniemellä, Seinäjoella, Lohjalla, Kirkkonummella, Hyvinkäällä, Riihimäellä, Nokialla, Paraisilla, Haukiputaalla и др.
- Экзонимы (~135 строк): Berliini, Hampuri, Lontoo, Pariisi, Rooma, Napoli, Firenze, Venetsia, Lissabon, Praha, Varsova, Krakova, Kööpenhamina, Tukholma, Bryssel, Haag, Ateena, Bukarest, Geneve, Tallinna, Tartto, Riika, Vilna, Moskova, Pietari, Kiova, Lyypekki, Haaparanta, Nizza…
- Остальные города — локальное латинское имя (`name_local`, иначе `name_en`) + правило инессива: после гласной `-ssa/-ssä`, после согласной `-issa/-issä`, гармония гласных по последней не-нейтральной гласной (e/i нейтральны). `decl_ok = 1`.
- `decl_ok = 0` + «kaupungissa X» там, где правило ненадёжно: названия из нескольких слов/с дефисом; вся Франция (немые буквы); немая -e в англоязычных и франкоязычных странах; немые конечные согласные в BE/CH/LU/MC; греческие -os/-as/-is/-es (по-фински -okse-); Прибалтика (финские формы с чередованием: Tartossa, Riiassa); нелатинские имена.
- Спорное: гармония для немецких имён на -en после задней гласной (`Oscherslebenissa`/`-issä`) — в финской практике встречаются оба варианта; правило берёт заднюю.

## Проверка
`python3 content/world/i18n/fi/check.py` (из корня репо) — ключи EN, плейсхолдеры и теги, пустые значения, категории плюралов = CLDR, слаги, CSV, структура texts.json. Результат: 0 ошибок.

## Результаты независимой проверки (09.11.2026, 23:55–00:05)
**Обратный перевод** 60 случайных строк (строки + texts.json) отдельным агентом, без доступа к EN: смысловых расхождений 0; «мы», «heti», фамильярного тона — 0. 12 стилистических замечаний, принято 7:
- `table_note` переписан (причина медианы через «koska», «— = ei indeksiä, koska…»);
- `fx_note`, `chart_eur`: дата в скобках («EKP:n viitekurssilla ({date})»);
- `per_100` → «/100 km», `th_ratio` → «DC / koti», `europe_label` → «hintansa julkaisseiden…», `h_fast` → «DC 50 kW:sta alkaen», `th_n` → «Paikkoja».
Не принято: `km_away` (EN тоже «{km} km», в таблице расстояний «päässä» лишнее), `share_ac` (контекст — доли), `pl_city_in` (это инессив после числа: «12 kaupungissa», корректно), `to_country`/`t_network` (верно при условии, что `{country_u}` — локатив; это контракт).

**Ревизия локативов** отдельным агентом: страны 149/150 верны, GI исправлен на «Gibraltarissa». Финские города (80) — все верны. Иностранные по правилу (выборка 150): 6 ошибок, 4 варианта — все из-за гармонии по написанию. Правило исправлено: в DE/AT/CH/LU/LI «ei/ey/ai/ay» считаются задним рядом (Peinessa, Wertheimissa, Steyrissa), «eu» — тоже; в NL/BE «eu/ui» — передний (Beuningenissä, Maassluisissä); англоязычные на -ow/-ew/-iew/-aw — с апострофом (Longview’ssa). Немецкое «oe» оставлено задним (Soestissa, Itzehoessa — там это долгое o); Oeldessa — допустимый вариант. Изменилось 92 строки.

## Что осталось / вопросы
- `decl_ok = 0` у 2 156 городов из 5 605 (безопасная конструкция «kaupungissa X»): Франция, многословные названия, немая -e, Греция/Прибалтика. Можно добить ручным списком для крупнейших ~200 по числу мест.
- В исходном `names/cities.csv` у Hollola два geonameid (657530 month, 657531 quarter) — дубль источника, не перевода.
- Экзоним Вильнюса — «Vilna» (рекомендация Kotus); в СМИ часто «Vilnius/Vilniuksessa».
- Названия сетей (`networks.csv`) не переводятся (P1: общие).

## FIXL (11.11.2026)
- `strings_home.json` (71 ключ, `pl_*` = one/other, партитив после числа); `strings_shell`: `lang_hint` «Tämä sivu on saatavilla myös suomeksi», `lang_hint_close` «Sulje».
- Слаги: /fi/maksaminen/ /fi/reitit/ /fi/medialle/ /fi/dataa-yrityksille/ /fi/embed/kartta/ /fi/kartta-omalle-sivustolle/ /fi/kehittajille/.
- `cities.csv` +49 (NOBIL NO 2 + SE 46 + Geneve «Genevessä»), note «FIXL». `name_nom` (D14) к fi не относится.
