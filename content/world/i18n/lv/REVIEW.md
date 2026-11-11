# L2-LV — review (11.11.2026)

## Back-translation (60 random new strings, blind, second agent)
58 match in meaning. 2 drifted → fixed:
- `strings_b2b.f_msg`: «Kam dati vajadzīgi» read as "who needs the data" → «Kādam nolūkam dati vajadzīgi, formāts, cik bieži».
- `strings_press.f_home`: «reizēm dārgāka» reads as "sometimes" → «reizes dārgāka».
Minor naturalness note taken: `strings_pay.apps_unk` «nav nosaukts» → «nav norādīts».
Noted, left as is: `svari` (weights, technical, same as m3), `maksas punkti` (toll stations), elliptical `stops_note`.

## Full package review (et/lt/lv had no R-pass)
Strings (403 existing):
- Index name unified: prices used «elektroauto», everything else «elektromobiļu» → `t_hub`, `h1_hub`, `d_hub`, `t_country`, `d_country` now «elektromobiļu»; citation in `data_p` now Latvian, same as press `credit`.
- `lead_hub`: «{nets} uzlādes tīkliem {countries} valstīs» breaks on 21, 31… (singular in lv) → counts moved to «Uzlādes tīkli: {nets}, valstis: {countries}».
- `t_near`: «netālu no {x}» needs genitive, {x} is nominative → « (tuvumā: {x})».
- `p3`: «DC līdz 50 kW» overlapped p4 → «DC zem 50 kW».
- Dates: «kursa uz {date}», «slāņa uz {layer}» like «Dati uz {date}» (fx_note, chart_eur, m3, m4).
- Quotes: “…” → Latvian „…” (report_map, profiles_note, data_p, cars_note, 6 in texts).
- texts.json: «uzticamība» → «ticamība» (same term as map and pages, 5 strings).
Countries: 150 checked; AX «Olandes salas» (CLDR) → «Ālandu salas» (LVA usage), slug `alandu-salas`.
Cities: all 1 128 `decl_ok=1` read:
- Rīga had `in_phrase` «pilsētā Rīga» → «Rīgā».
- Cluj-Napoca locative «Kluža-Napokā» → «Klužā-Napokā».
- US/CA namesakes no longer get European exonyms: London CA, Athens US, Amsterdam US → original name, «pilsētā X», `decl_ok=0`, note `r-lv-namesake`. US Cambridge/Manchester/Birmingham kept: lv Wikipedia uses the same form for them.
- Anchorage «Ankurija» → «Enkoridža».
- Other exonym-auto forms checked against common Latvian usage (Zalcburga, Grāca, Belgrada, Novisada, Kijiva, Ļviva, Stambula, Ņujorka …) — fine.
Disputed, left: Heraklion «Hērakliona» vs Irakleio «Iraklija» (two GeoNames rows), Seinäjoki/Pori locative = name.

## FIXL 11.11.2026
Checked: new `strings_home.json` (71 keys), `lang_hint`/`lang_hint_close`, D11 (`dv_p_lang`, `p_hub_na`), 7 slugs, 49 cities (48 NOBIL + Geneva).
Back-translation (wave 2, blind): 10 home strings (title, h1, data_as_of, search_none, near_err, prices_p, p_ratio, work_p, routes_p, trust_p) + 3 changed (dv_p_lang, p_hub_na, lang_hint) — all match in meaning, no fixes.
- `tab_ap` «Āzija un Okeānija» (shorter than «Āzijas un Klusā okeāna reģions») — same set of countries; minor wording divergence from EN "Asia-Pacific".
- `prices_p` keeps «ad hoc (bez līguma)», as in strings_prices; `map_alt` lime = «dzeltenzaļais».
- `p_ratio` «{x}× dārgāk nekā mājās» — the × sign avoids number agreement.
D13 (lv): «viesabonēšana» kept everywhere (pay_p uses it too).
D12: foreign city names checked — no historical/irredentist exonyms; Viļņa, Kauņa, Belostoka, Grodņa are the normal Latvian forms, kept.
NOBIL towns: Swedish/Norwegian form, «pilsētā X», decl_ok=0 (like Västerås, Umeå in this file); Geneva «Ženēva / Ženēvā», decl_ok=1.
Open: `exonym-auto` forms are still unchecked by a native speaker (R-LV).
