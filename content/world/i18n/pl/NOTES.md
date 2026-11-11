# L-PL — polski pakiet warstwy światowej (notatki)

Pool 3, 09.11.2026. Baza `g3-prices cf44fc3`, gałąź `l-pl`. Język przygotowany na zapas, **nie włączony** (włączenie po bramce G8).

## Forma i styl

- Forma bezosobowa: «Mapa łączy…», «Dane można pobrać…», «należy podać źródło», «warto sprawdzić u operatora». Bez «my/nasz/redakcja», bez «Prosimy/Dziękujemy» (to też 1. os. l.mn.). Bez zwracania się na «ty»; tryb rozkazujący tylko w etykietach przycisków i linków («Otwórz mapę», «Zgłoś błąd», «Pobierz dane», «Przeciągnij znacznik…») — tak jak w polskich interfejsach.
- `r_ok` (mapa): «Zgłoszenie przyjęte.» zamiast «Dziękujemy».
- Procent: `"{x}%"` bez spacji (polska norma typograficzna); EN ma «10 %», w PL — «10%».
- Liczby dla K8: separator dziesiętny `,`, tysiące — spacja nierozdzielająca (`1 234,5`). Daty: `9.11.2026` / `9 listopada 2026`.
- Cudzysłowy w tekście: „…”.

## Terminy (spójne we wszystkich plikach)

stacja ładowania (charging station) · punkt ładowania (charging point / charger na mapie) · ładowarka (urządzenie, «charger» w tabelach) · lokalizacja ładowania (charging location) · sieć ładowania / operator · złącze · moc · wiarygodność danych (reliability) · otwarte dane · ad hoc (bez umowy) · abonament (plan/subscription) · opłata za postój · prąd w domu / prąd dla gospodarstw domowych · indeks cen · EBC (ECB).
Glossary `pl` (Stacja ładowania, Ładowarka…) zastosowany.

## Plurale (CLDR pl: one, few, many, other)

- Obiekty `{one, few, many, other}`; `other` = ułamki (dopełniacz l.poj.: «1,5 lokalizacji»).
- **Kontekst przypadka:** `pl_cc` (strings_shell, «Jedna mapa: {n} w {c}») oraz `pl_city_in`, `pl_country_in` (strings_pages, po «w») mają formy **miejscownika**: kraju/krajach, mieście/miastach. Pozostałe — mianownik/dopełniacz liczebnikowy.
- `p_gnet` — «Sieć {net} jest obecna w {n_countries}.» (dodane «Sieć», bo rodzaj nazw sieci jest nieznany).

## Plejsholdery — świadome odstępstwa od EN (dla K8)

- `d_city`, `t_city`, `t_city_cc`: EN «in {city}» → PL `{city_u}` (fraza z `cities.csv/in_phrase`: «w Monachium», «w mieście X»). Tak samo jak SR/RU. `check.py` dopuszcza zamianę `{city}`→`{city_u}`/`{city_v}` i `{country}`→`{country_u}`.
- **world_prices.py `cu()`** zwraca dziś tylko EN/`sr_u`/`ru_v` — dla PL musi czytać `i18n/pl/countries.csv:in_phrase` (zadanie K8). Wszystkie `{country_u}` w PL zakładają frazę z przyimkiem: «w Niemczech», «na Węgrzech», «we Francji».
- `lead_hub` (ceny): «{nets} sieci w {countries} krajach» — formy stałe, poprawne dla każdej liczby poza 1 (w praktyce zawsze > 10). Jeśli K8 przepuści tu `pn()`, przejść na plurale.

## Kraje (`countries.csv`)

- `name` z CLDR (`names/countries.csv: name_pl`), poza: HK «Hongkong», MO «Makau», MM «Mjanma» (bez nawiasów CLDR), PS «Palestyna» — w kolumnie `note`.
- `in_phrase`: «w/we/na» + miejscownik wg uzusu KSNG: na Węgrzech, na Słowacji, na Litwie, na Łotwie, na Ukrainie, na Białorusi, na Cyprze, na Malcie, na Islandii, na Kubie, na Tajwanie, na Filipinach, na Sri Lance, na Dominikanie; we Francji, we Włoszech.
- Slug kraju: ASCII z nazwy PL (`niemcy`, `wegry`, `wielka-brytania`), unikalne.

