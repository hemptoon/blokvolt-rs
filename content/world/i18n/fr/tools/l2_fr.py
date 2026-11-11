#!/usr/bin/env python3
"""L2-fr (LANG pool, 11.11.2026): FR for the 274 keys added after L-FR
(strings_map ci_* + emb_open, strings_pay, strings_press, strings_b2b, strings_embed)
and texts.json sections pay / routes (LANG0 format: node path -> text).

Typography is applied here: U+00A0 before : ; ? ! and inside « », apostrophe ’.
Run from anywhere: python3 content/world/i18n/fr/tools/l2_fr.py
"""
import json, re
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
WORLD = HERE.parents[1]

MAP = {
    'ci_h': 'La borne fonctionne-t-elle ?',
    'ci_radi': 'Fonctionne',
    'ci_ne_radi': 'Ne fonctionne pas',
    'ci_zauzeto': 'Occupée',
    'ci_last_ok': 'Fonctionnement confirmé par des conducteurs : {d}',
    'ci_last_ne_radi': 'Dernier signalement : ne fonctionne pas, {d}',
    'ci_last_zauzeto': 'Dernier signalement : occupée, {d}',
    'ci_n30': 'Signalements des 30 derniers jours : {n}',
    'ci_thanks': 'Merci. Votre réponse s’affiche dans la fiche pour les autres conducteurs.',
    'ci_once': 'Votre réponse pour cette borne est déjà enregistrée aujourd’hui.',
    'ci_paid': 'Combien avez-vous payé ?',
    'ci_amt': 'Montant',
    'ci_cur': 'Devise',
    'ci_unit': 'Prix par',
    'ci_u_kwh': 'kWh',
    'ci_u_min': 'minute',
    'ci_u_session': 'session de recharge',
    'ci_month': 'Mois',
    'ci_need_amt': 'Saisissez le montant, par exemple 0,59.',
    'ci_far': 'C’est loin du tarif public du réseau ({p} par kWh). Vérifiez le montant, la devise et l’unité, puis appuyez de nouveau sur « Envoyer » pour confirmer.',
    'ci_paid_ok': 'Merci. Les prix signalés par les conducteurs sont comparés une fois par semaine au tarif publié du réseau.',
    'ci_err': 'La réponse n’a pas été envoyée. Réessayez.',
    'ci_err_limit': 'Trop de réponses depuis cette adresse aujourd’hui. Réessayez demain.',
    'ci_demo': 'Version d’aperçu : rien n’a été enregistré.',
    'ci_demo_note': 'Version d’aperçu : les réponses ne sont pas enregistrées.',
    'ci_rules_h': 'Règles et confidentialité',
    'ci_rules': 'Aucun compte n’est nécessaire. Seules comptent les réponses de conducteurs différents. Un prix est comparé au tarif publié du réseau ; il ne devient candidat à l’indice des prix que si deux conducteurs signalent indépendamment le même prix, et les prix impossibles sont masqués. Les réponses contenant de la publicité, des liens ou des données personnelles sont supprimées. Les mêmes règles s’appliquent à tous les réseaux.',
    'ci_privacy': 'Sont conservés : la borne, votre réponse, le prix s’il est indiqué, la langue et une empreinte quotidienne de la connexion — un hachage à clé qui change chaque jour, et non l’adresse IP. Pas de cookies, pas d’e-mail. Seuls des totaux sont affichés : la dernière confirmation et le nombre de signalements.',
    'emb_open': 'Ouvrir sur BlokVolt',
}

