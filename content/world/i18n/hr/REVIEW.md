# R-HR — lektura hrvatskog prijevoda (pool 4, 10.11.2026)

Baza `origin/l-hr` (c7438af), grana `r-hr`. Neovisni urednik; prijevod je radila sesija L-HR.

## Što je pregledano
- Svih 403 niza (map 125, pages 120, shell 41, prices 117), `texts.json`, `slugs.json`.
- Svih 150 zemalja: `name`, `in_phrase`, slug — bez ispravaka (lokativi, „na” za otoke i Kosovo, ASCII slugovi ispravni).
- Gradovi: svih 43 grada u HR i BA + prvih 500 gradova `stage = month` po redu datoteke (places-JSON nije korišten zbog vremena).
- Slugovi: nema preklapanja s `content/com/local/hr/` (stranice i 121 grad lokalnog odjeljka), svi pod `/hr/`, različiti od EN/SR/RU.
- Termini se poklapaju s lokalnim odjeljkom `/hr/` (punionica, priključak) i stupcem `hr` glossaryja.

## Ispravci
Nizovi (11):
- `d_city`, `t_city`, `t_city_cc`: „u gradu {city}” → `{city_u}` (odluka 00:12: `{city_u}` dopušten u svim jezicima).
- `p_city_cmp`: rečenica je počinjala genitivom („Brzih DC punjača…”) → „Brzi DC punjači (50 kW i više) na svakih 10 javnih lokacija: …”.
- `p_multi`: prirodniji red riječi („{pct_multi} lokacija potvrđeno je iz dva ili više izvora”).
- `th_ratio` „DC u odnosu na kuću” → „DC / kod kuće”; `th_cover` „Pokrivenost DC” → „DC pokrivenost” (zaglavlja tablice, duljina ≤ EN × 1,4).
- `acc_public_pay_at_location` → „Javno, plaćanje na mjestu”; `r_nije_javni` → „Nije javno”; `copied` → „Poveznica kopirana” (čipovi/toast, kraće).
- `texts.download.file_missing`: uklonjeno „Molimo,” (bezlični ton kao u ostatku).

Gradovi (100 redaka u `cities.csv`):
- Banja Luka: „u Banja Luci” → „u Banjoj Luci” (hrvatska norma, oba dijela se sklanjaju).
- Iraklion → Heraklion („u Heraklionu”); València → Valencija („u Valenciji”).
- 97 gradova iz top-500 sa sigurnom konstrukcijom „u gradu X” dobilo je pravi lokativ i `decl_ok = 1` (Breda → u Bredi, Maastricht → u Maastrichtu, Rennes → u Rennesu, Freiburg im Breisgau → u Freiburgu im Breisgau …). Napomena „R-HR lokativ”.
- `decl_ok = 1` ukupno: 2 337 → 2 435.

`check.py`: provjera plaseholdera sada prihvaća `{city_u}`/`{country_u}` umjesto `{city}`/`{country}` (jedina promjena u skripti). Rezultat: OK.

## Namjerno ostavljeno
- Imena na -e/-o bez jasnog hrvatskog lokativa (Zwolle, Enschede, Ede, Karlsruhe, Le Havre, Oulu, Espoo, Tampere…) ostaju „u gradu X”, `decl_ok = 0` — sigurno.
- `fallback_u` „u gradu {x}” — to je rezervna konstrukcija, ostaje.
- Kratke riječi koje su dulje od EN × 1,4 bez alternative (Izbornik, Automobil, Mješovito, Bez ugovora, Pretplata) — prihvatljivo.
- `pl_city_in` few = „grada” („u 3 grada”) — razgovorno, za sučelje prihvatljivo (vidi NOTES.md).

## Spornije (za Andreja / K8)
- Ostalih ~4 600 gradova izvan top-500 nisu ručno pregledani; ~3 100 ima sigurno „u gradu X”.
- Slugovi iz `l-hr` prihvaćeni odlukom 00:12 (korijen `/hr/svijet/`); ostale stranice svijeta nisu pod `/hr/svijet/…` nego izravno pod `/hr/` (npr. `/hr/punionice/`). Ako se želi sve pod `/hr/svijet/`, treba promijeniti `slugs.json` prije G8.

## Povratni prijevod (zaseban agent, naslijepo, 40 izmijenjenih nizova)
- OK 37, ISSUE 3 — sva tri ispravljena: `p_city_cmp` („od 50 kW” čitano kao „točno 50 kW”, „na 10” kao fiksni broj) → „(50 kW i više) na svakih 10”; `th_ratio` „kuća” = zgrada → „DC / kod kuće”; `p_multi` slaganje glagola → „potvrđeno je iz dva ili više izvora”.
- Svih 31 lokativa gradova u uzorku: OK.

