# L-SV — names (countries.csv, cities.csv)

- countries.csv: 150 rows. Names from CLDR sv (Babel 2.18); short forms for HK "Hongkong", MO "Macao", MM "Myanmar" (CLDR: "Hongkong SAR", "Macao SAR", "Myanmar (Burma)"). Slugs: ASCII, å/ä→a, ö→o, "S:t"→"st"; all unique.
- in_phrase: "i <land>"; "på" for island countries/territories as in standard Swedish (26): Åland, Barbados, Kuba, Cypern, Fiji, Färöarna, Guernsey, Haiti, Isle of Man, Island, Jersey, Jamaica, Caymanöarna, S:t Lucia, Sri Lanka, Saint-Martin, Malta, Mauritius, Nya Kaledonien, Filippinerna, Réunion, Svalbard och Jan Mayen, Tonga, Trinidad och Tobago, S:t Vincent och Grenadinerna, Samoa. Irland, Japan, Indonesien, Taiwan, Nya Zeeland, Storbritannien keep "i".
- cities.csv: all 5 605 cities. Order: SE/FI/AX (122) → other month → quarter → balkan. in_phrase always "i <stad>", decl_ok = 1 (Swedish has no case forms for place names).
- Names: local name (names/cities.csv name_local), Swedish exonym where established (30, note "sv exonym": Bryssel, Haag, Prag, Köpenhamn, Lissabon, Aten, Moskva, S:t Petersburg, Bukarest, Belgrad, Neapel, Venedig, Brygge, Iraklion, Rhodos, Korint, Korfu, Pireus, Kyiv, Charkiv, Teheran …); exonyms applied only in the right country (US Athens/Naples/Hanover stay English).
- Finland: Swedish official names for bilingual municipalities (26, "sv official": Helsingfors, Esbo, Vanda, Åbo, Borgå, Karleby, Vasa, Kyrkslätt, Sibbo, Lojo, S:t Karins, Raseborg, Jakobstad, Pargas, Korsholm, Kervo, Träskända, Hyvinge, Tusby, Vichtis, Nådendal …) and traditional Swedish names (15, "sv traditional": Tammerfors, Uleåborg, Tavastehus, Björneborg, Lahtis, Villmanstrand, S:t Michel, Raumo, Nyslott, Torneå, Kajana, Brahestad, Idensalmi, Birkala, Lembois).
- 165 cities with non-Latin local name (GR, BG, RU, BY, UA, HK, KR, CN …) use name_en (note "local non-Latin → EN").

Open questions
- Finnish monolingual cities: traditional Swedish names (Tammerfors, Uleåborg) are standard in Sweden; Lembois/Birkala/Idensalmi are less known in Sweden — Andrei may prefer the Finnish name there.
- Greek: only well-established exonyms changed; others romanised from name_en.