PAY = {
    'nav_pay': 'Comment payer',
    'nav_routes': 'Itinéraires',
    'kick_pay': 'Comment payer',
    'kick_routes': 'Itinéraires',
    't_pay_hub': 'Comment payer la recharge d’une voiture électrique en Europe',
    'h1_pay_hub': 'Comment payer la recharge en Europe',
    'd_pay_hub': 'Paiement par carte sans inscription selon les règles de l’UE, applications des réseaux, applications et badges d’itinérance par pays, avec les pages officielles de couverture et leur date de vérification.',
    'lead_pay_hub': 'Trois façons de payer : une carte bancaire directement à la borne (sans inscription), l’application du réseau lui-même, ou une application ou un badge d’itinérance valable sur de nombreux réseaux. La couverture ci-dessous provient uniquement des pages officielles de chaque application, avec leur date de vérification.',
    't_pay_country': 'Comment payer la recharge d’une voiture électrique {cu}',
    'd_pay_country': 'Paiement par carte à la borne, applications des réseaux, applications et badges d’itinérance qui fonctionnent {cu}, prix habituels et péages — avec les sources.',
    'h_afir': 'Payer par carte bancaire (règle de l’UE)',
    # {name} is a bare country name: no article in FR, so a label construction
    'afir_eu': '{name} : pays de l’Union européenne, où le règlement sur le déploiement d’une infrastructure pour carburants alternatifs (AFIR) s’applique aux bornes publiques.',
    'afir_non': '{name} : pays hors de l’Union européenne. L’AFIR est un règlement de l’UE et les règles ci-dessous peuvent ne pas s’y appliquer. Consultez les conditions du réseau.',
    'afir_src': 'Source : règlement (UE) 2023/1804 sur EUR-Lex, version au {date}.',
    'h_nets': 'Principaux réseaux et leurs applications',
    'nets_note': 'Réseaux classés selon le nombre de sites DC de 50 kW et plus dans la couche publique. La plupart des réseaux ont leur propre application ; la page des prix indique les prix sans inscription et dans l’application, avec les sources.',
    'th_net': 'Réseau',
    'th_dc': 'Sites DC ≥ 50 kW',
    'th_prices': 'Prix',
    'th_page': 'Page du réseau',
    'lnk_prices': 'prix',
    'lnk_page': 'sites',
    'h_apps': 'Applications et badges d’itinérance',
    'apps_note': 'Mêmes colonnes pour chaque application. « Mentionné » signifie que la page officielle de couverture de l’application cite le pays ; cela ne veut pas dire que toutes les bornes l’acceptent. Aucun lien partenaire.',
    'th_app': 'Application ou badge',
    'th_cover': 'Pays sur la page officielle de couverture',
    'th_src': 'Source',
    'th_checked': 'Vérifié',
    'cov_yes': 'Mentionné',
    'cov_no': 'Non mentionné',
    'h_typical': 'Prix habituels',
    'typ_line': 'Indice des prix pour ce pays : AC {ac}, DC {dc}, HPC {hpc} par kWh (sans inscription, EUR).',
    'typ_none': 'Pas encore assez de prix officiels pour établir un indice pour ce pays.',
    'typ_more': 'Tous les prix et sources',
    'h_road': 'Péages et vignettes',
    'sys_vignette': 'Vignette autoroutière (valable pour une durée).',
    'sys_distance': 'Péage selon la distance (barrières de péage ou télépéage).',
    'sys_none': 'Pas de péage autoroutier pour les voitures.',
    'sys_mixed': 'Vignette et péages sur certains tronçons.',
    'road_src': 'Page officielle',
    'road_none': 'Pas encore vérifié.',
    'h_conn': 'Prises et sites',
    'conn_txt': 'Les prises, les bornes rapides et les réseaux figurent sur la page du pays : {name}.',
    'conn_lnk': 'Bornes de recharge : {name}',
    'pay_disc': 'La couverture des applications change souvent. Avant un voyage, vérifiez dans l’application elle-même. BlokVolt ne vend ni recharge ni badges et ne reçoit pas d’argent des applications ni des réseaux.',
    'h_countries': 'Pays',
    'h_apps_all': 'Applications et badges : couverture officielle',
    'apps_n': 'pays mentionnés : {n}',
    't_routes': 'Voyager en voiture électrique dans les Balkans : bornes rapides par itinéraire',
    'h1_routes': 'Itinéraires en voiture électrique dans les Balkans',
    'd_routes': 'Bornes rapides de 50 kW et plus sur les itinéraires fréquentés vers et à travers les Balkans, arrêts tous les 150 km au plus, réseaux, applications, péages et coût du trajet.',
    'lead_routes': 'Pour chaque itinéraire : les bornes rapides (DC, 50 kW et plus, fiabilité 70+) à moins de {c} km de la route, une liste d’arrêts espacés de {s} km au plus et les tronçons où les données ne montrent aucune borne de ce type.',
    'th_route': 'Itinéraire',
    'th_km': '≈ km',
    'th_fast': 'Bornes rapides',
    'th_gaps': 'Écarts > 150 km',
    't_route': '{a} — {b} en voiture électrique : bornes rapides, péages, coût',
    'h1_route': '{a} — {b} en voiture électrique',
    'd_route': 'Bornes rapides sur l’itinéraire {a} — {b}, un arrêt tous les 150 km au plus, réseaux et applications par pays, péages et coût du trajet pour trois voitures.',
    'lead_route': 'Environ {km} km via {via}. Bornes rapides à moins de {c} km de la route : {n} (dont 150 kW et plus : {h}).',
    'h_stops': 'Arrêts suggérés (150 km au plus entre deux arrêts)',
    'stops_note': 'La borne rapide la plus éloignée à moins de 150 km de l’arrêt précédent ; si deux sont proches, la plus puissante. Les kilomètres sont une estimation le long de l’itinéraire. Vérifiez le site sur la carte avant de partir.',
    'th_stop_km': 'km',
    'th_place': 'Site',
    'th_kw': 'kW',
    'th_pts': 'Points de charge',
    'th_map': 'Carte',
    'lnk_map': 'sur la carte',
    'h_gaps': 'Tronçons sans borne rapide dans les données',
    'gap_line': 'km {a} – {b} : aucune borne rapide de fiabilité 70+ à moins de {c} km de la route dans la couche publique.',
    'gap_note': 'C’est une lacune des données, pas la preuve qu’il n’y a pas de borne : les bornes moins fiables ou un peu plus éloignées de la route figurent sur la carte. Prévoyez d’aborder ce tronçon avec une batterie pleine.',
    'no_gaps': 'Sur cet itinéraire, les données montrent une borne rapide au moins tous les 150 km.',
    'h_by_country': 'Réseaux, applications et péages par pays',
    'th_country': 'Pays',
    'th_top_nets': 'Réseaux sur l’itinéraire',
    'th_apps_c': 'Applications d’itinérance qui mentionnent le pays',
    'th_road': 'Péages',
    'h_cost': 'Coût du trajet',
    'cost_note': 'Toute la recharge se fait sur des bornes DC publiques au prix de l’indice DC du pays, pertes de recharge non comptées. Pour les pays encore sans indice, la moyenne DC européenne ({eu}) est utilisée : {miss}.',
    'cost_all': 'tous les pays de l’itinéraire ont un indice',
    'th_car': 'Voiture',
    'th_cons': 'kWh / 100 km',
    'th_trip': 'Trajet, EUR',
    'h_season': 'Hiver et été',
    'season': 'En hiver, l’autonomie baisse et la recharge DC est plus lente avec une batterie froide : prévoyez des étapes plus courtes, préchauffez la batterie avant une borne rapide si la voiture le permet et abordez les cols de montagne avec une réserve. En été, les itinéraires vers la côte sont les plus chargés les week-ends de juillet et d’août : il peut y avoir de l’attente aux bornes d’autoroute, et une borne à quelques kilomètres de la route peut faire gagner du temps.',
    'h_method': 'Mode de calcul',
    'method': 'L’itinéraire est une suite de villes sur l’autoroute ; la distance est la somme des segments en ligne droite entre elles, plus {f} % : c’est une estimation. Les bornes proviennent de la couche publique du {date} : DC 50 kW et plus, fiabilité 70 et plus, accès public, à {c} km au plus du tracé. Pas de disponibilité en temps réel.',
    'routes_more': 'Tous les itinéraires',
    'pay_more': 'Comment payer',
    'checked': 'Données du {date}',
    'via': ', ',
    'cov_unk': 'Liste des pays non publiée',
    'apps_unk': 'la page officielle ne donne pas de liste de pays',
}

