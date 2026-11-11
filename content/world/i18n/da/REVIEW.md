# R-DA — review of the Danish translation (da), pool 4, 10.11.2026

Base `origin/l-da` (cc101b8), branch `r-da`. Independent native-style review of the L-DA translation.

## Overall

The L-DA translation is solid: correct grammar, consistent impersonal style (no "vi", no "De"; "du" only in short UI imperatives), terms consistent with NOTES.md. No broken placeholders, no forbidden words (24/7, ratings, Evolako). Danish does not decline names, so `i X` is always grammatical — no `{city_u}` fixes needed.

## What was changed (403 strings reviewed, 34 changed; texts 5; countries 3; cities 17; check.py 1 line)

Strings (35):
- Length of labels/chips (≤ EN × 1.4): `f_net`, `c_net`, `k_network`, `th_net` (map/pages/prices) "Ladenetværk" → "Netværk"; `copied` → "Link kopieret"; `acc_public_pay_at_location` → "Offentlig, betal på stedet"; `acc_public_notice_required` / `acc_private_notice_required` → "…, efter aftale"; `ch_ft_checked` → "tjekket"; `net_page` → "netværkets side"; `h_nets` → "Netværk og abonnementer"; `pr_home`/`pr_street` → "Hjemmelader" / "Ingen hjemmelader" (also in `profiles_note`).
- Naturalness: "Middel" → "Mellem" for the reliability level (`conf_mid`, `c50`, `p_hub`, texts `conf_levels`); "websites" → "hjemmesider" (`src_net`); `th_ratio` → "DC vs. hjemme"; `h_n_compare` → "…og hjemmeopladning"; `h_pay` → "Betaling i korte træk"; `disc` "inden afgang" → "før turen"; `sources_p` → "fra {n} åbne kilder" (n is always > 1).
- Network names with spaces: hyphen compounds "{net}-ladesteder/-ladestationer" and "{net} ladepriser" replaced by "… fra {net}" / "Ladepriser hos {net}" (`d_gnet`, `d_network`, `t_gnet`, `t_network`, `t_net`, `n_station_page`). Works for "Allego GmbH", "Clever", "IONITY" alike.
- Quotation marks: Danish »…« instead of „…“ / “…” / "…" (`report_map`, `profiles_note`, `data_p`, `cars_note`, texts).
- `p_hub_na`: reworded to "USA og Canada findes på de engelske og russiske sider; …" — still to be decided before DA goes live (see below).

texts.json (5): button name aligned with the UI ("Meld en fejl", was "Rapportér en fejl"); "punktets kort" → "infoboks" (kort = map); page name »Om dataene« (matches nav); "Mellem".

Countries (3): TT and VC "i" → "på" (island states); PS "i De palæstinensiske områder" → "i de …". check.py now compares name and in_phrase case-insensitively (otherwise PS fails).

Cities (18): Danish exonyms/transliteration — Rhodos, Korinth, Korfu, Piræus, Theben, Jekaterinburg, Nisjnij Novgorod, Rostov ved Don, Rjasan, Tjumen, Sjusjary, Teheran, Malmø, Riga, Rendsborg, Egernførde; city Hongkong/Macao spelled as the country names.
Checked and kept: København + all 31 DK; Flensborg, Slesvig, Hamborg, Prag, Lissabon, Athen, Moskva, Sankt Petersborg, Venedig, Bukarest; local forms München, Köln, Nürnberg, Wien, Bruxelles, Antwerpen, Gent, Brugge, Milano, Napoli, Torino, Warszawa, Kraków, Göteborg, Helsingborg, Zürich, Beograd, Den Haag. `decl_ok = 1` stays everywhere (Danish has no case on names).

## Back-translation (40 changed strings, blind, second agent)

