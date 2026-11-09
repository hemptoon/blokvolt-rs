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