PRESS = {
    'nav_press': 'Médias',
    'ft_press': 'Médias : indice des prix',
    't_press': 'Indice européen des prix de la recharge — espace médias | BlokVolt',
    'd_press': 'Indice européen mensuel des prix de la recharge : chiffres clés, graphiques à intégrer, règles de citation et contact pour les journalistes.',
    'kick_press': 'Médias',
    'h1_press': 'Indice européen des prix de la recharge : espace médias',
    'lead_press': 'Chaque mois : ce que coûte la recharge publique en Europe, pays par pays, comparé au prix de l’électricité à domicile. Chiffres, graphiques et données sont libres d’utilisation avec la mention de la source et un lien.',
    'issue_of': 'Numéro du {date}',
    'h_latest': 'Dernier numéro : {month}',
    'read_issue': 'Lire le numéro complet',
    'h_key': 'Chiffres clés',
    'h_charts': 'Graphiques à intégrer',
    'charts_p': 'Le graphique intégré affiche toujours le dernier numéro. Pour l’impression ou un mois précis, prenez le fichier SVG de ce mois.',
    'embed_code': 'Code d’intégration',
    'svg_file': 'Fichier SVG, {month}',
    'ch_dc_home': 'Recharge rapide (DC) et électricité à domicile, €/kWh',
    'ch_dc_home_d': 'Prix moyen sans inscription de la recharge DC de 50 kW et plus dans chaque pays, à côté du prix de l’électricité des ménages, en euros par kWh TTC.',
    'ch_europe': 'Europe : prix moyen sans inscription par classe de recharge, €/kWh',
    'ch_europe_d': 'Prix moyen pondéré sans inscription par kWh TTC dans les pays de l’indice : AC, DC 50–149 kW et HPC 150 kW et plus.',
    'lg_dc': 'Recharge DC',
    'lg_home': 'Électricité à domicile',
    'cls_ac': 'AC',
    'cls_dc': 'DC 50–149 kW',
    'cls_hpc': 'HPC ≥ 150 kW',
    'credit': 'Source : BlokVolt, Indice européen des prix de la recharge, {month}',
    'h_cite': 'Comment citer',
    'cite_1': 'Mentionnez l’indice et le mois, avec un lien vers la page des prix, par exemple :',
    'cite_2': 'Les chiffres et graphiques peuvent être cités, reproduits et intégrés dans des contenus éditoriaux sans autorisation préalable, avec cette mention. Les fichiers CSV sont sous licence CC BY-NC 4.0 : utilisation libre à des fins non commerciales avec mention de la source ; toute utilisation commerciale des données (produits, rapports payants, revente) nécessite un accord écrit.',
    'cite_3': 'Merci de présenter les prix comme des moyennes des prix sans inscription tirés des grilles tarifaires des réseaux, et non comme ce que paie chaque conducteur : les abonnements et les applications d’itinérance peuvent être moins chers ou plus chers.',
    'h_contact': 'Contact',
    'contact_p': 'Questions sur les chiffres, la méthode ou un pays : {email}. Réponse sous 48 heures. Le prochain numéro paraît dans les premiers jours du mois.',
    'h_archive': 'Tous les numéros',
    'h_data': 'Données et méthode',
    'data_csv': 'Indice du mois, CSV',
    'method_link': 'Comment l’indice est calculé',
    'prices_link': 'Prix par pays et par réseau',
    't_issue': 'Indice européen des prix de la recharge — {month} | BlokVolt',
    'h1_issue': 'Indice européen des prix de la recharge — {month}',
    'd_issue': 'Ce qu’a coûté la recharge publique des voitures électriques en Europe en {month} : prix sans inscription AC, DC et HPC par pays, comparés à l’électricité à domicile.',
    'kick_issue': 'Numéro mensuel',
    'lead_issue': 'Prix sans inscription de {nets} réseaux dans {countries} pays, tirés des grilles tarifaires des réseaux, pondérés par le nombre de bornes.',
    # f_*: aligned with FACTS_DE_FR in scripts/world_press.py (same wording)
    'f_europe': 'La recharge rapide (DC 50–149 kW) a coûté en moyenne {dc} le kWh dans l’indice, la recharge ultra-rapide (HPC, 150 kW et plus) {hpc}, la recharge AC {ac}.',
    'f_range': 'La recharge DC était la moins chère {lo} ({lo_v}) et la plus chère {hi} ({hi_v}).',
    'f_home': 'La recharge DC publique a coûté entre {lo_r} fois ({lo}) et {hi_r} fois ({hi}) le prix de l’électricité domestique.',
    'f_mom': 'Par rapport à {prev}, la moyenne européenne DC a varié de {d} ({p}).',
    'f_mom_n': 'Pays où l’indice DC a le plus varié : {list}.',
    'f_first': 'C’est le premier numéro ; les variations d’un mois sur l’autre commencent avec le suivant.',
    'f_checkins': 'Les conducteurs ont confirmé ce mois-ci {n} prix payés aux bornes (un prix ne compte qu’avec deux signalements concordants).',
    'th_country': 'Pays',
    'th_change': 'Variation DC',
    'h_table_i': 'Prix par pays',
    'issue_note': 'Prix TTC, en euros par kWh au taux de la BCE du {fx}. Tarifs vérifiés jusqu’au {checked} ; pondération d’après la couche publique du {layer} ; électricité à domicile : {home}.',
    'embed_title': 'Graphique BlokVolt',
    'for_media_link': 'Graphiques, règles de citation et contact pour les médias',
}

