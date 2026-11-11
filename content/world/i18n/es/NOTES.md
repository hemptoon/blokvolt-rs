# L-ES — заметки по испанской локализации мирового слоя

Ветка `l-es` от `g3-prices` (cf44fc3). Все файлы лежат только здесь. В прод не включено (после ворот G8).

## Вариант языка и обращение
- Нейтральный европейский испанский (Испания), понятный и в Латинской Америке; регионализмов нет.
- BlokVolt безличен: «nosotros», «nuestro», «la redacción», «el equipo» не используются. К читателю — на «usted» или безлично/инфинитивом («Consulte…», «Descargar datos»). Формы на «tú» нет.
- `check.py` проверяет запрещённые слова: 24/7, inmediatamente/al instante, Evolako, nosotros/nuestro.

## Термины (из glossary.csv, колонка es)
- estación de carga, punto de carga, cargador, ubicación, red, operador, carga rápida/ultrarrápida, Tipo 2, potencia máxima, rango de potencia, fiabilidad de los datos, datos abiertos, Informar de un error, Ver en el mapa, Cómo llegar.
- В навигации и заголовках — «puntos de carga». Хаб `/es/puntos-de-carga/` и `nav_hub` = «Puntos de carga». Обратный перевод предлагал «Estaciones de carga»; оставлено так, чтобы совпадало со слагом и картой.
- «checked» = «verificado», как в глоссарии. Обратный перевод отметил, что «verificado» звучит сильнее, чем «comprobado». Если Андрей сочтёт, что это обещает больше, чем есть, — заменить на «comprobado» в глоссарии и в строках.
- Plans в ценах (`pay_sub`, `plan_sub`) = «Suscripción/Suscripciones», как в sr/ru (Pretplata / Подписка). `th_plan` = «Tarifa».
- ad hoc: «sin registro (ad-hoc)» в длинном тексте, «sin registro» в коротких подписях.
- «Report» в форме ошибок — «aviso» («El aviso no se ha enviado»).
- В `texts.json` юридические строки атрибуции, названия лицензий и колонок CSV оставлены как в оригинале («© OpenStreetMap contributors», ODbL 1.0, CC BY 4.0…).

## Плюралы
- CLDR/Babel для es: категории `one`, `many`, `other`. `many` (миллионы, «1 millón de…») равен `other`: числа выводятся цифрами, так что «1.000.000 ciudades» читается нормально.
- Пары `pl_city`/`pl_city_in` и `pl_country`/`pl_country_in` совпадают: в испанском существительные не склоняются.

## Типографика
- `pct` = «{x} %», с пробелом по нормам RAE. В EN — «{x}%». Плейсхолдер тот же.
- В диапазонах четырёхзначных чисел разделитель тысяч не ставится (2500–4999 kWh).

## Адреса (slugs.json)
`/es/`, `/es/mapa/`, `/es/puntos-de-carga/`, `red`, `sobre-los-datos`, `descargar`, `/es/redes-de-carga/`, `/es/precios-de-carga/`, `/es/acerca-de/`, `/es/fuentes/`, `/es/metodologia/`.

## Страны (countries.csv)
- Названия — из CLDR (`name_es`). Исправлено 4: HK «RAE de Hong Kong (China)» → Hong Kong; MO → Macao; MM «Myanmar (Birmania)» → Myanmar; AX «Islas Aland» → Islas Åland.
- Слаг — ASCII от испанского названия (espana, alemania, reino-unido, paises-bajos).
- `in_phrase` = «en X». С артиклем: el Reino Unido, los Países Bajos, los Emiratos Árabes Unidos, la India, la República Dominicana, las Islas Feroe/Caimán/Åland, la Isla de Man, los Territorios Palestinos, El Salvador. «en Estados Unidos» — без артикля, RAE это допускает.

## Города (cities.csv) — все 5 605
- Сначала идут испаноязычные страны (378), потом stage month → balkan → quarter.
- `in_phrase` = «en X», `decl_ok = 1` для всех: падежей в испанском нет.
- Экзонимы по RAE/Fundéu — 147 городов: Múnich, Colonia, Fráncfort, Londres, París, Marsella, Milán, Lisboa, Oporto, Bruselas, La Haya, Varsovia, Praga, Belgrado, Atenas, Estambul, Nueva York, Pekín, Tokio…
- Испания: официальные названия (A Coruña, Girona, Lleida, Ourense). Где у крупного города в испанском тексте принята кастильская форма — она (12 городов: Valencia, Castellón de la Plana, Alcoy, Ibiza, Mahón, Jávea, San Sebastián, Villajoyosa…), а официальная записана в `note`.
- Нелатинские местные названия (GR, BG, RU…) — латиница из `name_en`, 162 города. У самых известных — испанский экзоним (Atenas, Sofía, Heraclión, Rodas).
- Округа Марселя → «Marsella (distrito 9)»; округа Винтертура — так же.

## Проверка
- `python3 content/world/i18n/es/check.py`: 679 строк, 11 слагов, 150 стран, 5605/5605 городов, 0 ошибок.
- Обратный перевод 60 случайных строк вслепую (`backtranslation_report.md`): 53 ок, 5 мелких, 2 «расхождения». Расхождения — Plan/Suscripción, это сознательно, как в sr/ru. Из мелких исправлено: потерянное «примерно» в `cars_note`. Остальное — в разделах выше.

## Что осталось / для K8
- Мотору K8 нужно, чтобы `{country_u}`/`{city_u}` для es брались из `in_phrase` («en Alemania»). Строки на это рассчитаны, `fallback_u` = «en {x}».
- `p_hub_na` переведена буквально («США и Канада — на английском и русском…»). Когда es включат, проверить, верно ли это для испанской версии.
- `home_title` — 70 символов, длиннее 60. В EN тоже длинный (76).
- Экзонимы проставлены для известных городов. Полной ручной проверки по 5 605 городам не было: остальные идут под местным латинским названием.

## FIXL (11.11.2026)
- Добавлен `strings_home.json` (71 ключ, плюралы one/many/other). Shell: `lang_hint` «Esta página también está disponible en español», `lang_hint_close` «Cerrar».
- D14: колонка `name_nom` = `in_phrase` без «en » (артикль там же, где в in_phrase). `{name_nom}` не ставить в начало фразы и после «de»/«a»; конструкция «Al formar parte {name_nom} de la UE…».
- Слаги (F5): /es/como-pagar/ /es/rutas/ /es/para-medios/ /es/datos-para-empresas/ /es/embed/mapa/ /es/mapa-para-su-web/ /es/desarrolladores/.
- Города: Женева = Ginebra; 48 городов NOBIL — шведские/норвежские названия с диакритикой, «en X», decl_ok=1.
- FIXL2: +821 cities from names/cities_extra.csv (own market 86). Экзонимы: Florencia, Génova, Roma, Mesina, Odesa; исправления GeoNames: Alcalá de Guadaíra, Playa del Inglés, San Miguel de Abona, Ribeira (вместо Santa Uxía de Ribeira), Santa Fe (Granada); RO ş/ţ → ș/ț; GR/UA/BY — английская романизация, как в файле.
