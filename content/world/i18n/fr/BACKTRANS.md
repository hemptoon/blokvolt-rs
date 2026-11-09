# Back-translation QA — French UI strings (sample of 60)

Sample: random.seed(42), 60 of 403 string values across strings_map/pages/shell/prices (plural objects -> "other").
Back-translations written to /home/claude/work/backtrans.json before reading EN.

Counts: ok 57 · minor 3 · mismatch 0

Flags across the sample:
- "nous/notre/nos": none
- "24h/24" / "24/7": none
- rankings: none
- glossary: terms consistent (borne de recharge, point de charge, site de recharge, prise, réseau, données ouvertes, dernière confirmation, vérifié, indice des prix, 150 kW et plus). One terminology question: EN "Plan" rendered as "abonnement" (see below).
- typography: NBSP before « : ; » and inside « » is correct everywhere in the sample. Apostrophes are mixed: typographic ’ (map:t_ac "jusqu’à", shell:home_lead "l’origine") vs straight ' (pages:p1, prices:chart_desc, pages:d_network, prices:cars_note). Not a meaning issue; pick one style (’) and normalise across all files.
- placeholders/HTML: all preserved in the sample (map:ch_ft_data reorders "© contributeurs <a>OpenStreetMap</a>" — correct French order, tags intact).

## Items
- id: prices:serbia_link
  FR: Indice des prix de la Serbie
  back-EN: Serbia price index
  EN: Price index of Serbia
  verdict: ok

- id: map:c_pts
  FR: Points de charge
  back-EN: Charge points
  EN: Charging points
  verdict: ok

- id: map:t_ac
  FR: AC jusqu’à 22 kW
  back-EN: AC up to 22 kW
  EN: AC up to 22 kW
  verdict: ok

- id: prices:pay_note
  FR: Le mode de paiement exact — application, carte bancaire à la borne ou code QR — figure sur la page tarifaire du réseau, en lien dans le tableau.
  back-EN: The exact payment method — app, bank card at the charger or QR code — is on the network's pricing page, linked in the table.
  EN: How exactly to pay — app, card at the charger or QR code — is on the network's price page linked in the table.
  verdict: ok

- id: pages:download_link
  FR: Télécharger les données ouvertes (ODbL)
  back-EN: Download the open data (ODbL)
  EN: Download the open data (ODbL)
  verdict: ok

- id: pages:balkan_note
  FR: Ces pays ont leurs propres pages BlokVolt avec des données vérifiées.
  back-EN: These countries have their own BlokVolt pages with verified data.
  EN: These countries have their own BlokVolt pages with checked data.
  verdict: ok

- id: map:ch_ft_data
  FR: Cartes : © contributeurs <a href="https://www.openstreetmap.org/copyright" rel="noopener">OpenStreetMap</a>, <a href="https://openchargemap.org" rel="noopener">Open Charge Map</a>
  back-EN: Maps: © OpenStreetMap contributors, Open Charge Map
  EN: Maps: © <a href="https://www.openstreetmap.org/copyright" rel="noopener">OpenStreetMap</a> contributors, <a href="https://openchargemap.org" rel="noopener">Open Charge Map</a>
  verdict: ok

- id: map:osm_fix
  FR: Corrigez-le aussi dans OpenStreetMap
  back-EN: Fix it in OpenStreetMap too
  EN: Correct it in OpenStreetMap too
  verdict: ok

- id: prices:pay_sub
  FR: Abonnements : {list}.
  back-EN: Subscriptions: {list}.
  EN: Plans: {list}.
  verdict: minor
  note: EN 'Plans' is broader than 'Abonnements' (a network plan is not always a recurring subscription).
  suggested fix (FR): Formules : {list}.

- id: map:c_unnamed
  FR: Station de recharge pour voitures électriques
  back-EN: Electric car charging station
  EN: EV charging station
  verdict: ok

- id: prices:src_ops
  FR: Pages tarifaires de {n} opérateurs et {m} articles de presse datés citant les opérateurs ; chaque lien figure à côté de son prix sur les pages pays.
  back-EN: Pricing pages of {n} operators and {m} dated press articles quoting the operators; each link sits next to its price on the country pages.
  EN: Price pages of {n} operators and {m} dated news reports quoting operators; every link is next to its price on the country pages.
  verdict: ok

- id: shell:sources_p
  FR: Les données proviennent de {n} sources ouvertes : registres officiels, Open Charge Map, OpenStreetMap et données ouvertes publiées par les réseaux eux-mêmes. La liste complète, avec licences et attributions, figure sur une seule page :
  back-EN: The data come from {n} open sources: official registers, Open Charge Map, OpenStreetMap and open data published by the networks themselves. The full list, with licences and attributions, is on a single page:
  EN: The data comes from {n} open sources: official registries, Open Charge Map, OpenStreetMap and networks' own open data. The full list with licences and attribution is on one page:
  verdict: ok