B2B = {
    'title': 'Données pour les entreprises : couverture et prix de la recharge | BlokVolt',
    'desc': 'Jeux de données sur la recharge publique des voitures électriques pour les entreprises et les organismes publics : sites, puissance, réseaux et tarifs publiés par pays, avec sources et dates.',
    'h1': 'Données pour les entreprises',
    'lead': 'Données de couverture et de prix de la recharge publique, pays par pays — pour les opérateurs de recharge, les énergéticiens, les gestionnaires de flottes, les constructeurs, les cabinets de conseil, les investisseurs et les organismes publics. Chaque chiffre est accompagné de sa source et de sa date.',
    'what_h': 'Ce qui est disponible',
    'what_cov': '<b>Couverture</b> — sites de recharge publics par pays, ville et réseau : classes de puissance, part du DC et de la haute puissance, prises, nombre de sources, date de la dernière confirmation.',
    'what_price': '<b>Prix</b> — tarifs sans inscription publiés par les réseaux : prix AC, DC et haute puissance, frais de session et d’occupation, devise et EUR, TVA, source et date de vérification.',
    'what_cmp': '<b>Comparaisons</b> — recharge publique face à l’électricité domestique, synthèses par pays et par réseau, mises à jour mensuelles ou trimestrielles avec historique des modifications.',
    'focus': 'Régions prioritaires : Balkans occidentaux, Europe centrale et orientale, Turquie, Caucase et Asie centrale. Autres pays de la carte mondiale sur demande.',
    'lic_h': 'Licences',
    'lic_p': 'Les données détaillées à usage commercial sont constituées sans OpenStreetMap, à partir de registres publics ouverts, d’Open Charge Map, d’Overture Maps et des recherches propres de BlokVolt, avec un fichier d’attribution pour chaque source. Un jeu incluant OpenStreetMap n’est possible que sous Open Database License (ODbL 1.0), avec ses conditions de partage à l’identique. Les données ouvertes restent gratuites : toute la couche publique est téléchargeable sous ODbL.',
    'lic_dl': 'Télécharger les données ouvertes',
    'neutral': 'BlokVolt est indépendant des réseaux de recharge. Les clients des données n’ont aucune influence sur la carte, les pages ou l’indice des prix : ni placement payant, ni classement.',
    'form_h': 'Demander des données',
    'form_p': 'Décrivez votre besoin. La réponse vient de hello@blokvolt.com.',
    'f_name': 'Nom',
    'f_company': 'Entreprise ou organisme',
    'f_email': 'E-mail',
    'f_what': 'Données',
    'f_w_cov': 'Couverture',
    'f_w_price': 'Prix',
    'f_w_both': 'Couverture et prix',
    'f_w_other': 'Autre chose',
    'f_countries': 'Pays',
    'f_msg': 'Usage des données, format, fréquence',
    'f_ok_box': 'J’accepte que BlokVolt conserve cette demande pour y répondre.',
    'f_send': 'Envoyer la demande',
    'm_ok': 'Merci, la demande a bien été reçue.',
    'm_need': 'Renseignez le nom, l’e-mail et le message, et cochez la case de consentement.',
    'm_err': 'L’envoi a échoué. Réessayez ou écrivez à hello@blokvolt.com.',
    'm_limit': 'Trop de messages aujourd’hui. Écrivez à hello@blokvolt.com.',
    'm_demo': 'Aperçu : le formulaire fonctionne en mode démo, rien n’a été envoyé.',
    'ft_link': 'Données pour les entreprises',
}

