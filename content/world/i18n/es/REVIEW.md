# R-ES — вычитка испанского мирового слоя (10.11.2026)

База: `origin/l-es` (5f15341), ветка `r-es`. Редактор — независимая сессия пула 4.

## Итог
- Строки: просмотрены все 403 ключа + texts.json. Изменено 18 ключей строк (4 из них — только кавычки « ») и 6 строк texts.json (кавычки и название страницы «Sobre los datos»).
- Страны: просмотрены все 150; исправлено 2 in_phrase (Líbano, Polinesia Francesa — с артиклем).
- Города: просмотрены все 378 городов испаноязычных стран и первые 520 `stage = month` по порядку файла (places JSON не брал — время). Отдельно прогон по списку ~70 известных испанских экзонимов по всему файлу. Исправлено 7 названий.
- Слаги: без изменений. ASCII, естественные, пересечений нет (раздела `content/com/local/es/` нет; EN/SR/RU живут без префикса /es/).
- `texts.json`: удалён ключ `sources_pages` — по правилу 23:55 он один на все языки и не переводится. `check.py` больше его не требует.
- `check.py`: 0 ошибок (500 строк после удаления sources_pages, 11 слагов, 150 стран, 5 605 городов).
- Обратный перевод изменённых строк — отдельный агент вслепую: 23 ок, 2 замечания — оба учтены (th_share откатан к «Proporción», table_note переписан). Названия мест — все 9 стандартные.

## Принятые решения
- Ad hoc = «sin registro» везде (раньше в карточке было «sin contrato»); латинизм пишется «ad hoc» без дефиса.
- Хаб и навигация — «Puntos de carga» (shell `nav_stations` было «Estaciones de carga»). `c_unnamed` = «Estación de carga»: это заголовок станции без имени, а «Puntos de carga» в той же карточке — число разъёмов.
- Кавычки — « » (норма RAE) во всех строках и текстах.
- Страница данных называется «Sobre los datos» везде (h1 и ссылки на неё были «Acerca de los datos»). «Acerca de» остаётся только для /es/acerca-de/ — о BlokVolt.
- Числа без форм: `sources_n` = «Fuentes: {n}».
- Кнопки и подписи укорочены до EN × 1,4: «Borrar filtros», «Correo (opcional)», «DC / hogar».

## Спорное, не трогал
- «verificado» (подвал, глоссарий) vs «comprobado» (цены). Оставлено как есть: подвал говорит о проверенных региональных данных; если хочется мягче — заменить и в глоссарии.
- `p_hub_na` («EE. UU. и Канада — на английском и русском») — верно для сайта, но читается странно в es-версии. Решать при включении.
- `p_net_share`: «presente en 12 ciudades en Alemania» — «en … en» тяжеловато, но без нового плейсхолдера лучше не сделать.
- Районы как «города» (Chamartín, Ciudad Lineal, Gamonal, Natahoyo, Santutxu, Iturrama…) и лондонские районы — это данные GeoNames, не перевод. Вопрос к движку, не к es.
- Breslavia/Wrocław, Nimega/Nijmegen, Bolduque/'s-Hertogenbosch — оставлены местные формы: в современной прессе Испании они преобладают.

