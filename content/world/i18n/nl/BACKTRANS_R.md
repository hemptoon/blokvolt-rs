# NL back-translation check (40 lines)

**Counts:** ok 37 · minor 3 · mismatch 0
(Input has duplicates: strings_map.r_snaga at lines 10/21, strings_pages.p_city_cmp at 14/28, so 38 unique keys.)

## Items
- strings_map.title — World map of charging stations for electric cars | BlokVolt — ok
- strings_map.f_type — Charging type — ok
- strings_map.net_selected — Selected networks — ok
- strings_map.f_conf — Reliability — minor — EN "Data reliability"; NL drops "of data". Fine in a filter context, or use "Betrouwbaarheid van de gegevens".
- strings_map.zoom_note — When zoomed out, the densest areas show only part of the points; zoom in to see all — minor — "dichtste" can read as "closest/most closed"; "maar" is colloquial. Suggest: "In uitgezoomde weergave tonen de drukste gebieden slechts een deel van de punten; zoom in om alles te zien."
- strings_map.data_date — Data as of {d} — ok
- strings_map.c_unnamed — Charging station — ok (EN says "EV charging station"; context makes it clear)
- strings_map.c_conf — Reliability — minor — same as f_conf.
- strings_map.osm_fix — Also correct this in OpenStreetMap — ok
- strings_map.r_snaga — Wrong power or plugs — ok
- strings_map.r_sending — Sending… — ok
- strings_map.r_ok — Thanks. Reports are reviewed once a week; correction after next data update — ok (style: "Bedankt" is slightly casual for "u"; "Hartelijk dank." fits better)
- strings_pages.disc — Data shown as is, no guarantee… check with operator before you set off… — ok
- strings_pages.p_city_cmp — DC fast chargers 50 kW+ per 10 public locations: {city} here, average {country} across {country_name} — ok (style: "gemiddeld {country} in heel …" a bit telegraphic; "tegenover gemiddeld {country} in heel {country_name}" reads better)
- strings_pages.report — Report an error — ok
- strings_prices.lead_hub — Ad-hoc prices (what an EV driver without a contract pays)… weighted by charge points… method public, data downloadable — ok
- strings_prices.th_cover — DC coverage — ok
- strings_prices.h_profiles — What 100 km costs, for three kinds of EV drivers — ok
- strings_prices.h_pay — How you pay, in short — ok
- strings_prices.pay_free — no monthly fee — ok
- strings_map.r_snaga (dup) — Wrong power or plugs — ok
- strings_map.odbl_note — Merged point data available under the ODbL — ok
- strings_map.r_err_limit — Too many reports from this address today. Try again tomorrow — ok
- strings_map.noscript — The map requires JavaScript — ok
- strings_map.no_map — The map cannot be loaded in this browser — ok
- strings_pages.sources_note — Each location keeps its data source; licences here; network names belong to their owners — ok (style: "eigendom van hun eigenaars" is tautological; "zijn merken van hun respectieve eigenaren" is cleaner)
- strings_pages.d_gnet — {net} charging locations by country from open data: power, plugs, sources — ok
- strings_pages.p_city_cmp (dup) — ok
- strings_pages.t_country — EV charging stations {country_u} — ok (depends on NL value of {country_u}, e.g. "in Nederland"; verify)
- strings_pages.conf_link — How reliability is calculated — ok
- strings_prices.out_stale — price older than 12 months — ok
- strings_prices.chart_eur — EUR per kWh at ECB rate of {date} — ok
- strings_prices.d_hub — What public EV charging costs in Europe… every price with source and date — ok
- strings_prices.d_country — Public EV charging prices {country_u} by network… ad hoc and with subscription… — ok ({country_u} same caveat)
- strings_prices.dl_tariffs — All tariffs with sources (CSV) — ok
- strings_shell.sources_p — Data from {n} open sources… full list with licences and attribution on one page — ok
- strings_shell.home_desc — Where you can charge an electric car: map + pages per country/city/network, open data with source and date — ok
- strings_shell.home_lead — One map: {n} in {c}… where data comes from and when last confirmed — ok
- strings_shell.method_desc — How locations are merged, how reliable each is, which pages exist — ok
- strings_shell.about_desc — Who runs BlokVolt and how to get in touch — ok

## Dutch tone/grammar
Formal "u" used consistently (disc, h_pay, home_desc, about_desc); no "we"/"wij"; impersonal throughout. No grammar errors. Only naturalness nits listed above (zoom_note "dichtste/maar", r_ok "Bedankt", sources_note tautology, p_city_cmp phrasing, check {country_u} values).
