# Translating www.blokvolt.rs (Serbian → English, Serbian → Russian)

The Serbian site is the original. English and Russian pages are generated from it by
`scripts/i18n.py`; this folder holds the translation memory: `en.json` and `ru.json`,
`{Serbian segment: translation}`. A segment is the inner HTML of one element with running text
(a paragraph, a table cell, a heading, a menu label), or a plain string (title, description,
attribute, JSON value). Readers: people living in Serbia who do not read Serbian well — expats,
relocated Russians, Ukrainians, Belarusians — and people outside Serbia looking at the market.

## Hard rules (a translation that breaks these is rejected by the checker)

1. **Keep every tag and attribute exactly as in the source**: same tags, same `href`, `class`,
   `rel`, `id`, `data-*` values, same count. Only the text between tags is translated. You may move
   an inline tag within the sentence when the word order needs it, never drop or add one.
2. **Keep placeholders exactly**: `⟦0⟧`, `⟦1⟧` … stand for numbers (dates, prices, decimals). Each
   one must appear in the translation exactly as many times as in the source. Do not write the
   number yourself. `{kwh}`, `{x}`, `{q}`, `{n}` are placeholders for JavaScript — keep them too.
3. **Keep HTML entities as entities**: `&amp;` stays `&amp;` (Charge&amp;GO), `&lt;` stays `&lt;`.
4. **Numbers that are written out stay as written** (Serbian format: `1.200 kWh`, `7,4 kW`,
   `20 %`). Do not convert decimal commas or thousand dots. Integers stay as they are.
5. **Never translate proper names**: companies (Elektronapon, Charge&GO, JP „Putevi Srbije“ → only
   the quotes change), brands and models (ABB Terra AC W22-T-R-C-0), apps, websites, e-mails,
   phone numbers, product codes, law and standard numbers (SRPS HD 60364-6, čl. 210v → see below).
   Company names stay in Latin script in Russian too.
6. One segment in, one segment out. No notes, no alternatives, no quotes around the whole result.

## Voice

Plain, factual, calm — like a good reference site. No marketing, no exclamation marks, no
"we are proud". Address the reader politely: EN "you"; RU «вы» with a lowercase в. Keep sentences
roughly as long as the Serbian ones; do not add explanations the Serbian text does not have. When
a Serbian term has no exact equivalent, translate the meaning and keep the Serbian word in brackets
the first time it matters, e.g. EN "residents' assembly (skupština)", RU «собрание жильцов
(скупштина)» — only where the Serbian term itself is the subject (e.g. the guide about skupština).

Quotes copied from company websites („…“) are translated too, keeping quotation marks:
EN “…”, RU «…». Serbian „…“ must not survive in EN or RU text.

## Terminology (use exactly)

