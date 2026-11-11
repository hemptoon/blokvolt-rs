# R-BS — вычитка боснийского (bs), 10.11.2026, 00:15–00:50

База `origin/l-bs` (53b1878), ветка `r-bs`. Редактор-носитель, независимо от L-BS.

## Исправлено
**Строки — 35 правок из 403** (все 403 прочитаны):
- Термин: «konektor» → «priključak» во всех формах (glossary.csv `bs` и раздел /ba/): 13 строк в strings + 3 в texts.json.
- Падеж/предлог: `d_city`, `t_city`, `t_city_cc` → `{city_u}` (как в SR), вместо «u gradu {city}» и «— {city}».
- Согласование: `p_hub_na` «pokriveni» → «pokrivene» (SAD и Kanada — ж. р.); `p_gnet` «{net} je prisutna» → «Mreža {net} prisutna je» (род не зависит от названия).
- Числа без форм: `lead_hub`, `c_lead`, `src_ops` → нейтральные «(ukupno: {n})», «Obuhvaćeno mreža: {nets}; zemalja: {countries}» — убирает «22 mreža / 21 zemalja».
- Естественность: `p_multi`, `p_net_share`, `chart_desc` («Stubičasti grafikon, EUR po kWh»), `chart_eur`, `n_station_page`, `th_ratio` («DC / domaćinstvo»), `th_nets` («Mreže», был ген. ед.).
- Обращение «vi» единообразно: `ch_skip` «Preskočite», `more_map` «Otvorite mapu».
- Длина: `download` «Preuzmite podatke», `acc_public_pay_at_location` «Javni, plaćanje na mjestu».

**Страны — 2 из 150:** PR «Porto Riko» → «Portoriko» (как слаг и in_phrase); GI «u Gibraltaru» → «na Gibraltaru». Остальные 148 — верны.

**Города — 124 правки:** 19 городов BiH проверены (Banja Luka → «u Banjoj Luci»); первые 500 `month` прочитаны глазами:
- 64 города переведены в склонение (`decl_ok=1`): Rotterdamu, Leipzigu, Düsseldorfu, Stuttgartu, Barceloni, Sevilli, Zaragozi, Málagi, Lyonu, Bordeauxu, Marseilleu, Zürichu, Grazu, Salzburgu, Tallinnu, Vilniusu, Wrocławu, Poznanju, Gdanjsku и др.;
- 50 немецких названий с уточнением («an der», «am», «im», «bei», «in der») — было «u Mülheimu an der Ruhr», стало безопасное «u gradu …», `decl_ok=0`;
- экзонимы: València → Valencia, Eivissa → Ibiza («na Ibizi»), Donostia / San Sebastián → San Sebastián, İstanbul → Istanbul, Tiranë → Tirana; Dublin, Bari, Cluj-Napoca, Luzern склоняются.
Итого `decl_ok=1`: 2 643 из 5 605 (было 2 634).

**Слаги:** `/bs/…` — естественно, ASCII, пересечений с /ba/ (местный раздел) и с EN/SR/RU нет. Без изменений.

**check.py:** допускает `{city_u}`/`{country_u}` вместо `{city}`/`{country}` (решение 00:12) и предупреждает о коротких строках длиннее EN × 1,4. Результат — OK, 0 ошибок; 2 предупреждения длины («Automobil», «bez mjesečne naknade») — оставлены, это ячейки таблиц, не кнопки.

**Обратный перевод:** отдельный агент, 45 изменённых строк: 42 совпадают, 3 нюанса (два исправлены: `th_ratio`, `lead_hub`; третий — `p_hub_na` «na bosanskom» — намеренно), ошибок 0.

## Спорное / оставлено
- «© OpenStreetMap contributors» в `ch_ft_data` и texts — оставлено по-английски, как в SR (каноническая атрибуция OSM).
- Латинские названия городов — в оригинале по Pravopisu (Leipzig, а не Lajpcig), как решила L-BS.
- `fast_more`, `st_countries` («zemalja sa stranicom») при 21–24 дают неточную форму — редко, оставлено.
- ~2 960 городов stage quarter/balkan вне топ-500 — не вычитаны, безопасная форма «u gradu X».

## L2-bs — обратный перевод 60 новых строк (11.11.2026)
Выборка: 60 случайных из 237 новых строк (seed 20261111; strings_pay/press/b2b/embed, ci_* + emb_open, texts.pay). Независимый агент переводил bs → EN, не видя оригиналов. 48 — смысл совпал, 12 — замечания; экавизмов и хорватизмов нет, плейсхолдеры целы.
Применено:
- `press.f_checkins` — «{n} plaćenih cijena» не согласуется с 1–4 → «Broj cijena koje su vozači … potvrdili …: {n}».
- `press.lead_issue` — «{nets} mreža u {countries} zemalja» (та же проблема, найдена при сверке с R-BS) → «(mreža: {nets}; zemalja: {countries})».
- `pay.afir_non` — «nije članica EU» (ж. р.) не подходит к Kosovo / Ujedinjeno Kraljevstvo → «nije u Evropskoj uniji».
- `press.h_charts`, `press.d_press` — «za ugradnju» читалось как монтаж → «za vašu stranicu» / «za objavu na vašoj stranici».
- `press.f_mom` — «u odnosu na period {prev}» → «u odnosu na {prev}»; `press.f_mom_n` — «DC vrijednosti» → «DC indeksa».
- `pay.cost_all` → «indeks postoji za sve zemlje na ruti»; `embed.dv_open_btn` → «Preuzimanje i opis kolona»; `embed.dv_p_lang` → «Jezik: određuje ga adresa vidžeta (EN, SR, RU)».
Не применено:
- `press.f_range` «najjeftinije {lo}» — ложная тревога: `{lo}`/`{hi}` подставляются как `names.in_()` («u Njemačkoj»), предлог уже внутри.
- `press.d_issue` «u periodu {month}» — оставлено: `month_name()` даёт именительный («oktobar 2026»), «u {month}» дал бы «u oktobar».
- `embed.cf_view` «Grad ili tačan prikaz» — как в SR, под полем есть пояснение `cf_view_help`.
