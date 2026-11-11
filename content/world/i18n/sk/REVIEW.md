# L2-SK — REVIEW (11.11.2026)

Spätný preklad: 60 náhodných nových reťazcov (seed 1111) preložil naslepo samostatný agent SK → EN (bez prístupu k EN originálu).

**Výsledok: ok 60, mismatch 0.** Význam sedí vo všetkých 60. Agent označil 7 štylistických miest:

| # | kľúč | poznámka | čo sa stalo |
|---|---|---|---|
| 3 | b2b.what_price | „poplatok za nabíjanie… nečinné státie“ neurčité / kalk | opravené: „poplatok za spustenie nabíjania a za blokovanie stanice po nabití“ |
| 15 | pay.th_pts | „Body“ = aj bodové skóre | opravené: „Nabíjacie body“ |
| 40 | pay.cov_yes | ženský rod „Uvedená“ | ponechané: zhoduje sa so stĺpcom „Krajina…“ |
| 44 | pay.h_road | „známky“ | ponechané: „Diaľničné poplatky a známky“ — zrozumiteľné |
| 46 | map.ci_thanks | „v karte“ | opravené: „na karte“ |
| 55 | pay.d_route | „pre tri autá“ = spolu | opravené: „pre tri modely áut“ |
| 58 | press.f_range | chýba predložka pri {lo} | ponechané: `world_press.py` dosadzuje `names.in_()` = „v Nemecku“ |

## Spätné preklady

| # | kľúč | EN späť |
|---|---|---|
| 1 | `pay.method` | The route is a chain of places along the motorway; the distance is the sum of straight segments between them plus {f} %, i.e. an estimate. Chargers come from the public layer as of {date}: DC 50 kW and more, reliability 70 and more, public access, within {c} km of the route line. No real-time occupancy. |
| 2 | `pay.th_road` | Toll |
| 3 | `b2b.what_price` | <b>Prices</b> — published ad hoc tariffs of the networks: price of AC, DC and high-power charging, fee for charging and for idle parking, currency and EUR, VAT, source and date of check. |
| 4 | `pay.pay_disc` | App coverage changes often. Check it directly in the app before your trip. BlokVolt does not sell charging or cards and takes no money from apps or networks. |
| 5 | `b2b.f_company` | Company or organization |
| 6 | `embed.cf_frame_title` | Charging station map — BlokVolt |
| 7 | `pay.h_nets` | Largest networks and their apps |
| 8 | `embed.dv_f_site` | Website or app (optional) |
| 9 | `pay.gap_note` | This is a gap in the data, not proof that there is no charger here: chargers with lower reliability or slightly farther from the road are on the map. Plan to arrive at this section with a full battery. |
| 10 | `pay.th_page` | Network page |
| 11 | `b2b.lead` | Data on public charging coverage and prices by country — for charge point operators, energy companies, fleets, car makers, consulting firms, investors and public institutions. Every number has a source and a date. |
| 12 | `pay.th_src` | Source |
| 13 | `embed.cf_copied` | Copied |
| 14 | `pay.apps_n` | number of listed countries: {n} |
| 15 | `pay.th_pts` | Points |
| 16 | `press.cls_hpc` | HPC ≥ 150 kW |
| 17 | `map.ci_err_limit` | Too many responses were sent from this address today. Try again tomorrow. |
| 18 | `embed.dv_f_demo` | Demo: the form does not send anything here. Write to the address below. |
| 19 | `press.h1_press` | European charging price index for media |
| 20 | `pay.h_countries` | Countries |
| 21 | `pay.stops_note` | The farthest fast charger within 150 km of the previous stop; if two are close to each other, the more powerful one. Kilometres are an estimate along the route. Check the location on the map before your trip. |
| 22 | `embed.cf_copy` | Copy code |
| 23 | `pay.lead_routes` | For each route: fast chargers (DC, 50 kW and more, reliability 70+) within {c} km of the road, a list of stops spaced at most {s} km apart, and sections where the data show no such charger. |
| 24 | `pay.th_checked` | Verified |
| 25 | `pay.t_pay_hub` | How to pay for EV charging in Europe |
| 26 | `press.f_first` | This is the first edition; month-on-month changes will be added from the next edition. |
| 27 | `press.ch_dc_home_d` | Average ad hoc price of DC charging at 50 kW and more in each country next to the household electricity price, euros per kWh incl. VAT. |
| 28 | `press.data_csv` | Index of the month, CSV |
| 29 | `press.nav_press` | For media |
| 30 | `embed.dv_f_name` | Name or company |
| 31 | `embed.cf_more` | Open data and API requests |
| 32 | `pay.h_method` | How it is calculated |
| 33 | `pay.kick_pay` | How to pay |
| 34 | `press.d_press` | Monthly European EV charging price index: headline figures, embeddable charts, citation rules and press contact. |
| 35 | `press.t_issue` | European EV charging price index — {month} / BlokVolt |
| 36 | `pay.lead_pay_hub` | Three ways to pay: by bank card directly at the charging station (ad hoc), in the network's own app, or with a roaming app or card that works across many networks. The coverage below comes only from the official pages of each app, with the date of check. |
| 37 | `map.ci_ne_radi` | Not working |
| 38 | `pay.checked` | Data as of {date} |
| 39 | `pay.h_apps_all` | Apps and cards: official coverage |
| 40 | `pay.cov_yes` | Listed |
| 41 | `b2b.m_demo` | Demo: the form works in test mode, nothing was sent. |
| 42 | `pay.d_pay_hub` | Ad hoc card payment under EU rules, network apps, roaming apps and cards by country — with official coverage pages and date of check. |
| 43 | `pay.cov_unk` | List of countries not published |
| 44 | `pay.h_road` | Motorway tolls and vignettes |
| 45 | `press.ch_europe_d` | Weighted average ad hoc price per kWh incl. VAT in the index countries: AC, DC 50–149 kW and HPC 150 kW and more. |
| 46 | `map.ci_thanks` | Thanks. Other drivers will also see your answer in the card. |
| 47 | `b2b.h1` | Data for businesses |
| 48 | `map.ci_n30` | Reports in the last 30 days: {n} |
| 49 | `embed.dv_contact` | Or write to |
| 50 | `embed.cf_view_help` | Open the full map, move it to the desired city and paste the address of that page here. |
| 51 | `embed.dv_widget_btn` | Create code |
| 52 | `b2b.lic_dl` | Download open data |
| 53 | `pay.h_apps` | Roaming apps and cards |
| 54 | `pay.th_top_nets` | Networks on the route |
| 55 | `pay.d_route` | Fast chargers on the route {a} — {b}, a stop at most every 150 km, networks and apps by country, tolls and trip cost for three cars. |
| 56 | `pay.afir_src` | Source: Regulation (EU) 2023/1804 on EUR-Lex, as of {date}. |
| 57 | `pay.gap_line` | km {a} – {b}: in the public layer there is no fast charger with reliability 70+ within {c} km of the road. |
| 58 | `press.f_range` | DC charging was cheapest {lo} ({lo_v}) and most expensive {hi} ({hi_v}). |
| 59 | `press.lead_issue` | Network ad hoc prices: {nets}, countries: {countries}; from the networks' own price lists, weighted by number of charge points. |
| 60 | `embed.dv_f_ok` | The request was sent. The answer will come by e-mail. |