## Строки
| файл | ключ | было | стало | почему |
|---|---|---|---|---|
| map | `title` | Mapa mundial de carga para coches eléctricos | BlokVolt | Mapa mundial de puntos de carga para coches eléctricos | BlokVolt | «mapa de carga» неестественно; как h1 |
| map | `sources_n` | {n} fuentes | Fuentes: {n} | без форм после числа: «1 fuentes» невозможно |
| map | `c_price` | Precio sin contrato | Precio sin registro | единый термин ad hoc = «sin registro» |
| shell | `nav_stations` | Estaciones de carga | Puntos de carga | как nav_hub, хаб и слаг /es/puntos-de-carga/ |
| pages | `p_multi` | El {pct_multi} de las ubicaciones está confirmado por dos o más fuentes; el {pct_recent} se confirmó por última vez en 2025 o 2026. | El {pct_multi} de las ubicaciones están confirmadas por dos o más fuentes; el {pct_recent} se confirmaron por última vez en 2025 o 2026. | согласование с «de las ubicaciones» (норма Fundéu) |
| prices | `d_hub` | Cuánto cuesta la carga pública de vehículos eléctricos en Europa: precios sin registro (ad-hoc) de las redes por país, AC, DC y HPC, frente a la electricidad doméstica. Cada precio con su fuente y su fecha. | Cuánto cuesta la carga pública de vehículos eléctricos en Europa: precios sin registro (ad hoc) de las redes por país, AC, DC y HPC, frente a la electricidad doméstica. Cada precio con su fuente y su fecha. | латинизм ad hoc без дефиса (RAE) |
| prices | `lead_hub` | Precios sin registro (ad-hoc) —lo que paga un conductor sin contrato— de {nets} redes en {countries} países, ponderados por el número de puntos de carga de cada red en el país, junto al precio de la electricidad doméstica. El método es abierto y los datos se pueden descargar. | Precios sin registro (ad hoc) —lo que paga un conductor sin contrato— de {nets} redes en {countries} países, ponderados por el número de puntos de carga de cada red en el país, junto al precio de la electricidad doméstica. El método es abierto y los datos se pueden descargar. | латинизм ad hoc без дефиса (RAE) |
| prices | `table_note` | Precios sin registro (ad-hoc) con IVA, por kWh. {u} — mediana de las redes, sin ponderar: las redes con precio conocido tienen menos del 10 % de los puntos de carga del país cuya red se conoce. — sin índice: menos de dos redes con precio. | Precios sin registro (ad hoc) con IVA, por kWh. {u} — mediana de las redes, sin ponderar: las redes con precio conocido tienen menos del 10 % de los puntos de carga del país cuya red se conoce. — sin índice: menos de dos redes con precio. | латинизм ad hoc без дефиса (RAE) |
| prices | `m1` | Precios: la tarifa sin registro (ad-hoc) de cada red —lo que paga cualquiera sin contrato ni suscripción— tomada de la página de precios del propio operador o, si el operador no publica ninguna, de una noticia fechada que la cite. Precios con IVA, por kWh. Los precios por minuto o por sesión, los de más de 12 meses y aquellos cuya fuente no está clara se muestran en las páginas de cada país, pero quedan fuera del índice. | Precios: la tarifa sin registro (ad hoc) de cada red —lo que paga cualquiera sin contrato ni suscripción— tomada de la página de precios del propio operador o, si el operador no publica ninguna, de una noticia fechada que la cite. Precios con IVA, por kWh. Los precios por minuto o por sesión, los de más de 12 meses y aquellos cuya fuente no está clara se muestran en las páginas de cada país, pero quedan fuera del índice. | латинизм ad hoc без дефиса (RAE) |
| prices | `cars_note_net` | Consumo de la batería con clima templado, estimación (Open EV Data, © 2019 Chargeprice, MIT); en invierno, entre un 20 y un 30 % más. No incluye las pérdidas durante la carga. Precios: la tarifa sin registro (ad-hoc) de la red. | Consumo de la batería con clima templado, estimación (Open EV Data, © 2019 Chargeprice, MIT); en invierno, entre un 20 y un 30 % más. No incluye las pérdidas durante la carga. Precios: la tarifa sin registro (ad hoc) de la red. | латинизм ad hoc без дефиса (RAE) |
| prices | `cars_note_net` | Consumo de la batería con clima templado, estimación (Open EV Data, © 2019 Chargeprice, MIT); en invierno, entre un 20 y un 30 % más. No incluye las pérdidas durante la carga. Precios: la tarifa sin registro (ad hoc) de la red. | Consumo de la batería con clima templado, estimación (Open EV Data, © 2019 Chargeprice, MIT); en invierno, aproximadamente entre un 20 y un 30 % más. No incluye las pérdidas durante la carga. Precios: la tarifa sin registro (ad hoc) de la red. | потеряно «about», как в cars_note |
| map | `reset` | Restablecer filtros | Borrar filtros | кнопка: длина ≤ EN×1,4 |
| map | `r_email` | Correo electrónico (opcional) | Correo (opcional) | подпись поля: длина ≤ EN×1,4 |
| map | `c_unnamed` | Estación de carga para vehículos eléctricos | Estación de carga | заголовок карточки без имени: короче, контекст и так EV |
| prices | `th_ratio` | DC frente a hogar | DC / hogar | заголовок столбца: длина |
| prices | `table_note` | Precios sin registro (ad hoc) con IVA, por kWh. {u} — mediana de las redes, sin ponderar:  | Precios sin registro (ad hoc) con IVA, por kWh. {u} — mediana de las redes, sin ponderar: las redes con precio conocido  | неоднозначное «del país cuya red se conoce» (обратный перевод) |