EMBED = {
    'emb_title': 'Carte des bornes de recharge — BlokVolt',
    'emb_full': 'Ouvrir la carte complète',
    'cf_title': 'Carte des bornes de recharge pour votre site : widget gratuit | BlokVolt',
    'cf_h1': 'Une carte des bornes pour votre site',
    'cf_desc': 'Une carte mondiale gratuite des bornes de recharge publiques pour tout site web : choisissez le pays, le réseau, la puissance, la langue et le thème, puis copiez le code. Sans inscription.',
    'cf_lead': 'Les mêmes données ouvertes que la carte BlokVolt, dans un iframe sur votre page. Les données se mettent à jour automatiquement chaque semaine.',
    'cf_country': 'Pays',
    'cf_country_any': 'Monde entier (ou la vue ci-dessous)',
    'cf_view': 'Ville ou vue précise',
    'cf_view_help': 'Ouvrez la carte complète, placez-la sur la ville voulue et collez ici l’adresse de cette page.',
    'cf_view_bad': 'Ce n’est pas une adresse de la carte BlokVolt.',
    'cf_net': 'Réseau',
    'cf_net_any': 'Tous les réseaux',
    'cf_power': 'Puissance',
    'cf_lang': 'Langue',
    'cf_theme': 'Thème',
    'cf_light': 'Clair',
    'cf_dark': 'Sombre',
    'cf_height': 'Hauteur, px',
    'cf_preview': 'Aperçu',
    'cf_code': 'Code pour votre page',
    'cf_copy': 'Copier le code',
    'cf_copied': 'Copié',
    'cf_rules_h': 'Conditions',
    'cf_rules': 'Le widget est gratuit, y compris sur les sites commerciaux. Laissez visibles la ligne d’attribution et le lien vers BlokVolt. Pas d’inscription, pas de cookies, pas de publicité dans le widget. Le widget compte seulement le nombre d’affichages sur chaque site (le nom du site, rien sur le lecteur).',
    'cf_more': 'Données ouvertes et demandes d’API',
    'cf_frame_title': 'Carte des bornes de recharge — BlokVolt',
    'cf_src': 'Source :',
    'cf_link': 'Carte des bornes BlokVolt',
    'dv_title': 'Données de recharge pour développeurs et médias : widget, données ouvertes | BlokVolt',
    'dv_h1': 'Pour les développeurs',
    'dv_desc': 'Widget de carte pour sites web, données ouvertes hebdomadaires sur les points de charge publics (ODbL), fichiers de données des Balkans et demandes de données supplémentaires.',
    'dv_lead': 'Tout ce qui est ouvert est gratuit et ne demande aucune clé. Pour le reste, envoyez une demande.',
    'dv_widget_h': 'Widget de carte',
    'dv_widget_p': 'Un iframe avec la carte mondiale : pays, ville, réseau, puissance, langue et thème se règlent dans l’adresse.',
    'dv_widget_btn': 'Générer le code',
    'dv_params_h': 'Paramètres du widget',
    'dv_p_zemlja': 'Pays, code ISO 3166-1 alpha-2 (DE, FR…)',
    'dv_p_grad': 'Ville, identifiant GeoNames (repris d’un lien de la carte complète)',
    'dv_p_mreza': 'Identifiant (slug) du réseau ; plusieurs, séparés par des virgules',
    'dv_p_snaga': 'Classes de puissance : ac, dc, hpc, nepoznato (inconnue)',
    'dv_p_tema': 'tamna = fond de carte sombre',
    'dv_p_lang': 'Langue : selon l’adresse du widget (EN, SR, RU)',
    'dv_p_hash': 'Vue précise : #zoom/latitude/longitude à la fin de l’adresse',
    'dv_open_h': 'Données ouvertes de la carte mondiale',
    'dv_open_p': 'Un fichier CSV hebdomadaire de la couche publique, ODbL 1.0, colonnes : {n}.',
    'dv_open_btn': 'Téléchargement et colonnes',
    'dv_freq_h': 'Fréquence de mise à jour',
    'dv_freq_p': 'La couche mondiale, le widget et le fichier CSV : une fois par semaine. La date des données figure sur la carte et dans le fichier.',
    'dv_balkan_h': 'Serbie et Balkans',
    'dv_balkan_p': 'Les stations des sections régionales sous forme de fichiers JSON (OpenStreetMap ODbL, Open Charge Map CC BY 4.0) :',
    'dv_balkan_rs': 'Serbie : JSON ouvert, tableaux de prix en CSV et widget serbe sur blokvolt.rs',
    'dv_attr_h': 'Comment créditer',
    'dv_req_h': 'Demander un accès',
    'dv_req_p': 'API, champs supplémentaires, autres formats ou licence pour un usage hors ODbL : décrivez le projet. La réponse arrive par e-mail sous 48 heures.',
    'dv_f_name': 'Nom ou entreprise',
    'dv_f_email': 'E-mail',
    'dv_f_site': 'Site ou application (facultatif)',
    'dv_f_msg': 'Quelles données, et pour quel usage',
    'dv_f_send': 'Envoyer la demande',
    'dv_f_ok': 'Demande envoyée. La réponse arrivera par e-mail.',
    'dv_f_err': 'La demande n’a pas été envoyée. Réessayez ou écrivez à l’adresse ci-dessous.',
    'dv_f_demo': 'Aperçu : ici, le formulaire n’envoie rien. Écrivez à l’adresse ci-dessous.',
    'dv_f_need': 'Indiquez l’e-mail et la description.',
    'dv_contact': 'Ou écrivez à',
}

