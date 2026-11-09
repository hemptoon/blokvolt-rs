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