## Adresy (`slugs.json`)

`/pl/`, `/pl/mapa/`, `/pl/stacje-ladowania/`, `siec`, `o-danych`, `pobierz`, `/pl/sieci-ladowania/`, `/pl/ceny-ladowania/`, `/pl/o-serwisie/` (bezosobowo, bez «o-nas»), `/pl/zrodla/`, `/pl/metodologia/`.

## texts.json

- `about_data`, `download` — przetłumaczona proza; nazwy pól (`pid`, `lat`…), licencje, URL, zakresy liczb bez zmian.
- `sources_pages` — przetłumaczony tylko opisowy fragment pola `licence`; `name`, `url`, `licence_url`, `attribution`, `kind` jak w EN (atrybucja to wymóg licencji). Nazwa źródła «BlokVolt own check» została po angielsku, a w `conf_rows` jest «własna weryfikacja BlokVolt» — do decyzji, czy tłumaczyć nazwy źródeł.
- Linia atrybucji OSM w `about_data` («© OpenStreetMap contributors») — po angielsku; oficjalna polska forma OSM to «© autorzy OpenStreetMap». W `strings_map.ch_ft_data` użyto «© współtwórcy OpenStreetMap». Do ujednolicenia przy włączeniu.

## Miasta (`cities.csv`)

Wszystkie 5605 wierszy, kolejność jak w `names/cities.csv`. `decl_ok=1`: 3086 (month 1426, quarter 1616, balkan 44), `decl_ok=0`: 2519; egzonimów 210 — «w mieście X».
- 22 miasta PL — pełna odmiana z diakrytykami (we Wrocławiu, w Białymstoku, w Ostrowie Wielkopolskim).
- Egzonimy KSNG: Monachium, Kolonia, Lipsk, Drezno, Norymberga, Hanower, Akwizgran, Wiedeń, Zurych, Mediolan, Turyn, Neapol, Wenecja, Trydent, Marsylia, Bruksela, Antwerpia, Haga, Kopenhaga, Sztokholm, Londyn, Lizbona, Sewilla, Walencja, Ateny, Korynt, Janina, Stambuł, Lwów, Kijów, Charków, Łuck, Brześć, Nowy Sad, Belgrad, Zagrzeb, Lublana, Nowy Jork, Meksyk, Tokio…
- Homonimy w USA/CA (London ON, Venice FL, Athens GA) — bez egzonimu, nazwa angielska.
- Nazwy obce nieodmienne lub odmieniane wg uzusu: «w Reims», «w Bergen», «w Linköpingu», «w Aalborgu», «w Nyonie». Spór: część drobnych nazw angielskich/holenderskich ma `decl_ok=1` w formie nieodmiennej («w Dover», «w Assen») — gramatycznie dopuszczalne.
- Południowy Tyrol: nazwa włoska (Appiano sulla Strada del Vino, Bressanone) zamiast niemieckiej z `name_local` — do decyzji.
- Do sprawdzenia: francuskie nazwy nieodmienne («w Agen», «w Rodez», ~90), czeskie/słowackie -ov → -ovie («w Trutnovie»), litewskie egzonimy historyczne (Janów, Uciana, Wiłkomierz), «w Münsterze», «w Leicesterze». Sankt Petersburg wg KSNG.
- Nazwy chińskie/tureckie bez pewnej odmiany → «w mieście X».

## Kontrola wsteczna

Tłumaczenie wsteczne 60 losowych ciągów (osobny agent, najpierw na ślepo PL→EN, potem porównanie z EN): **53 ok, 5 drobnych, 2 poważne**. Wszystkie poprawione:
- `d_city` `{city_u}` zamiast `{city}` — celowe (patrz «Plejsholdery»), nie błąd.
- `about_p` — było «Andrieja i Danię» (zdrobnienie). Teraz: «Prowadzą go założyciele, Andrei i Danila, w Nowym Sadzie w Serbii»; «serwis informacyjny» → «niezależne źródło informacji»; «rankingów» → «ocen».
- `r_ok` — «Dziękujemy» (1. os. l.mn.) → «Zgłoszenie przyjęte.»; tak samo `data_err` «Prosimy…» → «Można spróbować później.»
- `mini_alt`, `p0`, `p6`, `p7` — «moc nieznana» → «moc niepodana» (EN «not stated»); `t_unk` (mapa) zostaje «Moc nieznana» (EN «unknown»).
- `m2` (ceny) — «wchodzi do DC» → «jest uwzględniana w DC i w HPC»; `map_p` — «z filtrami według mocy…».
- `pl_place` — próba brała tylko formę `many`; obiekt ma one/few/many/other, ok.