TEXT_PAY = {
    'afir.points[0]': 'Recharge sans inscription (ad hoc) : vous pouvez recharger sans vous inscrire ni signer de contrat avec l’opérateur.',
    'afir.points[1]': 'Les opérateurs de bornes publiques doivent proposer la recharge sans inscription avec un moyen de paiement largement utilisé dans l’UE.',
    'afir.points[2]': 'Les nouvelles bornes publiques de 50 kW et plus installées à partir du 13 avril 2024 doivent accepter les cartes bancaires via un lecteur de cartes ou un dispositif sans contact.',
    'afir.points[3]': 'Les nouvelles bornes publiques de moins de 50 kW peuvent proposer à la place un paiement en ligne, par exemple via le QR code de la borne.',
    'afir.points[4]': 'À partir du 1er janvier 2027, cela s’applique aussi aux stations existantes de 50 kW et plus sur le réseau routier RTE-T et sur les aires de stationnement sûres et sécurisées.',
    'afir.points[5]': 'Le prix sans inscription et ses composantes doivent être affichés à la station avant le début de la recharge.',
}

# route stop towns: EN -> FR (exonyms where French has one, otherwise the local name)
TOWN = {'Salzburg': 'Salzbourg', 'Belgrade': 'Belgrade', 'Sofia': 'Sofia'}