| Serbian | English | Russian |
|---|---|---|
| punjač (kućni) | (home) charger | зарядное устройство; in short labels «зарядка» |
| javni punjač | public charger | публичная зарядка / зарядная станция |
| wallbox | wallbox | wallbox (настенная станция) |
| ugradnja / montaža | installation | установка / монтаж |
| firma / firme | company / companies | компания / компании |
| registar firmi | company register | реестр компаний |
| prodavac, prodavnica, web-shop | seller, store, web shop | продавец, магазин, интернет-магазин |
| distributer brenda | brand distributor | дистрибьютор бренда |
| električar | electrician | электрик |
| solarni integrator | solar integrator | интегратор солнечных станций |
| javna cena / na upit | public price / on request | публичная цена / по запросу |
| Ne pominje se | Not mentioned | Не упоминается |
| Da / Ne | Yes / No | Да / Нет |
| provereno 22.09.2026 | checked … | проверено … |
| pokrivenost | coverage | география |
| brojilo, MID brojilo | meter, MID-certified meter | счётчик, счётчик с сертификатом MID |
| obračun (struje) po stanu | per-flat billing | расчёт по квартирам |
| zajednička struja / zajedničko brojilo | shared (common-area) electricity / shared meter | общедомовое электричество / общий счётчик |
| skupština stanara / stambene zajednice | residents' assembly | собрание жильцов |
| stambena zajednica | homeowners' association | жилищное сообщество (stambena zajednica) |
| upravnik | building manager | управляющий (upravnik) |
| saglasnost skupštine | assembly consent | согласие собрания жильцов |
| atest | test certificate (atest) | атест (протокол испытаний) |
| izveštaj o ispitivanju | test report | протокол испытаний |
| FID (zaštitni uređaj diferencijalne struje) | RCD | УЗО |
| FID tip A / tip B | type A RCD / type B RCD | УЗО типа A / типа B |
| osigurač | circuit breaker / fuse | автомат / предохранитель |
| razvodna tabla / ormar | distribution board | электрощит |
| zaseban strujni krug / namenska linija | dedicated circuit | отдельная линия |
| odobrena snaga | approved (contracted) power | разрешённая мощность |
| EPS, Elektrodistribucija Srbije (EDS) | EPS, Elektrodistribucija Srbije (the grid operator) | EPS, Elektrodistribucija Srbije (сетевой оператор) |
| niža / viša tarifa | low (night) / high (day) tariff | низкий (ночной) / высокий (дневной) тариф |
| zelena / plava / crvena zona | green / blue / red zone | зелёная / синяя / красная зона |
| PDV, akciza | VAT, excise duty | НДС, акциз |
| RSD, dinara | RSD, dinars | RSD, динаров |
| subvencija | subsidy | субсидия |
| uvoznik | importer | импортёр |
| autoodgovornost (AO) / kasko | third-party liability / comprehensive (kasko) | ОСАГО / каско |
| putarina | motorway toll | плата за проезд |
| punjenje po minutu / po kWh | per-minute / per-kWh charging | тарификация за минуту / за кВт·ч |
| naknada za zauzeće | idle fee | плата за простой |
| roming | roaming | роуминг |
| aplikacija | app | приложение |
| račun | receipt (charging) / bill (electricity) | чек / счёт |
| snimak ekrana redakcije | editorial screenshot | скриншот редакции |
| redakcija | the editors | редакция |
| vodič / vodiči | guide / guides | гайд / гайды |
| naša ponuda | our offer | наше предложение |
| Zakon o energetici, čl. 210v | Energy Law, Article 210v | Закон об энергетике, ст. 210v |
| „Sl. glasnik RS“, br. 31/2024 | Official Gazette of RS No. 31/2024 | «Службени гласник РС» № 31/2024 |
| Pravilnik | Rulebook (regulation) | правилник (подзаконный акт) |
| kW, kWh | kW, kWh | кВт, кВт·ч |
| JP „Putevi Srbije“ | JP “Putevi Srbije” | JP «Putevi Srbije» |

Package names of the offer listed as "naša ponuda" follow that company's own EN/RU site:
START and WALLBOX stay as they are; ZGRADA → EN BUILDING / RU ДОМ; PRETPLATA → EN SUBSCRIPTION /
RU ПОДПИСКА (upper case where the source is upper case).

Place names: Beograd → Belgrade / Белград; Novi Sad → Novi Sad / Нови-Сад; Niš → Niš / Ниш;
Subotica / Суботица; Čačak / Чачак; Kragujevac / Крагуевац; Šabac / Шабац; Sombor / Сомбор;
Pančevo / Панчево; Zrenjanin / Зренянин; Novi Beograd → New Belgrade / Нови-Београд;
Zemun / Земун; Vojvodina / Воеводина; Srbija → Serbia / Сербия; Crna Gora → Montenegro /
Черногория; BiH → Bosnia and Herzegovina / Босния и Герцеговина; Severna Makedonija → North
Macedonia / Северная Македония; Hrvatska → Croatia / Хорватия; Mađarska → Hungary / Венгрия.
Inside company names and addresses keep the Serbian spelling.

Russian specifics: «ё» where it matters (счёт, счётчик, расчёт); dash with spaces « — »;
decimal comma as in the source; «с НДС» / «без НДС»; «кВт·ч» with a middle dot.

The already translated menu, footer and table labels in `en.json` / `ru.json` are the reference for
terminology — read them before translating and stay consistent with them.
