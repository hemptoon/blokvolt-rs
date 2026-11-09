# R-NL — вычитка нидерландского (пул 4, 10.11.2026)

База `l-nl` 6b5fb2b → ветка `r-nl`. Перевод в целом сильный: обращение «u» везде, безлично, без «we», плюралы `{one, other}` верны.

## Строки — 403 проверены, 23 исправлены

- Термины и естественность: `f_type` Laadtype; `net_selected` Geselecteerde netwerken; `th_cover` DC-dekking; `c_unnamed` Laadstation; `title` (карта) «laadstations voor elektrische auto's» вместо «EV's»; «bestuurder» → «EV-rijder» (`lead_hub`, `h_profiles`).
- Смысл: `zoom_note` («drukste» = «самые оживлённые» → «gebieden met de meeste punten»); `p_city_cmp` («tegenover gemiddeld {country} in heel …»); `sources_note` («eigendom van hun eigenaars» → «merken van hun respectieve eigenaren»); `data_date` → «Gegevens per {d}», как `data_from`.
- Тон: `r_ok` «Hartelijk dank.»; `osm_fix`, `disc` «dit» вместо «het»; `r_sending` «Bezig met versturen…» (пара к «Bezig met laden…»); `h_pay` «Zo betaalt u, in het kort»; `pay_free` «geen maandelijkse kosten»; `report` «Fout melden» как на карте.
- Длина (EN × 1,4): `f_conf`/`c_conf` → «Betrouwbaarheid» (пояснение даёт `conf_note`); `r_snaga` сокращено.
- Длиннее EN × 1,4 оставлено намеренно, короче без потери смысла нельзя: `r_send` Versturen, `ch_ft_checked` gecontroleerd, `ft_about` «Over BlokVolt» («Over ons» нарушает безличность), `loading` «Bezig met laden…» (L-NL исправлял двусмысленность), `acc_public_pay_at_location`.

## Страны — 150 проверены, 1 исправлена

- VC → «op Saint Vincent en de Grenadines» (острова).
- IM: правильнее «op het eiland Man», но `check.py` требует, чтобы название было внутри `in_phrase`, поэтому оставлено «op Isle of Man». Вопрос для K8.

## Города

Проверены все 376 городов NL+BE, первые 500 `stage=month` по порядку файла (в `places-2026-11-09.json` нет счётчиков мест) и список экзонимов.
- Rodos → **Rhodos**, «op Rhodos».
- Urk → «**op** Urk» (бывший остров, так принято).
- `decl_ok = 1` везде: падежей в нидерландском нет.
- Спорное, оставлено как у L-NL (норма Taalunie, бельгийская практика): Rijsel (Lille), Bergen (Mons — совпадает с Bergen NH и Bergen NO; страна в заголовке различает), Gembloers, Tubeke, Lessen, Wezet, Eigenbrakel, Aat, Zinnik, 's-Gravenbrakel. Если важнее читатель из Нидерландов, у мелких валлонских городов надо вернуть французские названия.

## Слаги

`/nl/kaart/`, `/nl/laadstations/`, `/nl/laadnetwerken/`, `/nl/laadprijzen/`, `/nl/over/`, `/nl/bronnen/`, `/nl/methodologie/`, `netwerk`, `over-de-data`, `downloaden`. Всё ASCII, естественно. Пересечений нет: локального раздела `/nl/` в `content/com/local/` нет, EN/SR/RU-пути другие.

## Проверка

- `check.py` — 0 ошибок.
- Обратный перевод 40 строк (20 изменённых + 20 случайных) вслепую отдельным агентом: 37 ok, 3 minor, 0 mismatch. Minor-замечания исправлены (zoom_note) или оставлены осознанно (f_conf/c_conf — длина). Подробно — `BACKTRANS_R.md`.
