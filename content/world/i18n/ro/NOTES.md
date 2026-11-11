# L-RO — română (ro), note

Ramura `l-ro` de la `g3-prices` (cf44fc3). Doar fișiere în `content/world/i18n/ro/`. Limba nu este activată.

## Formă de adresare
- Impersonal; unde e nevoie de verb — imperativ de politețe, plural (Căutați, Descărcați, Trimiteți). Fără „noi”, „redacția”, „24/7”, „imediat”, clasamente sau Evolako.
- Diacritice: ș ț cu virgulă (U+0219/U+021B), niciodată sedilă (ş ţ); check.py verifică.
- Procente: `{x}%` fără spațiu (normă românească); numere în text: 2.500, zecimale cu virgulă.

## Plurale (CLDR ro: one / few / other)
- one = 1; few = 0, 2–19 și x01–x19; other = 20+ ș.a.
- În `other` stă „de”: `{"one":"oraș","few":"orașe","other":"de orașe"}` → „20 de orașe”. Motorul (K8) trebuie doar să pună `{n} {formă}`.
- Variantele `_in` au aceleași forme ca cele de bază: după „în” + număr substantivul nu se declină în română.
- Șirurile cu `{n}` din afara `pl_*` sunt neutre: „surse: {n}”, „rețele: {nets}”, „Rețele verificate: {n}”.

## Termeni (glossary.csv nu are coloana ro — termeni aleși aici)
stație de încărcare (charging station) · încărcător / punct de încărcare (charger, charge point) · locație de încărcare (site/location) · rețea (network) · operator · conector · putere · încărcare rapidă (DC) / ultrarapidă (HPC) · preț ad-hoc · taxă de sesiune · taxă de staționare/ocupare (idle fee) · abonament · TVA · fiabilitatea datelor (data reliability) · date deschise · licență · hartă.
Propunere: coloana `ro` în `names/glossary.csv` cu acești termeni — de adăugat de sesiunea care unește.

## Puncte discutabile
- `p_net_share` (pages): ordinea schimbată — „Rețeaua este prezentă {country_u} în {n_cities}” — ca să nu stea două „în” la rând. Presupune că {n_cities} = „12 orașe” și {country_u} = „în Germania”.
- `pct` (pages) = `{x}%`; codul folosește `L[l]['pct']` — în registrul K8 pentru ro: `pct='{x}%'`, `dec=','`, `thou='.'`.
- Țări: nume din CLDR (`name_ro`), scurtate: HK → Hong Kong, MO → Macao, MM → Myanmar. NL = „Țările de Jos” (CLDR, oficial); uzual se spune și „Olanda” — decizie de luat.
- `in_phrase` țări: „în” + forma articulată („în Germania”, „în Regatul Unit”, „în Statele Unite ale Americii”). Pentru insule s-ar putea „pe” („pe Insula Man”) — am lăsat „în”, corect gramatical.
- Orașe: numele local în grafia latină; exonime românești pentru 58 (Viena, Praga, Varșovia, Cracovia, Copenhaga, Lisabona, Haga, Anvers, Bruges, Veneția, Florența, Geneva, Berna, Lucerna, Marsilia (+ arondismente), Nisa, Londra, Budapesta, Belgrad, Luxemburg, Frankfurt pe Main, Istanbul, Izmir, Moscova, Sankt Petersburg, Liov, Atena, Salonic, Pireu, Corint, Rodos…). München, Köln, Nürnberg, Zürich, Milano, Torino, Napoli rămân ca în original (uz românesc).
- 169 orașe cu nume local nelatin (grecesc, chirilic etc.) → romanizarea din `name_en`. Exonime românești pentru Grecia/Bulgaria în afara celor de mai sus nu au fost căutate.
- `decl_ok = 1` pentru toate: în română numele de oraș nu se schimbă după „în”.
- Slug-uri țări: ASCII din numele românesc (germania, tarile-de-jos, statele-unite-ale-americii). Slug-urile de oraș și rețea sunt comune (regula P1), nu sunt aici.

## Verificare
- `python3 content/world/i18n/ro/check.py` — 0 erori.
- Retraducere oarbă (alt agent, fără acces la EN) a 60 de șiruri aleatorii: rezultatul mai jos.

## Rezultatul retraducerii (60 de șiruri, 09.11.2026)
- 12 observații. 4 = fals pozitiv: `{country_u}` conține deja prepoziția („în Germania”), agentul nu știa (more_stations, t_country, dataset_name, h_n_places).
- Corectate: r_err, r_err_net (+ r_ok, r_err_limit) — „Raportarea” → „Sesizarea/Sesizările”; h_more → „Alte țări din setul de date”; lead_hub — frază reformulată, numerele scoase în „Rețele: {nets}; țări: {countries}”; h_profiles → „Cât costă 100 km pentru trei tipuri de șoferi”; hpc_note — reformulat.
- Lăsate ca în EN: ch_ft_data („Hărți:” — așa e și în EN; dacă se schimbă EN, se schimbă și aici), acc_all („Afișați și celelalte” = EN „Show the others too”).
- Restul de 48: sensul coincide cu EN.

## FIXL (11.11.2026)
- strings_home.json (71 de chei); lang_hint „Această pagină este disponibilă și în română”, lang_hint_close „Închideți”.
- Slug-uri: /ro/cum-platiti/ /ro/rute/ /ro/pentru-presa/ /ro/date-pentru-companii/ /ro/embed/harta/ /ro/harta-pentru-site/ /ro/pentru-dezvoltatori/.
- name_nom: nefolosit (D14 doar de fr it es pt el); check.py îl permite.
- D13: Olanda (nu „Țările de Jos”), „în Olanda”, slug `olanda`.
- cities.csv: +48 NOBIL (nume local, „în X”) + Geneva „în Geneva”.
- FIXL2: +821 cities from names/cities_extra.csv (own market 41) — RO: diacritice cu virgulă (Iași, Pitești, Constanța, Târgu Mureș); UA/RU/BY/BG transliterare ca în fișier (Zaporojie, Odesa, Chernivtsi — nu Cernăuți, D12), GR fără accente; Roma, Florența, Genova, Triest, Siracuza; toate „în X”.
