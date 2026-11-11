# L2-NL — back-translation check (11.11.2026)

60 random new strings (seed 1111, of 196 with ≥3 words: ci_*, emb_open, strings_pay/press/b2b/embed, texts.pay). NL → EN by a separate reviewer that saw only the Dutch text; compared with the EN source.

Result: 0 meaning drifts. 20 style remarks; applied: bankpas → betaalkaart (NL+BE, covers debit and credit), typ_none, sys_mixed, apps_note, season, afir.points[3] "op de laadpaal", ch_europe "vermogensklasse", f_checkins, dv_params_h, dv_open_btn, dv_lead "API-sleutel", "Westelijke Balkan", "controledatum".
Kept on purpose: "antwoord" in ci_* (EN uses "answer" throughout the check-in UI), "stekkers" (glossary term from L-NL), "{lo}"/"{cu}" already carry their preposition ("in Malta"), "nepoznato"/"tamna" are literal URL parameter values, th_cover follows EN, "Voor de media" (not "Pers": the page is about the price index for journalists).

| id | back-translation | remark |
|---|---|---|
| strings_pay.t_route | {a} – {b} with an EV: fast chargers, toll, costs |  |
| strings_pay.t_routes | Through the Balkans with an EV: fast chargers per route |  |
| strings_press.read_issue | Read the full edition |  |
| strings_embed.dv_params_h | Parameters of the widget | Wordy; 'Widgetparameters' is more natural as a heading. |
| strings_pay.typ_none | Not enough official prices yet for an index of this country. | Slightly stiff; smoother: 'Nog te weinig officiële prijzen om voor dit land een index te berekenen.' |
| strings_press.ch_europe | Europe: average ad hoc price per charging class, €/kWh | 'laadklasse' is not an established term; 'vermogensklasse' (as used elsewhere) is clearer. |
| strings_press.f_mom | Compared with {prev}, the European DC average changed by {d} ({p}). |  |
| strings_pay.lead_pay_hub | There are three ways to pay: with a bank card at the charging post (ad hoc), with the network's own app, or with a roaming app or charging card that works on many networks. The coverage below comes only from each app's official pages, with the date of checking. | 'bankpas' suggests a debit card only (NL usage; BE says 'bankkaart'); neutral 'betaalkaart' fits contactless debit/credit better. 'met de datum van controle' is clunky; 'met de controledatum'. |
| strings_embed.dv_f_err | The request was not sent. Try again or write to the address below. |  |
| strings_b2b.what_cmp | <b>Comparisons</b> — public charging versus household electricity, overviews per country and network, monthly or quarterly updates with a change log. |  |
| strings_pay.pay_disc | App coverage changes often. Check the app itself before a trip. BlokVolt does not sell charging electricity or charging cards and receives no money from apps or networks. |  |
| strings_pay.d_pay_country | Paying with a bank card at the charging post, network apps, roaming apps and charging cards that work {cu}, typical prices and tolls — with sources. | Works only if {cu} carries its own preposition (e.g. 'in Servië'); list mixes an action ('Betalen met...') with nouns, a bit uneven. 'bankpas' as above. |
| strings_embed.cf_view_help | Open the full map, move it to the desired city and paste the address of that page here. |  |
| strings_press.issue_of | Edition of {date} |  |
| strings_embed.dv_p_snaga | Power classes: ac, dc, hpc, nepoznato (unknown) | Serbian value 'nepoznato' left as-is; fine if it is a literal parameter value, otherwise confusing. |
| strings_embed.dv_open_btn | Downloading and columns | Verb 'Downloaden' paired with a noun reads oddly as a button; use 'Downloads en kolommen'. |
| strings_pay.afir_src | Source: Regulation (EU) 2023/1804 on EUR-Lex, as of {date}. |  |
| strings_press.f_range | DC charging was cheapest {lo} ({lo_v}) and most expensive {hi} ({hi_v}). | Missing 'in' before {lo}/{hi} unless the placeholders already include it; 'het goedkoopst in {lo}'. |
| strings_pay.typ_more | All prices and sources |  |
| strings_embed.dv_desc | Map widget for websites, weekly open data on public charging points (ODbL), data files for the Balkans and requests for more data. |  |
| strings_b2b.ft_link | Data for businesses |  |
| strings_pay.conn_txt | Numbers of plugs, fast chargers and networks of {name} are on the country page. | 'stekkers' is colloquial; 'aansluitingen' or 'laadpunten' is the usual term. 'netwerken van {name}' reads as networks owned by the country; 'in {name}' is clearer. |
| strings_pay.cost_note | Everything charged at public DC chargers at the country's DC index price, charging losses not included. Where a country has no index yet, the European DC average ({eu}) is used: {miss}. |  |
| strings_map.ci_err | The answer was not sent. Try again. | 'antwoord' (answer) is the wrong word for a user report/check-in; use 'De melding is niet verzonden.' |
| strings_press.cls_dc | DC 50–149 kW |  |
| strings_b2b.title | Data for businesses: coverage and prices of EV charging / BlokVolt |  |
| strings_pay.season | In winter the range drops and DC charges more slowly with a cold battery: plan shorter legs, precondition the battery before a fast charger if the car can, and arrive at mountain passes with a reserve. In summer the coastal routes are busiest on weekends in July and August: there can be a queue at motorway chargers, so a charger a few kilometres off the road can save time. | 'laadt DC trager' is awkward (DC as subject); better 'laadt de auto trager aan een DC-lader'. 'kom met reserve aan bij bergpassen' slightly unnatural; 'zorg voor reserve vóór bergpassen'. |
| texts.pay.afir.points[3] | New public charging posts under 50 kW may instead offer online payment, for example via a QR code of the charging post. | 'van de laadpaal' should be 'op de laadpaal'. |
| strings_press.nav_press | For the media | Works, but 'Pers' is the conventional nav label. |
| texts.pay.afir.points[5] | The ad hoc price and its components must be shown at the station before the start of the charging session. |  |
| strings_pay.apps_note | Same columns for every app. 'Listed' means the app's own coverage page names the country; it does not mean every charging post accepts it. No partner links. | 'accepteert hem' (referring to 'de app') is informal-sounding; 'de app accepteert' or 'deze accepteert' reads better. |
| strings_embed.dv_lead | Everything that is open is free and needs no key. For everything else, you send a request. | 'sleutel' alone is vague; 'API-sleutel'. |
| strings_b2b.neutral | BlokVolt is independent of charging networks. Data customers get no influence on the map, the pages or the price index: no paid placement and no ratings. |  |
| strings_embed.cf_desc | A free world map of public charging posts for any website: choose country, network, power, language and theme, and copy the code. No registration. |  |
| strings_press.f_checkins | This month drivers confirmed {n} prices paid at charging posts (a price only counts with two matching reports). | 'Rijders' alone is unusual; 'EV-rijders' or 'bestuurders'. Pre-nominal phrase '{n} aan laadpalen betaalde prijzen' is heavy; 'bevestigden {n} prijzen die ze aan laadpalen betaalden'. |
| strings_press.charts_p | The embedded chart always shows the latest edition. For print or a fixed month, use that month's SVG file. |  |
| strings_press.lead_issue | Ad hoc prices from {nets} networks in {countries} countries, taken from the networks' own price lists, weighted by the number of charging posts. |  |
| strings_pay.th_dc | DC locations ≥ 50 kW |  |
| strings_press.embed_title | Chart by BlokVolt |  |
| strings_embed.cf_view | City or exact view |  |
| strings_pay.typ_line | Price index for this country: AC {ac}, DC {dc}, HPC {hpc} per kWh (ad hoc, EUR). |  |
| strings_map.ci_last_zauzeto | Last report: occupied, {d} |  |
| strings_embed.dv_contact | Or write to |  |
| strings_pay.h_method | How this is calculated |  |
| strings_pay.h1_route | {a} — {b} with an electric car | Em dash here vs en dash in t_route; minor inconsistency. |
| strings_pay.th_cover | Country on the official coverage page | Ambiguous as a column header; 'Land vermeld op officiële dekkingspagina' states the meaning (listed yes/no). |
| strings_press.f_mom_n | Countries with the largest change in the DC value: {list}. |  |
| strings_pay.h_gaps | Stretches with no fast charger in the data |  |
| strings_b2b.f_company | Company or organisation |  |
| strings_map.ci_far | This differs greatly from the network's price list ({p} per kWh). Check the amount, currency and unit; press Send again to confirm. |  |
| strings_map.ci_need_amt | Enter the amount, for example 0.59. |  |
| strings_pay.sys_mixed | Vignette and toll on sections. | Vague; 'Vignet en tol op bepaalde trajecten' (or 'tol per traject'). |
| texts.pay.afir.points[4] | From 1 January 2027 this also applies to existing stations of 50 kW and above on the TEN-T road network and in safe and secure parking areas. |  |
| strings_press.cite_1 | Mention the index and the month and link to the prices page, for example: |  |
| strings_press.lead_press | Every month: what public charging in Europe costs, country by country, alongside the electricity price at home. Figures, charts and data may be used freely with attribution and a link. |  |
| strings_pay.sys_none | No motorway tolls for passenger cars. |  |
| strings_press.ch_europe_d | Weighted average ad hoc price per kWh incl. VAT across the index countries: AC, DC 50–149 kW and HPC from 150 kW. |  |
| strings_b2b.focus | Focus regions: the Western Balkans, Central and Eastern Europe, Turkey, the Caucasus and Central Asia. Other countries on the world map on request. | 'westelijke Balkan' is normally capitalised as a proper name: 'de Westelijke Balkan'. |
| strings_pay.lead_route | About {km} km via {via}. Fast chargers within {c} km of the road: {n} (of which 150 kW and above: {h}). |  |
| strings_pay.conn_lnk | Charging stations in {name} |  |
