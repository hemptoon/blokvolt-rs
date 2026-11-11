# R-TR — вычитка турецкого (10.11.2026)

База `origin/l-tr` (ea969d0), ветка `r-tr`. `check.py`: 0 ошибок.

## Строки (403 просмотрено, 30 исправлено)
- Падеж перед существительным: `{country_u}` даёт «Almanya'da»; в определительной позиции нужен «-ki» → `{country_u}ki` («Almanya'daki şarj istasyonları»). 13 шаблонов: pages t_country, d_country, d_network, dataset_name, t_network, to_country; prices t_country, d_country, t_net, d_net, h_c_index, more_stations. «-ki» после местного падежа верен для любой формы in_phrase, включая «X şehrinde».
- Термины: legend «Açıklama» → «Gösterge» (стандарт для карт); crumbs «İçerik haritası» (= sitemap) → «Sayfa yolu».
- Естественность: net_none; about_p «Ücretli yerleşim» → «Ücretli listeleme yapılmaz»; p_multi переписан без «… kadarı» (читалось как «примерно»).
- Согласованность: report_map ссылается на кнопку «Hata bildirin» (как в map.rep); «ad-hoc» → «ad hoc» везде.
- Длина (≤ EN×1,4): c_price «Fiyat (ad hoc)», plan_adhoc «Ad hoc», pr_home/pr_street «Ev şarj cihazı (yok)» (+ кавычки в profiles_note), st_dc50/st_hpc короче. Остались длиннее из-за языка: «Harita» (Map), «Yalnızca yüksek», «Halka açık» и подобные — короче не бывает.
- Обращение «siz»/безличное везде; «biz», «7/24», рейтингов, Evolako нет.

## Страны (150)
Все `in_phrase` проверены по гармонии гласных и оглушению с учётом произношения (Liechtenstein'da, Nepal'de, …'nde после притяжательного). Ошибок нет.

## Города
- decl_ok=1 было 1 538 → стало 1 806 (+268, все из 500 крупнейших stage=month): NL по правилу написания (ij/ei/ui/eu — передний ряд, oe — задний: Goes'ta, Hoensbroek'ta), FR/GB/BE/FI/LT/DE — вручную по произношению (Metz'te, Reims'te, Caen'da, Le Havre'da, Brighton'da, Reading'de…).
- 47 из топ-500 оставлены «X şehrinde» (составные: «… an der …», «im …», скобки, редкие французские).
- Спорно: Mainz'da, Zeitz'da (по произношению «-ts» → 'ta, но в прессе «Mainz'da»). Оставлено как есть.

## Слаги
ASCII, естественные; раздела `content/com/local/tr/` нет — пересечений нет. Без изменений.

## Обратный перевод
33 изменённые строки (`BACKTRANSLATION_R.md`): смысловых расхождений 0. Замечания агента к table_note, lead_hub, pay_adhoc — старый текст L-TR, не правился (стиль, не ошибки) — на прочтение носителем перед G8.

# L2-TR — дельта ключей, тексты данных, города (11.11.2026)

Ветка `l2-tr` от `dev` (bb86f74). HOME2 в `dev` ещё нет — его ключи не переводились.

- **Ключи: 274** — strings_map +29 (28 `ci_*`, `emb_open`), новые файлы strings_pay 93, strings_press 54, strings_b2b 33, strings_embed 65. Обращение «siz»/безличное, без «biz», «7/24», Evolako.
- **texts.json**: `pay` (6 узлов AFIR) и `routes` (59 узлов — названия городов из `cities.csv`: Belgrad, Budapeşte, Sofya, Filibe (Plovdiv), Ohri…).
- **Термины (новые)**: embed → «yerleştirme / yerleştirilebilir»; issue (пресс-выпуск) → «bülten» («sayı» двусмыслен); check-in → «bildirim» (как сообщения об ошибке — на прочтение носителем); occupied → «Kullanımda»; route → «güzergâh»; toll → «otoyol ücreti», vignette → «vinyet»; roaming → «roaming uygulaması».
- `{cu}` (pay) = in_phrase, местный падеж: «{cu} elektrikli araç şarjı nasıl ödenir» → «Almanya'da …». `{lo}`/`{hi}` в f_range — тоже местный падеж; в f_home — именительный.
- `nepoznato`, `tamna` в dv_p_* — значения параметров адреса, не переводятся (как в EN).
- **Свои страны**: TR (Türkiye'de) и 28 городов TR проверены; страниц городов/сетей Турции в `pages_state.json` сейчас нет (страна ниже порога).
- **Города +48** (NOBIL: 2 NO, 46 SE) — их нет в `names/cities.csv`, взяты из `pages_state.json`; шведская орфография. decl_ok=1 у 19 с гласной на конце (Solna'da, Visby'de, Luleå'da…), у 29 — «X şehrinde», decl_ok=0. Всего 5 653, decl_ok=1 — 1 825.
- **check.py**: 8 файлов строк, разделы texts.json `pay`/`routes` по путям узлов LANG0, города из pages_state → 0 ошибок.
- **Обратный перевод** 60 случайных новых строк (независимый агент): смысловых расхождений 0. По замечаниям исправлено 10 строк: «embed», «bülten», «Kullanımda», «Diğer», «{c} km mesafe içinde» (было «на расстоянии», а не «в пределах»), f_europe, th_change, dv_f_ok.
- Длина ≤ EN×1,4: укорочены cf_copy, th_fast, th_gaps, th_car, dv_contact; длиннее остались «Kopyalandı», «Güzergâhlar», «Listelenmiş» — короче по-турецки нет.
