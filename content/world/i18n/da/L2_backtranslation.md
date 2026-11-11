# L2-DA — blind tilbageoversættelse (60 tilfældige nye strenge, seed 20261111)

Andet agent, kun de danske strenge, ingen adgang til EN. 60 af 60 stemmer i betydning; 16 bemærkninger, 5 accepteret (se REVIEW.md, afsnit L2).

| id | tilbageoversat EN | bemærkning |
|---|---|---|
| embed.cf_height | Height, px |  |
| press.ch_dc_home | Fast charging (DC) vs. household electricity price, €/kWh |  |
| b2b.title | Data for companies: coverage and prices for charging electric cars / BlokVolt |  |
| pay.lead_routes | For each route: fast chargers (DC, 50 kW and more, reliability 70+) within {c} km of the road, a stop list with at most {s} km between the stops, and the stretches where the data do not show such a charger. | 'pålidelighed 70+' is opaque: 70+ of what (score, %)? Reader can't tell. |
| embed.cf_more | Open data and API requests | 'API-forespørgsler' reads as API calls/queries, not requests for API access; ambiguous. |
| press.d_issue | What public EV charging cost in Europe in {month}: ad hoc prices for AC, DC and HPC per country compared with the household electricity price. |  |
| pay.th_checked | Checked |  |
| pay.th_place | Place |  |
| pay.t_pay_country | Payment for charging an electric car {cu} | Only grammatical if {cu} includes the preposition (e.g. 'i Danmark'). |
| map.ci_err | The answer was not sent. Try again. |  |
| embed.dv_widget_h | Map widget |  |
| embed.dv_widget_btn | Make the code | 'Lav koden' sounds clumsy for a button; 'Generér kode' / 'Hent kode' is more natural. |
| press.lead_press | Every month: what public charging costs in Europe, country by country, compared with the household electricity price. Figures, graphs and data may be used freely with source attribution and a link. |  |
| pay.conn_lnk | Charging stations: {name} |  |
| press.h_cite | How to cite the index |  |
| b2b.lic_h | Licences |  |
| pay.h_typical | Typical prices |  |
| press.ch_europe | Europe: average ad hoc price per charging class, €/kWh | 'ladeklasse' is a coined term; elsewhere 'effektklasse' is used - inconsistent. |
| pay.no_gaps | On this route the data show a fast charger at least every 150 km. | 'mindst hver 150 km' is slightly awkward/ambiguous (natural: 'mindst for hver 150. km' or 'højst 150 km mellem hver'); also hardcoded 150 while lead uses {s}. |
| pay.d_pay_country | Card payment at the charging post, the networks' apps, roaming apps and charging cards that work {cu}, typical prices and road tolls - with sources. |  |
| pay.h_by_country | Networks, apps and road tolls per country |  |
| pay.afir_non | {name} is not a member of the EU: AFIR is EU law, and the rules below may not apply there. Check the network's own terms. |  |
| map.ci_rules | No account is required. Only answers from different drivers count. A price is compared with the network's published tariff; it can only become a candidate for the price index once two drivers independently report the same price, and prices that cannot be right are hidden. Answers containing advertising, links or personal data are removed. The same rules apply to all networks. | Opening 'Det kræver ingen konto' has an unclear referent for 'Det'; 'Der kræves ingen konto' is cleaner. |
| embed.dv_lead | Everything that is open is free and requires no key. For anything beyond that, a request is sent. | Passive 'sendes en forespørgsel' is odd/ambiguous (who sends?); an instruction 'send en forespørgsel' is expected. |
| press.kick_issue | Monthly edition |  |
| pay.nets_note | The networks are sorted by the number of DC charging sites of 50 kW and more in the public layer. Most networks have their own app; the price page shows ad hoc and app prices with sources. | 'i det offentlige lag' (in the public layer) is internal jargon, unclear to readers. |
| embed.cf_view | City or exact view | Unclear what 'By eller præcis visning' means (choose a city or a precise map view?). |
| pay.apps_unk | the official page does not mention a list of countries |  |
| press.data_csv | The month's index, CSV |  |
| embed.dv_p_mreza | The network's slug, several separated by comma | 'slug' is untranslated dev jargon; 'adskilt med kommaer' (plural) is more natural. |
| embed.dv_h1 | For developers |  |
| embed.dv_title | Charging data for developers and media: widget, open data / BlokVolt |  |
| pay.sys_mixed | Vignette and toll on individual stretches. | Ambiguous: unclear whether the vignette also applies only on some stretches or network-wide with tolls on some. |
| pay.th_top_nets | Networks on the route |  |
| pay.t_route | {a} to {b} by electric car: fast chargers, road tolls, price |  |
| embed.cf_h1 | Charging map for websites |  |
| b2b.what_cov | <b>Coverage</b> - public charging sites per country, city and charging network: power classes, share of DC and high power, connectors, number of sources, date of latest confirmation. |  |
| pay.th_map | Map | 'Kort' means both 'map' and 'card'; in a payment context (charging cards) it is ambiguous as a column header. |
| embed.dv_p_lang | Language: the widget's address (EN, SR, RU) | Misspelling: 'widgettens' should be 'widgetens'; meaning of 'Sprog: widgetens adresse' is also unclear. |
| pay.h_gaps | Stretches without a fast charger in the data |  |
| embed.emb_full | Open the full map |  |
| press.credit | Source: BlokVolt, European EV Charging Price Index, {month} |  |
| map.ci_month | Month |  |
| pay.h_conn | Connectors and charging sites |  |
| embed.cf_copy | Copy code |  |
| b2b.m_limit | Too many messages today. Write to hello@blokvolt.com. |  |
| pay.h_countries | Countries |  |
| pay.h_road | Motorway tolls and vignettes |  |
| press.svg_file | SVG file, {month} |  |
| map.ci_u_min | minute | Singular 'minut' as a unit label may read oddly; 'min.' or 'pr. minut' depending on use. |
| b2b.f_send | Send request |  |
| b2b.f_what | Data |  |
| pay.t_pay_hub | Payment for charging electric cars in Europe |  |
| press.th_country | Country |  |
| texts.pay.afir.points[4] | From 1 January 2027 it also applies to existing charging stations of 50 kW and more on the TEN-T road network and in safe and secure parking areas. |  |
| pay.th_car | Car |  |
| embed.dv_p_hash | Exact view: #zoom/latitude/longitude at the end of the address |  |
| pay.gap_note | This is a gap in the data, not proof that no charger exists: chargers with lower reliability or slightly further from the road are shown on the map. Plan to reach this stretch with a full battery. |  |
| embed.cf_preview | Preview |  |
| embed.dv_open_btn | Download and columns | Odd button label; 'Download og kolonner' doesn't say what action happens. |
