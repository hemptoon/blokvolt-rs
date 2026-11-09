# L-SK — slovenčina, poznámky (09.11.2026)

## Forma oslovenia
- Tlačidlá, odkazy, menu, výzvy: neurčitok („Zobraziť filtre“, „Stiahnuť údaje“, „Nájsť sieť“).
- Celé vety k čitateľovi: vykanie s malým „vy/vám“ („Skúste to neskôr“, „overte“) alebo neosobne. Bez „my/náš/redakcia“.

## Termíny (glossary.csv nemá stĺpec sk — zvolené tu, odporúčam doplniť stĺpec `sk`)
- charging station → nabíjacia stanica; charging location / location → (nabíjacie) miesto; charging point → nabíjací bod
- network → sieť; operator → prevádzkovateľ; connector → konektor; power → výkon
- ad hoc → ad hoc; subscription/plan → predplatné (v tabuľke „Tarifa“); per session → /nabíjanie; VAT → DPH
- open data → otvorené údaje; reliability → spoľahlivosť; methodology → metodika; price index → cenový index
- Úroveň spoľahlivosti „Vysoká/Stredná/Nízka“ (ženský rod k „spoľahlivosť“); ak UI píše vedľa „skóre“, zmeniť na „Vysoké/Stredné/Nízke“.

## Plurály (CLDR sk: one, few, many, other)
- one = 1, few = 2–4, many = desatinné (gen. sg.), other = 0 a 5+ (gen. pl.).
- `_in` varianty = lokál po „v“ + číslo: v 1 meste / v 3 mestách / v 1,5 mesta / v 10 mestách.

## Väzby na K8 (dôležité)
- `{country_u}` (strings_prices, strings_pages) má byť lokál s predložkou → brať z `countries.csv` stĺpec `in_phrase` („v Nemecku“, „na Slovensku“, „vo Francúzsku“). Dnes `country_u()` v `world_pages.py` pozná len en/sr/ru.
- `fallback_u` = „v meste {x}“ (ako SR/RU „u gradu“, „в городе“) — vhodné len pre mestá.
- Názvy miest v titulkoch: dvojbodková konštrukcia („Nabíjacie stanice pre elektromobily: {city}, {country}“), aby sa mesto nemuselo skloňovať. Ak K8 dodá `{city_u}` z `cities.csv/in_phrase`, dá sa prepnúť.
- Pri reťazcoch s číslom mimo pl_* sa používa neutrálne „počet: {n}“, „Zdroje: {n}“.
- Riadok atribúcie „© OpenStreetMap contributors, BlokVolt“ v texts.json ostal po anglicky (presný text na kopírovanie); v bežnom texte „© prispievatelia OpenStreetMap“.
- `strings_shell` nemá kľúč `lang_label`; v `strings_pages.lang_label` = „Slovenčina“.

## Krajiny (countries.csv)
- Názvy = CLDR (zhodné s `name_sk` v names/countries.csv); skrátené: HK „Hongkong“, MO „Macao“, MF „Svätý Martin“.
- „na Slovensku“, „na Ukrajine“, ostrovy s „na“ (na Cypre, na Malte, na Islande, na Filipínach…); „vo“ pred v/f/š-skupinami (vo Francúzsku, vo Fínsku, vo Švajčiarsku, vo Švédsku, vo Vietname, vo Venezuele).

## Mestá (cities.csv) — všetkých 5 605 riadkov
- decl_ok=1: 541 (všetky SK 18, CZ 62/63, ~230 známych miest, 161 nemeckých/holandských podľa prípony -burg/-berg → -u, -dorf/-heim/-furt/-dam/-feld/-mund → -e; poznámka „rule -x“).
- Ostatné 5 064: bezpečné „v meste X“, decl_ok=0.
- Exonymá: 113 (Viedeň, Mníchov, Kolín, Drážďany, Lipsko, Paríž, Londýn, Varšava, Budapešť, Belehrad, Ľubľana, Záhreb…). Menej bežné, ale spisovné: Brémy, Ráb, Päťkostolie, Stoličný Belehrad — na zváženie, či nepoužiť Bremen/Győr/Pécs/Székesfehérvár.
- Neisté zakončenia s decl_ok=1: v Hannoveri, v Bologni, v Šoproni, v Kieli, v Chemnitzi, v Manchestri; nesklonné: v Nice, v Toulouse, v Bordeaux, v Malmö, v Bari.
- Cyrilika → slovenská transliterácia (poznámka „translit“); grécke/čínske/arabské bez exonyma → name_en („fallback EN“).
- Pravidlo prípon beží bez kontroly jednotlivých mien — odporúčam rýchlu kontrolu riadkov „rule -“.

## Spätný preklad
- 60 náhodných reťazcov naslepo späť do EN: ok 56, minor 4, mismatch 0 → BACKTRANSLATION.md. Opravené: h_c_index → „Cenový index {country_u}“.

## Zostáva
- Natívna korektúra (slovensky hovoriaci človek) pred zapnutím jazyka po bráne G8.
- Stĺpec `sk` v glossary.csv.
