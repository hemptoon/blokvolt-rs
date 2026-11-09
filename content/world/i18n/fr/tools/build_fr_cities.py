#!/usr/bin/env python3
"""Build French city names (name + locative) for the BlokVolt world layer.

Input : /home/claude/blokvolt-rs/content/world/names/cities.csv (read-only)
Output: /home/claude/work/out/cities.csv  (geonameid,name,in_phrase,decl_ok,note)
"""
import csv, re, sys, unicodedata

SRC = "/home/claude/blokvolt-rs/content/world/names/cities.csv"
OUT = "/home/claude/work/out/cities.csv"

# Established French exonyms, keyed by (cc, name_local) or (cc, name_en).
EX = {
    # Germany
    ("DE", "München"): "Munich", ("DE", "Köln"): "Cologne", ("DE", "Nürnberg"): "Nuremberg",
    ("DE", "Frankfurt am Main"): "Francfort-sur-le-Main", ("DE", "Frankfurt (Oder)"): "Francfort-sur-l'Oder",
    ("DE", "Hamburg"): "Hambourg", ("DE", "Bremen"): "Brême", ("DE", "Dresden"): "Dresde",
    ("DE", "Trier"): "Trèves", ("DE", "Aachen"): "Aix-la-Chapelle", ("DE", "Mainz"): "Mayence",
    ("DE", "Braunschweig"): "Brunswick", ("DE", "Hannover"): "Hanovre", ("DE", "Koblenz"): "Coblence",
    ("DE", "Regensburg"): "Ratisbonne", ("DE", "Augsburg"): "Augsbourg",
    ("DE", "Freiburg im Breisgau"): "Fribourg-en-Brisgau", ("DE", "Saarbrücken"): "Sarrebruck",
    ("DE", "Saarlouis"): "Sarrelouis", ("DE", "Zweibrücken"): "Deux-Ponts", ("DE", "Würzburg"): "Wurtzbourg",
    ("DE", "Brandenburg an der Havel"): "Brandebourg-sur-la-Havel", ("DE", "Magdeburg"): "Magdebourg",
    ("DE", "Speyer"): "Spire", ("DE", "Konstanz"): "Constance", ("DE", "Kassel"): "Cassel",
    ("DE", "Hameln"): "Hamelin", ("DE", "Lüneburg"): "Lunebourg", ("DE", "Oldenburg"): "Oldenbourg",
    ("DE", "Marburg"): "Marbourg", ("DE", "Lutherstadt Wittenberg"): "Wittemberg",
    ("DE", "Halle (Saale)"): "Halle-sur-Saale", ("DE", "Meißen"): "Meissen", ("DE", "Gießen"): "Giessen",
    ("DE", "Jena"): "Iéna", ("DE", "Offenbach am Main"): "Offenbach-sur-le-Main",
    ("DE", "Kleve"): "Clèves", ("DE", "Jülich"): "Juliers", ("DE", "Duisburg"): "Duisbourg",
    ("DE", "Flensburg"): "Flensbourg", ("DE", "Offenburg"): "Offenbourg", ("DE", "Ludwigsburg"): "Ludwigsbourg",
    ("DE", "Aschaffenburg"): "Aschaffenbourg", ("DE", "Coburg"): "Cobourg", ("DE", "Naumburg"): "Naumbourg",
    ("DE", "Merseburg"): "Mersebourg", ("DE", "Altenburg"): "Altenbourg", ("DE", "Ravensburg"): "Ravensbourg",
    ("DE", "Neubrandenburg"): "Neubrandebourg", ("DE", "Siegburg"): "Siegbourg",
    ("DE", "Oranienburg"): "Oranienbourg", ("DE", "Homburg"): "Hombourg",
    ("DE", "Limburg an der Lahn"): "Limbourg-sur-la-Lahn", ("DE", "Lutherstadt Eisleben"): "Eisleben",
    ("DE", "Ludwigshafen am Rhein"): "Ludwigshafen", ("DE", "Landau in der Pfalz"): "Landau",
    # Netherlands
    ("NL", "Den Haag"): "La Haye", ("NL", "'s-Hertogenbosch"): "Bois-le-Duc", ("NL", "Nijmegen"): "Nimègue",
    ("NL", "Groningen"): "Groningue", ("NL", "Leiden"): "Leyde", ("NL", "Vlissingen"): "Flessingue",
    ("NL", "Breda"): "Bréda", ("NL", "Bergen op Zoom"): "Berg-op-Zoom", ("NL", "Roermond"): "Ruremonde",
    ("NL", "Middelburg"): "Middelbourg", ("NL", "Tilburg"): "Tilbourg",
    # Belgium (French forms of Flemish cities)
    ("BE", "Gent"): "Gand", ("BE", "Antwerpen"): "Anvers", ("BE", "Brugge"): "Bruges", ("BE", "Leuven"): "Louvain",
    ("BE", "Mechelen"): "Malines", ("BE", "Kortrijk"): "Courtrai", ("BE", "Oostende"): "Ostende",
    ("BE", "Ieper"): "Ypres", ("BE", "Roeselare"): "Roulers", ("BE", "Sint-Truiden"): "Saint-Trond",
    ("BE", "Tongeren"): "Tongres", ("BE", "Tienen"): "Tirlemont", ("BE", "Ronse"): "Renaix", ("BE", "Halle"): "Hal",
    ("BE", "Aalst"): "Alost", ("BE", "Sint-Niklaas"): "Saint-Nicolas", ("BE", "Geraardsbergen"): "Grammont",
    ("BE", "Oudenaarde"): "Audenarde", ("BE", "Dendermonde"): "Termonde", ("BE", "Lier"): "Lierre",
    ("BE", "Vilvoorde"): "Vilvorde", ("BE", "Menen"): "Menin", ("BE", "Diksmuide"): "Dixmude",
    ("BE", "Koksijde"): "Coxyde", ("BE", "Sint-Genesius-Rode"): "Rhode-Saint-Genèse", ("BE", "Temse"): "Tamise",
    ("BE", "Wervik"): "Wervicq", ("BE", "Kessel-Lo"): "Kessel-Lo",
    # Switzerland
    ("CH", "Chur"): "Coire", ("CH", "St. Gallen"): "Saint-Gall", ("CH", "Zürich"): "Zurich", ("CH", "Bern"): "Berne",
    ("CH", "Basel"): "Bâle", ("CH", "Luzern"): "Lucerne", ("CH", "Biel/Bienne"): "Bienne",
    ("CH", "Solothurn"): "Soleure", ("CH", "Schwyz"): "Schwytz", ("CH", "Thun"): "Thoune",
    ("CH", "Burgdorf"): "Berthoud", ("CH", "Bellinzona"): "Bellinzone", ("CH", "Grenchen"): "Granges",
    ("CH", "Winterthur"): "Winterthour", ("CH", "Stadt Winterthur (Kreis 1)"): "Winterthour (arrondissement 1)",
    # Austria
    ("AT", "Wien"): "Vienne", ("AT", "Salzburg"): "Salzbourg", ("AT", "Klagenfurt am Wörthersee"): "Klagenfurt",
    # UK / Ireland
    ("GB", "London"): "Londres", ("GB", "Edinburgh"): "Édimbourg", ("GB", "Dover"): "Douvres",
    ("GB", "Canterbury"): "Cantorbéry",
    # Iberia
    ("PT", "Lisboa"): "Lisbonne",
    ("ES", "Sevilla"): "Séville", ("ES", "Zaragoza"): "Saragosse", ("ES", "Córdoba"): "Cordoue",
    ("ES", "Barcelona"): "Barcelone", ("ES", "València"): "Valence", ("ES", "Cádiz"): "Cadix",
    ("ES", "Granada"): "Grenade", ("ES", "Tarragona"): "Tarragone", ("ES", "Pamplona"): "Pampelune",
    ("ES", "Donostia / San Sebastián"): "Saint-Sébastien",
    ("ES", "Santiago de Compostela"): "Saint-Jacques-de-Compostelle", ("ES", "A Coruña"): "La Corogne",
    ("ES", "Girona"): "Gérone", ("ES", "Lleida"): "Lérida", ("ES", "Murcia"): "Murcie", ("ES", "Toledo"): "Tolède",
    ("ES", "Segovia"): "Ségovie", ("ES", "Salamanca"): "Salamanque", ("ES", "Cartagena"): "Carthagène",
    ("ES", "Algeciras"): "Algésiras", ("ES", "Sagunto"): "Sagonte", ("ES", "Tortosa"): "Tortose",
    ("ES", "Vitoria-Gasteiz"): "Vitoria", ("ES", "Málaga"): "Malaga", ("ES", "Eivissa"): "Ibiza",
    ("ES", "Maó-Mahón"): "Mahón", ("ES", "Castelló de la Plana"): "Castellón de la Plana",
    # Italy
    ("IT", "Milano"): "Milan", ("IT", "Torino"): "Turin", ("IT", "Napoli"): "Naples", ("IT", "Venezia"): "Venise",
    ("IT", "Padova"): "Padoue", ("IT", "Mantova"): "Mantoue", ("IT", "Verona"): "Vérone", ("IT", "Bologna"): "Bologne",
    ("IT", "Trento"): "Trente", ("IT", "Parma"): "Parme", ("IT", "Modena"): "Modène",
    ("IT", "Reggio nell'Emilia"): "Reggio d'Émilie", ("IT", "Piacenza"): "Plaisance", ("IT", "Ferrara"): "Ferrare",
    ("IT", "Ravenna"): "Ravenne", ("IT", "Cremona"): "Crémone", ("IT", "Bergamo"): "Bergame", ("IT", "Como"): "Côme",
    ("IT", "Novara"): "Novare", ("IT", "Vercelli"): "Verceil", ("IT", "Aosta"): "Aoste", ("IT", "Pinerolo"): "Pignerol",
    ("IT", "Savona"): "Savone", ("IT", "Carrara"): "Carrare", ("IT", "Livorno"): "Livourne", ("IT", "Taranto"): "Tarente",
    ("IT", "Vicenza"): "Vicence", ("IT", "Brixen"): "Bressanone",
    ("IT", "Eppan an der Weinstraße"): "Appiano sulla Strada del Vino",
    # Greece
    ("GR", "Athens"): "Athènes", ("GR", "Thessaloniki"): "Thessalonique", ("GR", "Piraeus"): "Le Pirée",
    ("GR", "Heraklion"): "Héraklion", ("GR", "Chania"): "La Canée", ("GR", "Corinth"): "Corinthe",
    ("GR", "Chalkida"): "Chalcis", ("GR", "Rethymno"): "Réthymnon", ("GR", "Corfu"): "Corfou",
    ("GR", "Sparta"): "Sparte", ("GR", "Thebes"): "Thèbes", ("GR", "Megara"): "Mégare", ("GR", "Elefsina"): "Éleusis",
    ("GR", "Salamina"): "Salamine", ("GR", "Mytilene"): "Mytilène", ("GR", "Alexandroupoli"): "Alexandroupolis",
    ("GR", "Larissa"): "Larissa", ("GR", "Patras"): "Patras", ("GR", "Rhodes"): "Rhodes",
    ("GR", "Veria"): "Véria", ("GR", "Serres"): "Serrès", ("GR", "Preveza"): "Préveza",
    # Central / Eastern Europe
    ("CZ", "Praha"): "Prague", ("PL", "Warszawa"): "Varsovie", ("PL", "Kraków"): "Cracovie",
    ("RO", "București"): "Bucarest", ("RS", "Beograd"): "Belgrade", ("AL", "Tiranë"): "Tirana",
    ("XK", "Prishtinë"): "Pristina", ("LV", "Rīga"): "Riga", ("IS", "Reykjavík"): "Reykjavik",
    ("DK", "København"): "Copenhague",
    ("BG", "Burgas"): "Bourgas", ("BG", "Ruse"): "Roussé",
    ("RU", "Moscow"): "Moscou", ("RU", "Saint Petersburg"): "Saint-Pétersbourg", ("RU", "Yekaterinburg"): "Iekaterinbourg",
    ("RU", "Ufa"): "Oufa", ("RU", "Ryazan"): "Riazan", ("RU", "Irkutsk"): "Irkoutsk",
    ("RU", "Rostov-on-Don"): "Rostov-sur-le-Don", ("RU", "Novosibirsk"): "Novossibirsk",
    ("RU", "Nizhny Novgorod"): "Nijni Novgorod", ("RU", "Tyumen"): "Tioumen", ("RU", "Shushary"): "Chouchary",
    ("BY", "Grodno"): "Grodno", ("UA", "Lutsk"): "Loutsk", ("UA", "Kyiv"): "Kyiv",
    ("TR", "İstanbul"): "Istanbul", ("TR", "İzmir"): "Izmir",
    ("AZ", "Bakı"): "Bakou", ("UZ", "Toshkent"): "Tachkent", ("UZ", "Samarqand"): "Samarcande",
    ("UZ", "Gʻazalkent"): "Gazalkent", ("GE", "Tbilisi"): "Tbilissi",
    # Asia / elsewhere
    ("KR", "Seoul"): "Séoul", ("MO", "Macau"): "Macao", ("TW", "New Taipei City"): "Nouveau Taipei",
    ("EG", "New Cairo"): "Le Nouveau Caire", ("IR", "Isfahan"): "Ispahan", ("IR", "Tehran"): "Téhéran",
    ("IN", "Bengaluru"): "Bangalore", ("VN", "Hà Nội"): "Hanoï", ("SG", "Singapore"): "Singapour",
    ("ZA", "Johannesburg"): "Johannesbourg", ("PA", "Panamá"): "Panama", ("CO", "Bogotá"): "Bogota",
    ("DO", "Santo Domingo"): "Saint-Domingue", ("MX", "Ciudad de México"): "Mexico",
    ("US", "New York City"): "New York", ("US", "Philadelphia"): "Philadelphie",
    ("US", "New Orleans"): "La Nouvelle-Orléans", ("US", "St. Louis"): "Saint-Louis",
    ("CA", "St. John's"): "Saint-Jean de Terre-Neuve", ("CA", "Greater Sudbury"): "Grand Sudbury",
}

