# R-CS — вычитка чешского (10.11.2026, пул 4)

База `origin/l-cs` (fa536d3), ветка `r-cs`. Редактор — независимая сессия.

## Строки (403 просмотрены все)
Перевод в целом чистый: грамматика, обращение (безлично / vy), термины по NOTES L-CS. Исправлено 10:
- `t_city`, `t_city_cc`, `d_city` — «– {city},» → `{city_u}` (раздел 5: склоняемые формы разрешены): «Nabíjecí stanice pro elektromobily v Mnichově (Německo)»; для `decl_ok=0` — «ve městě X (Země)».
- `p_multi` — «U {pct_multi} míst existuje potvrzení…» → «{pct_multi} míst je potvrzeno dvěma nebo více zdroji».
- `d_country` — «s tarifem» → «s předplatným» (единообразно с `plan_sub`, `d_net`, `pay_sub`).
- `t_net`, `n_station_page` — «{net}» → «sítě {net}» (как в `t_gnet`, `d_network`).
- `too_few` — «viz stránku» → «viz stránka» (норма: viz + им. п.).
- `lead_hub` — «u sítí (počet: …) v zemích (počet: …)» → «jednotlivých sítí podle zemí (sítě: {nets}, země: {countries})».
- `h_more` — «Další informace o nabíjení…» → «Více o nabíjení {country_u}» (короче).
- `check.py`: `{city_u}`/`{country_u}` засчитываются вместо `{city}`/`{country}`.

Длина кнопок: превышение EN×1,4 только у `pr_mixed` «Kombinace» (подпись профиля, не кнопка) и у неклавишных строк — оставлено.

## Страны (150)
Все `name` и `in_phrase` верны (v/ve/na + lokál). SJ «na Špicberkách a Jan Mayenu», TO «na Tonze», WS «na Samoi» — проверены, пометки «ověřit» сняты.

## Города
- 63 города CZ — все формы верны, ничего не менял.
- 500 первых `stage = month` (порядок файла; в `places-*.json` нет числа мест, только bbox): 61 исправлено → `decl_ok=1`. Braunschweig вместо архаичного «Brunšvik»; Reims → «Remeš / v Remeši»; склонение для крупных DE/NL/GB/FR/ES/FI (v Duisburgu, v Bochumi, v Münsteru, v Bredě, v Goudě, ve Venlu, v Brightonu, v Toulouse, v Palmě, v Klaipėdě…). Полный список — `R-CS/city_fixes.json` на маке.
- 88 прочих `decl_ok=1` (Štýrský Hradec, Vratislav, Curych, Lutych…) — верны.
- Итого `decl_ok=1`: 218 → 278.

## Спорное
- `p_city_cmp`: «v průměru za zemi {country_name}» — в движке нет `{country_u}` для этой строки; формально верно, звучит чуть канцелярски.
- `home_lead`: «{n}, {c}» (без предлога: «ve 150 zemích» требует v/ve по числу).
- Районы Лондона/Гааги как «города» (Earlsfield, Ypenburg) — «ve městě X», правится в `names/cities.csv`.
- Не менял: Metz/Mety, Patras/Patra, Le Havre — экзонимы редкие, оставлена безопасная форма.

## Слаги
ASCII, естественные, пересечений нет (`content/com/local/` чешского раздела не имеет).

`python3 content/world/i18n/cs/check.py` → OK — 0 errors.

## L2-CS (11.11.2026) — добор ключей до мотора LANG0
- Добавлено 274 ключа: strings_map +29 (28 `ci_*` и `emb_open`), новые strings_pay (93), strings_press (54), strings_b2b (33), strings_embed (65). Ключей HOME2 в `dev` пока нет.
- texts.json: разделы `pay` (6 пунктов AFIR) и `routes` (59 названий городов; экзонимы взяты из `cities.csv`: Salcburk, Lublaň, Záhřeb, Budapešť, Bělehrad, Sofie, Štýrský Hradec).
- `{cu}`, `{lo}`, `{hi}` — это `in_phrase` («v Německu»); `{name}`, `{a}`, `{b}`, `{month}` — именительный, поэтому в шаблонах стоят тире и двоеточие, а не предлоги с падежом.
- Без «my»: `r_ok` «Děkujeme» → «Díky»; в `ci_thanks`, `m_ok` тоже «Díky».
- Тире: 23 « — » → « – » (чешская норма).
- Город: «ve Žďáru» → «ve Žďáře nad Sázavou» (норма ÚJČ). Все 63 города CZ и 19 городских страниц CZ из pages_state на месте.
- check.py проверяет все 8 файлов и разделы `pay`/`routes` → 0 ошибок.
- Обратный перевод вслепую, 60 случайных новых строк: смысловых расхождений 0, 8 флагов, 4 исправления (`th_trip`, `stops_note`, `lic_p`, `desc` в b2b). Не исправлено: `ci_u_min` «minutu» (стоит после «Cena za» — винительный здесь верный), `cov_yes`/`cov_no` «Uvedena»/«Neuvedena» (речь о стране — женский род), `ci_err` «Odpověď» (так в интерфейсе отметок), «váhy» в press. Файл — `BACKTRANSLATION_L2.tsv`.

## FIXL 11.11.2026
- Проверено: новый `strings_home.json` (71 ключ, pl_* = one/few/many/other), `lang_hint`/`lang_hint_close`, D11 (`dv_p_lang`, `p_hub_na`), 7 новых слагов, +49 городов.
- Обратный перевод (волна 2): 10 строк home (title, desc, sub, near_err, search_none, prices_p, p_src, work_p, trust_p, org_desc) + 4 изменённых (dv_p_lang, p_hub_na, lang_hint, lang_hint_close). Смысл совпал 14/14.
- Исправлено: `prices_p` «Eura za kWh» → «Ceny v eurech za kWh včetně DPH»; `near_err` «posuňte ji na své místo» (двусмысленно) → «posuňte ji tam, kde jste».
- D12: исторических/ирредентистских экзонимов не найдено. Отличающиеся от местных формы (Vratislav, Štětín, Lvov, Budyšín, Zhořelec, Žitava, Kostnice, Řezno, Cáchy, Linec, Lutych, Lovaň, Soluň, Petrohrad…) — живые стандартные чешские экзонимы, оставлены. Braunschweig уже в местной форме.
- Шведские/норвежские города NOBIL — «ve městě X», decl_ok 0 (как Linköping, Västerås, Umeå в файле); Женева — «Ženeva», «v Ženevě».
- Сомнения: «Funguje nabíječka?» (EN «Is it working?»), «Cesty autem» для Road trips.