NBSP = ' '


def typo(s):
    s = s.replace("'", '’')
    s = re.sub(r' ([:;?!])', NBSP + r'\1', s)
    s = s.replace('« ', '«' + NBSP).replace(' »', NBSP + '»')
    s = re.sub(r'(\d|\}) %', r'\1' + NBSP + '%', s)
    return s


def nodes(n, p, out):
    if isinstance(n, dict):
        if isinstance(n.get('en'), str) and {'sr', 'ru'} <= set(n):
            out[p] = n
            return
        for k, v in n.items():
            nodes(v, f'{p}.{k}' if p else k, out)
    elif isinstance(n, list):
        for i, v in enumerate(n):
            nodes(v, f'{p}[{i}]', out)


def main():
    # strings
    m = json.loads((HERE / 'strings_map.json').read_text())
    m.update(MAP)
    src = json.loads((WORLD / 'strings_map.json').read_text())
    m = {k: (typo(m[k]) if isinstance(m[k], str) and k in MAP else m[k]) for k in src}  # EN key order
    (HERE / 'strings_map.json').write_text(json.dumps(m, ensure_ascii=False, indent=1) + '\n')
    for name, d in (('pay', PAY), ('press', PRESS), ('b2b', B2B), ('embed', EMBED)):
        src = json.loads((WORLD / f'strings_{name}.json').read_text())
        assert set(src) == set(d), (name, set(src) ^ set(d))
        (HERE / f'strings_{name}.json').write_text(
            json.dumps({k: typo(d[k]) for k in src}, ensure_ascii=False, indent=1) + '\n')
    # texts.json: pay / routes
    t = json.loads((HERE / 'texts.json').read_text())
    pn, rn = {}, {}
    nodes(json.loads((WORLD / 'pay.json').read_text()), '', pn)
    nodes(json.loads((WORLD / 'routes.json').read_text()), '', rn)
    assert set(pn) == set(TEXT_PAY), set(pn) ^ set(TEXT_PAY)
    t['pay'] = {k: typo(TEXT_PAY[k]) for k in pn}
    t['routes'] = {k: TOWN.get(v['en'], v['en']) for k, v in rn.items()}
    (HERE / 'texts.json').write_text(json.dumps(t, ensure_ascii=False, indent=1) + '\n')
    print('map', len(MAP), 'pay', len(PAY), 'press', len(PRESS), 'b2b', len(B2B), 'embed', len(EMBED),
          'texts.pay', len(t['pay']), 'texts.routes', len(t['routes']))


if __name__ == '__main__':
    main()