# Exonyms that are identical to the local/English form but worth a note are not listed.
# Special locatives that are not "à {name}".
SPECIAL_LOC = {
    ("US", "The Bronx"): ("le Bronx", "dans le Bronx", 1, "arrondissement de New York, article"),
}

QUEBEC = set("""Montréal|Laval|Mont-Royal|Westmount|Québec|L'Ancienne-Lorette|Sherbrooke|Côte-Saint-Luc|Boucherville|
Saint-Jérôme|Granby|Lévis|Trois-Rivières|Longueuil|Shawinigan|Sorel-Tracy|Gatineau|Saint-Hyacinthe|Vaudreuil-Dorion|
Victoriaville|Terrebonne|Saint-Georges|L'Assomption|Rimouski|Drummondville|Magog|Rivière-du-Loup|
Saint-Augustin-de-Desmaures|Saint-Jean-sur-Richelieu|Alma|Saint-Charles-Borromée|Sainte-Catherine|Varennes|Brossard|
Repentigny|Beloeil|Boisbriand|Saint-Constant|Châteauguay|Val-d'Or|Rock Forest|Saguenay|Joliette|LaSalle|Dorval|
Sainte-Thérèse|Thetford Mines|Chicoutimi|Salaberry-de-Valleyfield|Dollard-Des Ormeaux|Mascouche|Rouyn-Noranda|
Saint-Eustache|Chambly|Blainville|Mirabel|Jonquière|Saint-Bruno-de-Montarville|Saint-Lin–Laurentides|
La Haute-Saint-Charles|Sainte-Julie|Charlesbourg|Deux-Montagnes|Saint-Lazare|Candiac|Amos|Kirkland|Mont-Saint-Hilaire|
Pointe-Claire|Saint-Louis-de-Terrebonne|L’Île-Bizard–Sainte-Geneviève|Baie-Comeau|La Prairie|Pierrefonds-Roxboro|
Les Coteaux""".replace("\n", "").split("|"))