- id: map:sources_btn
  FR: Sources et licences
  back-EN: Sources and licences
  EN: Sources and licences
  verdict: ok

- id: prices:st_dc
  FR: DC 50–149 kW, par kWh
  back-EN: DC 50–149 kW, per kWh
  EN: DC 50–149 kW, per kWh
  verdict: ok

- id: pages:st_dc50
  FR: avec DC à partir de 50 kW
  back-EN: with DC from 50 kW
  EN: with DC from 50 kW
  verdict: ok

- id: map:f_net
  FR: Réseau
  back-EN: Network
  EN: Network
  verdict: ok

- id: map:t_unk
  FR: Puissance inconnue
  back-EN: Unknown power
  EN: Power unknown
  verdict: ok

- id: map:attr_map
  FR: Carte
  back-EN: Map
  EN: Map
  verdict: ok

- id: map:ch_ft_checked
  FR: vérifié
  back-EN: checked
  EN: checked
  verdict: ok

- id: map:ch_nav_region
  FR: Région (en anglais)
  back-EN: Region (in English)
  EN: Region (English)
  verdict: ok

- id: shell:home_lead
  FR: Une seule carte : {n} dans {c}, à partir de données ouvertes. Chaque site indique l’origine de ses données et la date de sa dernière confirmation.
  back-EN: One map: {n} in {c}, from open data. Each site shows where its data comes from and when it was last confirmed.
  EN: One map: {n} in {c}, from open data. Every place shows where its data comes from and when it was last confirmed.
  verdict: ok

- id: prices:h_chart
  FR: Recharge rapide et électricité domestique par pays
  back-EN: Fast charging and home electricity by country
  EN: Fast charging and home electricity by country
  verdict: ok

- id: map:t_dc
  FR: DC jusqu’à 149 kW
  back-EN: DC up to 149 kW
  EN: DC up to 149 kW
  verdict: ok

- id: prices:kick_index
  FR: Indice des prix
  back-EN: Price index
  EN: Price index
  verdict: ok

- id: map:r_ok
  FR: Merci. Les signalements sont examinés une fois par semaine ; la correction apparaît après la prochaine mise à jour des données.
  back-EN: Thanks. Reports are reviewed once a week; the fix appears after the next data update.
  EN: Thank you. Reports are reviewed once a week; a correction appears after the next data update.
  verdict: ok

- id: prices:out_unit
  FR: pas au kWh
  back-EN: not per kWh
  EN: not per kWh
  verdict: ok

- id: prices:pr_street
  FR: Sans borne à domicile
  back-EN: Without a home charger
  EN: No home charger
  verdict: ok

- id: prices:plan_sub
  FR: Abonnement
  back-EN: Subscription
  EN: Plan
  verdict: minor
  note: Same as pay_sub: EN 'Plan' rendered as 'Abonnement'; keep consistent with whatever pay_sub uses.
  suggested fix (FR): Formule

- id: pages:sources_note
  FR: Chaque site conserve la source de ses données ; la licence de chaque source est indiquée ici. Les noms des réseaux appartiennent à leurs propriétaires.
  back-EN: Each site keeps the source of its data; the licence of each source is given here. Network names belong to their owners.
  EN: Every location keeps the source of its data; the licence of each source is listed here. Network names belong to their owners.
  verdict: ok

- id: map:ch_ft_charging
  FR: Recharge
  back-EN: Charging
  EN: Charging
  verdict: ok

- id: pages:th_city
  FR: Ville
  back-EN: City
  EN: City
  verdict: ok

- id: prices:st_ac
  FR: AC, par kWh
  back-EN: AC, per kWh
  EN: AC, per kWh
  verdict: ok

- id: pages:fast_more
  FR: {shown} bornes de recharge rapide affichées sur {total} ; la carte les montre toutes.
  back-EN: {shown} of {total} fast chargers shown; the map shows all of them.
  EN: Showing {shown} of {total} fast chargers; the map shows all.
  verdict: ok

- id: map:lead
  FR: Bornes de recharge publiques hors de Serbie et de la région, à partir de données ouvertes.
  back-EN: Public charging stations outside Serbia and the region, from open data.
  EN: Public chargers outside Serbia and the region, from open data.
  verdict: ok

- id: prices:h_n_compare
  FR: Comparaison avec le pays et le domicile
  back-EN: Comparison with the country and home
  EN: Compared with the country and with home
  verdict: ok

- id: map:acc_restricted_private
  FR: Privé
  back-EN: Private
  EN: Private
  verdict: ok

- id: prices:th_fees
  FR: Autres frais
  back-EN: Other fees
  EN: Other fees
  verdict: ok

- id: pages:nav_hub
  FR: Stations de recharge
  back-EN: Charging stations
  EN: Charging stations
  verdict: ok

- id: map:acc_public_notice_required
  FR: Public, sur demande préalable
  back-EN: Public, with advance request
  EN: Public, by prior notice
  verdict: minor
  note: 'by prior notice' (inform in advance) became 'sur demande préalable' (ask in advance) — slight shift towards needing permission.
  suggested fix (FR): Public, sur préavis