## L2-PL (11.11.2026) — nowe pliki i sekcje

- Dodano `strings_pay`, `strings_press`, `strings_b2b`, `strings_embed` i 29 kluczy `strings_map` (`ci_*` z G6, `emb_open`): 274 klucze. Bez pluralów (EN nie ma `|` w tych plikach).
- `texts.json`: sekcje `pay` (6 punktów AFIR) i `routes` (59 nazw miast postojów, nazwy jak w `cities.csv`: Belgrad, Zagrzeb, Lublana, Budapeszt, Płowdiw, Szybenik, Ochryda, Plewen, Wielkie Tyrnowo, Sybin) w formacie LANG0 (`a.b[i].c` → tekst). Dodano też nowe źródło `sources_pages.nobil` (pola jak w EN).
- **Kontekst plejsholderów:** `{cu}` (pay) i `{lo}`/`{hi}` w `f_range` (press) — fraza z przyimkiem („w Niemczech”); `{name}` — mianownik, dlatego `afir_eu`/`afir_non`/`conn_lnk` mają konstrukcję z myślnikiem („{name} — państwo członkowskie UE…”), bez uzgadniania czasownika (Niemcy/Czechy to l.mn.). `{a}`, `{b}` (trasy) — mianownik: „{a} — {b} samochodem elektrycznym”. `{via}` — lista po dwukropku („przez: …”). `{month}` — mianownik („— {month}”). `{n}` w `f_checkins` — po dwukropku, bez odmiany rzeczownika.
- **Dla LANG0/K8:** `world_press.py` ma na sztywno teksty faktów tylko dla de/fr (`FACTS_DE_FR`) i `Names.in_()` bez gałęzi pl — dla PL musi brać `strings_press` i `countries.csv:in_phrase`. Tak samo `cu()` w `world_pay.py`.
- Termin: coverage aplikacji = „lista krajów / kraje obsługiwane”, coverage danych (B2B) = „pokrycie” — nie „zasięg” (kojarzy się z zasięgiem auta).
- Kraj własny: PL. Wszystkie 9 miast PL z `pages_state.json` są w `cities.csv` z pełną odmianą (we Wrocławiu, w Białymstoku, w Łodzi…); nowych miast PL brak. 48 miast NOBIL (SE 46, NO 2) nie ma jeszcze w `names/cities.csv` — to nie rynek PL, w PL będą tylko na stronach EN-fallback.

## FIXL (11.11.2026)

- Slugi (F5): `/pl/jak-placic/`, `/pl/trasy/`, `/pl/dla-mediow/`, `/pl/dane-dla-firm/`, `/pl/embed/mapa/`, `/pl/mapa-na-strone/`,
  `/pl/dla-programistow/`.
- Strona główna (F3): "charging place" = lokalizacja ładowania; `pl_countries` w mianowniku/dopełniaczu liczebnikowym
  (kraj/kraje/krajów/kraju), nie w miejscowniku jak `pl_cc`; tytuł SEO z «mapa ładowarek».
- D12: nazwy historyczne małych miast litewskich i Strzałów/Gryfia → nazwy urzędowe (lista w REVIEW.md).
- name_nom nie jest potrzebne (brak rodzajników); check.py dopuszcza `{name_nom}` zamiast `{name}` dla zgodności.
- Miasta: 48 NOBIL — -köping/-berg/-borg/-holm odmieniane (w Nyköpingu, w Sundbybergu, w Katrineholmie), -å nieodmienne
  (w Luleå, jak w Umeå), reszta «w mieście X» (decl_ok=0); Genewa — «w Genewie».
- FIXL2: +821 cities from names/cities_extra.csv (own market 64)
