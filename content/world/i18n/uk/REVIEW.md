# R-UK — вычитка украинского перевода мирового слоя (пул 4, 10.11.2026)

База — `origin/l-uk` (`5ed9434`), ветка `r-uk`. Язык по-прежнему не включён (после K8-i18n и G8).

## Строки (403 ключа, исправлено 32)

- **Термин «public» сведён к одному слову: «публічний».** В переводе были вперемешку «громадські місця» (pages, shell) и «публічні станції / Публічний доступ» (map, prices). «Громадське місце» по-украински звучит как «общественное место» вообще. Заменено в 14 ключах, включая формы `pl_publoc`.
- **Падежи через `{city_u}`** (уточнение пула 4): `d_city` («місця заряджання Мюнхен» → «місця заряджання у Мюнхені»), `t_city`, `t_city_cc` (заголовок с двоеточием → «Зарядні станції для електромобілів у Мюнхені, Німеччина»).
- **Согласование и порядок слов:** `p_shown`, `p_city_cmp`, `c_lead`.
- **Единые формулы:** дата — везде «станом на» (`data_date`, `c_price_note`, `ft_checked`); skip-link — «Перейти до вмісту» в обоих файлах.
- **Длина ≤ EN × 1,4** для меток, чипов и легенды: `c_price`, `c_unnamed`, `acc_public_membership`, `acc_public_notice_required`, `acc_private_notice_required`, `r_lokacija`, `pr_home`, `pr_street` (+ `profiles_note`, где эти названия цитируются).
- Мелочи: `osm_fix` (благозвучие), `contact` → «Контакти», `data_p` «Cite as» → «Як цитувати».
- Форма обращения проверена: везде «ви» / безлично, кнопки — инфинитив. «Ми», «редакція», «24/7» не встречаются.
- Оставлено как было (осознанно): `home_lead` «{n}, {c}» — после числа + «у» понадобился бы местный падеж, которого нет в `pl_cc`; `regional_guide` «для країни {country}»; кнопки «Повідомити про помилку» и тост «Посилання скопійовано» длиннее EN × 1,4, но короче не сказать без потери смысла.

## Страны (150, исправлено 3)

- US: «Сполучені Штати» → «США», `in_phrase` «у США», слаг `ssha` (на сайте в текстах уже «США»).
- XK: «у Косово» → «у Косові» (по-украински склоняется).
- EG: «у Єгипті» → «в Єгипті» (перед [йе] — «в»).
- Остальные 147 проверены: острова с «на», чередование у/в, несклоняемые (Монако, Перу, Чилі).

## Города

- 4 украинских города (Київ, Харків, Львів, Луцьк) — верно.
- 500 первых городов `stage = month` (по порядку `names/cities.csv`) проверены глазами: экзонимы и `in_phrase`. Исправлено 19 составных названий, где стояла безопасная форма, а склонение надёжно: «у Франкфурті-на-Майні»-образные (Мюльгайм-на-Рурі, Лімбург-на-Лані…), Ле-Ман, Ла-Рошель, Ювяскюля, Ден-Гелдер, Берген-оп-Зом и др. → `decl_ok = 1`.
- Остальные `decl_ok = 0` с «у місті X» оставлены: форма безопасная.

## Слаги

- Проверены: ASCII, КМУ-2010, естественные. Пересечений с `content/com/local/` (al ba hr me mk xk) нет: префикс `/uk/` свободен.

## Прочее

- `check.py`: `{city_u}`/`{country_u}` теперь считаются равными `{city}`/`{country}` EN (решение пула 4). 0 ошибок.
- Спорное для Андрея: апостроф `’` (U+2019) vs `ʼ` (U+02BC) — оставлен `’`, как решила L-UK.

## Обратный перевод (отдельный агент, вслепую)

32 изменённые строки → EN, затем сверка с оригиналом: ok 26, minor 6, mismatch 0. По итогам исправлены ещё 2 строки: `p_hub` (двусмысленный порядок «Балкани охоплюють сторінки» → «охоплено сторінками») и `shell.map_p` («офіційних реєстрів» → «відкритих реєстрів», как в EN). Остальные minor — осознанные («за попереднім записом», «заряджання вдома»). Итого исправлено 34 строки.

## L2-uk (11.11.2026) — back-translation of new strings

A separate agent blind-translated 60 random new strings (seed 20261111; 280 new strings of strings_map ci_*/emb_open, strings_pay, strings_press, strings_b2b, strings_embed and texts.pay) back into EN.

Result: 60 ok in meaning, 0 mismatch. Style notes taken in:
- press.lead_press: «з зазначенням» → «із зазначенням» (euphony).
- embed.cf_more: «запити на API» → «доступ до API».
- embed.dv_widget_btn: «Створити код» → «Згенерувати код».
- embed.cf_view, dv_p_hash: «точний вигляд» → «точне положення карти».
- embed.dv_open_btn: «Завантаження та колонки» → «Файл і колонки».
- embed.dv_lead: «Усе відкрите…» → «Усі відкриті дані безкоштовні…».
- pay.gap_note: «Плануйте під’їхати…» → «Заїжджайте на цю ділянку з повною батареєю».

Left as is (deliberate):
- «разова оплата» for ad hoc — the term fixed in NOTES.md and used in strings_prices.
- «достовірність від 70» — same scale as the rest of the site (0–100, explained on the methodology page).
- «Слаг» on the developers page — audience is developers.
- {cu} is the country in_phrase («в Україні»), not a bare name (scripts/world_pay.py: cu()).
- press {month} is used only in positions where the nominative fits: after a dash, in brackets, in quotes («Порівняно з випуском «{prev}»»).

## FIXL 11.11.2026
Checked: new `strings_home.json` (71 keys, 4 plural categories), `strings_shell` lang_hint/lang_hint_close, D11 (`dv_p_lang`, `p_hub_na`), 7 new slugs, 49 new cities (48 NOBIL + Geneva). No D12–D15 items for uk.
Back-translation (wave 2, blind): 10 home strings (title, sub, search_none, near_err, prices_p, p_ratio, work_p, tab_ap, data_as_of, map_more) + 2 changed (dv_p_lang, p_hub_na). Meaning matched in all 12; no fixes needed.
- `home.prices_p`: pay-as-you-go = «з разовою оплатою», as fixed in NOTES.md.
- `home.p_ratio` «у {x} раза дорожче, ніж удома» — works for fractions («у 2,3 раза»).
- `home.tab_ap` «Азія і Тихий океан» — shorter than «Азійсько-Тихоокеанський регіон» for a tab.
Cities: Swedish names transcribed as in the file (Лінчепінг, Єнчепінг, Вестерос): ö→е, å→о, y→ю, k/sk before front vowels → ч/ш, h → г (Ганінге, Гудіксвалль, Оскарсгамн, Тролльгеттан). Locative written by hand (-берг → -берзі, -га → -зі, -а → -і; names in -е/-о/-ю/-є indeclinable); «в» before a vowel, «у» before a consonant.
Open: Nässjö = «Несше» with safe «у місті Несше» (decl_ok 0) — pronunciation [nɛʃøː], native check welcome; Skien = «Шієн».
D12 grep: no historical/irredentist exonyms of foreign towns found that need changing. Kept as established Ukrainian forms: Білосток, Пряшів (Prešov — traditional Ukrainian name, still in use; switch to «Прешов» if Andrei wants strict local names), Вроцлав, Гданськ.
