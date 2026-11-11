# R-FR — relecture de la traduction française (pool 4, 10.11.2026)

Base : `origin/l-fr` (8456166). Branche : `r-fr`. Relecteur indépendant ; le travail L-FR était déjà de bonne qualité.

## Chiffres
- Chaînes : 403 relues, **49 modifiées** : 24 sur le fond (map 12, pages 5, prices 7, shell 0) + 25 uniquement typographiques (espace insécable entre nombre et kW/kWh/km, 33 occurrences).
- `texts.json` : 1 correction (`about_data.conf_p`) ; clé `sources_pages` retirée (consigne 23:55 : `sources_pages.json` ne se traduit pas ; contrat = `about_data` + `download`). `check.py` aligné.
- Pays : 150 relus, 0 correction (noms CLDR et prépositions en/au/aux/à justes).
- Villes : relues toutes celles de FR (568), BE (147), CH (54), LU (3), CA (233, Québec compris) + les 500 premières `stage=month` hors de ces pays (ordre du fichier : `places-2026-11-09.json` ne contient pas de comptage). **5 corrections** d’exonymes archaïques → forme moderne : Bréda→Breda, Tilbourg→Tilburg, Ruremonde→Roermond, Ludwigsbourg→Ludwigsburg, Cassel→Kassel. `in_phrase` vérifiés mécaniquement (Le→au, Les→aux, sinon à) : 3 exceptions voulues (Le Bronx, Central Coast, Blue Mountains).
- Slugs : naturels, ASCII, aucun conflit (`/fr/` n’existe pas dans `content/com/local/`). Aucun changement.
- `check.py` : 0 erreur. Rétrotraduction aveugle de 40 lignes (23 modifiées + 17 au hasard) : ok 36, minor 4, mismatch 0 ; 3 minor corrigés.

## Corrections principales
- Cas grammatical : `t_city`, `t_city_cc`, `d_city` passent de « à {city} » à `{city_u}` (décision 00:12) → « au Havre », « aux Sables-d’Olonne » corrects.
- Pluriels cassés avec n = 1 : `sources_n` → « Sources : {n} » ; `fast_more`, `no_prices_n`, `c_lead` reformulés sans accord sur le nombre.
- Sens : `disc` (un site ne « diffère » pas d’un prix → « le prix d’un site… ») ; `c_price_note` (« sur ce site » ambigu site web/lieu → « à cet endroit ») ; `noprice_p` (parallélisme) ; `m3` (« est pondéré par ») ; `conf_p` (« la même formule… tous les réseaux »).
- Cohérence : « avec abonnement » → « avec formule » dans `d_country`, `d_net`, `c_lead` (Plan = Formule partout).
- Longueur boutons/puces (≤ EN × 1,4) : `filters_show` Voir les filtres, `reset` Réinitialiser, `c70` Élevée, `lg_hpc` ≥ 150 kW, `download` Télécharger, `attr_show` Données et licences, `r_nije_javni` Non public, `acc_restricted_customers_staff` Clients et personnel, `open_map_dc` Bornes rapides sur la carte, `c_unnamed` Borne de recharge.

## Points discutables (non tranchés)
1. « ad hoc » = « sans inscription » (glossaire). Avis du relecteur : « sans abonnement » est plus courant chez les opérateurs français et dans les comparateurs ; « sans inscription » reste exact. Gardé selon le glossaire — à Andreï de trancher.
2. `acc_pub` « Accès public » perd le « uniquement » de « Public only » ; dans le groupe radio avec « Afficher aussi les autres » le sens reste clair. Alternative plus longue : « Publics uniquement » (20 car., > limite).
3. `t_near` « (près de {x}) » sans élision (« près de Ulm ») — à régler dans le moteur K8.
4. Valence (Espagne) homonyme de Valence (France) : le titre porte le pays, donc acceptable.
5. Plusieurs clés (`d_country`, `disc`, `t_country`) existent dans `strings_pages` et `strings_prices` avec des EN différents : vérifié, chaque fichier FR suit son fichier EN.


## L2-fr — обратный перевод новых строк (11.11.2026)

60 случайных строк из 274 новых ключей + `texts.pay` (seed 42), агент без доступа к EN.
Смысл: 60 ok, расхождений 0. Замечаний по языку: 5, все приняты:
- `pay.afir_non` — «une législation» → «un règlement de l’UE»;
- `pay.lead_route`, `pay.lead_routes` — «à {c} km au plus de la route» → «à moins de {c} km de la route»;
- `map.ci_privacy`, `map.ci_once` — «le site» читается как «веб-сайт» → «la borne»;
- `press.f_mom_n` — «la valeur DC» → «Pays où l’indice DC a le plus varié : {list}.»;
- `press.f_home` — «de … à … fois» → «entre … et … fois».
