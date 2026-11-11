# DE — Notizen zur Lokalisierung (L-DE, 09.11.2026)

Status: alle Dateien vollständig, `python3 content/world/i18n/de/check.py` → 0 Fehler.
Sprache wird NICHT eingeschaltet (erst nach Gate G8, über K8-i18n).

## Anrede und Ton
- Formell „Sie“ oder unpersönlich; nie „wir/uns/unser“, „Redaktion“, „Team“, „du“.
- Kein „24/7“, „rund um die Uhr“, „sofort/umgehend“ als Versprechen, keine Rangfolgen von Netzen, kein „unabhängig“ über die Seite (EN „independent reference“ → „neutrales Nachschlagewerk“).
- Deutsche Anführungszeichen „…“ im Fließtext; Gedankenstrich teils „–“ statt „—“.
- `pct` = „{x} %“ (mit Leerzeichen, deutsche Norm). Falls das Layout keine Lücke will — auf „{x}%“ ändern.

## Plurale (CLDR de: one, other)
- `pl_city_in`, `pl_country_in` stehen nach „in“ → Dativ: Stadt/Städten, Land/Ländern.
- `strings_shell.pl_cc` steht in `home_lead` nach „in“ → Land/Ländern (Dativ).
- Übrige pl_* im Nominativ/Akkusativ (Ladestandort/Ladestandorte, Ladenetz/Ladenetze, Ladepunkt/Ladepunkte …).

## Was der Motor (K8) für DE braucht
- `{country_u}` muss für DE aus `countries.csv:in_phrase` kommen („in Deutschland“, „in der Schweiz“, „in den Niederlanden“, „im Vereinigten Königreich“, „auf Zypern“). Viele Strings (d_country, t_country, t_network, h_n_places, p_net_share, Preis-Titel) setzen das voraus. `fallback_u` = „in {x}“.
- Stadtphrasen: `cities.csv:in_phrase` = „in <Name>“; deutsche Städtenamen werden nach „in“ nicht dekliniert → `decl_ok = 1` für alle 5 605.
- `pl_form` muss Objekte `{one, other}` annehmen (Babel).

## Termini (Glossar `de`)
Ladestation, Ladesäule (charger), Ladepunkt, Standort/Ladestandort, Ladenetz, Betreiber, Schnellladen, Stecker, Leistung, offene Daten, Zuverlässigkeit/Datenzuverlässigkeit, Ad-hoc-Preis, Abo, Grundgebühr, Haushaltsstrom, inkl./ohne MwSt.
Strittig, bewusst gewählt:
- „home charger“ → „Wallbox zu Hause“ (Glossar „Ladesäule“ klingt für Heimgeräte falsch).
- „Karte“ = Karte und Info-Karte; `report_map` etwas holprig — Alternative „im Infofenster des Standorts auf der Karte“.
- „public layer“ → „öffentliche Ebene“ (wörtlich).
- „Independent check“ (Datenqualität, nicht über die Seite) → „Externe Prüfung“.
- `ft_about` „About“ → „Über BlokVolt“ (blankes „Über“ geht im Deutschen nicht).
- „Mitarbeitende“ (geschlechtsneutral) statt „Mitarbeiter“.
- Zitiertitel des Preisindex in `data_p` bleibt Englisch (Eigenname des Datensatzes).

## Namen
- Länder: CLDR-Spalte `name_de`; Ausnahmen Kurzform „Hongkong“, „Macau“ statt „Sonderverwaltungsregion …“. Slugs: ASCII aus dem deutschen Namen (ä→ae, ö→oe, ü→ue, ß→ss), z. B. `oesterreich`, `vereinigte-staaten`, `vereinigtes-koenigreich`.
- Städte: Regel = Titel des Artikels in der deutschen Wikipedia. Exonyme u. a. Brüssel, Lüttich, Brügge, Ostende, Ypern, Luxemburg, Prag, Brünn, Pilsen, Budweis, Karlsbad, Olmütz, Warschau, Krakau, Breslau, Danzig, Posen, Stettin, Thorn, Mailand, Turin, Neapel, Venedig, Padua, Mantua, Bozen, Meran, Trient, Bukarest, Hermannstadt, Sathmar, Belgrad, Kopenhagen, Lissabon, Straßburg, Nizza, Athen, Piräus, Patras, Rhodos, Korfu, Korinth, Theben, Moskau, Sankt Petersburg, Kyjiw, Lwiw, Charkiw, Tokio, Teheran, Tiflis, Taschkent, Baku, Neu-Delhi, Hanoi.
- Kyrillisch (RU/BG/BY/UA/KZ): Duden-Transkription (Plowdiw, Warna, Jekaterinburg). MK: amtliche Lateinschrift (Štip, Kočani). Griechisch/CJK/Arabisch: EN-Umschrift außer Exonyme.
- Paris/Marseille/Lyon-Arrondissements: „Marseille (9. Arrondissement)“.
- Stadt- und Netz-Slugs bleiben gemeinsam (P1), nur der Länder-Slug ist deutsch.

