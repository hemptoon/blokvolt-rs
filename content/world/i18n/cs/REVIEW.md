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