# L2-HR — dopuna za blokvolt.com jezike (11.11.2026)

Grana `l2-hr` od `dev` (bb86f74). Samo `content/world/i18n/hr/`.

## Što je dodano
- 274 ključa: `strings_map` 29 (`ci_*` provjere vozača, `emb_open`), nove datoteke `strings_pay` 93, `strings_press` 54, `strings_b2b` 33, `strings_embed` 65. HOME2 još nije u `dev` — njegovi ključi nisu uključeni (LANGI).
- `texts.json`: odjeljci `pay` (6 točaka AFIR, `afir.points[i]`) i `routes` (59 naziva gradova, `routes[i].stops[j].city`; Beograd, Sofija, Budimpešta, Veliko Trnovo, ostalo izvorno).
- Svoje zemlje (`market_countries` = HR): Hrvatska u `countries.csv` u redu; svih 24 grada HR u `cities.csv` provjereno, `decl_ok = 1`. Za HR nema svjetskih stranica gradova (K3: lokalni odjeljak `/hr/`), pa novih gradova nema. 144 nova grada NOBIL (SE 138, NO 6) nisu u `names/cities.csv` — nisu za hr.
- `check.py`: sada svih 8 datoteka nizova i odjeljci `texts.pay` / `texts.routes` (ključevi = putanje višejezičnih čvorova u `pay.json`/`routes.json`, plaseholderi). Rezultat: OK.

## Termini
- ad hoc → „bez ugovora” (kao u cijenama); roaming → „roaming” (glossary); toll → „cestarina”, vignette → „vinjeta”, stretch → „dionica”, stop → „stajalište”; widget → „widget”; developers → „programeri”; check-in → „provjera”.
- `{cu}`, `{lo}`, `{hi}` = lokativna fraza zemlje („u Hrvatskoj”); `{name}` = nominativ; `{month}` = naziv mjeseca, uvijek bez prijedloga („({month})”, „izdanje „{prev}””).

## Povratni prijevod (zaseban agent, naslijepo, 60 nasumičnih novih nizova)
- Smisao: 60/60 OK, bez MISMATCH. Agent je dao 17 stilskih napomena; ispravljeno 9: `d_pay_country` („koje se mogu koristiti”), `d_route`/`d_routes` („najmanje svakih 150 km”, „tri modela automobila”), `lead_pay_hub` (tri načina jasno odvojena), `issue_note` („u eurima po kWh, po tečaju ESB-a na dan”), `f_checkins` (broj na kraju kao „Broj …: {n}”), `what_price` („tarife mreža za punjenje bez ugovora”), `focus` („Srednja Azija”), `ci_rules` (eksplicitni subjekt), `dv_lead`, `afir.points[5]` („sastavnice”).
- Ostavljeno: „javni sloj” (termin cijelog sučelja), „dnevni otisak veze / hash s ključem” (tehnički točno, isto u EN), `cov_no` „Nije navedena” (stupac je zemlja).

## Spornije
- Duljina iznad EN × 1,4 samo u zaglavljima (`th_app` „Aplikacija ili kartica”, `th_car` „Automobil”) — prihvatljivo.
- `pl_*` novih nema; nizovi s `{n}` napisani bez oblika („Broj …: {n}”).

## FIXL 11.11.2026
Provjereno: strings_home (71 ključ, nova datoteka), strings_shell `lang_hint`/`lang_hint_close`, D11 (`dv_p_lang`, `p_hub_na`), slugovi (+7), cities.csv (+49), D12.
Povratni prijevod (val 2, naslijepo pa usporedba s EN): 10 nizova home (title, desc, h1, sub, near_err, map_err, prices_p, work_p, trust_p, routes_p) + 4 izmijenjena (dv_p_lang, p_hub_na, lang_hint, lang_hint_close).
- Ispravljeno: `lang_hint` „Ova stranica postoji i na hrvatskom” (srbizam/kalk) → „Ova je stranica dostupna i na hrvatskom”.
- `desc` bez „za svako mjesto” na kraju (duljina 160) — smisao ostaje.
D12: „Ser” (734330, Σέρρες; povijesni srpski egzonim) → „Seres”, „u Seresu”. Ostali egzonimi uobičajeni i neutralni (Beč, Prag, Napulj, Krakov, Gdanjsk, Solun, Atena).
Slugovi: `/hr/…` bez sudara s lokalnim odjeljkom Hrvatske (karta/, cijene/, putovanje/ … i slugovi mjesta).
