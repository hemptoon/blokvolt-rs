# L-HR — hrvatski (hr), pool 3, 09.11.2026

## Oblik obraćanja i ton
- Bezlično, kao EN. Čitatelj se oslovljava množinom/učtivo („Pokušajte ponovno”, „Preuzmite”), bez „mi/naš/redakcija”.
- Hrvatski standard: ijekavica, „karta” (ne mapa), „točka”, „tisuća”, „tjedno”, „poslužitelj”, „preglednik”, „poveznica”, „izbornik”.
- Navodnici „…”; postotak s razmakom: `{x} %`.

## Termini (glossary.csv, stupac hr)
- charging station → punionica (objekt na karti, naslovi); charger → punjač (uređaj, „brzi DC punjači”); charging point → mjesto za punjenje; location → lokacija.
- connector → priključak (ne „konektor”); network → mreža; operator → operater; report an error → Prijavite grešku.
- country → **zemlja** (glossary), i u cijenama i u ljusci; agent je prvo stavio „država”, ujednačeno na „zemlja”.
- ad hoc → „bez ugovora”; plan → „pretplata”; ECB → **ESB** (hrvatska kratica).
- confidence → „pouzdanost podataka”, ocjena → „ocjena pouzdanosti” (odnosi se na podatke, ne na mrežu).

## Plurali
- CLDR hr (Babel 2.18): one, few, other → objekti `{one, few, other}` za sve `pl_*`.
- `pl_city_in` / `pl_country_in`: oblik iza „u” + broj: one = lokativ (u 1 gradu / zemlji), few/other = genitiv (u 3 grada, u 5 gradova). Standard bi za 2–4 tražio „u dvama gradovima”; „u 3 grada” je uobičajeni razgovorni oblik — prihvatljivo za sučelje.
- Nizovi s `{n}` bez oblika: „Izvori: {n}”, „Provjereno mreža: {n}”, „Cijene mreža … (broj mreža: {n})”.

## Plaseholderi koji traže pažnju (za K8)
- EN koristi `{city}` (nominativ) gdje sr ima `{city_u}`: hr slijedi EN → „u gradu {city}” (d_city, t_city, t_city_cc). Kad K8 doda `{city_u}` za sve jezike, zamijeniti „u gradu {city}” s `{city_u}`.
- `{country_u}` = `in_phrase` iz countries.csv (npr. „u Njemačkoj”, „na Islandu”).
- `{net}` ostaje nesklonjen: konstrukcija „mreže {net}” / „Mreža {net}”.

## Adrese (slugs.json) — PITANJE
- `/hr/` na blokvolt.com već zauzima lokalni odjeljak Hrvatska (content/com/local/hr: /hr/, /hr/karta/, /hr/cijene/, /hr/metodologija/ …).
- Pretpostavka: svjetski sloj na hrvatskom živi pod istim prefiksom `/hr/`, ali s putanjama koje se ne sudaraju: home `/hr/svijet/`, map `/hr/karta-svijeta/`, methodology `/hr/metodologija-podataka/`, prices `/hr/cijene-punjenja/`, hub `/hr/punionice/` itd. Provjereno protiv slugova lokalnih stranica — nema preklapanja.
- Ako Andrej želi da jezični prefiks bude `/hr/` = početna svijeta, lokalni odjeljak Hrvatske treba premjestiti — odluka za G8/K8.

## Nazivi
- countries.csv: CLDR `name_hr`; ispravljeno: HK „Hong Kong” (bilo „PUP Hong Kong Kina”), MO „Makao”, MM „Mjanmar”, PS „Palestina”. Lokativi ručno + pravilom; otoci/otočne države s „na” (na Islandu, na Malti, na Cipru, na Kubi, na Filipinima), Šri Lanka „u”.
- Slug zemlje: ASCII iz hr naziva, đ → dj (kao CYR mapa u world_pages.py): `madjarska`.
- cities.csv (sve 5 605): 
  - 95 ručnih hrvatskih egzonima/oblika (Beč, Prag, Pariz, Rim, Venecija, Firenca, Napulj, Trst, Varšava, Krakov, Budimpešta, Bukurešt, Lisabon, Kopenhagen, Ženeva, Haag, Frankfurt na Majni, Nica, Atena, Solun, Pirej, Sofija, Moskva, Kijev, Skoplje, Priština, Gdanjsk …). Njemačka, francuska, engleska imena ostaju u izvornom obliku (München, Köln, Strasbourg) — hrvatska norma.
  - 2 151 latinično ime s lokativom preuzetim iz sr_u gdje je sr ime isto kao izvorno i decl_ok_sr=1 (Berlin → u Berlinu); za višerječna strana imena izvan regije uvijek sigurna konstrukcija.
  - 3 187 sigurna konstrukcija „u gradu X”, decl_ok = 0.
  - 139 ćiriličnih/grčkih: latinica prema sr transkripciji (gotovo ista kao hrvatska) — napomena „provjeriti”; 33 azijska: EN latinizacija.
  - decl_ok = 1 ukupno 2 337.

## Kontrola
- `python3 check.py` → OK (ključevi, plaseholderi, tagovi, kategorije, slugovi, CSV).
- Povratni prijevod 60 nasumičnih nizova (zaseban agent, naslijepo) — vidi niže.

## Što ostaje
- Ručna provjera lokativa za gradove s decl_ok = 0 (njih ~3 200) — po potrebi kasnije.
- Grčki i bugarski gradovi: hrvatska transkripcija može se razlikovati u detaljima (npr. grčko „Kalamarija”).

### Povratni prijevod (60 nizova, naslijepo)
- OK 53 · MINOR 6 · MISMATCH 1. Uzorak je uzet prije zadnjih ispravaka.
- Ispravljeno: acc_restricted_customers_staff „Za goste…” → „Za kupce i zaposlenike”; src_net → „Web-stranice mreža”; table_note (jasnije „onih punjača … kojima je mreža poznata”); home_lead „{n} u {c}”; data_p „Licencija” → „Licenca”; „Prijavite pogrešku” → „Prijavite grešku” svugdje (glossary).
- p_hub „zasebne” ostavljeno (smisao isti). Puni izvještaj: bt_report.md u ~/dev/evdb/work/L-HR/.