- id: map:ch_ft_claim
  FR: Où recharger une voiture électrique en Serbie et dans les pays voisins, à quel prix et selon quelles règles.
  back-EN: Where to charge an electric car in Serbia and neighbouring countries, at what price and under which rules.
  EN: Where to charge an electric car in Serbia and its neighbours, what it costs and what the rules are.
  verdict: ok

- id: prices:th_cindex
  FR: Indice du pays
  back-EN: Country index
  EN: Country index
  verdict: ok

- id: pages:nav_about
  FR: À propos des données
  back-EN: About the data
  EN: About the data
  verdict: ok

- id: pages:p_hub
  FR: Les pays comptant au moins 100 sites publics de fiabilité moyenne ou élevée ont une page. Les Balkans occidentaux sont couverts par les pages BlokVolt de chaque pays.
  back-EN: Countries with at least 100 public sites of medium or high reliability have a page. The Western Balkans are covered by the BlokVolt pages of each country.
  EN: Countries with at least 100 public locations of medium or high reliability have a page. The Western Balkans are covered by the BlokVolt pages of each country.
  verdict: ok

- id: map:close
  FR: Fermer
  back-EN: Close
  EN: Close
  verdict: ok

- id: pages:p1
  FR: AC jusqu'à 7 kW
  back-EN: AC up to 7 kW
  EN: AC up to 7 kW
  verdict: ok

- id: pages:net_page
  FR: page du réseau
  back-EN: network page
  EN: network page
  verdict: ok

- id: prices:chart_desc
  FR: Diagramme en barres, EUR par kWh : l'indice DC 50–149 kW et le prix de l'électricité domestique pour chaque pays doté d'un indice. Les mêmes chiffres figurent dans le tableau ci-dessous.
  back-EN: Bar chart, EUR per kWh: the DC 50–149 kW index and the home electricity price for each country with an index. The same figures are in the table below.
  EN: Bar chart, EUR per kWh: the DC 50–149 kW index and the household electricity price for each country with an index. The same numbers are in the table below.
  verdict: ok

- id: pages:d_network
  FR: Sites de recharge {net} {country_u} d'après les données ouvertes : puissance, prises et villes, avec les sources.
  back-EN: {net} charging sites {country_u} from open data: power, connectors and cities, with sources.
  EN: {net} charging locations {country_u} from open data: power, connectors and cities, with sources.
  verdict: ok

- id: map:net_remove
  FR: Retirer le filtre : {x}
  back-EN: Remove filter: {x}
  EN: Remove filter: {x}
  verdict: ok

- id: prices:cars_note
  FR: Consommation prise sur la batterie par temps doux, estimation (Open EV Data, © 2019 Chargeprice, MIT) ; en hiver, environ 20–30 % de plus. Pertes pendant la recharge non comprises. Prix publics : l'indice du pays ; à défaut — « — ».
  back-EN: Consumption drawn from the battery in mild weather, estimate (Open EV Data, © 2019 Chargeprice, MIT); in winter about 20–30% more. Charging losses not included. Public prices: the country index; otherwise '—'.
  EN: Consumption from the battery in mild weather, an estimate (Open EV Data, © 2019 Chargeprice, MIT); in winter about 20–30 % more. Losses while charging not included. Public prices: the country index; where there is none — “—”.
  verdict: ok

- id: pages:th_lc
  FR: Dernière confirmation
  back-EN: Last confirmed
  EN: Last confirmed
  verdict: ok

- id: shell:about_more
  FR: Comment les données sont collectées et vérifiées
  back-EN: How data is collected and checked
  EN: How the data is collected and checked
  verdict: ok

- id: map:conf_hi
  FR: Élevée
  back-EN: High
  EN: High
  verdict: ok

- id: pages:p_gnet
  FR: {net} est présent dans {n_countries}.
  back-EN: {net} is present in {n_countries}.
  EN: {net} appears in {n_countries}.
  verdict: ok

- id: map:lg_hpc
  FR: 150 kW et plus
  back-EN: 150 kW and above
  EN: 150+ kW
  verdict: ok

- id: shell:method_desc
  FR: Comment les sites sont fusionnés, quelle est la fiabilité de chacun et quelles pages existent.
  back-EN: How sites are merged, how reliable each one is and which pages exist.
  EN: How places are merged, how reliable each one is and which pages exist.
  verdict: ok

- id: pages:h_balkan
  FR: Balkans occidentaux
  back-EN: Western Balkans
  EN: Western Balkans
  verdict: ok

- id: prices:th_cover
  FR: Couverture DC
  back-EN: DC coverage
  EN: DC coverage
  verdict: ok

- id: prices:th_dc
  FR: DC
  back-EN: DC
  EN: DC
  verdict: ok

- id: pages:p3
  FR: DC moins de 50 kW
  back-EN: DC under 50 kW
  EN: DC under 50 kW
  verdict: ok