## Тексты (texts.json)
| файл | ключ | было | стало | почему |
|---|---|---|---|---|
| texts | `sources_pages` | переведённые name/licence 29 источников | удалён ключ | правило 23:55: sources_pages один на все языки, не переводится |
| texts | `about_data.h1` | Acerca de los datos del mapa | Sobre los datos del mapa | кавычки «» (RAE); название страницы как в навигации «Sobre los datos» |
| texts | `about_data.osm_p` | Datos © OpenStreetMap contributors, disponibles bajo la Open Database License (ODbL) 1.0 — | Datos © OpenStreetMap contributors, disponibles bajo la Open Database License (ODbL) 1.0 — | кавычки «» (RAE); название страницы как в навигации «Sobre los datos» |
| texts | `about_data.notes[5]` | Para informar de un error o solicitar una corrección o eliminación, utilice el botón "Info | Para informar de un error o solicitar una corrección o eliminación, utilice el botón «Info | кавычки «» (RAE); название страницы как в навигации «Sobre los datos» |
| texts | `download.fields[12][1]` | Claves de las fuentes, separadas por comas (véase la página "Acerca de los datos") | Claves de las fuentes, separadas por comas (véase la página «Sobre los datos») | кавычки «» (RAE); название страницы как в навигации «Sobre los datos» |
| texts | `download.licence_p` | El archivo está disponible bajo la ODbL 1.0. Puede compartir los datos, crear obras a part | El archivo está disponible bajo la ODbL 1.0. Puede compartir los datos, crear obras a part | кавычки «» (RAE); название страницы как в навигации «Sobre los datos» |
| texts | `download.attribution_p` | Al usar los datos, muestre "© OpenStreetMap contributors, BlokVolt" con un enlace a www.op | Al usar los datos, muestre «© OpenStreetMap contributors, BlokVolt» con un enlace a www.op | кавычки «» (RAE); название страницы как в навигации «Sobre los datos» |
| pages | `report_map` | Un error en una ubicación se puede notificar con el botón “Informar de un error” de su fic | Un error en una ubicación se puede notificar con el botón «Informar de un error» de su fic | кавычки «» (RAE), единообразно с texts |
| prices | `profiles_note` | Coche: {car}, {cons} kWh por 100 km (estimación, clima templado, energía de la batería; no | Coche: {car}, {cons} kWh por 100 km (estimación, clima templado, energía de la batería; no | кавычки «» (RAE), единообразно с texts |
| prices | `data_p` | Descargue el índice y todas las tarifas con su fuente en CSV. Licencia: CC BY-NC 4.0 — uso | Descargue el índice y todas las tarifas con su fuente en CSV. Licencia: CC BY-NC 4.0 — uso | кавычки «» (RAE), единообразно с texts |
| prices | `cars_note` | Consumo de la batería con clima templado, estimación (Open EV Data, © 2019 Chargeprice, MI | Consumo de la batería con clima templado, estimación (Open EV Data, © 2019 Chargeprice, MI | кавычки «» (RAE), единообразно с texts |

## Страны и города
| файл | ключ | было | стало |
|---|---|---|---|
| countries.csv | LB | in_phrase: en Líbano | en el Líbano |
| countries.csv | LB | note:  | с артиклем по DPD RAE |
| countries.csv | PF | in_phrase: en Polinesia Francesa | en la Polinesia Francesa |
| countries.csv | PF | note:  | с артиклем, как обычно в испанском |
| cities.csv | 2918632 | name: Göttingen | Gotinga |
| cities.csv | 2918632 | in_phrase: en Göttingen | en Gotinga |
| cities.csv | 2918632 | note:  | традиционный экзоним |
| cities.csv | 588409 | name: Tallinn | Tallin |
| cities.csv | 588409 | in_phrase: en Tallinn | en Tallin |
| cities.csv | 588409 | note:  | экзоним Fundéu |
| cities.csv | 3034475 | name: Bayonne | Bayona |
| cities.csv | 3034475 | in_phrase: en Bayonne | en Bayona |
| cities.csv | 3034475 | note:  | испанский экзоним |
| cities.csv | 2820860 | name: Tübingen | Tubinga |
| cities.csv | 2820860 | in_phrase: en Tübingen | en Tubinga |
| cities.csv | 2820860 | note:  | традиционный экзоним |
| cities.csv | 2925535 | name: Frankfurt (Oder) | Fráncfort del Óder |
| cities.csv | 2925535 | in_phrase: en Frankfurt (Oder) | en Fráncfort del Óder |
| cities.csv | 2925535 | note:  | экзоним Fundéu |
| cities.csv | 3068160 | name: Plzeň | Pilsen |
| cities.csv | 3068160 | in_phrase: en Plzeň | en Pilsen |
| cities.csv | 3068160 | note:  | принятая испанская форма |
| cities.csv | 2989317 | name: Orléans | Orleans |
| cities.csv | 2989317 | in_phrase: en Orléans | en Orleans |
| cities.csv | 2989317 | note:  | экзоним RAE/Fundéu |

# L2-ES — дельта ключей, тексты данных, свои страны (11.11.2026)

Ветка `l2-es` от `dev` (bb86f74). HOME2 в `dev` ещё не было — его ключей нет.

## Что сделано
- 274 новых ключа: strings_map +29 (28 `ci_*` и `emb_open`), новые файлы strings_pay (93), strings_press (54), strings_b2b (33), strings_embed (65). Форма «usted», ad hoc = «sin registro», кавычки « », «24/7», «nosotros» и «el equipo» не используются.
- `texts.json`: новые разделы `pay` (6 узлов `afir.points[i]`) и `routes` (59 узлов `routes[i].stops[j].city`). Названия городов берутся из `cities.csv` es: Belgrado, Sofía, Salzburgo, Liubliana.
- Свои страны ES и AD: названия и `in_phrase` в порядке. Города со страницами — 177, все есть в `cities.csv`, `decl_ok = 1`. Пяти валенсийским городам поставлена кастильская форма, как раньше у Alcoy и Jávea: Játiva, Denia, Onteniente, Benicasim, Gandía. Официальное название записано в `note`. Слаги не меняются: они берутся из `names/cities.csv`.
- `check.py` теперь проверяет все 8 файлов строк и разделы `texts.pay` и `texts.routes`: ключи сверяются с многоязычными узлами `pay.json` и `routes.json`, плейсхолдеры и теги — с EN. Итог: 839 строк, 0 ошибок.

## Обратный перевод (60 случайных новых строк, отдельный агент вслепую)
60 из 60 — смысл совпадает. Мелочи, которые оставлены сознательно:
- «sin registro» обратно переводится как «no registration», а не «ad hoc». Это принятый термин R-ES.
- `ci_last_*` «aviso» → «report», а не «check-in». Термин тот же, что у формы ошибок.
- `th_gaps` «Tramos sin carga > 150 km» читается понятнее, чем EN «Gaps».

## Вопросы
- `dv_p_lang` перечисляет EN, SR, RU. Когда в виджете появится es, строку нужно обновить во всех языках (это задача LANG0/EN).
- В `pages_state.json` 144 города NOBIL (NO и SE), которых нет в `names/cities.csv`. Для es это не свои страны, но таких городов нет и в общем справочнике. Их нужно добавить в `names` (задача LANG0/LANGI).
- `credit` и цитата в `data_p` используют английское название индекса «European EV Charging Price Index», как в R-ES.

## FIXL 11.11.2026
Что проверено: новый `strings_home.json` (71 ключ), `lang_hint`/`lang_hint_close`, D11 (`embed.dv_p_lang`, `pages.p_hub_na`), D14 (`pay.afir_eu`, `afir_non`, `conn_txt` через `{name_nom}`), колонка `name_nom` в countries.csv, 49 городов FIXL, 7 слагов разделов.
Обратный перевод (волна 1, вслепую, сделан самим агентом FIXL): 20 строк home (title, desc, h1, sub, data_as_of, search_none, near_err, map_more, countries_h, below_h, prices_p, p_src, routes_p, work_p, o_press_p, trust_p, org_desc, map_err, ap_note, p_ratio) и все 7 других изменённых строк. По смыслу всё совпадает. Исправлено:
- `trust_p`: «Sin posiciones de pago» читалось как «без платёжных позиций» → «Sin posicionamiento de pago».
- `desc` сокращён до 213 знаков (EN 206): «EE. UU.», «de cada lugar».
- `near_err`: «ubicación» заменено на «geolocalización», чтобы не путать с термином «ubicación» (место для зарядки).
Принятые расхождения: в `h1`/`title` «puntos de carga» без «coches eléctricos» (как в хабе и карте); `p_src` «verificados» — по глоссарию (checked = verificado).
D14: `name_nom` = `in_phrase` без «en » (los Países Bajos, el Reino Unido, la India, el Líbano, Estados Unidos, España). Чтобы не было «Los Países Bajos» с маленькой буквы в начале фразы и проблем с согласованием глагола (los Países Bajos forman/España forma), использован инфинитив: «Al formar parte {name_nom} de la UE, …». После «de» `{name_nom}` не ставится (de + el = del) — в `conn_txt` «que hay en {name_nom}».
D12: в es cities.csv исторических/ирредентистских экзонимов нет (Niza, Ratisbona, Tesalónica, Leópolis — нормальные экзонимы RAE/Fundéu). Ничего не меняли.
Открыто: `pay.conn_lnk` по правилу оставлен с `{name}` («Puntos de carga en {name}» → «en Países Bajos» без артикля). `pages.p_city_cmp` «de media en {country_name}» — та же проблема с артиклем; движку нужен `{country_u}` для этого ключа.
