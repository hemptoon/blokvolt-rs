# Turkish back-translation (33 lines)

- net_none — "No charging network with this name was found." — ok
- legend — "Legend" — ok
- ch_ft_data — "Maps: © OpenStreetMap contributors, Open Charge Map" — issue (minor): "katkıcıları" is understandable, but the usual Turkish OSM attribution is "OpenStreetMap katkıda bulunanlar". Optional change.
- c_price — "Price (ad hoc)" — ok
- crumbs — "Page path" (breadcrumbs) — ok
- d_country (stations) — "Public charging locations in {country} according to open data: fast DC charging points, charging networks, cities, connectors, sources and licences." — ok
- d_network — "{net} charging locations in {country} according to open data: power, connectors and cities, together with their sources." — ok
- dataset_name — "Public EV charging locations in {country} (open data, ODbL)" — ok
- p_multi — "Share of locations confirmed by two or more sources: {pct_multi}; share of those last confirmed in 2025 or 2026: {pct_recent}." — ok
- report_map — "An error in a location can be reported with the 'Report an error' button on its card on the map." — ok (slightly heavy "haritadaki kartında bulunan", but correct)
- st_dc50 — "DC 50 kW and above" — ok
- st_hpc — "150 kW and above" — ok
- t_country (stations) — "Electric vehicle charging stations in {country}" — ok
- t_network — "{net} charging stations in {country}" — ok
- to_country — "Charging stations in {country}" — ok
- d_hub — "Cost of public EV charging across Europe: prices of charging networks without subscription (ad hoc) by country, AC, DC and HPC, compared with home electricity. Every price with its source and date." — ok
- lead_hub — "Ad hoc prices of {nets} charging networks in {countries} countries — what the driver pays without a contract — weighted by each network's number of charging points in the country, alongside the home electricity price. The method is open and the data can be downloaded." — issue (minor): first sentence has no main verb (noun-phrase fragment); acceptable as a lead but reads as a list rather than a sentence. Could end with "...yanında gösterilir."
- t_country (prices) — "Electric vehicle charging prices in {country}" — ok (note: key duplicates the stations t_country; fine only if in a different section/object)
- d_country (prices) — "Public EV charging prices in {country}, by charging network: AC, DC and HPC, without and with subscription, home electricity, cost of 100 km. Source and date for every price." — ok (same duplicate-key note)
- t_net — "{net} charging prices in {country}" — ok
- d_net — "{net} charging prices in {country}: published tariffs, without and with subscription, fees, cost of 100 km, and comparison with the country average and home charging." — ok
- table_note — "Ad hoc prices without subscription, VAT included, per kWh. {u} — unweighted median of charging networks: networks with known prices hold less than 10% of the country's charging points whose network is known. — no index: fewer than two charging networks with a known price." — issue: the "—" separators make it hard to parse; the second explanation ("— endeks yok: ...") has no symbol/marker before it, so it looks like a dangling dash. Also "fiyatı bilinen ağlar ... %10'undan azına sahip" is grammatical but clunky; clearer: "fiyatı bilinen ağların payı, ağı bilinen şarj noktalarının %10'undan az".
- profiles_note — "Car: {car}, {cons} kWh per 100 km (estimated, mild weather, energy drawn from the battery; charging losses not included). Charging shares: 'home charger' {p1}; 'mixed' {p2}; 'no home charger' {p3}. Country prices are taken from the table above." — issue (minor): "Şarj payları" ("charging shares") is vague; "Şarjın dağılımı" or "Ev/halka açık şarj oranları" would be clearer.
- pr_home — "Home charger" — ok
- pr_street — "No home charger" — ok
- m1 — "Prices: each charging network's ad hoc tariff — what anyone pays without a contract or subscription — is taken from the operator's own price page or, if the operator does not publish prices, from a dated news item reporting that price. Prices include VAT, per kWh. Per-minute or per-session prices, prices older than 12 months and prices of unclear source are shown on country pages but not included in the index." — ok
- h_c_index — "Charging price index in {country}" — ok
- plan_adhoc — "Ad hoc" — ok
- cars_note_net — "Consumption from the battery in mild weather, estimated (Open EV Data, © 2019 Chargeprice, MIT); about 20–30% more in winter. Charging losses not included. Prices: the network's ad hoc tariff without subscription." — ok
- pay_adhoc — "Without contract (ad hoc price published): {list}." — issue (minor): telegraphic and slightly unnatural; "Sözleşmesiz ödeme (ad hoc fiyatı yayımlanmış): {list}." or "Sözleşme olmadan ödeme mümkün (ad hoc fiyat yayımlanmış): {list}." reads better.
- more_stations — "Charging stations in {country}" — ok
- too_few — "Too few charging networks publish ad hoc prices without subscription for the index — see the country page" — ok (note: line has no trailing comma before the next key; JSON syntax error if both are in the same object)
- about_p — "BlokVolt is an independent reference source on EV charging; it is run by its founders Andrei and Danila in Novi Sad (Serbia). No paid listings, charging networks are not rated." — ok

Placeholder note: "{country_u}ki" works for all countries since the locative suffix is already harmonized and "-ki" does not change after -da/-de.
