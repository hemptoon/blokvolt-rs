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

## L2-RO — 11.11.2026 (ramura `l2-ro` de la `dev` bb86f74)
- Chei noi traduse: 274 = strings_map 29 (28 `ci_*` + `emb_open`), strings_pay 93, strings_press 54, strings_b2b 33, strings_embed 65. Chei HOME2: încă nu sunt în `dev` — rămân pentru LANGI.
- `texts.json`: secțiuni noi `pay` (6 noduri `afir.points[i]`) și `routes` (59 noduri `routes[i].stops[j].city`, numele din `cities.csv` ro), format LANG0.
- Țările proprii (RO, MD): nume, slug-uri și `in_phrase` verificate; toate 11 orașe RO corecte (din care 5 cu pagină în `pages_state.json`), MD — 0 orașe în set. Acoperire `cities.csv`: 5605/5605.
- Corectat: Veliko Tarnovo → Veliko Tărnovo (exonim românesc).
- Nu s-au adăugat: 144 de orașe noi NOBIL (SE 138, NO 6) din `pages_state.json` — lipsesc din `names/cities.csv` (doar slug ASCII, fără nume local); nu sunt țări proprii pentru ro, iar în română numele lor rămân cele locale. De adăugat după ce `names/cities.csv` le primește.
- Termeni: „semnalare” (check-in, consecvent cu „sesizare” pentru erori), „vinietă” (nu „rovinietă” — numele vinietei din România), „încorporare/încorporat” (embed), „amprentă zilnică” (daily fingerprint).
- `check.py` extins: toate 8 fișiere `strings_*` + `texts.pay` / `texts.routes` (căi existente, placeholdere, diacritice) — 0 erori, 0 avertismente.
- Retraducere oarbă (alt agent, fără EN) a 60 de șiruri noi aleatorii: sensul coincide la toate 60. 17 observații de stil; aplicate 16 (afir_src, th_cover, stops_note, viniete, th_gaps, ch_europe_d, d_issue, d_press/h_charts/charts_p/embed_code, h_data, desc, what_price, form_p, titlurile hărții încorporate, cf_light „Deschisă”, dv_balkan_p). Neaplicat: road_none „Neverificat încă” (fără substantiv de acord — corect).
- Butoane > EN × 1,4 rămase inevitabil: Funcționează/Working, Hartă/Map, Mașină/Car, Trimiteți cererea/Send request.

## FIXL 11.11.2026
- Verificat: `strings_home.json` nou (71 de chei), `lang_hint`/`lang_hint_close`, D11 (`dv_p_lang`, `p_hub_na`), 7 slug-uri noi, 49 de rânduri noi în cities.csv, D13.
- Retraducere (valul 2): 10 șiruri home (title, desc, data_as_of, search_none, p_ratio, prices_p, o_widget, trust_p, btn_near, countries_p) + cele schimbate (lang_hint, lang_hint_close, dv_p_lang, p_hub_na, NL). Divergență corectată: `btn_near` „În apropiere” („Nearby”) → „Lângă mine” (EN „Near me”). Restul: sensul coincide.
- D13: NL = „Olanda”, „în Olanda”; slug `tarile-de-jos` → `olanda` (slug-ul era derivat din nume; limba ro nu e încă publicată, deci nicio adresă publică nu se schimbă).
- `title` scurtat la 69 de caractere: „Stații de încărcare în Europa și lume: hartă, prețuri, plată | BlokVolt”.
- Rânduri noi orașe: 46 SE + 2 NO cu numele local (diacritice), „în X”, decl_ok=1; Geneva (2660646) = „Geneva”, „în Geneva”. Nota veche despre cele 144 de orașe NOBIL lipsă: rezolvată pentru cele 48 de pagini existente.
