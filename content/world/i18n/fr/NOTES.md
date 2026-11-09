# FR — notes de traduction (L-FR, pool 3, 09.11.2026)

Langue : français de France. Contrat : `tasks_pool3/00_README.md` §3 L-<код>. Не включать в прод до ворот G8.

## Форма обращения и типографика
- Безлично или на «vous» (Vérifiez…, Réessayez…); кнопки — инфинитив («Voir sur la carte», «Télécharger les données»). Ни «nous», ни «notre», ни «la rédaction» — проверяет `check.py`.
- Неразрывный пробел U+00A0 перед `: ; ? !` и внутри « ». Апостроф типографский ’ во всех файлах.
- Проценты — `"{x} %"` (с U+00A0). Разделители чисел даёт код (K8-реестр: dec `,`, thou U+202F или U+00A0 — решить в K8).

## Плюралы
CLDR fr: `one` (0 и 1), `many` (миллионы: «1 million de…»), `other`. В файлах `many` = `other` — для счётчиков мест/сетей это правильно, т. к. код печатает цифрами («1 000 000 sites»), а не словом «million».
Формы `pl_*_in` (падежные в sr/ru) во французском совпадают с обычными.

## Термины (glossary.csv, колонка fr)
station de recharge / borne de recharge / point de charge / site de recharge · prise · réseau · opérateur · recharge rapide (DC ≥ 50 kW) · ultra-rapide = 150 kW et plus · données ouvertes · fiabilité des données · dernière confirmation · signaler une erreur · itinéraire · indice des prix.
- «European EV Charging Price Index» → «Indice européen des prix de la recharge».
- «ad hoc» → «sans inscription» (глоссарий). Вариант «sans abonnement / à l’acte» читается естественнее в ценовых таблицах — вопрос к Андрею, сейчас по глоссарию.
- «Plan» → «Formule» (план сети не всегда подписка); «Subscription» в глоссарии остаётся «abonnement».
- «by prior notice» → «sur préavis».

## Что нужно от K8 (мотор)
- `{country_u}` во FR получает фразу целиком с предлогом из `countries.csv:in_phrase` («en Allemagne», «aux Pays-Bas», «au Mexique», «à Malte»); `{city_u}` — из `cities.csv:in_phrase` («à Munich», «au Havre»). В строках перед ними ничего не стоит.
- `t_city`/`t_city_cc` = «… à {city}, {country}» — для городов с артиклем («Le Havre») даст «à Le Havre». Лучше, чтобы K8 подставлял `in_phrase` города (ключ `t_city` можно перевести на `{city_u}`, если мотор это позволит).
- `t_near` = « (près de {x})» — без элизии («près de Ulm» вместо «près d’Ulm»). Нужна функция `de_elide()` в моторе или отдельная колонка; пока оставлено.
- `p_hub_na` говорит, что США и Канада покрыты на EN и RU — при включении FR текст надо будет обновить по факту.

## Названия
- `countries.csv`: CLDR (`name_fr`), 4 правки: Hong Kong, Macao, Myanmar (короткие формы вместо «R.A.S. chinoise de…», «Myanmar (Birmanie)»), Saint-Vincent-et-les-Grenadines (дефис). Предлоги: женский род/гласная → en, мужской → au, мн. ч. → aux, острова/города-государства → à; исключения вручную (au Mexique, au Cambodge, au Belize, au Suriname, en Israël, à Oman, à Bahreïn, à la Barbade, sur l’île de Man…).
- `cities.csv`: см. RESULT — экзонимы (Munich, Cologne, Aix-la-Chapelle, Londres, Varsovie…), иначе местное латинское имя, иначе EN.
- `texts.json`: названия источников (`sources_pages.*.name`) не переводились, хотя часть — английские описания («UK charge point operators’ open data…»). Если они показываются на FR-страницах — решить, переводить ли.
- Строка цитирования в `texts.json` оставлена «© OpenStreetMap contributors, BlokVolt» (как формула лицензии), в тексте `osm_p` — «© contributeurs OpenStreetMap».

## Проверка
- `python3 content/world/i18n/fr/check.py` → 0 ошибок.
- Обратный перевод 60 случайных строк (seed 42): ok 57, minor 3, mismatch 0; все 3 minor исправлены (Formule ×2, sur préavis).
