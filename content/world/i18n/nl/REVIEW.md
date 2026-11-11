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

## L2 (11.11.2026, branch l2-nl)

- 274 new keys translated: strings_map +29 (ci_* check-ins, emb_open), strings_pay 93, strings_press 54, strings_b2b 33, strings_embed 65.
- texts.json: new sections `pay` (6 AFIR points) and `routes` (59 stop city names, Dutch exonyms from cities.csv: Belgrado, Boedapest); `sources_pages.nobil` added (verbatim attribution).
- Back-translation of 60 random new strings: 0 meaning drifts, style fixes applied — see BACKTRANS_L2.md.
- NL/BE cities: all 302 city pages of NL and BE are in cities.csv (0 added); names and exonyms re-checked.
- Open: `cu`/`lo`/`hi` placeholders must carry the Dutch preposition ("in Duitsland", "in de Verenigde Staten") — LANG0 should fill them from `in_phrase`.

## FIXL 11.11.2026

- Checked: new `strings_home.json` (71 keys), `strings_shell` `lang_hint`/`lang_hint_close`, D11 (`dv_p_lang`, `p_hub_na`),
  D13 «je» conversion (every u/uw string, ≈35 in 9 files), 7 new slugs, 49 new cities (48 NOBIL + Genève).
- Back-translation NL→EN, wave 1: 20 random `strings_home` keys (countries_p, attr_borders, p_btn, map_go, pay_p, o_widget_p,
  search_go, attr, pl_countries, o_widget, prices_h, map_more, p_ratio, p_src, data_as_of, tab_eu, search_none, p_dc, all_link,
  btn_full) + 20 changed strings (ci_paid, ci_thanks, ci_once, ci_privacy, r_email_hint, report_map, dv_lead, dv_attr_h, cf_lead,
  form_p, fx_note, data_p, h_pay, pay_note, h1_pay_hub, stops_note, afir.points[0], texts licence_p / attribution_p, p_hub_na).
- Divergences fixed: `o_widget_p` «Plaats de kaart met je eigen filters» read back as "Place the map…" (lost "on your site")
  → «Zet de kaart met je eigen filters op je site». No meaning errors in the je-conversion; verb forms checked
  (inversion drops -t: «heb je», «betaal je», «vermeld je», «schrijf je»; subordinate keeps it: «dat je … vermeldt»).
- D12: no historical/irredentist exonyms found (Rijsel, Duinkerke, Aken, Kleef, Emmerik are current standard Dutch exonyms; kept).
- Open doubts: `tab_ap` «Azië-Pacific» (business usage) vs «Azië en de Stille Oceaan»; `routes_h` «Autoreizen».
