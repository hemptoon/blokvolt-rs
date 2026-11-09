# R-RO — vichitare (review) română, 10.11.2026

Bază: `origin/l-ro` (4b4698c). Ramura `r-ro`. Doar `content/world/i18n/ro/`.

## Șiruri (403 verificate)
22 de șiruri corectate:
- formulare/acord: zoom_note, conf_note, osm_fix, c_price_note („la stația”), r_type, r_need_type, crumbs („Cale de navigare”), p_gnet și d_gnet / d_network („rețeaua {net}” — numele rețelei nu are gen cunoscut), p_city_cmp, p_hub_na, h_more (era „Mai multe {country_u}”, agramatical), h_n_compare, sources_p (fără „surse: {n}” în mijlocul frazei; „{n} în total” evită „de” după 20);
- date: data_date → „Date actualizate la {d}” (ca data_from „Date la”);
- lungime butoane/cipuri (≤ EN × 1,4): c_unnamed „Stație de încărcare”, nav „Indicații”, acc_public_pay_at_location „Public, plată pe loc”, r_nije_javni „Nu e public”, lg_home „Curent acasă”, th_ratio „DC / acasă”.
Rămân mai lungi decât EN × 1,4, inevitabil (un cuvânt): Hartă/Map, Toate/All, Închideți/Close, Abonament/Plan, Mașină/Car, Ridicată/High, Scăzută/Low, Distribuiți/Share, Trimiteți/Send, Date deschise/Open data; h1 și titlurile nu sunt butoane.
Formă de adresare: verificată — imperativ de politețe peste tot, fără „noi”/„redacția”/„24/7”/„imediat”.

## Țări (150 verificate)
- IM: „pe Insula Man” (insulă → „pe”).
- US: slug `statele-unite` (era `statele-unite-ale-americii`).
- NL rămâne „Țările de Jos” (CLDR, uz oficial MAE); „Olanda” — decizia lui Andrei.

## Orașe
- Toate 11 orașe din RO (MD — 0 în set): corecte, diacritice ș/ț, `decl_ok = 1`.
- Primele 500 `stage = month` (ordinea fișierului; places-2026-11-09.json are bbox, nu număr de locații): exonime verificate. Corectate: Hannover → Hanovra, Tiranë → Tirana. Păstrate intenționat: München, Köln, Nürnberg, Zürich, Bruxelles, Sevilla, Gent, Bruges (uz românesc curent).
- `decl_ok = 1` corect pentru toate: în română numele după „în” nu se schimbă.
- De semnalat la nivelul setului (nu RO): `Kröpeliner-Tor-Vorstadt` (cartier din Rostock) apare ca oraș.

## Slug-uri
ASCII, firești, fără coliziuni: nu există `content/com/local/ro/`; prefixul `/ro/` nu e folosit de EN/SR/RU.

## Verificare
- `check.py` — 0 erori, 0 avertismente.
- Retraducere oarbă (alt agent) a celor 22 de șiruri + 4 nume: sensul coincide. Din 8 observații, 5 aplicate (data_date, r_nije_javni, nav, lg_home, p_city_cmp), 3 false (`{country_u}` conține deja prepoziția; p_hub_na e la fel în EN).