FRANCOPHONE = {"FR", "BE", "CH", "LU", "MC"}

# names to put in the safe form because the place is a region/area rather than a town
SAFE_FORM = {("AU", "Blue Mountains"), ("AU", "Central Coast")}


def is_latin(s):
    for ch in s:
        if ch.isalpha():
            name = unicodedata.name(ch, "")
            if "LATIN" not in name and ch not in "ʻ":
                return False
    return True


def locative(name):
    """French locative for a city name; returns (phrase, decl_ok, note)."""
    if name.startswith("Le ") and len(name) > 3:
        return "au " + name[3:], 1, "article contracté"
    if name.startswith("Les ") and len(name) > 4:
        return "aux " + name[4:], 1, "article contracté"
    if name.startswith("La ") or name.startswith("L'") or name.startswith("L’"):
        return "à " + name, 1, "article conservé"
    return "à " + name, 1, ""


def build():
    rows = list(csv.DictReader(open(SRC, encoding="utf-8")))
    out = []
    n_ex = 0
    doubtful = []
    for x in rows:
        cc, loc, en = x["cc"], x["name_local"], x["name_en"]
        key_l, key_e = (cc, loc), (cc, en)
        notes = []
        if key_l in SPECIAL_LOC or key_e in SPECIAL_LOC:
            name, phrase, ok, note = SPECIAL_LOC.get(key_l) or SPECIAL_LOC[key_e]
            name = name[0].upper() + name[1:]
            out.append((x, name, phrase, ok, note))
            n_ex += 1
            continue
        ex = EX.get(key_l) or EX.get(key_e)
        if ex and ex != loc:
            name = ex
            n_ex += 1
            notes.append("exonyme FR")
        elif is_latin(loc):
            name = loc
        else:
            name = en
            notes.append("translittération (nom EN)")
        if (cc, loc) in SAFE_FORM:
            phrase, ok = "dans la ville de " + name, 0
            notes.append("zone/agglomération, forme sûre")
            doubtful.append(f"{x['geonameid']} {cc} {name}")
        else:
            phrase, ok, n2 = locative(name)
            if n2:
                notes.append(n2)
        out.append((x, name, phrase, ok, "; ".join(notes)))

    def group(x):
        if x["cc"] in FRANCOPHONE or (x["cc"] == "CA" and x["name_local"] in QUEBEC):
            return 0
        if x["stage"] == "month":
            return 1
        return 2

    # stable sort keeps input order (chargers desc inside stage) within each group
    out.sort(key=lambda t: group(t[0]))
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["geonameid", "name", "in_phrase", "decl_ok", "note"])
        for x, name, phrase, ok, note in out:
            w.writerow([x["geonameid"], name, phrase, ok, note])

    # validation
    got = list(csv.DictReader(open(OUT, encoding="utf-8")))
    assert len(got) == len(rows), (len(got), len(rows))
    assert sorted(r["geonameid"] for r in got) == sorted(r["geonameid"] for r in rows)
    assert len({r["geonameid"] for r in got}) == len(got)
    assert all(r["name"].strip() and r["in_phrase"].strip() for r in got)
    missing_ca = QUEBEC - {x["name_local"] for x in rows if x["cc"] == "CA"}
    groups = [group(t[0]) for t in out]
    print("rows", len(got), "exonyms", n_ex, "groups", [groups.count(i) for i in range(3)])
    print("quebec names not found:", missing_ca)
    unused = [k for k in EX if not any((x["cc"], x["name_local"]) == k or (x["cc"], x["name_en"]) == k for x in rows)]
    print("unused exonym keys:", unused)
    print("doubtful:", doubtful)


if __name__ == "__main__":
    build()
