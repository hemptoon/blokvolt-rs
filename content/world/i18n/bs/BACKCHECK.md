# Bosnian (bs) back-translation check — 60 strings

Method: back60.json was written blind from the Bosnian only; then compared with the EN originals in content/world/.

## Summary
- Match in meaning: 56 / 60
- Minor nuance: 4
- Real errors (meaning changed / wrong / broken placeholder): 0
- Placeholders ({net}, {date}, {n}, {m}, {city}, {country_u}, {n_cities}, {share}, {pct_multi}, {pct_recent}) and the HTML link in ft_data are all preserved.
- Non-Bosnian lexis: no Serbian ekavica (cena/mesto/gde etc.) and no Croatian-only words (tjedan/tisuća/točka/karta/cjenik). Ijekavica is consistent (cijene, cjenovnici, mjesta, prosjek, provjereno, procijenjeni). "mapa", "tačka", "sedmični", "cjenovnik", "Evropa" are correct Bosnian choices. No "mi"/"naš".
- Borderline lexis (acceptable in Bosnian, optional polish): "zvaničnih" (službenih is more typical in BiH official style), "fajla" (datoteke is more formal), "spisak" (fine; popis also used).

## Discrepancies (all minor)

1. texts.download.what_p
   - EN: ...Prices, team checks and BlokVolt's corrections for the Balkans are not part of the file.
   - BS: ...Cijene, ručne provjere i ispravke BlokVolta za Balkan nisu dio fajla.
   - Back: ...Prices, manual checks and BlokVolt corrections...
   - Issue: "team checks" became "manual checks" — slight shift, but arguably the right impersonal rendering. "fajla" is colloquial.
   - Suggested: ...Cijene, provjere BlokVolta i ispravke za Balkan nisu dio datoteke.

2. strings_prices.t_hub
   - EN: European EV Charging Price Index
   - BS: Evropski indeks cijena javnog punjenja
   - Back: European public charging price index
   - Issue: "EV" dropped, "public" added. Meaning is close (the index covers public charging only), so acceptable; just not literal.
   - Suggested (if you want it literal): Evropski indeks cijena punjenja električnih vozila

3. texts.download.fields[11][1]
   - EN: Access type (public, restricted and similar)
   - BS: Vrsta pristupa (javno, ograničen pristup i slično)
   - Back: Access type (public, restricted access and similar)
   - Issue: the list mixes forms (neuter adverb "javno" + noun phrase "ograničen pristup").
   - Suggested: Vrsta pristupa (javni, ograničeni i slično)

4. strings_shell.sources_p
   - EN: The data comes from {n} open sources: official registries, ...
   - BS: Podaci dolaze iz otvorenih izvora (ukupno: {n}): zvaničnih registara, ...
   - Back: The data comes from open sources ({n} in total): official registers, ...
   - Issue: meaning matches (the "ukupno: {n}" structure neatly avoids number agreement — keep it). Only "zvaničnih" is more Serbian-leaning.
   - Suggested: Podaci dolaze iz otvorenih izvora (ukupno: {n}): službenih registara, Open Charge Mapa, OpenStreetMapa i otvorenih podataka samih mreža. Cijeli spisak s licencama i atribucijom nalazi se na jednoj stranici:

Other small differences that were judged a full match: "nisu učitani" vs "could not be loaded" (card_err); "bez ugovora / uz pretplatu" for "ad hoc / with a plan" (th_this, d_country) — the standard rendering; "Punjač za električne automobile" for "EV charging station" (c_unnamed); "Kako se računa indeks" for "How the index is made" (h_method).
