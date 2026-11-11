# L-HU — magyar lokalizáció: заметки (09.11.2026)

## Форма обращения
Безлично; где обращение неизбежно — вежливое «Ön» (Próbálja újra, Ellenőrizze…). Нигде нет «mi/nálunk/rólunk»: `ft_about` = «Névjegy» (не «Rólunk»), `how` = «A számítás módja».

## Грамматика, важное для K8
- Венгерский: после числа существительное всегда в ед. ч. («12 város»), CLDR hu = one/other, обе формы одинаковые.
- Падеж места — суффикс, поэтому `{country_u}`/`{city_u}` = готовое слово с суффиксом: «Németországban», «Magyarországon», «az Egyesült Államokban», «Budapesten», «Pécsett».
- `pl_*_in` и `pl_cc` — в форме места (-ban/-ben): «12 városban», «120 országban». В EN `pl_cc` нейтральный, в HU он стоит в `home_lead` после «{n}» как «в N странах» — поэтому locative.
- `t_city`, `t_city_cc`, `d_city` используют `{city_u}` вместо EN `{city}` (как sr/ru делают с `{city_u}`/`{city_v}`). check.py это разрешает явно.
- `fallback_u` = «{x} városában» («в городе X») — безопасная форма без склонения названия, когда `decl_ok = 0`.
- Сеть с артиклем: «A(z) {net}» — артикль a/az зависит от первой буквы, заранее неизвестной; «A(z)» — стандартная венгерская запись для подстановок.
- Ценовой `h_more`: «Továbbiak {country_u}» — стилистически слабее остальных; лучше бы отдельный ключ без падежа.

## Термины (glossary без колонки hu)
töltőállomás — станция; töltőhely — место/локация; töltőpont — точка зарядки; töltő — зарядка; gyorstöltő — быстрая (DC); csatlakozó — разъём; hálózat — сеть; megbízhatóság — надёжность данных; nyílt adatok — открытые данные; eseti ár — ad hoc; előfizetés — план/подписка; háztartási villamos energia — бытовое электричество; EKB — ECB.

## Названия
- Страны: CLDR `name_hu`, правки: Hongkong, Makaó (без «KKT»), Feröer, Palesztina, Eszvatini (не Szváziföld). Слаги — ASCII от венгерского названия.
- Города: 5605 из 5605. decl_ok=1 — 2305: 161 вручную (32 венгерских с правильными -on/-en/-ön/-ett, экзонимы: Bécs, Prága, Varsó, Párizs, Milánó, Brüsszel…), 2144 автоматически (-ban/-ben по последней гласной, удлинение a/e/o; только страны с фонетической латиницей: DE AT CH IT ES PT PL CZ SK HR SI RS BA ME RO FI EE LV LT TR NO SE DK NL IS). Остальные 3300 (FR, GB, US, BE, IE, CA, AU…, нелатинские) — decl_ok=0, «X városában».
- **Спорное (вопрос Андрею):** для городов бывшего Венгерского королевства взяты венгерские исторические названия — Pozsony, Kassa, Kolozsvár, Temesvár, Nagyvárad, Újvidék, Szabadka, Zombor, Pancsova, Nagybecskerek, Eszék, Varasd, Dunaszerdahely, Nyitra… Так пишет венгерская пресса и MTA; но это может читаться как ненейтральное. Альтернатива — местное название (Bratislava, Cluj-Napoca, Novi Sad). Сменить — одна правка в `EX` скрипта.
- Авто-склонение не проверено глазами целиком: проверены выборки (~60 шт.). Риски — немые буквы в CH-французских и отдельных NL/DE названиях.

## Проверки
- `python3 content/world/i18n/hu/check.py` → OK.
- Обратный перевод 60 случайных строк независимым агентом: 60/60 по смыслу, 0 расхождений (`backtranslation.md`).

## Не сделано
- Носитель языка не вычитывал. texts.json переведён отдельным агентом и проверен структурно + выборочно.

## L2-HU (11.11.2026)
- +274 ключа: strings_map +29 (ci_*, emb_open), новые strings_pay 93, strings_press 54, strings_b2b 33, strings_embed 65. HOME2 в dev ещё не было — его ключей нет.
- texts.json: `pay` (6 пунктов AFIR) и `routes` (59 узлов `routes[i].stops[j].city`) в формате LANG0. Названия остановок взяты из hu/cities.csv, чтобы совпадать со страницами городов (Belgrád, Szófia, Zágráb; Čakovec → Csáktornya, Sibiu → Nagyszeben — тот же открытый вопрос об исторических названиях).
- **Для LANG0 — какие формы ждут плейсхолдеры:** `{cu}` (t_pay_country, d_pay_country) и `{lo}`/`{hi}` в `f_range` — форма места = `in_phrase` из countries.csv («Németországban»). `{name}` в pay и `{lo}`/`{hi}` в `f_home` — именительный; фразы построены так, чтобы не требовать артикля a/az («Ez az ország ({name}) …», «Töltőállomások — {name}»). `{month}`, `{prev}`, `{date}`, `{fx}`, `{layer}` стоят без падежных суффиксов (после двоеточия или в скобках) — подойдёт любой формат даты/месяца.
- Название индекса: «Európai elektromosautó-töltési árindex». «Sajtónak» = For media. «szerkesztőségi» не используется (запрещённое слово в check.py) — «sajtótartalom».
- check.py: все 8 файлов + texts.json about_data, download, pay, routes (пути узлов сверяются с pay.json/routes.json) → OK.

## FIXL (11.11.2026)
- strings_home.json (71 kulcs); lang_hint „Ez az oldal magyarul is elérhető”, lang_hint_close „Bezárás”.
- Slugok: /hu/fizetesi-modok/ /hu/utvonalak/ /hu/sajtonak/ /hu/adatok-cegeknek/ /hu/embed/terkep/ /hu/terkep-a-weboldalara/ /hu/fejlesztoknek/.
- name_nom: nem használjuk (D14 csak de fr it es pt el); a check.py megengedi.
- D12 (végleges): a volt Magyar Királyság más országbeli városai helyi hivatalos névvel (Bratislava, Košice, Cluj-Napoca, Timișoara, Novi Sad, Subotica, Osijek, Čakovec, Sibiu …, 32 sor) — a fenti „спорное” kérdés lezárva. Bevett semleges exonimák maradnak (Bécs, Prága, Belgrád, Zágráb, Bukarest).
- cities.csv: +48 NOBIL (auto -ban/-ben) + Genf „Genfben”.