## Offene Fragen an Andrei
1. Historische deutsche Namen polnischer/tschechischer/rumänischer Städte (Breslau, Danzig, Stettin, Posen, Thorn, Brünn, Olmütz, Hermannstadt, Sathmar): Standard der de.wikipedia, aber für Leser aus PL/CZ teils sensibel. Annahme: so lassen. Alternative: lokale Namen (Wrocław …) für alles außer Prag/Warschau/Krakau/Bukarest.
2. Kyjiw/Lwiw/Charkiw (Auswärtiges Amt) statt Kiew/Lemberg/Charkow — Annahme: neue Schreibung.

## QA
- check.py: Schlüssel, Platzhalter, HTML, Entities, leere Werte, Plural-Kategorien (Babel), Slugs ASCII, CSV lesbar, verbotene Wörter.
- Rückübersetzung von 60 zufälligen Strings (blind): 59 ok, 1 „minor“ (`ft_about`, bewusst), 0 Sinnabweichungen.

## L2-de (11.11.2026)
- Neue Dateien: strings_pay, strings_press, strings_b2b, strings_embed; strings_map + 29 Schlüssel (Check-ins). texts.json + `pay`, `routes` (LANG0-Format: Knotenpfad → Text).
- Begriffe: check-in → „Rückmeldung“; drivers → „Fahrende“; Preisindex einheitlich „Europäischer Preisindex für das Laden von E-Autos“ (wie strings_prices); ODbL-„public layer“ → „öffentliche Ebene“.
- `{name}` (Land im Nominativ) nur in artikelfesten Konstruktionen („{name} gehört zur EU“, Länderseite „{name}“), damit „Schweiz/Niederlande“ ohne Artikel nicht holpern. Bei „Die Schweiz gehört …“ würde der Motor den Artikel brauchen — offen für LANGI.
- Routen-Städte wie cities.csv: Belgrad, Plowdiw, Plewen, Weliko Tarnowo, Hermannstadt.
- cities.csv: +48 NOBIL-Orte (NO 2, SE 46) mit lokalem Namen; drei Namen nach de.wikipedia: Siders, Düdelingen, Esch an der Alzette.
- check.py: alle 8 strings-Dateien, texts.pay/routes, Stadtseiten aus state/pages_state.json.

## FIXL (11.11.2026)
- `strings_home.json` neu (71 Schlüssel); `strings_shell` + `lang_hint` „Diese Seite gibt es auch auf Deutsch“, `lang_hint_close` „Schließen“.
- `countries.csv` + Spalte `name_nom` (Nominativ mit Artikel). Verwendung nur nach „für“ (`afir_eu`, `afir_non`, `conn_txt`), nie am Satzanfang, nie als Subjekt mit Verb (Kongruenz Plural).
- Slugs: `/de/bezahlen/`, `/de/routen/`, `/de/fuer-medien/`, `/de/daten-fuer-unternehmen/`, `/de/embed/karte/`, `/de/karte-fuer-ihre-website/`, `/de/fuer-entwickler/`.
- D12: Städte in PL/CZ/RO mit lokalem Namen außer Prag, Warschau, Krakau, Bukarest (offene Frage 1 oben damit entschieden). D13: Kyjiw.
- cities.csv: + Genf (2660646); check.py lässt keine geonameid außerhalb von names/cities.csv mehr zu.
