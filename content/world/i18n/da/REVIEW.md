# R-DA — review of the Danish translation (da), pool 4, 10.11.2026

Base `origin/l-da` (cc101b8), branch `r-da`. Independent native-style review of the L-DA translation.

## Overall

The L-DA translation is solid: correct grammar, consistent impersonal style (no "vi", no "De"; "du" only in short UI imperatives), terms consistent with NOTES.md. No broken placeholders, no forbidden words (24/7, ratings, Evolako). Danish does not decline names, so `i X` is always grammatical — no `{city_u}` fixes needed.

## What was changed (403 strings reviewed, 35 changed; texts 5; countries 3; cities 17; check.py 1 line)

Strings (35):
- Length of labels/chips (≤ EN × 1.4): `f_net`, `c_net`, `k_network`, `th_net` (map/pages/prices) "Ladenetværk" → "Netværk"; `legend` "Signaturforklaring" → "Forklaring"; `copied` → "Link kopieret"; `acc_public_pay_at_location` → "Offentlig, betal på stedet"; `acc_public_notice_required` / `acc_private_notice_required` → "…, efter aftale"; `ch_ft_checked` → "tjekket"; `net_page` → "netværkets side"; `h_nets` → "Netværk og abonnementer"; `pr_home`/`pr_street` → "Hjemmelader" / "Ingen hjemmelader" (also in `profiles_note`).
- Naturalness: "Middel" → "Mellem" for the reliability level (`conf_mid`, `c50`, `p_hub`, texts `conf_levels`); "websites" → "hjemmesider" (`src_net`); `th_ratio` → "DC vs. hjemme"; `h_n_compare` → "…og hjemmeopladning"; `h_pay` → "Betaling i korte træk"; `disc` "inden afgang" → "før turen"; `sources_p` → "fra {n} åbne kilder" (n is always > 1).
- Network names with spaces: hyphen compounds "{net}-ladesteder/-ladestationer" and "{net} ladepriser" replaced by "… fra {net}" / "Ladepriser hos {net}" (`d_gnet`, `d_network`, `t_gnet`, `t_network`, `t_net`, `n_station_page`). Works for "Allego GmbH", "Clever", "IONITY" alike.
- Quotation marks: Danish »…« instead of „…“ / “…” / "…" (`report_map`, `profiles_note`, `data_p`, `cars_note`, texts).
- `p_hub_na`: reworded to "USA og Canada findes på de engelske og russiske sider; …" — still to be decided before DA goes live (see below).

texts.json (5): button name aligned with the UI ("Meld en fejl", was "Rapportér en fejl"); "punktets kort" → "infoboks" (kort = map); page name »Om dataene« (matches nav); "Mellem".

Countries (3): TT and VC "i" → "på" (island states); PS "i De palæstinensiske områder" → "i de …". check.py now compares name and in_phrase case-insensitively (otherwise PS fails).

Cities (18): Danish exonyms/transliteration — Rhodos, Korinth, Korfu, Piræus, Theben, Jekaterinburg, Nisjnij Novgorod, Rostov ved Don, Rjasan, Tjumen, Sjusjary, Teheran, Malmø, Riga, Rendsborg, Egernførde; city Hongkong/Macao spelled as the country names.
Checked and kept: København + all 31 DK; Flensborg, Slesvig, Hamborg, Prag, Lissabon, Athen, Moskva, Sankt Petersborg, Venedig, Bukarest; local forms München, Köln, Nürnberg, Wien, Bruxelles, Antwerpen, Gent, Brugge, Milano, Napoli, Torino, Warszawa, Kraków, Göteborg, Helsingborg, Zürich, Beograd, Den Haag. `decl_ok = 1` stays everywhere (Danish has no case on names).

## Slugs

No change. All ASCII, under `/da/`; no overlap with `content/com/local/{al,ba,hr,me,mk,xk}` or the EN/SR/RU world paths. Country slugs unique (150).

## Check

`python3 content/world/i18n/da/check.py` → errors 0. Blind back-translation of the 40 changed strings: see `REVIEW_backtranslation.md`.

## Open

1. `p_hub_na` — on a Danish page the sentence about EN/RU/SR coverage is odd. Best: make it language-dependent in K8 or drop it for non-EN/RU/SR languages.
2. "Abonnement" (`th_plan`, `plan_sub`) is 2.5× EN "Plan" — no shorter natural Danish word; "Plan" would be misread. Kept.
3. Island cities (Rhodos, Korfu, Kos, Chios) keep "i X" (the town), not "på X" (the island).
4. Glossary column `da` still missing — proposed set in NOTES.md.