13 flags; accepted 8: `legend` reverted to "Signaturforklaring" (standard map term; heading, not a chip — length exception), `p_hub` "Landene på Vestbalkan …", `d_network` "byer, med kilder", `disc` last clause, `h_n_compare` "landeindekset", `cars_note` "hvor der ikke er et indeks", texts "Kildekoder, adskilt med komma", `attribution_p` as an obligation ("skal vises … skal angives"). Not accepted: `{country_u}` flags (the engine inserts "i Tyskland" per decision 10.11 00:12), `ch_ft_checked` "tjekket" (fine), `n_station_page` "ladestandere" (= EN "chargers"). Full report: `REVIEW_backtranslation.md`.

## Slugs

No change. All ASCII, under `/da/`; no overlap with `content/com/local/{al,ba,hr,me,mk,xk}` or the EN/SR/RU world paths. Country slugs unique (150).

## Check

`python3 content/world/i18n/da/check.py` → errors 0. Blind back-translation of the 40 changed strings: see `REVIEW_backtranslation.md`.

## Open

1. `p_hub_na` — on a Danish page the sentence about EN/RU/SR coverage is odd. Best: make it language-dependent in K8 or drop it for non-EN/RU/SR languages.
2. "Abonnement" (`th_plan`, `plan_sub`) is 2.5× EN "Plan" — no shorter natural Danish word; "Plan" would be misread. Kept.
3. Island cities (Rhodos, Korfu, Kos, Chios) keep "i X" (the town), not "på X" (the island).
4. Glossary column `da` still missing — proposed set in NOTES.md.

## L2-DA — delta for 27 sprog (11.11.2026)

Branch `l2-da` fra `dev` (bb86f74). HOME2 er endnu ikke i `dev`, så kun deltaen fra LANG_pool §0: 274 nøgler.

- `strings_map.json` +29 (`ci_*` driver-meldinger og `emb_open`); nye filer `strings_pay.json` (93), `strings_press.json` (54), `strings_b2b.json` (33), `strings_embed.json` (65).
- `texts.json` +`pay` (6 AFIR-punkter, nøgle = sti i pay.json, fx `afir.points[0]`) og `routes` (59 bynavne for stop; kun Belgrade → Beograd, resten lokal form = dansk praksis).
- Stil som før: upersonlig, »…«, tankestreg —, "du" kun i korte imperativer og i driver-formularen ("Dit svar", "Hvor meget betalte du?").
- Termer: How to pay = »Betaling« (nav) / »Betaling for opladning af elbiler i Europa« (titel); roaming app = roaming-app; card = ladekort; vignette = vignet; toll = vejafgift; check-in = melding; issue = udgave; embed = indlejre; widget = widget/widgetten.
- Indeksets officielle navn står på engelsk i citatlinjen (`press.credit`), som i `prices.data_p`; overskrifter bruger »Europæisk prisindeks for opladning af elbiler«.
- `conn_lnk` = »Ladestationer: {name}« (ikke »i {name}«, da øer kræver »på«).
- check.py: alle 8 filer + `texts.pay`/`texts.routes` (LANG0-format) → 0 fejl. `scripts/world_i18n.py check da` → OK.

Tilbageoversættelse (60 strenge, blind, andet agent): 60/60 i betydning, 16 bemærkninger. Accepteret 5: `ci_rules` »Der kræves ingen konto«, `dv_lead` »Til alt derudover: send en forespørgsel«, `dv_widget_btn` »Generér koden«, `cf_more` »Åbne data og API-adgang«, `ch_europe` »effektklasse« (som i prices). Afvist: »pålidelighed 70+« og »det offentlige lag« (eksisterende termer på hele sitet), »widgetten« (korrekt bøjning), `{cu}` (motoren indsætter »i Danmark«). Fuld liste: `L2_backtranslation.md`.

Byer: alle 16 DK-byer i pages_state (+10 netværk, 1 land) findes med korrekt navn og slug; cities.csv har alle 5 605 fra names/cities.csv. 48 byer i pages_state (SE 46, NO 2 — NOBIL) mangler i `names/cities.csv` og kan ikke tilføjes i i18n (check kræver geonameid i names) — opgave for sv/nb/LANG0, ikke DK.

Åbent: `p_hub_na` (stadig), `pay.th_map` »Kort« i en betalingskontekst (kort = map/card) — står kun i rute-tabellen, OK.
